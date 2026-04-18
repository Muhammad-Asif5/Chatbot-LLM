# download_models.py — Run ONCE to download models
"""
Run this before going offline:
  python download_models.py --model flan-t5-large
  python download_models.py --model phi-3-mini
  python download_models.py --model gemma-2b
  python download_models.py --model mistral-7b   (GPU only)
  python download_models.py --model llama-3-8b   (GPU only)
"""
import argparse, os, torch

DOWNLOAD_MAP = {
    "flan-t5-large": ("google/flan-t5-large", "models/flan-t5-large"),
    "phi-3-mini": ("microsoft/Phi-3-mini-4k-instruct", "models/Phi-3-mini"),
    "gemma": ("google/gemma-2b", "models/gemma-2b"),
    "mistral": ("mistralai/Mistral-7B-Instruct-v0.2", "models/mistral-7b"),
}

# Models that are GPU-only (need bitsandbytes 4-bit)
GPU_ONLY = {"mistral-7b", "llama-3-8b"}

def download(model_key: str):
    hub_id, save_path = DOWNLOAD_MAP[model_key]
    os.makedirs(save_path, exist_ok=True)

    from transformers import (
        AutoTokenizer,
        AutoModelForSeq2SeqLM,
        AutoModelForCausalLM,
        BitsAndBytesConfig,
    )

    print(f"\n[Download] {hub_id} → {save_path}")
    print(f"[Download] Saving tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(hub_id, trust_remote_code=True)
    tokenizer.save_pretrained(save_path)
    print(f"[Download] Tokenizer saved.")

    # ── Seq2Seq (Flan-T5) ─────────────────────────────────
    if model_key == "flan-t5-large":
        print(f"[Download] Loading Flan-T5 (seq2seq, CPU safe)...")
        model = AutoModelForSeq2SeqLM.from_pretrained(hub_id)
        model.save_pretrained(save_path)

    # ── GPU-only causal LM (Mistral / Llama) ──────────────
    elif model_key in GPU_ONLY:
        if not torch.cuda.is_available():
            print(f"[Download] ERROR: '{model_key}' requires a CUDA GPU to download+quantize.")
            print(f"[Download] Use 'phi-3-mini' or 'gemma-2b' for CPU-only machines.")
            return
        print(f"[Download] Loading {model_key} with 4-bit quantization (GPU required)...")
        bnb = BitsAndBytesConfig(
            load_in_4bit           = True,
            bnb_4bit_compute_dtype = torch.float16,
            bnb_4bit_quant_type    = "nf4",
        )
        model = AutoModelForCausalLM.from_pretrained(
            hub_id,
            quantization_config = bnb,
            device_map          = "auto",
            trust_remote_code   = True,
        )
        model.save_pretrained(save_path)

    # ── CPU-safe causal LM (Phi-3, Gemma) ─────────────────
    else:
        print(f"[Download] Loading {model_key} in float32 (CPU safe, no quantization)...")
        model = AutoModelForCausalLM.from_pretrained(
            hub_id,
            torch_dtype       = torch.float32,
            trust_remote_code = True,
            low_cpu_mem_usage = True,   # ← loads layer by layer, saves peak RAM
        )
        model.save_pretrained(save_path)

    print(f"\n[Download] ✅ Done! Saved to '{save_path}'")
    print(f"[Download] You can now run the server offline.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=list(DOWNLOAD_MAP.keys()), required=True)
    args = p.parse_args()
    download(args.model)