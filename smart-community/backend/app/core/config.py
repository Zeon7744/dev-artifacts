"""
AI Smart Community - 智能社区平台
核心配置
"""
from pathlib import Path
from typing import Optional
import os


class Settings:
    """应用配置"""

    # 基础
    APP_NAME: str = "AI Smart Community"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # 路径
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"

    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:////tmp/smart_community.db"
    )

    # Redis (可选, 用于缓存和任务队列)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_REDIS: bool = os.getenv("USE_REDIS", "false").lower() == "true"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # AI / LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # ollama / openai
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 工作流
    MAX_WORKFLOW_STEPS: int = 50
    WORKFLOW_TIMEOUT_SECONDS: int = 3600

    # 文件上传
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set = {".py", ".json", ".md", ".txt", ".csv", ".pdf"}

    # 社区
    MAX_POST_LENGTH: int = 10000
    RATE_LIMIT_PER_MINUTE: int = 60


settings = Settings()
