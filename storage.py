"""Tracks which articles have already been posted, so we never repeat one."""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent / "seen_articles.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen (
            id TEXT PRIMARY KEY,
            posted_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def has_seen(article_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT 1 FROM seen WHERE id = ?", (article_id,))
    result = cur.fetchone() is not None
    conn.close()
    return result


def mark_seen(article_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO seen (id, posted_at) VALUES (?, ?)",
        (article_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def prune_old(days: int = 30):
    """Keep the DB small by forgetting very old entries."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM seen WHERE posted_at < ?", (cutoff,))
    conn.commit()
    conn.close()
