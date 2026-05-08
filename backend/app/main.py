from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
import app.models

# Create all tables on Neon automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WhatsApp AI Assistant API",
    description="AI-powered WhatsApp Sales Assistant for African SMEs",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "WhatsApp AI Assistant API is running ✅",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "ai_provider": settings.ai_provider,
    }
