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
                quantity INTEGER DEFAULT 1
            );
            """
        )
        conn.commit()
        
        # Migrate from availability to quantity if needed
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='codes'")
            if cur.fetchone():
                # Check if availability column exists
                cur.execute("PRAGMA table_info(codes)")
                columns = [row[1] for row in cur.fetchall()]
                if 'availability' in columns and 'quantity' not in columns:
                    # Try RENAME COLUMN first (SQLite 3.25.0+)
                    try:
                        cur.execute("ALTER TABLE codes RENAME COLUMN availability TO quantity")
                        conn.commit()
                    except sqlite3.OperationalError:
                        # For older SQLite versions, recreate table
                        cur.execute("""
                            CREATE TABLE codes_new (
                                code TEXT PRIMARY KEY,
                                description TEXT,
                                quantity INTEGER DEFAULT 1
                            )
                        """)
                        cur.execute("""
                            INSERT INTO codes_new (code, description, quantity)
                            SELECT code, description, availability FROM codes
                        """)
                        cur.execute("DROP TABLE codes")
                        cur.execute("ALTER TABLE codes_new RENAME TO codes")
                        conn.commit()
        except sqlite3.OperationalError:
            # Table might not exist yet or migration not needed
            pass


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
def add_code(code: str, description: str, quantity: int = 1) -> None:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO codes (code, description, quantity) VALUES (?, ?, ?)",
            (code, description, quantity),
        )
        conn.commit()


def get_code(code: str) -> Optional[Tuple[str, str, int]]:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT code, description, quantity FROM codes WHERE code = ?", (code,))
        row = cur.fetchone()
        return tuple(row) if row else None


def set_code_quantity(code: str, quantity: int) -> None:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE codes SET quantity = ? WHERE code = ?", (quantity, code))
        conn.commit()


def decrement_code_quantity(code: str) -> None:
    """Decrement the quantity of a code by 1."""
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE codes SET quantity = quantity - 1 WHERE code = ? AND quantity > 0", (code,))
        conn.commit()


def get_code_info(code: str) -> Optional[Tuple[str, str, bool]]:
    """
    Return (description, expiry_date, is_available) or None if not found.
    expiry_date is not stored in the current schema, so we return "N/A".
    is_available is True when quantity > 0.
    """
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT description, quantity FROM codes WHERE code = ?", (code,))
        row = cur.fetchone()
        if not row:
            return None
        description, quantity = row
        expiry_date = "N/A"
        is_available = (quantity > 0)
        return (description, expiry_date, is_available)


def mark_code_used(code: str) -> None:
    """Decrement code quantity by 1 when used."""
    decrement_code_quantity(code)


if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DB_PATH)