"""
向量存储与相似度检索

- split_text: 纯函数文本切分（段落优先，超长段落滑窗切分，支持重叠）
- VectorStore: 基于 SQLAlchemy 的向量存取；
  检索时加载知识库全部切片向量，纯 Python 余弦相似度排序，
  不依赖 chromadb / faiss 等外部重依赖。
"""
import logging
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .embeddings import Embedder
from .models import KnowledgeChunk, KnowledgeDoc

logger = logging.getLogger(__name__)


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """文本切分（纯函数）。

    策略：
    1. 按空行（段落）优先聚合，尽量在段落边界切分；
    2. 单个超过 chunk_size 的段落，按字符滑窗硬切分；
    3. 滑窗 / 段落拼接处保留 overlap 字符的上下文重叠。

    Args:
        text: 原始文本
        chunk_size: 单块目标字符数（默认 500）
        overlap: 相邻块重叠字符数（默认 50）

    Returns:
        切分后的文本块列表（去除空白块）
    """
    if not text or not text.strip():
        return []

    overlap = max(0, min(overlap, chunk_size - 1))
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks: List[str] = []
    buffer = ""

    def flush() -> None:
        """将缓冲区内容作为一个块输出。"""
        nonlocal buffer
        if buffer.strip():
            chunks.append(buffer.strip())
        buffer = ""

    for para in paragraphs:
        # 超长段落：先把已有缓冲区落块，再对段落滑窗切分
        if len(para) > chunk_size:
            flush()
            start = 0
            while start < len(para):
                piece = para[start:start + chunk_size]
                chunks.append(piece.strip())
                start += chunk_size - overlap
            continue

        # 段落聚合：加入后不超长则累积，否则先落块（带重叠）
        candidate = f"{buffer}\n{para}" if buffer else para
        if len(candidate) <= chunk_size:
            buffer = candidate
        else:
            flush()
            buffer = para

    flush()
    return [c for c in chunks if c]


class VectorStore:
    """基于 SQLAlchemy 的向量存储与检索。"""

    def __init__(self, embedder: Optional[Embedder] = None) -> None:
        """初始化向量存储。

        Args:
            embedder: 向量化器，默认使用全局 Embedder()
        """
        self.embedder = embedder or Embedder()

    async def add_chunks(
        self,
        session: AsyncSession,
        chunks: List[Dict[str, Any]],
    ) -> int:
        """批量写入切片（含向量）。

        Args:
            session: 异步数据库会话
            chunks: 切片字典列表，每项含：
                doc_id, kb_id, content, chunk_index,
                embedding(list[float]), metadata(dict, 可选)

        Returns:
            成功写入的切片数量
        """
        if not chunks:
            return 0

        records = [
            KnowledgeChunk(
                doc_id=item["doc_id"],
                kb_id=item["kb_id"],
                content=item["content"],
                chunk_index=item.get("chunk_index", 0),
                embedding=item.get("embedding"),
                chunk_metadata=item.get("metadata") or {},
            )
            for item in chunks
        ]
        session.add_all(records)
        await session.flush()
        return len(records)

    async def search(
        self,
        session: AsyncSession,
        kb_id: int,
        query_embedding: Sequence[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """在指定知识库中做相似度检索。

        加载该知识库全部切片的向量，纯 Python 余弦相似度排序。
        向量缺失或维度不一致的切片记 0 分并跳过靠前排序。

        Args:
            session: 异步数据库会话
            kb_id: 知识库 ID
            query_embedding: 查询向量
            top_k: 返回前 K 条

        Returns:
            结果列表，每项：
            {"chunk_id", "content", "doc_id", "title", "score"}
            按 score 降序排列
        """
        result = await session.execute(
            select(KnowledgeChunk, KnowledgeDoc.title)
            .join(KnowledgeDoc, KnowledgeChunk.doc_id == KnowledgeDoc.id)
            .where(KnowledgeChunk.kb_id == kb_id)
        )
        rows = result.all()

        scored: List[Dict[str, Any]] = []
        for chunk, title in rows:
            if not chunk.embedding:
                continue
            score = Embedder.cosine_similarity(query_embedding, chunk.embedding)
            scored.append(
                {
                    "chunk_id": chunk.id,
                    "content": chunk.content,
                    "doc_id": chunk.doc_id,
                    "title": title,
                    "score": score,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]
