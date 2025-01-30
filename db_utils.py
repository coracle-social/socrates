# db_utils.py

import sqlite3
import json
import os
from typing import Optional, List, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "nostr_dvm.db")
print(f"[db_utils] Using DB_PATH={DB_PATH}")

def init_db():
    ...
    # same code

def insert_event(event_data: dict):
    ...
    # same code

def get_event_by_id(event_id: str) -> Optional[dict]:
    """
    Retrieve a single event by ID.
    Returns a dict with event fields or None if not found.
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
    Retrieve all events of a certain kind.
    Returns a list of dicts.
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