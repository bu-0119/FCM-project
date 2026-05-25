import httpx

from app.config import settings


async def code2session(code: str) -> dict | None:
    """Exchange WeChat login code for session info. Mocked for dev."""
    if settings.debug and not settings.wechat_appid:
        return {"openid": f"mock_openid_{code}", "session_key": "mock_session_key"}

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.wechat_appid,
        "secret": settings.wechat_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        if "errcode" in data and data["errcode"] != 0:
            return None
        return data
