import sqlite3
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path

def init_db(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        is_private INTEGER,
        last_seen TIMESTAMP
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        username TEXT,
        post_id TEXT,
        type TEXT,
        timestamp TIMESTAMP
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS status (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        running BOOLEAN NOT NULL,
        last_updated TIMESTAMP NOT NULL
    )
    """)

    conn.commit()
    return conn

def set_status(conn, running: bool):
    with closing(conn.cursor()) as c:
        c.execute('''
            INSERT INTO status (id, running, last_updated)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET running=excluded.running, last_updated=excluded.last_updated
        ''', (running, datetime.now(timezone.utc).isoformat()))
        conn.commit()

def get_daily_counts_range(conn, start_dt, end_dt):
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ?", (start_dt.isoformat(), end_dt.isoformat()))
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ? AND type = 'comment'", (start_dt.isoformat(), end_dt.isoformat()))
    comments = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ? AND type = 'like'", (start_dt.isoformat(), end_dt.isoformat()))
    likes = c.fetchone()[0]

    return total, comments, likes