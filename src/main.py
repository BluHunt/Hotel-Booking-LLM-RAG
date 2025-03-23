import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

# Import router
from api.router import router
from database.db import engine
from database.models import Base

# Create the FastAPI app
app = FastAPI(
    title="Hotel Booking Analytics & QA API",
    description="API for hotel booking analytics and retrieval-augmented question answering",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include router
app.include_router(router)

# Create a root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Hotel Booking Analytics & QA API",
        "docs_url": "/docs",
        "endpoints": [
            {"method": "POST", "path": "/analytics", "description": "Get analytics reports"},
            {"method": "POST", "path": "/ask", "description": "Answer booking-related questions"},
            {"method": "GET", "path": "/history", "description": "Get query history"},
            {"method": "GET", "path": "/health", "description": "Check system health"}
        ]
    }

# Helper function for datetime
def import_datetime():
    import datetime
    return datetime

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running and all system dependencies are functioning properly.
    Returns details about the status of each critical system component.
    """
    health_status = {
        "status": "online",
        "api_version": app.version,
        "timestamp": str(import_datetime().now()),
        "dependencies": {}
    }
    
    # Check database connection
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        health_status["dependencies"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["dependencies"]["database"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check file system access
    data_dir = Path("data")
    try:
        if not data_dir.exists():
            data_dir.mkdir(exist_ok=True)
        # Write and read a test file
        test_file = data_dir / "health_check_test.txt"
        test_file.write_text("test")
        test_file.read_text()
        test_file.unlink()  # Delete the test file
        health_status["dependencies"]["file_system"] = {"status": "healthy"}
    except Exception as e:
        health_status["dependencies"]["file_system"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check available memory
    try:
        import psutil
        available_memory = psutil.virtual_memory().available / (1024 * 1024 * 1024)  # GB
        memory_status = "healthy" if available_memory > 1.0 else "low"
        health_status["dependencies"]["memory"] = {
            "status": memory_status,
            "available_gb": round(available_memory, 2)
        }
        if memory_status == "low":
            health_status["status"] = "degraded"
    except ImportError:
        # psutil might not be installed
        health_status["dependencies"]["memory"] = {"status": "unknown", "message": "psutil not installed"}
    except Exception as e:
        health_status["dependencies"]["memory"] = {"status": "unknown", "message": str(e)}
    
    # Overall system status - if any dependency is unhealthy, mark as "degraded"
    if any(dep.get("status") == "unhealthy" for dep in health_status["dependencies"].values()):
        health_status["status"] = "degraded"
    
    return health_status

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Run the API server
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
