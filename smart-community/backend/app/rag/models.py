"""
RAG 知识库 ORM 模型

- KnowledgeBase: 知识库
- KnowledgeDoc: 知识库下的文档（ingesting/ready/failed）
- KnowledgeChunk: 文档切片，含向量与元数据

注意：embedding 以 JSON 列存储 float 列表，纯 Python 检索，不依赖向量数据库。
"""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from ..models.database import Base


class KnowledgeBase(Base):
    """知识库"""

    __tablename__ = "kb"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(200), nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    user_id: int = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # 统计字段（由上传流程维护）
    doc_count: int = Column(Integer, default=0, nullable=False)
    chunk_count: int = Column(Integer, default=0, nullable=False)

    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    docs = relationship(
        "KnowledgeDoc",
        back_populates="kb",
        cascade="all, delete-orphan",
    )
    chunks = relationship(
        "KnowledgeChunk",
        back_populates="kb",
        cascade="all, delete-orphan",
    )


class KnowledgeDoc(Base):
    """知识库文档"""

    __tablename__ = "kb_docs"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    kb_id: int = Column(
        Integer, ForeignKey("kb.id"), nullable=False, index=True
    )
    title: str = Column(String(300), nullable=False)
    source: Optional[str] = Column(String(500), nullable=True)

    # 状态：ingesting（处理中）/ ready（就绪）/ failed（失败）
    status: str = Column(String(20), default="ingesting", nullable=False, index=True)
    chunk_count: int = Column(Integer, default=0, nullable=False)
    error_message: Optional[str] = Column(Text, nullable=True)

    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    kb = relationship("KnowledgeBase", back_populates="docs")
    chunks = relationship(
        "KnowledgeChunk",
        back_populates="doc",
        cascade="all, delete-orphan",
    )


class KnowledgeChunk(Base):
    """文档切片（含向量）"""

    __tablename__ = "kb_chunks"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    doc_id: int = Column(
        Integer, ForeignKey("kb_docs.id"), nullable=False, index=True
    )
    kb_id: int = Column(
        Integer, ForeignKey("kb.id"), nullable=False, index=True
    )

    content: str = Column(Text, nullable=False)
    chunk_index: int = Column(Integer, default=0, nullable=False)

    # 向量：list[float]，以 JSON 存储（Ollama 768 维 / 降级哈希 256 维）
    embedding: Optional[list] = Column(JSON, nullable=True)
    # 附加元数据：{"title": ..., "chunk_index": ..., ...}
    chunk_metadata: Optional[Dict[str, Any]] = Column(
        "metadata", JSON, nullable=True
    )

    # 关系
    doc = relationship("KnowledgeDoc", back_populates="chunks")
    kb = relationship("KnowledgeBase", back_populates="chunks")
