import os
import pandas as pd
from sqlalchemy import create_engine, text
from src.utils import clean_text

# ── CONFIG ──────────────────────────────────────────────
FAQ_CSV_PATH = "data/faqs.csv"
DOCUMENTS_DIR = "data/documents/"
DB_URL = os.getenv("DATABASE_URL", "sqlite:///data/support.db")

engine = create_engine(DB_URL)

# ── FAQ LOADER ───────────────────────────────────────────
def load_faqs(csv_path: str = FAQ_CSV_PATH) -> pd.DataFrame:
    """Load FAQs from CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"FAQ CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df["question"] = df["question"].apply(clean_text)
    df["answer"]   = df["answer"].apply(clean_text)
    print(f"[DataLoader] Loaded {len(df)} FAQs from CSV.")
    return df

# ── SQL DB LOADER ────────────────────────────────────────
def init_faq_table(df: pd.DataFrame):
    """Push FAQs from CSV into SQL database."""
    df.to_sql("faqs", con=engine, if_exists="replace", index=False)
    print("[DataLoader] FAQs saved to SQL database.")

def search_faqs_sql(query: str, top_k: int = 3) -> list[dict]:
    """
    Improved SQL search:
    - Priority 1: Full phrase match  (score = 100)
    - Priority 2: Keyword hit count  (score += 1 per keyword)
    - Stopwords filtered before keyword search
    - Returns top_k results sorted by score descending
    """
    STOPWORDS = {
        "how", "do", "i", "can", "what", "is", "the",
        "a", "an", "to", "my", "your", "we", "are",
        "does", "did", "will", "where", "when", "who",
        "no", "yes", "any"                              # ← "no" bhi stopword banao
    }

    query_clean = query.lower().strip()
    keywords = [w for w in query_clean.split() if w not in STOPWORDS]

    # ── Agar meaningful keywords hi nahi hain → return empty ──
    if not keywords:
        return []

    results = {}  # id -> {row_data, score}

    with engine.connect() as conn:

        # ── Priority 1: Full phrase match ────────────────
        phrase_sql = text("""
            SELECT id, question, answer, category
            FROM faqs
            WHERE LOWER(question) LIKE :phrase
               OR LOWER(answer)   LIKE :phrase
            LIMIT :limit
        """)
        rows = conn.execute(phrase_sql, {
            "phrase": f"%{query_clean}%",
            "limit": top_k
        }).fetchall()

        for row in rows:
            results[row[0]] = {
                "id": row[0], 
                "question": row[1],
                "answer": row[2], 
                "category": row[3],
                "source": "sql", 
                "score":    100          # highest priority
            }

        # ── Priority 2: Per-keyword scoring ──────────────
        for keyword in keywords:
            kw_sql = text("""
                SELECT id, question, answer, category
                FROM faqs
                WHERE LOWER(question) LIKE :kw
                   OR LOWER(answer)   LIKE :kw
                LIMIT 10
            """)
            rows = conn.execute(kw_sql, {"kw": f"%{keyword}%"}).fetchall()

            for row in rows:
                if row[0] in results:
                    results[row[0]]["score"] += 1   # reward multiple keyword hits
                else:
                    results[row[0]] = {
                        "id":       row[0],
                        "question": row[1],
                        "answer":   row[2],
                        "category": row[3],
                        "source":   "sql",
                        "score":    1
                    }

    # ── Minimum score filter — score 2+ hona chahiye ────────
    filtered = {k: v for k, v in results.items() if v["score"] >= 2}

    if not filtered:
        return []   # ← Koi strong match nahi → not_found trigger hoga

    sorted_results = sorted(filtered.values(), key=lambda x: x["score"], reverse=True)
    for r in sorted_results:
        r.pop("score", None)

    return sorted_results[:top_k]

# ── DOCUMENT LOADER ──────────────────────────────────────
def load_documents(docs_dir: str = DOCUMENTS_DIR) -> list[dict]:
    """Load all .txt, .pdf, .docx documents from folder."""
    docs = []
    if not os.path.exists(docs_dir):
        print(f"[DataLoader] Documents folder not found: {docs_dir}")
        return docs

    for filename in os.listdir(docs_dir):
        filepath = os.path.join(docs_dir, filename)
        content  = ""

        if filename.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

        elif filename.endswith(".pdf"):
            try:
                import fitz  # PyMuPDF
                doc     = fitz.open(filepath)
                content = "\n".join([page.get_text() for page in doc])
            except ImportError:
                print("[DataLoader] Install PyMuPDF: pip install pymupdf")

        elif filename.endswith(".docx"):
            try:
                from docx import Document
                if not os.path.exists(filepath):  # ← yeh check add karo
                    print(f"[DataLoader] File not found, skipping: {filename}")
                    continue
                doc     = Document(filepath)
                content = "\n".join([p.text for p in doc.paragraphs])
            except Exception as e:
                print(f"[DataLoader] Error loading {filename}: {e}")
                continue

        if content:
            # clean_text mat lagao yahan — embedding.py mein lagega
            docs.append({"filename": filename, "content": content})
            print(f"[DataLoader] Loaded document: {filename}")

    return docs