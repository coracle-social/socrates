import time
import logging
from nostr.key import PrivateKey
from nostr.event import Event
from nostr.relay_manager import RelayManager
from nostr.filter import Filter, Filters

def main():
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)

    # Generate a private key and public key
    private_key = PrivateKey()
    public_key = private_key.bech32()
    print("Private Key:", private_key.bech32())
    print("Public Key:", public_key)

    # Create a relay manager and add relays
    relay_manager = RelayManager()
    relay_urls = [
        "wss://relay.damus.io",
        "wss://nos.lol",
        "wss://relay.snort.social"
    ]
    for relay_url in relay_urls:
        relay_manager.add_relay(relay_url)
        print(f"Connected to relay: {relay_url}")

    # Create and sign the event
    content = "Hello World from nostr library!"
    event = Event(content)
    private_key.sign_event(event)

    # Publish the event
    try:
        relay_manager.publish_event(event)
        print(f"Event published with ID: {event.id}")
    except Exception as e:
        print(f"Error publishing event: {e}")

    # Allow some time for the event to propagate
    time.sleep(2)

    # Set up a subscription to listen for events
    subscription_id = "mysub"
    filters = Filters([Filter(authors=[private_key.public_key.hex()], kinds=[1])])  # Filters for TEXT_NOTE events
    relay_manager.add_subscription_on_all_relays(subscription_id, filters)
    print("Subscription created to listen for events.")

    # Wait and process incoming events
    start_time = time.time()
    timeout = 10  # seconds
    while time.time() - start_time < timeout:
        if relay_manager.message_pool.has_events():
            received_event = relay_manager.message_pool.get_event()
            print(f"Received event content: {received_event.event.content}")

    # Clean up connections
    relay_manager.close_all_relay_connections()
    print("Closed all relay connections.")

if __name__ == "__main__":
    main()
