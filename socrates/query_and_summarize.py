#!/usr/bin/env python3
"""
This module retrieves relevant Nostr event documents from ChromaDB using an embedding model,
and then uses OpenAI's API to generate a personalized summary for a user query.

Configuration (e.g., API keys, model names, persist directory) is loaded from a local YAML file.
"""

import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from chromadb.errors import InvalidCollectionException
from socrates.config import config

def get_top_docs(user_query, embed_model, collection, top_k=5):
    """
    Encodes the user's query using the provided embedding model,
    queries the ChromaDB collection for the top matching documents,
    and returns these documents along with their metadata.
    
    Args:
      user_query (str): The user's search query.
      embed_model: Pre-trained sentence transformer model.
      collection: ChromaDB collection object.
      top_k (int): Number of top documents to retrieve.
      
    Returns:
      List[dict]: A list of dictionaries representing the retrieved documents.
    """
    # Encode query and convert embedding (numpy array) to list of floats.
    embedding = embed_model.encode(user_query)
    query_embedding = embedding.tolist()
    
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

def summarize_with_openai(user_query, docs, model_name):
    """
    Takes the user query and retrieved documents, builds a prompt,
    and uses OpenAI's chat completion API to generate a summary.
    
    Args:
      user_query (str): The original query from the user.
      docs (List[dict]): The list of retrieved document dictionaries.
      model_name (str): The name of the OpenAI model to use.
      
    Returns:
      str: The generated summary message.
    """
    # Load API key from environment variable or config.
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("No OpenAI API key found in environment variables")
    
    client = OpenAI(api_key=openai_api_key)
    
    # Combine retrieved docs into a single text block.
    combined_docs = "\n".join([
        f"Doc {i+1} (kind={doc['metadata'].get('kind', 'N/A')}): {doc['text']}"
        for i, doc in enumerate(docs)
    ])

    # Define system and user messages for the prompt.
    system_message = (
        "You are a helpful AI assistant. "
        "When a user asks a question, respond in a personalized way that starts with 'You asked about', "
        "followed by a summary of the relevant Nostr events. "
        "Please provide a concise and direct summary in response."
    )
    
    user_message = f"""User Query: {user_query}

Relevant Documents:
{combined_docs}

Please summarize these events in a cohesive way that directly addresses the user's query."""
    
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
    """
    Main execution flow:
      - Loads configuration.
      - Sets up the ChromaDB client and collection.
      - Loads the embedding model.
      - Prompts the user for a query.
      - Retrieves matching documents and summarizes them using OpenAI.
      - Outputs the summary and retrieved documents.
    """
    # Retrieve OpenAI API key.
    openai_api_key = os.environ.get("OPENAI_API_KEY", config.get("summarizer", {}).get("openai_api_key"))
    if not openai_api_key:
        raise ValueError("No OpenAI API key found. Set OPENAI_API_KEY in your environment or config.yaml.")
    
    summarizer_model = config.get("summarizer", {}).get("model", "gpt-4o-mini")

    # Setup Chroma configuration.
    chroma_config = config.get("chroma", {})
    current_dir = os.path.dirname(os.path.abspath(__file__))
    relative_dir = chroma_config.get("persist_directory", "data/.chroma")
    chroma_persist_dir = os.path.join(current_dir, relative_dir)

    collection_name = chroma_config.get("collection_name", "nostr_events")
    chroma_client = chromadb.Client(Settings(
        is_persistent=True,
        persist_directory=chroma_persist_dir,
        anonymized_telemetry=False
    ))
    try:
        collection = chroma_client.get_collection(collection_name)
    except InvalidCollectionException:
        collection = chroma_client.create_collection(name=collection_name)

    # Load the embedding model.
    embed_model_name = chroma_config.get("embed_model_name", "all-MiniLM-L6-v2")
    embed_model = SentenceTransformer(embed_model_name)

    # Prompt user for a query.
    user_query = input("Enter your query: ")

    # Retrieve top matching documents.
    top_docs = get_top_docs(user_query, embed_model, collection, top_k=5)
    if not top_docs:
        print("No documents found. Ensure your collection has been populated with events!")
        return

    # Generate summary using OpenAI.
    summary = summarize_with_openai(user_query, top_docs, model_name=summarizer_model)

    # Output summary and document details.
    print("=== SUMMARY ===")
    print(summary)
    print("\n=== RETRIEVED DOCUMENTS ===")
    for i, doc in enumerate(top_docs, start=1):
        print(f"Doc {i} (kind={doc['metadata'].get('kind', 'N/A')}):")
        print(doc['text'])
        print("---")

if __name__ == "__main__":
    main()
