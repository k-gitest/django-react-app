# --- 1. ビルドステージ (依存関係のインストールと静的ファイルの収集) ---
# Pythonの最新安定版を使用
FROM python:3.12-slim AS builder

# 作業ディレクトリを設定
WORKDIR /workspace/backend

# 依存関係ファイルをコピー
# 開発環境用のファイルはコピーせず、本番に必要なもののみ
COPY requirements.txt .

# 依存関係をインストール
# ここで --no-cache-dir をつけて不要なキャッシュを削除
RUN pip install --no-cache-dir -r requirements.txt

# コードをコピー
COPY . .

# 静的ファイル収集 (プロダクションデプロイメントの標準的なステップ)
# settings.pyでSTATIC_ROOTが定義されている必要あり
RUN python manage.py collectstatic --noinput

# --- 2. 最終ステージ (実行環境) ---
FROM python:3.12-slim AS final

# 作業ディレクトリを設定
WORKDIR /workspace/backend

# 実行ユーザーの追加（セキュリティ強化のため）
# RUN useradd --no-create-home django_user # 開発用
RUN useradd --no-create-home --shell /usr/sbin/nologin django_user # 本番用
ENV HOME=/home/django_user
# ✅ 本番環境では非rootユーザーで実行
USER django_user

# ビルドステージから必要なものをコピー
# 依存関係（インストールされたライブラリ）とコードをコピー
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
# COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /workspace/backend /workspace/backend

# アプリケーションファイルの所有権を変更
RUN chown -R django_user:django_user /workspace/backend

# 環境変数（必要に応じて設定）
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE config.settings 
# 本番環境であることを明示（settings.pyで活用）
ENV DJANGO_ENV production 

# Gunicornがリッスンするポート
EXPOSE 8000

# コンテナ起動時にGunicornでDjangoを実行
# configはプロジェクト名、wsgiはWSGIモジュール
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]