
# Dev Task Orchestrator — Plan Maestro de Implementación

## Objetivo del Proyecto

Construir una herramienta que permita **ejecutar tareas completas de desarrollo de software desde un chat (Telegram/Web)**, sin depender de una notebook, utilizando:

- **Claude Opus / Sonnet 4.5** para *planificación*
- **Gemini 3 Flash** para *ejecución*
- **Prompts personalizados versionados**
- **Entorno real con Docker, tests y Git**
- **Ubuntu LTS como runtime**

El sistema debe:
- Recibir una tarea por chat
- Generar un plan
- Permitir iterar el plan
- Ejecutar la tarea end-to-end
- Crear una rama
- Ejecutar tests
- Hacer commit y push
- Devolver el enlace de la rama

---

## Principios Fundamentales

1. Separación estricta de responsabilidades:
   - **Planner (Claude)**: analiza y planifica, no ejecuta
   - **Executor (Gemini)**: ejecuta código siguiendo el plan
2. El chat es solo una interfaz, no toma decisiones
3. Todo corre en una **VM Ubuntu persistente**
4. Los prompts son parte de la infraestructura
5. Nunca se hace merge automático

---

## Fase 0 — Preparación del Entorno

### 0.1 Crear la VM

- VirtualBox
- Ubuntu Server 22.04 LTS o 24.04 LTS
- 4 CPU / 8 GB RAM / 100 GB Disco
- SSH habilitado

### 0.2 Instalar dependencias base

- git
- docker + docker compose
- python 3.11+
- herramientas CLI (curl, jq, tmux)

### 0.3 Estructura base en la VM

```bash
/opt/dev-orchestrator
  /orchestrator
  /ai
  /repos
  /logs
  /scripts
```

---

## Fase 1 — Repositorio del Proyecto

Crear repositorio: `dev-orchestrator`

Estructura inicial:

```
dev-orchestrator/
  orchestrator/
    __init__.py
    main.py
    planner.py
    executor.py
    git_agent.py
    state.py
    config.py
  ai/
    system/
      base.md
    planner/
      role.md
      constraints.md
    executor/
      role.md
      coding_rules.md
    git/
      rules.md
    testing/
      rules.md
  scripts/
  run_task.py
  README.md
```

---

## Fase 2 — Sistema de Prompts

### 2.1 Principios

- Todos los prompts son archivos `.md`
- Versionados con Git
- Cargados dinámicamente por el orquestador

### 2.2 Tipos de prompts

- system/base.md → reglas globales
- planner/* → reglas para Claude
- executor/* → reglas para Gemini
- git/rules.md → reglas de Git
- testing/rules.md → cómo validar finalización

---

## Fase 3 — Modelo de Estado

Cada tarea tiene un estado persistente:

```json
{
  "task_id": "uuid",
  "status": "PLANNING | PLANNED | EXECUTING | COMPLETED | FAILED",
  "repo": "repo-name",
  "branch": "task/<id>",
  "plan": {},
  "logs": []
}
```

El estado se guarda en:
- SQLite o JSON (MVP)
- Redis opcional

---

## Fase 4 — Planificación (Claude)

### Flujo

1. Usuario envía tarea
2. Orquestador llama a Claude con:
   - descripción
   - contexto del repo
   - prompts de planner
3. Claude devuelve plan estructurado

Ejemplo:

```yaml
plan:
  - Analizar módulo de ventas
  - Agregar validación de stock
  - Crear tests
criteria:
  - Tests verdes
  - No romper flujo actual
```

4. El plan se devuelve al chat
5. El usuario puede pedir ajustes
6. Se itera hasta aprobación explícita

---

## Fase 5 — Ejecución (Gemini)

### Flujo

1. Checkout `development`
2. Crear rama de tarea
3. Enviar a Gemini:
   - plan aprobado
   - prompts de executor
   - contexto del código
4. Ciclo automático:

```
editar código
→ correr tests
→ analizar errores
→ corregir
→ repetir
```

5. Validar criterios de finalización
6. Commit + push

---

## Fase 6 — Git Automation

Reglas:
- Nunca push a main/dev
- Rama por tarea
- Commits descriptivos

Ejemplo de commit:

```
feat: validar stock negativo en ventas

- agrega validación en servicio
- tests unitarios incluidos
```

---

## Fase 7 — Interfaz de Chat (posterior)

### MVP

- Telegram Bot
- Comandos básicos:
  - /task nueva tarea
  - /plan aprobar
  - /status
  - /abort

El chat solo envía comandos al orquestador.

---

## Fase 8 — Desarrollo Iterativo

Orden recomendado:

1. CLI funcional (`run_task.py`)
2. Planificación con Claude
3. Ejecución con Gemini
4. Git automation
5. Tests
6. Chat

---

## Regla de Oro

> Si una tarea no puede ejecutarse sola desde la VM,
> no está lista para producción.

---

## Resultado Final Esperado

Desde un celular o web:

- Enviar tarea
- Ajustar plan
- Ejecutar
- Recibir link de rama
- Revisar y hacer PR

Sin notebook.

---

## Estado del Proyecto

Este archivo es la **fuente de verdad**.
No perder la ruta.
No saltar fases.
No automatizar sin control.
