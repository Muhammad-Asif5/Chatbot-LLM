"""
run_server.py — FastAPI application entry point.

Start dev server:
    python run_server.py

Start production server (Gunicorn):
    gunicorn run_server:app \
        --workers 2 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000
"""
import os

# ── Offline mode must be set BEFORE any HF import ────────
os.environ["TRANSFORMERS_OFFLINE"]   = "1"
os.environ["HF_HUB_OFFLINE"]         = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from dotenv import load_dotenv

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.database import engine
from src.models import Base
from src.model_config import UserModelConfig          # ensure table is created

from routers import (
    auth_router,
    faq_router,
    document_router,
    widget_router,
    analytics_router,
    knowledge_router,
    admin_router,
    model_router,
)
from core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    integrity_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
)

load_dotenv()

# ── Create all DB tables ──────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── FastAPI app ───────────────────────────────────────────
app = FastAPI(
    title       = "VST Support AI — Multi-tenant LLM Platform",
    description = "Customer support chatbot SaaS powered by Flan-T5 / Mistral / Llama",
    version     = "2.1.0",
    root_path   = "/api",
)

# ── Rate limiter ──────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],   # Restrict to your domain in production
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# ── Static files (chatbot.js embed script) ────────────────
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Global exception handlers ─────────────────────────────
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError,         integrity_exception_handler)
app.add_exception_handler(SQLAlchemyError,        sqlalchemy_exception_handler)
app.add_exception_handler(HTTPException,          http_exception_handler)
app.add_exception_handler(Exception,              general_exception_handler)

# ── Routers ───────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(faq_router.router)
app.include_router(document_router.router)
app.include_router(widget_router.router)
app.include_router(analytics_router.router)
app.include_router(knowledge_router.router)
app.include_router(admin_router.router)
app.include_router(model_router.router)


# ── Startup: optionally warm the default model ────────────
@app.on_event("startup")
async def on_startup():
    preload = os.getenv("PRELOAD_MODEL", "false").lower() == "true"
    if preload:
        print("[Startup] Pre-loading default model (flan-t5-large) …")
        try:
            from src.inference import _get_model
            _get_model("flan-t5-large")
            print("[Startup] Model warm.")
        except Exception as e:
            print(f"[Startup] Model pre-load failed (non-fatal): {e}")
    else:
        print("[Startup] Model will be loaded on first request (set PRELOAD_MODEL=true to change).")


# ── Health check ──────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "2.1.0"}


# ── Dev entry point ───────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "run_server:app",
        host   = "0.0.0.0",
        port   = 8000,
        reload = True,
    )