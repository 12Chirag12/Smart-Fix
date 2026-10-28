"""
SmartFix AI — Lab Monitor Shared Config & Protocol
Handles seat name persistence, protocol message helpers, and shared constants.
Includes protocol versioning, message size limits, and HMAC authentication.
"""
import json
import os
import socket
import hashlib
import hmac
import time
from typing import Any, Dict, Optional

LAB_PORT = int(os.getenv("SMARTFIX_LAB_PORT", "7771"))
DISCOVERY_PORT = int(os.getenv("SMARTFIX_DISCOVERY_PORT", "7772"))
LAB_AGENT_VERSION = "1.0"
PROTOCOL_VERSION = "1.1"  # Protocol version for future compatibility
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "lab_config.json")

# ── Protocol Constants ─────────────────────────────────────────────────────────
MAX_MESSAGE_SIZE = 1_048_576  # 1 MB — prevents memory exhaustion from oversized messages
MESSAGE_TIMEOUT  = 10.0       # Default socket timeout

# ── Message types ──────────────────────────────────────────────────────────────
MSG_PING          = "PING"
MSG_PONG          = "PONG"
MSG_STATUS        = "STATUS"          # Agent -> Admin: full status snapshot
MSG_REPAIR        = "REPAIR"          # Admin -> Agent: trigger a repair
MSG_REPAIR_RESULT = "REPAIR_RESULT"   # Agent -> Admin: result of a repair
MSG_GET_STATUS    = "GET_STATUS"      # Admin -> Agent: request a fresh status
MSG_SET_SEAT      = "SET_SEAT"        # Internal use
MSG_SHUTDOWN      = "SHUTDOWN"        # Admin -> Agent: graceful stop (future)


def _ensure_data_dir():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(data_dir, exist_ok=True)


def load_lab_config() -> Dict[str, Any]:
    """Load lab config from disk. Returns defaults if not found."""
    _ensure_data_dir()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"seat_name": "", "mode": "unset"}  # mode: "admin" | "client" | "unset"


def save_lab_config(cfg: Dict[str, Any]):
    """Persist lab config to disk."""
    _ensure_data_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_seat_name() -> str:
    seat = load_lab_config().get("seat_name", "").strip()
    if not seat:
        import socket
        try:
            h = socket.gethostname().strip()
            seat = f"PC-{h.upper()}"
        except Exception:
            seat = "PC-01"
    return seat


def set_seat_name(name: str):
    cfg = load_lab_config()
    cfg["seat_name"] = name
    save_lab_config(cfg)


def get_mode() -> str:
    return load_lab_config().get("mode", "unset")


def set_mode(mode: str):
    cfg = load_lab_config()
    cfg["mode"] = mode
    save_lab_config(cfg)


# ── Authentication & Security ──────────────────────────────────────────────────

DEFAULT_PASSKEY = os.getenv("SMARTFIX_ADMIN_PASSKEY", "admin123")


def _hash_passkey(passkey: str) -> str:
    return hashlib.sha256(passkey.strip().encode("utf-8")).hexdigest()


def get_admin_passkey_hash() -> str:
    """Retrieve or initialize the admin passkey hash."""
    cfg = load_lab_config()
    if "admin_passkey_hash" not in cfg:
        default_hash = _hash_passkey(DEFAULT_PASSKEY)
        cfg["admin_passkey_hash"] = default_hash
        save_lab_config(cfg)
        return default_hash
    return cfg["admin_passkey_hash"]


def set_admin_passkey(new_passkey: str):
    """Set and persist a new admin passkey."""
    cfg = load_lab_config()
    cfg["admin_passkey_hash"] = _hash_passkey(new_passkey)
    save_lab_config(cfg)


def verify_admin_passkey(passkey: str) -> bool:
    """Check if the provided passkey matches the stored passkey."""
    if not passkey:
        return False
    return _hash_passkey(passkey) == get_admin_passkey_hash()


def get_auth_token() -> str:
    """Generate auth token for signing admin-to-client commands."""
    return get_admin_passkey_hash()


def verify_auth_token(token: str) -> bool:
    """Verify an auth token sent from an admin."""
    if not token:
        return False
    return hmac.compare_digest(token, get_admin_passkey_hash())


# ── HMAC Signature for UDP Discovery ──────────────────────────────────────────

def sign_discovery_message(data: dict) -> dict:
    """Add HMAC signature to a discovery broadcast message."""
    data["version"] = PROTOCOL_VERSION
    data["timestamp"] = int(time.time())
    payload = json.dumps(data, sort_keys=True)
    sig = hmac.new(
        get_admin_passkey_hash().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return {"data": data, "sig": sig}


def verify_discovery_message(msg: dict) -> Optional[dict]:
    """Verify and extract a signed discovery message. Returns data if valid, None if tampered."""
    try:
        data = msg.get("data")
        sig = msg.get("sig", "")
        if not data or not sig:
            # Backwards compatibility: accept unsigned messages from older agents
            if msg.get("type") == "ANNOUNCE":
                return msg
            return None
        payload = json.dumps(data, sort_keys=True)
        expected_sig = hmac.new(
            get_admin_passkey_hash().encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(sig, expected_sig):
            # Check timestamp freshness (reject messages older than 60 seconds)
            ts = data.get("timestamp", 0)
            if abs(time.time() - ts) > 60:
                return None
            return data
        return None
    except Exception:
        # Backwards compatibility fallback
        if isinstance(msg, dict) and msg.get("type") == "ANNOUNCE":
            return msg
        return None


def get_local_ip() -> str:
    """Get this machine's LAN IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_known_clients() -> list:
    """Return list of known client entries: [{seat, ip, port}]."""
    return load_lab_config().get("known_clients", [])


def save_known_clients(clients: list):
    cfg = load_lab_config()
    cfg["known_clients"] = clients
    save_lab_config(cfg)


# ── Protocol Messaging ────────────────────────────────────────────────────────

def make_message(msg_type: str, payload: Optional[Dict] = None) -> bytes:
    """Encode a message as newline-terminated JSON with protocol version."""
    msg = {
        "type": msg_type,
        "version": PROTOCOL_VERSION,
        "payload": payload or {},
    }
    return (json.dumps(msg) + "\n").encode("utf-8")


def parse_message(raw: str) -> Optional[Dict[str, Any]]:
    """Decode a JSON message string. Returns None on parse error or oversized input."""
    if len(raw) > MAX_MESSAGE_SIZE:
        return None
    try:
        return json.loads(raw.strip())
    except Exception:
        return None


def send_message(sock: socket.socket, msg_type: str, payload: Optional[Dict] = None) -> bool:
    """Send a framed JSON message over a socket. Returns True on success."""
    try:
        sock.sendall(make_message(msg_type, payload))
        return True
    except Exception:
        return False


def recv_message(sock: socket.socket, timeout: float = MESSAGE_TIMEOUT, max_size: int = MAX_MESSAGE_SIZE) -> Optional[Dict[str, Any]]:
    """Receive one newline-terminated JSON message from a socket.
    Enforces max buffer size to prevent memory exhaustion attacks."""
    sock.settimeout(timeout)
    buf = b""
    try:
        while b"\n" not in buf:
            if len(buf) > max_size:
                return None  # Reject oversized messages — potential DoS
            chunk = sock.recv(65536)
            if not chunk:
                return None
            buf += chunk
        line = buf.split(b"\n", 1)[0]
        return parse_message(line.decode("utf-8"))
    except Exception:
        return None
