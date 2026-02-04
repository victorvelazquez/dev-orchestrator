"""Main orchestrator - coordinates all components."""

import logging
from typing import TYPE_CHECKING

from src.core.config import Config
from src.models.task import Task, TaskStatus, Intent


if TYPE_CHECKING:
    from src.agents.intent_classifier import IntentClassifier
    from src.agents.plan_generator import PlanGenerator
    from src.agents.executor import TaskExecutor


logger = logging.getLogger(__name__)


class DevTaskOrchestrator:
    """Main orchestrator that coordinates all system components."""
    
    def __init__(self, config: Config) -> None:
        """Initialize the orchestrator."""
        self.config = config
        self._intent_classifier: "IntentClassifier | None" = None
        self._plan_generator: "PlanGenerator | None" = None
        self._executor: "TaskExecutor | None" = None
        
        logger.info("DevTaskOrchestrator initialized")
    
    @property
    def intent_classifier(self) -> "IntentClassifier":
        """Lazy-load intent classifier."""
        if self._intent_classifier is None:
            from src.agents.intent_classifier import IntentClassifier
            self._intent_classifier = IntentClassifier(
                api_key=self.config.anthropic_api_key,
            )
        return self._intent_classifier
    
    @property
    def plan_generator(self) -> "PlanGenerator":
        """Lazy-load plan generator."""
        if self._plan_generator is None:
            from src.agents.plan_generator import PlanGenerator
            self._plan_generator = PlanGenerator(
                api_key=self.config.anthropic_api_key,
            )
        return self._plan_generator
    
    @property
    def executor(self) -> "TaskExecutor":
        """Lazy-load task executor."""
        if self._executor is None:
            from src.agents.executor import TaskExecutor
            self._executor = TaskExecutor(
                api_key=self.config.google_ai_api_key,
                workspace_path=self.config.workspace_dir,
            )
        return self._executor
    
    async def handle_message(
        self,
        user_id: int,
        chat_id: int,
        message: str,
    ) -> dict:
        """
        Handle incoming message from Telegram.
        
        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            message: User's message text
            
        Returns:
            Response dict with action and data
        """
        logger.info("Handling message from user %d: %s", user_id, message[:50])
        
        # Classify intent
        intent_result = await self.intent_classifier.classify(message)
        
        match intent_result.intent:
            case Intent.QUERY:
                return await self._handle_query(message, intent_result)
            
            case Intent.TASK_NEW:
                return await self._handle_new_task(user_id, chat_id, message, intent_result)
            
            case Intent.TASK_CONTINUE:
                return await self._handle_continue_task(user_id, message)
            
            case Intent.TASK_LIST:
                return await self._handle_list_tasks(user_id)
            
            case Intent.TASK_ABORT:
                return await self._handle_abort_task(user_id)
            
            case _:
                return {
                    "action": "clarify",
                    "message": "No entendí tu solicitud. ¿Puedes ser más específico?",
                }
    
    async def _handle_query(self, message: str, intent_result: dict) -> dict:
        """Handle a query (question) from user."""
        # TODO: Implement query handling
        return {
            "action": "respond",
            "message": "Esta funcionalidad está en desarrollo.",
        }
    
    async def _handle_new_task(
        self,
        user_id: int,
        chat_id: int,
        message: str,
        intent_result: dict,
    ) -> dict:
        """Handle new task creation."""
        # Check if info is complete
        if intent_result.needs_clarification:
            return {
                "action": "clarify",
                "message": intent_result.clarification_question,
            }
        
        # Generate plan
        plan = await self.plan_generator.generate(
            description=message,
            repo_url=intent_result.extracted_info.get("repo"),
        )
        
        # Create task
        task = Task(
            telegram_user_id=user_id,
            telegram_chat_id=chat_id,
            description=message,
            repo_url=intent_result.extracted_info.get("repo", ""),
            plan=plan,
            status=TaskStatus.PENDING_APPROVAL,
        )
        
        # Save task
        from src.models.database import save_task
        save_task(task)
        
        return {
            "action": "approve_plan",
            "task_id": task.id,
            "plan": plan,
        }
    
    async def _handle_continue_task(self, user_id: int, message: str) -> dict:
        """Handle continuation of existing task."""
        # TODO: Implement task continuation
        return {
            "action": "respond",
            "message": "Continuando con la tarea...",
        }
    
    async def _handle_list_tasks(self, user_id: int) -> dict:
        """Handle request to list tasks."""
        from src.models.database import get_user_tasks
        
        tasks = get_user_tasks(user_id)
        
        return {
            "action": "list",
            "tasks": [t.to_summary() for t in tasks],
        }
    
    async def _handle_abort_task(self, user_id: int) -> dict:
        """Handle task abort request."""
        from src.models.database import get_active_task, update_task
        
        task = get_active_task(user_id)
        
        if task is None:
            return {
                "action": "respond",
                "message": "No tienes tareas activas para cancelar.",
            }
        
        # Commit partial work if any
        if task.current_step > 0:
            await self.executor.commit_partial_work(task)
        
        # Update status
        task.status = TaskStatus.ABORTED
        update_task(task)
        
        return {
            "action": "respond",
            "message": f"Tarea {task.id} cancelada.",
        }
    
    async def approve_task(self, task_id: str) -> dict:
        """Approve a task for execution."""
        from src.models.database import get_task, update_task
        
        task = get_task(task_id)
        
        if task is None:
            return {"error": "Task not found"}
        
        if task.status != TaskStatus.PENDING_APPROVAL:
            return {"error": "Task is not pending approval"}
        
        task.status = TaskStatus.APPROVED
        update_task(task)
        
        # Start execution
        return await self.execute_task(task_id)
    
    async def execute_task(self, task_id: str) -> dict:
        """Execute an approved task."""
        from src.models.database import get_task, update_task
        
        task = get_task(task_id)
        
        if task is None:
            return {"error": "Task not found"}
        
        task.status = TaskStatus.IN_PROGRESS
        update_task(task)
        
        try:
            result = await self.executor.execute(task)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            update_task(task)
            
            return {
                "action": "completed",
                "task_id": task_id,
                "result": result,
            }
            
        except Exception as e:
            logger.exception("Task execution failed: %s", e)
            
            task.status = TaskStatus.FAILED
            task.error = str(e)
            update_task(task)
            
            # Try to commit partial work
            await self.executor.commit_partial_work(task)
            
            return {
                "action": "failed",
                "task_id": task_id,
                "error": str(e),
            }
