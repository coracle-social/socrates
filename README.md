# DVM Modular Pipeline Demo

This project demonstrates a modular pipeline designed as part of a Data Vending Machine (DVM) proof-of-concept. The demo collects events from a Nostr relay, stores them in an SQLite database, generates vector embeddings using a pre-trained SentenceTransformer model, and indexes these embeddings into a ChromaDB vector store for querying and summarization.

## Project Structure

The project is contained entirely within the `socrates/` directory and is organized as follows:

- **database.py**  
  Manages SQLite interactions (database initialization and event insertion/updating).

- **nostr_client.py**  
  Connects to a Nostr relay, collects event data, and stores the events in the SQLite database.

- **embedding.py**  
  Loads configuration from `config.yaml`, initializes the SentenceTransformer model, and generates embeddings. It also provides functionality to store individual embeddings into ChromaDB.

- **ingest_to_chroma.py**  
  Retrieves unprocessed events from the database, uses batch processing to generate embeddings, and upserts them into a ChromaDB collection.  
  It also includes a helper function to check the document count in the vector store.

- **query_and_summarize.py**  
  Prompts the user for a query, retrieves relevant documents from ChromaDB, and uses the OpenAI API to generate a summary.

- **run_pipeline.py**  
  The main entry point that orchestrates the entire pipeline:
  1. Configures logging to output to the console.
  2. Initializes the database.
  3. Collects events from Nostr.
  4. Runs the ingestion phase (bulk embedding and upsertion into ChromaDB).
  5. Checks the ChromaDB collection count.
  6. Executes the query and summarization module.

- **config.yaml**  
  Defines configuration options such as the persist directory for ChromaDB (`data/.chroma`), batch size, and embed model name (e.g., `"all-MiniLM-L6-v2"`).

- **data/**  
  - Contains the `.chroma` folder for ChromaDB persistence.
  - Contains the SQLite database file (`events.db`).

- **requirements.txt**  
  Lists only the top‑level packages required by the demo:
  
  ```plaintext
  chromadb==0.4.15
  openai==1.63.2
  PyYAML==6.0.2
  sentence_transformers==3.4.1
  websockets==14.2
  ```

## Setup Instructions

1. Clone the Repository

Clone the repository to your local machine and navigate to the project directory:

```sh
git clone <repository-url>
cd socrates
```

2. Create and Activate a Virtual Environment

It is recommended to use a virtual environment:

```sh
python -m venv venv
source venv/bin/activate  # On macOS and Linux
# venv\Scripts\activate   # On Windows
```

3. Install Dependencies

Ensure your active virtual environment has the necessary packages by running:

```sh
pip install -r requirements.txt
```

4. Configure Your OpenAI API Key

The summarization module uses OpenAI's API. To use it, you must provide your OpenAI API key. Set the OPENAI_API_KEY environment variable in your shell. For example:

```sh
export OPENAI_API_KEY=<your-openai-api-key>
```

On Windows (Command Prompt):

```sh
set OPENAI_API_KEY=<your-openai-api-key>
```

5. Running the Demo

Run the pipeline using Python’s module syntax to maintain correct package imports:

```sh
python -m socrates.run_pipeline
```

The pipeline will:
- Initialize logging (console output only, no log file).
- Set up the SQLite database and collect events.
- Batch embed events using SentenceTransformer and insert them into ChromaDB.
- Optionally check the document count in ChromaDB.
- Execute query and summarization (using the OpenAI API).

## Modular Design & Extensibility

Each component of this pipeline is engineered to work independently:
- Collection Module: Handles event collection and database storage.
- Ingestion Module: Manages batch processing to generate embeddings and upsert them into a vector store.
- Query/Summarization Module: Provides an interface to query the vector store and summarize results.

This design makes it simple to integrate parts of the pipeline into a larger DVM system. For instance, if you only need event ingestion or summarization functionality, you can import and use the respective modules without executing the entire pipeline.

## Model Downloads

The SentenceTransformer model ("all-MiniLM-L6-v2") is specified in config.yaml. The first time the demo is run, the model will be automatically downloaded from the Hugging Face Model Hub if it is not already cached locally.

## Additional Notes

### Configuration
All settings (e.g., persist directory, batch size, and model name) can be modified in config.yaml.

### Requirements Verification
You can use tools like pip freeze or pipreqs to verify and update the list of top-level dependencies if your project’s imports change.