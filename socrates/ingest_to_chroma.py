"""
This module ingests new events from the SQL database into the ChromaDB vector store.
It batches events to generate embeddings and store them in one call, then marks the events as processed.
"""

import logging
from socrates.database import get_unprocessed_events, mark_events_processed
from socrates.embedding import store_events

def main():
    logging.info("Starting batch ingestion from SQL to ChromaDB...")

    # Retrieve unprocessed events from the SQL database.
    events = get_unprocessed_events()
    if not events:
        logging.info("No new unprocessed events found. Exiting ingestion.")
        return

    try:
        # Store the batch into ChromaDB.
        store_events(events)
    except Exception as e:
        logging.error("Error storing batch in Chroma: %s", e)
        return

    # If successful, mark all events as processed.
    event_ids = [event["id"] for event in events]
    mark_events_processed(event_ids)
    logging.info(f"Successfully processed and ingested {len(events)} events.")

if __name__ == "__main__":
    main()
