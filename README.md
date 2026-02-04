# Dev Task Orchestrator

Sistema de orquestación de tareas de desarrollo impulsado por IA que ejecuta tareas de programación a través de un chat de Telegram.

## 🎯 Descripción

Dev Task Orchestrator es un agente autónomo que:

- Recibe instrucciones de desarrollo via Telegram
- Genera planes de ejecución usando Claude (Anthropic)
- Ejecuta código de forma segura con Gemini (Google)
- Gestiona branches, commits y PRs automáticamente
- Mantiene checkpoints para recuperación ante fallos

## 🏗️ Arquitectura

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Telegram   │────▶│   Orchestrator   │────▶│   GitHub    │
│    Bot      │◀────│                  │◀────│    Repos    │
└─────────────┘     └──────────────────┘     └─────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  Claude  │  │  Gemini  │  │  Docker  │
        │ (Plan)   │  │ (Execute)│  │ (Sandbox)│
        └──────────┘  └──────────┘  └──────────┘
```

## 🚀 Quick Start

### Prerequisitos

- Python 3.11+
- Docker & Docker Compose
- Cuenta de Telegram
- API keys: Anthropic, Google AI Studio, GitHub

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/your-org/dev-orchestrator.git
cd dev-orchestrator

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -e ".[dev]"

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

### Ejecutar Localmente

```bash
# Desarrollo
python -m src.main --debug

# Con Docker
docker compose -f docker-compose.dev.yml up
```

### Ejecutar en Producción

```bash
# En la VM
cd /opt/dev-orchestrator
./scripts/deploy.sh main
```

## 📱 Uso

### Comandos de Telegram

| Comando               | Descripción             |
| --------------------- | ----------------------- |
| `/start`              | Iniciar bot             |
| `/task <descripción>` | Crear nueva tarea       |
| `/status`             | Ver tareas activas      |
| `/list`               | Listar todas las tareas |
| `/abort`              | Cancelar tarea actual   |
| `/help`               | Mostrar ayuda           |

### Ejemplo de Conversación

```
Usuario: /task Agregar validación de email en el servicio de usuarios
         https://github.com/mi-org/mi-repo

Bot: 📋 He analizado tu solicitud. Este es el plan:

     **Objetivo**: Agregar validación de email
     **Archivos a modificar**:
     - src/services/user_service.py
     - tests/test_user_service.py

     **Pasos**:
     1. Crear función validate_email()
     2. Integrar en create_user()
     3. Agregar tests unitarios

     ⏱️ Tiempo estimado: 15 minutos

     ¿Aprobar este plan? [Sí] [No] [Modificar]

Usuario: Sí

Bot: ✅ Plan aprobado. Iniciando ejecución...
     📍 Paso 1/3: Creando función validate_email()
     📍 Paso 2/3: Integrando en create_user()
     📍 Paso 3/3: Agregando tests unitarios

     ✅ Tarea completada!
     🔗 PR creado: https://github.com/mi-org/mi-repo/pull/42
```

## 🔧 Configuración

### Variables de Entorno

| Variable                 | Descripción                      | Requerida |
| ------------------------ | -------------------------------- | --------- |
| `TELEGRAM_BOT_TOKEN`     | Token del bot de Telegram        | ✅        |
| `TELEGRAM_ALLOWED_USERS` | IDs permitidos (comma-separated) | ✅        |
| `ANTHROPIC_API_KEY`      | API key de Anthropic             | ✅        |
| `GOOGLE_AI_API_KEY`      | API key de Google AI Studio      | ✅        |
| `GITHUB_TOKEN`           | Personal Access Token            | ✅        |
| `LOG_LEVEL`              | Nivel de logging                 | ❌        |

### Archivos de Configuración

- `.env` - Variables de entorno (no en Git)
- `pyproject.toml` - Configuración de Python, linting, tests

## 📁 Estructura del Proyecto

```
dev-orchestrator/
├── src/
│   ├── main.py              # Entry point
│   ├── core/                # Lógica principal
│   ├── agents/              # Agentes AI
│   ├── chat/                # Telegram bot
│   ├── git/                 # GitHub operations
│   ├── models/              # Data models
│   └── utils/               # Utilidades
├── tests/                   # Tests
├── docs/                    # Documentación
├── specs/                   # Especificaciones
├── docker/                  # Docker configs
└── scripts/                 # Scripts operativos
```

## 🧪 Testing

```bash
# Todos los tests
pytest

# Con coverage
pytest --cov=src --cov-report=html

# Solo unit tests
pytest -m unit

# Solo integration tests
pytest -m integration
```

## 📊 Desarrollo

### Linting y Formato

```bash
# Formatear código
ruff format src tests

# Verificar linting
ruff check src tests

# Type checking
mypy src
```

### Pre-commit Hooks

```bash
# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

## 🔒 Seguridad

- **Autenticación**: Whitelist de usuarios de Telegram
- **Sandbox**: Ejecución en contenedores Docker aislados
- **Branches protegidos**: main, master, develop no pueden ser modificados directamente
- **Secrets**: Variables de entorno, nunca en código

## 📚 Documentación

- [Project Brief](project-brief.md) - Visión general del proyecto
- [Data Model](docs/data-model.md) - Modelo de datos
- [Architecture](docs/architecture.md) - Arquitectura del sistema
- [Security](specs/security.md) - Políticas de seguridad
- [Code Standards](docs/code-standards.md) - Estándares de código
- [Testing](docs/testing.md) - Estrategia de testing
- [Operations](docs/operations.md) - Operaciones y deployment

## 🤝 Contribuir

1. Fork el repositorio
2. Crear branch: `git checkout -b feature/mi-feature`
3. Commit: `git commit -m "feat: agregar mi feature"`
4. Push: `git push origin feature/mi-feature`
5. Crear Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

## 👤 Autor

Desarrollado con ❤️ y mucha IA.
