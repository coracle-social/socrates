from nostr.relay_manager import RelayManager
from nostr.filter import Filter, Filters
import time

# Minimal example: fetch recent text notes (kind=1)
def main():
    relay_url = "wss://relay.damus.io"  # or another known open relay
    relay_manager = RelayManager()
    relay_manager.add_relay(relay_url)

    # Subscribe to text-note events
    fltr = Filter(kinds=[1], limit=5)
    subscription_id = "test-sub"
    relay_manager.add_subscription(subscription_id, Filters([fltr]))
    relay_manager.open_connections({"cert_reqs": 0})

    start_time = time.time()
    while time.time() - start_time < 5:
        relay_manager.run_sync()
        while relay_manager.message_pool.has_events():
            event_msg = relay_manager.message_pool.get_event()
            print(f"\nEvent from {event_msg.event.pub_key[:8]}...")
            print("Content:", event_msg.event.content)

    relay_manager.close_subscription(subscription_id)
    relay_manager.close_connections()

if __name__ == "__main__":
    main()
