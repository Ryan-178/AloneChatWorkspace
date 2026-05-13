import pytest


class TestWorkspaces:
    class TestCreate:
        async def test_create_workspace_success(self, client, auth_headers):
            response = await client.post("/api/workspaces", headers=auth_headers, json={
                "name": "New Workspace",
                "description": "A new workspace",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "New Workspace"
            assert data["description"] == "A new workspace"
            assert data["owner_id"] is not None
            assert len(data["members"]) == 1
            assert data["members"][0]["role"] == "owner"

        async def test_create_workspace_no_auth(self, client):
            response = await client.post("/api/workspaces", json={
                "name": "New Workspace",
            })
            assert response.status_code == 401

        async def test_create_workspace_missing_name(self, client, auth_headers):
            response = await client.post("/api/workspaces", headers=auth_headers, json={
                "description": "No name",
            })
            assert response.status_code == 422

    class TestList:
        async def test_list_workspaces(self, client, auth_headers, test_workspace):
            response = await client.get("/api/workspaces", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) >= 1
            assert any(w["id"] == test_workspace.id for w in data["items"])

        async def test_list_workspaces_no_auth(self, client):
            response = await client.get("/api/workspaces")
            assert response.status_code == 401

        async def test_list_workspaces_only_my_workspaces(self, client, auth_headers2, test_workspace):
            response = await client.get("/api/workspaces", headers=auth_headers2)
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert not any(w["id"] == test_workspace.id for w in data["items"])

    class TestGet:
        async def test_get_workspace_success(self, client, auth_headers, test_workspace):
            response = await client.get(f"/api/workspaces/{test_workspace.id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == test_workspace.id
            assert data["name"] == "Test Workspace"

        async def test_get_workspace_not_found(self, client, auth_headers):
            response = await client.get("/api/workspaces/nonexistent-id", headers=auth_headers)
            assert response.status_code == 404

        async def test_get_workspace_no_permission(self, client, auth_headers2, test_workspace):
            response = await client.get(f"/api/workspaces/{test_workspace.id}", headers=auth_headers2)
            assert response.status_code == 403

    class TestUpdate:
        async def test_update_workspace_success(self, client, auth_headers, test_workspace):
            response = await client.put(f"/api/workspaces/{test_workspace.id}", headers=auth_headers, json={
                "name": "Updated Workspace",
                "description": "Updated description",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Workspace"
            assert data["description"] == "Updated description"

        async def test_update_workspace_not_admin(self, client, auth_headers2, test_workspace):
            response = await client.put(f"/api/workspaces/{test_workspace.id}", headers=auth_headers2, json={
                "name": "Hacked",
            })
            assert response.status_code == 403

        async def test_update_workspace_not_found(self, client, auth_headers):
            response = await client.put("/api/workspaces/nonexistent-id", headers=auth_headers, json={
                "name": "Updated",
            })
            assert response.status_code == 404

    class TestDelete:
        async def test_delete_workspace_success(self, client, auth_headers, test_workspace):
            response = await client.delete(f"/api/workspaces/{test_workspace.id}", headers=auth_headers)
            assert response.status_code == 204

        async def test_delete_workspace_not_owner(self, client, auth_headers2, test_workspace):
            response = await client.delete(f"/api/workspaces/{test_workspace.id}", headers=auth_headers2)
            assert response.status_code == 403

        async def test_delete_workspace_not_found(self, client, auth_headers):
            response = await client.delete("/api/workspaces/nonexistent-id", headers=auth_headers)
            assert response.status_code == 404

    class TestMembers:
        async def test_invite_member_success(self, client, auth_headers, test_workspace, test_user2):
            response = await client.post(
                f"/api/workspaces/{test_workspace.id}/members",
                headers=auth_headers,
                json={"email": "test2@example.com", "role": "member"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == test_user2.id
            assert data["role"] == "member"

        async def test_invite_member_not_admin(self, client, auth_headers2, test_workspace, test_user):
            response = await client.post(
                f"/api/workspaces/{test_workspace.id}/members",
                headers=auth_headers2,
                json={"email": "test@example.com", "role": "member"},
            )
            assert response.status_code == 403

        async def test_invite_member_duplicate(self, client, auth_headers, test_workspace, test_user):
            response = await client.post(
                f"/api/workspaces/{test_workspace.id}/members",
                headers=auth_headers,
                json={"email": "test@example.com", "role": "member"},
            )
            assert response.status_code == 400

        async def test_invite_member_user_not_found(self, client, auth_headers, test_workspace):
            response = await client.post(
                f"/api/workspaces/{test_workspace.id}/members",
                headers=auth_headers,
                json={"email": "nobody@example.com", "role": "member"},
            )
            assert response.status_code == 404

        async def test_remove_member_success(self, client, auth_headers, test_workspace, test_user2):
            await client.post(
                f"/api/workspaces/{test_workspace.id}/members",
                headers=auth_headers,
                json={"email": "test2@example.com", "role": "member"},
            )
            response = await client.delete(
                f"/api/workspaces/{test_workspace.id}/members/{test_user2.id}",
                headers=auth_headers,
            )
            assert response.status_code == 204

        async def test_remove_member_not_admin(self, client, auth_headers2, test_workspace, test_user):
            response = await client.delete(
                f"/api/workspaces/{test_workspace.id}/members/{test_user.id}",
                headers=auth_headers2,
            )
            assert response.status_code == 403

        async def test_remove_member_self(self, client, auth_headers, test_workspace, test_user):
            response = await client.delete(
                f"/api/workspaces/{test_workspace.id}/members/{test_user.id}",
                headers=auth_headers,
            )
            assert response.status_code == 400

        async def test_update_member_role_success(self, client, auth_headers, test_workspace, test_user2):
            await client.post(
                f"/api/workspaces/{test_workspace.id}/members",
                headers=auth_headers,
                json={"email": "test2@example.com", "role": "member"},
            )
            response = await client.put(
                f"/api/workspaces/{test_workspace.id}/members/{test_user2.id}",
                headers=auth_headers,
                json={"role": "admin"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["role"] == "admin"

        async def test_update_member_role_not_owner(self, client, auth_headers2, test_workspace, test_user):
            response = await client.put(
                f"/api/workspaces/{test_workspace.id}/members/{test_user.id}",
                headers=auth_headers2,
                json={"role": "admin"},
            )
            assert response.status_code == 403

        async def test_list_members(self, client, auth_headers, test_workspace):
            response = await client.get(
                f"/api/workspaces/{test_workspace.id}/members",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1
