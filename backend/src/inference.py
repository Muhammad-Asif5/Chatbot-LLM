"""
Inference engine:
Priority 1 → Vector DB (semantic search on FAQs + docs)
Priority 2 → SQL keyword search
Priority 3 → Fine-tuned LLM generation / Not Found Message
"""

import os

os.environ["TRANSFORMERS_OFFLINE"]   = "1"
os.environ["HF_HUB_OFFLINE"]         = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from src.embedding import search_vector_db
from src.utils import clean_text, detect_language, translate_to_english, translate_from_english

MODEL_PATH     = "models/llm_model"
FALLBACK_MODEL = "google/flan-t5-base"

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

# ── GENERATE WITH LLM ────────────────────────────────────
def generate_answer(question: str, context: str = "") -> str:
    """Use fine-tuned LLM to generate an answer."""
    if context:
        prompt = (
            f"Read the following text and answer the question precisely.\n"
            f"Text: {context[:900]}\n"
            f"Question: {question}\n"
            f"Answer:"
        )
    else:
        prompt = f"Answer the following question: {question}\nAnswer:"

    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=2
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# ── SUMMARIZE ────────────────────────────────────────────
def summarize(text: str) -> str:
    """Summarize a long document or passage."""
    prompt = f"summarize: {clean_text(text)[:1000]}"
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True).to(device)
    print(f"[Summarize] Input tokens: {inputs['input_ids'].shape[1]} prompt: {prompt[:50]}...")
    
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=200, num_beams=4)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# ── MAIN QUERY PIPELINE ──────────────────────────────────
def query(user_id: str, user_input: str, lang: str = "en") -> dict:
    """
    Full pipeline:
       Per-user query pipeline:
    1. Language — user ki di hui use karo, auto detect sirf backup
    2. Search vector DB (semantic) — only HIGH confidence
    3. If not high → search SQL DB
    4. If no match → Not Found message
    5. Translate answer back to user's language
    """
    user_input    = clean_text(user_input)
	
    # ── Language: user ne di toh wahi, warna detect karo ─
    if not lang or lang == "auto":
        lang = detect_language(user_input)

    english_input = translate_to_english(user_input, lang)

    # ── Step 1: Vector Search — sirf HIGH confidence ─────
    vector_results = search_vector_db(user_id, english_input, top_k=3)

    if vector_results and vector_results[0]["confidence"] == "high":
        best       = vector_results[0]
        answer     = best["answer"]
        source     = f"vector_db ({best['source']})"
        confidence = best["confidence"]

    else:
        # ── Step 2: SQL Fallback ─────────────────────────
        # sql_results = search_faqs_sql(english_input, top_k=3)

        # if sql_results:
        #     best       = sql_results[0]
        #     answer     = best["answer"]
        #     source     = "sql_db"
        #     confidence = "medium"

        # else:
        # ── Step 3: LLM Generation / Not Found ───────────
        context    = vector_results[0]["answer"] if vector_results else ""
        answer     = generate_answer(english_input, context)
        source     = "llm_generated"
        confidence = "low"

        # answer     = (
        #     "I'm sorry, I don't have information about that. "
        #     "Please contact support for further assistance."
        # )
        # source     = "not_found"
        # confidence = "none"

    # ── Translate back to user language ─────────────────
    final_answer = translate_from_english(answer, lang)

    return {
        "question":   user_input,
        "answer":     final_answer,
        "language":   lang,
        "source":     source,
        "confidence": confidence
    }
