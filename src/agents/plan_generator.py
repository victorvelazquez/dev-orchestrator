"""Plan generation agent using Claude."""

import json
import logging
from typing import Any

import anthropic


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Eres un arquitecto de software experto que genera planes de ejecución para tareas de desarrollo.

Dado una descripción de tarea y contexto del repositorio, genera un plan detallado y ejecutable.

El plan debe incluir:
1. Objetivo claro y conciso
2. Lista de archivos a crear/modificar
3. Pasos específicos y atómicos
4. Estimación de tiempo
5. Dependencias (si aplica)

Responde SIEMPRE en formato JSON:
{
    "objetivo": "Descripción clara del objetivo",
    "archivos": ["src/file1.py", "tests/test_file1.py"],
    "pasos": [
        {
            "paso": 1,
            "descripcion": "Descripción del paso",
            "archivos": ["src/file1.py"],
            "accion": "crear|modificar|eliminar"
        }
    ],
    "estimacion": "X minutos",
    "dependencias": [],
    "notas": "Consideraciones adicionales"
}

Cada paso debe ser:
- Atómico (una sola acción)
- Verificable (se puede confirmar que se completó)
- Ordenado por dependencias

No asumas acceso a herramientas externas más allá de Git, Python y comandos básicos de shell."""


class PlanGenerator:
    """Generates execution plans for tasks using Claude."""
    
    def __init__(self, api_key: str) -> None:
        """Initialize with Anthropic API key."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    async def generate(
        self,
        description: str,
        repo_url: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate execution plan for a task.
        
        Args:
            description: Task description from user
            repo_url: Optional repository URL
            context: Optional additional context (file structure, etc.)
            
        Returns:
            Plan dictionary with steps and details
        """
        logger.info("Generating plan for: %s", description[:100])
        
        # Build user message with context
        user_message = f"**Tarea solicitada:**\n{description}"
        
        if repo_url:
            user_message += f"\n\n**Repositorio:** {repo_url}"
        
        if context:
            user_message += f"\n\n**Contexto adicional:**\n```json\n{json.dumps(context, indent=2)}\n```"
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )
            
            content = response.content[0].text
            plan = self._parse_plan(content)
            
            logger.info(
                "Plan generated: %d steps, estimated %s",
                len(plan.get("pasos", [])),
                plan.get("estimacion", "unknown"),
            )
            
            return plan
            
        except Exception as e:
            logger.exception("Plan generation failed: %s", e)
            raise
    
    def _parse_plan(self, content: str) -> dict[str, Any]:
        """Parse Claude's response into plan dictionary."""
        try:
            # Find JSON in response
            start = content.find("{")
            end = content.rfind("}") + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")
            
            plan = json.loads(content[start:end])
            
            # Validate required fields
            required = ["objetivo", "archivos", "pasos", "estimacion"]
            for field in required:
                if field not in plan:
                    raise ValueError(f"Missing required field: {field}")
            
            return plan
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse plan: %s", e)
            raise ValueError(f"Invalid plan format: {e}") from e
    
    def format_plan_for_display(self, plan: dict[str, Any]) -> str:
        """Format plan for Telegram display."""
        lines = [
            f"📋 **Plan de Ejecución**",
            "",
            f"**Objetivo:** {plan['objetivo']}",
            "",
            "**Archivos a modificar:**",
        ]
        
        for archivo in plan["archivos"]:
            lines.append(f"  • `{archivo}`")
        
        lines.append("")
        lines.append("**Pasos:**")
        
        for paso in plan["pasos"]:
            lines.append(f"  {paso['paso']}. {paso['descripcion']}")
        
        lines.append("")
        lines.append(f"⏱️ **Tiempo estimado:** {plan['estimacion']}")
        
        if plan.get("notas"):
            lines.append("")
            lines.append(f"📝 **Notas:** {plan['notas']}")
        
        return "\n".join(lines)
