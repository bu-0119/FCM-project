from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.models import User
from app.utils.wechat import code2session

router = APIRouter(prefix="/auth", tags=["auth"])


class WechatLoginRequest(BaseModel):
    code: str
    nickname: str | None = None
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    user_id: str
    is_new_user: bool = False


@router.post("/wechat-login", response_model=TokenResponse)
async def wechat_login(req: WechatLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        session_info = await code2session(req.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    openid = session_info["openid"]
    result = await db.execute(select(User).where(User.wechat_openid == openid))
    user = result.scalar_one_or_none()

    is_new = False
    if user is None:
        is_new = True
        user = User(
            wechat_openid=openid,
            nickname=req.nickname,
            avatar_url=req.avatar_url,
        )
        db.add(user)
        await db.flush()

    token = create_access_token({"sub": str(user.id), "openid": openid})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        is_new_user=is_new,
    )
