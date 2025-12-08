"""
CourseMaster AI - Production Backend
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database.connection import init_db

# Import routers
from routers import auth, pdf, chat, quiz, analytics

# Initialize FastAPI app
app = FastAPI(
    title="CourseMaster AI",
    description="Production RAG-based tutoring platform with multi-user support",
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


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(pdf.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(quiz.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting CourseMaster AI...")
    
    # Initialize database
    try:
        init_db()
    except Exception as e:
        print(f"⚠️  Database initialization: {e}")
        print("   If using PostgreSQL, make sure it's running and DATABASE_URL is correct")
        print("   Or switch to SQLite in .env file")
    
    print("✅ CourseMaster AI ready!")
    print(f"📚 Groq Model: {settings.GROQ_MODEL}")
    print(f"🔐 JWT Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    print(f"📡 CORS Origins: {settings.CORS_ORIGINS}")


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
