# Myelina Server IA

Servidor de inferencia para Inteligencia Artificial construido con **FastAPI**, **SQLite** y gestión de entornos mediante **uv**. Cuenta con autenticación JWT robusta y control de acceso basado en roles (`user` y `admin`).

---

## 📁 Estructura del Proyecto y Organización de Módulos

```text
myelina_server_ia/
├── .venv/                   # Entorno virtual gestionado por uv
├── core/                    # Núcleo: configuración, base de datos y seguridad
│   ├── __init__.py
│   ├── config.py            # Variables de entorno y configuración (Pydantic Settings)
│   ├── database.py          # Conexión SQLite y generador de sesiones SQLAlchemy
│   └── security.py          # Hash con bcrypt, creación/validación de JWT y dependencias de roles
├── models/                  # Modelos ORM (Base de Datos)
│   ├── __init__.py
│   └── user.py              # Modelo de Usuario y Enum UserRole (user, admin)
├── routes/                  # Controladores / Endpoints de la API
│   ├── __init__.py          # Agregador central de routers
│   └── auth.py              # Rutas de autenticación (register, login, me, admin)
├── schemas/                 # Esquemas de validación y serialización Pydantic
│   ├── __init__.py
│   └── user.py              # DTOs de entrada y salida para usuarios y tokens
├── services/                # [Recomendado] Lógica de negocio e Inferencia IA (futuro)
│   └── __init__.py
├── tests/                   # Suite de pruebas automatizadas
│   └── test_auth.py
├── prompts/                 # Historial de requerimientos y guías del proyecto
│   └── 1.md
├── .env.example             # Plantilla de variables de entorno
├── .gitignore               # Exclusiones de Git
├── main.py                  # Punto de entrada de la aplicación FastAPI
└── pyproject.toml           # Configuración del proyecto y dependencias uv
```

---

## 🚀 Inicio Rápido con `uv`

### 1. Activar el entorno virtual
```bash
source .venv/bin/activate
```

### 2. Instalar / sincronizar dependencias
```bash
uv pip install -e .
```

### 3. Ejecutar el servidor en desarrollo
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en:
- **API Base:** [http://localhost:8000](http://localhost:8000)
- **Documentación Interactiva (Swagger UI):** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Documentación Alternativa (ReDoc):** [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

---

## 🔐 Endpoints de Autenticación y Seguridad

| Método | Endpoint | Acceso | Descripción |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Público | Registro de usuarios (selección libre de rol en `DEBUG=True`) |
| `POST` | `/api/v1/auth/login` | Público | Login estándar OAuth2 Form (integrado con Swagger) |
| `POST` | `/api/v1/auth/login/json` | Público | Login mediante JSON payload |
| `GET` | `/api/v1/auth/me` | Autenticado | Obtiene la información del usuario en sesión |
| `GET` | `/api/v1/auth/admin/users` | Admin | Lista todos los usuarios registrados |
| `GET` | `/debug_settings` | DEBUG only | UI Web interactiva para pruebas de registro (con rol), login y tokens |

---

## 🧪 Ejecutar Pruebas
```bash
uv run pytest
```
