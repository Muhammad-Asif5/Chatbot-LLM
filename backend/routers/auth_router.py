from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from src.database import get_db
from src.models import User
from src.auth import hash_password, verify_password, create_token
from src.dependencies import get_current_user
from core.response import success_response

router = APIRouter(prefix="/auth", tags=["Auth"])

class RegisterRequest(BaseModel):
    name:     str
    email:    EmailStr
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

    @validator('name')
    def name_valid(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

def _user_payload(user: User) -> dict:
    return {
        "id":       user.id,
        "name":     user.name,
        "email":    user.email,
        "plan":     user.plan,
        "is_admin": user.is_admin,
    }

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name     = req.name,
        email    = req.email,
        password = hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({"sub": user.id})
    return success_response(
        data={"token": token, "user": _user_payload(user)},
        message="Registration successful"
    )

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated. Contact support.")
    token = create_token({"sub": user.id})
    return success_response(
        data={"token": token, "user": _user_payload(user)},
        message="Login successful"
    )

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return success_response(data=_user_payload(current_user))