"""
数据库初始化与会话管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings
from ..models.database import Base

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """创建所有表"""
    import os
    # 确保数据目录存在
    data_dir = settings.BASE_DIR / "data"
    os.makedirs(data_dir, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    """FastAPI 依赖注入用的 async generator"""
    async with async_session() as session:
        yield session
