"""
seed_admin.py — Run ONCE to create the admin user.
Usage:
    cd backend
    python seed_admin.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ── Add src to path ──────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from src.database import SessionLocal, engine, Base
from src.models import User
from src.auth import hash_password

# ── Admin credentials — change before running ────────────
ADMIN_NAME     = "Super Admin"
ADMIN_EMAIL    = "chatbot@vstschool.com"
ADMIN_PASSWORD = "Chatbot@1234!"   # ← change this!
ADMIN_PLAN     = "enterprise"

def seed():
    # Create all tables if they don't exist yet
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if admin already exists
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            print(f"[Seed] Admin already exists: {ADMIN_EMAIL}")
            print(f"[Seed] ID: {existing.id} | is_admin: {existing.is_admin}")
            return

        admin = User(
            name       = ADMIN_NAME,
            email      = ADMIN_EMAIL,
            password   = hash_password(ADMIN_PASSWORD),
            plan       = ADMIN_PLAN,
            is_active  = True,
            is_admin   = True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("=" * 45)
        print("[Seed] ✅ Admin created successfully!")
        print(f"       ID       : {admin.id}")
        print(f"       Name     : {admin.name}")
        print(f"       Email    : {admin.email}")
        print(f"       Plan     : {admin.plan}")
        print(f"       is_admin : {admin.is_admin}")
        print("=" * 45)
        print("[Seed] ⚠️  Delete or secure this file after use.")

    except Exception as e:
        db.rollback()
        print(f"[Seed] ❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()