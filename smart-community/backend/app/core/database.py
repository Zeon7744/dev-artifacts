"""
数据库初始化与会话管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager
from .config import settings
from ..models.database import Base

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """创建所有表"""
    import os
    # 确保数据目录存在
    data_dir = settings.BASE_DIR / "data"
    os.makedirs(data_dir, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session():
    """获取数据库会话"""
    async with async_session() as session:
        yield session
