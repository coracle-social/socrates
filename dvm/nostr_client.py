# dvm/nostr_client.py
import json
import logging
import time
import yaml
from nostr.filter import Filter, Filters
from nostr.relay_manager import RelayManager
from dvm.embed import generate_embedding, store_embedding

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def subscribe_and_embed():
    config = load_config()
    nostr_config = config.get("nostr", {})
    relay_url = nostr_config.get("relay_url", "wss://bucket.coracle.social")
    kinds = nostr_config.get("kinds", [9, 11, 1111])
    subscription_id = nostr_config.get("subscription_id", "dvm_sub")
    run_seconds = nostr_config.get("run_seconds", 30)
    
    # Create the Filter object with only the allowed parameter "kinds"
    my_filter = Filter(kinds=kinds)
    
    # Process additional tag filters if provided.
    additional_filters = nostr_config.get("additional_filters", {})
    if "tags" in additional_filters:
        tag_filters = []
        for tag_key, tag_value in additional_filters["tags"].items():
            tag_filters.append([tag_key, tag_value])
        # Assign the tag filters directly to the filter object.
        my_filter.tags = tag_filters

    # Now wrap our filter into a Filters object.
    filters = Filters([my_filter])
    
    logging.info(f"Connecting to relay: {relay_url}")
    # Log the filter parameters. We cannot serialize the Filter object directly,
    # so we log our intended tag filters and kinds.
    logging.info(f"Using kinds: {kinds}")
    if "tags" in additional_filters:
        logging.info(f"Using tag filters: {tag_filters}")
    
    relay_manager = RelayManager()
    relay_manager.add_relay(relay_url)
    relay_manager.add_subscription_on_all_relays(subscription_id, filters)
    
    start_time = time.time()
    while time.time() - start_time < run_seconds:
        if relay_manager.message_pool.has_events():
            incoming_msg = relay_manager.message_pool.get_event()
            if incoming_msg and incoming_msg.event:
                event = incoming_msg.event
                event_data = {
                    "id": event.id,
                    "pubkey": event.public_key,
                    "kind": event.kind,
                    "content": event.content,
                    "created_at": event.created_at,
                    "tags": event.tags
                }
                embedding = generate_embedding(event_data)
                store_embedding(event_data, embedding)
                logging.info(f"Embedded event {event.id} (kind={event.kind})")
        time.sleep(1)
    
    relay_manager.close_all_relay_connections()
    logging.info("Closed all relay connections.")

def main():
    logging.basicConfig(level=logging.INFO)
    subscribe_and_embed()

if __name__ == "__main__":
    main()