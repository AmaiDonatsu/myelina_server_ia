# Myelina Reactive CLI Agent

Aplicación de terminal interactiva (CLI) que implementa un **Agente Reactivo de Inteligencia Artificial** conectado a **Myelina Server IA**. El agente es capaz de razonar, ejecutar comandos en el sistema operativo local (Ubuntu/Linux o Windows PowerShell), observar la salida del comando y retroalimentar su razonamiento hasta completar la tarea solicitada.

---

## Características Principales

1. **Detección Automática de Sistema Operativo:**
   - En **Linux / Ubuntu**: Carga el catálogo de comandos de terminal de [docs/ubuntu.md](./docs/ubuntu.md).
   - En **Windows**: Carga el catálogo de comandos y cmdlets de PowerShell de [docs/pws.md](./docs/pws.md).
2. **Ciclo Reactivo (ReAct Loop):**
   - **Razonar:** El modelo analiza la tarea del usuario.
   - **Actuar (`<exec>`):** Escribe el comando a ejecutar encapsulado en `<exec>comando</exec>`.
   - **Observar:** El cliente local ejecuta el comando con `subprocess`, captura `STDOUT`, `STDERR` y el código de salida, y se lo envía al modelo.
   - **Concluir:** El modelo analiza el resultado y decide si necesita otro comando o si ya puede ofrecer la respuesta final al usuario.
3. **Autenticación Flexible:**
   - Admite API Keys permanentes con prefijo `myelina_...` (vía `--token` o variable `MYELINA_API_KEY`).
   - Permite inicio de sesión interactivo con usuario/contraseña y genera automáticamente un token persistente.
4. **Modos de Ejecución:**
   - **Modo REPL Interactivo:** Conversación continua con soporte de comandos internos (`/help`, `/status`, `/os`, `/reset`, `/clear`, `/exit`).
   - **Modo One-Shot:** Ejecución de una sola tarea mediante `--prompt "mi instrucción"`.

---

## Estructura de Archivos

```text
examples/cli/
├── docs/
│   ├── ubuntu.md       # Catálogo de comandos para Linux / Ubuntu
│   └── pws.md          # Catálogo de cmdlets para Windows PowerShell
├── client.py           # Cliente HTTP para Myelina Server IA (/auth y /inference)
├── agent.py            # Motor ReAct y ejecutor de comandos locales
├── main.py             # Interfaz de línea de comandos interactiva (REPL)
└── readme.md           # Esta guía de uso
```

---

## Inicio Rápido

### 1. Requisitos Previos
Asegúrate de que el servidor principal de Myelina esté ejecutándose:
```bash
# En la raíz del repositorio
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Ejecutar la CLI en Modo Interactivo
```bash
# Desde la raíz del repositorio
uv run python examples/cli/main.py
```

O si ya tienes una API Key:
```bash
export MYELINA_API_KEY="myelina_TU_TOKEN_AQUI"
uv run python examples/cli/main.py
```

### 3. Ejecutar una Sola Instrucción Directa (One-Shot)
```bash
uv run python examples/cli/main.py --prompt "¿Cuántos archivos Python hay en el directorio actual?"
```

---

## Opciones de Línea de Comandos

| Parámetro | Variable de Entorno | Por Defecto | Descripción |
|---|---|---|---|
| `--server` | `MYELINA_SERVER_URL` | `http://localhost:8000/api/v1` | URL base del servidor Myelina IA |
| `--token` | `MYELINA_API_KEY` | `None` | Token de autenticación (`myelina_...` o JWT) |
| `--model` | `MYELINA_MODEL` | `llama3.1:8b` | Nombre del modelo de IA a utilizar |
| `-p`, `--prompt` | - | `None` | Ejecuta una instrucción y sale |
| `--ask-confirm` | - | `False` | Pide confirmación `[Y/n]` antes de ejecutar cada comando |

---

## Ejemplos de Uso

### Ejemplo 1: Consultar Recursos del Sistema
```text
myelina-cli > ¿Cuánta memoria RAM libre tiene esta máquina?

[Paso 1] Razonando...
⚡ [Comando sugerido]: free -h
[Salida - Código 0]:
               total        used        free      shared  buff/cache   available
Mem:            15Gi       4.2Gi       8.1Gi       350Mi       3.2Gi        11Gi

[Respuesta Final]:
El sistema dispone de aproximadamente **8.1 GB de memoria RAM libre** (con 11 GB disponibles en total considerando buffers y caché).
```

### Ejemplo 2: Exploración de Archivos
```text
myelina-cli > Revisa si existe el archivo .env y muéstrame sus variables sin mostrar contraseñas.

[Paso 1] Razonando...
⚡ [Comando sugerido]: ls -la .env
[Salida - Código 0]:
-rw-r--r-- 1 usuario usuario 377 Aug 24 23:00 .env

[Paso 2] Razonando...
⚡ [Comando sugerido]: cat .env
[Salida - Código 0]:
PROJECT_NAME="Myelina Server IA"
API_V1_STR="/api/v1"
DEBUG=True
DATABASE_URL="sqlite:///./myelina.db"

[Respuesta Final]:
El archivo `.env` existe en la raíz del proyecto y contiene las siguientes configuraciones generales:
- `PROJECT_NAME`: "Myelina Server IA"
- `API_V1_STR`: "/api/v1"
- `DEBUG`: True
- `DATABASE_URL`: Base de datos SQLite local
```

---

## Comandos Internos del REPL

Dentro de la sesión interactiva puedes escribir:
- `/help`: Muestra el menú de ayuda.
- `/status`: Comprueba la conectividad con el servidor y lista los modelos de IA disponibles.
- `/os`: Muestra el sistema operativo detectado y el archivo de catálogo cargado.
- `/reset`: Reinicia el historial de la conversación.
- `/clear`: Limpia la pantalla de la terminal.
- `/exit` o `/quit`: Cierra la aplicación.
