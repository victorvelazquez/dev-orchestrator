"""Logging configuration for the orchestrator."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_level: str = "INFO",
    log_dir: Path | None = None,
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files. If None, only console logging.
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handlers (if log_dir provided)
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main log file (rotating by size)
        file_handler = RotatingFileHandler(
            log_dir / "orchestrator.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file
        error_handler = RotatingFileHandler(
            log_dir / "errors.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
    
    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_task_logger(
    task_id: str,
    log_dir: Path | None = None,
) -> logging.Logger:
    """
    Get a logger for a specific task.
    
    Args:
        task_id: Unique task identifier
        log_dir: Directory for task logs
        
    Returns:
        Logger configured for the task
    """
    logger = logging.getLogger(f"task.{task_id}")
    
    if log_dir is not None:
        tasks_log_dir = log_dir / "tasks"
        tasks_log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(
            tasks_log_dir / f"task-{task_id}.log",
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
    
    return logger
