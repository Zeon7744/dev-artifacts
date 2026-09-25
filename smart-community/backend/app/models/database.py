"""
数据库模型 - 用户、工作流、Agent、社区
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


# ============ 枚举 ============

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    DEVELOPER = "developer"


class WorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, enum.Enum):
    ANALYST = "analyst"
    WATCHER = "watcher"
    REPORTER = "reporter"
    CUSTOM = "custom"


# ============ 用户系统 ============

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100))
    avatar_url = Column(String(500))
    bio = Column(Text)
    role = Column(SAEnum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    workflows = relationship("Workflow", back_populates="owner")
    agents = relationship("Agent", back_populates="owner")
    posts = relationship("Post", back_populates="author")
    tasks = relationship("TaskExecution", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    permissions = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="api_keys")


# ============ 工作流引擎 ============

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(SAEnum(WorkflowStatus), default=WorkflowStatus.DRAFT)

    # DAG 定义: nodes + edges
    # nodes: [{"id": "n1", "type": "trigger|action|condition|ai", "config": {...}}, ...]
    # edges: [{"from": "n1", "to": "n2", "condition": "..."}, ...]
    definition = Column(JSON, nullable=False, default=dict)

    # 调度
    schedule_cron = Column(String(100))  # cron 表达式, 空=手动触发
    is_scheduled = Column(Boolean, default=False)

    # 统计
    run_count = Column(Integer, default=0)
    last_run_at = Column(DateTime)
    last_run_status = Column(String(20))

    # 元数据
    is_public = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow")


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    trigger_type = Column(String(20))  # manual / schedule / webhook / api
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)

    # 节点执行记录
    # [{"node_id": "n1", "status": "success", "output": {...}, "duration_ms": 150}, ...]
    node_results = Column(JSON, default=list)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="executions")


# ============ Agent 系统 ============

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    agent_type = Column(SAEnum(AgentType), default=AgentType.CUSTOM)

    # Agent 配置
    system_prompt = Column(Text)
    tools = Column(JSON, default=list)  # 可用工具列表
    llm_config = Column(JSON, default=dict)  # {"provider": "ollama", "model": "llama3.2"}
    memory_config = Column(JSON, default=dict)  # 记忆配置

    # 市场
    is_published = Column(Boolean, default=False)
    install_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)

    # 元数据
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="agents")


# ============ 任务调度 ============

class TaskExecution(Base):
    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_type = Column(String(50), nullable=False)  # workflow_run / agent_run / scheduled
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING)

    # 任务配置
    config = Column(JSON, nullable=False)
    # workflow_run: {"workflow_id": 1, "input": {...}}
    # agent_run: {"agent_id": 1, "message": "..."}
    # scheduled: {"cron": "0 9 * * *", "action": "..."}

    # 结果
    result = Column(JSON)
    error = Column(Text)

    # 调度
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tasks")


# ============ 社区 ============

class AgentConversation(Base):
    """Agent 对话历史（第五轮）：按 用户×Agent 维度持久化消息，刷新不丢。"""

    __tablename__ = "agent_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    provider = Column(String(20))  # llm / fallback
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(String(20), default="discussion")  # discussion / share / tutorial / question

    # 关联
    workflow_id = Column(Integer, ForeignKey("workflows.id"))  # 分享的workflow
    agent_id = Column(Integer, ForeignKey("agents.id"))  # 分享的agent

    # 统计
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    tags = Column(JSON, default=list)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"))  # 嵌套回复
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")


# ============ 智能运维 ============

class SystemMetric(Base):
    """系统监控指标"""
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    labels = Column(JSON)  # {"host": "...", "service": "..."}
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class Alert(Base):
    """告警记录"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False)  # cpu / memory / error / workflow_fail
    severity = Column(String(20), default="warning")  # info / warning / critical
    title = Column(String(200), nullable=False)
    message = Column(Text)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
