import secrets
import hmac
import hashlib
from datetime import datetime, timezone
from flask import current_app
from flask_jwt_extended import create_access_token


def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


def hash_otp(otp: str) -> str:
    """Hash the OTP using HMAC-SHA256 with current_app.config['SECRET_KEY']."""
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(secret, otp.strip().encode("utf-8"), hashlib.sha256).hexdigest()


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    """Verify the candidate OTP against the stored HMAC-SHA256 hash."""
    candidate_hash = hash_otp(otp)
    return hmac.compare_digest(candidate_hash, otp_hash)


def generate_reset_token() -> str:
    """Generate a cryptographically secure URL-safe reset token."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """Hash the reset token using HMAC-SHA256."""
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(secret, token.strip().encode("utf-8"), hashlib.sha256).hexdigest()


def verify_reset_token_hash(token: str, token_hash: str) -> bool:
    """Verify candidate reset token against stored hash."""
    candidate = hash_reset_token(token)
    return hmac.compare_digest(candidate, token_hash)


def create_user_access_token(user_id: str, session_id: str) -> str:
    """Create an access JWT containing user ID (sub) and session ID (sid)."""
    return create_access_token(
        identity=str(user_id),
        additional_claims={"sid": str(session_id)},
    )
