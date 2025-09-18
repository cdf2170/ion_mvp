from typing import List
import os


class Settings:
    """Simple settings class without Pydantic to avoid parsing issues"""
    
    def __init__(self):
        # Database - Railway will provide DATABASE_URL automatically
        self.database_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:password@localhost:5435/mvp_db")
        
        # Authentication
        self.demo_api_token = os.getenv("DEMO_API_TOKEN", "demo-token-12345")
        
        # App
        self.app_name = os.getenv("APP_NAME", "MVP Backend")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.port = int(os.getenv("PORT", "8000"))
        
        # Railway specific
        self.railway_environment = os.getenv("RAILWAY_ENVIRONMENT", "development")
        self.railway_project_id = os.getenv("RAILWAY_PROJECT_ID", "")
        self.railway_service_id = os.getenv("RAILWAY_SERVICE_ID", "")
        
        # CORS origins - parse manually
        self._parse_allowed_origins()
    
    def _parse_allowed_origins(self):
        """Parse allowed origins from environment variable"""
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:5173,https://ion-app-rose.vercel.app,https://app.privion.tech,https://api.privion.tech")
        
        if not origins_str:
            self.allowed_origins = ["*"]
            return
        
        origins = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
        
        # In development, always include localhost origins
        if self.railway_environment != "production":
            localhost_origins = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
            for localhost_origin in localhost_origins:
                if localhost_origin not in origins:
                    origins.append(localhost_origin)
        
        # In production, remove localhost origins
        if self.railway_environment == "production":
            origins = [origin for origin in origins if not origin.startswith("http://localhost")]
        
        self.allowed_origins = origins if origins else ["*"]
        
    def get_database_url(self) -> str:
        """Get database URL with Railway compatibility"""
        db_url = self.database_url
        # Convert postgresql:// to postgresql+psycopg:// for Railway compatibility
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return db_url


settings = Settings()
