# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Render モジュール - 出力値
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "service_id" {
  description = "Render service ID"
  value       = render_web_service.backend.id
}

output "service_name" {
  description = "Render service name"
  value       = render_web_service.backend.name
}

output "service_url" {
  description = "Render service URL"
  value       = "https://${render_web_service.backend.name}.onrender.com"
}

output "dashboard_url" {
  description = "Render dashboard URL"
  value       = "https://dashboard.render.com/web/${render_web_service.backend.id}"
}

output "region" {
  description = "Deployment region"
  value       = render_web_service.backend.region
}
/*
output "runtime" {
  description = "Runtime type"
  value       = render_web_service.backend.runtime
}
*/