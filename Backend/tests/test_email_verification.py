from datetime import datetime, timezone, timedelta
from extensions import db
from modules.auth.models import AuthOTP
from modules.auth.tokens import hash_otp
from modules.users.models import User


def test_verify_email_success(client, app):
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "verify_me",
            "email": "verify@example.com",
            "password": "StrongPassword123!",
        },
    )

    with app.app_context():
        otp_rec = AuthOTP.query.filter_by(email="verify@example.com", purpose="EMAIL_VERIFICATION").first()
        assert otp_rec is not None
        # We can set known OTP hash
        known_otp = "123456"
        otp_rec.otp_hash = hash_otp(known_otp)
        db.session.commit()

    res = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "verify@example.com", "otp": "123456"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["email_verified"] is True
    assert data["data"]["account_status"] == "ACTIVE"


def test_verify_email_incorrect_otp(client, app):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "wrong_otp_user",
            "email": "wrong@example.com",
            "password": "StrongPassword123!",
        },
    )

    res = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "wrong@example.com", "otp": "999999"},
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "Invalid verification code" in data["message"]


def test_verify_email_expired_otp(client, app):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "expired_otp_user",
            "email": "expired@example.com",
            "password": "StrongPassword123!",
        },
    )

    with app.app_context():
        otp_rec = AuthOTP.query.filter_by(email="expired@example.com").first()
        otp_rec.otp_hash = hash_otp("123456")
        otp_rec.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.session.commit()

    res = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "expired@example.com", "otp": "123456"},
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "expired" in data["message"].lower()


def test_verify_email_reuse_otp(client, app):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "reuse_otp_user",
            "email": "reuse@example.com",
            "password": "StrongPassword123!",
        },
    )

    with app.app_context():
        otp_rec = AuthOTP.query.filter_by(email="reuse@example.com").first()
        otp_rec.otp_hash = hash_otp("123456")
        db.session.commit()

    # First attempt succeeds
    res1 = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "reuse@example.com", "otp": "123456"},
    )
    assert res1.status_code == 200

    # User is now active, so verifying again returns active
    res2 = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "reuse@example.com", "otp": "123456"},
    )
    assert res2.status_code == 200
    assert res2.get_json()["data"]["account_status"] == "ACTIVE"


def test_resend_verification_otp(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "resend_user",
            "email": "resend@example.com",
            "password": "StrongPassword123!",
        },
    )

    # First request right after registration triggers 60s cooldown or succeeds if not restricted
    # Request resend
    res = client.post(
        "/api/v1/auth/resend-verification-otp",
        json={"email": "resend@example.com"},
    )
    # Either 429 for cooldown or 200
    assert res.status_code in (200, 429)
