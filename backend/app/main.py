from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from backend.app.routers import users, devices, apis, policies, history
from backend.app.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="MVP Backend",
        description="Production-ready FastAPI backend with PostgreSQL",
        version="1.0.0",
    )
    
    # Configure CORS using centralized settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins if settings.allowed_origins else ["*"],
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
        """Simple health check endpoint for Railway"""
        import time
        
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
            "port": os.getenv("PORT", "not_set"),
            "database_url_set": bool(os.getenv("DATABASE_URL")),
        }
        
        # Simple database connectivity check (non-blocking)
        try:
            from backend.app.db.session import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                health_data["database"] = "connected"
        except Exception as e:
            health_data["database"] = f"error: {str(e)[:100]}"
        
        return health_data
    
    @app.get("/debug/routes")
    def debug_routes():
        """Debug endpoint to check what routes are registered"""
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append({
                    "path": route.path,
                    "methods": getattr(route, 'methods', []),
                    "name": getattr(route, 'name', 'unknown')
                })
        return {
            "total_routes": len(routes),
            "routes": routes,
            "routers_imported": {
                "users": "users" in str(users),
                "devices": "devices" in str(devices), 
                "apis": "apis" in str(apis),
                "policies": "policies" in str(policies),
                "history": "history" in str(history)
            }
        }
    
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
