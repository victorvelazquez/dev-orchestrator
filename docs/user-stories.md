# User Stories

## Épicas

```
┌─────────────────────────────────────────────────────────────────┐
│                         ÉPICAS                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  E1: Gestión de Tareas          E2: Ejecución de Código         │
│  ┌───────────────────┐          ┌───────────────────┐           │
│  │ • Crear tarea     │          │ • Generar plan    │           │
│  │ • Listar tareas   │          │ • Ejecutar pasos  │           │
│  │ • Cancelar tarea  │          │ • Manejar errores │           │
│  │ • Ver estado      │          │ • Checkpoints     │           │
│  └───────────────────┘          └───────────────────┘           │
│                                                                  │
│  E3: Integración Git            E4: Seguridad                   │
│  ┌───────────────────┐          ┌───────────────────┐           │
│  │ • Clonar repos    │          │ • Autenticación   │           │
│  │ • Crear branches  │          │ • Sandbox         │           │
│  │ • Commits auto    │          │ • Branches prot.  │           │
│  │ • Crear PRs       │          │ • Secrets         │           │
│  └───────────────────┘          └───────────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## E1: Gestión de Tareas

### US-001: Crear Nueva Tarea

**Como** usuario autorizado  
**Quiero** crear una tarea de desarrollo describiendo lo que necesito  
**Para** que el sistema ejecute la tarea automáticamente

#### Criterios de Aceptación

```gherkin
Escenario: Crear tarea con información completa
  Dado que soy un usuario autorizado
  Cuando envío "/task Agregar validación email https://github.com/org/repo"
  Entonces el sistema clasifica mi intent como TASK_NEW
  Y extrae el repositorio y la descripción
  Y crea una tarea en estado PENDING
  Y me muestra un plan de ejecución para aprobar

Escenario: Crear tarea con información incompleta
  Dado que soy un usuario autorizado
  Cuando envío "/task agregar tests"
  Entonces el sistema detecta que falta el repositorio
  Y me pregunta "¿En qué repositorio quieres que trabaje?"
  Y espera mi respuesta antes de continuar

Escenario: Usuario no autorizado intenta crear tarea
  Dado que NO soy un usuario autorizado
  Cuando envío "/task cualquier cosa"
  Entonces recibo el mensaje "⛔ No tienes autorización"
  Y la tarea NO se crea
```

#### Notas Técnicas

- Usar `IntentClassifier` para detectar TASK_NEW
- Máximo 10 rondas de clarificación
- Guardar en SQLite inmediatamente

---

### US-002: Aprobar Plan de Ejecución

**Como** usuario  
**Quiero** revisar y aprobar el plan generado por la IA  
**Para** asegurarme de que ejecutará lo que necesito

#### Criterios de Aceptación

```gherkin
Escenario: Aprobar plan
  Dado que tengo una tarea pendiente de aprobación
  Y veo el plan con objetivo, archivos y pasos
  Cuando presiono el botón "✅ Aprobar"
  Entonces la tarea cambia a estado APPROVED
  Y comienza la ejecución automáticamente
  Y recibo mensaje "✅ Plan aprobado. Iniciando ejecución..."

Escenario: Rechazar plan
  Dado que tengo una tarea pendiente de aprobación
  Cuando presiono el botón "❌ Rechazar"
  Entonces la tarea cambia a estado ABORTED
  Y recibo mensaje "❌ Plan rechazado. La tarea ha sido cancelada."

Escenario: Solicitar modificación
  Dado que tengo una tarea pendiente de aprobación
  Cuando presiono el botón "✏️ Modificar"
  Entonces recibo mensaje "Por favor, describe qué cambios quieres"
  Y puedo enviar mis modificaciones
  Y se genera un nuevo plan
```

#### Notas Técnicas

- Usar InlineKeyboardMarkup de Telegram
- Callback data: `approve:{task_id}`, `reject:{task_id}`, `modify:{task_id}`

---

### US-003: Listar Mis Tareas

**Como** usuario  
**Quiero** ver una lista de mis tareas  
**Para** conocer el estado de cada una

#### Criterios de Aceptación

```gherkin
Escenario: Listar tareas existentes
  Dado que tengo 3 tareas creadas
  Cuando envío "/list"
  Entonces veo una lista con:
    | ID | Descripción (truncada) | Estado | Fecha |
  Y cada tarea tiene un emoji indicando su estado
  Y están ordenadas por fecha (más reciente primero)

Escenario: Sin tareas
  Dado que no tengo tareas creadas
  Cuando envío "/list"
  Entonces veo el mensaje "📭 No tienes tareas registradas."
```

#### Notas Técnicas

- Limitar a últimas 10 tareas
- Emojis: ⏳ pending, 🔍 pending_approval, 🔄 in_progress, ✅ completed, ❌ failed, 🚫 aborted

---

### US-004: Ver Estado de Tarea Activa

**Como** usuario  
**Quiero** ver el progreso de mi tarea en ejecución  
**Para** saber en qué paso está

#### Criterios de Aceptación

```gherkin
Escenario: Ver tarea en progreso
  Dado que tengo una tarea en ejecución en paso 3 de 5
  Cuando envío "/status"
  Entonces veo:
    """
    🔄 Tarea en progreso
    ID: task-abc123
    Descripción: Agregar validación email
    Progreso: 3/5 pasos completados
    Paso actual: Implementando tests
    Tiempo: 5 minutos
    """

Escenario: Sin tarea activa
  Dado que no tengo tareas en ejecución
  Cuando envío "/status"
  Entonces veo "Sin tareas activas."
```

---

### US-005: Cancelar Tarea

**Como** usuario  
**Quiero** cancelar una tarea en curso  
**Para** detener la ejecución si ya no la necesito

#### Criterios de Aceptación

```gherkin
Escenario: Cancelar tarea con trabajo parcial
  Dado que tengo una tarea en ejecución con 2 pasos completados
  Cuando envío "/abort"
  Entonces la ejecución se detiene
  Y se hace commit del trabajo parcial
  Y la tarea cambia a estado ABORTED
  Y recibo mensaje con link al commit parcial

Escenario: Cancelar tarea sin trabajo
  Dado que tengo una tarea pendiente de aprobación
  Cuando envío "/abort"
  Entonces la tarea cambia a estado ABORTED
  Y recibo mensaje "Tarea cancelada."
  Y NO se crea ningún commit
```

---

## E2: Ejecución de Código

### US-006: Generar Plan de Ejecución

**Como** sistema  
**Quiero** generar un plan detallado usando Claude  
**Para** tener pasos claros y ejecutables

#### Criterios de Aceptación

```gherkin
Escenario: Plan generado correctamente
  Dado una descripción de tarea válida
  Cuando el PlanGenerator procesa la solicitud
  Entonces produce un JSON con:
    | Campo | Descripción |
    | objetivo | Descripción clara del objetivo |
    | archivos | Lista de archivos a modificar |
    | pasos | Array de pasos atómicos |
    | estimacion | Tiempo estimado |
  Y cada paso tiene: número, descripción, archivos, acción

Escenario: Descripción muy vaga
  Dado una descripción ambigua como "mejora el código"
  Cuando el PlanGenerator procesa la solicitud
  Entonces solicita más información
  Y NO genera un plan incompleto
```

#### Notas Técnicas

- Modelo: Claude 3.5/4 Sonnet
- Max tokens: 2000
- Temperature: 0.3 (más determinístico)

---

### US-007: Ejecutar Pasos del Plan

**Como** sistema  
**Quiero** ejecutar cada paso del plan usando Gemini  
**Para** implementar los cambios de código

#### Criterios de Aceptación

```gherkin
Escenario: Ejecutar paso exitosamente
  Dado un paso "Crear función validate_email()"
  Cuando el Executor procesa el paso
  Entonces genera el código necesario
  Y escribe el archivo en el workspace
  Y reporta success=true
  Y avanza al siguiente paso

Escenario: Paso falla
  Dado un paso que no puede completarse
  Cuando el Executor encuentra un error
  Entonces reporta success=false con error
  Y detiene la ejecución
  Y hace commit del trabajo completado hasta ahora
```

#### Notas Técnicas

- Modelo: Gemini 2.0 Flash
- Ejecutar en Docker sandbox
- Guardar output de cada paso

---

### US-008: Crear Checkpoints

**Como** sistema  
**Quiero** crear checkpoints periódicos durante la ejecución  
**Para** poder recuperar el estado si hay fallos

#### Criterios de Aceptación

```gherkin
Escenario: Checkpoint automático
  Dado una tarea en ejecución
  Cuando pasan 5 minutos desde el último checkpoint
  Entonces se guarda el estado actual:
    - Paso actual
    - Archivos modificados
    - Timestamp
  Y se escribe en .dev-tasks/checkpoint.json

Escenario: Recuperar de checkpoint
  Dado una tarea que falló con checkpoint guardado
  Cuando el usuario solicita continuar
  Entonces se carga el checkpoint
  Y se resume desde el paso guardado
  Y NO se repiten pasos completados
```

---

### US-009: Notificaciones de Progreso

**Como** usuario  
**Quiero** recibir notificaciones durante la ejecución  
**Para** saber que el sistema está trabajando

#### Criterios de Aceptación

```gherkin
Escenario: Notificación por paso
  Dado una tarea en ejecución
  Cuando se completa un paso
  Entonces recibo mensaje:
    "📍 Paso 2/5: Implementando validate_email() ✅"

Escenario: Notificación de finalización
  Dado una tarea que completa todos los pasos
  Cuando termina la ejecución
  Entonces recibo mensaje:
    """
    ✅ Tarea completada!

    📊 Resumen:
    - 5 pasos ejecutados
    - 3 archivos modificados
    - Tiempo: 12 minutos

    🔗 PR: https://github.com/org/repo/pull/42
    """
```

---

## E3: Integración Git

### US-010: Clonar Repositorio

**Como** sistema  
**Quiero** clonar el repositorio del usuario  
**Para** tener el código fuente disponible

#### Criterios de Aceptación

```gherkin
Escenario: Clonar repo público
  Dado una URL de repo público válida
  Cuando el GitManager clona el repositorio
  Entonces el código está disponible en workspace/{task_id}/{repo_name}
  Y se puede hacer git operations

Escenario: Clonar repo privado
  Dado una URL de repo privado y token válido
  Cuando el GitManager clona el repositorio
  Entonces usa el token para autenticación
  Y el código está disponible

Escenario: URL inválida
  Dado una URL que no es un repo GitHub
  Cuando el GitManager intenta clonar
  Entonces lanza error "Invalid GitHub URL"
```

---

### US-011: Crear Branch de Trabajo

**Como** sistema  
**Quiero** crear un branch para los cambios  
**Para** no modificar el branch principal

#### Criterios de Aceptación

```gherkin
Escenario: Crear branch desde main
  Dado un repositorio clonado
  Cuando creo un branch "feature/task-abc123"
  Entonces el branch se crea desde main (o master)
  Y se hace checkout automáticamente
  Y los commits van a este branch

Escenario: Nombre de branch sigue convención
  Dado una tarea tipo FEATURE
  Cuando se genera el nombre del branch
  Entonces sigue el formato: {type}/{task-id}-{slug}
  Ejemplo: feature/task-abc123-add-email-validation
```

---

### US-012: Commit Automático

**Como** sistema  
**Quiero** hacer commits automáticos de los cambios  
**Para** guardar el progreso en Git

#### Criterios de Aceptación

```gherkin
Escenario: Commit al completar tarea
  Dado una tarea completada con archivos modificados
  Cuando hago commit
  Entonces el mensaje sigue conventional commits:
    "feat(user): add email validation

    - Add validate_email() function
    - Integrate with create_user()
    - Add unit tests

    Task: task-abc123"

Escenario: Commit parcial en error
  Dado una tarea que falla en paso 3 de 5
  Cuando hago commit parcial
  Entonces el mensaje indica WIP:
    "wip: partial implementation of email validation

    Completed steps: 1, 2
    Failed at: step 3

    Task: task-abc123"
```

---

### US-013: Crear Pull Request

**Como** sistema  
**Quiero** crear un PR con los cambios  
**Para** que el usuario pueda revisar y mergear

#### Criterios de Aceptación

```gherkin
Escenario: PR creado exitosamente
  Dado cambios en branch feature/task-abc123
  Cuando creo el Pull Request
  Entonces el PR tiene:
    - Título: feat(user): add email validation
    - Body: Plan ejecutado, archivos modificados, link a tarea
    - Base: main
    - Head: feature/task-abc123
  Y recibo la URL del PR

Escenario: PR con trabajo parcial
  Dado una tarea abortada con trabajo parcial
  Cuando creo el PR
  Entonces el título indica [WIP]
  Y el body indica que está incompleto
  Y lista los pasos completados vs pendientes
```

---

## E4: Seguridad

### US-014: Autenticación por Whitelist

**Como** administrador  
**Quiero** definir qué usuarios pueden usar el bot  
**Para** controlar el acceso al sistema

#### Criterios de Aceptación

```gherkin
Escenario: Usuario autorizado
  Dado TELEGRAM_ALLOWED_USERS="123,456,789"
  Y mi user_id es 456
  Cuando envío cualquier comando
  Entonces el bot responde normalmente

Escenario: Usuario no autorizado
  Dado TELEGRAM_ALLOWED_USERS="123,456,789"
  Y mi user_id es 999
  Cuando envío cualquier comando
  Entonces recibo "⛔ No tienes autorización"
  Y se loggea el intento

Escenario: Lista vacía bloquea todos
  Dado TELEGRAM_ALLOWED_USERS=""
  Cuando cualquier usuario envía comando
  Entonces todos son rechazados
```

---

### US-015: Sandbox de Ejecución

**Como** sistema  
**Quiero** ejecutar código en un contenedor aislado  
**Para** proteger el sistema host

#### Criterios de Aceptación

```gherkin
Escenario: Ejecutar en sandbox
  Dado un paso que requiere ejecutar código
  Cuando el Executor procesa el paso
  Entonces el código se ejecuta en contenedor Docker
  Y el contenedor tiene acceso limitado:
    - Solo al workspace de la tarea
    - Sin acceso a red (opcional)
    - Timeout de 5 minutos por paso

Escenario: Comando no permitido
  Dado un paso que intenta ejecutar "rm -rf /"
  Cuando el Executor valida el comando
  Entonces rechaza la ejecución
  Y loggea intento sospechoso
```

---

### US-016: Proteger Branches Principales

**Como** sistema  
**Quiero** prevenir cambios directos a main/master  
**Para** proteger el código de producción

#### Criterios de Aceptación

```gherkin
Escenario: Bloquear push a main
  Dado que estoy en branch "main"
  Cuando intento hacer commit o push
  Entonces recibo error "Cannot commit to protected branch: main"
  Y la operación se cancela

Escenario: Branches protegidos configurables
  Dado PROTECTED_BRANCHES="main,master,develop,production"
  Cuando verifico si "develop" está protegido
  Entonces retorna True

Escenario: Branch de feature permitido
  Dado que estoy en branch "feature/task-abc123"
  Cuando hago commit y push
  Entonces la operación es exitosa
```

---

### US-017: Gestión Segura de Secrets

**Como** administrador  
**Quiero** que los secrets se manejen de forma segura  
**Para** proteger credenciales

#### Criterios de Aceptación

```gherkin
Escenario: Secrets en .env
  Dado un archivo .env con API keys
  Cuando el sistema inicia
  Entonces carga las variables de entorno
  Y NO las imprime en logs
  Y .env está en .gitignore

Escenario: Logs sin secrets
  Dado una operación que usa ANTHROPIC_API_KEY
  Cuando se loggea la operación
  Entonces el log muestra "ANTHROPIC_API_KEY=***"
  Y NO muestra el valor real

Escenario: Error si falta secret requerido
  Dado que TELEGRAM_BOT_TOKEN no está configurado
  Cuando el sistema intenta iniciar
  Entonces falla con mensaje claro
  Y NO expone información sensible
```

---

## Priorización

### Must Have (P0)

- US-001: Crear Nueva Tarea
- US-002: Aprobar Plan
- US-006: Generar Plan
- US-007: Ejecutar Pasos
- US-010: Clonar Repositorio
- US-011: Crear Branch
- US-012: Commit Automático
- US-014: Autenticación Whitelist

### Should Have (P1)

- US-003: Listar Tareas
- US-004: Ver Estado
- US-005: Cancelar Tarea
- US-008: Checkpoints
- US-009: Notificaciones
- US-013: Crear PR
- US-015: Sandbox
- US-016: Branches Protegidos

### Could Have (P2)

- US-017: Gestión Secrets (refinamiento)
- Múltiples tareas simultáneas
- Historial de conversación
- Estadísticas de uso

---

## Matriz de Trazabilidad

| User Story | Módulo Principal                                      | Tests Requeridos                     |
| ---------- | ----------------------------------------------------- | ------------------------------------ |
| US-001     | `chat/telegram_bot.py`, `agents/intent_classifier.py` | `test_telegram.py`, `test_intent.py` |
| US-002     | `chat/telegram_bot.py`, `core/orchestrator.py`        | `test_approval.py`                   |
| US-003     | `models/database.py`, `chat/telegram_bot.py`          | `test_list.py`                       |
| US-004     | `core/orchestrator.py`, `chat/telegram_bot.py`        | `test_status.py`                     |
| US-005     | `core/orchestrator.py`, `agents/executor.py`          | `test_abort.py`                      |
| US-006     | `agents/plan_generator.py`                            | `test_plan_generator.py`             |
| US-007     | `agents/executor.py`                                  | `test_executor.py`                   |
| US-008     | `core/checkpoint.py`                                  | `test_checkpoint.py`                 |
| US-009     | `chat/notifications.py`                               | `test_notifications.py`              |
| US-010     | `git/github_manager.py`                               | `test_git_clone.py`                  |
| US-011     | `git/github_manager.py`                               | `test_git_branch.py`                 |
| US-012     | `git/github_manager.py`                               | `test_git_commit.py`                 |
| US-013     | `git/github_manager.py`                               | `test_git_pr.py`                     |
| US-014     | `chat/telegram_bot.py`                                | `test_auth.py`                       |
| US-015     | `sandbox/docker_runner.py`                            | `test_sandbox.py`                    |
| US-016     | `git/github_manager.py`                               | `test_protected.py`                  |
| US-017     | `core/config.py`                                      | `test_config.py`                     |
