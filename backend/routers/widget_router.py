from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from src.database import get_db
from src.models import User, ChatLog
from src.inference import query as run_query, summarize
from core.response import success_response

router = APIRouter(prefix="/widget", tags=["Widget"])

class SummarizeRequest(BaseModel):
    text: str

class WidgetQueryRequest(BaseModel):
    owner_id: str
    question: str
    # ✅ FIXED: "en" → "auto"
    # Old default "en" bypassed ALL language detection in inference.py
    # "auto" tells the pipeline to detect language from the message itself
    language: Optional[str] = "en"

@router.post("/query")
def widget_query(req: WidgetQueryRequest, db: Session = Depends(get_db)):
    """
    Public endpoint — website embed ke liye.
    owner_id se user validate karo aur answer do.
    """
    user = db.query(User).filter(User.id == req.owner_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {req.owner_id} not found."
        )

    # ✅ Normalize: treat "en" sent from frontend as "auto" too
    # Some frontends hardcode language="en" — this ensures detection still runs
    target_lang = req.language if req.language else "auto"

    result = run_query(
        user_id    = req.owner_id,
        user_input = req.question,
        target_lang       = target_lang
    )
    
    print(f"\n\n📝Step Final - Query result: {result}")

    log = ChatLog(
        user_id  = req.owner_id,
        question = req.question,
        answer   = result["answer"],
        source   = result["source"],
        language = result["language"]
    )
    db.add(log)
    db.commit()

    return success_response(
        data=result,
        message="Query processed successfully",
        status_code=status.HTTP_200_OK
    )

@router.post("/summarize")
def summarize_text(req: SummarizeRequest):
    if not req.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty"
        )
    try:
        summary = summarize(req.text)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )