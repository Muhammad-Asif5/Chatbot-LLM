# rebuild_vdb.py
import sys
sys.path.insert(0, '.')

from src.database import SessionLocal
from src.models import FAQ, Document, User
from src.embedding import build_vector_db

db    = SessionLocal()

# Sab users ka rebuild karo
users = db.query(User).all()

if not users:
    print("⚠️ Koi user nahi mila — pehle register karo")
else:
    for user in users:
        faqs = db.query(FAQ).filter(FAQ.user_id == user.id).all()
        docs = db.query(Document).filter(Document.user_id == user.id).all()
        docs = [d for d in docs if d.content and len(d.content.strip()) > 0]

        print(f"\n── User: {user.name} ({user.id}) ──")
        print(f"   FAQs: {len(faqs)}")
        print(f"   Docs: {len(docs)}")

        if faqs or docs:
            build_vector_db(
                user_id   = user.id,
                faqs      = [{"question": f.question, "answer": f.answer, "category": f.category} for f in faqs],
                documents = [{"filename": d.filename, "content": d.content} for d in docs]
            )
            print(f"   ✅ Vector DB rebuilt!")
        else:
            print(f"   ⚠️ No data — FAQs ya Documents add karo pehle")

db.close()
print("\n✅ All done!")