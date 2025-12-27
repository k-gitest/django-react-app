# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cloudflare モジュール - 出力値
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "pages_project_name" {
  description = "Cloudflare Pages project name"
  value       = cloudflare_pages_project.frontend.name
}

output "pages_project_id" {
  description = "Cloudflare Pages project ID"
  value       = cloudflare_pages_project.frontend.id
}

output "pages_url" {
  description = "Cloudflare Pages deployment URL"
  value       = "https://${cloudflare_pages_project.frontend.subdomain}.pages.dev"
}

output "pages_subdomain" {
  description = "Cloudflare Pages subdomain"
  value       = cloudflare_pages_project.frontend.subdomain
}

output "github_owner" {
  description = "GitHub repository owner"
  value       = local.github_owner
}

output "github_repo" {
  description = "GitHub repository name"
  value       = local.github_repo
}