# Data Model - Dev Task Orchestrator

> **Generado:** 2026-02-03  
> **Fase:** 2 - Data Architecture

---

## 📊 Resumen de Arquitectura

| Componente                  | Tecnología | Ubicación                          |
| --------------------------- | ---------- | ---------------------------------- |
| **Base de Datos Principal** | SQLite     | VM (`/opt/dev-orchestrator/data/`) |
| **Estado de Tareas**        | JSON       | Rama Git (`.dev-tasks/`)           |
| **Documentos Legibles**     | Markdown   | Rama Git (`.dev-tasks/`)           |
| **Checkpoints**             | JSON       | VM (`/opt/dev-orchestrator/logs/`) |
| **Prompts**                 | Markdown   | Repo (`/ai/`)                      |

---

## 🗄️ Esquema SQLite

### Tabla: `tasks`

Registro principal de todas las tareas.

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,                              -- UUID
    repo TEXT NOT NULL,                               -- Nombre del repositorio
    branch TEXT,                                      -- Rama creada para la tarea
    type TEXT NOT NULL,                               -- feat, fix, refactor, docs, test, chore
    title TEXT NOT NULL,                              -- Título corto
    description TEXT,                                 -- Descripción completa
    status TEXT NOT NULL DEFAULT 'PLANNING',          -- Estado actual
    intent TEXT NOT NULL,                             -- Tipo de intent detectado
    current_step INTEGER NOT NULL DEFAULT 0,          -- Paso actual
    total_steps INTEGER NOT NULL DEFAULT 0,           -- Total de pasos
    error_message TEXT,                               -- Último error
    retries INTEGER NOT NULL DEFAULT 0,               -- Reintentos realizados
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

-- Índices
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_repo ON tasks(repo);
CREATE INDEX idx_tasks_created ON tasks(created_at);
CREATE INDEX idx_tasks_type ON tasks(type);
```

#### Estados de Tarea (`status`)

| Estado      | Descripción                         |
| ----------- | ----------------------------------- |
| `PLANNING`  | Generando plan con Claude           |
| `PLANNED`   | Plan generado, esperando aprobación |
| `EXECUTING` | Ejecutando con Gemini               |
| `COMPLETED` | Tarea finalizada exitosamente       |
| `FAILED`    | Tarea falló después de reintentos   |
| `ABORTED`   | Tarea cancelada por el usuario      |

#### Tipos de Tarea (`type`)

| Tipo       | Rama           | Descripción                 |
| ---------- | -------------- | --------------------------- |
| `feat`     | `feature/xxx`  | Nueva funcionalidad         |
| `fix`      | `fix/xxx`      | Corrección de bug           |
| `refactor` | `refactor/xxx` | Mejora sin cambio funcional |
| `docs`     | `docs/xxx`     | Documentación               |
| `test`     | `test/xxx`     | Tests                       |
| `chore`    | `chore/xxx`    | Configuración/dependencias  |

#### Tipos de Intent (`intent`)

| Intent          | Descripción                 |
| --------------- | --------------------------- |
| `QUERY`         | Consulta/pregunta sin tarea |
| `TASK_NEW`      | Nueva tarea de desarrollo   |
| `TASK_CONTINUE` | Continuar tarea existente   |
| `TASK_LIST`     | Listar tareas pendientes    |
| `TASK_ABORT`    | Cancelar tarea              |

---

### Tabla: `task_logs`

Historial de eventos por tarea.

```sql
CREATE TABLE task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    event TEXT NOT NULL,                              -- Tipo de evento
    message TEXT,                                     -- Mensaje descriptivo
    metadata TEXT,                                    -- JSON con datos extra
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Índices
CREATE INDEX idx_logs_task ON task_logs(task_id);
CREATE INDEX idx_logs_event ON task_logs(event);
CREATE INDEX idx_logs_created ON task_logs(created_at);
```

#### Tipos de Evento (`event`)

| Evento               | Descripción                    |
| -------------------- | ------------------------------ |
| `CREATED`            | Tarea creada                   |
| `INTENT_DETECTED`    | Intent clasificado             |
| `PLAN_GENERATED`     | Plan generado por Claude       |
| `PLAN_ADJUSTED`      | Plan modificado tras iteración |
| `PLAN_APPROVED`      | Plan aprobado por usuario      |
| `EXECUTION_STARTED`  | Inicio de ejecución            |
| `STEP_STARTED`       | Paso iniciado                  |
| `STEP_COMPLETED`     | Paso completado                |
| `STEP_FAILED`        | Paso falló                     |
| `TEST_PASSED`        | Tests pasaron                  |
| `TEST_FAILED`        | Tests fallaron                 |
| `CHECKPOINT_CREATED` | Checkpoint guardado            |
| `COMMIT_CREATED`     | Commit realizado               |
| `PUSH_COMPLETED`     | Push realizado                 |
| `COMPLETED`          | Tarea completada               |
| `FAILED`             | Tarea falló definitivamente    |
| `ABORTED`            | Tarea cancelada                |
| `ERROR`              | Error genérico                 |

---

### Tabla: `conversations`

Historial de mensajes del chat.

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,                                     -- NULL si es query sin tarea
    role TEXT NOT NULL,                               -- user, assistant, system
    content TEXT NOT NULL,                            -- Contenido del mensaje
    intent TEXT,                                      -- Intent detectado (si aplica)
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- Índices
CREATE INDEX idx_conv_task ON conversations(task_id);
CREATE INDEX idx_conv_created ON conversations(created_at);
```

---

## 📁 Archivos en Git (por tarea)

### Estructura

```
.dev-tasks/
├── README.md                    # Documentación del directorio
└── {task-id}/
    ├── plan.md                  # Plan aprobado (inmutable)
    ├── progress.md              # Progreso actual (se actualiza)
    └── state.json               # Estado técnico (se actualiza)
```

---

### `state.json`

Estado técnico parseable por el orquestador.

```json
{
  "version": "1.0",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "feat",
  "title": "Validación de stock negativo",
  "status": "EXECUTING",
  "branch": "feature/validacion-stock",
  "repo": "mi-proyecto",
  "created_at": "2026-02-03T20:00:00Z",
  "updated_at": "2026-02-03T21:45:00Z",
  "plan_hash": "abc123def456",
  "current_step": 3,
  "total_steps": 5,
  "steps": [
    {
      "id": 1,
      "title": "Crear archivo de servicio",
      "description": "Crear src/services/stock_validator.py",
      "status": "completed",
      "started_at": "2026-02-03T20:05:00Z",
      "completed_at": "2026-02-03T20:06:30Z",
      "duration_seconds": 90
    },
    {
      "id": 2,
      "title": "Implementar lógica de validación",
      "description": "Agregar función validate_stock_quantity",
      "status": "completed",
      "started_at": "2026-02-03T20:06:30Z",
      "completed_at": "2026-02-03T20:10:00Z",
      "duration_seconds": 210
    },
    {
      "id": 3,
      "title": "Crear tests unitarios",
      "description": "Crear tests/test_stock_validator.py",
      "status": "in_progress",
      "started_at": "2026-02-03T20:10:00Z",
      "substeps": {
        "done": 2,
        "total": 5,
        "items": [
          { "name": "test_valid_stock", "status": "passed" },
          { "name": "test_zero_stock", "status": "passed" },
          { "name": "test_negative_stock", "status": "pending" },
          { "name": "test_bulk_validation", "status": "pending" },
          { "name": "test_edge_cases", "status": "pending" }
        ]
      }
    },
    {
      "id": 4,
      "title": "Integrar con controller",
      "status": "pending"
    },
    {
      "id": 5,
      "title": "Tests de integración",
      "status": "pending"
    }
  ],
  "files": {
    "created": [
      "src/services/stock_validator.py",
      "tests/test_stock_validator.py"
    ],
    "modified": ["src/controllers/sales_controller.py"],
    "deleted": []
  },
  "tests": {
    "total": 12,
    "passed": 8,
    "failed": 0,
    "pending": 4,
    "last_run": "2026-02-03T21:40:00Z"
  },
  "execution": {
    "started_at": "2026-02-03T20:05:00Z",
    "elapsed_seconds": 6000,
    "retries": 0,
    "max_retries": 3
  },
  "last_error": null,
  "last_checkpoint": "2026-02-03T21:40:00Z",
  "can_continue": true
}
```

---

### `plan.md`

Plan aprobado por el usuario (no se modifica después de aprobación).

```markdown
# Plan: Validación de Stock Negativo

> **Task ID:** 550e8400-e29b-41d4-a716-446655440000  
> **Tipo:** feature  
> **Aprobado:** 2026-02-03 20:00

---

## 🎯 Objetivo

Implementar validación para prevenir valores de stock negativos en el módulo de ventas.

---

## 📋 Pasos

### Paso 1: Crear archivo de servicio

- Crear `src/services/stock_validator.py`
- Definir clase `StockValidator`

### Paso 2: Implementar lógica de validación

- Función `validate_stock_quantity(quantity: int) -> bool`
- Función `validate_stock_update(current: int, change: int) -> bool`
- Excepciones personalizadas

### Paso 3: Crear tests unitarios

- `test_valid_stock` - valores positivos
- `test_zero_stock` - valor cero
- `test_negative_stock` - valores negativos (debe fallar)
- `test_bulk_validation` - validación en lote
- `test_edge_cases` - casos límite

### Paso 4: Integrar con controller

- Modificar `src/controllers/sales_controller.py`
- Agregar validación antes de actualizar stock

### Paso 5: Tests de integración

- Verificar flujo completo de venta
- Verificar que rechaza stock negativo

---

## ✅ Criterios de Finalización

- [ ] Todos los tests pasan
- [ ] Cobertura ≥ 80%
- [ ] No hay errores de linting
- [ ] Código documentado

---

## 📁 Archivos a Modificar

| Archivo                               | Acción    |
| ------------------------------------- | --------- |
| `src/services/stock_validator.py`     | Crear     |
| `tests/test_stock_validator.py`       | Crear     |
| `src/controllers/sales_controller.py` | Modificar |
```

---

### `progress.md`

Progreso actual con instrucciones para continuar manualmente.

````markdown
# 📊 Progreso: Validación de Stock Negativo

> **Rama:** `feature/validacion-stock`  
> **Estado:** 🔄 En Progreso (60% completado)  
> **Actualizado:** 2026-02-03 21:45

---

## ✅ Completado

- [x] **Paso 1:** Crear servicio de validación
  - Archivo: `src/services/stock_validator.py`
  - Duración: 1m 30s

- [x] **Paso 2:** Implementar lógica de validación
  - Funciones: `validate_stock_quantity`, `validate_stock_update`
  - Duración: 3m 30s

- [~] **Paso 3:** Tests unitarios (en progreso)
  - ✅ `test_valid_stock` - PASSED
  - ✅ `test_zero_stock` - PASSED
  - ⏳ `test_negative_stock` - PENDING
  - ⏳ `test_bulk_validation` - PENDING
  - ⏳ `test_edge_cases` - PENDING

---

## ⏳ Pendiente

- [ ] **Paso 4:** Integrar con controller de ventas
- [ ] **Paso 5:** Tests de integración

---

## 📈 Tests

| Estado     | Cantidad |
| ---------- | -------- |
| ✅ Passed  | 8        |
| ❌ Failed  | 0        |
| ⏳ Pending | 4        |
| **Total**  | 12       |

---

## 🔧 Continuar Manualmente

Si deseas continuar este trabajo en tu PC:

### 1. Obtener el código

```bash
git fetch origin
git checkout feature/validacion-stock
git pull origin feature/validacion-stock
```
````

### 2. Estado actual

| Archivo                               | Estado       | Notas          |
| ------------------------------------- | ------------ | -------------- |
| `src/services/stock_validator.py`     | ✅ Completo  | Listo          |
| `tests/test_stock_validator.py`       | 🔄 Parcial   | Faltan 3 tests |
| `src/controllers/sales_controller.py` | ⏳ Pendiente | No modificado  |

### 3. Siguiente acción

Completar los tests faltantes en `tests/test_stock_validator.py`:

```python
# Línea ~45 - Implementar:

def test_negative_stock():
    """Verificar que rechaza stock negativo."""
    validator = StockValidator()
    with pytest.raises(InvalidStockError):
        validator.validate_stock_quantity(-5)

def test_bulk_validation():
    """Verificar validación en lote."""
    # TODO: Implementar
    pass

def test_edge_cases():
    """Verificar casos límite."""
    # TODO: Implementar
    pass
```

### 4. Verificar

```bash
# Correr tests
pytest tests/test_stock_validator.py -v

# Verificar cobertura
pytest --cov=src/services/stock_validator tests/
```

### 5. Completar tarea

```bash
git add .
git commit -m "feat: completar tests de validación de stock"
git push origin feature/validacion-stock
```

---

## 🕐 Timeline

| Hora  | Evento            |
| ----- | ----------------- |
| 20:00 | Tarea creada      |
| 20:00 | Plan aprobado     |
| 20:05 | Inicio ejecución  |
| 20:06 | Paso 1 completado |
| 20:10 | Paso 2 completado |
| 20:10 | Paso 3 iniciado   |
| 21:40 | Último checkpoint |
| 21:45 | Progreso guardado |

```

---

## 📁 Archivos en VM (Logs)

### Estructura

```

/opt/dev-orchestrator/
├── data/
│ └── orchestrator.db # SQLite database
└── logs/
└── {task-id}/
├── execution.log # Log detallado
├── errors.log # Errores capturados
└── checkpoints/
├── cp-001.json # Checkpoint 1
├── cp-002.json # Checkpoint 2
└── ...

````

### Checkpoint JSON

```json
{
  "checkpoint_id": "cp-003",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-02-03T21:40:00Z",
  "state_snapshot": {
    "current_step": 3,
    "files_modified": ["src/services/stock_validator.py"],
    "tests_passed": 8,
    "tests_failed": 0
  },
  "git_status": {
    "branch": "feature/validacion-stock",
    "last_commit": "abc123",
    "uncommitted_changes": ["tests/test_stock_validator.py"]
  }
}
````

---

## 📊 Diagrama de Relaciones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODELO DE DATOS                                      │
└─────────────────────────────────────────────────────────────────────────────┘

                              SQLite (VM)
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │   ┌──────────────┐         ┌──────────────┐                │
  │   │    tasks     │ ◄─────► │  task_logs   │                │
  │   │              │   1:N   │              │                │
  │   │  - id (PK)   │         │  - task_id   │                │
  │   │  - status    │         │  - event     │                │
  │   │  - type      │         │  - message   │                │
  │   │  - repo      │         └──────────────┘                │
  │   │  - branch    │                                         │
  │   └──────┬───────┘                                         │
  │          │                                                  │
  │          │ 1:N    ┌──────────────┐                         │
  │          └──────► │conversations │                         │
  │                   │              │                         │
  │                   │  - task_id   │                         │
  │                   │  - role      │                         │
  │                   │  - content   │                         │
  │                   └──────────────┘                         │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘

                              Git (Rama)
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │   .dev-tasks/{task-id}/                                    │
  │   ├── plan.md          (inmutable tras aprobación)         │
  │   ├── progress.md      (actualizado periódicamente)        │
  │   └── state.json       (estado técnico parseable)          │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘

                              VM (Local)
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │   /opt/dev-orchestrator/logs/{task-id}/                    │
  │   ├── execution.log    (log detallado)                     │
  │   ├── errors.log       (errores)                           │
  │   └── checkpoints/     (snapshots para recovery)           │
  │       ├── cp-001.json                                      │
  │       └── cp-002.json                                      │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
```

---

## 📏 Estimaciones de Volumen

| Entidad          | Año 1   | Tamaño Promedio | Total Estimado |
| ---------------- | ------- | --------------- | -------------- |
| Tasks            | ~1,000  | 1 KB            | ~1 MB          |
| TaskLogs         | ~25,000 | 0.5 KB          | ~12 MB         |
| Conversations    | ~10,000 | 1 KB            | ~10 MB         |
| **Total SQLite** | -       | -               | **~25 MB**     |

**Conclusión:** SQLite es más que suficiente para este volumen.

---

## 🔧 Mantenimiento

### Limpieza de Checkpoints

```bash
# Eliminar checkpoints de tareas completadas (>7 días)
find /opt/dev-orchestrator/logs/*/checkpoints -mtime +7 -delete
```

### Backup de SQLite

```bash
# Backup manual
cp /opt/dev-orchestrator/data/orchestrator.db /backup/orchestrator_$(date +%Y%m%d).db

# Restaurar
cp /backup/orchestrator_YYYYMMDD.db /opt/dev-orchestrator/data/orchestrator.db
```

### Vacuuming

```sql
-- Ejecutar periódicamente para optimizar
VACUUM;
```

---

_Documento generado por AI Flow - Phase 2: Data Architecture_
