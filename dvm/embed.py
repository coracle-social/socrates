# dvm/embed.py
import os
from chromadb.config import Settings
import chromadb
from sentence_transformers import SentenceTransformer

# Initialize your embedding model (load once if possible)
MODEL_NAME = "all-MiniLM-L6-v2"
embed_model = SentenceTransformer(MODEL_NAME)

# Initialize Chroma client and collection
CHROMA_PERSIST_DIR = ".chroma"  # Update as needed or load from config
chroma_client = chromadb.Client(Settings(
    is_persistent=True,
    persist_directory=CHROMA_PERSIST_DIR,
    anonymized_telemetry=False
))
COLLECTION_NAME = "nostr_events"
collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

def generate_embedding(event_data):
    # For now, just embed the 'content' of the event.
    text = event_data.get("content", "").strip()
    if not text:
        text = " "  # Ensure we have some text to embed.
    return embed_model.encode(text)

def store_embedding(event_data, embedding):
    # Store the event directly in Chroma.
    event_id = str(event_data["id"])
    content = event_data.get("content", "")
    metadata = {"kind": event_data.get("kind")}
    # Here, we add the event. For simplicity, adding one document at a time.
    collection.add(
        ids=[event_id],
        documents=[content],
        metadatas=[metadata],
        embeddings=[embedding]
    )