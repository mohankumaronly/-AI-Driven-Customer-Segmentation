import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def normalize_db_url(url: str | None) -> str:
    if not url:
        return "sqlite:///dev.db"
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def parse_origins(raw: str | None) -> list[str]:
    """Split comma-separated CORS origins, strip whitespace, drop empties."""
    if not raw:
        return []
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    TESTING = False

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-replace-in-production")

    # ---- CORS ----
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")
    CORS_ORIGINS = parse_origins(FRONTEND_URL)

    # Neon PostgreSQL database URL
    SQLALCHEMY_DATABASE_URI = normalize_db_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration - Cookie based
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-replace-in-production")
    JWT_TOKEN_LOCATION = ["cookies"]

    access_token_expires = int(os.getenv("ACCESS_TOKEN_EXPIRES_SECONDS", 604800))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=access_token_expires)

    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "False" if DEBUG else "True").lower() in ("true", "1", "t")
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_CHECK_FORM = False
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
    JWT_ACCESS_CSRF_COOKIE_NAME = "csrf_access_token"
    JWT_ACCESS_CSRF_HEADER_NAME = "X-CSRF-TOKEN"
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN") or None

    JWT_DECODE_ISSUER = "ai-customer-segmentation"
    JWT_DECODE_AUDIENCE = "ai-customer-segmentation-api"
    JWT_ENCODE_ISSUER = "ai-customer-segmentation"
    JWT_ENCODE_AUDIENCE = "ai-customer-segmentation-api"

    # Brevo Configuration
    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
    BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "noreply@example.com")
    BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "AI Customer Segmentation")

    # OTP & Reset Token Policies
    OTP_EXPIRE_SECONDS = 300
    OTP_MAX_ATTEMPTS = 5
    OTP_RESEND_COOLDOWN_SECONDS = 60
    PASSWORD_RESET_TOKEN_EXPIRE_SECONDS = 300

    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day; 50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = True
    RATELIMIT_ENABLED = False