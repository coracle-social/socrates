"""
This module ingests new events from the SQL database into the ChromaDB vector store.
It batches events to generate embeddings and store them in one call, then marks the events as processed.
"""

import logging
import os
from chromadb.config import Settings  # Now imported here for batch storage
import chromadb  # Now imported here for batch storage

from .database import get_unprocessed_events, mark_events_processed
from .embedding import generate_embeddings  # Updated to process a batch of texts.

# Compute the current directory (where run_pipeline resides)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIR = os.path.join(CURRENT_DIR, "data", ".chroma")

def store_batch_in_chroma(events, embeddings):
    """
    Stores a batch of events and their embeddings into ChromaDB.
    Args:
      events (List[dict]): List of event dictionaries.
      embeddings (List[List[float]]): Corresponding list of embeddings.
    """
    # For this demo, we assume persistence info is already set up.
    # Create or retrieve a collection named "nostr_events".
    client = chromadb.Client(Settings(
        is_persistent=True,
        persist_directory=PERSIST_DIR,  # Adjust or load from config if needed.
        anonymized_telemetry=False
    ))
    collection_name = "nostr_events"
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        collection = client.create_collection(name=collection_name)

    # Prepare batch data.
    ids = [event["id"] for event in events]
    docs = [event.get("content", "") for event in events]
    metadatas = [{"kind": event.get("kind"), "pubkey": event.get("pubkey"), "created_at": event.get("created_at")} for event in events]

    # Use upsert to add or update duplicates.
    collection.upsert(
        ids=ids,
        documents=docs,
        embeddings=embeddings,
        metadatas=metadatas
    )

    logging.info("Batch stored in ChromaDB successfully.")

def check_collection_count():
    client = chromadb.Client(Settings(
         is_persistent=True,
         persist_directory=PERSIST_DIR,
         anonymized_telemetry=False
    ))
    collection = client.get_or_create_collection("nostr_events")
    result = collection.get()
    count = len(result["ids"][0]) if result.get("ids") else 0
    print(f"Number of documents in ChromaDB: {count}")

def main():
    logging.info("Starting batch ingestion from SQL to ChromaDB...")

    # Retrieve unprocessed events from the SQL database.
    events = get_unprocessed_events()
    if not events:
        logging.info("No new unprocessed events found. Exiting ingestion.")
        return

    # Prepare a list of text contents for embedding.
    texts = [event.get("content", "") for event in events]

    try:
        # Generate embeddings in a batch.
        embeddings = generate_embeddings(texts)
    except Exception as e:
        logging.error("Error generating embeddings for batch: %s", e)
        return

    try:
        # Store the batch into ChromaDB.
        store_batch_in_chroma(events, embeddings)
    except Exception as e:
        logging.error("Error storing batch in Chroma: %s", e)
        return

    # If successful, mark all events as processed.
    event_ids = [event["id"] for event in events]
    mark_events_processed(event_ids)
    logging.info(f"Successfully processed and ingested {len(events)} events.")

if __name__ == "__main__":
    main()