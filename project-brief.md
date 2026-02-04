# Dev Task Orchestrator - Project Brief

> **Generado:** 2026-02-03  
> **Alcance:** Production-Ready  
> **Estado:** En Desarrollo

---

## 📋 Resumen Ejecutivo

**Dev Task Orchestrator** es un sistema de automatización que permite ejecutar tareas completas de desarrollo de software desde un chat (Telegram/Web), utilizando Claude para planificación y Gemini para ejecución, con entorno Docker, tests y Git automation.

---

## 🎯 Objetivos del Proyecto

| #   | Objetivo                                           | Métrica de Éxito                   |
| --- | -------------------------------------------------- | ---------------------------------- |
| 1   | Ejecutar tareas de desarrollo completas desde chat | Tarea → Rama con código funcional  |
| 2   | Separar planificación de ejecución (Claude/Gemini) | Plan aprobado antes de ejecutar    |
| 3   | Automatizar Git workflow sin merges automáticos    | Branch + Commits + Push automático |
| 4   | Validar código con tests antes de finalizar        | Tests verdes = tarea completada    |

---

## 👥 Usuarios

| Tipo            | Usuario           | Rol                                                     |
| --------------- | ----------------- | ------------------------------------------------------- |
| 👤 **Primario** | Desarrollador     | Envía tareas por chat, revisa planes, aprueba ejecución |
| 🤖 **Sistema**  | Claude (Planner)  | Analiza y genera planes estructurados                   |
| 🤖 **Sistema**  | Gemini (Executor) | Ejecuta código siguiendo el plan                        |
| 🔌 **Interfaz** | Telegram Bot      | Recibe comandos del usuario                             |

---

## 🔄 Flujo Principal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUJO DEL SISTEMA                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  📱 USUARIO                          🎯 ORQUESTADOR
     │                                      │
     │  Mensaje libre                       │
     │ ───────────────────────────────────► │
     │                                      │
     │                              ┌───────┴───────┐
     │                              │ INTENT        │
     │                              │ CLASSIFIER    │
     │                              └───────┬───────┘
     │                                      │
     │              ┌───────────────────────┼───────────────────────┐
     │              │                       │                       │
     │              ▼                       ▼                       ▼
     │         ┌────────┐             ┌──────────┐            ┌──────────┐
     │         │ QUERY  │             │ TASK_NEW │            │ CONTINUE │
     │         └────┬───┘             └────┬─────┘            └────┬─────┘
     │              │                      │                       │
     │      ┌───────┴───────┐              │                       │
     │      │ ¿Simple?      │              │                       │
     │      └───────┬───────┘              │                       │
     │         Sí   │   No                 │                       │
     │              │                      │                       │
     │    ┌─────────┴─────────┐            │                       │
     │    ▼                   ▼            ▼                       ▼
     │ Respuesta         Iterar →     Clasificar tipo         Cargar estado
     │ directa           Clarificar   (feat/fix/refactor)     guardado
     │                   → Informe          │                       │
     │                                      ▼                       │
     │                              ¿Necesita clarificar?           │
     │                                 Sí │ No                      │
     │                              ◄─────┼──────                   │
     │     Plan propuesto                 ▼                         │
     │ ◄───────────────────────────  Generar Plan  ◄────────────────┘
     │                                      │
     │  Iterar/Ajustar (máx 10 rondas)      │
     │ ───────────────────────────────────► │
     │ ◄─────────────────────────────────── │
     │                                      │
     │  "Aprobar" (explícito)               │
     │ ───────────────────────────────────► │
     │                                      │
     │                              ┌───────┴───────┐
     │                              │ VALIDACIÓN    │
     │                              │ PRE-EJECUCIÓN │
     │                              └───────┬───────┘
     │                                      │
     │                              ┌───────┴───────┐
     │                              │ Crear rama    │
     │                              │ (feat/fix/...)│
     │                              └───────┬───────┘
     │                                      │
     │  ⏳ Actualizaciones                  │
     │ ◄─────────────────────────── ┌───────┴───────┐
     │                              │   EXECUTOR    │
     │                              │ ┌───────────┐ │
     │                              │ │ Editar    │ │
     │                              │ │    ↓      │ │
     │                              │ │ Test      │ │
     │                              │ │    ↓      │ │
     │                              │ │ Checkpoint│ │
     │                              │ │    ↓      │ │
     │                              │ │ ¿OK? ─No──┼─┐
     │                              │ │  │        │ │
     │                              │ │  Sí       │ │ Retry (max 3)
     │                              │ └──┼────────┘ │
     │                              │    │       ◄──┘
     │                              └────┼──────────┘
     │                                   │
     │                           ┌───────┴───────┐
     │                           │ ¿Completado?  │
     │                           └───────┬───────┘
     │                              Sí   │   No (timeout/error)
     │                           ┌───────┴───────┐
     │                           ▼               ▼
     │                     Commit final    Commit parcial
     │                     + Push          + Push
     │                           │               │
     │     Link de rama          └───────┬───────┘
     │ ◄─────────────────────────────────┘
     ▼
```

---

## 🏗️ Clasificación de Intents

| Intent          | Ejemplo                          | Acción                      |
| --------------- | -------------------------------- | --------------------------- |
| `QUERY`         | "¿Cómo funciona el módulo X?"    | Respuesta directa o iterada |
| `TASK_NEW`      | "Agregar validación de stock"    | Crear plan → ejecutar       |
| `TASK_CONTINUE` | "Continúa con la tarea anterior" | Retomar estado guardado     |
| `TASK_LIST`     | "¿Qué tareas tengo pendientes?"  | Listar tareas en progreso   |
| `TASK_ABORT`    | "Cancela la tarea actual"        | Guardar estado → abortar    |

---

## 🏷️ Tipos de Tarea

| Tipo       | Rama                   | Ejemplo                     |
| ---------- | ---------------------- | --------------------------- |
| `feat`     | `feature/descripcion`  | Nueva funcionalidad         |
| `fix`      | `fix/descripcion`      | Corrección de bug           |
| `refactor` | `refactor/descripcion` | Mejora sin cambio funcional |
| `docs`     | `docs/descripcion`     | Solo documentación          |
| `test`     | `test/descripcion`     | Solo tests                  |
| `chore`    | `chore/descripcion`    | Configuración/dependencias  |

---

## ✨ Features Principales

| Módulo          | Feature                                      | Prioridad  |
| --------------- | -------------------------------------------- | ---------- |
| **Orquestador** | Recibir tarea y gestionar flujo completo     | 🔴 Crítica |
| **Orquestador** | Intent Classifier (detectar intención)       | 🔴 Crítica |
| **Planner**     | Generar plan estructurado con Claude         | 🔴 Crítica |
| **Planner**     | Iterar plan hasta aprobación del usuario     | 🔴 Crítica |
| **Executor**    | Ejecutar código con Gemini siguiendo el plan | 🔴 Crítica |
| **Executor**    | Ciclo automático: editar → tests → corregir  | 🔴 Crítica |
| **Executor**    | Checkpoints automáticos cada 5 min           | 🟡 Alta    |
| **Executor**    | Notificaciones proactivas de progreso        | 🟡 Alta    |
| **Git Agent**   | Crear rama por tarea (convención)            | 🔴 Crítica |
| **Git Agent**   | Commits descriptivos (Conventional Commits)  | 🟡 Alta    |
| **Git Agent**   | Push automático (nunca a main/dev)           | 🔴 Crítica |
| **Git Agent**   | Commit parcial si timeout/error              | 🟡 Alta    |
| **State**       | Persistir estado de tareas (SQLite)          | 🔴 Crítica |
| **State**       | Recovery desde checkpoints                   | 🟡 Alta    |
| **Prompts**     | Sistema de prompts versionados (.md)         | 🟡 Alta    |
| **CLI**         | `run_task.py` para ejecución local           | 🔴 Crítica |
| **Chat**        | Telegram Bot conversacional                  | 🟢 Media   |

---

## 🔒 Restricciones Inviolables

| #   | Restricción                                          | Tipo          |
| --- | ---------------------------------------------------- | ------------- |
| 1   | **Nunca hacer merge automático**                     | 🔒 Inviolable |
| 2   | **Nunca push a main/master/develop**                 | 🔒 Inviolable |
| 3   | **El chat solo envía mensajes, no toma decisiones**  | 🔒 Inviolable |
| 4   | **Planner (Claude) no ejecuta código**               | 🔒 Inviolable |
| 5   | **Executor (Gemini) solo sigue el plan aprobado**    | 🔒 Inviolable |
| 6   | **Tareas solo se ejecutan con aprobación explícita** | 🔒 Inviolable |
| 7   | **Todo corre en VM Ubuntu persistente**              | ⚙️ Técnica    |
| 8   | **Tests deben pasar antes de commit final**          | 📋 Proceso    |
| 9   | **Los prompts son archivos .md versionados**         | ⚙️ Técnica    |
| 10  | **Máximo 10 rondas de iteración por clarificación**  | 📋 Proceso    |

---

## 📂 Estructura de Archivos por Tarea

### En la Rama (Git - accesible desde cualquier PC)

```
feature/validacion-stock/
├── src/                      # Código del proyecto
├── tests/                    # Tests del proyecto
└── .dev-tasks/               # Directorio de tareas
    └── task-uuid-123/
        ├── plan.md           # Plan aprobado (inmutable)
        ├── progress.md       # Progreso + instrucciones manuales
        └── state.json        # Estado parseable por el orquestador
```

### En la VM (Local - solo orquestador)

```
/opt/dev-orchestrator/logs/
└── task-uuid-123/
    ├── execution.log         # Log detallado
    ├── errors.log            # Errores capturados
    └── checkpoints/          # Snapshots para recovery
        ├── cp-001.json
        └── cp-002.json
```

---

## 📊 Métricas de Éxito

| Métrica                       | Objetivo           | Cómo Medir                   |
| ----------------------------- | ------------------ | ---------------------------- |
| **Tasa de éxito de tareas**   | ≥ 80%              | `completadas / totales`      |
| **Tiempo promedio por tarea** | < 30 min (simples) | Timestamp inicio → fin       |
| **Tasa de rollback**          | < 10%              | Tareas canceladas            |
| **Cobertura de tests**        | ≥ 80%              | pytest --cov                 |
| **Clarificaciones por tarea** | ≤ 3 rondas         | Iteraciones antes de aprobar |

---

## ⚙️ Configuración y Límites

```json
{
  "max_execution_time": "30min",
  "max_retries_per_test": 3,
  "max_files_per_task": 20,
  "checkpoint_interval": "5min",
  "max_clarification_rounds": 10
}
```

---

## 🔌 Integraciones

### Core (Críticas)

| Integración               | Propósito               |
| ------------------------- | ----------------------- |
| Anthropic API (Claude)    | Planificación de tareas |
| Google AI Studio (Gemini) | Ejecución de código     |
| GitHub API                | Push, branches, links   |
| Telegram Bot API          | Interfaz de usuario     |
| Docker                    | Entorno de ejecución    |
| SQLite                    | Persistencia de estado  |

### Futuras (Opcionales)

| Integración | Propósito                     |
| ----------- | ----------------------------- |
| Webhooks    | Notificaciones flexibles      |
| Sentry      | Error tracking                |
| Redis       | Estado compartido (si escala) |
| PostgreSQL  | DB robusta (si escala)        |

---

## 🛠️ Stack Tecnológico

| Capa                 | Tecnología              | Versión             |
| -------------------- | ----------------------- | ------------------- |
| **Lenguaje**         | Python                  | 3.11+               |
| **Runtime**          | Ubuntu Server           | 22.04/24.04 LTS     |
| **Containerización** | Docker + Docker Compose | Latest              |
| **Base de Datos**    | SQLite                  | 3.x                 |
| **AI - Planner**     | Anthropic API           | Claude 3.5/4 Sonnet |
| **AI - Executor**    | Google AI Studio        | Gemini 2.0 Flash    |
| **Git Provider**     | GitHub API              | REST                |
| **Chat Interface**   | Telegram Bot API        | python-telegram-bot |
| **Config**           | .env + python-dotenv    | -                   |
| **Deploy**           | GitHub Actions → VM     | -                   |
| **Secrets**          | .env file               | -                   |
| **Backups**          | Rotación local + manual | -                   |

---

## 🐳 Ejecución de Repos Externos

El orquestador detecta automáticamente el tipo de proyecto:

```
¿Tiene docker-compose.yml?
├── SÍ → Usar Docker del proyecto
└── NO → Detectar lenguaje
         ├── Python → crear venv, pip install
         ├── Node → npm install
         └── etc.
```

---

## 🔄 Flujo Git

```
TAREA NUEVA:
────────────
develop ──┬── feature/descripcion
          │         │
          │         ├── commit 1
          │         ├── commit 2
          │         └── push → link al usuario
          │
          └── (nunca merge automático)

TAREA EXISTENTE (continuar):
────────────────────────────
feature/descripcion ── (ya existe)
          │
          ├── cargar último checkpoint
          ├── continuar desde donde quedó
          └── push → link al usuario
```

---

## 📱 Comandos de Chat (Atajos)

| Comando     | Alternativa Natural     | Acción                  |
| ----------- | ----------------------- | ----------------------- |
| `/tareas`   | "qué tareas tengo?"     | Lista tareas pendientes |
| `/estado`   | "cómo va la tarea?"     | Estado de tarea actual  |
| `/aprobar`  | "apruebo", "ok", "dale" | Aprueba plan y ejecuta  |
| `/cancelar` | "cancela", "aborta"     | Cancela tarea actual    |
| `/ayuda`    | "cómo funciona esto?"   | Muestra ayuda           |

---

## 📁 Estructura del Proyecto

```
dev-orchestrator/
├── orchestrator/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── intent_classifier.py # Clasificador de intenciones
│   ├── planner.py           # Integración con Claude
│   ├── executor.py          # Integración con Gemini
│   ├── git_agent.py         # Operaciones Git
│   ├── state.py             # Gestión de estado
│   └── config.py            # Configuración
├── ai/
│   ├── system/
│   │   └── base.md          # Reglas globales
│   ├── planner/
│   │   ├── role.md
│   │   └── constraints.md
│   ├── executor/
│   │   ├── role.md
│   │   └── coding_rules.md
│   ├── git/
│   │   └── rules.md
│   └── testing/
│       └── rules.md
├── scripts/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── run_task.py              # CLI
├── requirements.txt
└── README.md
```

---

_Documento generado por AI Flow - Phase 1: Discovery & Business_
