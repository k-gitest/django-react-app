# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cloudflare モジュール - 変数定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

variable "pages_project_name" {
  description = "Cloudflare Pages project name (e.g., django-react-app-frontend-production)"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.pages_project_name))
    error_message = "Pages project name must be lowercase alphanumeric with hyphens."
  }
}

variable "production_branch" {
  description = "Git branch for production deployment"
  type        = string
  default     = "main"
}

variable "github_repo_url" {
  description = "GitHub repository URL (HTTPS format)"
  type        = string
  
  validation {
    condition     = can(regex("^https://github\\.com/[^/]+/[^/]+$", var.github_repo_url))
    error_message = "GitHub URL must be HTTPS format: https://github.com/username/repo"
  }
}