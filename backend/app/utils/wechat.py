import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def code2session(code: str) -> dict:
    """Exchange WeChat login code for session info. Returns dict with openid or raises."""
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
        logger.info(f"WeChat jscode2session response: {data}")
        if "errcode" in data and data["errcode"] != 0:
            errmsg = data.get("errmsg", "unknown")
            raise ValueError(f"WeChat API error [{data['errcode']}]: {errmsg}")
        return data
