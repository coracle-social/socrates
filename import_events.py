import sqlite3
import json
import os

def main():
    # 1. Paths to your DB and JSON
    db_path = "nostr_dvm.db"         # If it's in the same folder
    json_path = "groups_chat.json"   # Also in the same folder

    # 2. Connect to the database
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found!")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 3. Check if events table exists (optional safety check)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    table_info = cursor.fetchone()
    if not table_info:
        print("Error: 'events' table does not exist in this DB.")
        conn.close()
        return

    # 4. Read lines from the JSON file
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found!")
        conn.close()
        return

    with open(json_path, "r", encoding="utf-8") as f:
        line_count = 0
        inserted_count = 0
        for line in f:
            line = line.strip()
            if not line:
                continue

            line_count += 1
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                print("Skipping malformed line:", line)
                continue

            # Extract fields
            event_id = event.get("id")
            kind = event.get("kind", 0)
            content = event.get("content", "")
            created_at = event.get("created_at", 0)
            pubkey = event.get("pubkey", "")
            # If your table has a 'tags' column, store them as JSON
            tags = json.dumps(event.get("tags", []))

            # 5. Insert into 'events' table
            # Adjust to match your table schema:
            # events (id TEXT PRIMARY KEY, pubkey TEXT, kind INTEGER, content TEXT, created_at INTEGER, tags TEXT)
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO events (id, pubkey, kind, content, created_at, tags)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (event_id, pubkey, kind, content, created_at, tags))
                # If the event already exists, no row is added because of OR IGNORE
                if cursor.rowcount > 0:
                    inserted_count += 1
            except Exception as e:
                print(f"Error inserting event {event_id}: {e}")

    # 6. Commit and close
    conn.commit()
    conn.close()

    # 7. Print a summary
    print(f"Processed {line_count} lines from {json_path}.")
    print(f"Inserted {inserted_count} new rows into the 'events' table.")

if __name__ == "__main__":
    main()
