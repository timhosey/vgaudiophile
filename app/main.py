"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from app.config import settings
import os

app = FastAPI(
    title="VGAudiophile API",
    description="API for indexing, cataloguing, and tagging video game soundtracks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["api"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api")
def api_info():
    """API info endpoint."""
    return {"message": "VGAudiophile API", "version": "1.0.0"}


# Serve frontend static files
# Get the project root (parent of app directory)
app_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(app_dir)
frontend_path = os.path.join(project_root, "frontend")

# Mount static assets (CSS, JS, etc.) at /static
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    # Serve frontend HTML files - this must come after API routes
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Serve frontend files."""
        # Don't interfere with API routes
        if full_path.startswith("api") or full_path.startswith("health"):
            return {"error": "Not found"}
        
        # Serve index.html for root or empty path
        if full_path == "" or full_path == "/" or full_path == "index.html":
            index_path = os.path.join(frontend_path, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path, media_type="text/html")
        
        # Try to serve the requested file (for direct file access)
        file_path = os.path.join(frontend_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Determine media type
            media_type = "text/html" if file_path.endswith(".html") else None
            return FileResponse(file_path, media_type=media_type)
        
        # For SPA routing, serve index.html for any non-API route
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")
        
        return {"error": "Not found", "path": full_path, "frontend_path": frontend_path}
else:
    # Frontend not found - log for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Frontend directory not found at: {frontend_path}")
    logger.warning(f"App dir: {app_dir}, Project root: {project_root}")

