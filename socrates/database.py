import sqlite3
import json
import logging
import os
import yaml
from socrates.config import config

def get_db_connection():
    """
    Returns a SQLite database connection. Ensures the directory for the database exists.
    """
    db_settings = config.get("database", {})
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_relative_path = db_settings.get("path", "data/events.db")
    db_path = os.path.join(current_dir, db_relative_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """
    Initializes the SQLite database by creating the 'nostr_events' table if it does not already exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nostr_events (
            id TEXT PRIMARY KEY,
            pubkey TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            kind INTEGER,
            content TEXT,
            tags TEXT,
            processed BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    logging.info("Database initialized and table created if not exists.")

def insert_event(event):
    """
    Inserts a Nostr event into the database using an upsert/ignore strategy.
    
    Expects event to be a dictionary with at least the following keys:
      - id, pubkey, created_at, kind, content,
      - tags (optional).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    tags = event.get("tags")
    tags_str = json.dumps(tags) if tags is not None else None

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO nostr_events (id, pubkey, created_at, kind, content, tags, processed)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (
            event.get("id"),
            event.get("pubkey"),
            event.get("created_at"),
            event.get("kind"),
            event.get("content"),
            tags_str
        ))
        conn.commit()
        if cursor.rowcount == 0:
            logging.info(f"Event {event.get('id')} already exists, skipping insert.")
        else:
            logging.info(f"Inserted event {event.get('id')}.")
    except Exception as e:
        logging.error(f"Error inserting event {event.get('id')}: {e}")
    finally:
        conn.close()

def get_unprocessed_events():
    """
    Retrieves unprocessed events (processed = 0) from the database, ordered by creation time.
    Returns a list of events as dictionaries. JSON-decoded tags are included when present.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nostr_events WHERE processed = 0 ORDER BY created_at")
    rows = cursor.fetchall()
    events = []
    for row in rows:
        event = dict(row)
        if event.get("tags"):
            try:
                event["tags"] = json.loads(event["tags"])
            except Exception:
                event["tags"] = None
        events.append(event)
    conn.close()
    return events

def mark_events_processed(event_ids):
    """
    Marks the provided event IDs as processed (sets processed = 1) in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany("UPDATE nostr_events SET processed = 1 WHERE id = ?", [(e_id,) for e_id in event_ids])
        conn.commit()
        logging.info(f"Marked {cursor.rowcount} events as processed.")
    except Exception as e:
        logging.error(f"Error marking events as processed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_db()
