import asyncio
import json
import time
import websockets
from nostr.event import Event  # using the nostr module as in your tests
from nostr.key import PrivateKey
from socrates.openai_summary import summarize_with_openai
from socrates.chroma import get_top_docs  # Import the method to retrieve top docs from ChromaDB
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Hard-coded keys for demo purposes
DVM_PRIVKEY_HEX = "8e0292b91b24ce292d83b448ebadb88e09b4a670efc1c7e797bebc40201704d2"
DVM_PUBKEY_HEX = "298f2741b893fe98e4464b142879cdd762c4f26a9e6c8f044b2064c36f153d30"

# Relay to use
RELAY_URL = "wss://nos.lol"

# Initialize the private key object
private_key = PrivateKey(bytes.fromhex(DVM_PRIVKEY_HEX))

async def subscribe_and_process():
    async with websockets.connect(RELAY_URL) as websocket:
        # Subscribe to job requests (kind 5300) where the "#p" tag matches our DVM pubkey
        subscription = [
            "REQ",
            "dvm-sub",
            {"kinds": [5300], "#p": [DVM_PUBKEY_HEX]}
        ]
        await websocket.send(json.dumps(subscription))
        print("Subscribed to job requests on relay:", RELAY_URL)

        async for message in websocket:
            data = json.loads(message)
            print("Received message:", data)
            
            # Check for EOSE message first
            if isinstance(data, list) and data[0] == "EOSE" and data[1] == "dvm-sub":
                print("EOSE received — now listening for new job requests")
                continue

            # Process event messages if they look as expected
            if isinstance(data, list) and len(data) >= 3:
                event = data[2]
                if not isinstance(event, dict):
                    continue
                if event.get("kind") == 5300:
                    await handle_job_request(event, websocket)
                else:
                    print("Relay response:", event)
            else:
                print("Relay response:", data)

async def handle_job_request(req_event, websocket):
    print("Processing job request:", req_event.get("id"))
    
    # Extract the query from the event's "tags" by looking for a tag with key "input".
    query = ""
    for tag in req_event.get("tags", []):
        if len(tag) >= 2 and tag[0] == "input":
            query = tag[1]
            break
    
    # Retrieve the top matching documents from the Chroma database.
    top_docs = get_top_docs(query, limit=5)
    
    # Generate summary using the client query and the top matching documents.
    summary = summarize_with_openai(query, top_docs)
    
    # Build detailed document information.
    doc_details = "\n".join([
        f"Doc {i+1} (kind={doc['metadata'].get('kind', 'N/A')}): {doc['text']}"
        for i, doc in enumerate(top_docs)
    ])
    
    # Combine the summary and document details.
    combined_response = summary + "\n\n=== Retrieved Documents ===\n" + doc_details
    
    # Build the response content as a JSON-encoded list.
    response_content = json.dumps([["e", combined_response]])
    
    # Build the list of tags to reference the original request.
    tags = [["e", req_event.get("id")]]
    
    # Create a result event (kind 6300) with a UTC timestamp.
    result_event = Event(
        public_key=DVM_PUBKEY_HEX,
        content=response_content,
        kind=6300,
        created_at=int(time.time()),
        tags=tags
    )
    
    # Sign the event using our hard-coded private key.
    private_key.sign_event(result_event)
    
    publish_msg = result_event.to_message()
    
    # Publish the signed event back to the relay.
    await websocket.send(publish_msg)
    print("Published result event:", result_event.id)

def main():
    asyncio.run(subscribe_and_process())

if __name__ == "__main__":
    main()