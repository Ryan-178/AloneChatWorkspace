import pytest


class TestAuth:
    class TestRegister:
        async def test_register_success(self, client):
            response = await client.post("/api/auth/register", json={
                "email": "newuser@example.com",
                "password": "password123",
                "display_name": "New User",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "newuser@example.com"
            assert data["display_name"] == "New User"
            assert "id" in data

        async def test_register_duplicate_email(self, client, test_user):
            response = await client.post("/api/auth/register", json={
                "email": "test@example.com",
                "password": "password123",
                "display_name": "Another User",
            })
            assert response.status_code == 409
            data = response.json()
            assert data["detail"]["error"] == "Conflict"

        async def test_register_invalid_email(self, client):
            response = await client.post("/api/auth/register", json={
                "email": "not-an-email",
                "password": "password123",
                "display_name": "Bad Email",
            })
            assert response.status_code == 422

        async def test_register_missing_password(self, client):
            response = await client.post("/api/auth/register", json={
                "email": "missing@example.com",
                "display_name": "No Password",
            })
            assert response.status_code == 422

    class TestLogin:
        async def test_login_success(self, client, test_user):
            response = await client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123",
            })
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

        async def test_login_wrong_password(self, client, test_user):
            response = await client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpassword",
            })
            assert response.status_code == 401
            data = response.json()
            assert data["detail"]["error"] == "Unauthorized"

        async def test_login_nonexistent_user(self, client):
            response = await client.post("/api/auth/login", json={
                "email": "nobody@example.com",
                "password": "password123",
            })
            assert response.status_code == 401

    class TestGetMe:
        async def test_get_me_success(self, client, auth_headers, test_user):
            response = await client.get("/api/users/me", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["display_name"] == "Test User"

        async def test_get_me_no_auth(self, client):
            response = await client.get("/api/users/me")
            assert response.status_code == 401

        async def test_get_me_invalid_token(self, client):
            response = await client.get("/api/users/me", headers={"Authorization": "Bearer invalid"})
            assert response.status_code == 401

    class TestUpdateMe:
        async def test_update_me_success(self, client, auth_headers, test_user):
            response = await client.patch("/api/users/me", headers=auth_headers, json={
                "display_name": "Updated Name",
                "avatar_url": "https://example.com/avatar.png",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Updated Name"
            assert data["avatar_url"] == "https://example.com/avatar.png"

        async def test_update_me_partial(self, client, auth_headers, test_user):
            response = await client.patch("/api/users/me", headers=auth_headers, json={
                "display_name": "Only Name",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Only Name"

    class TestSearchUsers:
        async def test_search_users(self, client, auth_headers, test_user, test_user2):
            response = await client.get("/api/users?q=test", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1

        async def test_search_users_no_query(self, client, auth_headers, test_user, test_user2):
            response = await client.get("/api/users", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert all(u["id"] != test_user.id for u in data)

        async def test_search_users_no_auth(self, client):
            response = await client.get("/api/users?q=test")
            assert response.status_code == 401

    class TestGetUser:
        async def test_get_user_success(self, client, auth_headers, test_user2):
            response = await client.get(f"/api/users/{test_user2.id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == test_user2.id

        async def test_get_user_not_found(self, client, auth_headers):
            response = await client.get("/api/users/nonexistent-id", headers=auth_headers)
            assert response.status_code == 404
