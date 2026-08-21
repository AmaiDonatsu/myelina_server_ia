from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta al archivo .env en la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Cargar variables de entorno desde .env si existe
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Myelina Server IA"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "myelina_default_secret_key_change_me_in_production_12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./myelina.db"

    # AI Model Inference (RunPod / Ollama)
    AI_INFERENCE_URL: str = "https://iapx06g61diaeb-11434.proxy.runpod.net"
    DEFAULT_AI_MODEL: str = "llama3.1:8b"
    AI_REQUEST_TIMEOUT: float = 120.0

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
