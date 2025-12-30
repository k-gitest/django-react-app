# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GitHub Secrets/Variables 管理モジュール
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GitHub Environment 作成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

resource "github_repository_environment" "main" {
  repository  = var.repository_name
  environment = var.environment
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Environment Variables（公開情報）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# フロントエンド用 - バックエンドURL
resource "github_actions_environment_variable" "vite_base_api_url" {
  repository    = var.repository_name
  environment   = github_repository_environment.main.environment
  variable_name = "VITE_BASE_API_URL"
  value         = var.backend_url
}

# フロントエンド用 - ストレージURL（静的アセット用）
resource "github_actions_environment_variable" "vite_storage_url" {
  repository    = var.repository_name
  environment   = github_repository_environment.main.environment
  variable_name = "VITE_STORAGE_URL"
  value         = var.storage_url
}

# バックエンド用 - DEBUG設定
resource "github_actions_environment_variable" "debug" {
  repository    = var.repository_name
  environment   = github_repository_environment.main.environment
  variable_name = "DEBUG"
  value         = var.debug_mode
}

# バックエンド用 - フロントエンドURL（CORS用）
resource "github_actions_environment_variable" "front_url" {
  repository    = var.repository_name
  environment   = github_repository_environment.main.environment
  variable_name = "FRONT_URL"
  value         = var.frontend_url
}

# バックエンド用 - ストレージバケット名
resource "github_actions_environment_variable" "aws_storage_bucket_name" {
  repository    = var.repository_name
  environment   = github_repository_environment.main.environment
  variable_name = "AWS_STORAGE_BUCKET_NAME"
  value         = var.storage_bucket_name
}

# バックエンド用 - S3エンドポイント
resource "github_actions_environment_variable" "aws_s3_endpoint_url" {
  repository    = var.repository_name
  environment   = github_repository_environment.main.environment
  variable_name = "AWS_S3_ENDPOINT_URL"
  value         = var.s3_endpoint_url
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Environment Secrets（機密情報）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Django Secret Key
resource "github_actions_environment_secret" "secret_key" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "SECRET_KEY"
  plaintext_value = var.secret_key
}

# PostgreSQL接続情報
resource "github_actions_environment_secret" "pgdatabase" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "PGDATABASE"
  plaintext_value = var.pgdatabase
}

resource "github_actions_environment_secret" "pguser" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "PGUSER"
  plaintext_value = var.pguser
}

resource "github_actions_environment_secret" "pgpassword" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "PGPASSWORD"
  plaintext_value = var.pgpassword
}

resource "github_actions_environment_secret" "pghost" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "PGHOST"
  plaintext_value = var.pghost
}

resource "github_actions_environment_secret" "pgport" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "PGPORT"
  plaintext_value = var.pgport
}

# Backblaze B2（機密情報）
resource "github_actions_environment_secret" "aws_access_key_id" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "AWS_ACCESS_KEY_ID"  # Django storages用
  plaintext_value = var.b2_application_key_id
}

resource "github_actions_environment_secret" "aws_secret_access_key" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "AWS_SECRET_ACCESS_KEY"  # Django storages用
  plaintext_value = var.b2_application_key
}

# E2Eテスト用の認証情報
resource "github_actions_environment_secret" "e2e_test_email" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "E2E_TEST_EMAIL"
  plaintext_value = var.e2e_test_email
}

resource "github_actions_environment_secret" "e2e_test_password" {
  repository      = var.repository_name
  environment     = github_repository_environment.main.environment
  secret_name     = "E2E_TEST_PASSWORD"
  plaintext_value = var.e2e_test_password
}
