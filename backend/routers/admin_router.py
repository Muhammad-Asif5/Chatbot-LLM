"""
Admin Router — full user management + platform stats.
All endpoints require is_admin=True on the JWT owner.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr
from typing import Optional
from src.database import get_db
from src.models import User, FAQ, Document, ChatLog, KnowledgeBase
from src.dependencies import get_admin_user
from src.auth import hash_password
from core.response import success_response

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── SERIALIZERS ───────────────────────────────────────────
def _serialize_user(u: User, db: Session) -> dict:
    return {
        "id":         u.id,
        "name":       u.name,
        "email":      u.email,
        "plan":       u.plan,
        "is_active":  u.is_active,
        "is_admin":   u.is_admin,
        "created_at": str(u.created_at),
        "stats": {
            "faqs":      db.query(FAQ).filter(FAQ.user_id == u.id).count(),
            "documents": db.query(Document).filter(Document.user_id == u.id).count(),
            "chats":     db.query(ChatLog).filter(ChatLog.user_id == u.id).count(),
            "kb":        db.query(KnowledgeBase).filter(KnowledgeBase.user_id == u.id).count(),
        }
    }


# ── SCHEMAS ───────────────────────────────────────────────
class UserCreateRequest(BaseModel):
    name:     str
    email:    EmailStr
    password: str
    plan:     Optional[str] = "free"
    is_admin: Optional[bool] = False

class UserUpdateRequest(BaseModel):
    name:      Optional[str]  = None
    email:     Optional[EmailStr] = None
    password:  Optional[str]  = None
    plan:      Optional[str]  = None
    is_active: Optional[bool] = None
    is_admin:  Optional[bool] = None


# ── PLATFORM OVERVIEW ─────────────────────────────────────
@router.get("/stats")
def get_platform_stats(
    db:    Session = Depends(get_db),
    admin: User    = Depends(get_admin_user)
):
    """High-level platform stats for the admin dashboard."""
    total_users    = db.query(User).count()
    active_users   = db.query(User).filter(User.is_active == True).count()
    inactive_users = total_users - active_users
    total_faqs     = db.query(FAQ).count()
    total_docs     = db.query(Document).count()
    total_chats    = db.query(ChatLog).count()
    total_kb       = db.query(KnowledgeBase).count()

    # Top 5 users by chat volume
    top_users = (
        db.query(User.id, User.name, User.email, func.count(ChatLog.id).label("chat_count"))
        .outerjoin(ChatLog, ChatLog.user_id == User.id)
        .group_by(User.id)
        .order_by(func.count(ChatLog.id).desc())
        .limit(5)
        .all()
    )

    # Recent 10 chat logs across all users
    recent_chats = (
        db.query(ChatLog, User.name, User.email)
        .join(User, User.id == ChatLog.user_id)
        .order_by(ChatLog.created_at.desc())
        .limit(10)
        .all()
    )

    return success_response(data={
        "overview": {
            "total_users":    total_users,
            "active_users":   active_users,
            "inactive_users": inactive_users,
            "total_faqs":     total_faqs,
            "total_documents":total_docs,
            "total_chats":    total_chats,
            "total_kb":       total_kb,
        },
        "top_users": [
            {"id": u.id, "name": u.name, "email": u.email, "chat_count": u.chat_count}
            for u in top_users
        ],
        "recent_chats": [
            {
                "id":         c.ChatLog.id,
                "user_name":  c.name,
                "user_email": c.email,
                "question":   c.ChatLog.question,
                "answer":     c.ChatLog.answer,
                "source":     c.ChatLog.source,
                "language":   c.ChatLog.language,
                "created_at": str(c.ChatLog.created_at),
            }
            for c in recent_chats
        ]
    })


# ── LIST ALL USERS ────────────────────────────────────────
@router.get("/users")
def list_users(
    db:    Session = Depends(get_db),
    admin: User    = Depends(get_admin_user)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return success_response(
        data=[_serialize_user(u, db) for u in users],
        message=f"{len(users)} users found"
    )


# ── GET SINGLE USER ───────────────────────────────────────
@router.get("/users/{user_id}")
def get_user(
    user_id: str,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return success_response(data=_serialize_user(user, db))


# ── CREATE USER ───────────────────────────────────────────
@router.post("/users")
def create_user(
    req:   UserCreateRequest,
    db:    Session = Depends(get_db),
    admin: User    = Depends(get_admin_user)
):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        name     = req.name.strip(),
        email    = req.email,
        password = hash_password(req.password),
        plan     = req.plan or "free",
        is_admin = req.is_admin or False,
    )
    db.add(user)
    db.flush()
    db.commit()
    db.refresh(user)
    return success_response(
        data=_serialize_user(user, db),
        message="User created successfully",
        status_code=status.HTTP_201_CREATED
    )


# ── UPDATE USER ───────────────────────────────────────────
@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    req:     UserUpdateRequest,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from removing their own admin rights
    if user_id == admin.id and req.is_admin is False:
        raise HTTPException(status_code=400, detail="You cannot remove your own admin rights")

    if req.name      is not None: user.name      = req.name.strip()
    if req.email     is not None:
        existing = db.query(User).filter(User.email == req.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = req.email
    if req.password  is not None: user.password  = hash_password(req.password)
    if req.plan      is not None: user.plan       = req.plan
    if req.is_active is not None: user.is_active  = req.is_active
    if req.is_admin  is not None: user.is_admin   = req.is_admin

    db.flush()
    db.commit()
    db.refresh(user)
    return success_response(
        data=_serialize_user(user, db),
        message="User updated successfully"
    )


# ── TOGGLE ACTIVE STATUS ──────────────────────────────────
@router.patch("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: str,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    state = "activated" if user.is_active else "deactivated"
    return success_response(
        data={"id": user.id, "is_active": user.is_active},
        message=f"User {state} successfully"
    )


# ── DELETE USER ───────────────────────────────────────────
@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    name = user.name
    db.delete(user)
    db.flush()
    db.commit()
    return success_response(
        data={"id": user_id},
        message=f"User '{name}' deleted successfully"
    )


# ── USER DETAIL: FAQs ─────────────────────────────────────
@router.get("/users/{user_id}/faqs")
def get_user_faqs(
    user_id: str,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    faqs = db.query(FAQ).filter(FAQ.user_id == user_id).all()
    return success_response(data=[
        {"id": f.id, "question": f.question, "answer": f.answer,
         "category": f.category, "created_at": str(f.created_at)}
        for f in faqs
    ])


# ── USER DETAIL: Documents ────────────────────────────────
@router.get("/users/{user_id}/documents")
def get_user_documents(
    user_id: str,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    docs = db.query(Document).filter(Document.user_id == user_id).all()
    return success_response(data=[
        {"id": d.id, "filename": d.filename, "created_at": str(d.created_at)}
        for d in docs
    ])


# ── USER DETAIL: Chat Logs ────────────────────────────────
@router.get("/users/{user_id}/chats")
def get_user_chats(
    user_id: str,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    chats = (
        db.query(ChatLog)
        .filter(ChatLog.user_id == user_id)
        .order_by(ChatLog.created_at.desc())
        .limit(50)
        .all()
    )
    return success_response(data=[
        {"id": c.id, "question": c.question, "answer": c.answer,
         "source": c.source, "language": c.language, "created_at": str(c.created_at)}
        for c in chats
    ])