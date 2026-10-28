"""
SmartFix AI — Self-Learning Repair Database
Manages AI-learned error repairs with thread-safe file operations and atomic writes.
Prevents data corruption from concurrent access across monitor and UI threads.
"""
import os
import json
import logging
import threading
from typing import Dict, Any

logger = logging.getLogger("smartfix.learning")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
LEARNED_ERRORS_FILE = os.path.join(DATA_DIR, "learned_errors.json")

# ── Thread-safe file access ───────────────────────────────────────────────────
_file_lock = threading.Lock()


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_learned_errors() -> Dict[str, dict]:
    """
    Returns a dictionary of learned errors (thread-safe read).
    Key: repair_id
    Value: { "error_info": { ... }, "ps_script": "..." }
    """
    with _file_lock:
        _ensure_data_dir()
        if not os.path.exists(LEARNED_ERRORS_FILE):
            return {}
        try:
            with open(LEARNED_ERRORS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    logger.warning("Learned errors file contains invalid data format — resetting")
                    return {}
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted learned errors JSON — attempting recovery: {e}")
            # Attempt recovery from backup
            backup_path = LEARNED_ERRORS_FILE + ".bak"
            if os.path.exists(backup_path):
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
            return {}
        except Exception as e:
            logger.error(f"Failed to load learned errors: {e}")
            return {}


def save_learned_error(error_info: dict, ps_script: str):
    """
    Saves a new learned error with atomic write (write → tmp → rename).
    Thread-safe. Overwrites if a similar signature exists.
    Generates a unique repair_id based on the error name or signature.
    """
    with _file_lock:
        _ensure_data_dir()

        # Load existing data
        learned = {}
        if os.path.exists(LEARNED_ERRORS_FILE):
            try:
                with open(LEARNED_ERRORS_FILE, 'r', encoding='utf-8') as f:
                    learned = json.load(f)
            except Exception:
                learned = {}

        # Generate deterministic repair_id from error name
        base_name = error_info.get("name", "Unknown").lower().replace(" ", "_").replace("/", "_")
        base_name = "".join([c for c in base_name if c.isalnum() or c == '_'])
        repair_id = f"learned_{base_name}"

        # Build the entry
        new_error_info = error_info.copy()
        new_error_info["id"] = repair_id
        new_error_info["repair_id"] = repair_id

        learned[repair_id] = {
            "error_info": new_error_info,
            "ps_script": ps_script
        }

        # Atomic write: write to .tmp, then rename (safe on NTFS)
        try:
            tmp_path = LEARNED_ERRORS_FILE + ".tmp"
            backup_path = LEARNED_ERRORS_FILE + ".bak"

            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(learned, f, indent=4, ensure_ascii=False)

            # Create backup of current file before replacing
            if os.path.exists(LEARNED_ERRORS_FILE):
                try:
                    os.replace(LEARNED_ERRORS_FILE, backup_path)
                except Exception:
                    pass

            os.replace(tmp_path, LEARNED_ERRORS_FILE)
            logger.info(f"Successfully learned and saved new repair: {repair_id}")
        except Exception as e:
            logger.error(f"Failed to save learned error: {e}")
            # Clean up tmp file on failure
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass


def remove_learned_error(repair_id: str) -> bool:
    """Remove a learned error by its repair_id (thread-safe, atomic)."""
    with _file_lock:
        if not os.path.exists(LEARNED_ERRORS_FILE):
            return False
        try:
            with open(LEARNED_ERRORS_FILE, 'r', encoding='utf-8') as f:
                learned = json.load(f)
            if repair_id not in learned:
                return False
            del learned[repair_id]
            tmp_path = LEARNED_ERRORS_FILE + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(learned, f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, LEARNED_ERRORS_FILE)
            logger.info(f"Removed learned repair: {repair_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove learned error: {e}")
            return False


def get_learned_count() -> int:
    """Return the number of learned repairs (for dashboard stats)."""
    try:
        return len(load_learned_errors())
    except Exception:
        return 0
