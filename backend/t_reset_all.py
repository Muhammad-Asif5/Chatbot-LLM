import sqlite3
import shutil
import os

print("=== RESET START ===")

# ── 1. Database reset ────────────────────────────────
conn   = sqlite3.connect('saas_llm.db')
cursor = conn.cursor()

cursor.execute("DELETE FROM chat_logs")
cursor.execute("DELETE FROM documents")
cursor.execute("DELETE FROM faqs")
cursor.execute("DELETE FROM knowledge_base")
cursor.execute("DELETE FROM users")
conn.commit()
conn.close()
print("✅ Database cleared!")

# ── 2. Vector DB delete ──────────────────────────────
if os.path.exists("embeddings"):
    shutil.rmtree("embeddings")
    os.makedirs("embeddings")
    print("✅ Embeddings cleared!")

# ── 3. Uploads delete ────────────────────────────────
if os.path.exists("uploads"):
    shutil.rmtree("uploads")
    os.makedirs("uploads")
    print("✅ Uploads cleared!")

print("\n=== RESET COMPLETE ===")
print("Ab fresh start kar sakte ho!")