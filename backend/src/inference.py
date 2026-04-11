# inference.py - Updated query function
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
def query(user_id: str, user_input: str, target_lang: str = "auto") -> dict:
    """
    Pipeline:
    1. Detect language of user_input
    2. Translate user_input to English (if not already English)
    3. Vector DB search in English
    4. HIGH confidence → return KB answer (in English)
    5. MEDIUM confidence → LLM with strict context (in English)
    6. No match → polite not-found message (in English)
    7. Translate final answer to target_lang (if target_lang != "en")
    
    Args:
        user_id: Owner's user ID
        user_input: User's question (any language)
        target_lang: Desired answer language ("auto", "en", "ur", "ar", etc.)
                    "auto" = answer in same language as question
    """
    user_input = clean_text(user_input)
    
    print(f"\n{'='*50}")
    print(f"[Query] User: {user_id}")
    print(f"[Query] Input: '{user_input[:100]}...'")
    print(f"[Query] Target language: {target_lang}")

    # ── Step 1: Detect input language ─────────────────────
    input_lang = detect_language(user_input)
    print(f"[Query] Detected input language: {input_lang}")
    
    # ── Step 2: Determine answer language ─────────────────
    if target_lang == "auto" or not target_lang:
        answer_lang = input_lang  # Answer in same language as question
    else:
        answer_lang = target_lang  # Answer in requested language
    
    print(f"[Query] Answer will be in: {answer_lang}")
    
    # ── Step 3: Translate input to English for search ─────
    english_input = translate_to_english(user_input, input_lang)
    print(f"[Query] English search query: '{english_input[:100]}...'")

    # ── Step 4: Vector search ─────────────────────────────
    vector_results = search_vector_db(user_id, english_input, top_k=5)
    print(f"[Query] Found {len(vector_results)} vector matches")

    best       = vector_results[0] if vector_results else None
    confidence = best["confidence"] if best else "none"
    print(f"[Query] Best confidence: {confidence}")

    # ── Step 5: Get answer in English ─────────────────────
    english_answer = ""
    source = ""
    
    if best and confidence == "high":
        english_answer = best["answer"]
        source = f"vector_db ({best['source']})"
        print(f"[Query] HIGH confidence - using vector answer")
        
    elif best and confidence == "medium":
        # Combine top-3 results for richer context
        context = "\n\n".join([
            r["answer"] for r in vector_results[:3] if r.get("answer")
        ])
        system_prompt = get_system_prompt(user_id)
        english_answer = generate_answer(english_input, context, system_prompt)
        source = "llm_grounded"
        print(f"[Query] MEDIUM confidence - generated grounded answer")
        
    else:
        english_answer = NOT_FOUND_MESSAGE
        source = "not_found"
        confidence = "none"
        print(f"[Query] No match - returning not found message")
    
    print(f"[Query] English answer: '{english_answer[:100]}...'")

    # ── Step 6: Translate answer to target language ───────
    if answer_lang != "en":
        final_answer = translate_from_english(english_answer, answer_lang)
        print(f"[Query] Translated to {answer_lang}: '{final_answer[:100]}...'")
    else:
        final_answer = english_answer
        print(f"[Query] Keeping English answer")

    print(f"{'='*50}\n")

    return {
        "question":   user_input,
        "answer":     final_answer,
        "language":   answer_lang,      # Answer language (for logging)
        "input_lang": input_lang,       # Question language (for reference)
        "source":     source,
        "confidence": confidence,
    }