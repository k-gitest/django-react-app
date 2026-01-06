import hmac
import hashlib
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def verify_qstash_signature(request) -> bool:
    """
    QStash署名を検証（HMAC-SHA256）
    
    Args:
        request: DjangoのHTTPRequestオブジェクト
    
    Returns:
        bool: 署名が有効ならTrue
    """
    signature = request.headers.get("Upstash-Signature")
    
    if not signature:
        logger.warning("Missing QStash signature")
        return False
    
    # 署名をパース（例: "v1=abc123,v1=def456"）
    parts = signature.split(",")
    signatures = {}
    for part in parts:
        try:
            key, value = part.split("=", 1)
            signatures[key] = value
        except ValueError:
            logger.warning(f"Invalid signature format: {part}")
            continue
    
    body = request.body
    
    # 現在のキーで検証
    current_signature = hmac.new(
        settings.QSTASH_CURRENT_SIGNING_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if signatures.get("v1") == current_signature:
        return True
    
    # 次のキーで検証（キーローテーション対応）
    next_signature = hmac.new(
        settings.QSTASH_NEXT_SIGNING_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if signatures.get("v1") == next_signature:
        return True
    
    logger.warning("QStash signature verification failed")
    return False