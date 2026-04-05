import os
os.environ["TRANSFORMERS_OFFLINE"]   = "1"
os.environ["HF_HUB_OFFLINE"]         = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from src.database import engine
from src.models import Base
from routers import auth_router, faq_router, document_router, widget_router, analytics_router

load_dotenv()

# ── Create DB tables ─────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SaaS LLM Platform",
    description="Multi-tenant chatbot platform",
    version="2.0.0"
)

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

# ── Routers ──────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(faq_router.router)
app.include_router(document_router.router)
app.include_router(widget_router.router)
app.include_router(analytics_router.router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run_server:app", host="0.0.0.0", port=8000, reload=True)