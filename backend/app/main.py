from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import traceback

# Import settings first
try:
    from backend.app.config import settings
    config_import_error = None
except Exception as e:
    config_import_error = str(e)
    # Create minimal settings fallback
    class Settings:
        allowed_origins = ["*"]
        demo_api_token = "demo-token-12345"
    settings = Settings()

# Try to import routers with error handling
router_import_errors = {}
routers_available = {}

try:
    from backend.app.routers import users
    routers_available['users'] = users
except Exception as e:
    router_import_errors['users'] = str(e)
    routers_available['users'] = None

try:
    from backend.app.routers import devices
    routers_available['devices'] = devices
except Exception as e:
    router_import_errors['devices'] = str(e)
    routers_available['devices'] = None

try:
    from backend.app.routers import apis
    routers_available['apis'] = apis
except Exception as e:
    router_import_errors['apis'] = str(e)
    routers_available['apis'] = None

try:
    from backend.app.routers import policies
    routers_available['policies'] = policies
except Exception as e:
    router_import_errors['policies'] = str(e)
    routers_available['policies'] = None

try:
    from backend.app.routers import history
    routers_available['history'] = history
except Exception as e:
    router_import_errors['history'] = str(e)
    routers_available['history'] = None


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
    
    # Include routers (only if successfully imported)
    routers_included = []
    routers_failed = []
    
    if routers_available['users']:
        app.include_router(routers_available['users'].router, prefix="/api/v1")
        routers_included.append('users')
    else:
        routers_failed.append('users')
    
    if routers_available['devices']:
        app.include_router(routers_available['devices'].router, prefix="/api/v1")
        routers_included.append('devices')
    else:
        routers_failed.append('devices')
    
    if routers_available['apis']:
        app.include_router(routers_available['apis'].router, prefix="/api/v1")
        routers_included.append('apis')
    else:
        routers_failed.append('apis')
    
    if routers_available['policies']:
        app.include_router(routers_available['policies'].router, prefix="/api/v1")
        routers_included.append('policies')
    else:
        routers_failed.append('policies')
    
    if routers_available['history']:
        app.include_router(routers_available['history'].router, prefix="/api/v1")
        routers_included.append('history')
    else:
        routers_failed.append('history')
    
    @app.get("/")
    def root():
        return {"message": "MVP Backend API", "status": "running", "version": "1.0.1", "deployment_test": "force_rebuild"}
    
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
            "routers_included": routers_included,
            "routers_failed": routers_failed,
            "router_import_errors": router_import_errors,
            "config_import_error": config_import_error,
            "python_path": sys.path[:5],  # First 5 paths
            "working_directory": os.getcwd(),
            "environment_vars": {
                "PYTHONPATH": os.getenv("PYTHONPATH", "not_set"),
                "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "not_set"),
                "PORT": os.getenv("PORT", "not_set")
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
