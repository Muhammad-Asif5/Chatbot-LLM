from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from src.database import get_db
from src.models import FAQ, User, Document, KnowledgeBase
from src.dependencies import get_current_user
from src.embedding import build_vector_db

router = APIRouter(prefix="/api/faqs", tags=["FAQs"])

class FAQCreate(BaseModel):
    question: str
    answer:   str
    category: Optional[str] = "general"

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer:   Optional[str] = None
    category: Optional[str] = None

def rebuild_user_vector_db(user_id: str, db: Session):
    """Helper — rebuild vector DB after any data change."""
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
    return db.query(FAQ).filter(FAQ.user_id == user.id).all()

@router.post("/")
def add_faq(req: FAQCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    faq = FAQ(user_id=user.id, question=req.question, answer=req.answer, category=req.category)
    db.add(faq)
    db.flush()       # ✅ ID generate karo commit se pehle
    db.commit()
    db.refresh(faq)
    rebuild_user_vector_db(user.id, db)
    return faq

@router.put("/{faq_id}")
def update_faq(faq_id: int, req: FAQUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id, FAQ.user_id == user.id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    # ✅ FIXED: None check properly (empty string bhi valid update ho sakti hai)
    if req.question is not None: faq.question = req.question
    if req.answer   is not None: faq.answer   = req.answer
    if req.category is not None: faq.category = req.category

    db.flush()   # ✅ Changes stage karo
    db.commit()
    db.refresh(faq)
    rebuild_user_vector_db(user.id, db)
    return faq

@router.delete("/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id, FAQ.user_id == user.id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    db.delete(faq)
    db.flush()    # ✅ DELETE statement execute karo immediately
    db.commit()   # ✅ Permanently commit to disk

    rebuild_user_vector_db(user.id, db)
    return {"message": "FAQ deleted", "id": faq_id}