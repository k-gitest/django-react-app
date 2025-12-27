# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cloudflare モジュール - リソース定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cloudflare Pages（フロントエンド）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 注意: GitHub連携は事前に手動で完了させる必要があります
# https://dash.cloudflare.com/ → Workers & Pages → Create application → Pages → Connect to Git

resource "cloudflare_pages_project" "frontend" {
  account_id        = var.account_id
  name              = var.pages_project_name
  production_branch = var.production_branch
  
  # ビルド設定
  build_config {
    build_command       = "npm run build"
    destination_dir     = "dist"
    root_dir            = "frontend"  # モノレポ構成
    web_analytics_tag   = null
    web_analytics_token = null
  }
  
  # ソース設定（GitHub連携）
  source {
    type = "github"
    config {
      owner                         = local.github_owner
      repo_name                     = local.github_repo
      production_branch             = var.production_branch
      pr_comments_enabled           = true
      deployments_enabled           = true
      production_deployment_enabled = true
      preview_deployment_setting    = "all"
      preview_branch_includes       = ["*"]
      preview_branch_excludes       = []
    }
  }
  
  # デプロイメント設定
  deployment_configs {
    production {
      environment_variables = {
        NODE_VERSION = "20"
      }
      
      compatibility_date  = "2024-01-01"
      compatibility_flags = []
      fail_open          = false
      always_use_latest_compatibility_date = false
    }
    
    preview {
      environment_variables = {
        NODE_VERSION = "20"
      }
      
      compatibility_date  = "2024-01-01"
      compatibility_flags = []
      fail_open          = false
      always_use_latest_compatibility_date = false
    }
  }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ローカル変数（GitHubリポジトリの分解）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

locals {
  # github_repo_url から owner と repo を抽出
  github_path  = replace(var.github_repo_url, "https://github.com/", "")
  github_parts = split("/", local.github_path)
  github_owner = local.github_parts[0]
  github_repo  = local.github_parts[1]
}