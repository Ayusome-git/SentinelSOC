import os
from typing import List, Union
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "SentinelSOC"
    API_V1_STR: str = "/api/v1"
    
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:3000"]'
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost", "http://localhost:8000"]

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://sentinelsoc:password@localhost:5432/sentinelsoc")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super_secret_key_placeholder")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # ML Configuration
    ML_ENABLED: bool = os.getenv("ML_ENABLED", "True").lower() in ("true", "1", "yes")
    ML_WINDOW_SECONDS: int = int(os.getenv("ML_WINDOW_SECONDS", "300")) # 5 mins
    ML_TRAINING_DAYS: int = int(os.getenv("ML_TRAINING_DAYS", "7"))
    ML_MIN_TRAINING_SAMPLES: int = int(os.getenv("ML_MIN_TRAINING_SAMPLES", "30"))
    ML_ANOMALY_THRESHOLD: int = int(os.getenv("ML_ANOMALY_THRESHOLD", "75"))
    ML_MODEL_DIRECTORY: str = os.getenv("ML_MODEL_DIRECTORY", "./ml_models")
    ML_RANDOM_STATE: int = int(os.getenv("ML_RANDOM_STATE", "42"))
    ML_N_ESTIMATORS: int = int(os.getenv("ML_N_ESTIMATORS", "100"))

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    class Config:
        case_sensitive = True

settings = Settings()
