"""
This module connects to a Nostr relay, subscribes for events, parses incoming messages,
and inserts the event data into the SQL database using the insert_event() function.
Configuration comes from a local 'config.yaml' file.
"""

import os
import asyncio
import json
import logging
import time
import yaml
import websockets
from .database import insert_event  # Inserts event info into the SQL database
from socrates.config import config

async def subscribe_to_nostr():
    """
    Subscribes to a Nostr relay using parameters from the config, receives events,
    and inserts events into the SQL database.
    """
    nostr_config = config.get("nostr", {})
    relay_url = nostr_config.get("relay_url", "wss://groups.0xchat.com")
    kinds = nostr_config.get("kinds", [9])
    subscription_id = nostr_config.get("subscription_id", "dvm_sub")
    run_seconds = nostr_config.get("run_seconds", 30)

    # Build the filter object, using "#h" as the tag filter if available.
    filter_obj = {"kinds": kinds}
    additional_filters = nostr_config.get("additional_filters", {})
    tags = additional_filters.get("tags", {})
    tag_value = tags.get("h")
    if tag_value:
        filter_obj["#h"] = [tag_value]

    # Construct the subscription (REQ) message for Nostr.
    req_message = ["REQ", subscription_id, filter_obj]
    start_time = time.time()

    async with websockets.connect(relay_url) as websocket:
        # Send our subscription request to the relay.
        await websocket.send(json.dumps(req_message))
        logging.info(f"Subscription request sent: {req_message}")

        # Continue receiving messages until the time limit is reached.
        while time.time() - start_time < run_seconds:
            try:
                # Wait up to 1 second for a message.
                message = await asyncio.wait_for(websocket.recv(), timeout=1)
                logging.info(f"Received: {message}")
                data = json.loads(message)

                # Process the message if it is an event (has EVENT marker in the first element).
                if isinstance(data, list) and len(data) >= 3 and data[0] == "EVENT":
                    event = data[2]  # The event details as a dictionary.
                else:
                    logging.debug("Skipping non-event message.")
                    continue

                # Insert the event in the SQL database.
                insert_event(event)
                logging.info(f"Inserted event {event.get('id')} into SQL database.")
            except asyncio.TimeoutError:
                continue

def main():
    """
    Sets up logging and runs the Nostr subscription using asyncio.
    """
    logging.basicConfig(level=logging.INFO)
    asyncio.run(subscribe_to_nostr())

if __name__ == "__main__":
    main()
