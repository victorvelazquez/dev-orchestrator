"""Database models and session management."""

from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.models.task import Task, TaskStatus


Base = declarative_base()

# Global engine and session factory
_engine = None
_SessionLocal = None


class TaskModel(Base):
    """SQLAlchemy model for tasks."""
    
    __tablename__ = "tasks"
    
    id = Column(String(50), primary_key=True)
    telegram_user_id = Column(Integer, nullable=False, index=True)
    telegram_chat_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    repo_url = Column(String(500), nullable=False)
    branch = Column(String(100), default="")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    plan = Column(Text, nullable=True)  # JSON string
    result = Column(Text, nullable=True)  # JSON string
    error = Column(Text, nullable=True)
    clarification_round = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class TaskLogModel(Base):
    """SQLAlchemy model for task logs."""
    
    __tablename__ = "task_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    step = Column(Integer, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string


class ConversationModel(Base):
    """SQLAlchemy model for conversation history."""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)


def init_database(database_url: str) -> None:
    """Initialize database connection and create tables."""
    global _engine, _SessionLocal
    
    _engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    )
    _SessionLocal = sessionmaker(bind=_engine)
    
    # Create tables
    Base.metadata.create_all(_engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get database session as context manager."""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def save_task(task: Task) -> None:
    """Save a task to database."""
    import json
    
    with get_session() as session:
        model = TaskModel(
            id=task.id,
            telegram_user_id=task.telegram_user_id,
            telegram_chat_id=task.telegram_chat_id,
            description=task.description,
            repo_url=task.repo_url,
            branch=task.branch,
            status=task.status,
            current_step=task.current_step,
            total_steps=task.total_steps,
            plan=json.dumps(task.plan) if task.plan else None,
            clarification_round=task.clarification_round,
            created_at=task.created_at,
        )
        session.add(model)


def get_task(task_id: str) -> Task | None:
    """Get task by ID."""
    import json
    
    with get_session() as session:
        model = session.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if model is None:
            return None
        
        return Task(
            id=model.id,
            telegram_user_id=model.telegram_user_id,
            telegram_chat_id=model.telegram_chat_id,
            description=model.description,
            repo_url=model.repo_url,
            branch=model.branch,
            status=model.status,
            current_step=model.current_step,
            total_steps=model.total_steps,
            plan=json.loads(model.plan) if model.plan else None,
            result=json.loads(model.result) if model.result else None,
            error=model.error,
            clarification_round=model.clarification_round,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


def update_task(task: Task) -> None:
    """Update existing task."""
    import json
    
    with get_session() as session:
        model = session.query(TaskModel).filter(TaskModel.id == task.id).first()
        
        if model is None:
            raise ValueError(f"Task {task.id} not found")
        
        model.status = task.status
        model.current_step = task.current_step
        model.total_steps = task.total_steps
        model.plan = json.dumps(task.plan) if task.plan else None
        model.result = json.dumps(task.result) if task.result else None
        model.error = task.error
        model.clarification_round = task.clarification_round
        model.updated_at = datetime.utcnow()
        model.started_at = task.started_at
        model.completed_at = task.completed_at


def get_user_tasks(user_id: int, limit: int = 10) -> list[Task]:
    """Get tasks for a user."""
    import json
    
    with get_session() as session:
        models = (
            session.query(TaskModel)
            .filter(TaskModel.telegram_user_id == user_id)
            .order_by(TaskModel.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return [
            Task(
                id=m.id,
                telegram_user_id=m.telegram_user_id,
                telegram_chat_id=m.telegram_chat_id,
                description=m.description,
                repo_url=m.repo_url,
                status=m.status,
                created_at=m.created_at,
            )
            for m in models
        ]


def get_active_task(user_id: int) -> Task | None:
    """Get currently active task for user."""
    active_statuses = [
        TaskStatus.PENDING_APPROVAL,
        TaskStatus.APPROVED,
        TaskStatus.IN_PROGRESS,
        TaskStatus.PAUSED,
    ]
    
    with get_session() as session:
        model = (
            session.query(TaskModel)
            .filter(
                TaskModel.telegram_user_id == user_id,
                TaskModel.status.in_(active_statuses),
            )
            .order_by(TaskModel.created_at.desc())
            .first()
        )
        
        if model is None:
            return None
        
        return get_task(model.id)
