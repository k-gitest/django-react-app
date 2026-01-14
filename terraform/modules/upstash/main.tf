terraform {
  required_providers {
    upstash = {
      source  = "upstash/upstash"
      version = "~> 1.5.0"
    }
  }
}

# --- Redis Database ---
resource "upstash_redis_database" "main" {
  database_name = "todo-redis-${var.environment}"
  region        = var.region
  plan          = "free"
  tls           = true
  eviction      = true
}

# --- Vector Index (AI検索用) ---
resource "upstash_vector_index" "main" {
  name                = "todo-vector-${var.environment}"
  region              = "us-east-1" # Vector対応リージョン
  dimension           = 768         # Gemini text-embedding-004 用
  similarity_function = "cosine"
}

# --- QStash Topic ---
resource "upstash_qstash_topic" "main" {
  name = "todo-tasks-${var.environment}"
}