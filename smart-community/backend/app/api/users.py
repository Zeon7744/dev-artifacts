"""用户API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_session
from ..core.auth import get_current_user
from ..models.database import User

router = APIRouter()

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role.value,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
