from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./chatbot.db"
    
    # AI Configuration - Now supports both OpenAI and Gemini
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    AI_PROVIDER: str = "gemini"  # "openai" or "gemini" or "mock"
    
    # Application Settings
    APP_NAME: str = "AI Customer Support Bot"
    DEBUG: bool = True
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_CONVERSATION_HISTORY: int = 10
    
    # Escalation Configuration
    CONFIDENCE_THRESHOLD: float = 0.7
    MAX_LOOP_DETECTION: int = 3
    
    # CORS Settings
    CORS_ORIGINS: list = ["http://localhost:8000", "http://localhost:3000", "http://127.0.0.1:8000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
