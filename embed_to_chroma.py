import os
import sqlite3
import time
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

def main():
    # 1. Connect to your SQLite DB
    db_path = "nostr_dvm.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 2. Fetch all events you want to embed (kind 9, 11, 1111)
    cursor.execute("""
        SELECT id, kind, content
        FROM events
        WHERE kind IN (9, 11, 1111)
    """)
    rows = cursor.fetchall()
    conn.close()

    # 3. Prepare the embedding model
    model_name = "all-MiniLM-L6-v2"
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)

    # 4. Initialize Chroma Client
    #    Use the new recommended config, specifying a persist directory
    client = chromadb.Client(Settings(
        is_persistent=True,
        persist_directory="/Users/venkravchenko/Dev/my-app/socrates/.chroma",
        anonymized_telemetry=False
    ))

    print("Working directory:", os.getcwd())
    print("Chroma data path:", "/Users/venkravchenko/Dev/my-app/socrates/.chroma")

    # 5. Get or create a collection
    #    You can name it "nostr_events" or something else
    collection_name = "nostr_events"
    collection = client.get_or_create_collection(collection_name)

    # 6. Optionally embed in batches (faster if you have many events)
    #    For 1,200+ events, a batch approach can be beneficial.

    BATCH_SIZE = 64
    # Break rows into chunks of 64 (adjust as needed)
    for start_idx in range(0, len(rows), BATCH_SIZE):
        batch = rows[start_idx:start_idx + BATCH_SIZE]
        
        # Gather IDs, text contents, metadatas
        ids = []
        texts = []
        metadatas = []
        
        for row in batch:
            event_id, kind, content = row
            # Clean or handle content if needed
            text = content.strip() if content else ""
            # Convert event_id to string in case it's stored as something else
            ids.append(str(event_id))
            texts.append(text)
            # You can store more fields in metadata if you want
            metadatas.append({"kind": kind})
        
        # Embed the entire batch
        embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
        
        # Add to Chroma
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )

        print(f"Inserted batch {start_idx} - {start_idx+len(batch)-1}")

    # 7. (Optional) Verify insertion with a query
    test_query = "Testing chat messages"  # any sample text
    query_embedding = model.encode(test_query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    print(f"Query: {test_query}")
    print("Top results:")
    for i, doc_id in enumerate(results["ids"][0]):
        doc = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        print(f"  ID: {doc_id}\n  Kind: {meta.get('kind')}\n  Content: {doc[:60]}...\n")

    print("Done inserting events into Chroma!")

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Total runtime: {end_time - start_time:.2f}s")
