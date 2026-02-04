# Code Standards - Dev Task Orchestrator

> **Generado:** 2026-02-03  
> **Fase:** 5 - Code Standards

---

## 📊 Resumen

| Aspecto        | Estándar                     |
| -------------- | ---------------------------- |
| **Lenguaje**   | Python 3.11+                 |
| **Formato**    | Ruff (Black compatible)      |
| **Linting**    | Ruff + MyPy                  |
| **Docstrings** | Google Style                 |
| **Async**      | asyncio + ThreadPoolExecutor |

---

## 🛠️ Herramientas

### Configuración en pyproject.toml

```toml
[project]
name = "dev-orchestrator"
version = "0.1.0"
description = "AI-powered development task orchestrator"
requires-python = ">=3.11"

[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "W",    # pycodestyle warnings
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
    "ARG",  # flake8-unused-arguments
    "PTH",  # flake8-use-pathlib
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false

[tool.ruff.isort]
known-first-party = ["orchestrator"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[[tool.mypy.overrides]]
module = [
    "anthropic.*",
    "google.generativeai.*",
    "telegram.*",
    "git.*",
]
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=orchestrator --cov-report=term-missing"
```

### Comandos de Desarrollo

```bash
# Formatear código
ruff format .

# Verificar linting
ruff check .

# Corregir automáticamente
ruff check --fix .

# Type checking
mypy orchestrator/

# Tests
pytest

# Tests con cobertura
pytest --cov=orchestrator --cov-report=html

# Todo junto (pre-commit)
ruff format . && ruff check . && mypy orchestrator/ && pytest
```

---

## 📝 Convenciones de Nombrado

### General

| Elemento     | Convención  | Ejemplo                |
| ------------ | ----------- | ---------------------- |
| Módulos      | snake_case  | `intent_classifier.py` |
| Clases       | PascalCase  | `TaskManager`          |
| Funciones    | snake_case  | `create_task()`        |
| Variables    | snake_case  | `task_id`              |
| Constantes   | UPPER_SNAKE | `MAX_RETRIES`          |
| Privados     | \_prefijo   | `_internal_method()`   |
| Type Aliases | PascalCase  | `TaskDict`             |

### Prefijos Semánticos

| Prefijo     | Uso                           | Ejemplo                  |
| ----------- | ----------------------------- | ------------------------ |
| `get_`      | Obtener dato existente        | `get_task_by_id()`       |
| `fetch_`    | Obtener de fuente externa     | `fetch_repo_info()`      |
| `create_`   | Crear nuevo recurso           | `create_task()`          |
| `update_`   | Modificar existente           | `update_task_status()`   |
| `delete_`   | Eliminar recurso              | `delete_checkpoint()`    |
| `is_`       | Retorna booleano (estado)     | `is_valid()`             |
| `has_`      | Retorna booleano (existencia) | `has_pending_tasks()`    |
| `can_`      | Retorna booleano (permiso)    | `can_execute()`          |
| `validate_` | Validación con excepción      | `validate_branch_name()` |
| `parse_`    | Convertir formato             | `parse_plan_response()`  |
| `handle_`   | Event handler                 | `handle_message()`       |
| `on_`       | Callback/listener             | `on_task_complete()`     |
| `_`         | Método privado                | `_build_prompt()`        |

### Nombres de Archivos

```
orchestrator/
├── main.py                  # Entry point
├── config.py                # Configuración
├── exceptions.py            # Excepciones
├── intent_classifier.py     # Clasificador de intenciones
├── planner.py               # Planner (Claude)
├── executor.py              # Executor (Gemini)
├── git_agent.py             # Operaciones Git
├── state.py                 # Estado y persistencia
├── prompts.py               # Cargador de prompts
├── models/
│   ├── __init__.py
│   ├── task.py              # Modelo Task
│   ├── plan.py              # Modelo Plan
│   └── checkpoint.py        # Modelo Checkpoint
└── chat/
    ├── __init__.py
    ├── base.py              # Interfaz base
    └── telegram.py          # Implementación Telegram
```

---

## 📄 Estructura de Módulos

### Template de Módulo

```python
"""
Module Name - Brief description.

Extended description explaining the purpose and main
functionality of this module.

Example:
    >>> from orchestrator.planner import Planner
    >>> planner = Planner()
    >>> plan = await planner.generate_plan(task)
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================

# Standard library
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Third-party
from pydantic import BaseModel

# Local
from orchestrator.config import settings
from orchestrator.exceptions import PlannerError

if TYPE_CHECKING:
    from orchestrator.models.task import Task

# =============================================================================
# CONSTANTS
# =============================================================================

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-3-sonnet-20240229"
MAX_TOKENS = 4096
TIMEOUT_SECONDS = 60

# =============================================================================
# TYPES
# =============================================================================

PlanDict = dict[str, Any]

# =============================================================================
# CLASSES
# =============================================================================


class Planner:
    """
    Generates development plans using Claude AI.

    This class handles all interactions with the Anthropic API
    to generate structured development plans.

    Attributes:
        model: The Claude model to use.
        max_tokens: Maximum tokens in response.

    Example:
        >>> planner = Planner()
        >>> plan = await planner.generate_plan(task, context)
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: int = MAX_TOKENS,
    ) -> None:
        """
        Initialize the Planner.

        Args:
            model: Claude model identifier.
            max_tokens: Maximum response tokens.
        """
        self.model = model
        self.max_tokens = max_tokens
        self._client = self._create_client()
        self._system_prompt = self._load_system_prompt()

    async def generate_plan(
        self,
        task: Task,
        context: str,
    ) -> Plan:
        """
        Generate a structured plan for a task.

        Args:
            task: The task to plan.
            context: Repository context.

        Returns:
            A structured Plan with steps.

        Raises:
            PlannerError: If plan generation fails.

        Example:
            >>> plan = await planner.generate_plan(task, context)
            >>> print(plan.steps)
        """
        logger.info(f"Generating plan for task: {task.id}")

        try:
            response = await self._call_api(task, context)
            plan = self._parse_response(response)
            logger.info(f"Plan generated with {len(plan.steps)} steps")
            return plan
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            raise PlannerError(f"Plan generation failed: {e}") from e

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _create_client(self) -> Anthropic:
        """Create Anthropic client."""
        from anthropic import Anthropic
        return Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        from orchestrator.prompts import load_prompt
        return load_prompt("planner/role.md")

    async def _call_api(self, task: Task, context: str) -> str:
        """Make API call to Claude."""
        # Implementation...
        pass

    def _parse_response(self, response: str) -> Plan:
        """Parse API response into Plan."""
        # Implementation...
        pass


# =============================================================================
# FUNCTIONS
# =============================================================================


async def create_planner() -> Planner:
    """
    Factory function to create a configured Planner.

    Returns:
        Configured Planner instance.
    """
    return Planner()
```

---

## 📖 Docstrings (Google Style)

### Función

```python
def validate_branch_name(name: str, protected: list[str] | None = None) -> str:
    """
    Validate and sanitize a Git branch name.

    Removes unsafe characters and checks against protected branches.

    Args:
        name: The branch name to validate.
        protected: List of protected branch names. Defaults to
            PROTECTED_BRANCHES if not provided.

    Returns:
        The sanitized branch name.

    Raises:
        ValidationError: If the name is empty after sanitization.
        ProtectedBranchError: If the branch is protected.

    Example:
        >>> validate_branch_name("feature/my-feature")
        'feature/my-feature'
        >>> validate_branch_name("main")
        ProtectedBranchError: Cannot use protected branch: main
    """
```

### Clase

```python
class TaskManager:
    """
    Manages task lifecycle and persistence.

    Handles creation, updates, and queries for development tasks.
    Uses SQLite for persistence and JSON for Git-stored state.

    Attributes:
        db_path: Path to SQLite database.
        repos_path: Path to cloned repositories.

    Example:
        >>> manager = TaskManager()
        >>> task = await manager.create_task("Add validation", "feat")
        >>> await manager.update_status(task.id, TaskStatus.EXECUTING)
    """
```

### Módulo

```python
"""
Intent Classifier Module.

Classifies user messages into intents (QUERY, TASK_NEW, etc.)
using pattern matching and AI-assisted analysis.

The classifier uses a hybrid approach:
1. Pattern matching for common commands (/tareas, /aprobar)
2. AI classification for natural language messages

Example:
    >>> from orchestrator.intent_classifier import classify_intent
    >>> intent = await classify_intent("Agregar validación de stock")
    >>> print(intent)
    Intent(type=TASK_NEW, confidence=0.95)

Attributes:
    COMMAND_PATTERNS: Regex patterns for command detection.
    INTENT_TYPES: Valid intent type enumeration.
"""
```

---

## ⚠️ Manejo de Errores

### Jerarquía de Excepciones

```python
# orchestrator/exceptions.py

"""
Custom exceptions for the orchestrator.

Exception hierarchy:
    OrchestratorError
    ├── AIError
    │   ├── PlannerError
    │   └── ExecutorError
    ├── GitError
    │   └── ProtectedBranchError
    ├── StateError
    │   └── TaskNotFoundError
    └── SecurityError
        ├── UnauthorizedError
        └── ValidationError
"""


class OrchestratorError(Exception):
    """Base exception for all orchestrator errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# -----------------------------------------------------------------------------
# AI Errors
# -----------------------------------------------------------------------------


class AIError(OrchestratorError):
    """Error related to AI providers."""
    pass


class PlannerError(AIError):
    """Error during plan generation with Claude."""
    pass


class ExecutorError(AIError):
    """Error during code execution with Gemini."""
    pass


# -----------------------------------------------------------------------------
# Git Errors
# -----------------------------------------------------------------------------


class GitError(OrchestratorError):
    """Error during Git operations."""
    pass


class ProtectedBranchError(GitError):
    """Attempt to modify a protected branch."""

    def __init__(self, branch: str) -> None:
        super().__init__(
            f"Cannot modify protected branch: {branch}",
            details={"branch": branch}
        )
        self.branch = branch


# -----------------------------------------------------------------------------
# State Errors
# -----------------------------------------------------------------------------


class StateError(OrchestratorError):
    """Error in state management."""
    pass


class TaskNotFoundError(StateError):
    """Task not found in database."""

    def __init__(self, task_id: str) -> None:
        super().__init__(
            f"Task not found: {task_id}",
            details={"task_id": task_id}
        )
        self.task_id = task_id


# -----------------------------------------------------------------------------
# Security Errors
# -----------------------------------------------------------------------------


class SecurityError(OrchestratorError):
    """Security-related error."""
    pass


class UnauthorizedError(SecurityError):
    """User not authorized."""

    def __init__(self, user_id: int) -> None:
        super().__init__(
            f"User not authorized: {user_id}",
            details={"user_id": user_id}
        )
        self.user_id = user_id


class ValidationError(SecurityError):
    """Input validation failed."""
    pass
```

### Patrones de Manejo

```python
# Patrón 1: Específico a genérico
async def execute_task(task_id: str) -> Result:
    try:
        task = await get_task(task_id)
        result = await executor.run(task)
        return result
    except TaskNotFoundError:
        logger.warning(f"Task not found: {task_id}")
        raise
    except ExecutorError as e:
        logger.error(f"Execution error: {e}")
        await save_error_state(task_id, str(e))
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise OrchestratorError(f"Unexpected error: {e}") from e


# Patrón 2: Context manager para cleanup
async def with_checkpoint(task_id: str):
    """Context manager that saves checkpoint on error."""
    try:
        yield
    except Exception:
        await create_checkpoint(task_id)
        raise


# Patrón 3: Retry con backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    reraise=True,
)
async def call_api_with_retry(prompt: str) -> str:
    """Call API with automatic retry."""
    return await api.call(prompt)
```

---

## 🔄 Async/Await

### Operaciones Async vs Sync

| Operación         | Tipo               | Implementación    |
| ----------------- | ------------------ | ----------------- |
| Llamadas a APIs   | async              | httpx / SDK async |
| Archivos          | async              | aiofiles          |
| SQLite            | sync → thread pool | run_in_executor   |
| Git               | sync → thread pool | run_in_executor   |
| Telegram handlers | async              | requerido         |

### Utility para Sync → Async

```python
# orchestrator/utils/async_utils.py

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")

# Thread pool compartido
_executor = ThreadPoolExecutor(max_workers=4)


async def run_sync(
    func: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """
    Run a synchronous function in a thread pool.

    Args:
        func: Synchronous function to run.
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        The function result.

    Example:
        >>> result = await run_sync(blocking_function, arg1, arg2)
    """
    loop = asyncio.get_event_loop()
    func_with_kwargs = partial(func, *args, **kwargs)
    return await loop.run_in_executor(_executor, func_with_kwargs)


def shutdown_executor() -> None:
    """Shutdown the thread pool executor."""
    _executor.shutdown(wait=True)
```

### Ejemplo de Uso

```python
# orchestrator/git_agent.py

from orchestrator.utils.async_utils import run_sync
import git


class GitAgent:
    """Git operations handler."""

    async def clone_repo(self, url: str, path: Path) -> git.Repo:
        """Clone a repository asynchronously."""
        return await run_sync(git.Repo.clone_from, url, path)

    async def create_branch(self, repo: git.Repo, name: str) -> None:
        """Create and checkout a new branch."""
        await run_sync(repo.git.checkout, "-b", name)

    async def commit(self, repo: git.Repo, message: str) -> str:
        """Create a commit with the given message."""
        await run_sync(repo.git.add, "-A")
        commit = await run_sync(repo.git.commit, "-m", message)
        return commit


# orchestrator/state.py

import sqlite3
from orchestrator.utils.async_utils import run_sync


class StateManager:
    """State persistence manager."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return await run_sync(self._fetch_task, task_id)

    def _fetch_task(self, task_id: str) -> Task | None:
        """Synchronous task fetch."""
        cursor = self._get_connection().cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        )
        row = cursor.fetchone()
        return Task.from_row(row) if row else None
```

---

## 📦 Modelos Pydantic

```python
# orchestrator/models/task.py

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PLANNING = "PLANNING"
    PLANNED = "PLANNED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class TaskType(str, Enum):
    """Task type enumeration."""
    FEAT = "feat"
    FIX = "fix"
    REFACTOR = "refactor"
    DOCS = "docs"
    TEST = "test"
    CHORE = "chore"


class Intent(str, Enum):
    """User intent enumeration."""
    QUERY = "QUERY"
    TASK_NEW = "TASK_NEW"
    TASK_CONTINUE = "TASK_CONTINUE"
    TASK_LIST = "TASK_LIST"
    TASK_ABORT = "TASK_ABORT"


class Task(BaseModel):
    """Development task model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repo: str
    branch: str | None = None
    type: TaskType
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.PLANNING
    intent: Intent = Intent.TASK_NEW
    current_step: int = 0
    total_steps: int = 0
    error_message: str | None = None
    retries: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    class Config:
        use_enum_values = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for SQLite."""
        return self.model_dump(mode="json")

    @classmethod
    def from_row(cls, row: tuple) -> "Task":
        """Create from SQLite row."""
        # Implementation...
        pass
```

---

## ✅ Checklist de Código

### Antes de Commit

- [ ] `ruff format .` ejecutado
- [ ] `ruff check .` sin errores
- [ ] `mypy orchestrator/` sin errores
- [ ] Tests pasan (`pytest`)
- [ ] Docstrings en funciones públicas
- [ ] Type hints en firmas
- [ ] No hay `print()`, usar `logger`
- [ ] No hay secrets hardcodeados

### Code Review

- [ ] Nombres descriptivos
- [ ] Funciones < 50 líneas
- [ ] Una responsabilidad por función
- [ ] Manejo de errores apropiado
- [ ] Logging en puntos clave
- [ ] Tests para nueva funcionalidad

---

## 📋 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.5.0
          - types-aiofiles

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
```

### Instalación

```bash
pip install pre-commit
pre-commit install
```

---

_Documento generado por AI Flow - Phase 5: Code Standards_
