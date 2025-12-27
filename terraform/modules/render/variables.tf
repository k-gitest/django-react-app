# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Render モジュール - 変数定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "owner_id" {
  description = "Render Owner ID (usr-xxx or tea-xxx)"
  type        = string
  
  validation {
    condition     = can(regex("^(usr|tea)-", var.owner_id))
    error_message = "Owner ID must start with 'usr-' or 'tea-'."
  }
}

variable "app_name" {
  description = "Render service name (e.g., django-react-app-backend-production)"
  type        = string
}

variable "github_repo_url" {
  description = "GitHub repository URL (HTTPS format)"
  type        = string
  
  validation {
    condition     = can(regex("^https://github\\.com/", var.github_repo_url))
    error_message = "GitHub URL must be in HTTPS format."
  }
}

variable "branch" {
  description = "Git branch to deploy"
  type        = string
  default     = "main"
}

variable "region" {
  description = "Render deployment region"
  type        = string
  
  validation {
    condition = contains([
      "oregon", "ohio", "virginia", "frankfurt", "singapore"
    ], var.region)
    error_message = "Must be a valid Render region."
  }
}

# モジュール間の依存関係
variable "database_url" {
  description = "Database connection string from Neon"
  type        = string
  sensitive   = true
}

variable "s3_endpoint" {
  description = "S3-compatible endpoint URL (Cloudflare R2)"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name (Cloudflare R2)"
  type        = string
}

# 環境変数
variable "env_vars" {
  description = "Additional environment variables"
  type        = map(string)
  default     = {}
}