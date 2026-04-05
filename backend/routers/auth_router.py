from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from src.database import get_db
from src.models import User
from src.auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["Auth"])

class RegisterRequest(BaseModel):
    name:     str
    email:    EmailStr
    password: str

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

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
    return {"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token({"sub": user.id})
    return {"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}

@router.get("/me")
def me(db: Session = Depends(get_db), current_user: User = Depends(lambda: None)):
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email}