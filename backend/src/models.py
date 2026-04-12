import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.database import Base

def gen_id():
    return f"usr_{uuid.uuid4().hex[:20]}"

class User(Base):
    __tablename__ = "users"

    id         = Column(String, primary_key=True, default=gen_id)
    name       = Column(String, nullable=False)
    email      = Column(String, unique=True, nullable=False)
    password   = Column(String, nullable=False)
    plan       = Column(String, default="free")
    is_active  = Column(Boolean, default=True)
    is_admin   = Column(Boolean, default=False)        # ✅ NEW: admin flag
    created_at = Column(DateTime, default=datetime.utcnow)

    faqs           = relationship("FAQ",           back_populates="user", cascade="all, delete")
    documents      = relationship("Document",      back_populates="user", cascade="all, delete")
    chat_logs      = relationship("ChatLog",       back_populates="user", cascade="all, delete")
    knowledge_base = relationship("KnowledgeBase", back_populates="user", cascade="all, delete")

class FAQ(Base):
    __tablename__ = "faqs"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String, ForeignKey("users.id"), nullable=False)
    question   = Column(Text, nullable=False)
    answer     = Column(Text, nullable=False)
    category   = Column(String, default="general")
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="faqs")

class Document(Base):
    __tablename__ = "documents"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String, ForeignKey("users.id"), nullable=False)
    filename   = Column(String, nullable=False)
    content    = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="documents")

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String, ForeignKey("users.id"), nullable=False)
    question   = Column(Text)
    answer     = Column(Text)
    source     = Column(String)
    language   = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="chat_logs")
    
class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String, ForeignKey("users.id"), nullable=False)
    title      = Column(String, nullable=False)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user       = relationship("User", back_populates="knowledge_base")