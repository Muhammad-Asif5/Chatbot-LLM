"""
Inference engine:
Priority 1 → Vector DB HIGH confidence  → return KB answer directly
Priority 2 → Vector DB MEDIUM confidence → pass context to LLM with strict system prompt
Priority 3 → No match                   → polite not-found message (never raw LLM)
"""

import os

os.environ["TRANSFORMERS_OFFLINE"]   = "1"
os.environ["HF_HUB_OFFLINE"]         = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sqlalchemy.orm import Session
from src.embedding import search_vector_db
from src.utils import clean_text, detect_language, translate_to_english, translate_from_english

MODEL_PATH     = "models/llm_model"
FALLBACK_MODEL = "google/flan-t5-base"

# ── NOT FOUND message ────────────────────────────────────
NOT_FOUND_MESSAGE = (
    "I'm sorry, I don't have that information right now. "
    "Please contact our support team for further assistance:\n"
    "📧 Email: support@theclothehanger.com\n"
    "📞 Phone: 555 123 4567"
)

# ── LOAD MODEL ───────────────────────────────────────────
def load_model():
    path = MODEL_PATH if os.path.exists(MODEL_PATH) else FALLBACK_MODEL
    print(f"[Inference] Loading model: {path}")
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
    model     = AutoModelForSeq2SeqLM.from_pretrained(path, local_files_only=True)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    print(f"[Inference] Model loaded on {device}")
    return tokenizer, model, device

tokenizer, model, device = load_model()

# ── FETCH SYSTEM PROMPT FROM KB ──────────────────────────
def get_system_prompt(user_id: str) -> str:
    """
    Read the user's Knowledge Base entries that contain system/role prompts.
    These are KB entries whose title contains keywords like 'prompt', 'role',
    'assistant', 'chatbot', 'guidelines', 'instructions'.
    Returns concatenated prompt text, or a safe default.
    """
    try:
        # Import here to avoid circular imports
        from src.database import SessionLocal
        from src.models import KnowledgeBase

        db = SessionLocal()
        try:
            PROMPT_KEYWORDS = ["prompt", "role", "assistant", "chatbot",
                               "guideline", "instruction", "behavior", "persona"]
            kbs = db.query(KnowledgeBase).filter(
                KnowledgeBase.user_id == user_id
            ).all()

            prompt_entries = []
            for kb in kbs:
                title_lower = kb.title.lower()
                if any(kw in title_lower for kw in PROMPT_KEYWORDS):
                    prompt_entries.append(kb.content)

            if prompt_entries:
                return "\n\n---\n\n".join(prompt_entries)
        finally:
            db.close()
    except Exception as e:
        print(f"[Inference] Could not load system prompt: {e}")

    # Safe default — always polite, never invents answers
    return (
        "You are a helpful and polite customer support assistant. "
        "Answer ONLY using the provided context. "
        "If the context does not contain enough information to answer, "
        "say you don't have that information and ask the user to contact support."
    )

# ── GENERATE WITH STRICT CONTEXT ─────────────────────────
def generate_answer(question: str, context: str, system_prompt: str) -> str:
    """
    Generate answer ONLY from the given context.
    The prompt is structured so the model cannot answer from its own training data.
    """
    # Truncate context to safe token budget
    context_trimmed = context[:800]

    prompt = (
        f"{system_prompt[:400]}\n\n"
        f"Use ONLY the following information to answer. "
        f"Do NOT use any outside knowledge.\n\n"
        f"Information:\n{context_trimmed}\n\n"
        f"Customer question: {question}\n\n"
        f"Answer (based only on the information above):"
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=3,
            # Force the model to stay grounded — penalise short yes/no answers
            min_new_tokens=10,
        )

    raw = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # ── Safety filter: reject single-word or vague answers ──
    # flan-t5 sometimes outputs just "yes", "no", "true" when context is weak
    BAD_ANSWERS = {"yes", "no", "true", "false", "maybe", "correct", "incorrect"}
    if raw.lower().strip(".").strip() in BAD_ANSWERS:
        return NOT_FOUND_MESSAGE

    return raw

# ── SUMMARIZE ────────────────────────────────────────────
def summarize(text: str) -> str:
    """Summarize a long document or passage."""
    prompt = f"summarize: {clean_text(text)[:1000]}"
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True).to(device)
    print(f"[Summarize] Input tokens: {inputs['input_ids'].shape[1]}")

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=200, num_beams=4)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# ── MAIN QUERY PIPELINE ──────────────────────────────────
def query(user_id: str, user_input: str, lang: str = "en") -> dict:
    """
    Pipeline:
    1. Detect / use provided language
    2. Translate to English for embedding search
    3. Vector DB search — HIGH confidence → return answer directly
    4. Vector DB search — MEDIUM confidence → LLM with strict context + system prompt
    5. No match / LOW only → polite not-found message (never raw LLM hallucination)
    6. Translate final answer back to user's language
    """
    user_input = clean_text(user_input)
    
    print(f"\nStep 1- Received query: '{user_input}' with lang='{lang}'")

    # ── Language ─────────────────────────────────────────
    if not lang or lang == "auto":
        lang = detect_language(user_input)
    print(f"\nStep 2 - Detected language: {lang} and user input: '{user_input}...'")
    english_input = translate_to_english(user_input, lang)
    print(f"Step 4 - [Query] Translated to English: '{english_input}'")

    # ── Vector search ────────────────────────────────────
    vector_results = search_vector_db(user_id, english_input, top_k=5)
    print(f"\nStep 5 - [Query] Vector search results (top {len(vector_results)}):")

    best       = vector_results[0] if vector_results else None
    confidence = best["confidence"] if best else "none"
    print(f"\nStep 6 - Best match confidence: {confidence} and answer: '{best['answer'][:100] if best else 'N/A'}...'")

    # ── HIGH confidence: return KB answer as-is ──────────
    if best and confidence == "high":
        answer = best["answer"]
        source = f"vector_db ({best['source']})"
        print(f"\nStep 7 - [Query] High confidence match: '{answer[:100]}...' from source: {source}")

    # ── MEDIUM confidence: LLM grounded strictly to context ──
    elif best and confidence == "medium":
        # Combine top-3 results for richer context
        context = "\n\n".join([
            r["answer"] for r in vector_results[:3] if r.get("answer")
        ])
        system_prompt = get_system_prompt(user_id)
        answer        = generate_answer(english_input, context, system_prompt)
        source        = "llm_grounded"

    # ── LOW / NO match: never guess, always redirect ─────
    else:
        answer = NOT_FOUND_MESSAGE
        source = "not_found"
        confidence = "none"

    # ── Translate back ───────────────────────────────────
    print(f"\nStep 8 - Final English answer before translation: '{answer[:100]}...'")
    final_answer = translate_from_english(answer, lang)
    print(f"\nStep 9 - Final answer after translation: '{final_answer[:100]}...' in language: {lang}")

    return {
        "question":   user_input,
        "answer":     final_answer,
        "language":   lang,
        "source":     source,
        "confidence": confidence,
    }