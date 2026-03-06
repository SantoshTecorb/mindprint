from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "MindPrint Memory API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str
    CONSULT_MODEL: str
    GROQ_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
