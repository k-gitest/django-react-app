# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GitHub Secrets モジュール - 変数定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "repository_name" {
  description = "GitHub repository name (e.g., username/django-react-app)"
  type        = string
}

variable "environment" {
  description = "Environment name (production or staging)"
  type        = string
  
  validation {
    condition     = contains(["production", "staging"], var.environment)
    error_message = "Environment must be either 'production' or 'staging'."
  }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# URL設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "backend_url" {
  description = "Backend API URL (for frontend)"
  type        = string
}

variable "frontend_url" {
  description = "Frontend URL (for backend CORS)"
  type        = string
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ストレージ設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "storage_url" {
  description = "Storage public URL (for frontend assets)"
  type        = string
}

variable "storage_bucket_name" {
  description = "Storage bucket name (for backend)"
  type        = string
}

variable "s3_endpoint_url" {
  description = "S3-compatible endpoint URL (for backend)"
  type        = string
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Django設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "debug_mode" {
  description = "Django DEBUG setting"
  type        = string
  default     = "False"
}

variable "secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PostgreSQL接続情報
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "pgdatabase" {
  description = "PostgreSQL database name"
  type        = string
}

variable "pguser" {
  description = "PostgreSQL user"
  type        = string
}

variable "pgpassword" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "pghost" {
  description = "PostgreSQL host"
  type        = string
}

variable "pgport" {
  description = "PostgreSQL port"
  type        = string
  default     = "5432"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Backblaze B2
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "b2_application_key_id" {
  description = "Backblaze B2 application key ID"
  type        = string
  sensitive   = true
}

variable "b2_application_key" {
  description = "Backblaze B2 application key"
  type        = string
  sensitive   = true
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# E2Eテスト用認証情報
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

variable "e2e_test_email" {
  description = "E2E test user email"
  type        = string
  sensitive   = true
}

variable "e2e_test_password" {
  description = "E2E test user password"
  type        = string
  sensitive   = true
}
