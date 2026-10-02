import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "shadowaccess.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            username TEXT,
            locked INTEGER DEFAULT 0,
            created_at REAL,
            locked_at REAL
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            type TEXT,
            data TEXT,
            ts REAL
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            score INTEGER,
            status TEXT,
            reasons TEXT,
            ts REAL
        );
        INSERT OR IGNORE INTO users VALUES ('demo', 'demo123');
        INSERT OR IGNORE INTO users VALUES ('admin', 'admin123');
        """)