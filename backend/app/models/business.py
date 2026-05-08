from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    business_type = Column(String(100))
    description = Column(Text)
    ai_persona_name = Column(String(50), default="Ama")
    products_sheet_url = Column(String(500))
    faqs_sheet_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    whatsapp_connected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customers = relationship("Customer", back_populates="business")
    messages = relationship("Message", back_populates="business")
    leads = relationship("Lead", back_populates="business")
