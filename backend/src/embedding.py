import os

# ── Offline mode — SABSE PEHLE, kisi bhi import se pehle ──
os.environ["TRANSFORMERS_OFFLINE"]   = "1"
os.environ["HF_DATASETS_OFFLINE"]    = "1"
os.environ["HF_HUB_OFFLINE"]         = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import re
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.utils import clean_text

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ── Cache path directly do ───────────────────────────────
CACHE_DIR = os.path.join(
    os.path.expanduser("~"), 
    ".cache", "huggingface", "hub",
    "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2",
    "snapshots"
)

def get_model_path() -> str:
    """Cache se local model path lo."""
    if os.path.exists(CACHE_DIR):
        snapshots = os.listdir(CACHE_DIR)
        if snapshots:
            path = os.path.join(CACHE_DIR, snapshots[0])
            print(f"[Embedding] Local model found: {path}")
            return path
    print(f"[Embedding] Cache not found, using model name: {EMBED_MODEL_NAME}")
    return EMBED_MODEL_NAME
	 
MODEL_LOCAL_PATH = get_model_path()
embedder = SentenceTransformer(MODEL_LOCAL_PATH, local_files_only=True)
   
# ── BUILD VECTOR DB ──────────────────────────────────────
def get_vector_db_path(user_id: str) -> str:
    """Per user vector DB path."""
    path = f"embeddings/{user_id}"
    os.makedirs(path, exist_ok=True)
    return f"{path}/vector_db.pkl"

def build_vector_db(
    user_id:        str,
    faqs:           list[dict],
    documents:      list[dict],
    knowledge_base: list[dict] = []   # ← naya parameter
):	  
    """
    Build vector DB for a specific user.
    faqs: [{"question": ..., "answer": ..., "category": ...}]
    documents: [{"filename": ..., "content": ...}]
    """
    entries = []

    # 1. Load FAQs
    for faq in faqs:
        entries.append({
            "text":     f"{faq['question']} {faq['question']} {faq['answer']}",
            "question": faq["question"],
            "answer":   faq["answer"],
            "source":   "faq",
            "category": faq.get("category", "general")
        })

    # 2. Load Documents
    for doc in documents:
        raw_content = doc["content"]

        # ── Double newline se split ───────────────────────
        sections    = [s.strip() for s in raw_content.split('\n\n') if len(s.strip()) > 10]

        # ── Fallback: single newline ──────────────────────
        if len(sections) <= 1:
            sections = [s.strip() for s in raw_content.split('\n') if len(s.strip()) > 10]

        for section in sections:
            lines         = section.split('\n')
            question_part = lines[0].strip()
            answer_part   = ' '.join(lines[1:]).strip() if len(lines) > 1 else question_part

            entries.append({
                "text":     clean_text(section),
                "question": question_part,
                "answer":   answer_part if answer_part else question_part,
                "source":   "document",
                "category": doc["filename"]
            })

    # 3. Knowledge Base ← Naya
    for kb in knowledge_base:
        raw_content = kb["content"]

        # ── Markdown headers se split karo ───────────
        import re
        sections = re.split(r'\n(?=#{1,3} )', raw_content)
        sections = [s.strip() for s in sections if len(s.strip()) > 10]

        # ── Fallback: double newline ──────────────────
        if len(sections) <= 1:
            sections = [s.strip() for s in raw_content.split('\n\n') if len(s.strip()) > 10]

        for section in sections:
            # Markdown headers clean karo
            clean_section = re.sub(r'^#{1,3} ', '', section, flags=re.MULTILINE)
            lines         = clean_section.split('\n')
            question_part = lines[0].strip()
            answer_part   = ' '.join(lines[1:]).strip() if len(lines) > 1 else question_part

            entries.append({
                "text":     clean_text(clean_section),
                "question": question_part,
                "answer":   answer_part if answer_part else question_part,
                "source":   "knowledge_base",
                "category": kb["title"]
            })

        print(f"[Embedding] KB '{kb['title']}': {len(sections)} chunks")

    if not entries:
        print(f"[Embedding] No data for user {user_id}")
        return

    # 3. Embeddings
    texts      = [e["text"] for e in entries]
    embeddings = embedder.encode(texts, show_progress_bar=False, batch_size=32)
    embeddings = np.array(embeddings).astype("float32")

    # 4. FAISS index
    dim   = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
	 
    # 5. Save
    save_path = get_vector_db_path(user_id)
    with open(save_path, "wb") as f:
        pickle.dump({"index": index, "entries": entries}, f)

    print(f"[Embedding] User {user_id}: {len(entries)} entries saved.")

	
# ── SEARCH VECTOR DB ─────────────────────────────────────
def search_vector_db(user_id: str, query: str, top_k: int = 3) -> list[dict]:
    save_path = get_vector_db_path(user_id)

    if not os.path.exists(save_path):
        return []

    with open(save_path, "rb") as f:
        db = pickle.load(f)

    query_vec          = embedder.encode([clean_text(query)]).astype("float32")
    distances, indices = db["index"].search(query_vec, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        entry               = db["entries"][idx].copy()
        entry["score"]      = float(dist)
        entry["confidence"] = "high" if dist < 18.0 else "medium" if dist < 25.0 else "low"
        results.append(entry)

    return results