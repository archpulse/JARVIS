import os
import sqlite3
import threading

_memory_conn = None
_memory_lock = threading.Lock()
AI_DATA_DIR = os.path.expanduser("~/.axinix/.ai")
MEMORY_DB = os.path.join(AI_DATA_DIR, "memory.db")


def _get_memory_conn():
    global _memory_conn
    if _memory_conn is None:
        os.makedirs(AI_DATA_DIR, exist_ok=True)
        _memory_conn = sqlite3.connect(MEMORY_DB, timeout=10, check_same_thread=False)
        _memory_conn.execute("PRAGMA journal_mode=WAL")
        _memory_conn.execute("PRAGMA synchronous=NORMAL")
    return _memory_conn


def save_fact(category: str, key: str, value: str):
    """Save a fact to persistent memory."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, key)
                )
            """)
            cursor.execute(
                "INSERT OR REPLACE INTO facts (category, key, value) VALUES (?, ?, ?)",
                (category, key, value),
            )
            conn.commit()
        return f"Remembered: {key} = {value}"
    except sqlite3.Error as exc:
        return f"Memory write error: {exc}"


def get_fact(category: str, key: str):
    """Read a fact from persistent memory."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM facts WHERE category = ? AND key = ?",
                (category, key),
            )
            row = cursor.fetchone()
        if row:
            return f"{key}: {row[0]}"
        return f"No fact found for key: {key}"
    except sqlite3.Error as exc:
        return f"Memory read error: {exc}"


def save_memory(category: str, key: str, value: str):
    """Backward-compatible alias for save_fact."""
    return save_fact(category, key, value)


def get_memory(category: str, key: str):
    """Backward-compatible alias for get_fact."""
    return get_fact(category, key)


def register_plugin():
    tools = [save_fact, get_fact, save_memory, get_memory]
    mapping = {
        "save_fact": save_fact,
        "get_fact": get_fact,
        "save_memory": save_memory,
        "get_memory": get_memory,
    }
    return tools, mapping
