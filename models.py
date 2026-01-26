from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

# Note: Using a different table name to avoid conflicts with existing explorejungles.com tables
class User(Base):
    """User model - maps to existing users table"""
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}  # Don't recreate if exists
    
    id = Column(PGUUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to chatbot sessions
    chatbot_sessions = relationship("ChatbotSession", back_populates="user", cascade="all, delete-orphan")

class ChatbotSession(Base):
    """Chatbot session model - renamed to avoid conflicts"""
    __tablename__ = "chatbot_sessions"
    
    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(PGUUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    history = Column(JSON, default=list)  # Store chat history as JSON
    
    # Relationship to user
    user = relationship("User", back_populates="chatbot_sessions")

class Package(Base):
    """Package model for storing expedition/safari packages"""
    __tablename__ = "chatbot_packages"  # Renamed to avoid conflicts
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    heading = Column(String)
    region = Column(String)
    duration = Column(String)
    type = Column(String)  # 'expedition', 'resort', etc.
    price = Column(Float)
    currency = Column(String, default="INR")
    image = Column(String)
    additional_images = Column(JSON, default=list)
    features = Column(JSON, default=dict)
    date = Column(JSON, default=list)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "_id": self.id,
            "title": self.title,
            "description": self.description,
            "heading": self.heading,
            "region": self.region,
            "duration": self.duration,
            "type": self.type,
            "price": self.price,
            "currency": self.currency,
            "image": self.image,
            "additional_images": self.additional_images,
            "features": self.features,
            "date": self.date,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 