# src/model_config.py
"""
Per-user model config stored in DB.
Supported models:
  - flan-t5-large   → fast, lightweight, ~700MB
  - mistral-7b      → human-like, ~4GB 4-bit quant
  - llama-3-8b      → advanced, ~5GB 4-bit quant
"""
from sqlalchemy import Column, String, ForeignKey
from src.database import Base

class UserModelConfig(Base):
    __tablename__ = "user_model_configs"
    user_id    = Column(String, ForeignKey("users.id"), primary_key=True)
    model_name = Column(String, default="flan-t5-large")

MODEL_PATHS = {
    "flan-t5-large": "models/flan-t5-large",
    "phi-3-mini":    "models/phi-3-mini",       # CPU-friendly, ~2GB
    "gemma-2b":      "models/gemma-2b",         # CPU-friendly, ~2GB
    "mistral-7b":    "models/mistral-7b-instruct-q4",   # GPU only
    "llama-3-8b":    "models/llama-3-8b-instruct-q4",   # GPU only
}

# Models that can run on CPU (no bitsandbytes needed)
CPU_SAFE_MODELS = {"flan-t5-large", "phi-3-mini", "gemma-2b"}