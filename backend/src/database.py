import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saas_llm.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    # ✅ Single connection in pool — SQLite is a file, not a server
    # Multiple pool connections cause WAL fragmentation
    pool_size=1,
    max_overflow=0,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # ✅ DELETE mode — writes go DIRECTLY into saas_llm.db, no -wal sidecar file
    # WAL mode keeps a separate -wal file that only merges on checkpoint (which never ran)
    cursor.execute("PRAGMA journal_mode=DELETE")
    # ✅ Foreign key constraints enforce karo
    cursor.execute("PRAGMA foreign_keys=ON")
    # ✅ FULL sync — every commit is immediately flushed to disk
    cursor.execute("PRAGMA synchronous=FULL")
    # ✅ Shared cache off — avoid stale read cache across sessions
    cursor.execute("PRAGMA cache_size=-2000")
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