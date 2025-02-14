#!/usr/bin/env python3

import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from openai import OpenAI

def get_top_docs(user_query, model, collection, top_k=3):
    """
    1) Encode the user query with SentenceTransformer.
    2) Query Chroma for the top_k most similar documents.
    3) Return the matched texts and metadata.
    """
    query_embedding = model.encode(user_query)
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

def summarize_with_openai(user_query, docs, client, model_name="gpt-4"):
    """
    1) Prepares a prompt that includes the user's query + the retrieved docs.
    2) Sends them to ChatGPT for summarization, returning the final answer.
    """
    # Combine docs into one text block for the prompt
    combined_docs = "\n".join([
        f"Doc {i+1} (kind={d['metadata']['kind']}): {d['text']}"
        for i, d in enumerate(docs)
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

    response = client.chat.completions.create(
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
    # 1. Create an OpenAI client instance (reads OPENAI_API_KEY from environment)
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # 2. Initialize Chroma client
    chroma_client = chromadb.Client(Settings(
        is_persistent=True,
        persist_directory="/Users/venkravchenko/Dev/my-app/socrates/.chroma",
        anonymized_telemetry=False
    ))

    # 3. Get your existing collection
    collection_name = "nostr_events"
    collection = chroma_client.get_collection(collection_name)

    # 4. Load embedding model
    embed_model_name = "all-MiniLM-L6-v2"
    embed_model = SentenceTransformer(embed_model_name)

    # 5. Prompt user
    user_query = input("Enter your query: ")

    # 6. Retrieve top docs
    top_docs = get_top_docs(user_query, embed_model, collection, top_k=3)
    if not top_docs:
        print("No documents found. Make sure your collection has data!")
        return

    # 7. Summarize with GPT
    summary = summarize_with_openai(user_query, top_docs, client, "gpt-4")

    # --- Print the summary first ---
    print("=== SUMMARY ===")
    print(summary)

    # --- Now print the retrieved documents AFTER summarization ---
    print("\n=== RETRIEVED DOCUMENTS ===")
    for i, doc in enumerate(top_docs, start=1):
        print(f"Doc {i} (kind={doc['metadata']['kind']}):")
        print(doc['text'])
        print("---")

if __name__ == "__main__":
    main()
