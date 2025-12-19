# --- 1. ビルドステージ (Reactアプリケーションのビルド) ---
# Node.jsの安定版LTSを使用
FROM node:20-slim AS builder

# 作業ディレクトリを設定
WORKDIR /workspace/frontend

# 依存関係ファイルをコピー
COPY package.json package-lock.json ./

# 依存関係をインストール
RUN npm install

# コードをコピー
COPY . .

# アプリケーションをビルド
# ✅ 開発環境ではビルドしない（docker-compose.ymlのtarget: builderで止まる）
# RUN npm run build 

# --- 2. 最終ステージ (Nginxサーバーで静的ファイルを配信) ---
FROM node:20-slim AS production-builder

WORKDIR /workspace/frontend

# ✅ builderステージから依存関係とコードをコピー
COPY --from=builder /workspace/frontend /workspace/frontend

# ✅ 本番環境でのみビルド実行
RUN npm run build

# 軽量なNginxイメージを使用
FROM nginx:alpine AS final

# Nginxの設定ファイル（必要に応じて）
# デフォルト設定を使う場合はこの行を省略
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# ビルドステージからビルド済みの静的ファイルをコピー
# ビルドディレクトリは通常 'dist' または 'build'
# COPY --from=builder /app/dist /usr/share/nginx/html
# ✅ production-builderステージからビルド済みファイルをコピー
COPY --from=production-builder /workspace/frontend/dist /usr/share/nginx/html

# Nginxがリッスンするポート
EXPOSE 80

# Nginxを起動
CMD ["nginx", "-g", "daemon off;"]