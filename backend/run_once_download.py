# run_once_download.py
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

print("Downloading embedding model...")
SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

print("Downloading LLM model...")
AutoTokenizer.from_pretrained("google/flan-t5-base")
AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

print("Done! Now run_server.py will work fully offline.")