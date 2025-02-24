import logging
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from socrates.config import CHROMA_MODEL

# Initialize the SentenceTransformer model
embed_model = SentenceTransformer(CHROMA_MODEL)

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


def get_top_docs(user_query, limit=5):
    """
    Encodes the user's query using the provided embedding model,
    queries the ChromaDB collection for the top matching documents,
    and returns these documents along with their metadata.

    Args:
      user_query (str): The user's search query.
      limit (int): Number of top documents to retrieve.

    Returns:
      List[dict]: A list of dictionaries representing the retrieved documents.
    """
    query_embedding = embed_model.encode(user_query).tolist()

    results = collection.query(query_embeddings=[query_embedding], n_results=limit)

    docs = []
    for i, doc_id in enumerate(results["ids"][0]):
        doc_text = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        docs.append({
            "id": doc_id,
            "text": doc_text,
            "metadata": meta
        })

    return docs
