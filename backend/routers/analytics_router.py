from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import ChatLog, FAQ, Document, User
from src.dependencies import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# ─────────────────────────────────────────────────────────
# RESPONSE MODELS
# ─────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    question: str
    answer: str
    source: str
    created_at: str

class PaginatedChatResponse(BaseModel):
    items: List[ChatResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# ─────────────────────────────────────────────────────────
# API ENDPOINT
# ─────────────────────────────────────────────────────────

@router.get("/")
def get_analytics(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # ─────────────── Counts ───────────────
    total_questions = db.query(ChatLog).filter(ChatLog.user_id == user.id).count()
    total_faqs      = db.query(FAQ).filter(FAQ.user_id == user.id).count()
    total_docs      = db.query(Document).filter(Document.user_id == user.id).count()

    # ─────────────── Pagination Logic ───────────────
    total_chats = db.query(ChatLog).filter(ChatLog.user_id == user.id).count()
    offset = (page - 1) * page_size

    chats = db.query(ChatLog)\
        .filter(ChatLog.user_id == user.id)\
        .order_by(ChatLog.created_at.desc())\
        .offset(offset)\
        .limit(page_size)\
        .all()

    total_pages = (total_chats + page_size - 1) // page_size

    # ─────────────── Response ───────────────
    return {
        "total_questions": total_questions,
        "total_faqs": total_faqs,
        "total_documents": total_docs,

        "recent_chats": {
            "items": [
                {
                    "question": c.question,
                    "answer": c.answer,
                    "source": c.source,
                    "created_at": str(c.created_at)
                } for c in chats
            ],
            "total": total_chats,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    }