"""
Admin Router — full user management + platform stats.
All endpoints require is_admin=True on the JWT owner.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Platform overview stats (lightweight, fast response).
    No pagination or heavy aggregations inside this endpoint.
    """

    # ─────────────────────────────
    # USERS
    # ─────────────────────────────
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    inactive_users = total_users - active_users

    # ─────────────────────────────
    # CONTENT STATS
    # ─────────────────────────────
    total_faqs = db.query(FAQ).count()
    total_documents = db.query(Document).count()
    total_chats = db.query(ChatLog).count()
    total_kb = db.query(KnowledgeBase).count()

    # ─────────────────────────────
    # OPTIONAL: small top summary (NOT full pagination)
    # ─────────────────────────────
    top_users_preview = (
        db.query(
            User.id,
            User.name,
            User.email,
            func.count(ChatLog.id).label("chat_count")
        )
        .outerjoin(ChatLog, ChatLog.user_id == User.id)
        .group_by(User.id)
        .order_by(func.count(ChatLog.id).desc())
        .limit(5)   # only preview (dashboard widget)
        .all()
    )

    # ─────────────────────────────
    # OPTIONAL: latest 5 chats preview
    # ─────────────────────────────
    recent_chats_preview = (
        db.query(
            ChatLog.id,
            ChatLog.question,
            ChatLog.answer,
            ChatLog.source,
            ChatLog.language,
            ChatLog.created_at,
            User.name.label("user_name")
        )
        .join(User, User.id == ChatLog.user_id)
        .order_by(ChatLog.created_at.desc())
        .limit(5)
        .all()
    )

    # ─────────────────────────────
    # RESPONSE
    # ─────────────────────────────
    return success_response(data={
        "overview": {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "total_faqs": total_faqs,
            "total_documents": total_documents,
            "total_chats": total_chats,
            "total_kb": total_kb,
        },

        # small dashboard preview only
        "top_users_preview": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "chat_count": u.chat_count
            }
            for u in top_users_preview
        ],

        "recent_chats_preview": [
            {
                "id": c.id,
                "user_name": c.user_name,
                "question": c.question,
                "answer": c.answer,
                "source": c.source,
                "language": c.language,
                "created_at": str(c.created_at),
            }
            for c in recent_chats_preview
        ],
    })

@router.get("/recent-conversations-scroll")
def get_recent_conversations_scroll(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
    recent_page: int = Query(1, ge=1),
    recent_page_size: int = Query(10, ge=1, le=100),
):

    print(f"Fetching recent conversations - page: {recent_page}, page_size: {recent_page_size}")
    # ─────────────────────────────
    # RECENT CHATS ONLY
    # ─────────────────────────────
    recent_query = (
        db.query(
            ChatLog.id,
            ChatLog.question,
            ChatLog.answer, 
            ChatLog.source,
            ChatLog.language,
            ChatLog.created_at,
            User.name.label("user_name")
        )
        .join(User, User.id == ChatLog.user_id)
        .order_by(ChatLog.created_at.desc())
    )

    recent_total = recent_query.count()

    recent_chats = (
        recent_query
        .offset((recent_page - 1) * recent_page_size)
        .limit(recent_page_size)
        .all()
    )

    # ─────────────────────────────
    # RESPONSE (MINIMAL + CLEAN)
    # ─────────────────────────────
    return success_response(data={

        "recent_chats": [
            {
                "id": c.id,
                "user_name": c.user_name,
                "question": c.question,
                "answer": c.answer,
                "source": c.source,
                "language": c.language,
                "created_at": str(c.created_at),
            }
            for c in recent_chats
        ],

        "pagination": {
            "page": recent_page,
            "page_size": recent_page_size,
            "total": recent_total,
            "has_more": (recent_page * recent_page_size) < recent_total
        }
    })

@router.get("/top-users")
def get_top_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),

    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    print(f"Fetching top users - page: {page}, page_size: {page_size}")

    base_query = (
        db.query(
            User.id,
            User.name,
            User.email,
            func.count(ChatLog.id).label("chat_count")
        )
        .outerjoin(ChatLog, ChatLog.user_id == User.id)
        .group_by(User.id)
    )

    # ✅ Correct total count using subquery
    total = db.query(func.count()).select_from(base_query.subquery()).scalar()

    # ✅ Apply ordering AFTER count (important)
    users = (
        base_query
        .order_by(func.count(ChatLog.id).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return success_response(data={
        "top_users": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "chat_count": u.chat_count
            }
            for u in users
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": (page * page_size) < total
        }
    })

# ── LIST ALL USERS ────────────────────────────────────────
@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),

    # ✅ NEW PARAMS
    search: str = Query(None, description="Search by name or email"),
    filter: str = Query("all", description="Filter: all | active | inactive | admin"),

    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    # ─────────────── Base Query ───────────────
    query = db.query(User)

    # ─────────────── SEARCH ───────────────
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )

    # ─────────────── FILTER ───────────────
    if filter == "active":
        query = query.filter(User.is_active == True)
    elif filter == "inactive":
        query = query.filter(User.is_active == False)
    elif filter == "admin":
        query = query.filter(User.is_admin == True)

    # ─────────────── TOTAL COUNT (AFTER FILTERS) ───────────────
    total_users = query.count()

    # ─────────────── PAGINATION ───────────────
    offset = (page - 1) * page_size

    users = (
        query
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = (total_users + page_size - 1) // page_size

    # ─────────────── RESPONSE ───────────────
    return success_response(
        data={
            "items": [_serialize_user(u, db) for u in users],
            "total": total_users,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        },
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