# Security Specification - Dev Task Orchestrator

> **Generado:** 2026-02-03  
> **Fase:** 4 - Security & Authentication

---

## 📊 Resumen de Seguridad

| Aspecto           | Implementación                 |
| ----------------- | ------------------------------ |
| **Autenticación** | Whitelist de Telegram User IDs |
| **Autorización**  | Usuario único (propietario)    |
| **Secrets**       | Variables de entorno (.env)    |
| **Ejecución**     | Container aislado con sandbox  |
| **Git**           | Protección de ramas sensibles  |

---

## 🔐 Autenticación

### Telegram Bot

El bot solo responde a usuarios autorizados mediante whitelist:

```python
# config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # ... otras configuraciones ...

    # Lista de Telegram User IDs autorizados
    ALLOWED_TELEGRAM_USERS: List[int] = []

    class Config:
        env_file = ".env"

settings = Settings()
```

```python
# chat/telegram.py
from orchestrator.config import settings

async def check_authorized(update: Update) -> bool:
    """Verifica si el usuario está autorizado."""
    user_id = update.effective_user.id

    if user_id not in settings.ALLOWED_TELEGRAM_USERS:
        await update.message.reply_text(
            "❌ No estás autorizado para usar este bot.\n"
            f"Tu User ID: {user_id}"
        )
        return False

    return True

# Decorador para handlers
def authorized_only(func):
    """Decorador que verifica autorización antes de ejecutar."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await check_authorized(update):
            return
        return await func(update, context)
    return wrapper

# Uso en handlers
@authorized_only
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Solo usuarios autorizados llegan aquí
    pass
```

### Obtener tu Telegram User ID

```python
# Script para obtener tu User ID
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Tu User ID es: {user_id}")
```

### Configuración en .env

```bash
# Lista de User IDs autorizados (separados por coma)
ALLOWED_TELEGRAM_USERS=123456789,987654321
```

---

## 🔑 Gestión de Secrets

### Variables de Entorno

| Variable                 | Descripción                   | Ejemplo         |
| ------------------------ | ----------------------------- | --------------- |
| `ANTHROPIC_API_KEY`      | API key de Anthropic (Claude) | `sk-ant-xxxxx`  |
| `GOOGLE_API_KEY`         | API key de Google (Gemini)    | `AIzaSy...`     |
| `GITHUB_TOKEN`           | Token personal de GitHub      | `ghp_xxxxx`     |
| `TELEGRAM_BOT_TOKEN`     | Token del bot de Telegram     | `123456:ABC...` |
| `ALLOWED_TELEGRAM_USERS` | IDs autorizados               | `123456789`     |

### Archivo .env

```bash
# =============================================================================
# SECRETS - NUNCA COMMITEAR ESTE ARCHIVO
# =============================================================================

# AI Providers
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
GOOGLE_API_KEY=AIzaSyxxxxx

# GitHub
GITHUB_TOKEN=ghp_xxxxx

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ALLOWED_TELEGRAM_USERS=123456789

# =============================================================================
```

### Protección de .env

```bash
# Permisos restrictivos (Linux/Mac)
chmod 600 .env

# Verificar que está en .gitignore
echo ".env" >> .gitignore
```

### .gitignore

```gitignore
# Secrets
.env
.env.local
.env.*.local
*.pem
*.key

# No ignorar el ejemplo
!.env.example
```

### Validación de Secrets al Iniciar

```python
# config.py
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str
    GOOGLE_API_KEY: str
    GITHUB_TOKEN: str
    TELEGRAM_BOT_TOKEN: str
    ALLOWED_TELEGRAM_USERS: list[int] = []

    @field_validator('ANTHROPIC_API_KEY')
    @classmethod
    def validate_anthropic_key(cls, v):
        if not v or not v.startswith('sk-ant-'):
            raise ValueError('ANTHROPIC_API_KEY inválida')
        return v

    @field_validator('GITHUB_TOKEN')
    @classmethod
    def validate_github_token(cls, v):
        if not v or not v.startswith('ghp_'):
            raise ValueError('GITHUB_TOKEN inválido')
        return v

    @field_validator('ALLOWED_TELEGRAM_USERS')
    @classmethod
    def validate_users(cls, v):
        if not v:
            raise ValueError('Debe haber al menos un usuario autorizado')
        return v
```

---

## 🛡️ Sandbox de Ejecución

### Comandos Permitidos

Solo se permiten comandos específicos para evitar ejecución de código malicioso:

```python
# security/sandbox.py

ALLOWED_COMMANDS = {
    # Git
    "git",

    # Python
    "python",
    "python3",
    "pip",
    "pip3",
    "pytest",

    # Node.js
    "node",
    "npm",
    "npx",

    # Utilidades seguras
    "cat",
    "ls",
    "mkdir",
    "touch",
    "echo",
    "cp",
    "mv",
    "rm",  # Solo dentro del repo
    "head",
    "tail",
    "grep",
    "find",
    "wc",
}

BLOCKED_COMMANDS = {
    # Peligrosos
    "sudo",
    "su",
    "chmod",
    "chown",
    "curl",
    "wget",
    "ssh",
    "scp",
    "rsync",
    "nc",
    "netcat",
    "eval",
    "exec",
    "source",
    ".",

    # Destructivos
    "rm -rf /",
    "mkfs",
    "dd",
    "shutdown",
    "reboot",
    "kill",
    "killall",
}

def validate_command(command: str) -> bool:
    """Valida que un comando sea seguro para ejecutar."""
    # Obtener el comando base
    parts = command.strip().split()
    if not parts:
        return False

    base_command = parts[0]

    # Verificar si está bloqueado
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            return False

    # Verificar si está permitido
    if base_command not in ALLOWED_COMMANDS:
        return False

    return True
```

### Repositorios Permitidos

```python
# security/sandbox.py

class RepoValidator:
    """Valida operaciones sobre repositorios."""

    def __init__(self, allowed_repos: list[str]):
        self.allowed_repos = allowed_repos

    def is_allowed(self, repo_name: str) -> bool:
        """Verifica si el repo está en la lista permitida."""
        # Si la lista está vacía, permitir todos
        if not self.allowed_repos:
            return True
        return repo_name in self.allowed_repos

    def validate_repo_url(self, url: str) -> bool:
        """Valida que la URL del repo sea de GitHub."""
        import re
        pattern = r'^https://github\.com/[\w-]+/[\w.-]+\.git$'
        return bool(re.match(pattern, url))
```

### Ramas Protegidas

```python
# security/sandbox.py

PROTECTED_BRANCHES = {
    "main",
    "master",
    "develop",
    "development",
    "release",
    "production",
    "staging",
}

def is_protected_branch(branch: str) -> bool:
    """Verifica si una rama está protegida."""
    branch_lower = branch.lower().strip()
    return branch_lower in PROTECTED_BRANCHES

def validate_branch_operation(operation: str, branch: str) -> bool:
    """Valida operaciones sobre ramas."""
    if operation in ("push", "force-push", "delete"):
        if is_protected_branch(branch):
            return False
    return True
```

### Validación de Paths

```python
# security/sandbox.py
from pathlib import Path

def validate_file_path(path: str, base_dir: str) -> bool:
    """
    Verifica que un path esté dentro del directorio permitido.
    Previene directory traversal attacks.
    """
    try:
        base = Path(base_dir).resolve()
        target = Path(base_dir, path).resolve()

        # Verificar que el target esté dentro de base
        return str(target).startswith(str(base))
    except Exception:
        return False

def sanitize_filename(filename: str) -> str:
    """Sanitiza un nombre de archivo."""
    import re
    # Remover caracteres peligrosos
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    # Prevenir traversal
    safe = safe.replace('..', '')
    # Limitar longitud
    return safe[:255]

def sanitize_branch_name(name: str) -> str:
    """Sanitiza un nombre de rama Git."""
    import re
    # Solo caracteres alfanuméricos, guiones, barras y guiones bajos
    safe = re.sub(r'[^a-zA-Z0-9/_-]', '', name)
    # Prevenir traversal
    safe = safe.replace('..', '')
    # Convertir a minúsculas
    return safe.lower()
```

---

## 🐳 Aislamiento Docker

### Dockerfile con Usuario No-Root

```dockerfile
FROM python:3.11-slim

# Crear usuario no-root
RUN groupadd -r orchestrator && useradd -r -g orchestrator orchestrator

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY --chown=orchestrator:orchestrator . .

# Crear directorios con permisos correctos
RUN mkdir -p /opt/dev-orchestrator/repos \
             /opt/dev-orchestrator/logs \
             /opt/dev-orchestrator/data \
    && chown -R orchestrator:orchestrator /opt/dev-orchestrator

# Cambiar a usuario no-root
USER orchestrator

CMD ["python", "-m", "orchestrator.main"]
```

### docker-compose.yml con Restricciones

```yaml
version: "3.8"

services:
  orchestrator:
    build: .
    container_name: dev-orchestrator
    restart: unless-stopped

    # Usuario no-root
    user: "1000:1000"

    # Restricciones de seguridad
    security_opt:
      - no-new-privileges:true

    # Límites de recursos
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G
        reservations:
          cpus: "0.5"
          memory: 512M

    # Red aislada
    networks:
      - orchestrator-internal

    # Volúmenes con permisos restrictivos
    volumes:
      - ./repos:/opt/dev-orchestrator/repos
      - ./logs:/opt/dev-orchestrator/logs
      - ./data:/opt/dev-orchestrator/data
      - ./ai:/app/ai:ro # Read-only
      - ./.env:/app/.env:ro # Read-only

    # Variables de entorno
    env_file:
      - .env

networks:
  orchestrator-internal:
    driver: bridge
    internal: false # Necesita acceso a internet para APIs
```

---

## 📝 Logging Seguro

### Reglas de Logging

```python
# utils/logger.py
import logging
import re

class SecureFormatter(logging.Formatter):
    """Formatter que oculta información sensible."""

    SENSITIVE_PATTERNS = [
        (r'sk-ant-[a-zA-Z0-9-]+', 'sk-ant-***'),
        (r'ghp_[a-zA-Z0-9]+', 'ghp_***'),
        (r'AIzaSy[a-zA-Z0-9-_]+', 'AIzaSy***'),
        (r'\d{9,}:[A-Za-z0-9_-]+', '***:***'),  # Telegram token
        (r'password["\']?\s*[:=]\s*["\']?[^"\']+', 'password=***'),
    ]

    def format(self, record):
        message = super().format(record)

        # Ocultar patrones sensibles
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message)

        return message

def setup_logging():
    """Configura logging seguro."""
    formatter = SecureFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler('/opt/dev-orchestrator/logs/orchestrator.log')
    file_handler.setFormatter(formatter)

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(console)
    root.addHandler(file_handler)
```

### Qué NO Loggear

| ❌ No Loggear                   | ✅ Alternativa       |
| ------------------------------- | -------------------- |
| API keys completas              | Últimos 4 caracteres |
| Tokens                          | `***`                |
| Contenido de archivos sensibles | Hash o tamaño        |
| Credenciales                    | Nunca                |
| IPs de usuarios                 | Solo si necesario    |

---

## ✅ Checklist de Seguridad

### Antes de Deploy

- [ ] `.env` no está en el repositorio
- [ ] `.env` tiene permisos `600`
- [ ] `ALLOWED_TELEGRAM_USERS` está configurado
- [ ] Todas las API keys son válidas
- [ ] Docker corre con usuario no-root
- [ ] Ramas protegidas están configuradas

### Periódicamente

- [ ] Revisar logs por intentos de acceso no autorizado
- [ ] Rotar tokens si hay sospecha de compromiso
- [ ] Actualizar dependencias con vulnerabilidades
- [ ] Verificar que no hay secrets en logs

### En Caso de Compromiso

1. **Inmediatamente:**
   - Revocar todos los tokens/API keys
   - Detener el contenedor
   - Revisar logs

2. **Después:**
   - Generar nuevos tokens
   - Revisar commits recientes
   - Analizar causa raíz

---

## 🔄 Rotación de Secrets

### Cuándo Rotar

| Secret               | Frecuencia | Trigger              |
| -------------------- | ---------- | -------------------- |
| `ANTHROPIC_API_KEY`  | Anual      | Sospecha de leak     |
| `GOOGLE_API_KEY`     | Anual      | Sospecha de leak     |
| `GITHUB_TOKEN`       | 90 días    | Sospecha de leak     |
| `TELEGRAM_BOT_TOKEN` | Nunca\*    | Solo si comprometido |

\*El token de Telegram está vinculado al bot, rotarlo crea un bot nuevo.

### Proceso de Rotación

```bash
# 1. Generar nuevo secret en el proveedor

# 2. Actualizar .env
nano .env

# 3. Reiniciar container
docker-compose restart orchestrator

# 4. Verificar funcionamiento
docker-compose logs -f orchestrator

# 5. Revocar secret anterior en el proveedor
```

---

## 📊 Resumen de Controles

| Control             | Implementación         | Estado |
| ------------------- | ---------------------- | ------ |
| Autenticación       | Whitelist Telegram IDs | ✅     |
| Secrets en .env     | Variables de entorno   | ✅     |
| .env en .gitignore  | No en Git              | ✅     |
| Permisos de .env    | chmod 600              | ✅     |
| Sandbox de comandos | Whitelist              | ✅     |
| Repos permitidos    | Configurable           | ✅     |
| Ramas protegidas    | Blacklist              | ✅     |
| Validación de paths | Prevenir traversal     | ✅     |
| Docker no-root      | USER orchestrator      | ✅     |
| Logging seguro      | Ocultar secrets        | ✅     |

---

_Documento generado por AI Flow - Phase 4: Security & Authentication_
