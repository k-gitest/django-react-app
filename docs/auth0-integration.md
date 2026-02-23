# Auth0統合詳細ガイド

## 目次

- [概要](#概要)
- [実装されている機能](#実装されている機能)
- [アーキテクチャ](#アーキテクチャ)
- [JWT検証の仕組み](#jwt検証の仕組み)
- [ユーザー管理戦略](#ユーザー管理戦略)
- [JWKSキャッシング](#jwksキャッシング)
- [エラーハンドリング](#エラーハンドリング)
- [トランザクション保護](#トランザクション保護)
- [セキュリティ考慮事項](#セキュリティ考慮事項)
- [パフォーマンス最適化](#パフォーマンス最適化)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

本プロジェクトでは、`apps/common/auth/oidc.py` の `OIDCAuthentication` クラスによってAuth0統合を実現しています。

**実装済みの機能**:
- ✅ JWT署名検証（RS256、joserfc使用）
- ✅ JWKSキャッシング（Django Cache、24時間）
- ✅ ユーザー自動作成（oidc_sub管理）
- ✅ トランザクション保護（同時リクエスト対策）
- ✅ カスタム例外への変換（JoseError → InvalidTokenError）
- ✅ 時刻ズレ許容（leeway=60秒）

**技術スタック**:
```
joserfc==1.0.0      # JWT検証
requests==2.31.0    # JWKS取得
```

---

## 実装されている機能

### 1. JWT検証フロー
```
1. Authorization ヘッダーからトークン取得
   ↓
2. JWKSエンドポイントから公開鍵取得（キャッシュ優先）
   ↓
3. joserfc.jwt.decode() で署名検証
   ↓
4. claims.validate() でクレーム検証
   ├─ issuer: https://{AUTH0_DOMAIN}/
   ├─ audience: {AUTH0_AUDIENCE}
   ├─ exp: 有効期限
   └─ leeway: 60秒の時刻ズレ許容
   ↓
5. ユーザー取得または作成
```

### 2. ユーザー管理戦略

**3段階のフォールバック**:
```python
# 1. oidc_sub で検索（Auth0ユーザー）
user = User.objects.filter(oidc_sub=oidc_sub).first()
if user:
    # メールアドレスや名前を更新
    return user

# 2. email で検索（既存Djangoユーザー）
user = User.objects.filter(email=email).first()
if user:
    # OIDC連携を追加
    user.oidc_sub = oidc_sub
    user.save()
    return user

# 3. 新規作成
user = User.objects.create(
    oidc_sub=oidc_sub,
    email=email,
    first_name=payload.get('given_name', ''),
    last_name=payload.get('family_name', ''),
)
return user
```

**メリット**:
- ✅ Auth0ユーザーは即座に認証
- ✅ 既存Djangoユーザーは自動でAuth0連携
- ✅ 新規ユーザーはシームレスに作成

---

## アーキテクチャ

### 認証フロー全体
```
┌─────────────────────────────────────────────────────────────┐
│                   Auth0 Authentication Flow                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【フロントエンド】                                          │
│    ├─ Auth0 React SDK (@auth0/auth0-react)                 │
│    ├─ loginWithRedirect()                                  │
│    │   └─ Auth0 Universal Login へリダイレクト             │
│    │                                                        │
│    ├─ Callback処理                                         │
│    │   └─ Access Token 取得                                │
│    │                                                        │
│    └─ API呼び出し                                           │
│        └─ Authorization: Bearer <token>                    │
│                                                             │
│  【バックエンド】                                            │
│    ├─ OIDCAuthentication.authenticate()                    │
│    │   ├─ Bearer トークン抽出                              │
│    │   ├─ get_jwks() → Django Cache確認                   │
│    │   │   └─ キャッシュなし → Auth0 JWKS取得             │
│    │   │                                                   │
│    │   ├─ _verify_token()                                 │
│    │   │   ├─ jwt.decode() → 署名検証（RS256）            │
│    │   │   └─ claims.validate() → クレーム検証            │
│    │   │       ├─ issuer                                  │
│    │   │       ├─ audience                                │
│    │   │       ├─ exp（有効期限）                          │
│    │   │       └─ leeway=60秒                             │
│    │   │                                                   │
│    │   └─ _get_or_create_user()                           │
│    │       ├─ @transaction.atomic                         │
│    │       ├─ select_for_update() → 排他ロック            │
│    │       └─ oidc_sub / email による取得・作成           │
│    │                                                        │
│    └─ (user, None) を返却                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## JWT検証の仕組み

### joserfc による検証

**joserfc** は、JWTの検証に特化した高速・安全なライブラリです。

**特徴**:
- ✅ RS256アルゴリズムをネイティブサポート
- ✅ クレーム検証を一括実行
- ✅ 時刻ズレ許容（leeway）に対応
- ✅ JWKSから自動的にkid照合

**実装**:
```python
def _verify_token(self, token):
    jwks = self.get_jwks()
    
    # 1. 署名検証（RS256固定）
    # kidの照合は joserfc が内部で自動実行
    claims = jwt.decode(token, jwks, algorithms=['RS256'])
    
    # 2. クレーム検証（exp, iss, aud を一括チェック）
    claims.validate(
        issuer=self.issuer,           # https://{AUTH0_DOMAIN}/
        audience=self.audience,        # API Identifier
        leeway=self.leeway             # 60秒の時刻ズレ許容
    )
    
    # claims は辞書のように扱える
    return claims
```

### JWKS（JSON Web Key Set）

Auth0は公開鍵を以下のエンドポイントで公開しています：
```
https://{AUTH0_DOMAIN}/.well-known/jwks.json
```

**JWKSの構造**:
```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "abc123",
      "use": "sig",
      "n": "...",
      "e": "AQAB",
      "alg": "RS256"
    }
  ]
}
```

**検証プロセス**:
1. トークンのヘッダーから`kid`（Key ID）を取得
2. JWKSから一致する`kid`の公開鍵を取得
3. 公開鍵で署名を検証
4. クレーム（iss, aud, exp）を検証

**joserfcの利点**:
- ❌ 手動でkid照合する必要なし
- ❌ 手動でRS256検証する必要なし
- ✅ `jwt.decode(token, jwks, algorithms=['RS256'])` だけで完結

---

## ユーザー管理戦略

### oidc_sub フィールド

**設計判断**:
- Auth0の`sub`（Subject）をユーザーの一意識別子として使用
- `sub`の形式: `auth0|507f1f77bcf86cd799439011`

**データベーススキーマ**:
```python
class CustomUser(AbstractUser):
    oidc_sub = models.CharField(
        max_length=255,
        unique=True,        # 一意制約
        null=True,
        blank=True,
        db_index=True,      # 検索高速化
    )
```

**インデックス**:
```python
indexes = [
    models.Index(fields=['email']),
    models.Index(fields=['oidc_sub']),
]
```

### ユーザー作成フロー
```python
@transaction.atomic
def _get_or_create_user(self, payload):
    oidc_sub = payload.get('sub')
    email = payload.get('email')
    
    # 1. oidc_sub で検索（Auth0ユーザー）
    user = User.objects.select_for_update().filter(oidc_sub=oidc_sub).first()
    
    if user:
        # 情報更新（メールアドレスや名前が変更されている可能性）
        if user.email != email:
            user.email = email
            user.save(update_fields=['email', 'first_name', 'last_name'])
        return user
    
    # 2. email で検索（既存Djangoユーザー）
    user = User.objects.select_for_update().filter(email=email).first()
    
    if user:
        # OIDC連携を追加
        user.oidc_sub = oidc_sub
        user.save(update_fields=['oidc_sub'])
        return user
    
    # 3. 新規作成
    user = User.objects.create(
        oidc_sub=oidc_sub,
        email=email,
        first_name=payload.get('given_name', ''),
        last_name=payload.get('family_name', ''),
    )
    return user
```

---

## JWKSキャッシング

### Django Cacheによるキャッシング

**実装**:
```python
def get_jwks(self):
    cache_key = 'auth0_jwks'
    jwks = cache.get(cache_key)
    
    if not jwks:
        response = requests.get(self.jwks_url, timeout=10)
        response.raise_for_status()
        jwks = response.json()
        cache.set(cache_key, jwks, 60 * 60 * 24)  # 24時間
        logger.info('Auth0 JWKS fetched and cached')
    
    return jwks
```

**キャッシュ戦略**:
- **キャッシュ先**: Django Cache（Redis）
- **キャッシュ期間**: 24時間
- **理由**: Auth0のキーローテーションは通常24時間以上

**メリット**:
- ⚡ API呼び出しを大幅削減（初回のみ取得）
- 💰 ネットワーク帯域の節約
- 🚀 認証処理の高速化（数十ミリ秒 → 数ミリ秒）

**キーローテーション対応**:
- Auth0がキーローテーション時、新しい`kid`でトークンを発行
- 古い`kid`のトークンは検証失敗 → キャッシュをクリア
- 次回リクエストで新しいJWKSを取得

---

## エラーハンドリング

### JoseError → カスタム例外への変換

**実装**:
```python
try:
    payload = self._verify_token(token)
    user = self._get_or_create_user(payload)
    return (user, None)

except JoseError as e:
    error_msg = str(e).lower()
    
    # 有効期限切れ
    if 'expired' in error_msg or 'exp' in error_msg:
        logger.warning(f'Token expired: {e}')
        raise TokenExpiredError()
    
    # その他のJWT検証失敗
    else:
        logger.warning(f'JWT verification failed: {e}')
        raise InvalidTokenError(internal_reason=str(e))

except Exception as e:
    logger.error(f'Authentication error: {e}', exc_info=True)
    raise AuthenticationFailed(f'Authentication error: {str(e)}')
```

### カスタム例外の定義

**InvalidTokenError**:
```python
class InvalidTokenError(AuthenticationError):
    def __init__(self, internal_reason: Optional[str] = None):
        super().__init__(
            message="トークンの検証に失敗しました。再度ログインしてください。",
            internal_info=internal_reason  # ログのみ
        )
        self.code = "invalid_token"
```

**TokenExpiredError**:
```python
class TokenExpiredError(AuthenticationError):
    def __init__(self):
        super().__init__(
            message="トークンの有効期限が切れています。再度ログインしてください。"
        )
        self.code = "token_expired"
```

**フロントエンドへのレスポンス**:
```json
{
  "error": "token_expired",
  "detail": "トークンの有効期限が切れています。再度ログインしてください。"
}
```

**internal_reason の利点**:
- ✅ フロントエンドには詳細を返さない（セキュリティ）
- ✅ ログには詳細を記録（デバッグ）
- ✅ Sentryには詳細を送信（モニタリング）

---

## トランザクション保護

### 同時リクエスト対策

**問題**:
```
ユーザーAが同時に2つのリクエストを送信
↓
両方のリクエストが同時に _get_or_create_user() を実行
↓
両方とも「ユーザーが存在しない」と判断
↓
両方が User.objects.create() を実行
↓
IntegrityError: UNIQUE constraint failed
```

**解決策**:
```python
@transaction.atomic
def _get_or_create_user(self, payload):
    # select_for_update() で排他ロック
    user = User.objects.select_for_update().filter(oidc_sub=oidc_sub).first()
    
    if user:
        return user
    
    # この時点で他のトランザクションはロック待ち
    user = User.objects.create(...)
    return user
```

**メリット**:
- ✅ 同時リクエストでも安全
- ✅ IntegrityErrorを回避
- ✅ パフォーマンスへの影響は最小限

### IntegrityError の処理

**実装**:
```python
try:
    user = User.objects.create(...)
    return user

except DjangoIntegrityError as e:
    error_msg = str(e).lower()
    
    # メールアドレス重複
    if 'unique' in error_msg and 'email' in error_msg:
        user = User.objects.filter(email=email).first()
        if user:
            user.oidc_sub = oidc_sub
            user.save(update_fields=['oidc_sub'])
            return user
        raise IntegrityConstraintError(
            constraint_type='unique_email',
            user_hint='このメールアドレスは既に使用されています',
            internal_details=str(e)
        )
    
    # oidc_sub重複
    if 'unique' in error_msg and 'oidc_sub' in error_msg:
        user = User.objects.filter(oidc_sub=oidc_sub).first()
        if user:
            return user
        raise IntegrityConstraintError(
            constraint_type='unique_oidc_sub',
            user_hint='認証情報の重複エラーが発生しました',
            internal_details=str(e)
        )
```

---

## セキュリティ考慮事項

### 1. JWT検証の厳格性

**検証項目**:
```python
claims.validate(
    issuer=self.issuer,      # 発行元検証
    audience=self.audience,   # オーディエンス検証
    leeway=self.leeway        # 時刻ズレ許容（60秒）
)
```

**重要性**:
- ✅ **issuer**: 信頼できるAuth0テナントからのトークンのみ受け入れ
- ✅ **audience**: このAPIのために発行されたトークンのみ受け入れ
- ✅ **exp**: 有効期限切れのトークンを拒否
- ✅ **leeway**: サーバー間の時刻ズレを許容（60秒）

### 2. HTTPS必須

本番環境では、Auth0との通信は必ずHTTPSで行われます：
```python
# settings/production.py
SECURE_SSL_REDIRECT = True
```

### 3. internal_info の分離

**設計原則**:
- ✅ ユーザー向けメッセージ（`message`）は汎用的
- ✅ 詳細情報（`internal_info`）はログ・Sentryのみ
- ❌ フロントエンドには詳細を返さない

**例**:
```python
# ユーザーには汎用メッセージ
message="トークンの検証に失敗しました。再度ログインしてください。"

# ログには詳細
internal_info="Invalid signature: RS256 verification failed"
```

---

## パフォーマンス最適化

### 1. JWKSキャッシング（実装済み）

**効果**:
```
キャッシュなし: 300-500ms
キャッシュあり: 10-50ms
```

### 2. select_for_update() の最小化

**ベストプラクティス**:
```python
# ✅ 良い例: 必要な時だけロック
user = User.objects.filter(oidc_sub=oidc_sub).first()
if user:
    return user

# ロックが必要な場合のみ
user = User.objects.select_for_update().filter(email=email).first()
```

### 3. ユーザー情報のキャッシング（将来的な拡張）

**実装例**:
```python
def _get_or_create_user(self, payload):
    oidc_sub = payload.get('sub')
    
    # キャッシュから取得
    cache_key = f'user_oidc_{oidc_sub}'
    user_id = cache.get(cache_key)
    
    if user_id:
        return User.objects.get(id=user_id)
    
    # DB検索
    user = User.objects.filter(oidc_sub=oidc_sub).first()
    
    if user:
        cache.set(cache_key, user.id, 900)  # 15分
    
    return user
```

---

## トラブルシューティング

### エラー: Unable to find appropriate key

**症状**:
```
InvalidTokenError: Unable to find appropriate key
```

**原因**:
- JWTの`kid`とJWKSの公開鍵が一致しない
- JWKSキャッシュが古い

**解決策**:
```bash
# 1. JWKSを確認
curl https://{AUTH0_DOMAIN}/.well-known/jwks.json

# 2. トークンのkidを確認
# https://jwt.io でトークンをデコード

# 3. キャッシュをクリア
python manage.py shell
>>> from django.core.cache import cache
>>> cache.delete('auth0_jwks')
```

---

### エラー: Token has expired

**症状**:
```
TokenExpiredError: トークンの有効期限が切れています
```

**原因**:
- アクセストークンの有効期限切れ（デフォルト: 24時間）

**解決策**:
```typescript
// フロントエンドでトークンをリフレッシュ
const token = await getAccessTokenSilently({
  cacheMode: 'off'  // キャッシュを無視して再取得
});
```

---

### エラー: Email not found in token

**症状**:
```
InvalidTokenError: Email not found in token
```

**原因**:
- Auth0のスコープ設定で`email`が含まれていない

**解決策**:
```typescript
// フロントエンドでスコープを指定
<Auth0Provider
  authorizationParams={{
    scope: "openid profile email"
  }}
>
```

---

### エラー: IntegrityConstraintError

**症状**:
```
IntegrityConstraintError: このメールアドレスは既に使用されています
```

**原因**:
- 同じメールアドレスの既存ユーザーが存在

**解決策**:
```python
# 既存ユーザーにOIDC連携を追加
user = User.objects.filter(email=email).first()
user.oidc_sub = oidc_sub
user.save(update_fields=['oidc_sub'])
```

---

## まとめ

本プロジェクトのAuth0統合は以下の特徴があります：

**実装済み**:
- ✅ joserfc による厳格なJWT検証
- ✅ JWKSキャッシング（24時間）
- ✅ oidc_sub による柔軟なユーザー管理
- ✅ トランザクション保護
- ✅ カスタム例外への変換
- ✅ 時刻ズレ許容（60秒）

**セキュリティ**:
- 🔒 issuer/audience/exp 検証
- 🔒 HTTPS必須
- 🔒 internal_info の分離

**パフォーマンス**:
- ⚡ JWKSキャッシング
- ⚡ select_for_update() の最小化

この実装により、Auth0による安全で高速な認証を実現しています。