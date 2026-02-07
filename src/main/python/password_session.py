# SPDX-License-Identifier: GPL-2.0-or-later

from crypto.password_crypto import PasswordCrypto


class PasswordSession:
    """
    Singleton managing the master password session.

    Handles encryption/decryption of password macros and maintains
    the derived key in memory only while the session is unlocked.
    """

    _instance = None

    def __init__(self):
        self._derived_key = None
        self._key_salt = None
        self._is_unlocked = False

    @classmethod
    def instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (mainly for testing)."""
        if cls._instance is not None:
            cls._instance.lock()
        cls._instance = None

    def is_unlocked(self) -> bool:
        """Check if session is unlocked."""
        return self._is_unlocked

    def unlock(self, master_password: str, stored_hash: bytes, salt: bytes) -> bool:
        """
        Verify master password and derive key.

        Args:
            master_password: The master password entered by user
            stored_hash: Previously stored hash for verification
            salt: Salt used for key derivation

        Returns:
            True if password is correct and session is now unlocked
        """
        if not PasswordCrypto.verify_master_password(master_password, salt, stored_hash):
            return False

        self._derived_key = bytearray(PasswordCrypto.derive_key(master_password, salt))
        self._key_salt = salt
        self._is_unlocked = True
        return True

    def setup(self, master_password: str) -> tuple:
        """
        Set up a new master password (first time setup).

        Args:
            master_password: The new master password

        Returns:
            Tuple of (hash, salt) to be stored for verification
        """
        salt = PasswordCrypto.generate_salt()
        password_hash = PasswordCrypto.hash_master_password(master_password, salt)

        self._derived_key = bytearray(PasswordCrypto.derive_key(master_password, salt))
        self._key_salt = salt
        self._is_unlocked = True

        return password_hash, salt

    def lock(self):
        """Clear derived key from memory and lock session."""
        if self._derived_key is not None:
            PasswordCrypto.secure_zero(self._derived_key)
            self._derived_key = None
        self._key_salt = None
        self._is_unlocked = False

    def get_key(self) -> bytes:
        """
        Get derived key for encryption/decryption.

        Returns:
            The derived encryption key

        Raises:
            RuntimeError: If session is locked
        """
        if not self._is_unlocked or self._derived_key is None:
            raise RuntimeError("Password session is locked")
        return bytes(self._derived_key)

    def encrypt(self, plaintext: str) -> tuple:
        """
        Encrypt text using the session key.

        Args:
            plaintext: Text to encrypt

        Returns:
            Tuple of (ciphertext, salt, iv)

        Raises:
            RuntimeError: If session is locked
        """
        if not self._is_unlocked:
            raise RuntimeError("Password session is locked")

        key = self.get_key()
        ciphertext, iv = PasswordCrypto.encrypt_password(plaintext, key)
        return ciphertext, self._key_salt, iv

    def decrypt(self, ciphertext: bytes, salt: bytes, iv: bytes) -> str:
        """
        Decrypt password using the session key.

        Args:
            ciphertext: Encrypted password bytes
            salt: Salt used during encryption
            iv: IV used during encryption

        Returns:
            Decrypted password string

        Raises:
            RuntimeError: If session is locked
            cryptography.exceptions.InvalidTag: If decryption fails
        """
        if not self._is_unlocked:
            raise RuntimeError("Password session is locked")

        key = self.get_key()
        return PasswordCrypto.decrypt_password(ciphertext, key, iv)
