from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.database import get_db
from src.models import KnowledgeBase, FAQ, Document, User
from src.dependencies import get_current_user
from src.embedding import build_vector_db
from core.response import success_response   # ← consistent with all other routers

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

def rebuild_user_vector_db(user_id: str, db: Session):
    faqs = db.query(FAQ).filter(FAQ.user_id == user_id).all()
    docs = db.query(Document).filter(Document.user_id == user_id).all()
    docs = [d for d in docs if d.content and len(d.content.strip()) > 0]
    kbs  = db.query(KnowledgeBase).filter(KnowledgeBase.user_id == user_id).all()

    build_vector_db(
        user_id        = user_id,
        faqs           = [{"question": f.question, "answer": f.answer, "category": f.category} for f in faqs],
        documents      = [{"filename": d.filename, "content": d.content} for d in docs],
        knowledge_base = [{"title": k.title, "content": k.content} for k in kbs],
    )


# ── Serializer ────────────────────────────────────────────
def _serialize(kb: KnowledgeBase) -> dict:
    return {
        "id":         kb.id,
        "user_id":    kb.user_id,
        "title":      kb.title,
        "content":    kb.content,
        "created_at": str(kb.created_at),
        "updated_at": str(kb.updated_at),
    }

# ── Schemas ───────────────────────────────────────────────
class KBCreate(BaseModel):
    title:   str
    content: str

class KBUpdate(BaseModel):
    title:   Optional[str] = None
    content: Optional[str] = None

@router.get("/")
def get_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.query(KnowledgeBase).filter(KnowledgeBase.user_id == user.id).all()
    return success_response(data=items, message=f"Retrieved {len(items)} articles successfully")


@router.get("/{kb_id}")
def get_one(
    kb_id: int,
    db:    Session = Depends(get_db),
    user:  User    = Depends(get_current_user),
):
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == user.id,
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Article not found")
    return success_response(data=_serialize(kb))


@router.post("/")
def create_kb(
    req:  KBCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    if not req.title.strip() or not req.content.strip():
        raise HTTPException(status_code=400, detail="Title and content are required")

    kb = KnowledgeBase(
        user_id = user.id,
        title   = req.title.strip(),
        content = req.content.strip(),
    )
    db.add(kb)
    db.flush()
    db.commit()
    db.refresh(kb)
    rebuild_user_vector_db(user.id, db)
    return success_response(data=_serialize(kb), message="Article created successfully")


@router.put("/{kb_id}")
def update_kb(
    kb_id: int,
    req:   KBUpdate,
    db:    Session = Depends(get_db),
    user:  User    = Depends(get_current_user),
):
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == user.id,
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Article not found")

    if req.title   is not None: kb.title   = req.title.strip()
    if req.content is not None: kb.content = req.content.strip()
    kb.updated_at = datetime.utcnow()
    db.flush()
    db.commit()
    db.refresh(kb)
    rebuild_user_vector_db(user.id, db)
    return success_response(data=_serialize(kb), message="Article updated successfully")


@router.delete("/{kb_id}")
def delete_kb(kb_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == user.id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Not found")

    title = kb.title   # ✅ Save before delete
    db.delete(kb)
    db.flush()    # ✅
    db.commit()

    rebuild_user_vector_db(user.id, db)
    return success_response(data={"id": kb_id}, message=f"'{title}' deleted successfully")