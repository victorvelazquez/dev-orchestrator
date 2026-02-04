"""Intent classification agent using Claude."""

import json
import logging
from typing import Any

import anthropic

from src.models.task import Intent, IntentResult


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Eres un clasificador de intenciones para un sistema de orquestación de tareas de desarrollo.

Analiza el mensaje del usuario y clasifica su intención en una de las siguientes categorías:

- QUERY: El usuario hace una pregunta o consulta (no quiere ejecutar una tarea)
- TASK_NEW: El usuario quiere crear una nueva tarea de desarrollo
- TASK_CONTINUE: El usuario quiere continuar o proporciona información adicional sobre una tarea existente
- TASK_LIST: El usuario quiere ver sus tareas
- TASK_ABORT: El usuario quiere cancelar una tarea

Responde SIEMPRE en formato JSON con esta estructura:
{
    "intent": "TASK_NEW",
    "confidence": 0.95,
    "needs_clarification": false,
    "clarification_question": null,
    "extracted_info": {
        "repo": "https://github.com/...",
        "description": "...",
        "task_type": "feature"
    }
}

Si el mensaje es ambiguo o falta información crítica (como el repositorio para TASK_NEW), 
marca needs_clarification=true y proporciona una pregunta específica."""


class IntentClassifier:
    """Classifies user message intent using Claude."""
    
    def __init__(self, api_key: str) -> None:
        """Initialize with Anthropic API key."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    async def classify(self, message: str) -> IntentResult:
        """
        Classify user message intent.
        
        Args:
            message: User's message text
            
        Returns:
            IntentResult with classification details
        """
        logger.debug("Classifying intent for: %s", message[:100])
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": message}
                ],
            )
            
            # Parse response
            content = response.content[0].text
            result = self._parse_response(content)
            
            logger.info(
                "Intent classified: %s (confidence: %.2f)",
                result.intent.value,
                result.confidence,
            )
            
            return result
            
        except Exception as e:
            logger.exception("Intent classification failed: %s", e)
            # Default to clarification on error
            return IntentResult(
                intent=Intent.QUERY,
                confidence=0.0,
                needs_clarification=True,
                clarification_question="Hubo un error procesando tu mensaje. ¿Puedes reformularlo?",
            )
    
    def _parse_response(self, content: str) -> IntentResult:
        """Parse Claude's response into IntentResult."""
        try:
            # Find JSON in response
            start = content.find("{")
            end = content.rfind("}") + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")
            
            data = json.loads(content[start:end])
            
            return IntentResult(
                intent=Intent(data["intent"].lower()),
                confidence=float(data.get("confidence", 0.8)),
                needs_clarification=bool(data.get("needs_clarification", False)),
                clarification_question=data.get("clarification_question"),
                extracted_info=data.get("extracted_info", {}),
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Failed to parse intent response: %s", e)
            return IntentResult(
                intent=Intent.QUERY,
                confidence=0.5,
                needs_clarification=True,
                clarification_question="No pude entender tu solicitud. ¿Puedes ser más específico?",
            )
