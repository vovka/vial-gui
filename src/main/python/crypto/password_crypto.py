# SPDX-License-Identifier: GPL-2.0-or-later
import secrets
import hashlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class PasswordCrypto:
    """Cryptographic utilities for password macro encryption."""

    SALT_SIZE = 16
    IV_SIZE = 12  # GCM standard nonce size
    KEY_SIZE = 32  # AES-256
    PBKDF2_ITERATIONS = 100000

    @staticmethod
    def generate_salt() -> bytes:
        """Generate a cryptographically secure random salt."""
        return secrets.token_bytes(PasswordCrypto.SALT_SIZE)

    @staticmethod
    def generate_iv() -> bytes:
        """Generate a cryptographically secure random IV/nonce."""
        return secrets.token_bytes(PasswordCrypto.IV_SIZE)

    @staticmethod
    def derive_key(master_password: str, salt: bytes) -> bytes:
        """
        Derive an encryption key from the master password using PBKDF2.

        Args:
            master_password: The user's master password
            salt: Random salt bytes

        Returns:
            32-byte derived key suitable for AES-256
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=PasswordCrypto.KEY_SIZE,
            salt=salt,
            iterations=PasswordCrypto.PBKDF2_ITERATIONS,
        )
        return kdf.derive(master_password.encode("utf-8"))

    @staticmethod
    def encrypt_password(plaintext: str, key: bytes) -> tuple:
        """
        Encrypt a password using AES-256-GCM.

        Args:
            plaintext: The password to encrypt
            key: 32-byte encryption key

        Returns:
            Tuple of (ciphertext, iv)
        """
        iv = PasswordCrypto.generate_iv()
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
        return ciphertext, iv

    @staticmethod
    def decrypt_password(ciphertext: bytes, key: bytes, iv: bytes) -> str:
        """
        Decrypt a password using AES-256-GCM.

        Args:
            ciphertext: The encrypted password bytes
            key: 32-byte encryption key
            iv: The initialization vector used during encryption

        Returns:
            The decrypted password string

        Raises:
            cryptography.exceptions.InvalidTag: If decryption fails
        """
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
        return plaintext.decode("utf-8")

    @staticmethod
    def hash_master_password(password: str, salt: bytes) -> bytes:
        """
        Create a hash of the master password for verification purposes.
        Uses a different derivation than the encryption key for security.

        Args:
            password: The master password
            salt: Random salt bytes

        Returns:
            Hash bytes for verification
        """
        # Use a different iteration count to ensure hash != key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt + b"_verify",
            iterations=PasswordCrypto.PBKDF2_ITERATIONS,
        )
        return kdf.derive(password.encode("utf-8"))

    @staticmethod
    def verify_master_password(password: str, salt: bytes, stored_hash: bytes) -> bool:
        """
        Verify a master password against a stored hash.

        Args:
            password: The password to verify
            salt: The salt used when creating the hash
            stored_hash: The previously stored hash

        Returns:
            True if password matches, False otherwise
        """
        computed_hash = PasswordCrypto.hash_master_password(password, salt)
        return secrets.compare_digest(computed_hash, stored_hash)

    @staticmethod
    def secure_zero(data: bytearray):
        """
        Securely zero out sensitive data in memory.

        Args:
            data: Bytearray to zero out
        """
        for i in range(len(data)):
            data[i] = 0
