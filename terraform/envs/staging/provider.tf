# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Terraform Cloud Backend 設定（Staging）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

terraform {
  required_version = ">= 1.14.0, < 2.0.0"
  
  cloud {
    organization = "django-react-app"
    workspaces {
      name = "django-react-staging"
    }
  }
  
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.3"
    }
    neon = {
      source  = "kislerdm/neon"
      version = "~> 0.6"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    b2 = {
      source  = "Backblaze/b2"
      version = "~> 0.8"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Provider 設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Render Provider
provider "render" {
  owner_id = var.render_owner_id
}

# Neon Provider
provider "neon" {}

# Cloudflare Provider
provider "cloudflare" {}

# Black blaze Provider
provider "b2" {}

# GitHub Provider
provider "github" {}