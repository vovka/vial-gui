# SPDX-License-Identifier: GPL-2.0-or-later
import secrets

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class PasswordCrypto:
    """Cryptographic utilities for password macro encryption."""

    SALT_SIZE = 16
    IV_SIZE = 16  # AES-CTR uses 16-byte IV to match firmware
    KEY_SIZE = 32  # Full derived key size (sent to keyboard)
    ENCRYPTION_KEY_SIZE = 16  # AES-128 key size for encryption
    PBKDF2_ITERATIONS = 310000

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
            32-byte derived key (first 16 bytes used for AES-128)
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
        Encrypt a password using AES-128-CTR to match firmware.

        The encryption is retried with new IVs until the result contains
        no NUL bytes (0x00), since NUL is used as macro separator in EEPROM.

        Args:
            plaintext: The password to encrypt
            key: 32-byte encryption key (first 16 bytes used)

        Returns:
            Tuple of (ciphertext, iv)
        """
        max_attempts = 100  # Should succeed within a few tries
        for _ in range(max_attempts):
            iv = PasswordCrypto.generate_iv()
            # Use first 16 bytes of key for AES-128
            cipher = Cipher(
                algorithms.AES(key[:PasswordCrypto.ENCRYPTION_KEY_SIZE]),
                modes.CTR(iv)
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()

            # Check if ciphertext or IV contains NUL bytes (would break macro format)
            if b'\x00' not in ciphertext and b'\x00' not in iv:
                return ciphertext, iv

        # Fallback (should rarely happen)
        raise RuntimeError("Failed to encrypt password without NUL bytes")

    @staticmethod
    def decrypt_password(ciphertext: bytes, key: bytes, iv: bytes) -> str:
        """
        Decrypt a password using AES-128-CTR to match firmware.

        Args:
            ciphertext: The encrypted password bytes
            key: 32-byte encryption key (first 16 bytes used)
            iv: The initialization vector used during encryption

        Returns:
            The decrypted password string
        """
        # Use first 16 bytes of key for AES-128
        cipher = Cipher(
            algorithms.AES(key[:PasswordCrypto.ENCRYPTION_KEY_SIZE]),
            modes.CTR(iv)
        )
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
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
