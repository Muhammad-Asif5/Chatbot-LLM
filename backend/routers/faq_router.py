from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from src.database import get_db
from src.models import FAQ, User, Document, KnowledgeBase
from src.dependencies import get_current_user
from src.embedding import build_vector_db
from core.response import success_response

router = APIRouter(prefix="/faqs", tags=["FAQs"])

# ─────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────────────────

class FAQCreate(BaseModel):
    question: str
    answer:   str
    category: Optional[str] = "general"

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer:   Optional[str] = None
    category: Optional[str] = None

class FAQResponse(BaseModel):
    id:         int
    user_id:    str
    question:   str
    answer:     str
    category:   str
    created_at: str

class PaginatedFAQResponse(BaseModel):
    """Paginated FAQ response structure"""
    items:      List[FAQResponse]
    total:      int
    page:       int
    page_size:  int
    total_pages: int

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

def _serialize_faq(f: FAQ) -> FAQResponse:
    """Serialize FAQ model to response schema."""
    return FAQResponse(
        id=f.id,
        user_id=f.user_id,
        question=f.question,
        answer=f.answer,
        category=f.category,
        created_at=str(f.created_at)
    )

# ─────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────

@router.get("/", response_model=PaginatedFAQResponse)
def get_faqs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get paginated FAQs for the current user.
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 100)
    """
    # Get total count
    total = db.query(FAQ).filter(FAQ.user_id == user.id).count()
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get paginated items
    faqs = db.query(FAQ)\
        .filter(FAQ.user_id == user.id)\
        .order_by(FAQ.created_at.desc())\
        .offset(offset)\
        .limit(page_size)\
        .all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    # Build response
    response = PaginatedFAQResponse(
        items=[_serialize_faq(f) for f in faqs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    
    return response

@router.post("/")
def add_faq(req: FAQCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Add a new FAQ."""
    faq = FAQ(user_id=user.id, question=req.question, answer=req.answer, category=req.category)
    db.add(faq)
    db.flush()
    db.commit()
    db.refresh(faq)
    rebuild_user_vector_db(user.id, db)
    return success_response(data=_serialize_faq(faq).dict(), message="FAQ added successfully")

@router.put("/{faq_id}")
def update_faq(faq_id: int, req: FAQUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Update an existing FAQ."""
    faq = db.query(FAQ).filter(FAQ.id == faq_id, FAQ.user_id == user.id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    if req.question is not None:
        faq.question = req.question
    if req.answer is not None:
        faq.answer = req.answer
    if req.category is not None:
        faq.category = req.category

    db.flush()
    db.commit()
    db.refresh(faq)
    rebuild_user_vector_db(user.id, db)
    return success_response(data=_serialize_faq(faq).dict(), message="FAQ updated successfully")

@router.delete("/all")
def delete_all_faqs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Delete ALL FAQs for the current user."""
    deleted_count = db.query(FAQ).filter(FAQ.user_id == user.id).count()
    db.query(FAQ).filter(FAQ.user_id == user.id).delete(synchronize_session=False)
    db.flush()
    db.commit()
    rebuild_user_vector_db(user.id, db)
    return success_response(
        data={"deleted": deleted_count},
        message=f"All {deleted_count} FAQs deleted successfully"
    )

@router.delete("/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Delete a single FAQ."""
    faq = db.query(FAQ).filter(FAQ.id == faq_id, FAQ.user_id == user.id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    db.delete(faq)
    db.flush()
    db.commit()

    rebuild_user_vector_db(user.id, db)
    return success_response(data={"id": faq_id}, message="FAQ deleted successfully")