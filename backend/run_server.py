import os

from fastapi.exceptions import RequestValidationError

# ── ENV SETTINGS ─────────────────────────────────────────
os.environ["TRANSFORMERS_OFFLINE"]   = "1"
os.environ["HF_HUB_OFFLINE"]         = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from src.database import engine
from src.models import Base
from routers import auth_router, faq_router, document_router, widget_router, analytics_router, knowledge_router
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# ✅ Rate Limiting Imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    integrity_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)

load_dotenv()

# ── Create DB tables ─────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Initialize FastAPI ───────────────────────────────────
app = FastAPI(
    title="SaaS LLM Platform",
    description="Multi-tenant chatbot platform",
    version="2.0.0"
)

# # Initialize offline translator (downloads packages if needed)
# @app.on_event("startup")
# async def startup_event():
#     """Initialize services on startup."""
#     print("[Startup] Initializing offline translator...")
#     translator = get_translator()
#     print("[Startup] Ready!")


# ✅ Initialize Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# ✅ Add Rate Limit Exception Handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Production mein apni domain dalo
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (chatbot.js) ────────────────────────────
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Register exception handlers ──────────────────────────
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError,         integrity_exception_handler)
app.add_exception_handler(SQLAlchemyError,        sqlalchemy_exception_handler)
app.add_exception_handler(Exception,              general_exception_handler)
app.add_exception_handler(HTTPException,          http_exception_handler)

# ── Routers ──────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(faq_router.router)
app.include_router(document_router.router)
app.include_router(widget_router.router)
app.include_router(analytics_router.router)
app.include_router(knowledge_router.router)

# ── Health Check ─────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

# ── Run Server ───────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run_server:app", host="0.0.0.0", port=8000, reload=True)