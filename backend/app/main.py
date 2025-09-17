from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from backend.app.routers import users, devices, apis, policies, history


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="MVP Backend",
        description="Production-ready FastAPI backend with PostgreSQL",
        version="1.0.0",
    )
    
    # Parse comma-separated origins from env (no spaces)
    _allowed = os.getenv("ALLOWED_ORIGINS", "")
    origins = [o for o in _allowed.split(",") if o]
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],  # loosen if needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(devices.router, prefix="/api/v1")
    app.include_router(apis.router, prefix="/api/v1")
    app.include_router(policies.router, prefix="/api/v1")
    app.include_router(history.router, prefix="/api/v1")
    
    @app.get("/")
    def health():
        return {"ok": True}
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}
    
    return app


# Create the app instance
app = create_app()


# Removed uvicorn.run() - Railway handles this via Procfile
