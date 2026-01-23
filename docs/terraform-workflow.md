# Terraform + デプロイワークフロー詳細ガイド

## 目次

- [概要](#概要)
- [アーキテクチャ](#アーキテクチャ)
- [Terraformワークフロー](#terraformワークフロー)
- [terraform-plan.yml](#terraform-planyml)
- [terraform-apply.yml](#terraform-applyyml)
- [terraform-destroy.yml](#terraform-destroyyml)
- [デプロイ戦略](#デプロイ戦略)
- [Backend/Frontend Deployワークフロー](#backendfrontend-deployワークフロー)
- [Health Check](#health-check)
- [実際の運用フロー](#実際の運用フロー)
- [GitHub Environment設定](#github-environment設定)
- [トラブルシューティング](#トラブルシューティング)
- [ベストプラクティス](#ベストプラクティス)

---

## 概要

**Terraform Cloud**によるインフラ管理と**GitHub Actions**による自動デプロイを組み合わせ、安全で再現性の高いデプロイフローを実現しています。

**主な特徴**:
- ✅ インフラのコード化（IaC）
- ✅ Pull Requestでの変更プレビュー
- ✅ 段階的デプロイ（Staging → Production）
- ✅ ゼロダウンタイムデプロイ

---

## アーキテクチャ

### フロー全体

```
1. terraform/** 変更 + PR作成
   └─ terraform-plan.yml（自動実行）
      └─ Staging/Production Plan をPRにコメント

2. PR マージ（develop または main）
   └─ 通常のCI/CDワークフロー実行
      （backend-staging.yml, frontend-staging.yml等）

3. terraform-apply.yml（手動実行）
   ├─ Terraform Apply（インフラ変更）
   │  └─ GitHub Environment Variables 更新
   └─ デプロイ戦略の選択
      ├─ Parallel: Backend + Frontend 同時デプロイ
      └─ Sequential: Backend → Health Check → Frontend

4. アプリケーションデプロイ（自動トリガー）
   ├─ Backend Deployment（Render）
   └─ Frontend Deployment（Cloudflare Pages）
```

---

## Terraformワークフロー

```
.github/workflows/
├── terraform-plan.yml      # PR作成時に自動実行
├── terraform-apply.yml     # 手動実行（インフラ構築）
├── terraform-fmt.yml       # フォーマットチェック
└── terraform-destroy.yml   # 緊急時の環境削除
```

---

## terraform-plan.yml

### 概要

**トリガー**: Pull Request作成・更新時（terraform/配下の変更）

**目的**: インフラ変更のプレビュー

### 実装

```yaml
name: Terraform Plan

on:
  pull_request:
    paths:
      - 'terraform/**'
      - '.github/workflows/terraform-plan.yml'

jobs:
  plan-staging:
    name: Plan (Staging)
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}
      
      - name: Terraform Init
        working-directory: terraform/environments/staging
        run: terraform init
      
      - name: Terraform Plan
        working-directory: terraform/environments/staging
        id: plan
        run: terraform plan -no-color -out=tfplan
        continue-on-error: true
      
      - name: Comment Plan on PR
        uses: actions/github-script@v7
        with:
          script: |
            const output = `### Terraform Plan (Staging)
            
            \`\`\`
            ${{ steps.plan.outputs.stdout }}
            \`\`\`
            
            *Pushed by: @${{ github.actor }}*`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });
  
  plan-production:
    name: Plan (Production)
    runs-on: ubuntu-latest
    
    steps:
      # Staging と同様
      ...
```

### Plan結果の例

```terraform
Terraform will perform the following actions:

  # github_actions_environment_variable.staging_api_url will be updated in-place
  ~ resource "github_actions_environment_variable" "staging_api_url" {
      ~ value = "https://old-api.onrender.com" -> "https://new-api.onrender.com"
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

---

## terraform-apply.yml

### 概要

**トリガー**: 手動実行（workflow_dispatch）

**目的**: インフラ構築・変更の適用

### 実装

```yaml
name: Terraform Apply

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to apply'
        required: true
        type: choice
        options:
          - staging
          - production
      deployment_strategy:
        description: 'Deployment strategy'
        required: true
        type: choice
        options:
          - parallel
          - sequential
        default: sequential
      auto_approve:
        description: 'Auto approve (use with caution)'
        required: false
        type: boolean
        default: false

jobs:
  terraform-apply:
    name: Terraform Apply (${{ inputs.environment }})
    runs-on: ubuntu-latest
    environment: terraform-${{ inputs.environment }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}
      
      - name: Terraform Init
        working-directory: terraform/environments/${{ inputs.environment }}
        run: terraform init
      
      - name: Terraform Apply
        working-directory: terraform/environments/${{ inputs.environment }}
        run: |
          if [ "${{ inputs.auto_approve }}" = "true" ]; then
            terraform apply -auto-approve
          else
            terraform apply
          fi
      
      - name: Get Outputs
        id: outputs
        working-directory: terraform/environments/${{ inputs.environment }}
        run: |
          echo "backend_url=$(terraform output -raw backend_url)" >> $GITHUB_OUTPUT
          echo "frontend_url=$(terraform output -raw frontend_url)" >> $GITHUB_OUTPUT
  
  deploy:
    name: Deploy Applications
    needs: terraform-apply
    runs-on: ubuntu-latest
    
    steps:
      - name: Parallel Deployment
        if: inputs.deployment_strategy == 'parallel'
        run: |
          echo "Triggering parallel deployment..."
          # Backend と Frontend を同時デプロイ
          curl -X POST ${{ secrets.BACKEND_DEPLOY_HOOK }} &
          curl -X POST ${{ secrets.FRONTEND_DEPLOY_HOOK }} &
          wait
      
      - name: Sequential Deployment
        if: inputs.deployment_strategy == 'sequential'
        run: |
          echo "Triggering sequential deployment..."
          
          # 1. Backend デプロイ
          curl -X POST ${{ secrets.BACKEND_DEPLOY_HOOK }}
          
          # 2. Health Check（最大5分）
          for i in {1..30}; do
            if curl -f ${{ needs.terraform-apply.outputs.backend_url }}/health/; then
              echo "Backend is healthy"
              break
            fi
            echo "Waiting for backend... ($i/30)"
            sleep 10
          done
          
          # 3. Frontend デプロイ
          curl -X POST ${{ secrets.FRONTEND_DEPLOY_HOOK }}
      
      - name: Send Notification
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "Terraform Apply & Deploy: ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Terraform Apply & Deploy*\nEnvironment: ${{ inputs.environment }}\nStrategy: ${{ inputs.deployment_strategy }}\nStatus: ${{ job.status }}"
                  }
                }
              ]
            }
```

### 手動実行方法

```
1. GitHub → Actions タブ
2. "Terraform Apply" を選択
3. "Run workflow" をクリック
4. パラメータを選択
   - Environment: staging / production
   - Deployment strategy: parallel / sequential
   - Auto approve: false（推奨）
5. "Run workflow" を実行
```

---

## terraform-destroy.yml

### 概要

**トリガー**: 手動実行（workflow_dispatch）

**目的**: 緊急時の環境削除

**注意**: Productionは安全機能で保護

### 実装

```yaml
name: Terraform Destroy

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to destroy'
        required: true
        type: choice
        options:
          - staging
          # production は選択肢に含めない（安全機能）
      confirmation:
        description: 'Type "DESTROY" to confirm'
        required: true
        type: string

jobs:
  terraform-destroy:
    name: Terraform Destroy (${{ inputs.environment }})
    runs-on: ubuntu-latest
    environment: terraform-${{ inputs.environment }}
    
    steps:
      - name: Validate Confirmation
        run: |
          if [ "${{ inputs.confirmation }}" != "DESTROY" ]; then
            echo "Error: Confirmation text does not match"
            exit 1
          fi
      
      - name: Block Production Destroy
        if: inputs.environment == 'production'
        run: |
          echo "Error: Production environment cannot be destroyed via workflow"
          echo "Please use Terraform Cloud UI or CLI manually"
          exit 1
      
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}
      
      - name: Terraform Init
        working-directory: terraform/environments/${{ inputs.environment }}
        run: terraform init
      
      - name: Terraform Destroy
        working-directory: terraform/environments/${{ inputs.environment }}
        run: terraform destroy -auto-approve
      
      - name: Send Notification
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "⚠️ Terraform Destroy: ${{ inputs.environment }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*⚠️ Terraform Destroy*\nEnvironment: ${{ inputs.environment }}\nStatus: ${{ job.status }}\nTriggered by: @${{ github.actor }}"
                  }
                }
              ]
            }
```

---

## デプロイ戦略

### Parallel（並列実行）

**推奨環境**: Staging

```
Terraform Apply 完了
  ↓
┌─────────────┬─────────────┐
│  Backend    │  Frontend   │ ← 同時実行
│  Deploy     │  Deploy     │
└─────────────┴─────────────┘
  ↓             ↓
完了（2-3分）
```

**メリット**:
- ⚡ 高速（2-3分で完了）
- 🎯 開発速度を優先

**デメリット**:
- ⚠️ Frontend が先に完成する可能性
- ⚠️ Backend APIエラーが発生する可能性

**適用例**:
```bash
# Staging環境で使用
Environment: staging
Deployment strategy: parallel
```

---

### Sequential（順次実行）

**推奨環境**: Production

```
Terraform Apply 完了
  ↓
Backend Deploy
  ↓
Health Check（最大5分）
  ↓ ✅ Healthy
Frontend Deploy
  ↓
完了（5-7分）
```

**メリット**:
- 🛡️ 安全（ゼロダウンタイム）
- ✅ Backend が健全な状態でFrontendデプロイ

**デメリット**:
- ⏱️ 時間がかかる（5-7分）

**適用例**:
```bash
# Production環境で使用
Environment: production
Deployment strategy: sequential
```

---

## Backend/Frontend Deployワークフロー

### backend-deploy.yml

**トリガー**: Terraform Applyから呼び出し

```yaml
name: Backend Deploy

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string

jobs:
  deploy:
    name: Deploy Backend
    runs-on: ubuntu-latest
    
    steps:
      - name: Trigger Render Deploy
        run: |
          curl -X POST https://api.render.com/deploy/srv-xxx?key=${{ secrets.RENDER_DEPLOY_HOOK }}
      
      - name: Wait for Deploy
        run: sleep 60
```

### frontend-deploy.yml

**トリガー**: Terraform Applyから呼び出し

```yaml
name: Frontend Deploy

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string

jobs:
  deploy:
    name: Deploy Frontend
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: ./.github/actions/setup-node
      
      - name: Build
        working-directory: frontend
        env:
          VITE_BASE_API_URL: ${{ vars.VITE_BASE_API_URL }}
        run: npm run build
      
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: your-project-${{ inputs.environment }}
          directory: frontend/dist
```

---

## Health Check

### 実装

**backend/health/views.py**:
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health Checkエンドポイント
    
    DB接続とアプリケーションの健全性を確認
    """
    try:
        # DB接続確認
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return Response({
            "status": "healthy",
            "database": "connected"
        })
    except Exception as e:
        return Response({
            "status": "unhealthy",
            "error": str(e)
        }, status=503)
```

### GitHub Actionsでの使用

```yaml
- name: Health Check
  run: |
    for i in {1..30}; do
      if curl -f https://your-api.onrender.com/health/; then
        echo "Health check passed"
        exit 0
      fi
      echo "Attempt $i/30 failed, retrying..."
      sleep 10
    done
    echo "Health check failed after 30 attempts"
    exit 1
```

---

## 実際の運用フロー

### シナリオ1: 新しい環境変数の追加

```bash
1. .env.example に環境変数を追加
   VITE_NEW_FEATURE_FLAG=true

2. Terraform に反映
   # terraform/modules/github/main.tf
   resource "github_actions_environment_variable" "new_feature_flag" {
     repository    = var.repository_name
     environment   = "staging"
     variable_name = "VITE_NEW_FEATURE_FLAG"
     value         = "true"
   }

3. PR作成
   → terraform-plan.yml が自動実行
   → Plan結果がPRにコメント

4. レビュー & マージ（develop）

5. terraform-apply.yml を手動実行
   Environment: staging
   Deployment strategy: parallel
   Auto approve: false

6. GitHub Environment Variables が更新される

7. 自動デプロイ開始
   - Backend: Render
   - Frontend: Cloudflare Pages

8. 完了 🎉
```

---

### シナリオ2: データベース設定の変更

```bash
1. Neon モジュールを編集
   # terraform/modules/neon/main.tf
   resource "neon_branch" "staging" {
     name          = "staging"
     compute_units = 0.5  # 変更: 0.25 → 0.5
   }

2. PR作成
   → Staging/Production Plan が表示

3. レビュー & マージ（develop）

4. terraform-apply.yml を手動実行（Staging）
   Environment: staging
   Deployment strategy: parallel

5. Staging で動作確認
   - DB接続確認
   - パフォーマンステスト

6. main ブランチにマージ

7. terraform-apply.yml を手動実行（Production）
   Environment: production
   Deployment strategy: sequential  # 安全優先

8. Production デプロイ完了 🎉
```

---

### シナリオ3: 緊急時のロールバック

```bash
1. 問題発生を検知
   - モニタリングアラート
   - ユーザーからの報告

2. 前回のコミットにrevert
   git revert HEAD
   git push origin main

3. terraform-apply.yml を手動実行
   Environment: production
   Deployment strategy: sequential
   Auto approve: false  # 念のため確認

4. デプロイ完了
   - Health Check成功を確認
   - モニタリングで正常性確認

5. 根本原因の調査
   - ログ分析
   - エラー追跡

6. 修正 & 再デプロイ
```

---

## GitHub Environment設定

### terraform-staging

**Protection rules**:
```
Required reviewers: 0人
Wait timer: なし
```

**理由**: Staging環境は開発速度を優先

---

### terraform-production

**Protection rules**:
```
Required reviewers: 1人以上
Wait timer: 0分（任意）
```

**理由**: Production環境は安全性を優先

---

### 設定方法（Terraform）

```hcl
# terraform/modules/github/main.tf

resource "github_repository_environment" "terraform_staging" {
  repository  = var.repository_name
  environment = "terraform-staging"
}

resource "github_repository_environment" "terraform_production" {
  repository  = var.repository_name
  environment = "terraform-production"
  
  reviewers {
    users = [var.admin_github_user_id]
  }
}
```

---

## トラブルシューティング

### Terraform Planが失敗する

```bash
# 確認項目
1. Terraform Cloud設定
   → https://app.terraform.io/
   → Workspace設定を確認

2. API Tokenが有効か
   → TF_API_TOKEN を再生成

3. terraform init が成功するか
   → ローカルで terraform init を実行

4. 構文エラーを確認
   → terraform validate
```

### Terraform Applyが失敗する

```bash
# 確認項目
1. Plan結果を確認
   → 期待通りの変更内容か

2. ロックが発生していないか
   → Terraform Cloud → Workspace → Unlock

3. 依存関係の問題
   → 依存するリソースが存在するか確認

4. ログを確認
   → Terraform Cloud → Runs → ログ詳細
```

### デプロイが失敗する

```bash
# 確認項目
1. Deploy Hookが正しいか
   → Render Dashboard → Deploy Hook URL

2. Health Checkが通るか
   → curl https://your-api.onrender.com/health/

3. 環境変数が更新されているか
   → GitHub Settings → Environments → Variables

4. Build が成功しているか
   → Render/Cloudflare のログを確認
```

---

## ベストプラクティス

### 1. 段階的デプロイ

```bash
# ✅ 良い例: Staging → Production
1. Staging で terraform apply
2. 動作確認
3. Production で terraform apply

# ❌ 悪い例: いきなりProduction
1. Production で terraform apply
```

### 2. Plan結果の確認

```bash
# ✅ 良い例: Plan結果を必ず確認
1. PR作成
2. Plan結果をレビュー
3. 期待通りか確認
4. Apply実行

# ❌ 悪い例: Plan結果を確認せずApply
1. PR作成
2. 即Apply（危険）
```

### 3. Sequential デプロイ（Production）

```bash
# ✅ 良い例: Production は Sequential
Environment: production
Deployment strategy: sequential

# ❌ 悪い例: Production で Parallel
Environment: production
Deployment strategy: parallel（リスク）
```

### 4. Auto Approveの使用

```bash
# ✅ 良い例: 通常はfalse
Auto approve: false

# ⚠️ 注意: 緊急時のみtrue
Auto approve: true（慎重に使用）
```

---

## まとめ

| 項目 | 実装方法 |
|------|---------|
| **IaC** | Terraform Cloud |
| **Plan** | PR作成時に自動実行 |
| **Apply** | 手動実行（承認フロー） |
| **デプロイ戦略** | Parallel（Staging）/ Sequential（Production） |
| **Health Check** | Backend デプロイ後に自動実行 |
| **環境管理** | GitHub Environment（Terraform管理） |

この設計により、以下を実現しています：

✅ **インフラのコード化**: 再現性の高いインフラ管理  
✅ **変更のプレビュー**: PRでPlan結果を確認  
✅ **安全なデプロイ**: 段階的デプロイと承認フロー  
✅ **ゼロダウンタイム**: Sequential デプロイとHealth Check  
✅ **自動化**: Apply後のデプロイを自動実行  
✅ **保守性**: Terraformによる一元管理