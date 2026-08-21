from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
# Ruta absoluta al archivo .env en la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Cargar variables de entorno desde .env si existe
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME")
    VERSION: str = os.getenv("VERSION")
    API_V1_STR: str = os.getenv("API_V1_STR")
    DEBUG: bool = os.getenv("DEBUG") == "True"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # AI Model Inference (RunPod / Ollama)
    AI_INFERENCE_URL: str = os.getenv("AI_INFERENCE_URL")
    DEFAULT_AI_MODEL: str = os.getenv("DEFAULT_AI_MODEL")
    AI_REQUEST_TIMEOUT: float = float(os.getenv("AI_REQUEST_TIMEOUT"))

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
