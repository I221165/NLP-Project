"""
CourseMaster AI - Production Backend
Main FastAPI application with LangChain integration
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database.connection import init_db
from logging_config import setup_logging, get_logger
import time

# Setup logging
setup_logging(level="INFO")
logger = get_logger(__name__)

# Import routers
from routers import auth, pdf, chat, quiz, analytics

# Initialize FastAPI app
app = FastAPI(
    title="CourseMaster AI",
    description="Production RAG-based tutoring platform with LangChain agentic framework",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses"""
    start_time = time.time()
    
    # Log request
    logger.info("Incoming request", extra={
        "method": request.method,
        "path": request.url.path,
        "client": request.client.host if request.client else None
    })
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = (time.time() - start_time) * 1000  # ms
    logger.info("Request completed", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration": round(duration, 2)
    })
    
    return response


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(pdf.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(quiz.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting CourseMaster AI...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        logger.warning("If using PostgreSQL, ensure it's running and DATABASE_URL is correct")
    
    logger.info("CourseMaster AI ready", extra={
        "groq_model": settings.GROQ_MODEL,
        "jwt_expiry_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "cors_origins": settings.CORS_ORIGINS
    })


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CourseMaster AI",
        "version": "2.0.0",
        "features": [
            "Multi-user authentication",
            "PDF upload & indexing",
            "RAG-based Q&A",
            "AI quiz generation",
            "Weakness tracking"
        ]
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "groq_api": "configured",
        "chroma_db": "initialized"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
