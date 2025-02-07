import time
import logging

from nostr.key import PrivateKey
from nostr.event import Event
from nostr.filter import Filter, Filters
from nostr.relay_manager import RelayManager

from generate_key import get_or_create_privkey  # Load or create static key
import db_utils  # Our DB utility module


def main():
    logging.basicConfig(level=logging.INFO)

    # 1) Initialize the DB (creates 'events' table if not present)
    db_utils.init_db()

    # 2) Load (or create) the private key
    privkey_hex = get_or_create_privkey("secrets/my_static_key.hex")
    private_key = PrivateKey(bytes.fromhex(privkey_hex))
    pubkey_hex = private_key.public_key.hex()

    # 3) Connect to the single relay
    relay_manager = RelayManager()
    relay_url = "wss://bucket.coracle.social"
    relay_manager.add_relay(relay_url)
    logging.info(f"Connecting to relay: {relay_url}")

    # -----------------------
    # Publish events in order
    # -----------------------

    channel_name = "Nostr Dev Chat (Test)"

    # (A) Kind 11: Channel creation
    channel_event = Event(f"Creating channel: {channel_name}")
    channel_event.kind = 11
    channel_event.tags.append(["name", channel_name])
    private_key.sign_event(channel_event)
    relay_manager.publish_event(channel_event)
    logging.info(f"[Time 0] Published Kind=11 (channel). id={channel_event.id}")
    time.sleep(2)

    # (B) Kind 9: Chat messages referencing the channel
    chat1 = Event("Hello, everyone! (Test chat #1)")
    chat1.kind = 9
    chat1.tags.append(["c", channel_name])
    private_key.sign_event(chat1)
    relay_manager.publish_event(chat1)
    logging.info(f"[Time 1] Published Kind=9 (chat). id={chat1.id}")
    time.sleep(2)

    chat2 = Event("Hey there! (Test chat #2)")
    chat2.kind = 9
    chat2.tags.append(["c", channel_name])
    private_key.sign_event(chat2)
    relay_manager.publish_event(chat2)
    logging.info(f"[Time 2] Published Kind=9 (chat). id={chat2.id}")
    time.sleep(2)

    # (C) Kind 1111: Thread replies referencing specific events
    reply_to_chat1 = Event("Replying to your message #1")
    reply_to_chat1.kind = 1111
    reply_to_chat1.tags.append(["e", chat1.id])
    reply_to_chat1.tags.append(["p", pubkey_hex])  # mention the author
    private_key.sign_event(reply_to_chat1)
    relay_manager.publish_event(reply_to_chat1)
    logging.info(f"[Time 3] Published Kind=1111 (reply to chat1). id={reply_to_chat1.id}")
    time.sleep(2)

    reply_to_chat2 = Event("Another reply, referencing chat #2")
    reply_to_chat2.kind = 1111
    reply_to_chat2.tags.append(["e", chat2.id])
    reply_to_chat2.tags.append(["p", pubkey_hex])
    private_key.sign_event(reply_to_chat2)
    relay_manager.publish_event(reply_to_chat2)
    logging.info(f"[Time 4] Published Kind=1111 (reply to chat2). id={reply_to_chat2.id}")
    time.sleep(2)

    # -----------------------
    # Subscribe to these events & store them in DB
    # -----------------------
    subscription_id = "mysub"
    filter_kinds = [9, 11, 1111]
    filters = Filters([Filter(authors=[pubkey_hex], kinds=filter_kinds)])
    relay_manager.add_subscription_on_all_relays(subscription_id, filters)
    logging.info(f"Subscription created for kinds={filter_kinds}. Listening...")

    # 4) Listen ~10s for incoming events and store them
    start_time = time.time()
    listen_seconds = 10

    while time.time() - start_time < listen_seconds:
        if relay_manager.message_pool.has_events():
            incoming_msg = relay_manager.message_pool.get_event()
            if incoming_msg and incoming_msg.event:
                e = incoming_msg.event
                logging.info(f"Received event: kind={e.kind}, id={e.id}, content={e.content}")

                # Convert the event to a dict for DB insertion
                event_data = {
                    "id": e.id,
                    "pubkey": e.public_key,
                    "kind": e.kind,
                    "content": e.content,
                    "created_at": e.created_at,
                    "tags": e.tags  # a list of lists
                }
                db_utils.insert_event(event_data)
                logging.info(f"Inserted event {e.id} into the local DB.")

    # 5) Clean up
    relay_manager.close_all_relay_connections()
    logging.info("Closed relay connection. Exiting.")


if __name__ == "__main__":
    main()
