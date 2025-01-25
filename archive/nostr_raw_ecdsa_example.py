import asyncio
import websockets
import json
import ecdsa
from ecdsa.util import sigencode_string, sigdecode_string
import hashlib
import time

def low_s_sign_digest(privkey, digest):
    """Sign digest ensuring the S value is <= n/2."""
    # Temporarily sign (raw 64‐byte, but S could be high)
    raw_sig = privkey.sign_digest(digest, sigencode=sigencode_string)

    # Parse R, S from the signature
    r = int.from_bytes(raw_sig[:32], "big")
    s = int.from_bytes(raw_sig[32:], "big")

    # Curve order (SECP256k1)
    n = ecdsa.SECP256k1.order

    # If S is high, flip it
    if s > (n // 2):
        s = n - s

    # Rebuild the signature as 64 bytes (low‐S)
    r_bytes = r.to_bytes(32, "big")
    s_bytes = s.to_bytes(32, "big")
    fixed_sig = r_bytes + s_bytes

    return fixed_sig

# 1. Generate ephemeral private/public key
# Using ecdsa for secp256k1
privkey = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
pubkey_obj = privkey.get_verifying_key()

# Convert to hex strings
privkey_hex = privkey.to_string().hex()

# Extract the x-coordinate as a 32-byte value
x_coord = pubkey_obj.pubkey.point.x()
pubkey_hex = x_coord.to_bytes(32, "big").hex()
print("Pubkey length (hex):", len(pubkey_hex))  # Should be 64

print("Private key:", privkey_hex)
print("Public key: ", pubkey_hex)

async def send_nostr_event():
    # 2. Connect to a Nostr relay (raw WebSocket)
    relay_url = "wss://relay.snort.social"
    print(f"Connecting to {relay_url} ...")

    async with websockets.connect(relay_url) as ws:
        print("Connected.")

        # 3. Build a Nostr event
        created_at = int(time.time())
        kind = 1  # TEXT_NOTE
        content = "Hello from a minimal Nostr client!"
        tags = []
        
        # Nostr event structure: [0, pubkey, created_at, kind, tags, content]
        event_data = [
            0,
            pubkey_hex,
            created_at,
            kind,
            tags,
            content
        ]

        # Convert to JSON string for hashing
        event_json = json.dumps(event_data, separators=(',', ':'))

        # 4. Hash the event data using SHA-256
        event_hash_bytes = hashlib.sha256(event_json.encode('utf-8')).digest()
        event_id = event_hash_bytes.hex()
        
        # 5. Sign the event hash with our private key, with low-S:
        signature = low_s_sign_digest(privkey, event_hash_bytes)
        sig_hex = signature.hex()

        # LOCAL VERIFICATION STEP
        try:
            # pubkey_obj is your verifying key. We use .verify_digest() with sigdecode_string
            pubkey_obj.verify_digest(signature, event_hash_bytes, sigdecode=sigdecode_string)
            print("Local verify: Signature is valid.")
        except ecdsa.BadSignatureError:
            print("Local verify: Signature is INVALID.")
                
            
        # 6. Construct the final event object to send
        event_to_send = {
            "id": event_id,
            "pubkey": pubkey_hex,
            "created_at": created_at,
            "kind": kind,
            "tags": tags,
            "content": content,
            "sig": sig_hex
        }
        message = ["EVENT", event_to_send]
        
        # 7. Send the event
        await ws.send(json.dumps(message))
        print("Sent Event:", message)

        # 8. Listen for a response (OK message, etc.)
        try:
            reply = await asyncio.wait_for(ws.recv(), timeout=5)
            print("Relay Response:", reply)
        except asyncio.TimeoutError:
            print("No response from relay.")

    # 9. The connection closes automatically when exiting the async with-block
    print("Connection closed.")

# Run the async function
if __name__ == "__main__":
    asyncio.run(send_nostr_event())