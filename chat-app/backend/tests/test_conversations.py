import pytest


class TestConversations:
    class TestCreate:
        async def test_create_conversation_success(self, client, auth_headers, test_user2):
            response = await client.post("/api/conversations", headers=auth_headers, json={
                "type": "direct",
                "name": "New Conversation",
                "participant_ids": [test_user2.id],
            })
            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "direct"
            assert data["name"] == "New Conversation"
            assert len(data["participants"]) == 2

        async def test_create_conversation_no_auth(self, client, test_user2):
            response = await client.post("/api/conversations", json={
                "type": "direct",
                "name": "New Conversation",
                "participant_ids": ["some-id"],
            })
            assert response.status_code == 401

        async def test_create_conversation_missing_participants(self, client, auth_headers):
            response = await client.post("/api/conversations", headers=auth_headers, json={
                "type": "direct",
                "name": "No Participants",
            })
            assert response.status_code == 422

    class TestList:
        async def test_list_conversations(self, client, auth_headers, test_conversation):
            response = await client.get("/api/conversations", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1

        async def test_list_conversations_no_auth(self, client):
            response = await client.get("/api/conversations")
            assert response.status_code == 401

        async def test_list_conversations_only_my_conversations(self, client, auth_headers2, test_conversation):
            response = await client.get("/api/conversations", headers=auth_headers2)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert any(c["id"] == test_conversation.id for c in data)

    class TestGet:
        async def test_get_conversation_success(self, client, auth_headers, test_conversation):
            response = await client.get(f"/api/conversations/{test_conversation.id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == test_conversation.id

        async def test_get_conversation_not_found(self, client, auth_headers):
            response = await client.get("/api/conversations/nonexistent-id", headers=auth_headers)
            assert response.status_code == 404

        async def test_get_conversation_no_auth(self, client, test_conversation):
            response = await client.get(f"/api/conversations/{test_conversation.id}")
            assert response.status_code == 401

    class TestMessages:
        async def test_get_messages_success(self, client, auth_headers, test_conversation):
            response = await client.get(
                f"/api/conversations/{test_conversation.id}/messages",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data

        async def test_get_messages_pagination(self, client, auth_headers, test_conversation):
            response = await client.get(
                f"/api/conversations/{test_conversation.id}/messages?page=1&page_size=5",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 1
            assert data["page_size"] == 5

        async def test_get_messages_no_auth(self, client, test_conversation):
            response = await client.get(f"/api/conversations/{test_conversation.id}/messages")
            assert response.status_code == 401
