from pydantic import BaseModel
from typing import Optional


class BusinessRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone_number: str
    business_type: Optional[str] = None
    description: Optional[str] = None
    ai_persona_name: Optional[str] = "Ama"


class BusinessLoginRequest(BaseModel):
    email: str
    password: str


class BusinessResponse(BaseModel):
    id: str
    name: str
    email: str
    phone_number: str
    business_type: Optional[str]
    ai_persona_name: Optional[str]
    is_active: bool
    whatsapp_connected: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    business: BusinessResponse


class MessageResponse(BaseModel):
    message: str
    success: bool = True
