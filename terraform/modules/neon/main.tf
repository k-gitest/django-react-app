# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Neon モジュール - リソース定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

terraform {
  required_providers {
    neon = {
      source  = "kislerdm/neon"
      version = "~> 0.6"
    }
  }
}

# Neonプロジェクトの作成
resource "neon_project" "main" {
  name      = var.project_name
  region_id = var.region_id
  
  # Compute設定（無料枠: 0.25 CU）
  compute_provisioner = "k8s-pod"
  
  default_endpoint_settings {
    autoscaling_limit_min_cu = 0.25  # 最小0.25 Compute Units
    autoscaling_limit_max_cu = 0.25  # 最大0.25 CU（無料枠内）
    
    # サスペンド設定（5分間アクティビティがなければスリープ）
    suspend_timeout_seconds = 300
  }
  
  # PostgreSQLバージョン（最新の安定版を推奨）
  pg_version = 16
  
  # ヒストリー保持期間（無料プランでは7日間）
  history_retention_seconds = 604800  # 7日間
}

# データベースブランチの作成
resource "neon_branch" "main" {
  project_id = neon_project.main.id
  name       = var.branch_name
  
  # 親ブランチは指定しない（メインブランチとして作成）
}

# エンドポイント（Compute）の作成
resource "neon_endpoint" "main" {
  project_id = neon_project.main.id
  branch_id  = neon_branch.main.id
  
  # Compute設定
  compute_provisioner = "k8s-pod"
  type                = "read_write"
  
  autoscaling_limit_min_cu = 0.25
  autoscaling_limit_max_cu = 0.25
  
  suspend_timeout_seconds = 300
}

# データベースロールの作成
resource "neon_role" "main" {
  project_id = neon_project.main.id
  branch_id  = neon_branch.main.id
  name       = "app_user"
}

# データベースの作成
resource "neon_database" "main" {
  project_id = neon_project.main.id
  branch_id  = neon_branch.main.id
  name       = "appdb"
  owner_name = neon_role.main.name
}