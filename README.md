# DVM Modular Pipeline Demo

This project demonstrates a modular Data Vending Machine (DVM) pipeline. It collects events from Nostr relays into an SQLite database, processes those events by generating vector embeddings using a pre-trained SentenceTransformer model, and indexes them into a persistent ChromaDB vector store for querying and summarization. 

---

## Project Structure

- **database.py**  
  Manages SQLite interactions including database initialization and event insertion/updating.

- **nostr_client.py**  
  Connects to a Nostr relay, collects event data, and stores these events in the SQLite database.

- **chroma.py**  
  Loads configuration from `config.yaml`, initializes the SentenceTransformer model, and manages the ChromaDB vector store.  
  It provides functions for batch embedding and upserting events (`store_events`) as well as retrieving documents based on a query (`get_top_docs`).

- **openai_summary.py**  
  Uses OpenAI’s API to generate summaries by combining a user query with the text and metadata of retrieved events.

- **run_pipeline.py**  
  Orchestrates the overall pipeline by:
  - Collecting unprocessed events from the database.
  - Ingesting (batch embedding) events into ChromaDB.
  - Optionally verifying the document count in the vector store.
  - Executing a query and generating a summary for testing purposes.

- **dvm_service.py**  
  An asynchronous live service module that:
  - Connects to a relay (e.g., `wss://nos.lol`).
  - Subscribes to job request events (of kind 5300) intended for the DVM public key.
  - Extracts the query from the event’s `input` tag.
  - Retrieves matching documents from the ChromaDB collection.
  - Generates a summary via the OpenAI summarization module.
  - Builds and signs a response event (kind 6300) that is then published back to the relay.
  
---

## Setup Instructions

1. **Clone the Repository**

   Clone the repository and navigate into the project directory:
   ```sh
   git clone <repository-url>
   cd socrates
   ```

2. **Create and Activate a Virtual Environment**

   It is recommended to use a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On macOS and Linux
   # venv\Scripts\activate    # On Windows
   ```

3. **Install Dependencies**

   Install the required packages:
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure the OpenAI API Key**

   Set your OpenAI API key as an environment variable:
   ```sh
   export OPENAI_API_KEY=<your-openai-api-key>
   ```
   On Windows (Command Prompt):
   ```sh
   set OPENAI_API_KEY=<your-openai-api-key>
   ```

5. **Configuration Files**

   All configuration settings (such as the persist directory for ChromaDB, batch size, and the embed model name) can be modified in `config.yaml`.

---

## Using the DVM Service Module for Demo Purposes

The `dvm_service.py` module is designed to run continuously and act as a live service that responds to job requests. Follow the steps below to demo its functionality:

1. **Start the DVM Service**

   Run the DVM service by executing:
   ```sh
   python -m socrates.dvm_service
   ```
   The service will:
   - Connect to the relay at `wss://nos.lol`.
   - Subscribe to job requests targeted to the DVM’s public key.
   - Log every message it receives for debugging purposes.

2. **Submit a Job Request**

   For testing, you can use your client or the command-line tool `nak` to send a job request. Please note that you'll need to install `nak` if you want to use it for testing. For example, on macOS you can install it via Homebrew:
   ```sh
   brew install nak
   ```
   Then, send a job request with the query included in an `input` tag:
   ```sh
   nak event -k 5300 \
     -t p=298f2741b893fe98e4464b142879cdd762c4f26a9e6c8f044b2064c36f153d30 \
     -t expiration=$(( $(date +%s) + 120 )) \
     -t input="<add your query here>" \
     wss://nos.lol
   ```
   This command generates an event with the necessary tags. The `dvm_service.py` module will extract the query from the `input` tag, query the ChromaDB collection for related events, generate a summary using OpenAI’s API, and finally publish a signed response event back to the relay.

3. **Verify the Output**

   The service logs the extracted query, details about the documents retrieved, and the published response event. To verify from the client side, you can use the following command to search for the response event (kind 6300) using its etag (which should contain the original event's ID):
   ```sh
   nak req -k 6300 -t e=<original_event_id> --stream wss://nos.lol
   ```
   Replace `<original_event_id>` with the ID of the job request event that was originally sent. This command streams matching events from the relay and helps verify that:
   - The query is correctly parsed from the event’s tags.
   - The summarization correctly combines the query with matching documents.
   - A signed response event (kind 6300) is sent back to the relay.

---

## Additional Notes

- **Modular Design & Extensibility**  
  Each module is designed to work independently. You can use the ingestion or summarization functions alone if needed.

- **Model Downloads**  
  The first time the demo runs, the SentenceTransformer model (e.g., `"all-MiniLM-L6-v2"`) will be automatically downloaded from the Hugging Face Model Hub if not already cached locally.

- **Dependencies**  
  Review `requirements.txt` for the list of top‑level dependencies. Use tools such as `pip freeze` to verify your environment if any issues occur.

- **Ignoring Archive Files**  
  This repository includes only the contents of the `socrates/` directory. Any scripts or files in the archive folders are for reference only and will not be committed to GitHub.

---

Happy coding and demoing your DVM service!