import logging
import asyncio

# Import core functions from your socrates directory
from socrates.nostr_client import subscribe_to_nostr
from socrates.database import get_unprocessed_events, mark_events_processed
from socrates.chroma import store_events, get_top_docs, check_collection_count
from socrates.openai import summarize_with_openai

def configure_logging():
    """
    Configures logging to output messages to the console only.
    """
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s]: %(message)s")
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    root = logging.getLogger()
    root.handlers = [console_handler]
    root.setLevel(logging.INFO)

def run_nostr_collection():
    """
    Collects events from Nostr and stores them in the SQL database.
    """
    logging.info("Starting Nostr event collection...")
    asyncio.run(subscribe_to_nostr())
    logging.info("Nostr event collection complete.")

def run_chroma_ingestion():
    """
    Ingests new events stored in the SQL database into the ChromaDB vector store.
    """
    logging.info("Starting ingestion of new events into Chroma...")

    # Retrieve unprocessed events from the SQL database.
    events = store_events(get_unprocessed_events())
    mark_events_processed([event["id"] for event in events])

    logging.info(f"Successfully processed and ingested {len(events)} events.")

def run_query_and_summarize():
    """
    Retrieves a user query, fetches relevant documents from ChromaDB,
    and generates a summary using the configured OpenAI model.
    """
    logging.info("Now testing query and summarization...")

    # Prompt user for a query.
    user_query = input("Enter your query: ")

    # Retrieve top matching documents.
    top_docs = get_top_docs(user_query, limit=5)
    if not top_docs:
        print("No documents found. Ensure your collection has been populated with events!")
        return

    # Generate summary using OpenAI.
    summary = summarize_with_openai(user_query, top_docs)

    # Output summary and document details.
    print("=== SUMMARY ===")
    print(summary)
    print("\n=== RETRIEVED DOCUMENTS ===")
    for i, doc in enumerate(top_docs, start=1):
        print(f"Doc {i} (kind={doc['metadata'].get('kind', 'N/A')}):")
        print(doc['text'])
        print("---")

def main():
    # Configure logger and ensure the SQL database is set up.
    configure_logging()

    # Stage 1: Collect events from Nostr.
    run_nostr_collection()

    # Stage 2: Ingest events from SQL into ChromaDB.
    run_chroma_ingestion()

    # Optionally, check and output the current collection count.
    check_collection_count()

    # Stage 3: Query the database and perform summarization.
    run_query_and_summarize()

if __name__ == "__main__":
    main()
