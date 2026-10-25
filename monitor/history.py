"""
SmartFix AI — Repair History Module
Tracks all detected errors and repair outcomes in SQLite database.
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "smartfix_history.db")

def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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
            before_repair_id TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_detection(error_info: dict):
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
    conn.close()

def log_repair(error_info: dict, result: dict):
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
    conn.close()

def log_ignore(error_info: dict):
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
    conn.close()

def get_history(limit: int = 200) -> List[dict]:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT * FROM repair_history ORDER BY timestamp DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stats() -> dict:
    conn = _get_conn()
    total     = conn.execute("SELECT COUNT(*) FROM repair_history").fetchone()[0]
    detected  = conn.execute("SELECT COUNT(*) FROM repair_history WHERE action='DETECTED'").fetchone()[0]
    repaired  = conn.execute("SELECT COUNT(*) FROM repair_history WHERE action='REPAIRED'").fetchone()[0]
    success   = conn.execute("SELECT COUNT(*) FROM repair_history WHERE action='REPAIRED' AND success=1").fetchone()[0]
    ignored   = conn.execute("SELECT COUNT(*) FROM repair_history WHERE action='IGNORED'").fetchone()[0]
    conn.close()
    return {
        "total": total, "detected": detected,
        "repaired": repaired, "success": success,
        "failed": repaired - success, "ignored": ignored,
    }

def clear_history():
    conn = _get_conn()
    conn.execute("DELETE FROM repair_history")
    conn.commit()
    conn.close()


try:
    init_db()
except Exception:
    pass
