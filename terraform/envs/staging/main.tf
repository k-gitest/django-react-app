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
    # Upstash Redis
    "UPSTASH_REDIS_REST_URL"   = module.upstash.redis_rest_url
    "UPSTASH_REDIS_REST_TOKEN" = module.upstash.redis_rest_token
    # Upstash Vector
    "UPSTASH_VECTOR_REST_URL"   = module.upstash.vector_endpoint
    "UPSTASH_VECTOR_REST_TOKEN" = module.upstash.vector_token
    # QStash
    "QSTASH_TOKEN"      = module.upstash.qstash_token
    "QSTASH_TOPIC_NAME" = module.upstash.qstash_topic_name
    # API Keys
    "GEMINI_API_KEY"           = var.gemini_api_key
    "RESEND_API_KEY"           = var.resend_api_key
    # Django Secret Key (random_password から取得)
    "SECRET_KEY"               = random_password.django_secret_key.result
  }
}

# --- Cache & Vector (Upstash) ---
module "upstash" {
  source      = "../../modules/upstash"
  environment = local.environment
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

  # Cloudflare デプロイ用に追加
  cloudflare_project_name = module.cloudflare.pages_project_name
  cloudflare_account_id   = var.cloudflare_account_id

  # Gemini
  gemini_api_key    = var.gemini_api_key

  # Resend
  resend_api_key    = var.resend_api_key

  # Upstash
  upstash_redis_rest_url   = module.upstash.redis_rest_url
  upstash_redis_rest_token = module.upstash.redis_rest_token
  upstash_vector_endpoint  = module.upstash.vector_endpoint
  upstash_vector_token     = module.upstash.vector_token
  upstash_qstash_token      = module.upstash.qstash_token
  upstash_qstash_topic_name = module.upstash.qstash_topic_name
}
