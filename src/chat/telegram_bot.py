"""Telegram bot implementation."""

import logging
from typing import TYPE_CHECKING

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


if TYPE_CHECKING:
    from src.core.orchestrator import DevTaskOrchestrator


logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for Dev Task Orchestrator."""
    
    def __init__(
        self,
        token: str,
        allowed_users: list[int],
        orchestrator: "DevTaskOrchestrator",
    ) -> None:
        """Initialize bot with configuration."""
        self.token = token
        self.allowed_users = set(allowed_users)
        self.orchestrator = orchestrator
        
        # Build application
        self.app = Application.builder().token(token).build()
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register message handlers."""
        # Commands
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("help", self._handle_help))
        self.app.add_handler(CommandHandler("task", self._handle_task))
        self.app.add_handler(CommandHandler("status", self._handle_status))
        self.app.add_handler(CommandHandler("list", self._handle_list))
        self.app.add_handler(CommandHandler("abort", self._handle_abort))
        
        # Callback queries (button presses)
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Regular messages
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self._handle_message,
        ))
    
    async def _check_auth(self, update: Update) -> bool:
        """Check if user is authorized."""
        user_id = update.effective_user.id
        
        if user_id not in self.allowed_users:
            await update.message.reply_text(
                "⛔ No tienes autorización para usar este bot."
            )
            logger.warning("Unauthorized access attempt from user %d", user_id)
            return False
        
        return True
    
    async def _handle_start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /start command."""
        if not await self._check_auth(update):
            return
        
        await update.message.reply_text(
            "👋 ¡Hola! Soy el Dev Task Orchestrator.\n\n"
            "Puedo ayudarte a ejecutar tareas de desarrollo automáticamente.\n\n"
            "**Comandos disponibles:**\n"
            "/task <descripción> - Crear nueva tarea\n"
            "/status - Ver tarea activa\n"
            "/list - Ver todas las tareas\n"
            "/abort - Cancelar tarea actual\n"
            "/help - Mostrar ayuda\n\n"
            "O simplemente escríbeme qué necesitas hacer.",
            parse_mode="Markdown",
        )
    
    async def _handle_help(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /help command."""
        if not await self._check_auth(update):
            return
        
        await update.message.reply_text(
            "📚 **Ayuda del Dev Task Orchestrator**\n\n"
            "**Crear una tarea:**\n"
            "`/task Agregar validación de email https://github.com/org/repo`\n\n"
            "**Ver estado:**\n"
            "`/status` - Tarea actual\n"
            "`/list` - Todas las tareas\n\n"
            "**Controlar ejecución:**\n"
            "`/abort` - Cancelar tarea\n\n"
            "**Flujo típico:**\n"
            "1. Describes la tarea\n"
            "2. Reviso y genero un plan\n"
            "3. Apruebas el plan\n"
            "4. Ejecuto los pasos\n"
            "5. Creo PR con los cambios",
            parse_mode="Markdown",
        )
    
    async def _handle_task(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /task command."""
        if not await self._check_auth(update):
            return
        
        # Get task description from command arguments
        if not context.args:
            await update.message.reply_text(
                "❓ Por favor proporciona una descripción de la tarea.\n\n"
                "Ejemplo:\n"
                "`/task Agregar validación de email en user_service.py https://github.com/org/repo`",
                parse_mode="Markdown",
            )
            return
        
        description = " ".join(context.args)
        await self._process_task_request(update, description)
    
    async def _handle_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /status command."""
        if not await self._check_auth(update):
            return
        
        result = await self.orchestrator.handle_message(
            user_id=update.effective_user.id,
            chat_id=update.effective_chat.id,
            message="/status",
        )
        
        await update.message.reply_text(
            result.get("message", "Sin tareas activas."),
            parse_mode="Markdown",
        )
    
    async def _handle_list(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /list command."""
        if not await self._check_auth(update):
            return
        
        result = await self.orchestrator._handle_list_tasks(
            user_id=update.effective_user.id,
        )
        
        tasks = result.get("tasks", [])
        
        if not tasks:
            await update.message.reply_text("📭 No tienes tareas registradas.")
            return
        
        lines = ["📋 **Tus tareas:**\n"]
        for t in tasks:
            status_emoji = {
                "pending": "⏳",
                "pending_approval": "🔍",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌",
                "aborted": "🚫",
            }.get(t["status"], "❓")
            
            lines.append(f"{status_emoji} `{t['id']}`: {t['description']}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def _handle_abort(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /abort command."""
        if not await self._check_auth(update):
            return
        
        result = await self.orchestrator._handle_abort_task(
            user_id=update.effective_user.id,
        )
        
        await update.message.reply_text(
            result.get("message", "Operación completada."),
            parse_mode="Markdown",
        )
    
    async def _handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle regular text messages."""
        if not await self._check_auth(update):
            return
        
        await self._process_task_request(update, update.message.text)
    
    async def _process_task_request(
        self,
        update: Update,
        message: str,
    ) -> None:
        """Process a task request message."""
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        result = await self.orchestrator.handle_message(
            user_id=update.effective_user.id,
            chat_id=update.effective_chat.id,
            message=message,
        )
        
        action = result.get("action")
        
        if action == "clarify":
            await update.message.reply_text(
                f"🤔 {result['message']}",
                parse_mode="Markdown",
            )
        
        elif action == "approve_plan":
            # Show plan with approval buttons
            from src.agents.plan_generator import PlanGenerator
            
            plan_text = PlanGenerator(
                api_key=self.orchestrator.config.anthropic_api_key
            ).format_plan_for_display(result["plan"])
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Aprobar", callback_data=f"approve:{result['task_id']}"),
                    InlineKeyboardButton("❌ Rechazar", callback_data=f"reject:{result['task_id']}"),
                ],
                [
                    InlineKeyboardButton("✏️ Modificar", callback_data=f"modify:{result['task_id']}"),
                ],
            ])
            
            await update.message.reply_text(
                plan_text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        
        elif action == "completed":
            await update.message.reply_text(
                f"✅ **Tarea completada!**\n\n"
                f"ID: `{result['task_id']}`",
                parse_mode="Markdown",
            )
        
        elif action == "failed":
            await update.message.reply_text(
                f"❌ **Tarea falló**\n\n"
                f"Error: {result.get('error', 'Unknown')}",
                parse_mode="Markdown",
            )
        
        else:
            await update.message.reply_text(
                result.get("message", "Procesado."),
                parse_mode="Markdown",
            )
    
    async def _handle_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle button callback queries."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        action, task_id = data.split(":", 1)
        
        if action == "approve":
            await query.edit_message_text(
                "✅ Plan aprobado. Iniciando ejecución...",
                parse_mode="Markdown",
            )
            
            result = await self.orchestrator.approve_task(task_id)
            
            if result.get("action") == "completed":
                await query.message.reply_text(
                    "✅ **Tarea completada exitosamente!**",
                    parse_mode="Markdown",
                )
            elif "error" in result:
                await query.message.reply_text(
                    f"❌ Error: {result['error']}",
                    parse_mode="Markdown",
                )
        
        elif action == "reject":
            await query.edit_message_text(
                "❌ Plan rechazado. La tarea ha sido cancelada.",
                parse_mode="Markdown",
            )
        
        elif action == "modify":
            await query.edit_message_text(
                "✏️ Por favor, describe qué cambios quieres hacer al plan:",
                parse_mode="Markdown",
            )
    
    async def run_polling(self) -> None:
        """Start the bot with polling."""
        logger.info("Starting Telegram bot...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        # Keep running until stopped
        import asyncio
        stop_event = asyncio.Event()
        await stop_event.wait()
    
    async def stop(self) -> None:
        """Stop the bot."""
        logger.info("Stopping Telegram bot...")
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()


def create_bot(
    token: str,
    allowed_users: list[int],
    orchestrator: "DevTaskOrchestrator",
) -> TelegramBot:
    """Factory function to create bot instance."""
    return TelegramBot(
        token=token,
        allowed_users=allowed_users,
        orchestrator=orchestrator,
    )
