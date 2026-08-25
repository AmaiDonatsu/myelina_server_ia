# Guía de Integración y Uso del Cliente — Myelina Server IA

Bienvenido a la guía de integración para desarrolladores de **Myelina Server IA**. Este documento describe cómo consumir la API desde cualquier aplicación cliente (Web, Móvil, Scripts backend, etc.), cómo autenticar peticiones, gestionar Tokens/API Keys y cómo estructurar las llamadas de inferencia para modelos de Inteligencia Artificial (RunPod / Ollama).

---

## Tabla de Contenido
1. [Visión General y URLs Base](#-visión-general-y-urls-base)
2. [Estrategias de Autenticación](#-estrategias-de-autenticación)
   - [Opción A: API Keys Persistentes (`myelina_...`) — Recomendado](#opción-a-api-keys-persistentes-myelina_-recomendado-para-aplicaciones)
   - [Opción B: Sesión Temporal con JWT](#opción-b-sesión-temporal-con-jwt)
3. [Endpoints de Inferencia de IA](#-endpoints-de-inferencia-de-ia)
   - [Chat con Historial (`POST /api/v1/inference/chat`)](#1-chat-con-historial-post-apiv1inferencechat)
   - [Generación Simple de Texto (`POST /api/v1/inference/generate`)](#2-generación-simple-de-texto-post-apiv1inferencegenerate)
   - [Modelos Disponibles (`GET /api/v1/inference/models`)](#3-modelos-disponibles-get-apiv1inferencemodels)
   - [Estado del Servidor (`GET /api/v1/inference/status`)](#4-estado-del-servidor-get-apiv1inferencestatus)
4. [Ejemplos de Clientes Listos para Usar](#-ejemplos-de-clientes-listos-para-usar)
   - [JavaScript / TypeScript (Fetch / Browser / Node.js)](#ejemplo-en-javascript--typescript-fetch)
   - [Python (httpx / requests)](#ejemplo-en-python-httpx)
   - [cURL / Bash](#ejemplo-en-curl--bash)
5. [Gestión de Errores y Buenas Prácticas](#-gestión-de-errores-y-buenas-prácticas)

---

## Visión General y URLs Base

- **URL Base de la API:** `http://localhost:8000/api/v1` *(o la URL de tu servidor en producción)*
- **Documentación Interactiva (Swagger UI):** `http://localhost:8000/api/v1/docs`
- **Documentación OpenAPI (ReDoc):** `http://localhost:8000/api/v1/redoc`

Todas las respuestas y peticiones utilizan el formato estándar `application/json` salvo indicación contraria.

---

##  Estrategias de Autenticación

Todas las rutas de inferencia y datos privados requieren autenticación mediante la cabecera HTTP estándar:
```http
Authorization: Bearer <TOKEN>
```

Tienes dos formas de autenticar tu cliente:

### Opción A: API Keys Persistentes (`myelina_...`) *(Recomendado para Aplicaciones)*
Ideal para servidores backend, microservicios, bots o clientes persistentes. No caducan a menos que configures fecha de expiración o las revoques manualmente.

#### 1. Crear un Token de API
Primero, con tu usuario registrado e iniciado sesión (vía JWT):
- **Endpoint:** `POST /api/v1/auth/tokens`
- **Headers:** `Authorization: Bearer <JWT_TEMPORAL>`
- **Body:**
```json
{
  "label": "mi_aplicacion_web",
  "expires_in_days": 60,
  "scopes": "all"
}
```
- **Respuesta (201 Created):**
```json
{
  "id": 1,
  "label": "mi_aplicacion_web",
  "token": "myelina_aB3_9xKl80QzM...",
  "prefix": "myelina_aB3...",
  "scopes": "all",
  "revoked": false,
  "created_at": "2026-08-24T22:00:00",
  "expires_at": "2026-10-23T22:00:00",
  "message": "Token generado con éxito. Cópialo y guárdalo en un lugar seguro; no podrás volver a verlo."
}
```
> **Importante:** La clave completa en texto plano (`token`) solo se devuelve una vez al crearla. En la base de datos se guarda únicamente el hash criptográfico SHA-256.

#### 2. Usar tu API Key en tu Aplicación
A partir de este momento, tu cliente solo necesita enviar la API Key en el header `Authorization`:
```http
Authorization: Bearer myelina_aB3_9xKl80QzM...
```

---

### Opción B: Sesión Temporal con JWT
Ideal para login interactivo de usuarios en interfaces web o móviles.

#### 1. Registro de Usuario (Sign Up)
- **Endpoint:** `POST /api/v1/auth/register`
- **Body:**
```json
{
  "username": "juan_perez",
  "email": "juan@example.com",
  "password": "miPasswordSegura123",
  "role": "user"
}
```

#### 2. Inicio de Sesión (Login)
- **Endpoint:** `POST /api/v1/auth/login/json`
- **Body:**
```json
{
  "username": "juan_perez",
  "password": "miPasswordSegura123"
}
```
- **Respuesta (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer"
}
```

---

## Endpoints de Inferencia de IA

### 1. Chat con Historial (`POST /api/v1/inference/chat`)

Permite enviar un hilo de conversación completo al modelo (compatible con plantillas de Ollama / RunPod) y recibir la respuesta contextualizada.

#### Roles Admitidos en los Mensajes
El campo `role` acepta tanto términos en inglés como sinónimos en español:
- `system` o `sistema`: Instrucciones y directivas generales del asistente.
- `user` o `usuario`: Mensajes o preguntas enviadas por el usuario final.
- `assistant`, `asistente`, `agent` o `model`: Respuestas anteriores generadas por la IA.

#### Estructura de la Petición (Request Body)
```json
{
  "messages": [
    {
      "role": "system",
      "content": "Eres un asistente de IA experto en desarrollo de software, conciso y amable."
    },
    {
      "role": "user",
      "content": "¿Cuáles son las diferencias principales entre FastAPI y Flask?"
    }
  ],
  "model": "llama3.1:8b",
  "temperature": 0.7,
  "top_p": 0.9,
  "stream": false
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `messages` | Array de Objetos | **Sí** | Lista ordenada de mensajes con `role` y `content`. |
| `model` | String | No | Nombre del modelo a invocar (por defecto: `llama3.1:8b`). |
| `temperature` | Float (0.0 - 2.0) | No | Control de creatividad/aleatoriedad (por defecto: `0.7`). |
| `top_p` | Float (0.0 - 1.0) | No | Muestreo por núcleo (por defecto: `0.9`). |
| `stream` | Booleano | No | `false` para respuesta JSON única, `true` para Server-Sent Events (SSE). |

#### Estructura de la Respuesta (Response Body)
El servidor responde con un objeto JSON enriquecido con el texto generado y metadatos de ejecución:
```json
{
  "model": "llama3.1:8b",
  "content": "FastAPI y Flask son frameworks populares de Python, pero tienen diferencias clave:\n1. **Rendimiento y Asincronía:** FastAPI está construido sobre ASGI (Starlette) con soporte nativo de `async/await`...\n2. **Validación:** FastAPI incluye Pydantic nativo...",
  "date": "2026-08-24 23:30:00 UTC",
  "message": {
    "role": "assistant",
    "content": "FastAPI y Flask son frameworks populares de Python, pero tienen diferencias clave:\n1. **Rendimiento y Asincronía:** FastAPI está construido sobre ASGI (Starlette) con soporte nativo de `async/await`...\n2. **Validación:** FastAPI incluye Pydantic nativo..."
  },
  "done": true,
  "total_duration": 4321098765,
  "prompt_eval_count": 38,
  "eval_count": 215
}
```

- `content`: Texto principal generado por la IA listo para mostrar en la interfaz.
- `date`: Fecha y hora de generación.
- `model`: Modelo de IA que procesó la respuesta.
- `message`: Objeto de mensaje estructurado con `{ "role": "assistant", "content": "..." }`.
- `total_duration`: Tiempo total de procesamiento en nanosegundos (RunPod/Ollama).
- `eval_count`: Cantidad de tokens generados.

---

### 2. Generación Simple de Texto (`POST /api/v1/inference/generate`)

Para instrucciones directas o prompts aislados sin necesidad de construir una lista de mensajes.

#### Request Body
```json
{
  "prompt": "Explica la fotosíntesis en tres oraciones sencillas.",
  "system": "Eres un profesor de biología de secundaria.",
  "model": "llama3.1:8b",
  "temperature": 0.7
}
```

#### Response Body
```json
{
  "model": "llama3.1:8b",
  "content": "La fotosíntesis es el proceso mediante el cual las plantas convierten la luz solar en energía química...",
  "response": "La fotosíntesis es el proceso mediante el cual las plantas convierten la luz solar en energía química...",
  "date": "2026-08-24 23:30:00 UTC",
  "done": true,
  "total_duration": 1820456123
}
```

---

### 3. Modelos Disponibles (`GET /api/v1/inference/models`)
Consulta los modelos de IA actualmente descargados y disponibles en el servidor de inferencia RunPod.

- **Headers:** `Authorization: Bearer <TU_TOKEN>`
- **Respuesta (200 OK):**
```json
{
  "models": [
    {
      "name": "llama3.1:8b",
      "model": "llama3.1:8b",
      "size": 4920753328,
      "details": {
        "format": "gguf",
        "family": "llama",
        "parameter_size": "8.0B",
        "quantization_level": "Q4_K_M"
      }
    }
  ]
}
```

---

### 4. Estado del Servidor (`GET /api/v1/inference/status`)
Comprueba la conectividad directa entre este backend y la instancia de RunPod / Ollama.

- **Headers:** `Authorization: Bearer <TU_TOKEN>`
- **Respuesta (200 OK):**
```json
{
  "status": "connected",
  "service": "ollama",
  "endpoint": "https://tu-pod.proxy.runpod.net",
  "message": "Ollama is running"
}
```

---

## Ejemplos de Clientes Listos para Usar

### Ejemplo en JavaScript / TypeScript (Fetch)

Guarda este cliente en tu proyecto frontend (React, Vue, Next.js) o Node.js:

```javascript
class MyelinaClient {
  constructor(baseUrl = "http://localhost:8000/api/v1", apiKey = null) {
    this.baseUrl = baseUrl;
    this.token = apiKey;
  }

  // 1. Iniciar sesión si se requiere token dinámico
  async login(username, password) {
    const res = await fetch(`${this.baseUrl}/auth/login/json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(`Error en Login (${res.status}): ${err.detail || "Credenciales inválidas"}`);
    }

    const data = await res.json();
    this.token = data.access_token;
    return this.token;
  }

  // 2. Crear un API Key persistente
  async createApiKey(label, expiresInDays = null) {
    const res = await fetch(`${this.baseUrl}/auth/tokens`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.token}`
      },
      body: JSON.stringify({ label, expires_in_days: expiresInDays })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(`Error al crear Token (${res.status}): ${err.detail}`);
    }

    return await res.json();
  }

  // 3. Enviar conversación a la IA
  async chat(messages, model = "llama3.1:8b", temperature = 0.7) {
    if (!this.token) {
      throw new Error("No hay un token o API Key configurado en el cliente.");
    }

    const res = await fetch(`${this.baseUrl}/inference/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.token}`
      },
      body: JSON.stringify({
        messages: messages,
        model: model,
        temperature: temperature,
        stream: false
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(`Error de Inferencia (${res.status}): ${err.detail || "Error en el servidor de IA"}`);
    }

    return await res.json();
  }
}

// ================= USO PRÁCTICO =================
async function main() {
  // Inicializa con tu API Key persistente
  const client = new MyelinaClient("http://localhost:8000/api/v1", "myelina_TU_API_KEY_AQUI");

  const conversationHistory = [
    { role: "system", content: "Eres un asistente amigable y experto en tecnología." },
    { role: "user", content: "Hola, ¿cuál es el mejor lenguaje para crear APIs rápidas en Python?" }
  ];

  try {
    const response = await client.chat(conversationHistory);
    console.log("Respuesta del modelo (" + response.model + "):");
    console.log(response.content);
    console.log("Fecha:", response.date);

    // Agregar la respuesta al historial para continuar la conversación
    conversationHistory.push(response.message);
    conversationHistory.push({ role: "user", content: "¿Puedes darme un ejemplo mínimo de código?" });

    const secondResponse = await client.chat(conversationHistory);
    console.log("\nSegunda Respuesta:\n", secondResponse.content);
  } catch (error) {
    console.error("Ocurrió un error:", error.message);
  }
}

main();
```

---

### Ejemplo en Python (`httpx`)

```python
from typing import List, Dict, Any, Optional
import httpx


class MyelinaClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = api_key

    def login(self, username: str, password: str) -> str:
        """Autentica con usuario y contraseña para obtener JWT."""
        url = f"{self.base_url}/auth/login/json"
        with httpx.Client() as client:
            res = client.post(url, json={"username": username, "password": password})
            if res.status_code != 200:
                raise Exception(f"Error de login: {res.json().get('detail')}")
            self.token = res.json()["access_token"]
            return self.token

    def create_api_key(self, label: str, expires_in_days: Optional[int] = None) -> Dict[str, Any]:
        """Crea un token persistente con prefijo myelina_."""
        url = f"{self.base_url}/auth/tokens"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"label": label, "expires_in_days": expires_in_days}
        with httpx.Client() as client:
            res = client.post(url, json=payload, headers=headers)
            if res.status_code != 201:
                raise Exception(f"Error al crear token: {res.json().get('detail')}")
            return res.json()

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3.1:8b",
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Envía un historial de mensajes a la IA."""
        if not self.token:
            raise ValueError("Debes configurar un token o API Key.")

        url = f"{self.base_url}/inference/chat"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "stream": False,
        }

        with httpx.Client(timeout=120.0) as client:
            res = client.post(url, json=payload, headers=headers)
            if res.status_code != 200:
                raise Exception(f"Error de inferencia ({res.status_code}): {res.text}")
            return res.json()


# ================= USO =================
if __name__ == "__main__":
    client = MyelinaClient(api_key="myelina_TU_API_KEY_AQUI")

    historial = [
        {"role": "sistema", "content": "Eres un asistente de programación conciso."},
        {"role": "usuario", "content": "Explica la diferencia entre un Set y una Lista en Python."}
    ]

    respuesta = client.chat(historial)
    print(f"Respuesta ({respuesta['model']}):")
    print(respuesta["content"])
```

---

### Ejemplo en cURL / Bash

#### 1. Iniciar Sesión (Login)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/json" \
     -H "Content-Type: application/json" \
     -d '{"username": "tu_usuario", "password": "tu_password"}'
```

#### 2. Generar Token Persistente
```bash
curl -X POST "http://localhost:8000/api/v1/auth/tokens" \
     -H "Authorization: Bearer <TU_JWT_AQUI>" \
     -H "Content-Type: application/json" \
     -d '{"label": "mi_script_bash"}'
```

#### 3. Realizar Consulta a la IA (Chat)
```bash
curl -X POST "http://localhost:8000/api/v1/inference/chat" \
     -H "Authorization: Bearer myelina_TU_API_KEY_AQUI" \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [
         {"role": "system", "content": "Eres un asistente amigable."},
         {"role": "user", "content": "Dame una lista de 3 consejos para mejorar el rendimiento de una base de datos."}
       ],
       "model": "llama3.1:8b"
     }'
```

---

## Gestión de Errores y Buenas Prácticas

### Códigos de Respuesta HTTP

| Código | Significado | Causa Habitual / Solución |
|---|---|---|
| `200 OK` | Éxito | La solicitud se completó correctamente. |
| `201 Created` | Creado | Usuario o Token creado exitosamente. |
| `400 Bad Request` | Petición Inválida | Etiqueta de token repetida, usuario existente o payload malformado. |
| `401 Unauthorized` | No Autorizado | Token inválido, expirado, revocado o cabecera `Authorization` ausente. |
| `403 Forbidden` | Prohibido | El usuario no tiene rol de administrador para la ruta solicitada. |
| `503 Service Unavailable` | Servicio no disponible | No se pudo conectar a la instancia de RunPod / Ollama. Verifica la URL configurada. |
| `504 Gateway Timeout` | Tiempo de espera agotado | El modelo tardó más de los segundos configurados (`AI_REQUEST_TIMEOUT`) en procesar el prompt. |

### Buenas Prácticas de Seguridad
1. **Nunca expongas tus API Keys en repositorios públicos**: Almacena las claves en variables de entorno (`.env` o secretos de producción).
2. **Usa un Token por Aplicación/Cliente**: Así, si un cliente se ve comprometido, puedes revocar ese token específico con `POST /api/v1/auth/tokens/{id}/revoke` sin afectar a tus otras aplicaciones.
3. **Maneja el Historial en el Cliente**: Recuerda agregar la respuesta del asistente (`response.message`) a la lista `messages` antes de enviar la siguiente pregunta para conservar el contexto de la charla.