import os
from typing import Optional

class Settings:
    PROJECT_NAME: str = "TWELVE"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Voice Infrastructure V1
    DEEPGRAM_API_KEY: Optional[str] = os.getenv("DEEPGRAM_API_KEY")
    DEEPGRAM_MODEL: str = os.getenv("DEEPGRAM_MODEL", "nova-2")
    DEEPGRAM_LANGUAGE: str = os.getenv("DEEPGRAM_LANGUAGE", "en-US")
    DEEPGRAM_ENDPOINT: str = os.getenv("DEEPGRAM_ENDPOINT", "wss://api.deepgram.com/v1/listen")
    VOICE_PROVIDER: str = os.getenv("VOICE_PROVIDER", "deepgram")
    VOICE_PLAYBACK_VOICE: str = os.getenv("VOICE_PLAYBACK_VOICE", "Samantha")
    VOICE_PLAYBACK_RATE: int = int(os.getenv("VOICE_PLAYBACK_RATE", "180"))
    VOICE_SAMPLE_RATE_HZ: int = int(os.getenv("VOICE_SAMPLE_RATE_HZ", "16000"))
    VOICE_CHANNELS: int = int(os.getenv("VOICE_CHANNELS", "1"))
    VOICE_SILENCE_RMS_THRESHOLD: int = int(os.getenv("VOICE_SILENCE_RMS_THRESHOLD", "150"))
    VOICE_SILENCE_SECONDS: float = float(os.getenv("VOICE_SILENCE_SECONDS", "1.25"))
    
    # Storage
    TRANSCRIPT_STORAGE_PATH: str = os.getenv("TRANSCRIPT_STORAGE_PATH", "./data/transcripts")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-dev")

settings = Settings()
