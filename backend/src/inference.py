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

    path     = MODEL_PATHS.get(model_name, MODEL_PATHS["flan-t5-large"])
    is_local = os.path.exists(path)

    if not is_local:
        os.environ.pop("TRANSFORMERS_OFFLINE", None)
        os.environ.pop("HF_HUB_OFFLINE",       None)

    print(f"[Model] Loading '{model_name}' from {path} …")
    has_gpu   = torch.cuda.is_available()
    device    = "cuda" if has_gpu else "cpu"
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


# ── Noise detector ────────────────────────────────────────
# Patterns that identify system log / import messages that
# should never be treated as real knowledge-base content.
_NOISE_PATTERNS = [
    r"^\[FAQ Import\]",
    r"^\[.*?Import\]",
    r"^\[.*?Error\]",
    r"^\[.*?Warning\]",
    r"\d+\s+(FAQs?|items?|records?)\s+imported",
    r"skipped from ['\"]",
    r"^\[.*?\]\s+\d+",          # generic bracketed-tag + number log lines
]

def _is_noise(text: str) -> bool:
    """
    Returns True if *text* looks like a system/import log message
    rather than real knowledge-base content.
    """
    if not text or len(text.strip()) < 10:
        return True
    for pattern in _NOISE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# ── System-prompt loader ──────────────────────────────────
def _get_system_prompt(user_id: str, db) -> str:
    """
    Load the custom system prompt from the owner's Knowledge Base.
    Looks for an article whose title starts with 'System Prompt'
    (case-insensitive). Falls back to a sensible default if none found.
    """
    if db is None:
        return ""
    try:
        from src.models import KnowledgeBase, FAQ
        kb = (
            db.query(KnowledgeBase)
            .filter(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.title.ilike("system prompt%"),
            )
            .first()
        )
        # Case 1: KnowledgeBase exists
        if kb and hasattr(kb, "content"):
            print(f"[Inference] System prompt KB row found - {kb}")
            return kb.content.strip() if kb.content else ""
        
        # Case 2: fallback to FAQ answers (SQLite group_concat)
        answers = (
            db.query(func.group_concat(FAQ.answer, ", "))
            .filter(FAQ.user_id == user_id)
            .scalar()
        )

        print(f"[Inference] System prompt from FAQ: {answers}")

        return answers.strip() if answers else ""
        
    except Exception as e:
        print(f"[Inference] Could not load system prompt: {e}")
        return ""


# ── Context builder ───────────────────────────────────────
def _build_context(search_results: list[dict]) -> str:
    """
    Build a deduplicated context string from vector-search results.

    Filters out:
      - Noise / system-log entries (import messages, error lines, etc.)
      - Results whose answer field is empty or too short to be useful
      - Duplicate answers (keyed on first 80 chars)

    Returns an empty string when no valid content survives — the caller
    must handle this case and return NOT_FOUND_MESSAGE instead of
    passing empty context to the LLM.
    """
    seen, context = set(), []

    for r in search_results:
        answer   = (r.get("answer")   or "").strip()
        question = (r.get("question") or "").strip()

        print(f"[Context] Evaluating result: '{answer[:80]}'")

        # Skip noise in either field
        if _is_noise(answer) or _is_noise(question):
            print(f"[Context] Skipping noise entry: '{answer[:60]}'")
            continue

        # Skip suspiciously short answers
        if len(answer) < 10:
            print(f"[Context] Skipping too-short answer: '{answer}'")
            continue

        key = answer[:80]
        if key in seen:
            print(f"[Context] Skipping duplicate: '{key}'")
            continue

        seen.add(key)
        context.append(f"- {answer}")

        if len("\n".join(context)) > 600:
            break

    print(f"Step 6 {context} ")
    print(f"Step 7 {search_results} ")

    return "\n".join(context)


# ── Prompt builder ────────────────────────────────────────
def _build_prompt(model_name, question, context, style, sys_prompt):
    style_map = {
        "simple":    "Use simple, clear language. Be brief and direct.",
        "technical": "Use technical language and precise details.",
        "detailed":  "Give a thorough, structured explanation.",
    }
    style_hint       = style_map.get(style, style_map["simple"])
    base_instruction = sys_prompt or "You are a helpful customer support assistant."

    # Causal LM models (phi-3, gemma, mistral, llama)
    if model_name in ("mistral-7b", "llama-3-8b", "phi-3-mini", "gemma-2b"):
        return (
            f"<s>[INST] {base_instruction}\n"
            f"{style_hint}\n"
            f"Use ONLY the context below. "
            f"If the answer is not there, say so clearly.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question} [/INST]"
        )
    else:
        return (
            f"{base_instruction}\n{style_hint}\n"
            f"Use ONLY the context below to answer. "
            f"If the answer cannot be found in the context, "
            f"respond with: 'I don't have information about that.'\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\nAnswer:"
        )


# ── Conversational rephrase prompt (human mode) ───────────
def _build_rephrase_prompt(model_name, question, raw_answer, sys_prompt):
    """
    Build a prompt that instructs the LLM to reword a known FAQ answer
    in a warm, conversational tone — without inventing new information.
    The raw_answer is passed as the sole source of truth so the model
    cannot hallucinate beyond what the KB already contains.
    """
    base_instruction = sys_prompt or "You are a friendly customer support assistant."

    if model_name in ("mistral-7b", "llama-3-8b", "phi-3-mini", "gemma-2b"):
        return (
            f"<s>[INST] {base_instruction}\n"
            f"Rephrase the answer below in a warm, conversational tone. "
            f"Do NOT add any information that is not already in the answer.\n\n"
            f"Original answer: {raw_answer}\n\n"
            f"Customer question: {question} [/INST]"
        )
    else:
        # Flan-T5 and other seq2seq models.
        # A single clear instruction verb works far better than
        # a list of "Do NOT" rules, which cause Flan-T5 to echo input.
        # return (
        #     f"Rewrite the following customer support answer in a warm, "
        #     f"friendly, and conversational tone. "
        #     f"Only use the information already in the answer.\n\n"
        #     f"Customer question: {question}\n\n"
        #     f"Original answer: {raw_answer}\n\n"
        #     f"Friendly reply:"
        # )
        return (
            f"Rewrite this answer to sound friendly and conversational:\n\n"
            f"Answer: {raw_answer}\n\n"
            f"Friendly version:"
        )

import os, requests
def _rephrase_via_api(question: str, raw_answer: str, sys_prompt: str) -> str | None:
    """
    Use the Anthropic API to rephrase a raw FAQ answer conversationally.
    Returns None on failure so the caller can fall back to raw_answer.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    base_instruction = sys_prompt or "You are a friendly customer support assistant."

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type":      "application/json",
            },
            json={
                "model":      "claude-haiku-4-5-20251001",   # fast + cheap
                "max_tokens": 300,
                "system":     base_instruction,
                "messages": [{
                    "role":    "user",
                    "content": (
                        f"Rewrite the following support answer in a warm, "
                        f"conversational tone. Use only the information given — "
                        f"do not add anything new.\n\n"
                        f"Customer question: {question}\n\n"
                        f"Support answer to rephrase:\n{raw_answer}"
                    ),
                }],
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        print(f"[Inference] API rephrase failed: {e}")
        return None

# ── Generator ─────────────────────────────────────────────
def _generate(model_name: str, prompt: str, style: str) -> str:
    tokenizer, model, device = _get_model(model_name)
    max_new = {"simple": 100, "technical": 180, "detailed": 250}.get(style, 120)

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
            # Seq2seq (Flan-T5): enable sampling so output is
            # conversational rather than a beam-search echo of the input.
            # output = model.generate(
            #     **inputs,
            #     max_new_tokens     = max_new, #max(max_new, 150),   # floor at 150 — 100 is too short to rephrase
            #     do_sample          = True,
            #     temperature        = 0.75,
            #     top_p              = 0.92,
            #     repetition_penalty = 1.2,
            #     num_beams          = 1,                   # beam search fights sampling; disable it
            #     early_stopping     = False,
            # )
            output = model.generate(
                **inputs,
                max_new_tokens     = max_new,
                do_sample          = True,
                temperature        = 0.7,
                top_p              = 0.9,
                repetition_penalty = 1.15,
                num_beams          = 1,
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
    results    = search_vector_db(user_id, english_input, top_k=5)
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

    elif mode == "fast":
        # ── 4b. Fast mode — return raw FAQ answer, no LLM ──
        # Never touches the LLM; does not consume quota.
        english_answer = best["answer"]
        source         = "kb_direct"
        print("[Query] Path: fast → kb_direct")

    # elif mode == "human":
    #     # ── 4c. Human mode — LLM rephrases the KB answer ───
    #     # The raw FAQ answer is the only context given to the
    #     # LLM, so it cannot hallucinate beyond what the KB says.
    #     if not _check_plan_limit(user_id, user_plan, db):
    #         english_answer = (
    #             "You have reached your daily query limit. "
    #             "Please upgrade your plan for more queries."
    #         )
    #         source = "plan_limit"
    #         print("[Query] Path: plan_limit")

    #     else:
    #         sys_prompt     = _get_system_prompt(user_id, db)
    #         raw_answer     = best["answer"]
    #         prompt         = _build_rephrase_prompt(
    #             model_name, english_input, raw_answer, sys_prompt
    #         )
    #         print(f'STEP 1 _build_rephrase_prompt - {prompt} \n\n')
    #         english_answer = _generate(model_name, prompt, style)
    #         print(f'STEP 2 english_answer - {english_answer} \n\n')
            
    #         source         = f"rag_{model_name}"
    #         print(f"[Query] Path: human → rephrase via {model_name}")

    elif mode == "human":
        if not _check_plan_limit(user_id, user_plan, db):
            english_answer = (
                "You have reached your daily query limit. "
                "Please upgrade your plan for more queries."
            )
            source = "plan_limit"
            print("[Query] Path: plan_limit")

        else:
            sys_prompt = _get_system_prompt(user_id, db)
            raw_answer = best["answer"]

            # ── Try Anthropic API first (best conversational quality) ──
            rephrased = _rephrase_via_api(english_input, raw_answer, sys_prompt)

            if rephrased:
                english_answer = rephrased
                source         = "rag_api"
                print("[Query] Path: human → rephrase via Anthropic API")
            else:
                # ── Fallback to local LLM if API unavailable ───────────
                prompt         = _build_rephrase_prompt(model_name, english_input, raw_answer, sys_prompt)
                english_answer = _generate(model_name, prompt, style)
                source         = f"rag_{model_name}"
                print(f"[Query] Path: human → rephrase via {model_name} (API fallback)")
                
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
