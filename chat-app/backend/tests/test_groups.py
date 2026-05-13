import pytest


class TestGroups:
    class TestCreate:
        async def test_create_group_success(self, client, auth_headers, test_user2):
            response = await client.post("/api/groups", headers=auth_headers, json={
                "name": "New Group",
                "description": "A new group",
                "member_ids": [test_user2.id],
            })
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "New Group"
            assert data["description"] == "A new group"
            assert len(data["members"]) == 2

        async def test_create_group_no_auth(self, client, test_user2):
            response = await client.post("/api/groups", json={
                "name": "New Group",
                "member_ids": ["some-id"],
            })
            assert response.status_code == 401

        async def test_create_group_missing_name(self, client, auth_headers):
            response = await client.post("/api/groups", headers=auth_headers, json={
                "description": "No name",
            })
            assert response.status_code == 422

    class TestList:
        async def test_list_groups(self, client, auth_headers, test_group):
            response = await client.get("/api/groups", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1

        async def test_list_groups_no_auth(self, client):
            response = await client.get("/api/groups")
            assert response.status_code == 401

        async def test_list_groups_only_my_groups(self, client, auth_headers2, test_group):
            response = await client.get("/api/groups", headers=auth_headers2)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert any(g["id"] == test_group.id for g in data)

    class TestGet:
        async def test_get_group_success(self, client, auth_headers, test_group):
            response = await client.get(f"/api/groups/{test_group.id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == test_group.id
            assert data["name"] == "Test Group"

        async def test_get_group_not_found(self, client, auth_headers):
            response = await client.get("/api/groups/nonexistent-id", headers=auth_headers)
            assert response.status_code == 404

        async def test_get_group_no_auth(self, client, test_group):
            response = await client.get(f"/api/groups/{test_group.id}")
            assert response.status_code == 401

    class TestUpdate:
        async def test_update_group_success(self, client, auth_headers, test_group):
            response = await client.patch(f"/api/groups/{test_group.id}", headers=auth_headers, json={
                "name": "Updated Group",
                "description": "Updated description",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Group"
            assert data["description"] == "Updated description"

        async def test_update_group_not_owner(self, client, auth_headers2, test_group):
            response = await client.patch(f"/api/groups/{test_group.id}", headers=auth_headers2, json={
                "name": "Hacked",
            })
            assert response.status_code == 403

        async def test_update_group_not_found(self, client, auth_headers):
            response = await client.patch("/api/groups/nonexistent-id", headers=auth_headers, json={
                "name": "Updated",
            })
            assert response.status_code == 404

    class TestMembers:
        async def test_add_member_success(self, client, auth_headers, test_group, test_user2):
            response = await client.post(
                f"/api/groups/{test_group.id}/members?user_id={test_user2.id}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == test_user2.id
            assert data["role"] == "member"

        async def test_add_member_not_owner(self, client, auth_headers2, test_group, test_user):
            response = await client.post(
                f"/api/groups/{test_group.id}/members?user_id={test_user.id}",
                headers=auth_headers2,
            )
            assert response.status_code == 403

        async def test_add_member_duplicate(self, client, auth_headers, test_group, test_user2):
            response = await client.post(
                f"/api/groups/{test_group.id}/members?user_id={test_user2.id}",
                headers=auth_headers,
            )
            assert response.status_code == 409

        async def test_remove_member_success(self, client, auth_headers, test_group, test_user2):
            response = await client.delete(
                f"/api/groups/{test_group.id}/members/{test_user2.id}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Member removed"

        async def test_remove_member_not_owner(self, client, auth_headers2, test_group, test_user):
            response = await client.delete(
                f"/api/groups/{test_group.id}/members/{test_user.id}",
                headers=auth_headers2,
            )
            assert response.status_code == 403

    class TestMessages:
        async def test_get_group_messages(self, client, auth_headers, test_group):
            response = await client.get(
                f"/api/groups/{test_group.id}/messages",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data

        async def test_get_group_messages_not_member(self, client, test_group):
            from auth import create_access_token
            fake_token = create_access_token(data={"sub": "fake-user-id"})
            response = await client.get(
                f"/api/groups/{test_group.id}/messages",
                headers={"Authorization": f"Bearer {fake_token}"},
            )
            assert response.status_code == 403
