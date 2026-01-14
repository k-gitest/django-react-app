variable "environment" {
  type = string
}

variable "region" {
  description = "Upstash region (e.g. 'us-east-1')"
  type        = string
  default     = "us-east-1" # Vector 等が対応しているリージョン
}