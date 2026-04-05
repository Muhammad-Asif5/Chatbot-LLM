from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.database import get_db
from src.models import User, ChatLog
from src.inference import query as run_query

router = APIRouter(prefix="/widget", tags=["Widget"])

class WidgetQueryRequest(BaseModel):
    owner_id: str
    question: str
    language: str = "en"

@router.post("/query")
def widget_query(req: WidgetQueryRequest, db: Session = Depends(get_db)):
    """
    Public endpoint — website embed ke liye.
    owner_id se user validate karo aur answer do.
    """
    user = db.query(User).filter(User.id == req.owner_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid owner_id")

    result = run_query(
        user_id    = req.owner_id,
        user_input = req.question,
        lang       = req.language
    )

    # Chat log save karo
    log = ChatLog(
        user_id  = req.owner_id,
        question = req.question,
        answer   = result["answer"],
        source   = result["source"],
        language = result["language"]
    )
    db.add(log)
    db.commit()

    return result