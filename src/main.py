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

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Run the API server
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
