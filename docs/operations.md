# Operations & Deployment

## Arquitectura de Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                      Ubuntu VM                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Docker Compose Stack                    │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │         dev-orchestrator container          │    │    │
│  │  │  ┌─────────────┐  ┌──────────────────┐     │    │    │
│  │  │  │ Telegram Bot│  │ Task Orchestrator│     │    │    │
│  │  │  └─────────────┘  └──────────────────┘     │    │    │
│  │  │  ┌─────────────┐  ┌──────────────────┐     │    │    │
│  │  │  │  AI Agents  │  │   Git Manager    │     │    │    │
│  │  │  └─────────────┘  └──────────────────┘     │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  │                         │                            │    │
│  │  ┌──────────────────────┴───────────────────────┐   │    │
│  │  │              Volumes                          │   │    │
│  │  │  /data/orchestrator.db  /logs/  /workspace/  │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                               │
│  ┌───────────────────────────┴─────────────────────────┐    │
│  │              Host Docker Socket                      │    │
│  │  (Para ejecutar contenedores de tareas)              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Estructura de Directorios en VM

```
/opt/dev-orchestrator/
├── docker-compose.yml      # Stack principal
├── .env                    # Variables de entorno (secrets)
├── data/
│   └── orchestrator.db     # SQLite persistente
├── logs/
│   ├── orchestrator.log    # Log principal
│   └── tasks/              # Logs por tarea
│       └── task-{id}.log
├── workspace/              # Repos clonados temporalmente
│   └── {task-id}/
│       └── {repo-name}/
└── scripts/
    ├── deploy.sh
    ├── backup.sh
    ├── restore.sh
    └── health-check.sh
```

## Docker Configuration

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim AS base

# Metadata
LABEL maintainer="Dev Task Orchestrator"
LABEL version="1.0.0"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (for running task containers)
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-24.0.7.tgz \
    | tar xz --strip-components=1 -C /usr/local/bin docker/docker

# Create non-root user
RUN useradd --create-home --shell /bin/bash orchestrator
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=orchestrator:orchestrator src/ src/
COPY --chown=orchestrator:orchestrator pyproject.toml .

# Create directories
RUN mkdir -p /app/data /app/logs /app/workspace \
    && chown -R orchestrator:orchestrator /app

USER orchestrator

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health')" || exit 1

# Default command
CMD ["python", "-m", "src.main"]
```

### Docker Compose - Production

```yaml
# docker-compose.yml
version: "3.8"

services:
  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: dev-orchestrator
    restart: unless-stopped

    environment:
      # Telegram
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_ALLOWED_USERS=${TELEGRAM_ALLOWED_USERS}

      # AI Providers
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_AI_API_KEY=${GOOGLE_AI_API_KEY}

      # GitHub
      - GITHUB_TOKEN=${GITHUB_TOKEN}

      # App config
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DATABASE_URL=sqlite:///data/orchestrator.db
      - WORKSPACE_PATH=/app/workspace

    volumes:
      # Persistent data
      - ./data:/app/data
      - ./logs:/app/logs
      - ./workspace:/app/workspace

      # Docker socket for running task containers
      - /var/run/docker.sock:/var/run/docker.sock

      # SSH keys for private repos (optional)
      - ~/.ssh:/home/orchestrator/.ssh:ro

    ports:
      - "8080:8080" # Health check / metrics endpoint

    networks:
      - orchestrator-net

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  orchestrator-net:
    driver: bridge
```

### Docker Compose - Development

```yaml
# docker-compose.dev.yml
version: "3.8"

services:
  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile
      target: base
    container_name: dev-orchestrator-dev

    environment:
      - LOG_LEVEL=DEBUG
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_ALLOWED_USERS=${TELEGRAM_ALLOWED_USERS}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_AI_API_KEY=${GOOGLE_AI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - DATABASE_URL=sqlite:///data/orchestrator.db

    volumes:
      # Mount source for hot reload
      - ./src:/app/src:ro
      - ./data:/app/data
      - ./logs:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock

    ports:
      - "8080:8080"

    command: ["python", "-m", "src.main", "--debug"]
```

### .dockerignore

```
# .dockerignore
.git
.gitignore
.env
.env.*
*.md
!README.md

# Python
__pycache__
*.pyc
*.pyo
.pytest_cache
.mypy_cache
.ruff_cache
.coverage
htmlcov/
coverage_html/

# IDE
.vscode
.idea
*.swp

# Tests
tests/
pytest.ini

# Docs
docs/
specs/

# Build
dist/
build/
*.egg-info/

# Local data
data/
logs/
workspace/
```

## Environment Variables

### .env.example

```bash
# .env.example - Copy to .env and fill values

# =============================================================================
# TELEGRAM
# =============================================================================
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
# Comma-separated Telegram user IDs allowed to use the bot
TELEGRAM_ALLOWED_USERS=123456789,987654321

# =============================================================================
# AI PROVIDERS
# =============================================================================
# Anthropic (Claude) - Used for planning
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Google AI Studio (Gemini) - Used for execution
GOOGLE_AI_API_KEY=AIzaSyxxxxx

# =============================================================================
# GITHUB
# =============================================================================
# Personal Access Token with repo scope
GITHUB_TOKEN=ghp_xxxxx

# =============================================================================
# APPLICATION
# =============================================================================
LOG_LEVEL=INFO
# DEBUG, INFO, WARNING, ERROR, CRITICAL

# Database path (relative to container)
DATABASE_URL=sqlite:///data/orchestrator.db

# Workspace for cloned repos
WORKSPACE_PATH=/app/workspace

# =============================================================================
# OPTIONAL
# =============================================================================
# Checkpoint interval in seconds (default: 300 = 5 min)
CHECKPOINT_INTERVAL=300

# Max clarification rounds (default: 10)
MAX_CLARIFICATION_ROUNDS=10

# Task timeout in seconds (default: 1800 = 30 min)
TASK_TIMEOUT=1800
```

## Deployment Scripts

### deploy.sh

```bash
#!/bin/bash
# scripts/deploy.sh - Deploy or update the orchestrator

set -euo pipefail

DEPLOY_DIR="/opt/dev-orchestrator"
REPO_URL="https://github.com/your-org/dev-orchestrator.git"
BRANCH="${1:-main}"

echo "🚀 Deploying Dev Task Orchestrator..."
echo "   Branch: $BRANCH"

# Create directory if not exists
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "📁 Creating deployment directory..."
    sudo mkdir -p "$DEPLOY_DIR"
    sudo chown "$USER:$USER" "$DEPLOY_DIR"
fi

cd "$DEPLOY_DIR"

# Clone or pull
if [ ! -d ".git" ]; then
    echo "📥 Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" .
else
    echo "📥 Pulling latest changes..."
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
fi

# Check .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "   Copy .env.example to .env and configure it."
    exit 1
fi

# Create required directories
mkdir -p data logs workspace

# Build and start
echo "🔨 Building Docker image..."
docker compose build

echo "🔄 Restarting services..."
docker compose down
docker compose up -d

echo "⏳ Waiting for service to be ready..."
sleep 5

# Health check
if docker compose exec orchestrator python -c "print('OK')" 2>/dev/null; then
    echo "✅ Deployment successful!"
    docker compose logs --tail=20
else
    echo "❌ Deployment failed!"
    docker compose logs --tail=50
    exit 1
fi
```

### backup.sh

```bash
#!/bin/bash
# scripts/backup.sh - Backup database and logs

set -euo pipefail

DEPLOY_DIR="/opt/dev-orchestrator"
BACKUP_DIR="/opt/backups/dev-orchestrator"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

echo "📦 Creating backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Stop container briefly for consistent backup
cd "$DEPLOY_DIR"
docker compose stop orchestrator

# Backup database
if [ -f "data/orchestrator.db" ]; then
    cp "data/orchestrator.db" "$BACKUP_DIR/orchestrator_$DATE.db"
    echo "   ✅ Database backed up"
fi

# Backup logs (compress)
if [ -d "logs" ]; then
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/
    echo "   ✅ Logs backed up"
fi

# Restart container
docker compose start orchestrator

# Cleanup old backups
echo "🧹 Cleaning old backups (> $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

echo "✅ Backup complete: $BACKUP_DIR"
ls -lh "$BACKUP_DIR"
```

### restore.sh

```bash
#!/bin/bash
# scripts/restore.sh - Restore from backup

set -euo pipefail

DEPLOY_DIR="/opt/dev-orchestrator"
BACKUP_DIR="/opt/backups/dev-orchestrator"

# List available backups
echo "Available backups:"
ls -lh "$BACKUP_DIR"/*.db 2>/dev/null || echo "No database backups found"

echo ""
read -p "Enter backup date (e.g., 20260203_120000): " BACKUP_DATE

DB_FILE="$BACKUP_DIR/orchestrator_$BACKUP_DATE.db"

if [ ! -f "$DB_FILE" ]; then
    echo "❌ Backup not found: $DB_FILE"
    exit 1
fi

echo "⚠️  This will replace the current database!"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

cd "$DEPLOY_DIR"

# Stop container
docker compose stop orchestrator

# Backup current before restore
if [ -f "data/orchestrator.db" ]; then
    mv "data/orchestrator.db" "data/orchestrator.db.before_restore"
fi

# Restore
cp "$DB_FILE" "data/orchestrator.db"

# Start container
docker compose start orchestrator

echo "✅ Restore complete from: $BACKUP_DATE"
```

### health-check.sh

```bash
#!/bin/bash
# scripts/health-check.sh - Check service health

set -euo pipefail

DEPLOY_DIR="/opt/dev-orchestrator"

cd "$DEPLOY_DIR"

echo "🔍 Dev Task Orchestrator Health Check"
echo "======================================"

# Container status
echo ""
echo "📦 Container Status:"
docker compose ps

# Resource usage
echo ""
echo "📊 Resource Usage:"
docker stats --no-stream dev-orchestrator 2>/dev/null || echo "Container not running"

# Recent logs
echo ""
echo "📋 Recent Logs (last 10 lines):"
docker compose logs --tail=10 orchestrator

# Database size
echo ""
echo "💾 Database Size:"
if [ -f "data/orchestrator.db" ]; then
    ls -lh data/orchestrator.db
else
    echo "Database not found"
fi

# Disk space
echo ""
echo "💿 Disk Space:"
df -h "$DEPLOY_DIR"

# Check if bot is responsive
echo ""
echo "🤖 Bot Status:"
if docker compose exec -T orchestrator python -c "
from src.core.health import check_health
import asyncio
result = asyncio.run(check_health())
print('OK' if result['healthy'] else 'UNHEALTHY')
for k, v in result.items():
    print(f'  {k}: {v}')
" 2>/dev/null; then
    echo "✅ Bot is healthy"
else
    echo "⚠️  Could not check bot health"
fi
```

## Logging Configuration

```python
# src/core/logging_config.py
"""Logging configuration for the orchestrator."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

def setup_logging(
    log_level: str = "INFO",
    log_dir: Path = Path("/app/logs"),
) -> None:
    """Configure application logging."""

    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler - main log (rotating by size)
    file_handler = RotatingFileHandler(
        log_dir / "orchestrator.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Error file handler
    error_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


def get_task_logger(task_id: str, log_dir: Path = Path("/app/logs/tasks")) -> logging.Logger:
    """Get a logger for a specific task."""
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(f"task.{task_id}")

    # Task-specific file handler
    handler = logging.FileHandler(log_dir / f"task-{task_id}.log")
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)

    return logger
```

## Monitoring & Alerts

### Health Endpoint

```python
# src/core/health.py
"""Health check endpoint."""

from dataclasses import dataclass
from datetime import datetime
import asyncio

import httpx
from sqlalchemy import text


@dataclass
class HealthStatus:
    healthy: bool
    database: bool
    telegram: bool
    anthropic: bool
    google: bool
    last_task: datetime | None
    uptime_seconds: float


async def check_health() -> dict:
    """Perform health checks on all components."""
    from src.core.config import get_config
    from src.models.database import get_session

    config = get_config()
    results = {
        "healthy": True,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    # Database check
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        results["checks"]["database"] = "ok"
    except Exception as e:
        results["checks"]["database"] = f"error: {e}"
        results["healthy"] = False

    # Telegram API check
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.telegram.org/bot{config.telegram_token}/getMe",
                timeout=5.0,
            )
            if resp.status_code == 200:
                results["checks"]["telegram"] = "ok"
            else:
                results["checks"]["telegram"] = f"error: {resp.status_code}"
                results["healthy"] = False
    except Exception as e:
        results["checks"]["telegram"] = f"error: {e}"
        results["healthy"] = False

    # Anthropic API check (simple)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": config.anthropic_api_key},
                timeout=5.0,
            )
            results["checks"]["anthropic"] = "ok" if resp.status_code in (200, 401) else f"error: {resp.status_code}"
    except Exception as e:
        results["checks"]["anthropic"] = f"error: {e}"

    return results
```

### Systemd Service (Alternative to Docker)

```ini
# /etc/systemd/system/dev-orchestrator.service
[Unit]
Description=Dev Task Orchestrator
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=orchestrator
WorkingDirectory=/opt/dev-orchestrator
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dev-orchestrator

[Install]
WantedBy=multi-user.target
```

## CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to VM
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.VM_HOST }}
          username: ${{ secrets.VM_USER }}
          key: ${{ secrets.VM_SSH_KEY }}
          script: |
            cd /opt/dev-orchestrator
            docker compose pull
            docker compose up -d
            docker compose logs --tail=20
```

## Comandos Operativos

```bash
# Iniciar
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f orchestrator

# Reiniciar
docker compose restart orchestrator

# Detener
docker compose down

# Ver estado
docker compose ps

# Ejecutar comando dentro del contenedor
docker compose exec orchestrator python -m src.cli status

# Backup manual
./scripts/backup.sh

# Health check
./scripts/health-check.sh

# Ver uso de recursos
docker stats dev-orchestrator
```
