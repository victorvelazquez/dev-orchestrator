"""Dev Task Orchestrator - Main entry point."""

import asyncio
import logging
import sys
from pathlib import Path

from src.core.config import get_config
from src.core.logging_config import setup_logging


logger = logging.getLogger(__name__)


async def main() -> None:
    """Main application entry point."""
    # Load configuration
    config = get_config()
    
    # Setup logging
    setup_logging(
        log_level=config.log_level,
        log_dir=Path(config.log_dir),
    )
    
    logger.info("Starting Dev Task Orchestrator v%s", config.version)
    
    # Import here to avoid circular imports
    from src.chat.telegram_bot import create_bot
    from src.core.orchestrator import DevTaskOrchestrator
    from src.models.database import init_database
    
    # Initialize database
    init_database(config.database_url)
    logger.info("Database initialized")
    
    # Create orchestrator
    orchestrator = DevTaskOrchestrator(config=config)
    
    # Create and run Telegram bot
    bot = create_bot(
        token=config.telegram_token,
        allowed_users=config.telegram_allowed_users,
        orchestrator=orchestrator,
    )
    
    logger.info("Bot started. Listening for messages...")
    
    # Run the bot
    await bot.run_polling()


def cli_main() -> None:
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dev Task Orchestrator")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_config().version}",
    )
    
    args = parser.parse_args()
    
    if args.debug:
        import os
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
