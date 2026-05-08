from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    phone_number = Column(String(20), nullable=False)
    name = Column(String(255))
    context_summary = Column(Text)
    extra_data = Column(JSON, default={})
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="customers")
    messages = relationship("Message", back_populates="customer")
    leads = relationship("Lead", back_populates="customer")
