# Implementation Roadmap

## Visión General

Este roadmap define las fases de implementación del Dev Task Orchestrator, organizadas por prioridad y dependencias.

## Fases de Desarrollo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IMPLEMENTATION ROADMAP                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: Foundation (Semanas 1-2)                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Config    │ │  Database   │ │   Models    │ │   Logging   │           │
│  │   System    │ │   Setup     │ │   (Pydantic)│ │   Setup     │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│         │              │               │               │                    │
│         └──────────────┴───────────────┴───────────────┘                    │
│                                │                                            │
│  Phase 2: Chat Interface (Semanas 3-4)                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                           │
│  │  Telegram   │ │    Auth     │ │   Command   │                           │
│  │    Bot      │ │  Whitelist  │ │  Handlers   │                           │
│  └─────────────┘ └─────────────┘ └─────────────┘                           │
│         │              │               │                                    │
│         └──────────────┴───────────────┘                                    │
│                                │                                            │
│  Phase 3: AI Agents (Semanas 5-7)                                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                           │
│  │   Intent    │ │    Plan     │ │   Task      │                           │
│  │ Classifier  │ │  Generator  │ │  Executor   │                           │
│  └─────────────┘ └─────────────┘ └─────────────┘                           │
│         │              │               │                                    │
│         └──────────────┴───────────────┘                                    │
│                                │                                            │
│  Phase 4: Git Operations (Semanas 8-9)                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                           │
│  │    Clone    │ │   Branch    │ │     PR      │                           │
│  │    Repos    │ │   Commits   │ │  Creation   │                           │
│  └─────────────┘ └─────────────┘ └─────────────┘                           │
│         │              │               │                                    │
│         └──────────────┴───────────────┘                                    │
│                                │                                            │
│  Phase 5: Execution & Safety (Semanas 10-12)                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Docker    │ │  Checkpoint │ │   Timeout   │ │   Partial   │           │
│  │   Sandbox   │ │   System    │ │  Handling   │ │   Commits   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                                              │
│  Phase 6: Polish & Deploy (Semanas 13-14)                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                           │
│  │   Docker    │ │    CI/CD    │ │  Monitoring │                           │
│  │   Deploy    │ │   Pipeline  │ │   & Logs    │                           │
│  └─────────────┘ └─────────────┘ └─────────────┘                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (Semanas 1-2)

### Objetivo

Establecer la base del proyecto con configuración, modelos y persistencia.

### Entregables

| Tarea                     | Archivo(s)                           | Prioridad | Estimación |
| ------------------------- | ------------------------------------ | --------- | ---------- |
| Setup proyecto Python     | `pyproject.toml`, `requirements.txt` | P0        | 2h         |
| Sistema de configuración  | `src/core/config.py`                 | P0        | 4h         |
| Modelos de datos Pydantic | `src/models/task.py`                 | P0        | 4h         |
| SQLAlchemy models         | `src/models/database.py`             | P0        | 6h         |
| Sistema de logging        | `src/core/logging_config.py`         | P1        | 3h         |
| Tests unitarios base      | `tests/unit/test_models.py`          | P1        | 4h         |

### Criterios de Aceptación

- [ ] `pip install -e .` funciona sin errores
- [ ] Configuración carga desde `.env`
- [ ] SQLite DB se crea automáticamente
- [ ] Modelos Task serializan/deserializan correctamente
- [ ] Tests pasan con `pytest -m unit`

### Dependencias

- Ninguna (fase inicial)

---

## Phase 2: Chat Interface (Semanas 3-4)

### Objetivo

Implementar el bot de Telegram con autenticación y comandos básicos.

### Entregables

| Tarea                             | Archivo(s)                    | Prioridad | Estimación |
| --------------------------------- | ----------------------------- | --------- | ---------- |
| Bot Telegram base                 | `src/chat/telegram_bot.py`    | P0        | 8h         |
| Sistema de autenticación          | `src/chat/auth.py`            | P0        | 4h         |
| Comando /start, /help             | `src/chat/handlers/`          | P0        | 3h         |
| Comando /task                     | `src/chat/handlers/task.py`   | P0        | 4h         |
| Comando /status, /list            | `src/chat/handlers/status.py` | P1        | 3h         |
| Comando /abort                    | `src/chat/handlers/abort.py`  | P1        | 2h         |
| Botones inline (aprobar/rechazar) | `src/chat/keyboards.py`       | P1        | 3h         |
| Tests de handlers                 | `tests/unit/test_telegram.py` | P1        | 4h         |

### Criterios de Aceptación

- [ ] Bot responde a `/start` con mensaje de bienvenida
- [ ] Usuarios no autorizados son rechazados
- [ ] `/task` crea entrada en base de datos
- [ ] Botones de aprobación funcionan
- [ ] Logs muestran actividad del bot

### Dependencias

- Phase 1 completada

---

## Phase 3: AI Agents (Semanas 5-7)

### Objetivo

Implementar los agentes de IA para clasificación, planificación y ejecución.

### Entregables

| Tarea                     | Archivo(s)                        | Prioridad | Estimación |
| ------------------------- | --------------------------------- | --------- | ---------- |
| Cliente Anthropic wrapper | `src/agents/anthropic_client.py`  | P0        | 4h         |
| Intent Classifier         | `src/agents/intent_classifier.py` | P0        | 8h         |
| Clarification flow        | `src/agents/clarifier.py`         | P0        | 6h         |
| Plan Generator            | `src/agents/plan_generator.py`    | P0        | 10h        |
| Cliente Google AI wrapper | `src/agents/google_client.py`     | P0        | 4h         |
| Task Executor base        | `src/agents/executor.py`          | P0        | 12h        |
| Prompts engineering       | `src/agents/prompts/`             | P1        | 8h         |
| Tests con mocks           | `tests/unit/test_agents.py`       | P1        | 8h         |

### Criterios de Aceptación

- [ ] Intent classifier distingue 5 tipos de intent
- [ ] Clarificación funciona hasta 10 rondas
- [ ] Plan generator produce JSON válido
- [ ] Executor ejecuta pasos secuencialmente
- [ ] Mocks permiten testing sin APIs reales

### Dependencias

- Phase 2 completada
- API keys configuradas

---

## Phase 4: Git Operations (Semanas 8-9)

### Objetivo

Implementar todas las operaciones de Git y GitHub.

### Entregables

| Tarea                    | Archivo(s)                      | Prioridad | Estimación |
| ------------------------ | ------------------------------- | --------- | ---------- |
| GitHub API client        | `src/git/github_client.py`      | P0        | 4h         |
| Clone repositories       | `src/git/operations.py`         | P0        | 4h         |
| Branch management        | `src/git/branch.py`             | P0        | 4h         |
| Commit changes           | `src/git/commit.py`             | P0        | 4h         |
| Push to remote           | `src/git/push.py`               | P0        | 3h         |
| Create PR                | `src/git/pull_request.py`       | P0        | 4h         |
| Protected branches check | `src/git/security.py`           | P0        | 2h         |
| .dev-tasks management    | `src/git/task_state.py`         | P1        | 6h         |
| Tests con repo temporal  | `tests/integration/test_git.py` | P1        | 6h         |

### Criterios de Aceptación

- [ ] Clone funciona con repos públicos y privados
- [ ] Branches se crean desde main/master
- [ ] Commits siguen conventional commits
- [ ] PRs se crean con descripción del plan
- [ ] No se puede hacer push a branches protegidos
- [ ] Estado se guarda en `.dev-tasks/`

### Dependencias

- Phase 3 completada
- GitHub token configurado

---

## Phase 5: Execution & Safety (Semanas 10-12)

### Objetivo

Implementar ejecución segura con sandbox, checkpoints y recuperación.

### Entregables

| Tarea                    | Archivo(s)                            | Prioridad | Estimación |
| ------------------------ | ------------------------------------- | --------- | ---------- |
| Docker sandbox runner    | `src/sandbox/docker_runner.py`        | P0        | 10h        |
| Allowed commands list    | `src/sandbox/commands.py`             | P0        | 4h         |
| Checkpoint system        | `src/core/checkpoint.py`              | P0        | 8h         |
| Timeout handling         | `src/core/timeout.py`                 | P0        | 4h         |
| Partial commit on error  | `src/core/recovery.py`                | P0        | 6h         |
| Progress notifications   | `src/chat/notifications.py`           | P1        | 4h         |
| Orchestrator integration | `src/core/orchestrator.py`            | P0        | 8h         |
| Integration tests        | `tests/integration/test_execution.py` | P1        | 8h         |

### Criterios de Aceptación

- [ ] Código se ejecuta en contenedor aislado
- [ ] Solo comandos permitidos pueden ejecutarse
- [ ] Checkpoint cada 5 minutos
- [ ] Timeout de 30 min cancela tarea
- [ ] Error produce commit parcial
- [ ] Usuario recibe notificaciones de progreso

### Dependencias

- Phase 4 completada
- Docker disponible en VM

---

## Phase 6: Polish & Deploy (Semanas 13-14)

### Objetivo

Preparar para producción con Docker, CI/CD y monitoreo.

### Entregables

| Tarea                 | Archivo(s)                     | Prioridad | Estimación |
| --------------------- | ------------------------------ | --------- | ---------- |
| Dockerfile producción | `Dockerfile`                   | P0        | 4h         |
| Docker Compose        | `docker-compose.yml`           | P0        | 3h         |
| GitHub Actions CI     | `.github/workflows/test.yml`   | P0        | 4h         |
| GitHub Actions CD     | `.github/workflows/deploy.yml` | P1        | 4h         |
| Health check endpoint | `src/core/health.py`           | P1        | 3h         |
| Deployment scripts    | `scripts/*.sh`                 | P1        | 4h         |
| Documentation final   | `README.md`, `docs/`           | P1        | 4h         |
| End-to-end tests      | `tests/e2e/`                   | P2        | 8h         |

### Criterios de Aceptación

- [ ] `docker compose up` inicia el sistema
- [ ] CI corre tests en cada PR
- [ ] CD despliega a VM automáticamente
- [ ] Health endpoint responde en `/health`
- [ ] Scripts de backup/restore funcionan
- [ ] README tiene instrucciones completas

### Dependencias

- Phase 5 completada
- VM configurada

---

## Timeline Visual

```
Semana:  1   2   3   4   5   6   7   8   9  10  11  12  13  14
         ├───┴───┼───┴───┼───┴───┴───┼───┴───┼───┴───┴───┼───┴───┤
Phase 1: ████████│       │           │       │           │       │
Phase 2:         ████████│           │       │           │       │
Phase 3:                 ████████████│       │           │       │
Phase 4:                             ████████│           │       │
Phase 5:                                     ████████████│       │
Phase 6:                                                 ████████│
         │       │       │           │       │           │       │
         ▼       ▼       ▼           ▼       ▼           ▼       ▼
      Config  Telegram  AI Ready   Git OK  Execution  Production
      Ready   Working              Working  Safe       Ready
```

---

## Milestones

### M1: Foundation Complete (Fin Semana 2)

- Proyecto configurado y ejecutable
- Base de datos funcional
- Tests base pasando

### M2: Chat Functional (Fin Semana 4)

- Bot responde comandos
- Autenticación funciona
- Usuarios pueden crear tareas

### M3: AI Integrated (Fin Semana 7)

- Clasificación de intents funciona
- Planes se generan automáticamente
- Ejecución básica de pasos

### M4: Git Complete (Fin Semana 9)

- Clonado de repos funciona
- Branches y commits automáticos
- PRs se crean correctamente

### M5: Safe Execution (Fin Semana 12)

- Sandbox Docker funciona
- Checkpoints y recovery
- Notificaciones de progreso

### M6: Production Ready (Fin Semana 14)

- Desplegado en VM
- CI/CD configurado
- Documentación completa

---

## Riesgos y Mitigaciones

| Riesgo                       | Probabilidad | Impacto | Mitigación                                           |
| ---------------------------- | ------------ | ------- | ---------------------------------------------------- |
| API rate limits              | Media        | Alto    | Implementar caching y backoff                        |
| Complejidad Docker-in-Docker | Alta         | Medio   | Usar socket mount en lugar de DinD                   |
| Prompts AI inconsistentes    | Media        | Alto    | Testing extensivo, fallbacks                         |
| Timeout en tareas largas     | Alta         | Medio   | Checkpoints frecuentes                               |
| Costos API elevados          | Media        | Medio   | Límites de uso, modelo más barato para clasificación |

---

## Recursos Necesarios

### Desarrollo

- 1 desarrollador Python senior
- ~280 horas totales (14 semanas × 20h/semana)

### Infraestructura

- VM Ubuntu (mínimo 2 CPU, 4GB RAM)
- Dominio (opcional, para webhooks)
- GitHub repo privado

### APIs y Servicios

- Telegram Bot Token (gratis)
- Anthropic API (~$50-100/mes estimado)
- Google AI Studio (gratis tier o ~$20/mes)
- GitHub Token (gratis)

---

## Checklist de Lanzamiento

### Pre-Launch

- [ ] Todos los tests pasan (>85% coverage)
- [ ] Secrets configurados en VM
- [ ] Backups configurados
- [ ] Monitoreo activo
- [ ] Documentación revisada

### Launch Day

- [ ] Deploy a producción
- [ ] Verificar health check
- [ ] Enviar mensaje de prueba
- [ ] Ejecutar tarea de prueba
- [ ] Verificar PR creado

### Post-Launch

- [ ] Monitorear logs primeras 24h
- [ ] Ajustar rate limits si necesario
- [ ] Documentar issues encontrados
- [ ] Planificar mejoras v1.1
