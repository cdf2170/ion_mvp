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
    def root():
        return {"message": "MVP Backend API", "status": "running", "version": "1.0.0"}
    
    @app.get("/health")
    def health_check():
        """Comprehensive health check endpoint for Railway"""
        from backend.app.db.session import engine
        from sqlalchemy import text
        import time
        
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
            "checks": {}
        }
        
        # Database connectivity check
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                health_data["checks"]["database"] = "healthy"
        except Exception as e:
            health_data["status"] = "unhealthy"
            health_data["checks"]["database"] = f"unhealthy: {str(e)}"
        
        # Memory and basic system checks
        try:
            import psutil
            health_data["checks"]["memory_usage"] = f"{psutil.virtual_memory().percent}%"
        except ImportError:
            health_data["checks"]["memory_usage"] = "not_available"
        
        return health_data
    
    @app.get("/readiness")
    def readiness_check():
        """Readiness probe for Railway"""
        from backend.app.db.session import engine
        from sqlalchemy import text
        
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ready"}
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=f"Database not ready: {str(e)}")
    
    @app.get("/liveness")
    def liveness_check():
        """Liveness probe for Railway"""
        return {"status": "alive"}
    
    return app


# Create the app instance
app = create_app()


# Removed uvicorn.run() - Railway handles this via Procfile
