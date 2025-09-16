from typing import List
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+psycopg://postgres:password@localhost:5435/mvp_db"
    
    # Authentication
    demo_api_token: str = "demo-token-12345"
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:5173",
        "https://ion-app-rose.vercel.app",
        "https://app.privion.tech"
    ]
    
    # App
    app_name: str = "MVP Backend"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
