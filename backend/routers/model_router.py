# routers/model_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal
from src.database import get_db
from src.models import User
from src.dependencies import get_current_user
from src.model_config import UserModelConfig
from core.response import success_response
from typing import Literal

router = APIRouter(prefix="/model", tags=["Model Config"])

VALID_MODELS = {"flan-t5-large", "mistral-7b", "llama-3-8b"}

class ModelSelectRequest(BaseModel):
    model_name: Literal["flan-t5-large", "phi-3-mini", "gemma-2b", "mistral-7b", "llama-3-8b"]
    
@router.get("/")
def get_model(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cfg = db.query(UserModelConfig).filter(UserModelConfig.user_id == user.id).first()
    return success_response(data={"model": cfg.model_name if cfg else "flan-t5-large"})

@router.post("/")
def set_model(req: ModelSelectRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cfg = db.query(UserModelConfig).filter(UserModelConfig.user_id == user.id).first()
    if cfg:
        cfg.model_name = req.model_name
    else:
        cfg = UserModelConfig(user_id=user.id, model_name=req.model_name)
        db.add(cfg)
    db.commit()
    return success_response(data={"model": req.model_name}, message=f"Model switched to {req.model_name}")