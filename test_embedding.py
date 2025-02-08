import sqlite3
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

def main():
    # -----------------------------------
    # 1. Connect to your nostr_dvm.db
    # -----------------------------------
    conn = sqlite3.connect("nostr_dvm.db")
    cursor = conn.cursor()

    # Example query: grab a few events from your events table
    # Adjust the query or LIMIT as needed
    cursor.execute("SELECT id, kind, content FROM events LIMIT 10")
    rows = cursor.fetchall()

    # -----------------------------------
    # 2. Initialize the embedding model
    # -----------------------------------
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # -----------------------------------
    # 3. Initialize Chroma
    # -----------------------------------
    client = chromadb.Client(Settings(
        persist_directory=".chroma",  # or wherever you want your Chroma files
        anonymized_telemetry=False    # optional; turn off telemetry if you prefer
    ))
    collection = client.get_or_create_collection("nostr_events")

    # -----------------------------------
    # 4. Prepare data for insertion
    # -----------------------------------
    ids = []
    documents = []
    metadatas = []
    embeddings = []

    for row in rows:
        event_id, kind, content = row
        # Clean up the content if needed
        text = (content or "").strip()

        # Compute embedding
        embedding = model.encode(text)

        # Append to lists for Chroma
        ids.append(str(event_id))
        documents.append(text)
        metadatas.append({"kind": kind})
        embeddings.append(embedding)

    # -----------------------------------
    # 5. Insert into Chroma collection
    # -----------------------------------
    # Note: If you're repeatedly inserting the same IDs, 
    # you might need upsert=True or to handle duplicates
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    # -----------------------------------
    # 6. Quick Retrieval Test
    # -----------------------------------
    test_query = "recent chat messages"
    test_embedding = model.encode(test_query)

    # Retrieve the top 3 matches
    results = collection.query(
        query_embeddings=[test_embedding],
        n_results=3
    )

    print(f"Query: {test_query}")
    print("Top results:")
    
    # `results["ids"]` is a list of lists if multiple query embeddings
    for i, doc_id in enumerate(results["ids"][0]):
        # We'll also extract the document text and metadata
        doc_text = results["documents"][0][i]
        doc_meta = results["metadatas"][0][i]
        
        print(f"  ID: {doc_id}")
        print(f"  Kind: {doc_meta.get('kind')}")
        print(f"  Content: {doc_text[:80]}...")  # Show a preview
        print("  ---")

    # -----------------------------------
    # 7. Cleanup
    # -----------------------------------
    conn.close()

if __name__ == "__main__":
    main()
