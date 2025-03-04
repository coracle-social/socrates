import os
from openai import OpenAI
from socrates.config import SUMMARIZER_MODEL

# Load API key from environment variable or config.
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OpenAI API key found in environment variables")

client = OpenAI(api_key=openai_api_key)

def summarize_with_openai(user_query, docs):
    """
    Takes the user query and retrieved documents, builds a prompt,
    and uses OpenAI's chat completion API to generate a summary.

    Args:
      user_query (str): The original query from the user.
      docs (List[dict]): The list of retrieved document dictionaries.

    Returns:
      str: The generated summary message.
    """

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

    user_message = (
        f"User Query: {user_query}"
        "Relevant Documents:"
        f"{combined_docs}"
        "Please summarize these events in a cohesive way that directly addresses the user's query."
    )

    response = client.chat.completions.create(
        model=SUMMARIZER_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        max_tokens=300,
        temperature=0.7
    )

    return response.choices[0].message.content
