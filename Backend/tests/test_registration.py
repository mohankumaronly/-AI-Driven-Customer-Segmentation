def test_registration_success(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john_doe",
            "email": "john@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["verification_required"] is True
    assert data["data"]["user"]["username"] == "john_doe"
    assert data["data"]["user"]["account_status"] == "PENDING_VERIFICATION"
    assert data["data"]["user"]["email_verified"] is False


def test_registration_duplicate_username(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john_doe",
            "email": "john@example.com",
            "password": "StrongPassword123!",
        },
    )
    # Register with same username but different case and email
    res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "John_Doe",
            "email": "other@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert res.status_code == 409
    data = res.get_json()
    assert data["success"] is False
    assert "Username is already taken" in data["message"]


def test_registration_duplicate_email(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john_doe",
            "email": "john@example.com",
            "password": "StrongPassword123!",
        },
    )
    # Register with same email but different username
    res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "jane_doe",
            "email": "John@Example.com",
            "password": "StrongPassword123!",
        },
    )
    assert res.status_code == 409
    data = res.get_json()
    assert data["success"] is False
    assert "Email is already registered" in data["message"]


def test_registration_invalid_username(client):
    # Too short
    res = client.post(
        "/api/v1/auth/register",
        json={"username": "ab", "email": "ab@example.com", "password": "StrongPassword123!"},
    )
    assert res.status_code == 400

    # Invalid characters
    res2 = client.post(
        "/api/v1/auth/register",
        json={"username": "john.doe", "email": "ab@example.com", "password": "StrongPassword123!"},
    )
    assert res2.status_code == 400


def test_registration_weak_password(client):
    # No uppercase / no special char / too short
    res = client.post(
        "/api/v1/auth/register",
        json={"username": "valid_user", "email": "valid@example.com", "password": "weak"},
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "errors" in data
