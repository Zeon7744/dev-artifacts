"""Agent API - 创建/发布/调用Agent"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..core.database import get_session
from ..core.auth import get_current_user
from ..models.database import User, Agent, AgentType
from ..services.llm_service import LLMService

router = APIRouter()

class AgentCreate(BaseModel):
    name: str
    description: str = ""
    agent_type: str = "custom"
    system_prompt: str = ""
    tools: List[str] = []
    llm_config: Dict = {}
    tags: List[str] = []

class AgentChat(BaseModel):
    message: str
    agent_id: int

@router.get("/")
async def list_agents(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Agent)
        .where(Agent.is_published == True)  # noqa: E712
        .options(selectinload(Agent.owner))
        .offset(skip).limit(limit)
    )
    agents = result.scalars().all()
    return [{"id": a.id, "name": a.name, "description": a.description, "agent_type": a.agent_type.value,
             "owner": a.owner.username if a.owner else "unknown", "rating": a.rating, "tags": a.tags} for a in agents]

@router.post("/")
async def create_agent(req: AgentCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    try:
        agent_type = AgentType(req.agent_type)
    except ValueError:
        agent_type = AgentType.CUSTOM
    agent = Agent(user_id=user.id, name=req.name, description=req.description,
                  agent_type=agent_type, system_prompt=req.system_prompt,
                  tools=req.tools, llm_config=req.llm_config, tags=req.tags)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return {"id": agent.id, "name": agent.name, "status": "created"}

@router.post("/chat")
async def chat_with_agent(req: AgentChat, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Agent).where(Agent.id == req.agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    llm = LLMService()
    try:
        response = await llm.generate(req.message, system_prompt=agent.system_prompt or "You are a helpful assistant.")
        provider = "llm"
    except Exception as e:
        # LLM 不可用时优雅降级，不返回 500
        response = f"[本地LLM未就绪] 已收到你的消息：{req.message[:200]}。请启动 Ollama 或配置 OPENAI_API_KEY 后获得 AI 回复。"
        provider = "fallback"
    return {"response": response, "agent": agent.name, "provider": provider}
