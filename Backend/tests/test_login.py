from extensions import db
from modules.users.models import User
from werkzeug.security import generate_password_hash


def test_login_success_with_username(client, active_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["user"]["username"] == "active_user"
    assert data["data"]["expires_in_seconds"] == 604800
    assert "csrf_token" in data["data"]
    # Verify cookie was set
    assert "access_token_cookie" in res.headers.get("Set-Cookie", "")


def test_login_success_with_email(client, active_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active@example.com", "password": "ValidPass123!"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "active@example.com"


def test_login_incorrect_password(client, active_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    data = res.get_json()
    assert data["success"] is False
    assert "Invalid username/email or password" in data["message"]


def test_login_pending_verification(client, pending_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "pending_user", "password": "ValidPass123!"},
    )
    assert res.status_code == 403
    data = res.get_json()
    assert data["success"] is False
    assert "verify your email" in data["message"].lower()


def test_login_suspended_account(client, app):
    with app.app_context():
        user = User(
            username="suspended_user",
            normalized_username="suspended_user",
            email="suspended@example.com",
            normalized_email="suspended@example.com",
            password_hash=generate_password_hash("ValidPass123!"),
            email_verified=True,
            account_status="SUSPENDED",
        )
        db.session.add(user)
        db.session.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "suspended_user", "password": "ValidPass123!"},
    )
    assert res.status_code == 403
    data = res.get_json()
    assert data["success"] is False
    assert "suspended" in data["message"].lower()
