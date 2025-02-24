#!/usr/bin/env python3
"""
This module retrieves relevant Nostr event documents from ChromaDB using an embedding model,
and then uses OpenAI's API to generate a personalized summary for a user query.

Configuration (e.g., API keys, model names, persist directory) is loaded from a local YAML file.
"""

from sentence_transformers import SentenceTransformer
from socrates.embeddings import collection
from socrates.openai import summarize_with_openai

def main():
    """
    Main execution flow:
      - Loads configuration.
      - Loads the embedding model.
      - Prompts the user for a query.
      - Retrieves matching documents and summarizes them using OpenAI.
      - Outputs the summary and retrieved documents.
    """
    # Load the embedding model.

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

if __name__ == "__main__":
    main()
