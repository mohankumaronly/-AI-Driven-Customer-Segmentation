from extensions import db
from modules.auth.models import AuthOTP, AuthSession
from modules.auth.tokens import hash_otp


def test_forgot_password_generic_response(client, active_user):
    # Existing user
    res1 = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "active@example.com"},
    )
    assert res1.status_code == 200
    assert "eligible account exists" in res1.get_json()["message"]

    # Nonexistent user
    res2 = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert res2.status_code == 200
    assert "eligible account exists" in res2.get_json()["message"]


def test_verify_reset_otp_and_reset_password_flow(client, app, active_user):
    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "active@example.com"},
    )

    with app.app_context():
        otp_rec = AuthOTP.query.filter_by(email="active@example.com", purpose="PASSWORD_RESET").first()
        assert otp_rec is not None
        otp_rec.otp_hash = hash_otp("654321")
        db.session.commit()

    # Verify reset OTP
    res_otp = client.post(
        "/api/v1/auth/verify-reset-otp",
        json={"email": "active@example.com", "otp": "654321"},
    )
    assert res_otp.status_code == 200
    otp_data = res_otp.get_json()
    assert "reset_token" in otp_data["data"]
    reset_token = otp_data["data"]["reset_token"]

    # Reset password
    res_reset = client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "NewValidPassword456!"},
    )
    assert res_reset.status_code == 200
    assert "Password reset successfully" in res_reset.get_json()["message"]

    # Old password fails
    res_old = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    assert res_old.status_code == 401

    # New password succeeds
    res_new = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "NewValidPassword456!"},
    )
    assert res_new.status_code == 200


def test_reuse_reset_token(client, app, active_user):
    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "active@example.com"},
    )

    with app.app_context():
        otp_rec = AuthOTP.query.filter_by(email="active@example.com", purpose="PASSWORD_RESET").first()
        otp_rec.otp_hash = hash_otp("654321")
        db.session.commit()

    res_otp = client.post(
        "/api/v1/auth/verify-reset-otp",
        json={"email": "active@example.com", "otp": "654321"},
    )
    reset_token = res_otp.get_json()["data"]["reset_token"]

    # First reset
    res1 = client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "NewValidPassword456!"},
    )
    assert res1.status_code == 200

    # Second reset with same token fails
    res2 = client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "AnotherPassword789!"},
    )
    assert res2.status_code == 400


def test_reset_password_revokes_sessions(client, app, active_user):
    # Log in first
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    assert login_res.status_code == 200

    # Initiate and perform reset
    client.post("/api/v1/auth/forgot-password", json={"email": "active@example.com"})

    with app.app_context():
        otp_rec = AuthOTP.query.filter_by(email="active@example.com", purpose="PASSWORD_RESET").first()
        otp_rec.otp_hash = hash_otp("654321")
        db.session.commit()

    res_otp = client.post(
        "/api/v1/auth/verify-reset-otp",
        json={"email": "active@example.com", "otp": "654321"},
    )
    reset_token = res_otp.get_json()["data"]["reset_token"]

    client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "NewValidPassword456!"},
    )

    # Previous session cookie now revoked
    res_me = client.get("/api/v1/users/me")
    assert res_me.status_code == 401
