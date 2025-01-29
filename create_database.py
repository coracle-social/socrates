import sqlite3

# Create a SQLite database file
conn = sqlite3.connect("nostr_dvm.db")
cursor = conn.cursor()

# Create the events table
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

print("Database and table created successfully!")
conn.commit()
conn.close()