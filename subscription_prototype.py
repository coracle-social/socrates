# subscription_prototype.py
#
# Purpose:
#   - Connect to a Nostr relay (nos.lol).
#   - Subscribe to events of kinds [9, 11, 1111].
#   - For each incoming event, store it in the single 'events' table.
#   - Log basic info so we can confirm operation.

import os
import time
import logging
import json

from nostr.key import PrivateKey
from nostr.event import Event
from nostr.relay_manager import RelayManager
from nostr.filter import Filter, Filters

# Load or create a static private key (not strictly necessary for subscription,
# but included here since you already had it).
from generate_key import get_or_create_privkey

# Our database utilities with the single 'events' table
import db_utils

def main():
    # Basic logging setup
    logging.basicConfig(level=logging.INFO)

    # 1) Initialize the DB (creates 'events' table if not present)
    db_utils.init_db()

    # Just to confirm our working directory
    cwd = os.getcwd()
    logging.info(f"Current working directory: {cwd}")

    # 2) Load/create the static private key
    privkey_hex = get_or_create_privkey("secrets/my_static_key.hex")
    private_key = PrivateKey(bytes.fromhex(privkey_hex))
    logging.info(f"Using static private key (bech32): {private_key.bech32()}")

    # 3) Create a RelayManager and connect to a single relay
    relay_manager = RelayManager()
    relay_url = "wss://bucket.coracle.social"
    relay_manager.add_relay(relay_url)
    logging.info(f"Attempting to connect to relay: {relay_url}")

    # 4) Subscribe to Kinds 9, 11, 1111
    subscription_id = "my_dvm_sub"
    my_filters = Filters([Filter(kinds=[9, 11, 1111])])
    relay_manager.add_subscription_on_all_relays(subscription_id, my_filters)
    logging.info(f"Subscription '{subscription_id}' created for kinds [9, 11, 1111].")

    # 5) Listen for incoming events for ~10 seconds
    run_seconds = 10
    start_time = time.time()

    try:
        while time.time() - start_time < run_seconds:
            # Check if there's an event in the relay manager's message pool
            if relay_manager.message_pool.has_events():
                incoming_msg = relay_manager.message_pool.get_event()
                if incoming_msg and incoming_msg.event:
                    event = incoming_msg.event
                    
                    # Convert the event object into a dict for insertion
                    event_data = {
                        "id": event.id,
                        "pubkey": event.public_key,
                        "kind": event.kind,
                        "content": event.content,
                        "created_at": event.created_at,
                        "tags": event.tags  # Usually a list of lists
                    }

                    # Store it in the single 'events' table
                    db_utils.insert_event(event_data)

                    # Log to console for confirmation
                    logging.info(f"Stored event: {event.id} (kind={event.kind})")
                    logging.info(f"  pubkey={event.public_key}")
                    logging.info(f"  content={event.content}")
                    logging.info(f"  tags={event.tags}")

            # Sleep briefly to avoid busy looping
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    finally:
        # Cleanly close all relay connections
        relay_manager.close_all_relay_connections()
        logging.info("Closed relay connection. Exiting.")

if __name__ == "__main__":
    main()
