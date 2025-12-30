# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Staging環境 - メイン設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Django SECRET_KEY の生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

resource "random_password" "django_secret_key" {
  length  = 50
  special = true
  
  lifecycle {
    ignore_changes = [
      length,
      special,
    ]
  }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# E2Eテスト用パスワード生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

resource "random_password" "e2e_test_password" {
  length  = 16
  special = false  # E2Eテスト用なのでシンプルに
  
  lifecycle {
    ignore_changes = [
      length,
      special,
    ]
  }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Modules の呼び出し
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# --- Database (Neon) ---
module "neon" {
  source       = "../../modules/neon"
  project_name = local.neon_project_name
  branch_name  = "main"
  region_id    = var.neon_region
}

# --- Storage (Backblaze B2) ---
module "backblaze" {
  source      = "../../modules/backblaze"
  bucket_name = local.backblaze_bucket_name
  bucket_type = "allPrivate"  # または "allPublic"
}

# --- Frontend (Cloudflare Pages) ---
module "cloudflare" {
  source             = "../../modules/cloudflare"
  account_id         = var.cloudflare_account_id
  pages_project_name = local.cloudflare_pages_name
  production_branch  = "main"
  github_repo_url    = var.github_repo_url
}

# --- Backend (Render) ---
module "render" {
  source          = "../../modules/render"
  owner_id        = var.render_owner_id
  app_name        = local.render_app_name
  github_repo_url = var.github_repo_url
  branch          = "main"
  region          = var.render_region
  
  # モジュール間の依存関係
  database_url   = module.neon.connection_uri
  s3_endpoint    = module.backblaze.s3_endpoint
  s3_bucket_name = module.backblaze.bucket_name
  
  # 環境変数
  env_vars = {
    "DEBUG"                   = local.debug_mode
    "ENVIRONMENT"             = local.environment
    "FRONT_URL"               = module.cloudflare.pages_url
    "AWS_ACCESS_KEY_ID"       = module.backblaze.application_key_id
    "AWS_SECRET_ACCESS_KEY"   = module.backblaze.application_key
    "AWS_STORAGE_BUCKET_NAME" = module.backblaze.bucket_name
    "AWS_S3_ENDPOINT_URL"     = module.backblaze.s3_endpoint
  }
}

# --- GitHub Secrets/Variables ---
module "github_secrets" {
  source = "../../modules/github"
  
  repository_name = local.github_repository
  environment     = local.environment
  
  # URL設定
  backend_url  = module.render.service_url
  frontend_url = module.cloudflare.pages_url
  
  # ストレージ設定
  storage_url         = local.storage_public_url
  storage_bucket_name = module.backblaze.bucket_name
  s3_endpoint_url     = module.backblaze.s3_endpoint
  
  # Django設定
  debug_mode = local.debug_mode
  secret_key = random_password.django_secret_key.result
  
  # PostgreSQL（Neonから取得）
  pgdatabase = module.neon.database_name
  pguser     = module.neon.role_name
  pgpassword = module.neon.password
  pghost     = module.neon.host
  pgport     = "5432"
  
  # Backblaze B2
  b2_application_key_id = module.backblaze.application_key_id
  b2_application_key    = module.backblaze.application_key
  
  # E2Eテスト用認証情報
  e2e_test_email    = var.e2e_test_email
  e2e_test_password = random_password.e2e_test_password.result
}
