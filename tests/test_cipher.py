"""Unit tests for the AES Text Encryptor core module.

Student Index Number: 10335136

Run from the project root with:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import base64
import unittest

import aes_text_cipher as cipher

PASSWORD = "Correct-Horse-Battery-Staple-10335136"


def decode_payload(token: str) -> bytes:
    """Return the raw salt + nonce + ciphertext + tag bytes from a token."""
    encoded = token[len(cipher.TOKEN_PREFIX) :]
    return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))


def encode_payload(payload: bytes) -> str:
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return cipher.TOKEN_PREFIX + encoded


class AesTextCipherTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        message = "Meet me at the library at 10:00."
        token = cipher.encrypt_text(message, PASSWORD)

        self.assertTrue(token.startswith(cipher.TOKEN_PREFIX))
        self.assertNotIn(message, token)
        self.assertEqual(cipher.decrypt_text(token, PASSWORD), message)

    def test_round_trip_unicode_and_multiline_text(self) -> None:
        message = "Héllo, wörld! 🌍\nLine 2: 日本語 and русский.\n\tEnd."
        token = cipher.encrypt_text(message, PASSWORD)
        self.assertEqual(cipher.decrypt_text(token, PASSWORD), message)

    def test_empty_text_round_trip(self) -> None:
        token = cipher.encrypt_text("", PASSWORD)
        self.assertEqual(cipher.decrypt_text(token, PASSWORD), "")

    def test_every_encryption_uses_a_fresh_salt_and_nonce(self) -> None:
        first = decode_payload(cipher.encrypt_text("same message", PASSWORD))
        second = decode_payload(cipher.encrypt_text("same message", PASSWORD))

        salt_size = cipher.SALT_SIZE
        nonce_end = salt_size + cipher.NONCE_SIZE
        self.assertNotEqual(first[:salt_size], second[:salt_size])
        self.assertNotEqual(first[salt_size:nonce_end], second[salt_size:nonce_end])
        self.assertNotEqual(first, second)

    def test_same_password_and_text_produce_different_tokens(self) -> None:
        first = cipher.encrypt_text("repeatable input", PASSWORD)
        second = cipher.encrypt_text("repeatable input", PASSWORD)
        self.assertNotEqual(first, second)
        self.assertEqual(cipher.decrypt_text(first, PASSWORD), "repeatable input")
        self.assertEqual(cipher.decrypt_text(second, PASSWORD), "repeatable input")

    def test_wrong_password_is_rejected(self) -> None:
        token = cipher.encrypt_text("top secret", PASSWORD)
        with self.assertRaises(cipher.DecryptionError) as context:
            cipher.decrypt_text(token, "Wrong-Password-123")
        self.assertIn("wrong password", str(context.exception).lower())

    def test_modified_ciphertext_is_rejected(self) -> None:
        token = cipher.encrypt_text("integrity matters", PASSWORD)
        payload = bytearray(decode_payload(token))
        payload[-1] ^= 0x01  # flip one bit in the authentication tag

        with self.assertRaises(cipher.DecryptionError):
            cipher.decrypt_text(encode_payload(bytes(payload)), PASSWORD)

    def test_modified_salt_is_rejected(self) -> None:
        token = cipher.encrypt_text("integrity matters", PASSWORD)
        payload = bytearray(decode_payload(token))
        payload[0] ^= 0x80

        with self.assertRaises(cipher.DecryptionError):
            cipher.decrypt_text(encode_payload(bytes(payload)), PASSWORD)

    def test_modified_nonce_is_rejected(self) -> None:
        token = cipher.encrypt_text("integrity matters", PASSWORD)
        payload = bytearray(decode_payload(token))
        payload[cipher.SALT_SIZE] ^= 0x01

        with self.assertRaises(cipher.DecryptionError):
            cipher.decrypt_text(encode_payload(bytes(payload)), PASSWORD)

    def test_token_with_line_breaks_is_accepted(self) -> None:
        token = cipher.encrypt_text("line-wrapped token", PASSWORD)
        wrapped = token[:20] + "\n" + token[20:40] + "\r\n" + token[40:]
        self.assertEqual(cipher.decrypt_text(wrapped, PASSWORD), "line-wrapped token")

    def test_malformed_tokens_are_rejected(self) -> None:
        bad_tokens = [
            "not-a-token",
            "AES256GCM1:",
            "AES256GCM1:!!!!",
            "AES256GCM1:abc",
            cipher.TOKEN_PREFIX + "A" * 20,
        ]
        for token in bad_tokens:
            with self.subTest(token=token):
                with self.assertRaises(cipher.InvalidTokenError):
                    cipher.decrypt_text(token, PASSWORD)

    def test_short_password_is_rejected_for_encryption_and_decryption(self) -> None:
        with self.assertRaises(cipher.WeakPasswordError):
            cipher.encrypt_text("text", "short")

        token = cipher.encrypt_text("text", PASSWORD)
        with self.assertRaises(cipher.WeakPasswordError):
            cipher.decrypt_text(token, "short")

    def test_eight_character_password_is_accepted(self) -> None:
        token = cipher.encrypt_text("minimum length", "12345678")
        self.assertEqual(cipher.decrypt_text(token, "12345678"), "minimum length")

    def test_unicode_password_round_trip(self) -> None:
        password = "pässwörd-🔐-long-enough"
        token = cipher.encrypt_text("unicode password", password)
        self.assertEqual(cipher.decrypt_text(token, password), "unicode password")

    def test_non_string_input_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            cipher.encrypt_text(None, PASSWORD)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            cipher.encrypt_text("text", None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            cipher.decrypt_text(None, PASSWORD)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            cipher.decrypt_text("token", None)  # type: ignore[arg-type]

    def test_token_uses_url_safe_characters_only(self) -> None:
        token = cipher.encrypt_text("x" * 500, PASSWORD)
        body = token[len(cipher.TOKEN_PREFIX) :]
        self.assertRegex(body, r"^[A-Za-z0-9_-]+$")


if __name__ == "__main__":
    unittest.main(verbosity=2)
