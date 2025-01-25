import asyncio
import websockets
import json
import secp256k1
import hashlib
import time
import secrets

async def main():
    # 1) Generate a random 32-byte private key
    privkey_bytes = secrets.token_bytes(32)
    privkey = secp256k1.PrivateKey(privkey_bytes)

    # 2) Build x-only public key (remove the 0x02/0x03 prefix)
    compressed_pubkey = privkey.pubkey.serialize(compressed=True)
    xonly_hex = compressed_pubkey[1:].hex()
    print("Private key (hex):", privkey_bytes.hex())
    print("Public key (x-only hex):", xonly_hex)

    # 3) Create the event
    created_at = int(time.time())
    kind = 1  # TEXT_NOTE
    tags = []
    content = "Hello World!"
    event_data = [0, xonly_hex, created_at, kind, tags, content]
    event_json = json.dumps(event_data, separators=(",", ":"))
    event_hash_bytes = hashlib.sha256(event_json.encode("utf-8")).digest()
    event_id_hex = event_hash_bytes.hex()

    # Schnorr sign (64-byte signature)
    signature_raw = privkey.schnorr_sign(event_hash_bytes, bip340tag=None, raw=True)
    sig_hex = signature_raw.hex()

    event_message = {
        "id": event_id_hex,
        "pubkey": xonly_hex,
        "created_at": created_at,
        "kind": kind,
        "tags": tags,
        "content": content,
        "sig": sig_hex
    }

    # We'll connect to an example relay:
    relay_url = "wss://nos.lol"
    print(f"Connecting to {relay_url} ...")

    async with websockets.connect(relay_url) as ws:
        print("Connected.")

        # 4) Publish (send) the event
        client_message = ["EVENT", event_message]
        await ws.send(json.dumps(client_message))
        print("Event sent:", client_message)

        # 5) See if the relay acknowledges it
        try:
            ack = await asyncio.wait_for(ws.recv(), timeout=5)
            print("Relay response:", ack)
        except asyncio.TimeoutError:
            print("No relay response on publish.")

        # 6) Now subscribe to read that event back
        sub_id = "mysub"
        subscription_req = ["REQ", sub_id, {"authors": [xonly_hex], "kinds": [1]}]
        await ws.send(json.dumps(subscription_req))


        # 7) Listen for incoming messages
        try:
            while True:
                reply = await asyncio.wait_for(ws.recv(), timeout=10)
                print("Subscription response:", reply)

                # Typically, messages come in the form:
                # ["EVENT", <sub_id>, <event_object>] or ["EOSE", <sub_id>]
                data = json.loads(reply)

                if data[0] == "EVENT" and data[1] == sub_id:
                    # We got an event back from the relay
                    returned_event = data[2]
                    print("Received event from subscription:", returned_event)

                elif data[0] == "EOSE" and data[1] == sub_id:
                    # End Of Stored Events
                    print("End of stored events for this subscription.")
                    # We can close out the subscription if we want:
                    close_req = ["CLOSE", sub_id]
                    await ws.send(json.dumps(close_req))
                    break  # exit the loop
        except asyncio.TimeoutError:
            print("No more subscription messages. Exiting.")

    print("Connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
