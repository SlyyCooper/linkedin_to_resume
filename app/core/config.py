from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    APP_NAME: str = "LinkedIn Profile Assistant"
    DEBUG: bool = True
    OPENAI_MODEL: str = "gpt-4o"  # Using the latest model as of April 2024
    OPENAI_API_KEY: str
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 