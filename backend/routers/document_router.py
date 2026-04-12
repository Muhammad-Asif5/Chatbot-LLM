import os
import re
import csv
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Document, FAQ, KnowledgeBase, User
from src.dependencies import get_current_user
from src.embedding import build_vector_db
from core.response import success_response, error_response

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"
SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".xlsx", ".csv"}

# ── REBUILD HELPER ────────────────────────────────────────
def rebuild_user_vector_db(user_id: str, db: Session):
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

# ── Q&A PATTERN DETECTOR ──────────────────────────────────
def _detect_qa_pairs(text: str, filename: str) -> list[dict]:
    """
    Auto-detect Q&A pairs from plain text extracted from any file type.

    Supports three formats:

    Format 1 — blank-line separated blocks (most common .txt uploads):
        How to request a refund?
        Please email us at support@...

        How long does it take?
        Refund requests are processed within ...

    Format 2 — explicit Q:/A: labels:
        Q: How to request a refund?
        A: Please email us at ...

    Format 3 — numbered questions:
        1. How to request a refund?
           Please email us at ...

    Returns a list of {"question", "answer"} dicts, or [] if no
    clear Q&A pattern is found (caller falls back to document mode).
    """
    pairs = []

    # ── Format 2: Q:/A: labels ────────────────────────────
    qa_label_pattern = re.compile(
        r'(?:^|\n)\s*[Qq][:\.]?\s+(.+?)\s*\n\s*[Aa][:\.]?\s+(.+?)(?=\n\s*[Qq][:\.]|\Z)',
        re.DOTALL
    )
    matches = qa_label_pattern.findall(text)
    if matches:
        for q, a in matches:
            q = q.strip()
            a = a.strip()
            if q and a and len(q) > 4 and len(a) > 4:
                pairs.append({"question": q, "answer": a})
        if pairs:
            print(f"[QA Detect] '{filename}' — Format 2 (Q:/A:) → {len(pairs)} pairs")
            return pairs

    # ── Format 1 & 3: blank-line block detection ──────────
    blocks = [b.strip() for b in re.split(r'\n\s*\n', text) if b.strip()]

    # Fast-exit: if the text has zero '?' AND no numbered lines it is
    # almost certainly narrative prose — skip block detection entirely
    has_question_marks = "?" in text
    has_numbered_lines = bool(re.search(r'^\d+[\.\)]\s+', text, re.MULTILINE))
    if not has_question_marks and not has_numbered_lines:
        print(f"[QA Detect] '{filename}' — no '?' or numbering found → document mode")
        return []

    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            continue

        first_line  = lines[0]
        answer_text = " ".join(lines[1:]).strip()

        # Strip leading numbering (e.g. "1. " or "1) ")
        clean_q = re.sub(r'^\d+[\.\)]\s+', '', first_line).strip()

        # Strict rule: first line must end with '?' OR be numbered.
        # Removed the length heuristic — it caused false positives on narrative text.
        is_question = (
            first_line.endswith("?")
            or re.match(r'^\d+[\.\)]\s+', first_line)
        )

        if is_question and clean_q and answer_text and len(answer_text) > 4:
            pairs.append({"question": clean_q, "answer": answer_text})

    # Confidence gate: ≥50% of blocks must look like Q&A
    if pairs and len(pairs) >= max(1, len(blocks) * 0.5):
        print(f"[QA Detect] '{filename}' — Format 1/3 (block) → {len(pairs)} pairs from {len(blocks)} blocks")
        return pairs

    print(f"[QA Detect] '{filename}' — no Q&A pattern detected → document mode")
    return []


# ── XLSX PARSER ───────────────────────────────────────────
def _parse_xlsx(file_path: str) -> tuple[str, list[dict] | str]:
    """
    Returns ("faq", [rows]) when file has 'question'+'answer' columns.
    Returns ("document", text_str) otherwise.
    """
    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(status_code=500, detail="pandas not installed.")

    try:
        df = pd.read_excel(file_path, engine="openpyxl", dtype=str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"XLSX parse error: {e}")

    # ✅ Strip BOM, invisible unicode, whitespace and lowercase — all in one pass
    df.columns = [
        c.encode("ascii", "ignore").decode().strip().lower()
        if isinstance(c, str) else str(c).strip().lower()
        for c in df.columns
    ]
    df.dropna(how="all", inplace=True)
    df.fillna("", inplace=True)  # ✅ Turn all NaN cells into empty strings

    if "question" in df.columns and "answer" in df.columns:
        rows = []
        for _, row in df.iterrows():
            question = str(row.get("question", "")).strip()
            answer   = str(row.get("answer",   "")).strip()
            category = str(row.get("category", "")).strip()
            status   = str(row.get("status",   "")).strip().lower()

            # ✅ Skip empty rows
            if not question or not answer:
                continue
            # ✅ Skip header-repeat rows and pandas NaN artifacts
            if question.lower() in {"question", "nan"} or answer.lower() in {"answer", "nan"}:
                continue
            # ✅ Only skip rows explicitly marked inactive/disabled/no/false/0
            #    blank status (most xlsx files have no status column) = allowed
            if status and status not in {"active", "nan", "yes", "true", "1", ""}:
                continue
            # ✅ Normalize empty/nan category to "general"
            if not category or category.lower() in {"nan", "none", "general"}:
                category = "general"

            rows.append({"question": question, "answer": answer, "category": category})
        return "faq", rows
    else:
        lines = []
        for _, row in df.iterrows():
            parts = [f"{col}: {str(val).strip()}" for col, val in row.items()
                     if str(val).strip() and str(val).strip().lower() != "nan"]
            if parts:
                lines.append("\n".join(parts))
        return "document", "\n\n".join(lines)


# ── CSV PARSER ────────────────────────────────────────────
def _parse_csv(file_path: str) -> tuple[str, list[dict] | str]:
    """
    Returns ("faq", [rows]) when file has 'question'+'answer' columns.
    Returns ("document", text_str) otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            sample = f.read(2048)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            reader   = csv.DictReader(f, dialect=dialect)
            raw_rows = list(reader)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    if not raw_rows:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    norm_rows = [{k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
                 for row in raw_rows]
    cols = set(norm_rows[0].keys())

    if "question" in cols and "answer" in cols:
        faq_rows = []
        for row in norm_rows:
            question = row.get("question", "").strip()
            answer   = row.get("answer",   "").strip()
            category = row.get("category", "general").strip()
            status   = row.get("status",   "active").strip().lower()
            if not question or not answer:
                continue
            if question.lower() in {"question"} or answer.lower() in {"answer"}:
                continue
            if status not in {"active", ""}:
                continue
            faq_rows.append({"question": question, "answer": answer, "category": category or "general"})
        return "faq", faq_rows
    else:
        lines = []
        for row in norm_rows:
            parts = [f"{col}: {val}" for col, val in row.items() if val]
            if parts:
                lines.append("\n".join(parts))
        return "document", "\n\n".join(lines)


# ── BULK INSERT FAQs ──────────────────────────────────────
def _bulk_insert_faqs(faq_rows: list[dict], user_id: str, filename: str, db: Session) -> dict:
    """Insert FAQ rows, skipping exact-question duplicates. Returns stats."""
    inserted        = 0
    skipped         = 0
    # Derive a clean category name from the filename as fallback
    default_category = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()

    for row in faq_rows:
        exists = db.query(FAQ).filter(
            FAQ.user_id  == user_id,
            FAQ.question == row["question"]
        ).first()
        if exists:
            skipped += 1
            continue

        # Use file-derived category if row category is blank/generic
        category = row.get("category", "").strip()
        if not category or category.lower() == "general":
            category = default_category

        faq = FAQ(
            user_id  = user_id,
            question = row["question"],
            answer   = row["answer"],
            category = category,
        )
        db.add(faq)
        inserted += 1

    db.flush()
    db.commit()
    return {"imported": inserted, "skipped": skipped, "total": len(faq_rows)}


# ── GET all documents ─────────────────────────────────────
@router.get("/")
def get_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.user_id == user.id).all()
    serialized = [
        {
            "id":         d.id,
            "filename":   d.filename,
            "content":    d.content,
            "user_id":    d.user_id,
            "created_at": str(d.created_at),
        }
        for d in docs
    ]
    return success_response(data=serialized, message="Documents fetched successfully")


# ── POST upload ───────────────────────────────────────────
@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    db:   Session    = Depends(get_db),
    user: User       = Depends(get_current_user)
):
    filename = file.filename or ""
    ext      = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # ── Save raw file to disk ──────────────────────────────
    user_dir  = os.path.join(UPLOAD_DIR, user.id)
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, filename)

    # ✅ Use await file.read() — shutil.copyfileobj reads synchronously from
    # the async stream and can produce a truncated file for binary formats
    # like xlsx, which then silently fails to parse correctly.
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # ── Extract content & decide mode ─────────────────────
    raw_text    = ""
    faq_rows    = []
    import_mode = "document"

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        detected = _detect_qa_pairs(raw_text, filename)
        if detected:
            faq_rows    = detected
            import_mode = "faq"

    elif ext == ".pdf":
        try:
            import fitz
            doc      = fitz.open(file_path)
            raw_text = "\n".join([p.get_text() for p in doc])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF error: {e}")
        detected = _detect_qa_pairs(raw_text, filename)
        if detected:
            faq_rows    = detected
            import_mode = "faq"

    elif ext == ".docx":
        try:
            from docx import Document as DocxDocument
            doc      = DocxDocument(file_path)
            raw_text = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DOCX error: {e}")
        detected = _detect_qa_pairs(raw_text, filename)
        if detected:
            faq_rows    = detected
            import_mode = "faq"

    elif ext == ".xlsx":
        import_mode, parsed = _parse_xlsx(file_path)
        if import_mode == "faq":
            faq_rows = parsed
        else:
            raw_text = parsed

    elif ext == ".csv":
        import_mode, parsed = _parse_csv(file_path)
        if import_mode == "faq":
            faq_rows = parsed
        else:
            raw_text = parsed

    # ── FAQ import path ────────────────────────────────────
    if import_mode == "faq" and faq_rows:
        stats = _bulk_insert_faqs(faq_rows, user.id, filename, db)

        # ✅ Also save a Document record so the file appears in the Documents list
        existing_doc = db.query(Document).filter(
            Document.user_id == user.id,
            Document.filename == filename
        ).first()
        if not existing_doc:
            summary = (
                f"[FAQ Import] {stats['imported']} FAQs imported, "
                f"{stats['skipped']} skipped from '{filename}'"
            )
            doc = Document(user_id=user.id, filename=filename, content=summary)
            db.add(doc)
            db.flush()
            db.commit()
            db.refresh(doc)
            doc_id = doc.id
        else:
            doc_id = existing_doc.id

        rebuild_user_vector_db(user.id, db)
        return success_response(
            data={
                "id":       doc_id,
                "filename": filename,
            "imported": stats["imported"],
            "skipped":  stats["skipped"],
            "total":    stats["total"],
            "mode":     "faq_import",
            },
            message=f"FAQ import successful from '{filename}'",
            status_code=status.HTTP_201_CREATED,
        )

    # ── Document import path (fallback) ───────────────────
    doc = Document(user_id=user.id, filename=filename, content=raw_text)
    db.add(doc)
    db.flush()
    db.commit()
    db.refresh(doc)

    rebuild_user_vector_db(user.id, db)
    return success_response(
        data={"id": doc.id, "filename": doc.filename, "created_at": str(doc.created_at)},
        message="Document uploaded successfully",
        status_code=status.HTTP_201_CREATED
    )


# ── DELETE document ───────────────────────────────────────
@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    db:     Session = Depends(get_db),
    user:   User    = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = os.path.join(UPLOAD_DIR, user.id, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"[Document] File deleted: {file_path}")

    filename = doc.filename
    db.delete(doc)
    db.flush()
    db.commit()

    rebuild_user_vector_db(user.id, db)
    return {"message": f"{filename} deleted successfully", "id": doc_id}
