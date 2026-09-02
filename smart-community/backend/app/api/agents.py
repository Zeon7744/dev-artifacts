"""Agent API - 创建/发布/调用Agent"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    result = await db.execute(select(Agent).where(Agent.is_published == True).offset(skip).limit(limit))
    agents = result.scalars().all()
    return [{"id": a.id, "name": a.name, "description": a.description, "agent_type": a.agent_type.value,
             "owner": a.owner.username if a.owner else "unknown", "rating": a.rating, "tags": a.tags} for a in agents]

@router.post("/")
async def create_agent(req: AgentCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    agent = Agent(user_id=user.id, name=req.name, description=req.description,
                  agent_type=AgentType(req.agent_type), system_prompt=req.system_prompt,
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
    response = await llm.generate(req.message, system_prompt=agent.system_prompt or "You are a helpful assistant.")
    return {"response": response, "agent": agent.name}
