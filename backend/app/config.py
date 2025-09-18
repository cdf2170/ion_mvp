from typing import List
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database - Railway will provide DATABASE_URL automatically
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:password@localhost:5435/mvp_db")
    
    # Authentication
    demo_api_token: str = os.getenv("DEMO_API_TOKEN", "demo-token-12345")
    
    # App
    app_name: str = os.getenv("APP_NAME", "MVP Backend")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    port: int = int(os.getenv("PORT", "8000"))
    
    # Railway specific
    railway_environment: str = os.getenv("RAILWAY_ENVIRONMENT", "development")
    railway_project_id: str = os.getenv("RAILWAY_PROJECT_ID", "")
    railway_service_id: str = os.getenv("RAILWAY_SERVICE_ID", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def get_database_url(self) -> str:
        """Get database URL with Railway compatibility"""
        db_url = self.database_url
        # Convert postgresql:// to postgresql+psycopg:// for Railway compatibility
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return db_url


settings = Settings()

# Handle CORS origins manually to avoid Pydantic parsing issues
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:5173,https://ion-app-rose.vercel.app,https://app.privion.tech")
settings.allowed_origins = [origin.strip() for origin in allowed_origins_env.split(',') if origin.strip()]

# Ensure production CORS origins are properly set for Railway
if settings.railway_environment == "production":
    # Add Railway domains and remove localhost origins in production
    production_origins = [origin for origin in settings.allowed_origins if not origin.startswith("http://localhost")]
    settings.allowed_origins = production_origins
