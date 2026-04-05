# config.py
import os

# ── Paths ──────────────────────────────
DATA_CSV      = "data/faqs.csv"
DOCS_FOLDER   = "data/documents"
PREPARED_DATA = "data/prepared_text.txt"
TOKENIZER_PATH = "tokenizer/my_tokenizer"
GOOGLE_BASE_MODEL = "google/flan-t5-base"
MODEL_OUTPUT_PATH = "models/llm_model"

# ── Model Architecture ─────────────────
VOCAB_SIZE     = 8000       # kitne unique words/tokens
MAX_LENGTH     = 256        # ek prompt mein max tokens
EMBED_DIM      = 256        # word embedding size
NUM_HEADS      = 8          # attention heads
NUM_LAYERS     = 4          # transformer layers (deep = better but slow)
FF_DIM         = 512        # feedforward layer size
DROPOUT        = 0.1

# ── Training Settings ──────────────────
BATCH_SIZE    = 2
EPOCHS        = 50        # zyada epochs — kam data hai to
LEARNING_RATE = 5e-5
SAVE_EVERY    = 10

# ── Device ─────────────────────────────
import torch
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"