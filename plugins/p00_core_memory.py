import os
import sqlite3
import threading
import json
from datetime import datetime

_memory_conn = None
_memory_lock = threading.Lock()
AI_DATA_DIR = os.path.expanduser("~/.jarvis/.ai")
MEMORY_DB = os.path.join(AI_DATA_DIR, "memory.db")


def _get_memory_conn():
    global _memory_conn
    if _memory_conn is None:
        os.makedirs(AI_DATA_DIR, exist_ok=True)
        _memory_conn = sqlite3.connect(MEMORY_DB, timeout=30, check_same_thread=False)
        _memory_conn.execute("PRAGMA journal_mode=WAL")
        _memory_conn.execute("PRAGMA synchronous=NORMAL")
        _memory_conn.execute("PRAGMA busy_timeout=30000")  # wait up to 30s on lock
        _init_db(_memory_conn)
    return _memory_conn


def _init_db(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, key)
        )
    """)
    # Migration: add updated_at if missing (existing DBs)
    try:
        cursor.execute("SELECT updated_at FROM facts LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE facts ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_stats (
            id INTEGER PRIMARY KEY,
            total_queries INTEGER DEFAULT 0,
            last_search TIMESTAMP
        )
    """)
    conn.commit()


def save_fact(category: str, key: str, value: str):
    """Save a fact to persistent memory. Overwrites existing value."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                """INSERT OR REPLACE INTO facts (category, key, value, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (category, key, value, now),
            )
            conn.commit()
        return f"Remembered: [{category}] {key} = {value}"
    except sqlite3.Error as exc:
        return f"Memory write error: {exc}"


def get_fact(category: str, key: str):
    """Read a single fact from persistent memory."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value, updated_at FROM facts WHERE category = ? AND key = ?",
                (category, key),
            )
            row = cursor.fetchone()
        if row:
            return f"[{category}] {key}: {row[0]} (updated: {row[1][:10]})"
        return f"No fact found for key: {key} in category: {category}"
    except sqlite3.Error as exc:
        return f"Memory read error: {exc}"


def search_memories(query: str):
    """Search all memories for a query string in key or value."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT category, key, value, updated_at FROM facts
                   WHERE key LIKE ? OR value LIKE ? OR category LIKE ?
                   ORDER BY updated_at DESC LIMIT 20""",
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
            rows = cursor.fetchall()
        if not rows:
            return f"No memories found for: {query}"
        lines = [f"Found {len(rows)} memories for '{query}':"]
        for cat, key, val, updated in rows:
            lines.append(f"  [{cat}] {key}: {val[:80]}{'...' if len(val) > 80 else ''}")
        return "\n".join(lines)
    except sqlite3.Error as exc:
        return f"Memory search error: {exc}"


def delete_memory(category: str, key: str):
    """Delete a specific memory by category and key."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM facts WHERE category = ? AND key = ?",
                (category, key),
            )
            conn.commit()
            if cursor.rowcount > 0:
                return f"Deleted memory: [{category}] {key}"
            return f"No memory found to delete: [{category}] {key}"
    except sqlite3.Error as exc:
        return f"Memory delete error: {exc}"


def get_all_memories():
    """Get all memories formatted for display."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT category, key, value, updated_at FROM facts
                   ORDER BY category, updated_at DESC"""
            )
            rows = cursor.fetchall()
        if not rows:
            return "No memories stored yet."
        lines = ["=== ALL MEMORIES ==="]
        current_cat = None
        for cat, key, val, updated in rows:
            if cat != current_cat:
                lines.append(f"\n[{cat.upper()}]")
                current_cat = cat
            date = updated[:10] if updated else "?"
            lines.append(f"  {key}: {val[:100]}{'...' if len(val) > 100 else ''} ({date})")
        return "\n".join(lines)
    except sqlite3.Error as exc:
        return f"Memory read error: {exc}"


def append_memory(category: str, key: str, value: str):
    """Append to an existing memory value (for lists/history)."""
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
                # Try to parse as JSON list, otherwise append with newline
                try:
                    existing = json.loads(row[0])
                    if isinstance(existing, list):
                        existing.append(value)
                        new_value = json.dumps(existing)
                    else:
                        new_value = row[0] + "\n" + value
                except (json.JSONDecodeError, TypeError):
                    new_value = row[0] + "\n" + value
            else:
                new_value = value

            now = datetime.now().isoformat()
            cursor.execute(
                """INSERT OR REPLACE INTO facts (category, key, value, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (category, key, new_value, now),
            )
            conn.commit()
        return f"Appended to [{category}] {key}"
    except sqlite3.Error as exc:
        return f"Memory append error: {exc}"


def get_memory_stats():
    """Get memory statistics."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM facts")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT category, COUNT(*) FROM facts GROUP BY category")
            by_category = cursor.fetchall()
            cursor.execute("SELECT SUM(LENGTH(value)) FROM facts")
            size_chars = cursor.fetchone()[0] or 0
        lines = [f"=== MEMORY STATS ===", f"Total memories: {total}", f"Approx size: {size_chars // 1024}KB"]
        if by_category:
            lines.append("By category:")
            for cat, count in by_category:
                lines.append(f"  [{cat}]: {count}")
        return "\n".join(lines)
    except sqlite3.Error as exc:
        return f"Memory stats error: {exc}"


def save_conversation(role: str, content: str):
    """Save a conversation turn to history."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (role, content) VALUES (?, ?)",
                (role, content),
            )
            conn.commit()
        return "Conversation saved"
    except sqlite3.Error as exc:
        return f"Conversation save error: {exc}"


def get_recent_conversations(limit: int = 10):
    """Get recent conversation history."""
    try:
        with _memory_lock:
            conn = _get_memory_conn()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT role, content, timestamp FROM conversations
                   ORDER BY id DESC LIMIT ?""",
                (limit,),
            )
            rows = cursor.fetchall()
        if not rows:
            return "No conversation history."
        lines = ["=== RECENT CONVERSATION ==="]
        for role, content, ts in reversed(rows):
            lines.append(f"[{role}] {content[:150]}{'...' if len(content) > 150 else ''}")
        return "\n".join(lines)
    except sqlite3.Error as exc:
        return f"Conversation read error: {exc}"


# Backward-compatible aliases
def save_memory(category: str, key: str, value: str):
    return save_fact(category, key, value)


def get_memory(category: str, key: str):
    return get_fact(category, key)


def manage_memory(action: str, category: str = "", key: str = "", value: str = "", query: str = "", limit: int = 10, role: str = "", content: str = ""):
    """Manage AI memory and conversation history. Use actions: 'save_fact', 'get_fact', 'search', 'delete', 'get_all', 'append', 'stats', 'save_conversation', 'get_recent_conversations'."""
    if action == "save_fact": return save_fact(category, key, value)
    elif action == "get_fact": return get_fact(category, key)
    elif action == "search": return search_memories(query)
    elif action == "delete": return delete_memory(category, key)
    elif action == "get_all": return get_all_memories()
    elif action == "append": return append_memory(category, key, value)
    elif action == "stats": return get_memory_stats()
    elif action == "save_conversation": return save_conversation(role, content)
    elif action == "get_recent_conversations": return get_recent_conversations(limit)
    else: return "Unknown action."

def register_plugin():
    tools = [manage_memory]
    mapping = {"manage_memory": manage_memory}
    return tools, mapping
