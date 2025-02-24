"""
This module connects to a Nostr relay, subscribes for events, parses incoming messages,
and inserts the event data into the SQL database using the insert_event() function.
Configuration comes from a local 'config.yaml' file.
"""

import asyncio
import json
import logging
import time
import websockets
from socrates.database import insert_event
from socrates.config import config

async def subscribe_to_nostr():
    """
    Subscribes to a Nostr relay using parameters from the config, receives events,
    and inserts events into the SQL database.
    """
    nostr_config = config.get("nostr", {})
    relay = nostr_config.get("relay")
    filter = nostr_config.get("filter")

    if not relay:
        raise Exception('config: nostr.relay is required')

    if not filter:
        raise Exception('config: nostr.filter is required')

    # Construct the subscription (REQ) message for Nostr.
    req_message = ["REQ", 'socrates', filter]

    async with websockets.connect(relay) as websocket:
        # Send our subscription request to the relay.
        await websocket.send(json.dumps(req_message))
        logging.info(f"Subscription request sent: {req_message}")

        # Continue receiving messages until the time limit is reached.
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                logging.info(f"Received: {message}")
                data = json.loads(message)

                if not isinstance(data, list):
                    logging.debug("Skipping non-event message.")
                    continue

                # Process the message if it is an event (has EVENT marker in the first element).
                if len(data) >= 3 and data[0] == "EVENT":
                    insert_event(data[2])
                    logging.info(f"Inserted event {event.get('id')} into SQL database.")

                # Stop listening on EOSE
                if len(data) >= 1 and data[0] == "EOSE":
                    logging.info(f"Received eose from {relay}")
                    break
            except asyncio.TimeoutError:
                break

def main():
    """
    Sets up logging and runs the Nostr subscription using asyncio.
    """
    logging.basicConfig(level=logging.INFO)
    asyncio.run(subscribe_to_nostr())

if __name__ == "__main__":
    main()
