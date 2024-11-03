from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys (optional for now)
    COINGECKO_API_KEY: str = ""
    ETHERSCAN_API_KEY: str = ""
    
    # General settings
    DEBUG: bool = True
    UPDATE_INTERVAL: int = 300  # seconds
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()