# generate_key.py

import os
import secrets

def get_or_create_privkey(filepath="secrets/my_static_key.hex"):
    """
    Generates or retrieves a static private key (hex string) from a file.
    By default, it stores/loads from secrets/my_static_key.hex.

    :param filepath: The file path where the key is stored or generated.
    :return: A hex-encoded private key string (64 chars for 32 bytes).
    """
    # Ensure the "secrets" directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if not os.path.exists(filepath):
        # Generate a new 32-byte key and write it as hex
        privkey_hex = secrets.token_hex(32)
        with open(filepath, "w") as f:
            f.write(privkey_hex)
        # Removed the print statement to avoid revealing the key
    else:
        with open(filepath, "r") as f:
            privkey_hex = f.read().strip()
        # Removed the print statement to avoid revealing the key

    return privkey_hex

if __name__ == "__main__":
    # If run directly, it will just create or load the key, but won't print anything.
    private_key_hex = get_or_create_privkey()
    # Omit the final print if you never want the key printed out.
    # For debugging only, you might re-enable with caution:
    # print("Your static private key (hex):", private_key_hex)
