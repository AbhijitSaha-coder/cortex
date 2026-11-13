def test_register_user(client):
    payload = {
        "email": "new_scholar@cortex.ai",
        "password": "SecurePassword999!",
        "full_name": "Ada Lovelace"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new_scholar@cortex.ai"
    assert data["full_name"] == "Ada Lovelace"
    assert "hashed_password" not in data


def test_register_duplicate_email(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "AnotherPassword123!",
        "full_name": "Clone User"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "SuperSecret123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "WrongPassword!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401


def test_get_me(client, auth_headers, test_user):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


def test_get_me_unauthorized(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_refresh_token(client, test_user):
    login_res = client.post("/api/auth/login", json={"email": test_user.email, "password": "SuperSecret123!"})
    refresh_token = login_res.json()["refresh_token"]

    ref_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    assert "access_token" in ref_res.json()


def test_logout(client, auth_headers):
    response = client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert "logged out" in response.json()["message"]

