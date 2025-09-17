from typing import List
import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+psycopg://postgres:password@localhost:5435/mvp_db"
    
    # Authentication
    demo_api_token: str = "demo-token-12345"
    
    # CORS
    allowed_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:5173,https://ion-app-rose.vercel.app,https://app.privion.tech",
        alias="ALLOWED_ORIGINS"
    )
    
    @field_validator('allowed_origins_str')
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @property
    def allowed_origins(self) -> List[str]:
        if isinstance(self.allowed_origins_str, list):
            return self.allowed_origins_str
        return [origin.strip() for origin in self.allowed_origins_str.split(',')]
    
    # App
    app_name: str = "MVP Backend"
    debug: bool = True
    port: int = int(os.getenv("PORT", "8000"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
