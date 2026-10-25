import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("smartfix.learning")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
LEARNED_ERRORS_FILE = os.path.join(DATA_DIR, "learned_errors.json")

def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_learned_errors() -> Dict[str, dict]:
    """
    Returns a dictionary of learned errors.
    Key: repair_id
    Value: { "error_info": { ... }, "ps_script": "..." }
    """
    _ensure_data_dir()
    if not os.path.exists(LEARNED_ERRORS_FILE):
        return {}
    try:
        with open(LEARNED_ERRORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load learned errors: {e}")
        return {}

def save_learned_error(error_info: dict, ps_script: str):
    """
    Saves a new learned error. Overwrites if a similar signature exists.
    Generates a unique repair_id based on the error name or signature.
    """
    _ensure_data_dir()
    learned = load_learned_errors()
    
    
    base_name = error_info.get("name", "Unknown").lower().replace(" ", "_").replace("/", "_")
    base_name = "".join([c for c in base_name if c.isalnum() or c == '_'])
    repair_id = f"learned_{base_name}"
    
    
    new_error_info = error_info.copy()
    new_error_info["id"] = repair_id
    new_error_info["repair_id"] = repair_id
    
    learned[repair_id] = {
        "error_info": new_error_info,
        "ps_script": ps_script
    }
    
    try:
        with open(LEARNED_ERRORS_FILE, 'w', encoding='utf-8') as f:
            json.dump(learned, f, indent=4)
        logger.info(f"Successfully learned and saved new repair: {repair_id}")
    except Exception as e:
        logger.error(f"Failed to save learned error: {e}")
