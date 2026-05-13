import pytest


class TestAgent:
    class TestCreateSession:
        async def test_create_session_success(self, client, auth_headers):
            response = await client.post("/api/agent/sessions", headers=auth_headers, json={
                "title": "My Agent Session",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "My Agent Session"
            assert data["status"] == "active"
            assert data["messages"] == []

        async def test_create_session_with_conversation_id(self, client, auth_headers, test_conversation):
            response = await client.post("/api/agent/sessions", headers=auth_headers, json={
                "conversation_id": test_conversation.id,
                "title": "Linked Session",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["conversation_id"] == test_conversation.id

        async def test_create_session_no_auth(self, client):
            response = await client.post("/api/agent/sessions", json={
                "title": "No Auth",
            })
            assert response.status_code == 401

    class TestListSessions:
        async def test_list_sessions(self, client, auth_headers, test_agent_session):
            response = await client.get("/api/agent/sessions", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) >= 1
            assert any(s["id"] == test_agent_session.id for s in data["items"])

        async def test_list_sessions_no_auth(self, client):
            response = await client.get("/api/agent/sessions")
            assert response.status_code == 401

        async def test_list_sessions_only_mine(self, client, auth_headers2, test_agent_session):
            response = await client.get("/api/agent/sessions", headers=auth_headers2)
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert not any(s["id"] == test_agent_session.id for s in data["items"])

    class TestGetSession:
        async def test_get_session_success(self, client, auth_headers, test_agent_session):
            response = await client.get(f"/api/agent/sessions/{test_agent_session.id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == test_agent_session.id
            assert data["title"] == "Test Agent Session"

        async def test_get_session_not_found(self, client, auth_headers):
            response = await client.get("/api/agent/sessions/nonexistent-id", headers=auth_headers)
            assert response.status_code == 404

        async def test_get_session_no_permission(self, client, auth_headers2, test_agent_session):
            response = await client.get(f"/api/agent/sessions/{test_agent_session.id}", headers=auth_headers2)
            assert response.status_code == 404

    class TestDeleteSession:
        async def test_delete_session_success(self, client, auth_headers, test_agent_session):
            response = await client.delete(f"/api/agent/sessions/{test_agent_session.id}", headers=auth_headers)
            assert response.status_code == 204

        async def test_delete_session_not_found(self, client, auth_headers):
            response = await client.delete("/api/agent/sessions/nonexistent-id", headers=auth_headers)
            assert response.status_code == 404

        async def test_delete_session_no_permission(self, client, auth_headers2, test_agent_session):
            response = await client.delete(f"/api/agent/sessions/{test_agent_session.id}", headers=auth_headers2)
            assert response.status_code == 404

    class TestRunAgent:
        async def test_run_agent_no_auth(self, client, test_agent_session):
            response = await client.post(f"/api/agent/sessions/{test_agent_session.id}/run", json={
                "message": "Hello",
            })
            assert response.status_code == 401

        async def test_run_agent_session_not_found(self, client, auth_headers):
            response = await client.post("/api/agent/sessions/nonexistent-id/run", headers=auth_headers, json={
                "message": "Hello",
            })
            assert response.status_code == 404
