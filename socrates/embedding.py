# dvm/embed.py
import os
import yaml
import logging
from chromadb.config import Settings
import chromadb
from sentence_transformers import SentenceTransformer
from socrates.config import config

# Load Chroma settings from config
chroma_config = config.get("chroma", {})
current_dir = os.path.dirname(os.path.abspath(__file__))
# Build the persist directory path relative to the socrates folder.
CHROMA_PERSIST_DIR = os.path.join(current_dir, chroma_config.get("persist_directory", "data/.chroma"))
COLLECTION_NAME = chroma_config.get("collection_name", "nostr_events")
EMBED_MODEL_NAME = chroma_config.get("embed_model_name", "all-MiniLM-L6-v2")

# Initialize the SentenceTransformer model
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# Initialize Chroma client and collection
chroma_client = chromadb.Client(Settings(
    is_persistent=True,
    persist_directory=CHROMA_PERSIST_DIR,
    anonymized_telemetry=False
))
collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

def generate_embedding(event_data):
    """
    Generates an embedding vector for the event's content.
    If content is empty, it embeds a single space.
    """
    text = event_data.get("content", "").strip()
    if not text:
        text = " "  # Ensure there's content to embed.
    try:
        embedding = embed_model.encode(text)
        return embedding
    except Exception as e:
        logging.error(f"Error generating embedding for event {event_data.get('id')}: {e}")
        return None

def store_embedding(event_data, embedding):
    try:
        # Convert numpy array to a list of native Python floats.
        embedding_list = list(map(float, embedding.tolist()))
        
        collection.add(
            ids=[event_data["id"]],
            embeddings=[embedding_list],  # Now a list of floats, as expected
            documents=[event_data.get("content", "")],
            metadatas=[{
                "kind": event_data.get("kind"),
                "pubkey": event_data.get("pubkey"),
                "created_at": event_data.get("created_at")
            }]
        )
        logging.info(f"Stored embedding for event {event_data['id']} in ChromaDB.")
    except Exception as e:
        logging.error(f"Error storing embedding for event {event_data.get('id')}: {e}")

def generate_embeddings(texts):
    """
    Generates embeddings in batch for a list of texts.
    Args:
      texts (List[str]): List of texts to embed.
    
    Returns:
      List[List[float]]: List of embeddings, where each embedding is a list of floats.
    """
    embeddings = embed_model.encode(texts, batch_size=32)
    # Ensure they are converted into plain Python lists of floats.
    return [list(map(float, emb.tolist())) for emb in embeddings]
