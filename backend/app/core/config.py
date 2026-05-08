from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    app_env: str = "development"
    debug: bool = True

    # Database (Neon)
    database_url: str

    # AI Provider
    ai_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"

    # Ollama (backup)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # WhatsApp
    whatsapp_api_url: str = ""
    whatsapp_token: str = ""
    whatsapp_verify_token: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
