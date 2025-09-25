import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/bd_jobs"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Scraping
    SCRAPER_DELAY: float = 1.0
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_RETRIES: int = 3
    USE_PROXY: bool = False
    PROXY_LIST: List[str] = []
    
    # Email
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
