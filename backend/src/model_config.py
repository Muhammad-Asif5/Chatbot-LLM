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
    "flan-t5-large": "models/flan-t5-large",
    "Phi-3-mini-4k-instruct": "models/Phi-3-mini-4k-instruct",
    "gemma": "models/gemma-2b",
    "mistral": "models/mistral-7b-instruct-q4"
}
