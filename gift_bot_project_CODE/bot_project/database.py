"""
SQLite database module.
Three tables: users, sessions, feedback.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("gift_bot.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they do not exist."""
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                profile_data_json TEXT NOT NULL,
                strategy_used TEXT NOT NULL,
                response_json TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                rating_relevance INTEGER,
                rating_creativity INTEGER,
                rating_specificity INTEGER,
                comment TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)


def save_user(telegram_id: int, username: str) -> int:
    """Insert user if not exists. Return the internal id."""
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username),
        )
        row = c.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        return row["id"]


def save_session(telegram_id: int, profile: dict, strategy: str, response: dict) -> int:
    """Save one recommendation session. Return session id."""
    user_id = save_user(telegram_id, "")
    with _conn() as c:
        cur = c.execute(
            """
            INSERT INTO sessions (user_id, profile_data_json, strategy_used, response_json)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, json.dumps(profile), strategy, json.dumps(response)),
        )
        return cur.lastrowid


def save_feedback(
    session_id: int,
    rating_relevance: int | None,
    rating_creativity: int | None,
    rating_specificity: int | None,
    comment: str,
) -> None:
    """Save user feedback for one session."""
    with _conn() as c:
        c.execute(
            """
            INSERT INTO feedback
            (session_id, rating_relevance, rating_creativity, rating_specificity, comment)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, rating_relevance, rating_creativity, rating_specificity, comment),
        )


def get_user_sessions(telegram_id: int, limit: int = 5) -> list[sqlite3.Row]:
    """Return last sessions of a user."""
    with _conn() as c:
        return c.execute(
            """
            SELECT s.* FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE u.telegram_id = ?
            ORDER BY s.id DESC
            LIMIT ?
            """,
            (telegram_id, limit),
        ).fetchall()
