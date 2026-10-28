"""
Tests for Lab LAN Protocol & Security Hardening.
Validates HMAC message signing, discovery verification, and protocol formatting.
"""
import unittest
from monitor.lab_config import (
    make_message, parse_message, sign_discovery_message, verify_discovery_message,
    verify_auth_token, set_admin_passkey, verify_admin_passkey, PROTOCOL_VERSION
)


class TestLabProtocol(unittest.TestCase):

    def test_message_framing_and_version(self):
        payload = {"seat": "PC-01", "ip": "192.168.1.50"}
        raw = make_message("STATUS", payload)
        self.assertTrue(raw.endswith(b"\n"), "Framed message must end with newline delimiter")

        parsed = parse_message(raw.decode("utf-8"))
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.get("type"), "STATUS")
        self.assertEqual(parsed.get("version"), PROTOCOL_VERSION)
        self.assertEqual(parsed.get("payload", {}).get("seat"), "PC-01")

    def test_hmac_discovery_signing(self):
        msg = sign_discovery_message({"seat": "PC-TEST", "ip": "127.0.0.1"})
        self.assertIn("sig", msg)
        self.assertIn("data", msg)

        # Verification must succeed for valid message
        verified_data = verify_discovery_message(msg)
        self.assertIsNotNone(verified_data, "Valid signed discovery message failed verification")
        self.assertEqual(verified_data.get("seat"), "PC-TEST")

        # Tampered message must be rejected
        tampered = {"data": dict(msg["data"]), "sig": msg["sig"]}
        tampered["data"]["seat"] = "PC-IMPOSTOR"
        self.assertIsNone(verify_discovery_message(tampered), "Tampered discovery message was not rejected!")

    def test_passkey_verification(self):
        test_key = "secure_lab_pass_2026"
        set_admin_passkey(test_key)
        self.assertTrue(verify_admin_passkey(test_key))
        self.assertFalse(verify_admin_passkey("wrong_passkey"))


if __name__ == "__main__":
    unittest.main()
