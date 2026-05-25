from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.deps import get_current_user_id
from app.api.v1.schemas import BaseSchema
from app.models import User, Post, Comment
from app.services.social import social_service

router = APIRouter(tags=["social"])


async def _get_user(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class PostCreate(BaseModel):
    team_id: int
    content: str
    images: list[str] = []


class PostResponse(BaseSchema):
    id: str
    user_id: str
    team_id: int
    content: str
    images: list
    like_count: int
    comment_count: int
    created_at: str


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseSchema):
    id: str
    post_id: str
    user_id: str
    content: str
    created_at: str


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    page: int
    size: int


@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    team_id: int | None = Query(None),
    sort: str = Query("latest", pattern="^(latest|hot)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if team_id is not None:
        conditions.append(Post.team_id == team_id)

    base_query = select(Post)
    if conditions:
        base_query = base_query.where(*conditions)

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    if sort == "hot":
        order = Post.like_count.desc()
    else:
        order = Post.created_at.desc()

    items_query = base_query.order_by(order).offset((page - 1) * size).limit(size)
    result = await db.execute(items_query)
    items = result.scalars().all()

    return PostListResponse(items=items, total=total, page=page, size=size)


@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    req: PostCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    return await social_service.create_post(db, user, req.team_id, req.content, req.images)


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    result = await db.execute(select(Post).where(Post.id == post_id, Post.user_id == user.id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)


@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    return await social_service.toggle_like(db, user, post_id)


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    post_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return result.scalars().all()


@router.post("/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    req: CommentCreate,
    post_id: str = Query(..., alias="post_id"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    return await social_service.create_comment(db, user, post_id, req.content)
