# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Render モジュール - リソース定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

terraform {
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.3"
    }
  }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Render モジュール - リソース定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Render Web Service（Django バックエンド）
resource "render_web_service" "backend" {
  name   = var.app_name
  plan   = "free"
  region = var.region
  
  # ランタイム設定
  runtime_source = {
    docker = {
      auto_deploy = true
      branch      = var.branch
      repo_url    = var.github_repo_url
      
      # Dockerの詳細設定はここ
      docker_context  = "backend"
      dockerfile_path = "backend/Dockerfile"
      
      # ビルドフィルター（特定の変更時のみデプロイしたい場合）
      build_filter = {
        paths         = ["backend/**"]
        ignored_paths = []
      }
    }
  }
  
  # 環境変数
  env_vars = merge(
    {
      "DATABASE_URL" = {
        value = var.database_url
      }
      "AWS_S3_ENDPOINT_URL" = {
        value = var.s3_endpoint
      }
      "AWS_STORAGE_BUCKET_NAME" = {
        value = var.s3_bucket_name
      }
      "AWS_S3_REGION_NAME" = {
        value = "us-west-004"
      }
      "AWS_S3_USE_SSL" = {
        value = "True"
      }
      "DJANGO_SETTINGS_MODULE" = {
        value = "config.settings"
      }
      "PYTHONUNBUFFERED" = {
        value = "1"
      }
    },
    # 動的な変数（var.env_vars）も、値（string）をオブジェクト形式に変換してマージします
    { for k, v in var.env_vars : k => { value = v } }
  )
}