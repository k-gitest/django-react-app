# CI/CD パイプライン詳細ガイド

## 目次

- [概要](#概要)
- [ワークフロー構成](#ワークフロー構成)
- [Pull Request チェック](#pull-requestチェック)
- [バックエンドCI/CD](#バックエンドcicd)
- [フロントエンドCI/CD](#フロントエンドcicd)
- [再利用可能なワークフロー](#再利用可能なワークフロー)
- [カスタムアクション](#カスタムアクション)
- [環境変数管理](#環境変数管理)
- [Smoke Tests](#smoke-tests)
- [デプロイ戦略](#デプロイ戦略)
- [トラブルシューティング](#トラブルシューティング)
- [ベストプラクティス](#ベストプラクティス)

---

## 概要

GitHub Actionsによる自動化されたCI/CDパイプラインを採用し、コード品質の維持とデプロイの自動化を実現しています。

**主な特徴**:
- ✅ Pull Request時の自動チェック
- ✅ Staging/Production環境の自動デプロイ
- ✅ E2Eテストの自動実行
- ✅ カバレッジ要件の強制

---

## ワークフロー構成

```
.github/
├── workflows/
│   ├── pr-check.yml                      # PR時の基本チェック
│   ├── backend-staging.yml               # Staging: バックエンド
│   ├── backend-production.yml            # Production: バックエンド
│   ├── frontend-staging.yml              # Staging: フロントエンド
│   ├── frontend-production.yml           # Production: フロントエンド
│   ├── e2e-smoke-test-staging.yml        # Staging: 疎通確認
│   ├── e2e-smoke-test-production.yml     # Production: 疎通確認
│   ├── terraform-plan.yml                # Terraform Plan
│   ├── terraform-apply.yml               # Terraform Apply
│   ├── terraform-fmt.yml                 # Terraform Format
│   └── terraform-destroy.yml             # Terraform Destroy
│
├── actions/
│   ├── setup-node/                       # Node.js環境セットアップ
│   └── setup-python/                     # Python環境セットアップ
│
└── reusable-workflows/
    ├── reusable-backend-test.yml         # バックエンドテスト（再利用可能）
    └── reusable-frontend-test.yml        # フロントエンドテスト（再利用可能）
```

---

## Pull Request チェック

### pr-check.yml

**トリガー**: Pull Request作成・更新時

**実行内容**:
```yaml
name: PR Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  commit-message-check:
    name: Commit Message Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      # Conventional Commits形式をチェック
      - name: Check Commit Messages
        run: |
          git log --format=%B origin/${{ github.base_ref }}..HEAD | \
          grep -E '^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}'
  
  file-size-check:
    name: File Size Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # 大きなファイルの追加をチェック（5MB以上）
      - name: Check Large Files
        run: |
          git diff --name-only origin/${{ github.base_ref }} | \
          xargs -I {} sh -c 'test -f "{}" && test $(stat -f%z "{}") -gt 5242880 && echo "{}"'
  
  secret-scan:
    name: Secret Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      # シークレット漏洩をチェック（Gitleaks）
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## バックエンドCI/CD

### backend-staging.yml

**トリガー**: `develop`ブランチへのpush

**実行内容**:
```yaml
name: Backend Staging

on:
  push:
    branches: [develop]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-staging.yml'

jobs:
  test:
    name: Backend Tests (Staging)
    uses: ./.github/reusable-workflows/reusable-backend-test.yml
    with:
      environment: staging
      debug-mode: false
      strict-mode: false
      coverage-threshold: 60
    secrets: inherit
  
  deploy:
    name: Deploy to Render (Staging)
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Deploy
        run: |
          curl -X POST https://api.render.com/deploy/srv-xxx?key=${{ secrets.RENDER_DEPLOY_HOOK_STAGING }}
      
      - name: Wait for Deploy
        run: sleep 60
      
      - name: Send Slack Notification
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "Backend Staging Deploy: ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Backend Staging Deploy*\nStatus: ${{ job.status }}\nCommit: ${{ github.sha }}"
                  }
                }
              ]
            }
```

### backend-production.yml

**トリガー**: `main`ブランチへのpush

**実行内容**:
```yaml
name: Backend Production

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-production.yml'

jobs:
  test:
    name: Backend Tests (Production)
    uses: ./.github/reusable-workflows/reusable-backend-test.yml
    with:
      environment: production
      debug-mode: false
      strict-mode: true
      coverage-threshold: 80
    secrets: inherit
  
  deploy:
    name: Deploy to Render (Production)
    needs: test
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://your-api.onrender.com
    steps:
      - name: Trigger Render Deploy
        run: |
          curl -X POST https://api.render.com/deploy/srv-yyy?key=${{ secrets.RENDER_DEPLOY_HOOK_PRODUCTION }}
      
      - name: Wait for Deploy
        run: sleep 60
      
      - name: Health Check
        run: |
          for i in {1..10}; do
            if curl -f https://your-api.onrender.com/health/; then
              echo "Health check passed"
              exit 0
            fi
            echo "Attempt $i failed, retrying..."
            sleep 10
          done
          echo "Health check failed after 10 attempts"
          exit 1
```

---

## フロントエンドCI/CD

### frontend-staging.yml

**トリガー**: `develop`ブランチへのpush

**実行内容**:
```yaml
name: Frontend Staging

on:
  push:
    branches: [develop]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-staging.yml'

jobs:
  test:
    name: Frontend Tests (Staging)
    uses: ./.github/reusable-workflows/reusable-frontend-test.yml
    with:
      environment: staging
      strict-mode: false
      coverage-threshold: 60
      e2e-browsers: '["chromium"]'
    secrets: inherit
  
  deploy:
    name: Deploy to Cloudflare (Staging)
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: ./.github/actions/setup-node
      
      - name: Build
        working-directory: frontend
        env:
          VITE_BASE_API_URL: ${{ secrets.VITE_BASE_API_URL_STAGING }}
        run: npm run build
      
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: your-project-staging
          directory: frontend/dist
          branch: develop
```

### frontend-production.yml

**トリガー**: `main`ブランチへのpush

**実行内容**:
```yaml
name: Frontend Production

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-production.yml'

jobs:
  test:
    name: Frontend Tests (Production)
    uses: ./.github/reusable-workflows/reusable-frontend-test.yml
    with:
      environment: production
      strict-mode: true
      coverage-threshold: 70
      e2e-browsers: '["chromium", "firefox", "webkit"]'
    secrets: inherit
  
  deploy:
    name: Deploy to Cloudflare (Production)
    needs: test
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://your-app.pages.dev
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: ./.github/actions/setup-node
      
      - name: Build
        working-directory: frontend
        env:
          VITE_BASE_API_URL: ${{ secrets.VITE_BASE_API_URL_PRODUCTION }}
        run: npm run build
      
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: your-project-production
          directory: frontend/dist
          branch: main
```

---

## 再利用可能なワークフロー

### reusable-backend-test.yml

```yaml
name: Reusable Backend Test

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      debug-mode:
        required: false
        type: boolean
        default: false
      strict-mode:
        required: false
        type: boolean
        default: false
      coverage-threshold:
        required: false
        type: number
        default: 60

jobs:
  test:
    name: Backend Tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: ./.github/actions/setup-python
      
      - name: Install Dependencies
        working-directory: backend
        run: |
          pip install -r requirements.txt
          pip install coverage pytest-cov
      
      - name: Run Linting
        working-directory: backend
        run: |
          black --check .
          isort --check-only .
          flake8 .
      
      - name: Run Django Checks
        working-directory: backend
        run: python manage.py check
      
      - name: Run Tests
        working-directory: backend
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost/test_db
          DJANGO_SETTINGS_MODULE: config.settings.test
        run: |
          coverage run --source='.' manage.py test
          coverage report --fail-under=${{ inputs.coverage-threshold }}
          coverage xml
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend-${{ inputs.environment }}
```

### reusable-frontend-test.yml

```yaml
name: Reusable Frontend Test

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      strict-mode:
        required: false
        type: boolean
        default: false
      coverage-threshold:
        required: false
        type: number
        default: 60
      e2e-browsers:
        required: false
        type: string
        default: '["chromium"]'

jobs:
  test:
    name: Frontend Tests
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: ./.github/actions/setup-node
      
      - name: Run Linting
        working-directory: frontend
        run: |
          npm run lint
          npm run format:check
      
      - name: Type Check
        working-directory: frontend
        run: npm run type-check
      
      - name: Run Unit Tests
        working-directory: frontend
        run: npm run test:coverage
      
      - name: Check Coverage
        working-directory: frontend
        run: |
          COVERAGE=$(jq '.total.lines.pct' coverage/coverage-summary.json)
          if (( $(echo "$COVERAGE < ${{ inputs.coverage-threshold }}" | bc -l) )); then
            echo "Coverage $COVERAGE% is below threshold ${{ inputs.coverage-threshold }}%"
            exit 1
          fi
      
      - name: Build
        working-directory: frontend
        run: npm run build
      
      - name: Install Playwright
        working-directory: frontend
        run: npx playwright install --with-deps
      
      - name: Run E2E Tests
        working-directory: frontend
        env:
          E2E_BASE_URL: ${{ secrets.E2E_BASE_URL }}
          E2E_TEST_EMAIL: ${{ secrets.E2E_TEST_EMAIL }}
          E2E_TEST_PASSWORD: ${{ secrets.E2E_TEST_PASSWORD }}
        run: |
          BROWSERS='${{ inputs.e2e-browsers }}'
          for browser in $(echo $BROWSERS | jq -r '.[]'); do
            npm run test:e2e -- --project=$browser
          done
      
      - name: Upload E2E Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report-${{ inputs.environment }}
          path: frontend/playwright-report/
```

---

## カスタムアクション

### setup-node/action.yml

```yaml
name: Setup Node.js
description: Setup Node.js with caching

inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'

runs:
  using: composite
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install Dependencies
      shell: bash
      working-directory: frontend
      run: npm ci
```

### setup-python/action.yml

```yaml
name: Setup Python
description: Setup Python with caching

inputs:
  python-version:
    description: 'Python version'
    required: false
    default: '3.11'

runs:
  using: composite
  steps:
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}
        cache: 'pip'
        cache-dependency-path: backend/requirements.txt
    
    - name: Install Dependencies
      shell: bash
      working-directory: backend
      run: pip install -r requirements.txt
```

---

## 環境変数管理

### GitHub Environment Variables（Terraform管理）

**terraform/modules/github/main.tf**:
```hcl
resource "github_actions_environment_variable" "staging_api_url" {
  repository      = var.repository_name
  environment     = "staging"
  variable_name   = "VITE_BASE_API_URL"
  value           = var.staging_api_url
}

resource "github_actions_environment_variable" "production_api_url" {
  repository      = var.repository_name
  environment     = "production"
  variable_name   = "VITE_BASE_API_URL"
  value           = var.production_api_url
}

resource "github_actions_environment_secret" "e2e_test_email" {
  repository      = var.repository_name
  environment     = "staging"
  secret_name     = "E2E_TEST_EMAIL"
  plaintext_value = var.e2e_test_email
}
```

### ワークフローでの使用

```yaml
- name: Build
  env:
    VITE_BASE_API_URL: ${{ vars.VITE_BASE_API_URL }}  # Environment Variable
    E2E_TEST_EMAIL: ${{ secrets.E2E_TEST_EMAIL }}     # Environment Secret
  run: npm run build
```

---

## Smoke Tests

### e2e-smoke-test-staging.yml

**トリガー**: 手動実行（workflow_dispatch）

**目的**: Staging環境の疎通確認

```yaml
name: E2E Smoke Test (Staging)

on:
  workflow_dispatch:

jobs:
  smoke-test:
    name: Smoke Test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: ./.github/actions/setup-node
      
      - name: Install Playwright
        working-directory: frontend
        run: npx playwright install --with-deps chromium
      
      - name: Run Smoke Tests
        working-directory: frontend
        env:
          E2E_BASE_URL: ${{ secrets.E2E_BASE_URL_STAGING }}
          E2E_TEST_EMAIL: ${{ secrets.E2E_TEST_EMAIL }}
          E2E_TEST_PASSWORD: ${{ secrets.E2E_TEST_PASSWORD }}
        run: npm run test:e2e:smoke
      
      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: smoke-test-results-staging
          path: frontend/playwright-report/
```

**Smoke Tests定義**（frontend/tests/e2e/smoke.spec.ts）:
```typescript
import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('should load homepage', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Your App/);
  });
  
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', process.env.E2E_TEST_EMAIL!);
    await page.fill('[name="password"]', process.env.E2E_TEST_PASSWORD!);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/dashboard/);
  });
  
  test('should access API health endpoint', async ({ request }) => {
    const response = await request.get(`${process.env.E2E_BASE_URL}/health/`);
    expect(response.ok()).toBeTruthy();
  });
});
```

---

## デプロイ戦略

### テスト戦略の違い

| 環境 | カバレッジ | E2Eブラウザ | Strict Mode | 理由 |
|------|-----------|------------|-------------|------|
| **Staging** | 60%+ | Chromiumのみ | false | 開発速度を優先 |
| **Production** | 70-80%+ | 全ブラウザ | true | 品質を最優先 |

### デプロイフロー

```
1. コード変更
   ↓
2. Pull Request作成
   └─ pr-check.yml 実行
      ├─ Commit message check
      ├─ File size check
      └─ Secret scan
   ↓
3. developブランチにマージ
   └─ backend-staging.yml, frontend-staging.yml 実行
      ├─ Lint & Format
      ├─ Tests (60%+ coverage)
      ├─ Build
      ├─ E2E tests (Chromium)
      └─ デプロイ
   ↓
4. Render & Cloudflare が自動デプロイ
   ↓
5. Smoke Test実行（手動、オプション）
   ↓
6. mainブランチにマージ
   └─ backend-production.yml, frontend-production.yml 実行
      ├─ Lint & Format
      ├─ Tests (70-80%+ coverage)
      ├─ Build
      ├─ E2E tests (全ブラウザ)
      └─ デプロイ
   ↓
7. Render & Cloudflare が自動デプロイ
   ↓
8. Health Check（自動）
```

---

## トラブルシューティング

### CI/CDが失敗する

```bash
# 確認項目
1. ログを確認
   → GitHub Actions タブ → 失敗したワークフロー → ログを確認

2. ローカルで再現
   → 同じコマンドをローカルで実行して問題を特定

3. キャッシュをクリア
   → GitHub Actions → Caches → 該当キャッシュを削除
```

### カバレッジが不足

```bash
# カバレッジを上げる
1. 未テストのファイルを特定
   → coverage report で確認

2. テストを追加
   → 重要な関数・クラスを優先

3. カバレッジ閾値を調整（一時的）
   → coverage-threshold を下げる（非推奨）
```

### E2Eテストが失敗

```bash
# デバッグ方法
1. Playwright レポートを確認
   → Artifacts → playwright-report をダウンロード

2. ローカルで実行
   → npm run test:e2e -- --debug

3. スクリーンショットを確認
   → test-results/ ディレクトリ
```

### デプロイが失敗

```bash
# 確認項目
1. Deploy Hookが正しいか
   → Render Dashboard → Deploy Hook URL を確認

2. 環境変数が設定されているか
   → GitHub Settings → Environments → Variables/Secrets を確認

3. Health Checkが成功するか
   → curl https://your-api.onrender.com/health/
```

---

## ベストプラクティス

### 1. 適切なトリガー設定

```yaml
# ✅ 良い例: 関連ファイルのみでトリガー
on:
  push:
    branches: [develop]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-staging.yml'

# ❌ 悪い例: すべての変更でトリガー
on:
  push:
    branches: [develop]
```

### 2. 再利用可能なワークフローを活用

```yaml
# ✅ 良い例: 再利用可能なワークフローを使用
jobs:
  test:
    uses: ./.github/reusable-workflows/reusable-backend-test.yml
    with:
      environment: staging
      coverage-threshold: 60

# ❌ 悪い例: すべてのステップを重複して記述
```

### 3. 環境変数の管理

```yaml
# ✅ 良い例: Terraformで管理
resource "github_actions_environment_variable" "api_url" {
  repository    = var.repository_name
  environment   = "staging"
  variable_name = "VITE_BASE_API_URL"
  value         = var.staging_api_url
}

# ❌ 悪い例: 手動でGitHub UIから設定
```

### 4. Secrets の保護

```yaml
# ✅ 良い例: Secretsを環境変数として参照
env:
  API_KEY: ${{ secrets.API_KEY }}

# ❌ 悪い例: Secretsをログに出力
run: echo "API Key: ${{ secrets.API_KEY }}"
```

---

## まとめ

| 項目 | 実装方法 |
|------|---------|
| **CI** | GitHub Actions（Lint, Test, Build） |
| **CD** | Render + Cloudflare Pages（自動デプロイ） |
| **テスト戦略** | Staging: 60%+, Production: 70-80%+ |
| **E2E** | Playwright（Staging: Chromium、Production: 全ブラウザ） |
| **環境変数** | Terraform管理 |
| **通知** | Slack Webhook |

この設計により、以下を実現しています：

✅ **自動化**: コミットからデプロイまで完全自動化  
✅ **品質保証**: カバレッジ要件と複数ブラウザでのE2E  
✅ **高速フィードバック**: PRチェックで早期発見  
✅ **安全なデプロイ**: 段階的デプロイ（Staging → Production）  
✅ **再利用性**: カスタムアクションと再利用可能なワークフロー  
✅ **保守性**: Terraformによる環境変数管理