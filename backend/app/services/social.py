import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, Comment, Like, User


class SocialService:
    """Business logic for posts, comments, and likes."""

    async def create_post(
        self, db: AsyncSession, user: User, team_id: int, content: str, images: list[str] | None = None
    ) -> Post:
        post = Post(
            id=uuid.uuid4(),
            user_id=user.id,
            team_id=team_id,
            content=content,
            images=images or [],
        )
        db.add(post)
        await db.flush()
        return post

    async def create_comment(
        self, db: AsyncSession, user: User, post_id: str, content: str
    ) -> Comment:
        comment = Comment(
            id=uuid.uuid4(),
            post_id=post_id,
            user_id=user.id,
            content=content,
        )
        db.add(comment)

        # Update post comment count
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            post.comment_count = (post.comment_count or 0) + 1
            db.add(post)

        await db.flush()
        return comment

    async def toggle_like(self, db: AsyncSession, user: User, post_id: str) -> dict:
        """Toggle like on a post. Returns {"liked": bool, "count": int}."""
        result = await db.execute(
            select(Like).where(Like.post_id == post_id, Like.user_id == user.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            await db.delete(existing)
            liked = False
        else:
            like = Like(id=uuid.uuid4(), post_id=post_id, user_id=user.id)
            db.add(like)
            liked = True

        # Update post like count
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            count_result = await db.execute(
                select(func.count()).select_from(Like).where(Like.post_id == post_id)
            )
            post.like_count = count_result.scalar() or 0
            db.add(post)

        await db.flush()
        return {"liked": liked, "count": post.like_count if post else 0}


social_service = SocialService()
