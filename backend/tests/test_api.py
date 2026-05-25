import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_auth_login(client):
    resp = await client.post("/api/v1/auth/wechat-login", json={
        "code": "test_code_123",
        "nickname": "测试用户",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "user_id" in data
    assert data["is_new_user"] is True


@pytest.mark.asyncio
async def test_auth_login_existing_user(client):
    # Login twice - second should not be new
    resp1 = await client.post("/api/v1/auth/wechat-login", json={"code": "test_code_456"})
    assert resp1.status_code == 200

    resp2 = await client.post("/api/v1/auth/wechat-login", json={"code": "test_code_456"})
    assert resp2.status_code == 200
    assert resp2.json()["is_new_user"] is False


@pytest.mark.asyncio
async def test_get_teams_empty(client):
    resp = await client.get("/api/v1/teams")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 403  # no auth header


@pytest.mark.asyncio
async def test_user_profile(client):
    # Login first
    login = await client.post("/api/v1/auth/wechat-login", json={"code": "test_profile"})
    token = login.json()["access_token"]

    resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["selected_teams"] == []


@pytest.mark.asyncio
async def test_update_teams(client):
    login = await client.post("/api/v1/auth/wechat-login", json={"code": "test_teams"})
    token = login.json()["access_token"]

    resp = await client.put(
        "/api/v1/users/me/teams",
        json={"team_ids": [1, 5, 12]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["selected_teams"] == [1, 5, 12]


@pytest.mark.asyncio
async def test_update_too_many_teams(client):
    login = await client.post("/api/v1/auth/wechat-login", json={"code": "test_too_many"})
    token = login.json()["access_token"]

    resp = await client.put(
        "/api/v1/users/me/teams",
        json={"team_ids": [1, 2, 3, 4]},  # 4 teams > max 3
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_agent_chat_empty_message(client):
    login = await client.post("/api/v1/auth/wechat-login", json={"code": "test_agent"})
    token = login.json()["access_token"]

    resp = await client.post(
        "/api/v1/agent/chat",
        json={"message": "", "session_id": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_content_feed_empty(client):
    resp = await client.get("/api/v1/content/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_create_post(client):
    login = await client.post("/api/v1/auth/wechat-login", json={"code": "test_post"})
    token = login.json()["access_token"]

    resp = await client.post(
        "/api/v1/posts",
        json={"team_id": 1, "content": "Go Barcelona!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "Go Barcelona!"
    assert data["team_id"] == 1


@pytest.mark.asyncio
async def test_notification_settings(client):
    login = await client.post("/api/v1/auth/wechat-login", json={"code": "test_notify"})
    token = login.json()["access_token"]

    resp = await client.put(
        "/api/v1/notifications/settings",
        json={"match_reminder": 60, "daily_summary": "9:00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["match_reminder"] == 60
    assert resp.json()["daily_summary"] == "9:00"
