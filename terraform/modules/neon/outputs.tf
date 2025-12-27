# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Neon モジュール - 出力値
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "project_id" {
  description = "Neon project ID"
  value       = neon_project.main.id
}

output "project_name" {
  description = "Neon project name"
  value       = neon_project.main.name
}

output "branch_id" {
  description = "Neon branch ID"
  value       = neon_branch.main.id
}

output "branch_name" {
  description = "Neon branch name"
  value       = neon_branch.main.name
}

output "database_name" {
  description = "Database name"
  value       = neon_database.main.name
}

output "role_name" {
  description = "Database role name"
  value       = neon_role.main.name
}

output "host" {
  description = "Database host (endpoint)"
  value       = neon_endpoint.main.host
}

output "connection_uri" {
  description = "PostgreSQL connection string"
  value       = "postgresql://${neon_role.main.name}@${neon_endpoint.main.host}/${neon_database.main.name}"
  sensitive   = true
}

output "endpoint_id" {
  description = "Neon endpoint ID"
  value       = neon_endpoint.main.id
}