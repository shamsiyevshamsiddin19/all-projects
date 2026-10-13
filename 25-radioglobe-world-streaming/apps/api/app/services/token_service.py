import hmac
import hashlib
import time
from app.config import settings

def generate_stream_token(stream_id: int, ttl_seconds: int = 7200) -> str:
    """
    Generates a secure, expiring HMAC token for a stream_id (default TTL: 2 hours).
    Format: timestamp.signature
    """
    expires_at = int(time.time()) + ttl_seconds
    message = f"{stream_id}:{expires_at}".encode("utf-8")
    sig = hmac.new(
        settings.PROXY_SECRET_KEY.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
    return f"{expires_at}.{sig}"

def verify_stream_token(stream_id: int, token: str) -> bool:
    """
    Verifies that the provided token is authentic, belongs to stream_id, and has not expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False
        
        expires_at = int(parts[0])
        provided_sig = parts[1]

        # Check expiration
        if time.time() > expires_at:
            return False

        expected_message = f"{stream_id}:{expires_at}".encode("utf-8")
        expected_sig = hmac.new(
            settings.PROXY_SECRET_KEY.encode("utf-8"),
            expected_message,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(provided_sig, expected_sig)
    except Exception:
        return False
