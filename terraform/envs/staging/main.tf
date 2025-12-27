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
    "AWS_ACCESS_KEY_ID"       = module.backblaze.application_key_id
    "AWS_SECRET_ACCESS_KEY"   = module.backblaze.application_key
  }
}