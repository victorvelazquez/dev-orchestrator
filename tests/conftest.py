"""Global pytest fixtures for Dev Task Orchestrator."""

import asyncio
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.models.database import Base
from src.models.task import Task, TaskStatus, TaskType


# ============================================================================
# Event Loop
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create database session for tests."""
    session_factory = sessionmaker(bind=db_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ============================================================================
# Task Fixtures
# ============================================================================

@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    return Task(
        id="task-test-001",
        repo_url="https://github.com/test/repo",
        branch="feature/test-task",
        description="Add unit tests for user service",
        status=TaskStatus.PENDING,
        task_type=TaskType.FEATURE,
        telegram_user_id=123456789,
        telegram_chat_id=123456789,
    )


@pytest.fixture
def sample_task_with_plan(sample_task: Task) -> Task:
    """Task with generated plan."""
    sample_task.plan = {
        "objetivo": "Agregar tests unitarios",
        "archivos": ["tests/test_user_service.py"],
        "pasos": [
            {"paso": 1, "descripcion": "Crear archivo de tests"},
            {"paso": 2, "descripcion": "Implementar test_create_user"},
            {"paso": 3, "descripcion": "Implementar test_get_user"},
        ],
        "estimacion": "15 minutos",
    }
    sample_task.status = TaskStatus.PENDING_APPROVAL
    return sample_task


# ============================================================================
# Git Fixtures
# ============================================================================

@pytest.fixture
def git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary Git repository."""
    import subprocess
    
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path, check=True, capture_output=True
    )
    
    # Create initial commit
    readme = repo_path / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path, check=True, capture_output=True
    )
    
    yield repo_path


@pytest.fixture
def dev_tasks_dir(git_repo: Path) -> Path:
    """Create .dev-tasks directory in repo."""
    tasks_dir = git_repo / ".dev-tasks"
    tasks_dir.mkdir()
    return tasks_dir


# ============================================================================
# Telegram Fixtures
# ============================================================================

@pytest.fixture
def telegram_update() -> dict:
    """Create a mock Telegram Update object."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "date": 1706918400,
            "chat": {
                "id": 123456789,
                "type": "private",
                "username": "testuser",
            },
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "text": "/task Agregar tests unitarios al servicio de usuarios",
        },
    }


@pytest.fixture
def allowed_users() -> list[int]:
    """List of allowed Telegram user IDs for testing."""
    return [123456789, 987654321]


# ============================================================================
# AI Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_ai_response() -> dict:
    """Standard AI response for plan generation."""
    return {
        "objetivo": "Implementar feature solicitada",
        "archivos": ["src/main.py"],
        "pasos": [
            {"paso": 1, "descripcion": "Analizar código existente"},
            {"paso": 2, "descripcion": "Implementar cambios"},
            {"paso": 3, "descripcion": "Agregar tests"},
        ],
        "estimacion": "20 minutos",
    }


@pytest.fixture
def mock_intent_classification() -> dict:
    """Mock intent classification response."""
    return {
        "intent": "TASK_NEW",
        "confidence": 0.95,
        "extracted_info": {
            "repo": "https://github.com/test/repo",
            "description": "Agregar tests unitarios",
        },
    }
