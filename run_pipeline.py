import logging
import asyncio

# Import core functions from your socrates directory
from .nostr_client import subscribe_to_nostr
from .database import initialize_db
from socrates.ingest_to_chroma import check_collection_count

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
    from socrates.ingest_to_chroma import main as ingest_main
    logging.info("Starting ingestion of new events into Chroma...")
    ingest_main()
    logging.info("Chroma ingestion complete.")

def run_query_and_summarize():
    """
    Retrieves a user query, fetches relevant documents from ChromaDB,
    and generates a summary using the configured OpenAI model.
    """
    from socrates.query_and_summarize import main as query_main
    logging.info("Now testing query and summarization...")
    query_main()
    logging.info("Query and summarization test complete.")

def main():
    # Configure logger and ensure the SQL database is set up.
    configure_logging()
    initialize_db()

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