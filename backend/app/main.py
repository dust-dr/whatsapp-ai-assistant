from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
import app.models

# Import and register routers
from app.api.v1.chat import router as chat_router

# Create database tables
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

# Register the chat router
# prefix="/api/v1" means all chat routes start with /api/v1
# so our endpoint becomes: /api/v1/chat
# tags=["chat"] groups it nicely in the /docs page
app.include_router(
    chat_router,
    prefix="/api/v1",
    tags=["chat"]
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
