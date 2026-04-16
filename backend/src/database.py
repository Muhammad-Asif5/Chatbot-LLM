import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saas_llm.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    # ✅ Pool size raised to 10 — allows concurrent connections from
    #    FastAPI request handlers AND inference.py system prompt loader
    #    without either one blocking for 30s waiting on a free slot.
    pool_size=10,
    max_overflow=20,
    # ✅ Fail fast — if no connection is free after 5s, raise immediately
    #    instead of the default 30s hang. Surfaces real problems quickly.
    pool_timeout=5,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # ✅ WAL mode — allows simultaneous readers + 1 writer without blocking.
    #    Multiple connections (pool_size=10) NEED WAL to avoid SQLITE_BUSY.
    #    DELETE mode with pool_size>1 causes write contention.
    cursor.execute("PRAGMA journal_mode=WAL")
    # ✅ WAL checkpoint: auto-merge WAL back into main DB every 1000 pages
    cursor.execute("PRAGMA wal_autocheckpoint=1000")
    # ✅ Foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON")
    # ✅ NORMAL sync — safe with WAL, faster than FULL
    cursor.execute("PRAGMA synchronous=NORMAL")
    # ✅ 8MB cache per connection
    cursor.execute("PRAGMA cache_size=-8000")
    # ✅ Busy timeout — if another connection is writing, wait up to 3s
    #    before raising SQLITE_BUSY instead of failing immediately
    cursor.execute("PRAGMA busy_timeout=3000")
    cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    """FastAPI dependency — DB session."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()