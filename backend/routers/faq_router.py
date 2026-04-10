from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from src.database import get_db
from src.models import FAQ, User
from src.dependencies import get_current_user
from src.embedding import build_vector_db
from src.models import Document, KnowledgeBase

router = APIRouter(prefix="/api/faqs", tags=["FAQs"])

class FAQCreate(BaseModel):
    question: str
    answer:   str
    category: Optional[str] = "general"

class FAQUpdate(BaseModel):
    question: Optional[str]
    answer:   Optional[str]
    category: Optional[str]

# Dono routers mein same helper function update karo
def rebuild_user_vector_db(user_id: str, db: Session):
    """Helper — rebuild vector DB after FAQ changes."""
    faqs = db.query(FAQ).filter(FAQ.user_id == user_id).all()
    docs = db.query(Document).filter(Document.user_id == user_id).all()
    docs = [d for d in docs if d.content and len(d.content.strip()) > 0]
    kbs  = db.query(KnowledgeBase).filter(KnowledgeBase.user_id == user_id).all()

    build_vector_db(
        user_id        = user_id,
        faqs           = [{"question": f.question, "answer": f.answer, "category": f.category} for f in faqs],
        documents      = [{"filename": d.filename, "content": d.content} for d in docs],
        knowledge_base = [{"title": k.title, "content": k.content} for k in kbs]
    )

@router.get("/")
def get_faqs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    faqs = db.query(FAQ).filter(FAQ.user_id == user.id).all()
    return faqs

@router.post("/")
def add_faq(req: FAQCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    faq = FAQ(user_id=user.id, question=req.question, answer=req.answer, category=req.category)
    db.add(faq)
    db.commit()
    db.refresh(faq)
    rebuild_user_vector_db(user.id, db)
    return faq

@router.put("/{faq_id}")
def update_faq(faq_id: int, req: FAQUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id, FAQ.user_id == user.id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    if req.question: faq.question = req.question
    if req.answer:   faq.answer   = req.answer
    if req.category: faq.category = req.category
    db.commit()
    rebuild_user_vector_db(user.id, db)
    return faq

@router.delete("/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id, FAQ.user_id == user.id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    db.delete(faq)
    db.commit()
    rebuild_user_vector_db(user.id, db)
    return {"message": "FAQ deleted"}