def test_logout_success(client, active_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "active_user", "password": "ValidPass123!"},
    )
    assert login_res.status_code == 200
    csrf_token = login_res.get_json()["data"]["csrf_token"]

    # Verify status is authenticated
    status_res1 = client.get("/api/v1/auth/status")
    assert status_res1.get_json()["data"]["authenticated"] is True

    # Call logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-TOKEN": csrf_token},
    )
    assert logout_res.status_code == 200
    assert logout_res.get_json()["success"] is True

    # Status should now be unauthenticated
    status_res2 = client.get("/api/v1/auth/status")
    assert status_res2.get_json()["data"]["authenticated"] is False


def test_logout_without_session(client):
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert res.get_json()["success"] is True
