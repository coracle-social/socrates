# db_utils.py
#
# Purpose:
#   - Creates and manages a single "events" table in SQLite.
#   - Provides functions to insert and retrieve events.
#
# NOTE:
#   This version has no optional/specialized tables—everything
#   goes into "events" to simplify searching across kinds.

import sqlite3
import json
import os
from typing import Optional, List, Dict

# Build the path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "nostr_dvm.db")
print(f"[db_utils] Using DB_PATH={DB_PATH}")

def init_db():
    """
    Initialize the database by creating the 'events' table if it doesn't exist.
    We'll store all events in one table, regardless of kind (9, 11, 1111, etc.).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Single table for all events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            pubkey TEXT,
            kind INTEGER,
            content TEXT,
            created_at INTEGER,
            tags TEXT
        )
    """)

    conn.commit()
    conn.close()

def insert_event(event_data: dict):
    """
    Insert an event into the single 'events' table.
    This function is called for all kinds (9, 11, 1111, etc.).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Convert the tags list to JSON before storing
    cursor.execute("""
        INSERT OR IGNORE INTO events (id, pubkey, kind, content, created_at, tags)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        event_data["id"],
        event_data["pubkey"],
        event_data["kind"],
        event_data["content"],
        event_data["created_at"],
        json.dumps(event_data["tags"])
    ))

    conn.commit()
    conn.close()

def get_event_by_id(event_id: str) -> Optional[dict]:
    """
    Retrieve a single event by ID from the 'events' table.
    Returns a dict of the event fields, or None if not found.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, pubkey, kind, content, created_at, tags
        FROM events
        WHERE id = ?
    """, (event_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "pubkey": row[1],
            "kind": row[2],
            "content": row[3],
            "created_at": row[4],
            "tags": json.loads(row[5]) if row[5] else []
        }
    else:
        return None

def get_events_by_kind(kind: int) -> List[dict]:
    """
    Retrieve all events of a certain kind (9, 11, 1111, etc.)
    from the 'events' table, ordered by newest first.
    Returns a list of event dicts.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, pubkey, kind, content, created_at, tags
        FROM events
        WHERE kind = ?
        ORDER BY created_at DESC
    """, (kind,))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "pubkey": row[1],
            "kind": row[2],
            "content": row[3],
            "created_at": row[4],
            "tags": json.loads(row[5]) if row[5] else []
        })
    return results