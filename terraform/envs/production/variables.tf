# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 環境固有の変数定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# プロジェクト名
variable "project_name" {
  description = "Project name (matches Terraform Cloud organization name)"
  type        = string
  default     = "django-react-app"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (production or staging)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["production", "staging"], var.environment)
    error_message = "Environment must be 'production' or 'staging'."
  }
}

variable "render_owner_id" {
  description = "Render Owner ID"
  type        = string
}

variable "cloudflare_account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

variable "github_repo_url" {
  description = "GitHub repository URL"
  type        = string
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# リージョン設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "neon_region" {
  description = "Neon database region (AWS format)"
  type        = string
  default     = "aws-ap-southeast-1"  # ✅ シンガポール（AWS形式）
  
  validation {
    condition = can(regex("^aws-", var.neon_region))
    error_message = "Neon region must use AWS format (e.g., aws-ap-southeast-1)."
  }
}

variable "render_region" {
  description = "Render deployment region"
  type        = string
  default     = "singapore"  # ✅ シンガポール（Render形式）
  
  validation {
    condition = contains([
      "oregon",
      "ohio", 
      "virginia",
      "frankfurt",
      "singapore"
    ], var.render_region)
    error_message = "Must be a valid Render region."
  }
}