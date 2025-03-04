"""
This module connects to a Nostr relay, subscribes for events, parses incoming messages,
and inserts the event data into the SQL database using the insert_event() function.
Configuration comes from a local 'config.yaml' file.
"""

import asyncio
import json
import logging
import websockets
from socrates.database import insert_event
from socrates.config import NOSTR_RELAY, NOSTR_FILTER

async def subscribe_to_nostr():
    """
    Subscribes to a Nostr relay using parameters from the config, receives events,
    and inserts events into the SQL database.
    """
    req_message = ["REQ", 'socrates', NOSTR_FILTER]

    async with websockets.connect(NOSTR_RELAY) as websocket:
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
                    event = data[2]
                    insert_event(event)
                    logging.info(f"Inserted event {event['id']} into SQL database.")

                # Stop listening on EOSE
                if len(data) >= 1 and data[0] == "EOSE":
                    logging.info(f"Received eose from {NOSTR_RELAY}")
                    break
            except asyncio.TimeoutError:
                break
