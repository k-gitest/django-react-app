# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Staging環境 - 出力値
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Neon（データベース）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "neon_project_id" {
  description = "Neon project ID"
  value       = module.neon.project_id
}

output "neon_project_name" {
  description = "Neon project name"
  value       = local.neon_project_name
}

output "neon_database_host" {
  description = "Neon database host"
  value       = module.neon.host
}

output "neon_database_name" {
  description = "Neon database name"
  value       = module.neon.database_name
}

output "neon_connection_uri" {
  description = "Neon PostgreSQL connection URI (sensitive)"
  value       = module.neon.connection_uri
  sensitive   = true
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Backblaze B2（ストレージ）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "backblaze_bucket_name" {
  description = "Backblaze B2 bucket name"
  value       = module.backblaze.bucket_name
}

output "backblaze_s3_endpoint" {
  description = "Backblaze B2 S3-compatible endpoint"
  value       = module.backblaze.s3_endpoint
}

output "backblaze_application_key_id" {
  description = "Backblaze B2 Application Key ID (sensitive)"
  value       = module.backblaze.application_key_id
  sensitive   = true
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cloudflare（フロントエンド）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "cloudflare_pages_project_name" {
  description = "Cloudflare Pages project name"
  value       = module.cloudflare.pages_project_name
}

output "cloudflare_pages_url" {
  description = "Cloudflare Pages deployment URL"
  value       = module.cloudflare.pages_url
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Render（バックエンド）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "render_service_id" {
  description = "Render service ID"
  value       = module.render.service_id
}

output "render_service_name" {
  description = "Render service name"
  value       = module.render.service_name
}

output "render_service_url" {
  description = "Render backend service URL"
  value       = module.render.service_url
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 環境情報
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "environment" {
  description = "Environment name"
  value       = local.environment
}

output "project_name" {
  description = "Project name"
  value       = local.project_name
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# デプロイ情報（まとめ）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "deployment_info" {
  description = "Deployment information summary"
  value = {
    environment = local.environment
    project     = local.project_name
    
    database = {
      provider = "Neon"
      host     = module.neon.host
      name     = module.neon.database_name
    }
    
    backend = {
      provider = "Render"
      url      = module.render.service_url
      name     = module.render.service_name
    }
    
    frontend = {
      provider = "Cloudflare Pages"
      url      = module.cloudflare.pages_url
    }
    
    storage = {
      provider = "Backblaze B2"
      bucket   = module.backblaze.bucket_name
      endpoint = module.backblaze.s3_endpoint
    }
  }
}