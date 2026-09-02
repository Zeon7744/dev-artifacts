"""
RAG 知识库模块

- models: 知识库 / 文档 / 切片 ORM 模型
- embeddings: 文本向量化（优先 Ollama，失败自动降级为纯 Python 哈希向量）
- vector_store: 基于 SQLAlchemy 的向量存储与相似度检索
- api.rag: RAG API 路由（文档上传、切片入库、检索问答）
"""
# 导入模型以确保表注册到 Base.metadata（配合 init_db 自动建表）
from . import models  # noqa: F401

__all__ = ["models"]
