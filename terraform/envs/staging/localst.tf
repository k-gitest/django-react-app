# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Staging環境 - ローカル変数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

locals {
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # 基本設定
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  project_name = var.project_name
  environment  = var.environment
  
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # GitHub設定
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  # "https://github.com/username/repo" → "username/repo"
  github_repository = regex(
    "github\\.com/([^/]+/[^/]+?)(?:\\.git)?$",
    var.github_repo_url
  )[0]
  
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # 環境別設定
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  debug_mode = var.environment == "production" ? "False" : "True"
  
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # リソース命名規則: {project_name}-{component}-{environment}
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  neon_project_name      = "${local.project_name}-db-${local.environment}"
  backblaze_bucket_name  = "${local.project_name}-assets-${local.environment}"
  cloudflare_pages_name  = "${local.project_name}-frontend-${local.environment}"
  render_app_name        = "${local.project_name}-backend-${local.environment}"
  
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # ストレージURL構築
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  # Backblaze B2の公開URL（フロントエンド用）
  # 形式: https://f004.backblazeb2.com/file/{bucket_name}/
  storage_public_url = "https://f004.backblazeb2.com/file/${local.backblaze_bucket_name}"
}
