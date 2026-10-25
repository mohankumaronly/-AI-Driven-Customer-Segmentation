from extensions import db
from modules.auth.models import AuthSession


def test_access_protected_route_without_cookie(client):
    res = client.get("/api/v1/users/me")
    assert res.status_code == 401
    assert res.get_json()["message"] == "Authentication is required."


def test_access_protected_route_with_cookie(client, active_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    assert login_res.status_code == 200

    res = client.get("/api/v1/users/me")
    assert res.status_code == 200
    assert res.get_json()["data"]["username"] == "active_user"


def test_state_changing_request_requires_csrf_token(client, active_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    assert login_res.status_code == 200
    csrf_token = login_res.get_json()["data"]["csrf_token"]

    # Request without CSRF token should be rejected (400)
    res_no_csrf = client.patch(
        "/api/v1/users/me",
        json={"username": "new_username"},
    )
    assert res_no_csrf.status_code == 400
    assert "CSRF" in res_no_csrf.get_json()["message"]

    # Request with valid CSRF token should succeed
    res_with_csrf = client.patch(
        "/api/v1/users/me",
        json={"username": "new_username"},
        headers={"X-CSRF-TOKEN": csrf_token},
    )
    assert res_with_csrf.status_code == 200
    assert res_with_csrf.get_json()["data"]["username"] == "new_username"


def test_access_with_revoked_session(client, app, active_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    assert login_res.status_code == 200

    with app.app_context():
        session = AuthSession.query.filter_by(user_id=active_user.id).first()
        assert session is not None
        session.revoked_at = db.func.now()
        db.session.commit()

    res = client.get("/api/v1/users/me")
    assert res.status_code == 401
    assert "session is invalid or has expired" in res.get_json()["message"]
