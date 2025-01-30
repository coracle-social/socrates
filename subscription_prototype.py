import os
import time
import logging
import json

from nostr.key import PrivateKey
from nostr.event import Event
from nostr.relay_manager import RelayManager, RelayException
from nostr.filter import Filter, Filters

# Import the function to load (or create) the static key
from generate_key import get_or_create_privkey

# Import our DB utilities
import db_utils

def main():
    logging.basicConfig(level=logging.INFO)

    # 1) Initialize the database
    db_utils.init_db()

    # Print the current working directory
    cwd = os.getcwd()
    logging.info(f"Current working directory: {cwd}")

    # 2) Load the existing static key or create one if missing
    privkey_hex = get_or_create_privkey("secrets/my_static_key.hex")
    private_key = PrivateKey(bytes.fromhex(privkey_hex))
    logging.info(f"Using static private key (bech32): {private_key.bech32()}")

    # 3) Create a RelayManager and add a single relay
    relay_manager = RelayManager()
    relay_url = "wss://nos.lol"
    relay_manager.add_relay(relay_url)
    logging.info(f"Attempting to connect to relay: {relay_url}")

    # 4) Subscribe to Kinds 9, 11, 1111
    subscription_id = "my_dvm_sub"
    my_filters = Filters([Filter(kinds=[9, 11, 1111])])
    relay_manager.add_subscription_on_all_relays(subscription_id, my_filters)
    logging.info(f"Subscription '{subscription_id}' created for kinds [9, 11, 1111].")

    # 5) Poll for incoming events for ~10 seconds
    run_seconds = 10
    start_time = time.time()

    try:
        while time.time() - start_time < run_seconds:
            if relay_manager.message_pool.has_events():
                incoming_msg = relay_manager.message_pool.get_event()
                if incoming_msg and incoming_msg.event:
                    event = incoming_msg.event
                    
                    # Convert the event to a dict for DB insertion
                    event_data = {
                        "id": event.id,
                        "pubkey": event.public_key,   # event.public_key from your library
                        "kind": event.kind,
                        "content": event.content,
                        "created_at": event.created_at,
                        "tags": event.tags  # This is usually a list of lists
                    }
                    
                    # Insert into the DB
                    db_utils.insert_event(event_data)

                    # Log the event
                    logging.info(f"Stored event: {event.id} (kind={event.kind})")
                    logging.info(f"  pubkey={event.public_key}")
                    logging.info(f"  content={event.content}")
                    logging.info(f"  tags={event.tags}")

            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    finally:
        relay_manager.close_all_relay_connections()
        logging.info("Closed relay connection. Exiting.")

if __name__ == "__main__":
    main()