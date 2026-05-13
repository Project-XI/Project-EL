import os
from typing import Optional

class Settings:
    PROJECT_NAME: str = "TWELVE"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Storage
    TRANSCRIPT_STORAGE_PATH: str = os.getenv("TRANSCRIPT_STORAGE_PATH", "./data/transcripts")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-dev")

settings = Settings()
