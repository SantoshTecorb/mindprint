from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "MindPrint Memory API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str = "postgresql://nanobot:password@localhost/memorydb"
    CONSULT_MODEL: str = "gpt-3.5-turbo"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
