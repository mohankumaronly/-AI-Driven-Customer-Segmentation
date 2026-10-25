from extensions import db
from modules.users.models import User


def test_get_current_user_profile(client, active_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    assert login_res.status_code == 200

    res = client.get("/api/v1/users/me")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["username"] == "active_user"
    assert data["email"] == "active@example.com"
    assert data["email_verified"] is True
    assert data["account_status"] == "ACTIVE"


def test_update_username(client, active_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    csrf_token = login_res.get_json()["data"]["csrf_token"]

    res = client.patch(
        "/api/v1/users/me",
        json={"username": "updated_user"},
        headers={"X-CSRF-TOKEN": csrf_token},
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["username"] == "updated_user"


def test_update_forbidden_fields(client, active_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    csrf_token = login_res.get_json()["data"]["csrf_token"]

    res = client.patch(
        "/api/v1/users/me",
        json={"email": "hacked@example.com", "account_status": "SUPER_ADMIN"},
        headers={"X-CSRF-TOKEN": csrf_token},
    )
    assert res.status_code == 400
    assert "Cannot update field" in res.get_json()["message"]


def test_change_password_authenticated(client, active_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    csrf_token = login_res.get_json()["data"]["csrf_token"]

    # Wrong current password fails
    res_wrong = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongPassword123!", "new_password": "BrandNewPassword123!"},
        headers={"X-CSRF-TOKEN": csrf_token},
    )
    assert res_wrong.status_code == 400

    # Correct current password succeeds
    res_ok = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "ValidPass123!", "new_password": "BrandNewPassword123!"},
        headers={"X-CSRF-TOKEN": csrf_token},
    )
    assert res_ok.status_code == 200
    assert "Password changed successfully" in res_ok.get_json()["message"]

    # Verify old session no longer works
    res_me = client.get("/api/v1/users/me")
    assert res_me.status_code == 401


def test_delete_account(client, app, active_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    csrf_token = login_res.get_json()["data"]["csrf_token"]

    res = client.delete(
        "/api/v1/users/me",
        headers={"X-CSRF-TOKEN": csrf_token},
    )
    assert res.status_code == 200
    assert "Account deletion request received" in res.get_json()["message"]

    # Account status in DB is PENDING_DELETION
    with app.app_context():
        user = db.session.get(User, active_user.id)
        assert user.account_status == "PENDING_DELETION"
