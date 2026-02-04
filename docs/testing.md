# Testing Strategy

## Estructura de Tests

```
tests/
├── conftest.py              # Fixtures globales
├── unit/
│   ├── test_intent_classifier.py
│   ├── test_task_manager.py
│   ├── test_state_manager.py
│   ├── test_plan_generator.py
│   ├── test_executor.py
│   ├── test_checkpoint.py
│   └── test_validators.py
├── integration/
│   ├── test_task_flow.py
│   ├── test_git_operations.py
│   ├── test_ai_planning.py
│   └── test_telegram_handler.py
└── mocks/
    ├── __init__.py
    ├── ai_mock.py
    ├── telegram_mock.py
    ├── github_mock.py
    └── docker_mock.py
```

## Configuración pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html:coverage_html",
    "--cov-fail-under=85",
]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (slower, external deps)",
    "slow: Tests that take > 1s",
    "ai: Tests that mock AI providers",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

## Fixtures Globales

```python
# tests/conftest.py
"""Global pytest fixtures for Dev Task Orchestrator."""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

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
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
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
    sample_task.status = TaskStatus.APPROVED
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
```

## Mocks

### AI Mock

```python
# tests/mocks/ai_mock.py
"""Mock implementations for AI providers."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockAnthropicClient:
    """Mock Anthropic client for testing."""

    def __init__(self, responses: dict[str, Any] | None = None):
        self.responses = responses or {}
        self.call_history: list[dict] = []

    async def generate_plan(self, task_description: str) -> dict:
        """Mock plan generation."""
        self.call_history.append({
            "method": "generate_plan",
            "args": {"task_description": task_description},
        })
        return self.responses.get("plan", {
            "objetivo": "Mock objective",
            "archivos": ["mock_file.py"],
            "pasos": [{"paso": 1, "descripcion": "Mock step"}],
            "estimacion": "5 minutos",
        })

    async def classify_intent(self, message: str) -> dict:
        """Mock intent classification."""
        self.call_history.append({
            "method": "classify_intent",
            "args": {"message": message},
        })
        return self.responses.get("intent", {
            "intent": "TASK_NEW",
            "confidence": 0.9,
        })


class MockGeminiClient:
    """Mock Gemini client for testing."""

    def __init__(self, responses: dict[str, Any] | None = None):
        self.responses = responses or {}
        self.call_history: list[dict] = []

    async def execute_step(self, step: dict, context: dict) -> dict:
        """Mock step execution."""
        self.call_history.append({
            "method": "execute_step",
            "args": {"step": step, "context": context},
        })
        return self.responses.get("execution", {
            "success": True,
            "output": "Mock execution output",
            "files_modified": [],
        })

    async def generate_code(self, prompt: str) -> str:
        """Mock code generation."""
        self.call_history.append({
            "method": "generate_code",
            "args": {"prompt": prompt},
        })
        return self.responses.get("code", "# Mock generated code\npass")


def create_mock_ai_clients() -> tuple[MockAnthropicClient, MockGeminiClient]:
    """Factory to create mock AI clients."""
    return MockAnthropicClient(), MockGeminiClient()
```

### Telegram Mock

```python
# tests/mocks/telegram_mock.py
"""Mock implementations for Telegram bot."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockTelegramBot:
    """Mock Telegram bot for testing."""

    def __init__(self):
        self.sent_messages: list[dict] = []
        self.edited_messages: list[dict] = []

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Any = None,
        parse_mode: str = "Markdown",
    ) -> dict:
        """Mock send message."""
        message = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": reply_markup,
            "parse_mode": parse_mode,
            "message_id": len(self.sent_messages) + 1,
        }
        self.sent_messages.append(message)
        return message

    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
    ) -> dict:
        """Mock edit message."""
        edit = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        self.edited_messages.append(edit)
        return edit

    def get_last_message(self) -> dict | None:
        """Get last sent message."""
        return self.sent_messages[-1] if self.sent_messages else None

    def clear_history(self) -> None:
        """Clear message history."""
        self.sent_messages.clear()
        self.edited_messages.clear()


def create_mock_update(
    user_id: int = 123456789,
    chat_id: int = 123456789,
    text: str = "Test message",
    username: str = "testuser",
) -> MagicMock:
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.text = text
    update.message.chat_id = chat_id
    update.message.from_user = MagicMock()
    update.message.from_user.id = user_id
    update.message.from_user.username = username
    update.message.reply_text = AsyncMock()
    update.callback_query = None
    return update


def create_mock_context() -> MagicMock:
    """Create a mock Telegram context."""
    context = MagicMock()
    context.bot = MockTelegramBot()
    context.user_data = {}
    context.chat_data = {}
    return context
```

### GitHub Mock

```python
# tests/mocks/github_mock.py
"""Mock implementations for GitHub operations."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock


class MockGitHubClient:
    """Mock GitHub API client for testing."""

    def __init__(self):
        self.created_branches: list[str] = []
        self.commits: list[dict] = []
        self.pull_requests: list[dict] = []

    async def create_branch(
        self,
        repo: str,
        branch_name: str,
        base: str = "main",
    ) -> dict:
        """Mock branch creation."""
        self.created_branches.append(branch_name)
        return {
            "ref": f"refs/heads/{branch_name}",
            "sha": "abc123def456",
        }

    async def create_commit(
        self,
        repo: str,
        branch: str,
        message: str,
        files: list[dict],
    ) -> dict:
        """Mock commit creation."""
        commit = {
            "sha": f"commit-{len(self.commits)}",
            "branch": branch,
            "message": message,
            "files": files,
        }
        self.commits.append(commit)
        return commit

    async def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> dict:
        """Mock PR creation."""
        pr = {
            "number": len(self.pull_requests) + 1,
            "title": title,
            "body": body,
            "head": head,
            "base": base,
            "html_url": f"https://github.com/{repo}/pull/{len(self.pull_requests) + 1}",
        }
        self.pull_requests.append(pr)
        return pr

    async def get_repository(self, repo: str) -> dict:
        """Mock get repository info."""
        return {
            "full_name": repo,
            "default_branch": "main",
            "private": False,
        }


class MockGitRepo:
    """Mock GitPython repository for testing."""

    def __init__(self, path: Path):
        self.path = path
        self.current_branch = "main"
        self.branches: list[str] = ["main"]
        self.staged_files: list[str] = []
        self.commits: list[dict] = []

    def checkout(self, branch: str, create: bool = False) -> None:
        """Mock checkout."""
        if create:
            self.branches.append(branch)
        self.current_branch = branch

    def add(self, files: list[str]) -> None:
        """Mock git add."""
        self.staged_files.extend(files)

    def commit(self, message: str) -> str:
        """Mock git commit."""
        commit = {
            "sha": f"sha-{len(self.commits)}",
            "message": message,
            "files": self.staged_files.copy(),
        }
        self.commits.append(commit)
        self.staged_files.clear()
        return commit["sha"]

    def push(self, remote: str = "origin") -> None:
        """Mock git push."""
        pass  # No-op for testing
```

### Docker Mock

```python
# tests/mocks/docker_mock.py
"""Mock implementations for Docker operations."""

from typing import Any
from unittest.mock import MagicMock


class MockDockerContainer:
    """Mock Docker container for testing."""

    def __init__(
        self,
        container_id: str = "mock-container-123",
        exit_code: int = 0,
        output: str = "Mock output",
    ):
        self.id = container_id
        self.exit_code = exit_code
        self.output = output
        self.status = "created"

    def start(self) -> None:
        """Mock container start."""
        self.status = "running"

    def wait(self, timeout: int | None = None) -> dict:
        """Mock container wait."""
        self.status = "exited"
        return {"StatusCode": self.exit_code}

    def logs(self, stdout: bool = True, stderr: bool = True) -> bytes:
        """Mock container logs."""
        return self.output.encode()

    def remove(self, force: bool = False) -> None:
        """Mock container remove."""
        self.status = "removed"


class MockDockerClient:
    """Mock Docker client for testing."""

    def __init__(self):
        self.containers = MockContainersAPI()
        self.images = MockImagesAPI()


class MockContainersAPI:
    """Mock Docker containers API."""

    def __init__(self):
        self.created: list[MockDockerContainer] = []

    def run(
        self,
        image: str,
        command: str | list[str] | None = None,
        volumes: dict | None = None,
        environment: dict | None = None,
        working_dir: str | None = None,
        detach: bool = False,
        remove: bool = False,
        **kwargs: Any,
    ) -> MockDockerContainer | str:
        """Mock container run."""
        container = MockDockerContainer()
        self.created.append(container)

        if detach:
            return container
        else:
            return container.output


class MockImagesAPI:
    """Mock Docker images API."""

    def pull(self, repository: str, tag: str = "latest") -> MagicMock:
        """Mock image pull."""
        image = MagicMock()
        image.id = f"{repository}:{tag}"
        return image


def create_mock_docker_client() -> MockDockerClient:
    """Factory to create mock Docker client."""
    return MockDockerClient()
```

## Tests Unitarios Ejemplo

```python
# tests/unit/test_intent_classifier.py
"""Unit tests for intent classification."""

import pytest

from src.agents.intent_classifier import IntentClassifier, Intent
from tests.mocks.ai_mock import MockAnthropicClient


class TestIntentClassifier:
    """Tests for IntentClassifier."""

    @pytest.fixture
    def classifier(self) -> IntentClassifier:
        """Create classifier with mock client."""
        mock_client = MockAnthropicClient({
            "intent": {"intent": "TASK_NEW", "confidence": 0.95}
        })
        return IntentClassifier(ai_client=mock_client)

    @pytest.mark.asyncio
    async def test_classify_new_task(self, classifier: IntentClassifier):
        """Test classification of new task request."""
        message = "Crea una función para validar emails en utils.py"

        result = await classifier.classify(message)

        assert result.intent == Intent.TASK_NEW
        assert result.confidence >= 0.9

    @pytest.mark.asyncio
    async def test_classify_query(self, classifier: IntentClassifier):
        """Test classification of query."""
        classifier.ai_client.responses["intent"] = {
            "intent": "QUERY",
            "confidence": 0.88,
        }
        message = "¿Cuántas tareas tengo pendientes?"

        result = await classifier.classify(message)

        assert result.intent == Intent.QUERY

    @pytest.mark.asyncio
    async def test_classify_task_list(self, classifier: IntentClassifier):
        """Test classification of task list request."""
        classifier.ai_client.responses["intent"] = {
            "intent": "TASK_LIST",
            "confidence": 0.92,
        }
        message = "Muéstrame todas las tareas"

        result = await classifier.classify(message)

        assert result.intent == Intent.TASK_LIST

    @pytest.mark.asyncio
    async def test_low_confidence_triggers_clarification(
        self,
        classifier: IntentClassifier,
    ):
        """Test that low confidence asks for clarification."""
        classifier.ai_client.responses["intent"] = {
            "intent": "TASK_NEW",
            "confidence": 0.5,  # Below threshold
        }
        message = "hazlo"

        result = await classifier.classify(message)

        assert result.needs_clarification is True
```

## Tests de Integración Ejemplo

```python
# tests/integration/test_task_flow.py
"""Integration tests for complete task flow."""

import pytest
from pathlib import Path

from src.core.orchestrator import DevTaskOrchestrator
from src.models.task import TaskStatus
from tests.mocks.ai_mock import MockAnthropicClient, MockGeminiClient
from tests.mocks.telegram_mock import MockTelegramBot, create_mock_update
from tests.mocks.github_mock import MockGitHubClient


class TestCompleteTaskFlow:
    """Integration tests for complete task execution flow."""

    @pytest.fixture
    def orchestrator(
        self,
        db_session,
        git_repo: Path,
    ) -> DevTaskOrchestrator:
        """Create orchestrator with all mocks."""
        return DevTaskOrchestrator(
            db_session=db_session,
            anthropic_client=MockAnthropicClient(),
            gemini_client=MockGeminiClient(),
            github_client=MockGitHubClient(),
            telegram_bot=MockTelegramBot(),
            workspace_path=git_repo,
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_task_lifecycle(
        self,
        orchestrator: DevTaskOrchestrator,
        telegram_update: dict,
    ):
        """Test complete task from message to commit."""
        # 1. Receive message
        update = create_mock_update(
            text="/task Agregar validación de email en user_service.py"
        )

        # 2. Process message → creates task, generates plan
        task = await orchestrator.handle_message(update)
        assert task.status == TaskStatus.PENDING_APPROVAL
        assert task.plan is not None

        # 3. User approves
        approval_update = create_mock_update(text="aprobar")
        await orchestrator.handle_approval(task.id, approved=True)

        # 4. Execute
        task = await orchestrator.execute_task(task.id)
        assert task.status == TaskStatus.COMPLETED

        # 5. Verify commit was created
        assert len(orchestrator.github_client.commits) >= 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_task_with_clarification(
        self,
        orchestrator: DevTaskOrchestrator,
    ):
        """Test task that needs clarification."""
        # Vague message
        update = create_mock_update(text="arréglalo")

        # Should ask for clarification
        response = await orchestrator.handle_message(update)

        assert response.needs_clarification is True
        assert orchestrator.telegram_bot.get_last_message() is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_task_abort_commits_partial(
        self,
        orchestrator: DevTaskOrchestrator,
        sample_task_with_plan,
    ):
        """Test that aborting task commits partial work."""
        # Start execution
        task = sample_task_with_plan
        task.current_step = 2  # Partially executed

        # Abort
        aborted_task = await orchestrator.abort_task(task.id)

        assert aborted_task.status == TaskStatus.ABORTED
        # Should have committed partial work
        assert len(orchestrator.github_client.commits) >= 1
```

## Coverage Targets

| Módulo        | Target  | Prioridad |
| ------------- | ------- | --------- |
| `src/core/`   | 90%     | Alta      |
| `src/agents/` | 85%     | Alta      |
| `src/chat/`   | 80%     | Media     |
| `src/git/`    | 85%     | Alta      |
| `src/models/` | 95%     | Alta      |
| `src/utils/`  | 90%     | Media     |
| **Global**    | **85%** | -         |

## CI Integration

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          fail_ci_if_error: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install ruff mypy

      - name: Ruff check
        run: ruff check src tests

      - name: Ruff format check
        run: ruff format --check src tests

      - name: Type check
        run: mypy src
```

## Comandos de Testing

```bash
# Ejecutar todos los tests
pytest

# Solo unit tests
pytest -m unit

# Solo integration tests
pytest -m integration

# Con coverage report
pytest --cov=src --cov-report=html

# Test específico
pytest tests/unit/test_intent_classifier.py -v

# Tests en paralelo
pytest -n auto

# Watch mode (requiere pytest-watch)
ptw tests/
```
