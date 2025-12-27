# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Neon モジュール - 変数定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "project_name" {
  description = "Neon project name (e.g., django-react-app-db-production)"
  type        = string
}

variable "branch_name" {
  description = "Database branch name (typically 'main' or 'develop')"
  type        = string
  default     = "main"
}

variable "region_id" {
  description = "AWS region ID for Neon database (e.g., aws-ap-southeast-1)"
  type        = string
  
  validation {
    condition     = can(regex("^aws-", var.region_id))
    error_message = "Region ID must be in AWS format (e.g., aws-ap-southeast-1)."
  }
}