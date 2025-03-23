from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from database.db import get_db
from analytics.analyzer import BookingAnalyzer
from qa.qa_system import QASystem
from qa.qa_singleton import QASystemSingleton


# Pydantic models for request/response validation
class AnalyticsRequest(BaseModel):
    """Request model for analytics endpoint."""
    period: Optional[str] = "monthly"  # Time period for aggregation


class QuestionRequest(BaseModel):
    """Request model for question answering endpoint."""
    question: str


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    database: str
    vector_store: str


# Create API router
router = APIRouter()


@router.post("/analytics", response_model=Dict[str, Any])
async def get_analytics(request: AnalyticsRequest, db: Session = Depends(get_db)):
    """
    Generate and return analytics reports.
    
    Args:
        request: Analytics request with optional parameters
        db: Database session
        
    Returns:
        dict: Analytics data
    """
    try:
        analyzer = BookingAnalyzer(db_session=db)
        analytics = analyzer.get_all_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")


@router.post("/ask", response_model=Dict[str, Any])
async def answer_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """
    Answer a booking-related question using RAG.
    
    Args:
        request: Question request with the question text
        db: Database session
        
    Returns:
        dict: Answer and context
    """
    try:
        # Use singleton to avoid repeated initialization
        qa_system = QASystemSingleton.get_instance()
        answer = qa_system.answer_question(request.question)
        return answer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@router.get("/query_history", response_model=List[Dict[str, Any]])
async def get_query_history(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """
    Get recent query history.
    
    Args:
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        list: Recent queries and responses
    """
    try:
        # Use singleton to avoid repeated initialization
        qa_system = QASystemSingleton.get_instance()
        history = qa_system.get_query_history(limit=limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving query history: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Check system health.
    
    Args:
        db: Database session
        
    Returns:
        dict: Health status
    """
    # Check database
    try:
        db.execute("SELECT 1").fetchone()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    try:
        # Check vector store using singleton
        qa_system = QASystemSingleton.get_instance()
        vector_store = qa_system.vector_store
        if vector_store.index and vector_store.index.ntotal > 0:
            vs_status = f"operational ({vector_store.index.ntotal} vectors)"
        else:
            vs_status = "empty"
    except Exception as e:
        vs_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
        "vector_store": vs_status
    }
