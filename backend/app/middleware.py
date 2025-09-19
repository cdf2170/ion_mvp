"""
Custom middleware for better error handling and debugging
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
import logging
import traceback

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Enhanced error handling for better frontend debugging"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # Return structured error response
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "type": "HTTPException",
                        "message": e.detail,
                        "status_code": e.status_code,
                        "path": str(request.url.path),
                        "method": request.method
                    }
                }
            )
        except Exception as e:
            # Log the full error for debugging
            logger.error(f"Unhandled error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return structured error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "InternalServerError", 
                        "message": "An internal server error occurred",
                        "path": str(request.url.path),
                        "method": request.method,
                        "debug_info": str(e) if request.app.debug else None
                    }
                }
            )


class CORSDebugMiddleware(BaseHTTPMiddleware):
    """Debug CORS issues by logging requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Log CORS-related info for debugging
        origin = request.headers.get("origin")
        if origin:
            logger.info(f"CORS request from origin: {origin}")
            
        response = await call_next(request)
        
        # Add debug headers in development
        if request.app.debug:
            response.headers["X-Debug-Origin"] = origin or "none"
            response.headers["X-Debug-Method"] = request.method
            
        return response
