# ベクトル検索機能詳細ガイド

## 目次

- [概要](#概要)
- [アーキテクチャ](#アーキテクチャ)
- [非同期処理の実装](#非同期処理の実装)
- [Gemini API設定](#gemini-api設定)
- [Upstash Vector設定](#upstash-vector設定)
- [実装構成](#実装構成)
- [APIエンドポイント](#apiエンドポイント)
- [使用例](#使用例)
- [パフォーマンス最適化](#パフォーマンス最適化)
- [セキュリティ](#セキュリティ)
- [運用とモニタリング](#運用とモニタリング)
- [トラブルシューティング](#トラブルシューティング)
- [将来の拡張](#将来の拡張)

---

## 概要

Google Gemini APIとUpstash Vectorを使用した**セマンティック検索**機能を実装。自然言語でTodoを検索できます。

**例**:
- "明日の会議関連のタスク" → 会議資料作成、プレゼン準備など
- "プログラミングの勉強" → Python学習、React練習など

---

## アーキテクチャ

### 全体フロー

```
Todo作成/更新
    ↓
QStash にメッセージ送信（即座にレスポンス）
    ↓
Webhook エンドポイント（/api/v1/webhooks/vector-indexing）
    ↓
Gemini API でベクトル化（768次元）
    ↓
Upstash Vector に保存
```

### 使用技術

| サービス | 用途 | 選定理由 |
|---------|------|---------|
| **Google Gemini API** | テキストのベクトル化 | 永久無料枠（1,500リクエスト/日）、高品質 |
| **Upstash Vector** | ベクトルデータベース | サーバーレス課金、既存Upstashアカウント統合 |
| **QStash** | 非同期処理キュー | 自動リトライ、Todo CRUD操作を高速化 |

---

## 非同期処理の実装

### なぜ非同期か？

| 処理 | 同期（変更前） | 非同期（変更後） | 改善 |
|------|--------------|----------------|------|
| **Todo作成** | 300-500ms | 50-100ms | **3-5倍高速** ⚡ |
| **Todo更新** | 300-500ms | 50-100ms | **3-5倍高速** ⚡ |
| **Todo削除** | 100-200ms | 50-100ms | **1-2倍高速** ⚡ |
| **検索** | 100-300ms | 100-300ms | 同じ（同期処理） |

**メリット**:
- ✅ ユーザーがベクトル化を待つ必要がない
- ✅ QStashの自動リトライ（最大3回）
- ✅ Renderのスリープ対応

---

### QStash Service（共通基盤）

```python
# backend/common/infrastructure/qstash_client.py
class QStashClient:
    """
    QStashを使った非同期タスク送信（汎用版）
    
    Users（メール送信）とTodos（ベクトル化）で共通利用
    """
    
    @staticmethod
    def publish(endpoint_path: str, payload: dict, delay_seconds: int = 0):
        """QStashにメッセージを送信"""
        webhook_url = f"{settings.WEBHOOK_BASE_URL}{endpoint_path}"
        
        response = requests.post(
            f"https://qstash.upstash.io/v2/publish/{webhook_url}",
            headers={
                "Authorization": f"Bearer {settings.QSTASH_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload
        )
        return response.json()
```

---

### Todo Service（ビジネス層）

```python
# backend/todos/service.py
class TodoService:
    @staticmethod
    def create_todo(user, validated_data):
        # 1. Todoを作成（同期）
        todo = Todo.objects.create(user=user, **validated_data)
        
        # 2. ベクトル化をキューに追加（非同期）
        try:
            TodoQStashService.queue_vector_indexing(todo.id, operation="upsert")
        except Exception as e:
            logger.error(f"Failed to queue vector indexing: {e}")
            # エラーでもTodo作成は成功
        
        return todo
```

---

### Webhook Endpoint

```python
# backend/todos/views.py
@api_view(['POST'])
@permission_classes([IsQStashAuthenticated])  # QStash署名検証
def vector_indexing_webhook(request):
    """
    QStashから呼ばれるWebhook
    
    実際のベクトル化処理を実行
    """
    todo_id = request.data.get("todo_id")
    operation = request.data.get("operation")
    
    vector_service = VectorService()
    
    if operation == "delete":
        vector_service.delete_todo(todo_id)
    else:
        todo = get_object_or_404(Todo, id=todo_id)
        vector_service.add_todo(todo)
    
    return Response({"message": "Vector indexing completed"})
```

---

## Gemini API設定

### モデル設定

**モデル**: `text-embedding-004`
- **次元数**: 768
- **無料枠**: 1,500リクエスト/日、1M トークン/日
- **多言語対応**: 100+言語（日本語含む）

### テキスト準備

```python
def prepare_text(todo) -> str:
    # タイトル + 優先度 + 進捗を結合
    text = f"{todo.todo_title} 優先度:{todo.get_priority_display()} 進捗:{todo.progress}%"
    return text.strip()
```

### タスクタイプ

- `retrieval_document`: Todo保存時（検索される側）
- `retrieval_query`: 検索クエリ（検索する側）

### 実装例

```python
# backend/todos/embedding_service.py
import google.generativeai as genai

class EmbeddingService:
    MODEL_NAME = "models/text-embedding-004"
    
    @staticmethod
    def generate_embedding(text: str, task_type: str = "retrieval_document") -> list:
        """
        テキストをベクトル化
        
        Args:
            text: ベクトル化するテキスト
            task_type: "retrieval_document" | "retrieval_query"
        
        Returns:
            768次元のベクトル
        """
        result = genai.embed_content(
            model=EmbeddingService.MODEL_NAME,
            content=text,
            task_type=task_type
        )
        return result['embedding']
```

---

## Upstash Vector設定

### データベース設定

**データベース設定**:
- **Type**: Dense（密なベクトル）
- **Dimensions**: 768（Gemini text-embedding-004）
- **Similarity Function**: COSINE（コサイン類似度）
- **Region**: us-west-1（Renderと同じ）

### メタデータ保存

```python
{
  "title": "会議資料の作成",
  "user_id": 1,
  "priority": "HIGH",
  "progress": 50,
  "created_at": "2025-01-06T10:00:00Z"
}
```

### ユーザー分離

```python
# 検索時に user_id でフィルタリング
results = index.query(
    vector=query_embedding,
    top_k=5,
    filter=f"user_id = {user.id}"  # 他人のTodoは検索されない
)
```

### 実装例

```python
# backend/todos/vector_service.py
from upstash_vector import Index

class VectorService:
    def __init__(self):
        self.index = Index(
            url=settings.UPSTASH_VECTOR_REST_URL,
            token=settings.UPSTASH_VECTOR_REST_TOKEN
        )
    
    def add_todo(self, todo):
        """TodoをVector Indexに追加"""
        text = self._prepare_text(todo)
        embedding = EmbeddingService.generate_embedding(text)
        
        self.index.upsert(
            vectors=[{
                "id": str(todo.id),
                "vector": embedding,
                "metadata": {
                    "title": todo.todo_title,
                    "user_id": todo.user.id,
                    "priority": todo.priority,
                    "progress": todo.progress,
                    "created_at": todo.created_at.isoformat()
                }
            }]
        )
    
    def search_similar(self, query: str, user_id: int, top_k: int = 5):
        """類似Todoを検索"""
        query_embedding = EmbeddingService.generate_embedding(
            query, 
            task_type="retrieval_query"
        )
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=f"user_id = {user_id}",
            include_metadata=True
        )
        
        return results
```

---

## 実装構成

```
backend/todos/
├── service.py                # TodoService（ベクトル化をQStashにキューイング）
├── qstash_service.py         # TodoQStashService（QStash送信ラッパー）
├── embedding_service.py      # EmbeddingService（Gemini API呼び出し）
├── vector_service.py         # VectorService（Upstash Vector操作）
├── views.py                  # Webhook（vector_indexing_webhook, bulk_vector_indexing_webhook）
└── urls.py                   # APIエンドポイント

backend/webhooks/
└── urls.py                   # Webhook統合ルーティング

backend/common/
├── infrastructure/
│   └── qstash_client.py      # QStashClient（QStash実処理）
└── permissions.py            # IsQStashAuthenticated
```

---

## APIエンドポイント

| エンドポイント | Method | 説明 | 認証 |
|--------------|--------|-----|------|
| `/api/v1/todos/search/?q={query}` | GET | セマンティック検索 | 必須 |
| `/api/v1/todos/bulk-index/` | POST | 一括インデックス | 必須 |
| `/api/v1/webhooks/vector-indexing` | POST | ベクトル化Webhook | QStash |
| `/api/v1/webhooks/bulk-vector-indexing` | POST | 一括ベクトル化Webhook | QStash |

---

## 使用例

### セマンティック検索

```bash
# 基本的な検索
GET /api/v1/todos/search/?q=明日の会議関連
Authorization: Bearer <access-token>

# パラメータ指定
GET /api/v1/todos/search/?q=プログラミング&top_k=10&min_score=0.6
Authorization: Bearer <access-token>

# レスポンス例
{
  "query": "明日の会議関連",
  "results": [
    {
      "id": 15,
      "score": 0.87,
      "title": "会議資料の作成",
      "priority": "HIGH",
      "progress": 50
    },
    {
      "id": 23,
      "score": 0.75,
      "title": "プレゼン準備",
      "priority": "MEDIUM",
      "progress": 30
    }
  ],
  "count": 2
}
```

### 初期データのインデックス

```bash
# 方法1: APIエンドポイント
POST /api/v1/todos/bulk-index/
Authorization: Bearer <access-token>

# レスポンス
{
  "message": "インデックス処理をバックグラウンドで開始しました",
  "status": "queued"
}

# 方法2: 管理コマンド（将来実装）
docker compose exec backend python manage.py reindex_todos
```

---

## パフォーマンス最適化

### 1. 非同期処理によるレスポンス高速化

**変更前**（同期処理）:
```
Todo作成 → ベクトル化 → レスポンス
(50ms)     (250ms)      (300ms合計)
```

**変更後**（非同期処理）:
```
Todo作成 → QStash → レスポンス
(50ms)     (1ms)     (51ms合計) ⚡

--- バックグラウンド ---
QStash → Webhook → ベクトル化 → Upstash Vector
(1秒後)   (10ms)     (250ms)     (50ms)
```

---

### 2. キャッシュの活用

検索結果はTanStack Queryでキャッシュ：

```typescript
// frontend/src/features/todo/hooks/useTodoSearch.ts
export const useTodoSearch = (query: string) => {
  return useQuery({
    queryKey: ['todos', 'search', query],
    queryFn: () => todoService.searchSimilar(query),
    staleTime: 5 * 60 * 1000,  // 5分間キャッシュ
    enabled: query.length > 0,
  });
};
```

---

## セキュリティ

| 機能 | 実装 |
|-----|------|
| **QStash署名検証** | HMAC-SHA256で検証（common/security.py） |
| **ユーザー分離** | vector_service.py で user_id フィルタ |
| **認証必須** | 検索・一括インデックスは認証必須 |

**QStash署名検証**:

```python
# backend/common/permissions.py
class IsQStashAuthenticated(BasePermission):
    """QStash署名検証"""
    
    def has_permission(self, request, view):
        signature = request.headers.get('Upstash-Signature')
        
        if not signature:
            return False
        
        # HMAC-SHA256検証
        return verify_qstash_signature(
            signature=signature,
            body=request.body,
            signing_keys=[
                settings.QSTASH_CURRENT_SIGNING_KEY,
                settings.QSTASH_NEXT_SIGNING_KEY
            ]
        )
```

---

## 運用とモニタリング

### ログ確認

```bash
# ベクトル化の成功/失敗を確認
docker compose logs -f backend | grep "vector"

# 成功例
✅ Added/Updated todo 15 to vector index (async)

# 失敗例
❌ Vector indexing webhook error: ...
```

### QStash Dashboard

```
1. https://console.upstash.com/qstash にアクセス
2. "Messages" タブでメッセージ配信状況を確認
3. リトライ回数、成功/失敗を監視
```

### Gemini API 使用量

```
1. https://makersuite.google.com/app/apikey にアクセス
2. 使用量を確認
3. 無料枠（1,500リクエスト/日）の消費状況を監視
```

---

## トラブルシューティング

### ベクトル化が実行されない

```bash
# 確認項目
1. QStash Webhook が到達しているか
   → QStash Dashboard で確認

2. 環境変数が正しく設定されているか
   → GOOGLE_API_KEY
   → UPSTASH_VECTOR_REST_URL
   → UPSTASH_VECTOR_REST_TOKEN

3. Webhook署名検証が成功しているか
   → ログで "Invalid signature" を確認
```

### 検索結果が返らない

```bash
# 確認項目
1. Todoがベクトルインデックスに追加されているか
   → POST /api/v1/todos/bulk-index/ を実行

2. 類似度スコアが低すぎないか
   → min_score を 0.3 に下げて再検索

3. user_id フィルタが正しく動作しているか
   → ログで filter=f"user_id = {user_id}" を確認
```

### Gemini API エラー

```bash
# エラー: API Key invalid
解決策: GOOGLE_API_KEY を再確認

# エラー: Quota exceeded
解決策:
  1. 無料枠（1,500リクエスト/日）を超過
  2. 翌日まで待つ
  3. または有料プランに移行

# エラー: Rate limit exceeded
解決策:
  1. リクエスト頻度を下げる
  2. delay_seconds を増やす
```

---

## 将来の拡張

### フェーズ1: MVP（現在）

- ✅ 基本的なセマンティック検索
- ✅ 非同期ベクトル化
- ✅ Google Gemini API（無料枠）
- ✅ Upstash Vector（無料枠）
- 現在はTodoの短いテキスト（タイトル + メタデータ）を処理しているためチャンク化は不要
- **コスト**: $0/月

---

### フェーズ2: エンタープライズ（100K+ ユーザー）

**長文ドキュメント対応（チャンク化導入）**

将来的に長文ドキュメント（添付ファイル、メモ、プロジェクト説明等）を扱う場合：

| 段階 | チャンク化手法 | 選定理由 |
|------|--------------|---------|
| **Phase 1** | LangChain（RecursiveCharacterTextSplitter） | 実績豊富、コミュニティサポート充実 |
| **Phase 2** | Semantic Chunker（LlamaIndex） | 意味的なまとまりでチャンク分割 |
| **Phase 3** | カスタムチャンカー | ドメイン固有の最適化 |

**チャンク化が必要になるケース**:
- Todo に長文メモ機能を追加
- PDFドキュメントのアップロード対応
- プロジェクト説明（複数段落）の検索

**技術スタック例**:
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,        # Gemini の推奨チャンクサイズ
    chunk_overlap=50,      # 文脈の連続性を保つ
    separators=["\n\n", "\n", " ", ""]
)

chunks = splitter.split_text(long_document)
```

**インフラ構成**:
- 🚀 Vector DB: **Pinecone**
  - Namespace機能でユーザー・チャンク管理
  - メタデータフィルタリング（document_id, chunk_index等）
- 🚀 Embedding: **Gemini API 維持**（品質・コスト優位）
- 🚀 Hybrid Search（Dense + Sparse）
  - セマンティック検索 + キーワード検索の組み合わせ
- 🚀 リアルタイムインデックス更新
- **コスト**: $70-200+/月

---

## まとめ

| 項目 | 実装方法 |
|------|---------|
| **ベクトル化** | Google Gemini API（text-embedding-004） |
| **ベクトルDB** | Upstash Vector（COSINE類似度） |
| **非同期処理** | QStash（自動リトライ） |
| **ユーザー分離** | user_id フィルタ |
| **パフォーマンス** | 3-5倍高速化（非同期化） |
| **セキュリティ** | QStash署名検証 + 認証必須 |
| **コスト** | $0/月（無料枠のみ） |

この設計により、以下を実現しています：

✅ **高速なレスポンス**: ベクトル化を待たずに即座にレスポンス  
✅ **自然言語検索**: 曖昧な検索でもTodoを発見  
✅ **スケーラブル**: 非同期処理で高負荷に対応  
✅ **低コスト**: 無料枠のみで運用可能  
✅ **セキュア**: ユーザー分離とQStash署名検証  
✅ **保守性**: レイヤードアーキテクチャで保守容易