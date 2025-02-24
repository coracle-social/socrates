import logging
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from socrates.config import config

chroma_config = config.get("chroma", {})

EMBED_MODEL_NAME = chroma_config.get("embed_model_name", "all-MiniLM-L6-v2")

# Initialize the SentenceTransformer model
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# Initialize Chroma client and collection
client = chromadb.Client(Settings(
    is_persistent=True,
    persist_directory="data/.chroma",
    anonymized_telemetry=False
))

# Initialize our collection
collection = client.get_or_create_collection('nostr_events')

def store_events(events):
    """
    Stores a batch of events and their embeddings into ChromaDB.
    Args:
      events (List[dict]): List of event dictionaries.
      embeddings (List[List[float]]): Corresponding list of embeddings.
    """
    ids = [event["id"] for event in events]
    docs = [event["content"] for event in events]
    embeddings = [list(map(float, emb.tolist())) for emb in embed_model.encode(docs, batch_size=32)]
    metadatas = [{"kind": event["kind"], "pubkey": event["pubkey"], "created_at": event["created_at"]} for event in events]

    # Use upsert to add or update duplicates.
    collection.upsert(
        ids=ids,
        documents=docs,
        embeddings=embeddings,
        metadatas=metadatas
    )

    logging.info("Batch stored in ChromaDB successfully.")

def count_events():
    result = collection.get()
    count = len(result["ids"][0]) if result.get("ids") else 0
    print(f"Number of documents in ChromaDB: {count}")
