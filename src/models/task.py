"""Task model and related enums."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""
    
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class TaskType(str, Enum):
    """Type of development task."""
    
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    DOCS = "docs"
    TEST = "test"
    CHORE = "chore"


class Intent(str, Enum):
    """User message intent classification."""
    
    QUERY = "query"
    TASK_NEW = "task_new"
    TASK_CONTINUE = "task_continue"
    TASK_LIST = "task_list"
    TASK_ABORT = "task_abort"


class IntentResult(BaseModel):
    """Result of intent classification."""
    
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    needs_clarification: bool = False
    clarification_question: str | None = None
    extracted_info: dict[str, Any] = Field(default_factory=dict)


class TaskPlan(BaseModel):
    """Execution plan for a task."""
    
    objetivo: str
    archivos: list[str]
    pasos: list[dict[str, Any]]
    estimacion: str
    dependencias: list[str] = Field(default_factory=list)


class Task(BaseModel):
    """Development task model."""
    
    # Identification
    id: str = Field(default_factory=lambda: f"task-{uuid4().hex[:8]}")
    
    # Telegram info
    telegram_user_id: int
    telegram_chat_id: int
    
    # Task info
    description: str
    repo_url: str
    branch: str = ""
    task_type: TaskType = TaskType.FEATURE
    
    # Status
    status: TaskStatus = TaskStatus.PENDING
    current_step: int = 0
    total_steps: int = 0
    
    # Plan and execution
    plan: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    
    # Clarification
    clarification_round: int = 0
    max_clarification_rounds: int = 10
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    # Checkpoint
    last_checkpoint_at: datetime | None = None
    checkpoint_data: dict[str, Any] | None = None
    
    def to_summary(self) -> dict[str, Any]:
        """Get task summary for display."""
        return {
            "id": self.id,
            "description": self.description[:50] + "..." if len(self.description) > 50 else self.description,
            "status": self.status.value,
            "progress": f"{self.current_step}/{self.total_steps}" if self.total_steps > 0 else "N/A",
            "created_at": self.created_at.isoformat(),
        }
    
    def can_clarify(self) -> bool:
        """Check if more clarification rounds are allowed."""
        return self.clarification_round < self.max_clarification_rounds
    
    def increment_clarification(self) -> None:
        """Increment clarification round counter."""
        self.clarification_round += 1
        self.updated_at = datetime.utcnow()
