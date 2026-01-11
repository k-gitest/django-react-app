import os
from django.conf import settings
import logging
from qstash import Receiver

logger = logging.getLogger(__name__)

def verify_qstash_signature(request) -> bool:
    """
    QStashから送信された署名の妥当性を公式SDKを用いて検証します。
    
    内部でHMAC-SHA256の計算に加え、タイムスタンプの検証（リプレイアタック防止）
    およびキーローテーションの処理を自動的に行います。
    
    Args:
        request: DjangoのHTTPRequestオブジェクト
    
    Returns:
        bool: 署名が有効であればTrue、それ以外はFalse
    """
    
    # QStashが付与する署名ヘッダーの取得
    signature = request.headers.get("Upstash-Signature")
    
    if not signature:
        logger.warning("Missing QStash signature header")
        return False
    
    # SDKのReceiverを初期化（環境変数に設定されたSigning Keyを使用）
    receiver = Receiver(
        current_signing_key=settings.QSTASH_CURRENT_SIGNING_KEY,
        next_signing_key=settings.QSTASH_NEXT_SIGNING_KEY,
    )
    
    # 検証に使用するURLの動的構築
    # QStash側の署名は「送信先フルURL」を材料に含めるため、
    # プロキシ環境（Codespaces等）でのhttp/httpsの不一致やドメインの相違を補正します。
    base_url = os.getenv("WEBHOOK_BASE_URL")
    path = request.get_full_path()
    url = f"{base_url}{path}"

    # Codespaces等のドメインにおいて、内部的にhttpとして扱われている場合はhttpsに正規化
    if not url.startswith("https") and ".app.github.dev" in url:
        url = url.replace("http://", "https://")
    
    # リクエストボディを文字列として取得
    body = request.body.decode("utf-8")

    try:
        # SDKを用いた包括的な署名検証の実行
        # body, signature, url が一つでも送信時と異なると検証失敗となります
        receiver.verify(
            body=body,
            signature=signature,
            url=url
        )
        return True
    except Exception as e:
        # 検証失敗時はログに詳細を記録（本番運用時のトラブルシューティング用）
        logger.warning(f"QStash signature verification failed: {e}")
        return False