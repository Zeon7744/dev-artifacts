"""社区API - 帖子/评论"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_session
from ..core.auth import get_current_user
from ..models.database import User, Post, Comment

router = APIRouter()

class PostCreate(BaseModel):
    title: str
    content: str
    post_type: str = "discussion"
    tags: list = []

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None

@router.get("/posts")
async def list_posts(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit))
    posts = result.scalars().all()
    return [{"id": p.id, "title": p.title, "post_type": p.post_type,
             "author": p.author.username if p.author else "unknown",
             "like_count": p.like_count, "comment_count": p.comment_count,
             "tags": p.tags, "created_at": p.created_at.isoformat() if p.created_at else None} for p in posts]

@router.post("/posts")
async def create_post(req: PostCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    post = Post(author_id=user.id, title=req.title, content=req.content, post_type=req.post_type, tags=req.tags)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return {"id": post.id, "title": post.title, "status": "created"}

@router.get("/posts/{post_id}")
async def get_post(post_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.view_count += 1
    await db.commit()
    return {"id": post.id, "title": post.title, "content": post.content, "post_type": post.post_type,
            "author": post.author.username if post.author else "unknown",
            "like_count": post.like_count, "comment_count": post.comment_count,
            "view_count": post.view_count, "tags": post.tags}

@router.post("/posts/{post_id}/comments")
async def add_comment(post_id: int, req: CommentCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    comment = Comment(post_id=post_id, author_id=user.id, content=req.content, parent_id=req.parent_id)
    db.add(comment)
    post = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if post:
        post.comment_count += 1
    await db.commit()
    return {"id": comment.id, "status": "created"}
