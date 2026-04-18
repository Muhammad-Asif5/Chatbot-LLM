# inference.py — Multi-tenant RAG Engine
# ─────────────────────────────────────────────────────────
# FLOW:
#   1. Customer question + owner_id arrives at /widget/query
#   2. Language detected, translated to English if needed
#   3. ONLY this owner's Vector DB is searched (full isolation)
#   4. mode="fast"  → direct KB answer if found, NOT_FOUND otherwise
#   5. mode="human" → KB answer found → LLM rephrases conversationally
#                     KB answer not found → NOT_FOUND_MESSAGE
#   6. Translate answer back to customer's language
#   7. Log to ChatLog table
# ─────────────────────────────────────────────────────────

from sqlalchemy import func
import os, re, time, torch

os.environ["TRANSFORMERS_OFFLINE"]   = "1"
os.environ["HF_HUB_OFFLINE"]         = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from src.embedding import search_vector_db
from src.utils import (
    clean_text,
    detect_language,
    translate_to_english,
    translate_from_english,
)
from src.model_config import MODEL_PATHS

# ── Plan-based limits ─────────────────────────────────────
# How many RAG calls (LLM generations) per plan per day.
# Direct KB hits (fast mode) are free — they never touch the LLM.
PLAN_DAILY_LIMITS = {
    "free":       50,
    "pro":       500,
    "enterprise": 99_999,
}

NOT_FOUND_MESSAGE = (
    "I'm sorry, I don't have information about that. "
    "Please contact our support team for assistance."
)

# ── Shared model cache ────────────────────────────────────
# One model instance in RAM — reused for ALL tenants.
_model_cache: dict = {}


# ── Model loader ──────────────────────────────────────────
def _get_model(model_name: str):
    if model_name in _model_cache:
        return _model_cache[model_name]

    hf_repo, local_path = MODEL_PATHS.get(model_name, MODEL_PATHS["flan-t5-large"])
    is_local = os.path.exists(local_path)

    if not is_local:
        os.environ.pop("TRANSFORMERS_OFFLINE", None)
        os.environ.pop("HF_HUB_OFFLINE",       None)

    print(f"[Model] Loading '{model_name}' from {local_path if is_local else hf_repo} …")
    has_gpu   = torch.cuda.is_available()
    device    = "cuda" if has_gpu else "cpu"
    path = local_path if is_local else hf_repo
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=is_local)

    # ── GPU-only models (Mistral / Llama) ─────────────────
    if model_name in ("mistral-7b", "llama-3-8b"):
        if not has_gpu:
            print(f"[Model] WARNING: '{model_name}' requires GPU. "
                  f"Falling back to flan-t5-large on CPU.")
            _model_cache[model_name] = _get_model("flan-t5-large")
            return _model_cache[model_name]

        bnb = BitsAndBytesConfig(
            load_in_4bit              = True,
            bnb_4bit_compute_dtype    = torch.float16,
            bnb_4bit_quant_type       = "nf4",
            bnb_4bit_use_double_quant = True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            path,
            quantization_config = bnb,
            device_map          = "auto",
            local_files_only    = is_local,
            trust_remote_code   = True,
        )

    # ── Phi-3 Mini / Gemma 2B — CPU-friendly causal LM ────
    elif model_name in ("phi-3-mini", "gemma-2b"):
        model = AutoModelForCausalLM.from_pretrained(
            path,
            torch_dtype      = torch.float32,   # float32 for CPU
            device_map        = "cpu",
            local_files_only  = is_local,
            trust_remote_code = True,
        )
        model.eval()

    # ── Flan-T5 (seq2seq, CPU default) ────────────────────
    else:
        model = AutoModelForSeq2SeqLM.from_pretrained(
            path,
            local_files_only = is_local
        )
        model.eval()
        model.to(device)

    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"]       = "1"

    _model_cache[model_name] = (tokenizer, model, device)
    print(f"[Model] '{model_name}' ready on {device}")
    return _model_cache[model_name]

# ── Conversational rephrase prompt (human mode) ───────────
def _build_rephrase_prompt(model_name, question, raw_answer):
    """
    Build a prompt that instructs the LLM to reword a known FAQ answer
    in a warm, conversational tone — without inventing new information.
    The raw_answer is passed as the sole source of truth so the model
    cannot hallucinate beyond what the KB already contains.
    """
    base_instruction = "You are a friendly customer support assistant."

    if model_name in ("mistral-7b", "llama-3-8b", "phi-3-mini", "gemma-2b"):
        return (
            f"<s>[INST] {base_instruction}\n"
            f"Rephrase the answer below in a warm, conversational tone. "
            f"Do NOT add any information that is not already in the answer.\n\n"
            f"Original answer: {raw_answer}\n\n"
            f"Customer question: {question} [/INST]"
        )
    else:
        opener = "Sure! "
        return (
            f"Paraphrase the following answer to the customer's question "
            f"in a warm, conversational tone. Start your reply with '{opener}'.\n\n"
            f"Question: {question}\n"
            f"Answer: {raw_answer}\n\n"
            f"Conversational reply: {opener}"
        )

def _safe_rephrase(generated: str, raw_answer: str) -> str:
    """
    Validate the LLM-generated rephrasing.
    Falls back to a conversational wrap of the raw answer (never bare FAQ text).
    """
    # Conversational fallback — always sounds human even on LLM failure
    conversational_fallback = f"{raw_answer}"

    gen = generated.strip()
    if not gen:
        print("[SafeRephrase] Step 1 — empty output, using conversational fallback")
        return conversational_fallback

    if gen.endswith("?"):
        # Model drifted into a question — strip trailing sentence and keep the rest
        sentences = re.split(r'(?<=[.!])\s+', gen)
        sentences = [s for s in sentences if not s.strip().endswith("?")]
        gen = " ".join(sentences).strip()
        if not gen:
            print("[SafeRephrase] Step 2 — only question sentences, using conversational fallback")
            return conversational_fallback

    if len(gen) < len(raw_answer) * 0.2:
        print("[SafeRephrase] Step 3 — output too short, using conversational fallback")
        return conversational_fallback

    # ── Faithfulness check ────────────────────────────────
    # If the generated text shares almost no content words with the
    # raw_answer, the model has hallucinated. Fall back to conversational wrap.
    raw_words = set(raw_answer.lower().split())
    gen_words = set(gen.lower().split())
    stopwords = {"the","a","an","is","are","to","of","and","in","it",
                 "for","that","this","or","with","can","you","your","we"}
    raw_content = raw_words - stopwords
    gen_content = gen_words - stopwords
    if raw_content:
        print(f"[SafeRephrase] Step 4 — faithfulness check: raw_content={len(raw_content)} words")
        overlap = len(raw_content & gen_content) / len(raw_content)
        print(f"[SafeRephrase] Step 4 — overlap={overlap:.2f}")
        if overlap < 0.15:   # relaxed from 0.25 → 0.15 to reduce false fallbacks
            print("[SafeRephrase] Step 5 — low overlap (hallucination risk), using conversational fallback")
            return conversational_fallback

    print(f"[SafeRephrase] Step 6 — rephrased output accepted: '{gen[:80]}...'")
    return gen

# ── Generator ─────────────────────────────────────────────
def _generate(model_name: str, prompt: str, style: str) -> str:
    print(f"[Generate] Model: {model_name}\n\n")
    print(f"[Generate] Style: {style}\n\n")

    tokenizer, model, device = _get_model(model_name)
    max_new = {"simple": 100, "technical": 180, "detailed": 250}.get(style, 120) 
    print(f"[Generate] device: {device}\n\n")

    inputs = tokenizer(
        prompt, return_tensors="pt", truncation=True,
        max_length=512, padding=True,
    ).to(device)

    with torch.no_grad():
        # All causal LM models share the same generation path
        if model_name in ("mistral-7b", "llama-3-8b", "phi-3-mini", "gemma-2b"):
            output = model.generate(
                **inputs,
                max_new_tokens     = max_new,
                do_sample          = True,
                temperature        = 0.7,
                top_p              = 0.9,
                repetition_penalty = 1.1,
                pad_token_id       = tokenizer.eos_token_id,
            )
            generated = output[0][inputs["input_ids"].shape[1]:]
            answer    = tokenizer.decode(generated, skip_special_tokens=True)
        else:
            # In _generate(), for seq2seq path:
            output = model.generate(
                **inputs,
                max_new_tokens     = max(max_new, 150),  # floor at 150 — enough to rephrase naturally
                min_new_tokens     = 20,                 # prevent ultra-short echoes
                do_sample          = True,
                temperature        = 0.7,   # higher = more natural/varied output
                top_p              = 0.92,
                repetition_penalty = 1.3,   # stronger penalty prevents input echoing
                num_beams          = 1,     # beam search fights sampling; keep off
            )

            answer = tokenizer.decode(output[0], skip_special_tokens=True)

    return answer.strip()


# ── Plan guard ────────────────────────────────────────────
def _check_plan_limit(user_id: str, plan: str, db) -> bool:
    """
    Returns True when the user is within their daily LLM-generation limit.
    Direct-hit answers (fast mode) bypass this check entirely.
    """
    if db is None:
        return True
    try:
        from src.models import ChatLog
        from sqlalchemy import func
        from datetime import date
        limit = PLAN_DAILY_LIMITS.get(plan, PLAN_DAILY_LIMITS["free"])
        today = date.today()
        used  = (
            db.query(func.count(ChatLog.id))
            .filter(
                ChatLog.user_id == user_id,
                func.date(ChatLog.created_at) == today,
                ChatLog.source.like("rag_%"),   # only LLM calls count
            )
            .scalar()
        )
        return (used or 0) < limit
    except Exception as e:
        print(f"[Inference] Plan-limit check failed: {e}")
        return True   # fail open so users are never silently blocked

# ── Main entry point ──────────────────────────────────────
def query(
    user_id:     str,
    user_input:  str,
    target_lang: str  = "auto",
    style:       str  = "simple",
    mode:        str  = "fast",
    db                = None,
) -> dict:
    """
    Process one customer question for one specific tenant's chatbot.

    mode="fast"  — Return the raw KB answer immediately if found;
                   return NOT_FOUND_MESSAGE if not. Never calls the LLM.

    mode="human" — If a KB answer is found, pass it to the LLM so it can
                   rephrase the answer in a warm, conversational tone.
                   If no KB answer is found, return NOT_FOUND_MESSAGE.
                   Counts against the tenant's daily LLM quota.

    Returns a dict: question, answer, source, confidence, language, model.
    """
    start      = time.time()
    user_input = clean_text(user_input)

    print(f"\n{'='*50}")
    print(f"[Query] User:            {user_id}")
    print(f"[Query] Input:           '{user_input[:100]}'")
    print(f"[Query] Mode:            {mode}")
    print(f"[Query] Target language: {target_lang}")

    # ── 1. Language detection ──────────────────────────────
    input_lang  = detect_language(user_input)
    answer_lang = input_lang if target_lang == "auto" else target_lang
    print(f"[Query] Detected lang:   {input_lang}")
    print(f"[Query] Answer lang:     {answer_lang}")

    english_input = (
        user_input if input_lang == "en"
        else translate_to_english(user_input, input_lang)
    )
    print(f"[Query] English query:   '{english_input[:100]}'")

    # ── 2. Resolve model + plan for this tenant ────────────
    model_name = "flan-t5-large"
    user_plan  = "free"
    if db:
        try:
            from src.models import User
            from src.model_config import UserModelConfig
            owner = db.query(User).filter(User.id == user_id).first()
            if owner:
                user_plan = owner.plan or "free"
            cfg = (
                db.query(UserModelConfig)
                .filter(UserModelConfig.user_id == user_id)
                .first()
            )
            if cfg:
                model_name = cfg.model_name
        except Exception as e:
            print(f"[Inference] Config lookup error: {e}")

    print(f"[Query] Plan:  {user_plan}")
    print(f"[Query] Model: {model_name}")

    # ── 3. Vector search (tenant-isolated) ────────────────
    results    = search_vector_db(user_id, english_input, top_k=3)
    print(f"[Query] results 1: {results}\n\n")
   
    best       = results[0] if results else None
    confidence = best["confidence"] if best else "none"
    kb_found   = best is not None and confidence in ("high", "medium")
    print(f"[Query] Best confidence: {confidence} | kb_found={kb_found}")

    # ── 4. Generate answer ────────────────────────────────
    english_answer = ""
    source         = "not_found"

    if not kb_found:
        # ── 4a. Nothing useful in KB for either mode ───────
        english_answer = NOT_FOUND_MESSAGE
        source         = "not_found"
        print("[Query] Path: not_found (no KB match)")

    elif mode == "fast" and confidence in ("high", "medium"):
        # ── 4b. Fast mode — return raw FAQ answer, no LLM ──
        # Never touches the LLM; does not consume quota.
        assert best is not None
        english_answer = best["answer"]
        source         = "kb_direct"
        print(f"[Query] Path: fast → kb_direct (confidence={confidence})")

    elif mode == "human":
        if not _check_plan_limit(user_id, user_plan, db):
            english_answer = (
                "You have reached your daily query limit. "
                "Please upgrade your plan for more queries."
            )
            source = "plan_limit"
            print("[Query] Path: plan_limit")

        else:
            assert best is not None
            raw_answer = best["answer"]
            print(f"[Query] raw_answer: {raw_answer}")

            prompt         = _build_rephrase_prompt(model_name, english_input, raw_answer)
            raw_output     = _generate(model_name, prompt, style)
            english_answer = _safe_rephrase(raw_output, raw_answer)
            source         = f"rag_{model_name}"
            print(f"[Query] Path: human → rephrase via {model_name}")
            print(f"[Query] Prompt sent to model:\n{prompt}")
            print(f"[Query] Raw KB answer:        {raw_answer}")
            print(f"[Query] Raw model output:     {raw_output}")
            print(f"[Query] Final answer:         {english_answer}")
            print(f"[Query] Source:               {source}")
                
    else:
        # ── 4d. Unknown mode — safe fallback ───────────────
        english_answer = NOT_FOUND_MESSAGE
        source         = "not_found"
        print(f"[Query] Path: unknown mode '{mode}' → not_found")

    # ── 5. Post-process & translate back ─────────────────
    english_answer = re.sub(r"\s+", " ", english_answer).strip()

    final_answer = (
        translate_from_english(english_answer, answer_lang)
        if answer_lang != "en"
        else english_answer
    )

    elapsed = (time.time() - start) * 1000
    print(f"[Query] Done in {elapsed:.0f}ms | source={source}")
    print(f"{'='*50}\n")

    return {
        "question":   user_input,
        "answer":     final_answer,
        "mode":       mode,
        "confidence": confidence,
        "source":     source,
        "language":   answer_lang,
        "model":      model_name,
    }