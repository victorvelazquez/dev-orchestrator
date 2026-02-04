"""Task execution agent using Gemini."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import google.generativeai as genai

from src.models.task import Task


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Eres un desarrollador experto que ejecuta tareas de programación.

Dado un paso específico de un plan, genera el código o cambios necesarios.

Reglas:
1. Genera código limpio, idiomático y bien documentado
2. Sigue las convenciones del proyecto existente
3. Incluye manejo de errores apropiado
4. Agrega docstrings y comentarios donde sea necesario
5. Si modificas un archivo, muestra el contenido completo resultante

Responde en formato JSON:
{
    "success": true,
    "action": "create|modify|delete",
    "file_path": "src/example.py",
    "content": "# Contenido completo del archivo...",
    "explanation": "Explicación breve de los cambios"
}

Si hay un error o no puedes completar el paso:
{
    "success": false,
    "error": "Descripción del problema",
    "suggestion": "Sugerencia para resolver"
}"""


class TaskExecutor:
    """Executes task steps using Gemini."""
    
    def __init__(
        self,
        api_key: str,
        workspace_path: Path,
    ) -> None:
        """Initialize with Google AI API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.workspace_path = workspace_path
    
    async def execute(self, task: Task) -> dict[str, Any]:
        """
        Execute all steps of a task.
        
        Args:
            task: Task with plan to execute
            
        Returns:
            Execution result with details
        """
        if task.plan is None:
            raise ValueError("Task has no plan")
        
        logger.info("Executing task %s with %d steps", task.id, len(task.plan["pasos"]))
        
        results = []
        task.started_at = datetime.utcnow()
        task.total_steps = len(task.plan["pasos"])
        
        for paso in task.plan["pasos"]:
            task.current_step = paso["paso"]
            
            logger.info("Executing step %d: %s", paso["paso"], paso["descripcion"])
            
            try:
                result = await self._execute_step(task, paso)
                results.append(result)
                
                if not result.get("success", False):
                    logger.error("Step %d failed: %s", paso["paso"], result.get("error"))
                    break
                    
            except Exception as e:
                logger.exception("Step %d execution error: %s", paso["paso"], e)
                results.append({
                    "success": False,
                    "step": paso["paso"],
                    "error": str(e),
                })
                break
        
        task.completed_at = datetime.utcnow()
        
        # Determine overall success
        all_success = all(r.get("success", False) for r in results)
        
        return {
            "success": all_success,
            "steps_completed": task.current_step,
            "total_steps": task.total_steps,
            "results": results,
        }
    
    async def _execute_step(
        self,
        task: Task,
        paso: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single step."""
        # Build context for the model
        context = {
            "task_description": task.description,
            "repo_url": task.repo_url,
            "current_step": paso,
            "previous_steps": task.plan["pasos"][:paso["paso"] - 1],
        }
        
        prompt = f"""Ejecuta el siguiente paso de desarrollo:

**Paso {paso['paso']}:** {paso['descripcion']}

**Contexto de la tarea:**
{json.dumps(context, indent=2, ensure_ascii=False)}

Genera el código o cambios necesarios."""

        response = self.model.generate_content(prompt)
        content = response.text
        
        # Parse and apply result
        result = self._parse_step_result(content)
        
        if result.get("success") and result.get("content"):
            await self._apply_changes(task, result)
        
        result["step"] = paso["paso"]
        return result
    
    def _parse_step_result(self, content: str) -> dict[str, Any]:
        """Parse Gemini's response."""
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            
            if start == -1 or end == 0:
                return {
                    "success": False,
                    "error": "No JSON found in response",
                }
            
            return json.loads(content[start:end])
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON: {e}",
            }
    
    async def _apply_changes(
        self,
        task: Task,
        result: dict[str, Any],
    ) -> None:
        """Apply file changes from step result."""
        file_path = result.get("file_path")
        content = result.get("content")
        action = result.get("action", "modify")
        
        if not file_path or not content:
            return
        
        # Get task workspace
        task_workspace = self.workspace_path / task.id
        full_path = task_workspace / file_path
        
        if action == "delete":
            if full_path.exists():
                full_path.unlink()
                logger.info("Deleted: %s", file_path)
        else:
            # Create or modify
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            logger.info("Written: %s", file_path)
    
    async def commit_partial_work(self, task: Task) -> dict[str, Any] | None:
        """Commit any partial work done on a task."""
        task_workspace = self.workspace_path / task.id
        
        if not task_workspace.exists():
            return None
        
        # TODO: Implement Git commit logic
        logger.info("Committing partial work for task %s", task.id)
        
        return {
            "committed": True,
            "message": f"WIP: Partial work from task {task.id}",
        }
    
    async def create_checkpoint(self, task: Task) -> dict[str, Any]:
        """Create a checkpoint of current task state."""
        checkpoint = {
            "task_id": task.id,
            "timestamp": datetime.utcnow().isoformat(),
            "current_step": task.current_step,
            "status": task.status.value,
        }
        
        # Save checkpoint to .dev-tasks directory
        task_workspace = self.workspace_path / task.id
        checkpoint_dir = task_workspace / ".dev-tasks"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_file = checkpoint_dir / "checkpoint.json"
        checkpoint_file.write_text(
            json.dumps(checkpoint, indent=2),
            encoding="utf-8",
        )
        
        task.last_checkpoint_at = datetime.utcnow()
        task.checkpoint_data = checkpoint
        
        logger.info("Checkpoint created for task %s at step %d", task.id, task.current_step)
        
        return checkpoint
