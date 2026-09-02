"""RAG 知识库测试（离线哈希向量降级，sources 照常返回）"""
import uuid

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

SAMPLE_DOC = (
    "Smart Community 是一个智能社区平台。\n"
    "平台支持工作流编排、Agent 对话、社区发帖、定时调度与知识库检索等功能。\n"
    "知识库模块使用向量检索：文档被切分为片段并生成嵌入向量，"
    "查询时按余弦相似度返回最相关的资料片段。\n"
    "在没有 Ollama 或 OpenAI 服务时，系统会自动降级为本地哈希向量与降级回复，"
    "保证离线环境下检索能力依然可用。"
)


async def test_kb_create_upload_query(client, auth):
    """创建 KB -> 上传文本文档 -> 查询返回非空 sources"""
    headers = auth["headers"]

    # 1. 创建知识库
    kb_resp = await client.post(
        "/api/rag/kb",
        headers=headers,
        json={"name": f"测试知识库_{uuid.uuid4().hex[:6]}", "description": "pytest kb"},
    )
    assert kb_resp.status_code == 200, kb_resp.text
    kb_id = kb_resp.json()["id"]

    # 2. 上传文本文档（JSON 接口）
    doc_resp = await client.post(
        f"/api/rag/kb/{kb_id}/docs",
        headers=headers,
        json={"title": "平台介绍.txt", "content": SAMPLE_DOC, "source": "pytest"},
    )
    assert doc_resp.status_code == 200, doc_resp.text
    doc_data = doc_resp.json()
    assert doc_data["status"] == "ready"
    assert doc_data["chunk_count"] >= 1

    # 文档列表可见
    docs_resp = await client.get(f"/api/rag/kb/{kb_id}/docs", headers=headers)
    assert docs_resp.status_code == 200
    assert len(docs_resp.json()) == 1

    # 3. 检索问答：LLM 可能降级，但 sources 必须非空
    query_resp = await client.post(
        f"/api/rag/kb/{kb_id}/query",
        headers=headers,
        json={"question": "知识库在离线时如何工作？", "top_k": 3},
    )
    assert query_resp.status_code == 200, query_resp.text
    qdata = query_resp.json()
    assert "answer" in qdata
    assert qdata["sources"], "检索 sources 不应为空"
    # sources 中应包含文档内容/标题信息
    assert qdata["provider"] in ("llm", "fallback")


async def test_kb_access_requires_ownership(client, auth):
    """他人知识库不可访问（404）"""
    headers = auth["headers"]
    kb_resp = await client.post(
        "/api/rag/kb", headers=headers, json={"name": "私有知识库"}
    )
    kb_id = kb_resp.json()["id"]

    from tests.conftest import register_and_login
    other = await register_and_login(client, prefix="rag_other")
    resp = await client.get(
        f"/api/rag/kb/{kb_id}/docs", headers=other["headers"]
    )
    assert resp.status_code == 404, resp.text
