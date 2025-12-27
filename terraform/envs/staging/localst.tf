# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ローカル変数（命名規則の統一）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

locals {
  # 基本情報
  project_name = var.project_name
  environment  = var.environment
  
  # 命名規則: {project_name}-{component}-{environment}
  neon_project_name      = "${local.project_name}-db-${local.environment}"
  backblaze_bucket_name  = "${local.project_name}-assets-${local.environment}"
  cloudflare_pages_name  = "${local.project_name}-frontend-${local.environment}"
  render_app_name        = "${local.project_name}-backend-${local.environment}"
  
  # 環境ごとの設定
  is_production = local.environment == "production"
  debug_mode    = local.is_production ? "False" : "True"
  
  # 共通タグ
  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    ManagedBy   = "Terraform"
  }
}