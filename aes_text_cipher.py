"""
aes_text_cipher.py
------------------
Core encryption and decryption logic for the AES Text Encryptor project.

Student Index Number: 10335136

Algorithm
---------
AES-256-GCM (Advanced Encryption Standard, 256-bit key, Galois/Counter Mode).
AES is the symmetric encryption algorithm covered in class.

Key derivation
--------------
PBKDF2-HMAC-SHA256 with a random 16-byte salt and 600,000 iterations.  This
turns a human-memorable password into a 256-bit AES key without storing the
password anywhere.

Encrypted token format
----------------------
    "AES256GCM1:" + base64url( salt[16] || nonce[12] || ciphertext || tag[16] )

* The salt makes every derived key unique, even for the same password.
* The nonce must never repeat under a given key; a fresh random nonce is
  generated for every encryption.
* GCM appends a 16-byte authentication tag, so a wrong password or a modified
  token is detected before any plaintext is returned.
"""

from __future__ import annotations

import base64
import binascii
import os
from typing import Final

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Public constants used by the CLI, GUI, tests and documentation.
TOKEN_PREFIX: Final = "AES256GCM1:"
SALT_SIZE: Final = 16
NONCE_SIZE: Final = 12
KEY_SIZE: Final = 32  # 32 bytes = 256 bits
TAG_SIZE: Final = 16
KDF_ITERATIONS: Final = 600_000
MIN_PASSWORD_LENGTH: Final = 8

# Additional authenticated data binds a token to this format/version.  It is
# authenticated by GCM but is not secret and is not stored in the token.
_AAD: Final = b"aes-text-encryptor:v1"


class CipherError(Exception):
    """Base class for all user-facing errors raised by this module."""


class InvalidTokenError(CipherError):
    """Raised when an encrypted token is not in the expected format."""


class DecryptionError(CipherError):
    """Raised when authentication fails (wrong password or modified token)."""


class WeakPasswordError(CipherError):
    """Raised when a password is shorter than MIN_PASSWORD_LENGTH."""


def _require_string(value: str, label: str) -> None:
    """Reject non-string input early with a clear message."""
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")


def _validate_password(password: str) -> None:
    """Apply the minimum password policy shared by encryption and decryption."""
    _require_string(password, "Password")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from *password* and *salt* using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_text(plaintext: str, password: str) -> str:
    """Encrypt *plaintext* with *password* and return a printable token.

    A fresh random salt and nonce are generated for every call, so encrypting
    the same message twice produces two different tokens.

    Raises:
        TypeError: If plaintext or password is not a string.
        WeakPasswordError: If the password is shorter than 8 characters.
    """
    _require_string(plaintext, "Plaintext")
    _validate_password(password)

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(password, salt)

    ciphertext = AESGCM(key).encrypt(
        nonce,
        plaintext.encode("utf-8"),
        _AAD,
    )
    payload = salt + nonce + ciphertext
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return TOKEN_PREFIX + encoded


def decrypt_text(token: str, password: str) -> str:
    """Decrypt a token produced by :func:`encrypt_text` and return the text.

    Raises:
        TypeError: If token or password is not a string.
        WeakPasswordError: If the password is shorter than 8 characters.
        InvalidTokenError: If the token is malformed or truncated.
        DecryptionError: If the password is wrong or the token was modified.
    """
    _require_string(token, "Token")
    _validate_password(password)

    # Whitespace is not part of the base64url alphabet.  Removing it lets a
    # token survive being wrapped by a chat application or terminal.
    compact = "".join(token.split())
    if not compact.startswith(TOKEN_PREFIX):
        raise InvalidTokenError(
            "This does not look like an AES Text Encryptor token "
            f"(expected it to start with {TOKEN_PREFIX!r})."
        )

    encoded = compact[len(TOKEN_PREFIX) :].rstrip("=")
    if not encoded:
        raise InvalidTokenError("The token is empty.")

    try:
        payload = base64.b64decode(
            (encoded + "=" * (-len(encoded) % 4)).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError, UnicodeEncodeError):
        raise InvalidTokenError("The token contains invalid base64 data.") from None

    if len(payload) < SALT_SIZE + NONCE_SIZE + TAG_SIZE:
        raise InvalidTokenError("The token is too short to be valid.")

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE :]

    key = _derive_key(password, salt)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, _AAD)
    except InvalidTag:
        # Deliberately do not distinguish a wrong password from a modified
        # token: both mean authentication failed.
        raise DecryptionError(
            "Decryption failed: wrong password or the token was modified."
        ) from None

    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError:
        raise DecryptionError(
            "Decryption failed: the decrypted data is not valid UTF-8 text."
        ) from None


__all__ = [
    "CipherError",
    "DecryptionError",
    "InvalidTokenError",
    "WeakPasswordError",
    "TOKEN_PREFIX",
    "SALT_SIZE",
    "NONCE_SIZE",
    "KEY_SIZE",
    "TAG_SIZE",
    "KDF_ITERATIONS",
    "MIN_PASSWORD_LENGTH",
    "encrypt_text",
    "decrypt_text",
]
