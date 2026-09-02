"""
RAG 知识库 API

路由（由 main.py 以 prefix="/api/rag" 挂载，与其他 api 模块约定一致）：
- POST /kb            创建知识库
- GET  /kb            列出我的知识库
- POST /kb/{kb_id}/docs   上传文档（切分 -> 向量化 -> 入库）
- GET  /kb/{kb_id}/docs   列出文档
- POST /kb/{kb_id}/query  检索 + LLM 问答（LLM 不可用时降级，sources 照常返回）
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import get_current_user
from ..core.database import get_session
from ..models.database import User
from ..rag.embeddings import Embedder
from ..rag.models import KnowledgeBase, KnowledgeChunk, KnowledgeDoc
from ..rag.vector_store import VectorStore, split_text
from ..services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()

# 模块级单例：向量化器与向量存储（Embedder 内部自动降级，可离线运行）
embedder = Embedder()
vector_store = VectorStore(embedder=embedder)

# 问答时拼入 prompt 的最大片段数与片段长度
MAX_CONTEXT_CHUNKS = 8
MAX_CONTEXT_CHARS_PER_CHUNK = 800


# ============ 请求模型 ============

class KBCreate(BaseModel):
    """创建知识库请求"""

    name: str = Field(..., min_length=1, max_length=200, description="知识库名称")
    description: str = Field("", description="知识库描述")


class DocCreate(BaseModel):
    """上传文档请求"""

    title: str = Field(..., min_length=1, max_length=300, description="文档标题")
    content: str = Field(..., min_length=1, description="文档正文")
    source: Optional[str] = Field(None, max_length=500, description="来源（文件名/URL 等）")


class QueryRequest(BaseModel):
    """知识库问答请求"""

    question: str = Field(..., min_length=1, description="问题")
    top_k: int = Field(5, ge=1, le=20, description="检索片段数")


# ============ 辅助函数 ============

async def _get_owned_kb(db: AsyncSession, kb_id: int, user: User) -> KnowledgeBase:
    """获取知识库并校验归属。

    Args:
        db: 数据库会话
        kb_id: 知识库 ID
        user: 当前用户

    Returns:
        知识库对象

    Raises:
        HTTPException: 404 不存在或不属于当前用户
    """
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


# ============ 知识库管理 ============

@router.post("/kb")
async def create_kb(
    req: KBCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """创建知识库"""
    kb = KnowledgeBase(
        name=req.name,
        description=req.description or None,
        user_id=user.id,
        doc_count=0,
        chunk_count=0,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "doc_count": kb.doc_count,
        "chunk_count": kb.chunk_count,
        "created_at": kb.created_at,
    }


@router.get("/kb")
async def list_kb(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """列出当前用户的知识库"""
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.user_id == user.id)
        .order_by(KnowledgeBase.created_at.desc())
    )
    kbs = result.scalars().all()
    return [
        {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "doc_count": kb.doc_count,
            "chunk_count": kb.chunk_count,
            "created_at": kb.created_at,
        }
        for kb in kbs
    ]


# ============ 文档管理 ============

@router.post("/kb/{kb_id}/docs")
async def upload_doc(
    kb_id: int,
    req: DocCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """上传文档：切分正文 -> 向量化 -> 切片入库 -> 更新统计。

    文档初始状态为 ingesting，全部成功后置为 ready；
    向量化 / 入库失败置为 failed 并返回 500。
    """
    kb = await _get_owned_kb(db, kb_id, user)

    doc = KnowledgeDoc(
        kb_id=kb.id,
        title=req.title,
        source=req.source,
        status="ingesting",
        chunk_count=0,
    )
    db.add(doc)
    await db.flush()  # 获取 doc.id

    try:
        # 1. 切分（段落优先，~500 字符，50 字符重叠）
        pieces = split_text(req.content, chunk_size=500, overlap=50)
        if not pieces:
            raise ValueError("文档内容切分为空")

        # 2. 批量向量化（Ollama 不可用时 Embedder 内部自动降级哈希向量）
        embeddings = await embedder.embed(pieces)

        # 3. 切片入库
        chunks = [
            {
                "doc_id": doc.id,
                "kb_id": kb.id,
                "content": piece,
                "chunk_index": idx,
                "embedding": embeddings[idx],
                "metadata": {
                    "title": req.title,
                    "source": req.source,
                    "chunk_index": idx,
                },
            }
            for idx, piece in enumerate(pieces)
        ]
        await vector_store.add_chunks(db, chunks)

        # 4. 更新文档与知识库统计
        doc.chunk_count = len(pieces)
        doc.status = "ready"
        kb.doc_count = (kb.doc_count or 0) + 1
        kb.chunk_count = (kb.chunk_count or 0) + len(pieces)

        await db.commit()
        await db.refresh(doc)
        return {
            "id": doc.id,
            "kb_id": kb.id,
            "title": doc.title,
            "source": doc.source,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "created_at": doc.created_at,
        }
    except Exception as exc:
        await db.rollback()
        # 回滚后文档可能已不存在（flush 未提交），重新建失败记录
        logger.error("文档入库失败 kb_id=%s title=%s: %s", kb_id, req.title, exc)
        failed_doc = KnowledgeDoc(
            kb_id=kb.id,
            title=req.title,
            source=req.source,
            status="failed",
            chunk_count=0,
        )
        failed_doc.error_message = str(exc)[:1000]
        db.add(failed_doc)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"文档处理失败: {exc}")


@router.get("/kb/{kb_id}/docs")
async def list_docs(
    kb_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """列出知识库下的文档"""
    kb = await _get_owned_kb(db, kb_id, user)

    result = await db.execute(
        select(KnowledgeDoc)
        .where(KnowledgeDoc.kb_id == kb.id)
        .order_by(KnowledgeDoc.created_at.desc())
    )
    docs = result.scalars().all()
    return [
        {
            "id": doc.id,
            "kb_id": doc.kb_id,
            "title": doc.title,
            "source": doc.source,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "created_at": doc.created_at,
        }
        for doc in docs
    ]


# ============ 检索问答 ============

@router.post("/kb/{kb_id}/query")
async def query_kb(
    kb_id: int,
    req: QueryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """知识库问答：问题向量化 -> 相似度检索 -> 拼接上下文 -> LLM 生成。

    LLM 不可用时降级返回 answer="[LLM未就绪]"，但检索 sources 正常返回。
    """
    kb = await _get_owned_kb(db, kb_id, user)

    # 1. 问题向量化（同样支持离线降级）
    query_vectors = await embedder.embed([req.question])
    query_embedding = query_vectors[0]

    # 2. 向量检索
    sources = await vector_store.search(
        db, kb_id=kb.id, query_embedding=query_embedding, top_k=req.top_k
    )

    if not sources:
        return {
            "answer": "知识库中暂无相关资料，请先上传文档。",
            "sources": [],
            "provider": "empty",
        }

    # 3. 拼接上下文
    context_parts: List[str] = []
    for idx, item in enumerate(sources[:MAX_CONTEXT_CHUNKS], start=1):
        content = item["content"][:MAX_CONTEXT_CHARS_PER_CHUNK]
        context_parts.append(f"[资料{idx}] 来源：{item['title']}\n{content}")
    context = "\n\n".join(context_parts)

    prompt = (
        "请基于以下资料回答用户问题。若资料中没有相关信息，请如实说明，"
        "不要编造内容。\n\n"
        f"【参考资料】\n{context}\n\n"
        f"【用户问题】\n{req.question}"
    )

    # 4. 调用 LLM；不可用则降级（sources 照常返回）
    llm = LLMService()
    try:
        answer = await llm.generate(
            prompt,
            system_prompt="你是知识库助手，基于资料回答",
            temperature=0.3,
        )
        provider = "llm"
        if not answer or not answer.strip():
            answer = "[LLM未就绪] 暂未生成回答，请稍后重试或检查 LLM 服务。"
            provider = "fallback"
    except Exception as exc:
        logger.warning("LLM 生成失败，降级返回: %s", exc)
        answer = "[LLM未就绪] 无法连接大模型服务（请启动 Ollama 或配置 OPENAI_API_KEY）。以下为检索到的相关资料片段。"
        provider = "fallback"

    return {
        "answer": answer,
        "sources": sources,
        "provider": provider,
    }
