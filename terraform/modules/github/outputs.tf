# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GitHub Secrets モジュール - 出力値
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

output "environment_name" {
  description = "GitHub Environment name"
  value       = github_repository_environment.main.environment
}

output "variables_created" {
  description = "List of Environment Variables created"
  value = [
    github_actions_environment_variable.vite_base_api_url.variable_name,
    github_actions_environment_variable.vite_storage_url.variable_name,
    github_actions_environment_variable.debug.variable_name,
    github_actions_environment_variable.front_url.variable_name,
    github_actions_environment_variable.aws_storage_bucket_name.variable_name,
    github_actions_environment_variable.aws_s3_endpoint_url.variable_name,
  ]
}

output "secrets_created" {
  description = "List of Environment Secrets created"
  value = [
    github_actions_environment_secret.secret_key.secret_name,
    github_actions_environment_secret.pgdatabase.secret_name,
    github_actions_environment_secret.pguser.secret_name,
    github_actions_environment_secret.pgpassword.secret_name,
    github_actions_environment_secret.pghost.secret_name,
    github_actions_environment_secret.pgport.secret_name,
    github_actions_environment_secret.aws_access_key_id.secret_name,
    github_actions_environment_secret.aws_secret_access_key.secret_name,
    github_actions_environment_secret.e2e_test_email.secret_name,
    github_actions_environment_secret.e2e_test_password.secret_name,
  ]
}
