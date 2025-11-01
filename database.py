import sqlite3
import os
from typing import Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create users and codes tables."""
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                number TEXT
            );

            CREATE TABLE IF NOT EXISTS codes (
                code TEXT PRIMARY KEY,
                description TEXT,
                availability INTEGER DEFAULT 1
            );
            """
        )
        conn.commit()


# Users helpers
def add_or_update_user(user_id: int, first_name: Optional[str] = None,
                       username: Optional[str] = None, number: Optional[str] = None) -> None:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (user_id, first_name, username, number)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name=excluded.first_name,
                username=excluded.username,
                number=excluded.number
            """,
            (user_id, first_name, username, number),
        )
        conn.commit()


def get_user(user_id: int) -> Optional[Tuple[int, str, str, str]]:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, first_name, username, number FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return tuple(row) if row else None


# Codes helpers
def add_code(code: str, description: str, availability: int = 1) -> None:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO codes (code, description, availability) VALUES (?, ?, ?)",
            (code, description, availability),
        )
        conn.commit()


def get_code(code: str) -> Optional[Tuple[str, str, int]]:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT code, description, availability FROM codes WHERE code = ?", (code,))
        row = cur.fetchone()
        return tuple(row) if row else None


def set_code_availability(code: str, available: bool) -> None:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE codes SET availability = ? WHERE code = ?", (1 if available else 0, code))
        conn.commit()


def get_code_info(code: str) -> Optional[Tuple[str, str, bool]]:
    """
    Return (description, expiry_date, is_used) or None if not found.
    expiry_date is not stored in the current schema, so we return "N/A".
    is_used is True when availability == 0.
    """
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT description, availability FROM codes WHERE code = ?", (code,))
        row = cur.fetchone()
        if not row:
            return None
        description, availability = row
        expiry_date = "N/A"
        is_used = (availability == 0)
        return (description, expiry_date, is_used)


def mark_code_used(code: str) -> None:
    """Mark a code as used by setting availability = 0."""
    set_code_availability(code, False)


if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DB_PATH)