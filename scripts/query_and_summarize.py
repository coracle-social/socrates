#!/usr/bin/env python3
import os
import yaml
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import openai

def load_config():
    """Load settings from config.yaml."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def get_top_docs(user_query, embed_model, collection, top_k=5):
    """
    Encode the user's query, retrieve the top_k most similar documents from Chroma,
    and return them along with their metadata.
    """
    query_embedding = embed_model.encode(user_query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
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

def summarize_with_openai(user_query, docs, model_name="gpt-4"):
    """
    Prepares a prompt combining the user query with retrieved documents and uses OpenAI's API
    to produce a summary.
    """
    # Combine the docs into a single text block
    combined_docs = "\n".join([
        f"Doc {i+1} (kind={doc['metadata'].get('kind', 'N/A')}): {doc['text']}"
        for i, doc in enumerate(docs)
    ])

    system_message = (
        "You are a helpful AI assistant. "
        "Given the user's query and some relevant Nostr events, "
        "please provide a concise summary."
    )
    user_message = f"""User Query: {user_query}

Relevant Documents:
{combined_docs}

Please summarize these events in a cohesive way, focusing on the user's query.
"""
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        max_tokens=300,
        temperature=0.7
    )
    return response.choices[0].message.content

def main():
    # Load configuration from config.yaml
    config = load_config()

    # Set up OpenAI API key (from environment variable or config)
    openai_api_key = os.environ.get("OPENAI_API_KEY", config.get("openai_api_key"))
    if not openai_api_key:
        raise ValueError("No OpenAI API key found. Set OPENAI_API_KEY in your environment or config.yaml.")
    openai.api_key = openai_api_key

    # Initialize the Chroma client using settings from config (or defaults)
    chroma_persist_dir = config.get("chroma_persist_directory", "socrates/.chroma")
    chroma_client = chromadb.Client(Settings(
        is_persistent=True,
        persist_directory=chroma_persist_dir,
        anonymized_telemetry=False
    ))
    collection_name = config.get("collection_name", "nostr_events")
    collection = chroma_client.get_collection(collection_name)

    # Load the embedding model (e.g., all-MiniLM-L6-v2)
    embed_model_name = config.get("embed_model_name", "all-MiniLM-L6-v2")
    embed_model = SentenceTransformer(embed_model_name)

    # Prompt the user for a query
    user_query = input("Enter your query: ")

    # Retrieve top matching documents from the Chroma collection
    top_docs = get_top_docs(user_query, embed_model, collection, top_k=3)
    if not top_docs:
        print("No documents found. Ensure your collection has been populated with events!")
        return

    # Summarize the retrieved documents using OpenAI's GPT-4
    summary = summarize_with_openai(user_query, top_docs, model_name="gpt-4")

    # Print the summary and the retrieved documents for reference
    print("=== SUMMARY ===")
    print(summary)
    print("\n=== RETRIEVED DOCUMENTS ===")
    for i, doc in enumerate(top_docs, start=1):
        print(f"Doc {i} (kind={doc['metadata'].get('kind', 'N/A')}):")
        print(doc['text'])
        print("---")

if __name__ == "__main__":
    main()