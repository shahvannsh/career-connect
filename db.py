import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "jobswipe.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        name TEXT DEFAULT '',
        title TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        photo TEXT DEFAULT '',
        resume TEXT DEFAULT '',
        skills TEXT DEFAULT '',
        linkedin_connected INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS saved (
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        job_id INTEGER,
        PRIMARY KEY (user_id, job_id)
    );

    CREATE TABLE IF NOT EXISTS applied (
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        job_id INTEGER,
        applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, job_id)
    );

    CREATE TABLE IF NOT EXISTS skipped (
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        job_id INTEGER,
        PRIMARY KEY (user_id, job_id)
    );
    """)
    conn.commit()
    conn.close()
