from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database import get_db
from src.models import ChatLog, FAQ, Document, User
from src.dependencies import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/")
def get_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_questions = db.query(ChatLog).filter(ChatLog.user_id == user.id).count()
    total_faqs      = db.query(FAQ).filter(FAQ.user_id == user.id).count()
    total_docs      = db.query(Document).filter(Document.user_id == user.id).count()
    recent_chats    = db.query(ChatLog).filter(
                        ChatLog.user_id == user.id
                      ).order_by(ChatLog.created_at.desc()).limit(10).all()

    return {
        "total_questions": total_questions,
        "total_faqs":      total_faqs,
        "total_documents": total_docs,
        "recent_chats": [
            {
                "question":   c.question,
                "answer":     c.answer,
                "source":     c.source,
                "created_at": str(c.created_at)
            } for c in recent_chats
        ]
    }