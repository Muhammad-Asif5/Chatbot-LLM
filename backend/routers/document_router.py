import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Document, FAQ, KnowledgeBase, User
from src.dependencies import get_current_user
from src.embedding import build_vector_db

router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"

def rebuild_user_vector_db(user_id: str, db: Session):
    """Helper — rebuild vector DB after FAQ changes."""
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
def get_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Document).filter(Document.user_id == user.id).all()

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    db:   Session    = Depends(get_db),
    user: User       = Depends(get_current_user)
):
    user_dir = os.path.join(UPLOAD_DIR, user.id)
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Content read karo
    content = ""
    if file.filename.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    elif file.filename.endswith(".pdf"):
        try:
            import fitz
            doc     = fitz.open(file_path)
            content = "\n".join([p.get_text() for p in doc])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF error: {e}")
    elif file.filename.endswith(".docx"):
        try:
            from docx import Document as DocxDocument
            doc     = DocxDocument(file_path)
            content = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DOCX error: {e}")

    # ── DB mein save karo ────────────────────────────
    doc = Document(user_id=user.id, filename=file.filename, content=content)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # ── Vector DB rebuild karo ───────────────────────
    rebuild_user_vector_db(user.id, db)
    return doc

@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # ── Physical file bhi delete karo ────────────────
    file_path = os.path.join(UPLOAD_DIR, user.id, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"[Document] File deleted: {file_path}")

    # ── DB se delete karo ────────────────────────────
    db.delete(doc)
    db.commit()

    # ── Vector DB rebuild karo ───────────────────────
    rebuild_user_vector_db(user.id, db)

    return {"message": f"{doc.filename} deleted successfully"}