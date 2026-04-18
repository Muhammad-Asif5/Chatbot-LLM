# src/model_config.py
"""
Per-user model config stored in DB.
Supported models is given by MODEL_PATHS, and user can select one of them as their default model.
"""
from sqlalchemy import Column, String, ForeignKey
from src.database import Base

class UserModelConfig(Base):
    __tablename__ = "user_model_configs"
    user_id    = Column(String, ForeignKey("users.id"), primary_key=True)
    model_name = Column(String, default="flan-t5-large")  

MODEL_PATHS = {
    "flan-t5-large": ("google/flan-t5-large", "models/flan-t5-large"),
    "phi-3-mini": ("microsoft/Phi-3-mini-4k-instruct", "models/Phi-3-mini"),
    "gemma-2b": ("google/gemma-2b", "models/gemma-2b"),
    "mistral-7b": ("mistralai/Mistral-7B-Instruct-v0.2", "models/mistral-7b"),
    "llama-3-8b": ("meta-llama/Meta-Llama-3-8B-Instruct", "models/llama-3-8b"),
}