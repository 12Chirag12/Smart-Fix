"""
SmartFix AI — Repair History Module
Tracks all detected errors and repair outcomes in SQLite database.
Thread-safe with WAL mode for concurrent multi-thread access.
"""
import sqlite3
import os
import json
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "smartfix_history.db")

# ── Thread-safe database access ───────────────────────────────────────────────
_db_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    """Get or create the singleton thread-safe SQLite connection with WAL mode."""
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA busy_timeout=5000")
    return _conn


def init_db():
    with _db_lock:
        conn = _get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS repair_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                error_id TEXT NOT NULL,
                error_name TEXT NOT NULL,
                category TEXT,
                severity TEXT,
                action TEXT NOT NULL,
                repair_id TEXT,
                success INTEGER,
                output TEXT,
                elapsed_seconds REAL,
                system_snapshot TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS restore_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                description TEXT,
                before_repair_id TEXT,
                success INTEGER DEFAULT 0
            )
        """)
        conn.commit()


def log_detection(error_info: dict):
    with _db_lock:
        conn = _get_conn()
        conn.execute("""
            INSERT INTO repair_history (timestamp, error_id, error_name, category, severity, action)
            VALUES (?, ?, ?, ?, ?, 'DETECTED')
        """, (
            datetime.now().isoformat(),
            error_info.get("id", ""),
            error_info.get("name", ""),
            error_info.get("category", ""),
            error_info.get("severity", ""),
        ))
        conn.commit()


def log_repair(error_info: dict, result: dict):
    with _db_lock:
        conn = _get_conn()
        conn.execute("""
            INSERT INTO repair_history (timestamp, error_id, error_name, category, severity, action, repair_id, success, output, elapsed_seconds)
            VALUES (?, ?, ?, ?, ?, 'REPAIRED', ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            error_info.get("id", ""),
            error_info.get("name", ""),
            error_info.get("category", ""),
            error_info.get("severity", ""),
            result.get("repair_id", ""),
            1 if result.get("success") else 0,
            result.get("output", "")[:2000],
            result.get("elapsed_seconds", 0),
        ))
        conn.commit()


def log_ignore(error_info: dict):
    with _db_lock:
        conn = _get_conn()
        conn.execute("""
            INSERT INTO repair_history (timestamp, error_id, error_name, category, severity, action)
            VALUES (?, ?, ?, ?, ?, 'IGNORED')
        """, (
            datetime.now().isoformat(),
            error_info.get("id", ""),
            error_info.get("name", ""),
            error_info.get("category", ""),
            error_info.get("severity", ""),
        ))
        conn.commit()


def log_restore_point(description: str, repair_id: str, success: bool):
    """Log a system restore point creation attempt."""
    with _db_lock:
        conn = _get_conn()
        conn.execute("""
            INSERT INTO restore_points (timestamp, description, before_repair_id, success)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            description,
            repair_id,
            1 if success else 0,
        ))
        conn.commit()


def get_history(limit: int = 200) -> List[dict]:
    with _db_lock:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT * FROM repair_history ORDER BY timestamp DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_stats() -> dict:
    with _db_lock:
        conn = _get_conn()
        total     = conn.execute("SELECT COUNT(*) FROM repair_history").fetchone()[0]
        detected  = conn.execute("SELECT COUNT(*) FROM repair_history WHERE action='DETECTED'").fetchone()[0]
        repaired  = conn.execute("SELECT COUNT(*) FROM repair_history WHERE action='REPAIRED'").fetchone()[0]
        success   = conn.execute("SELECT COUNT(*) FROM repair_history WHERE action='REPAIRED' AND success=1").fetchone()[0]
        ignored   = conn.execute("SELECT COUNT(*) FROM repair_history WHERE action='IGNORED'").fetchone()[0]
        return {
            "total": total, "detected": detected,
            "repaired": repaired, "success": success,
            "failed": repaired - success, "ignored": ignored,
        }


def get_category_stats() -> List[dict]:
    """Get repair success rates grouped by error category for analytics."""
    with _db_lock:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT category,
                   COUNT(*) as attempts,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
            FROM repair_history
            WHERE action = 'REPAIRED' AND category != ''
            GROUP BY category
            ORDER BY attempts DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_recent_failures(error_id: str, limit: int = 5) -> int:
    """Count recent consecutive failures for a specific error (for escalation logic)."""
    with _db_lock:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT success FROM repair_history
            WHERE error_id = ? AND action = 'REPAIRED'
            ORDER BY timestamp DESC LIMIT ?
        """, (error_id, limit)).fetchall()
        count = 0
        for row in rows:
            if row[0] == 0:
                count += 1
            else:
                break
        return count


def clear_history():
    with _db_lock:
        conn = _get_conn()
        conn.execute("DELETE FROM repair_history")
        conn.commit()


try:
    init_db()
except Exception:
    pass
