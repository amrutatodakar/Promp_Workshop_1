import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "ReportSaathi API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    FRONTEND_URL: str = "https://promp-workshop-1.onrender.com/"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,https://promp-workshop-1.onrender.com"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    
    # Supabase optional
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        origins = []
        for origin in self.CORS_ORIGINS.split(","):
            cleaned = origin.strip()
            if cleaned:
                origins.append(cleaned)
                origins.append(cleaned.rstrip("/"))
        return list(dict.fromkeys(origins))

settings = Settings()
