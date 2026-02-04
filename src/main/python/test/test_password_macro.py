# SPDX-License-Identifier: GPL-2.0-or-later
import unittest
import base64

from crypto.password_crypto import PasswordCrypto
from password_session import PasswordSession
from macro.macro_action import ActionPassword


class TestPasswordCrypto(unittest.TestCase):

    def test_generate_salt(self):
        salt = PasswordCrypto.generate_salt()
        self.assertEqual(len(salt), 16)
        # Ensure randomness - two salts should be different
        salt2 = PasswordCrypto.generate_salt()
        self.assertNotEqual(salt, salt2)

    def test_generate_iv(self):
        iv = PasswordCrypto.generate_iv()
        self.assertEqual(len(iv), 12)

    def test_derive_key(self):
        password = "test_password"
        salt = PasswordCrypto.generate_salt()
        key = PasswordCrypto.derive_key(password, salt)
        self.assertEqual(len(key), 32)
        # Same password and salt should produce same key
        key2 = PasswordCrypto.derive_key(password, salt)
        self.assertEqual(key, key2)
        # Different salt should produce different key
        salt2 = PasswordCrypto.generate_salt()
        key3 = PasswordCrypto.derive_key(password, salt2)
        self.assertNotEqual(key, key3)

    def test_encrypt_decrypt_roundtrip(self):
        password = "my_secret_password"
        plaintext = "Hello, World!"
        salt = PasswordCrypto.generate_salt()
        key = PasswordCrypto.derive_key(password, salt)

        ciphertext, iv = PasswordCrypto.encrypt_password(plaintext, key)
        self.assertNotEqual(ciphertext, plaintext.encode())

        decrypted = PasswordCrypto.decrypt_password(ciphertext, key, iv)
        self.assertEqual(decrypted, plaintext)

    def test_hash_master_password(self):
        password = "master_password"
        salt = PasswordCrypto.generate_salt()
        hash1 = PasswordCrypto.hash_master_password(password, salt)
        self.assertEqual(len(hash1), 32)
        # Same password and salt should produce same hash
        hash2 = PasswordCrypto.hash_master_password(password, salt)
        self.assertEqual(hash1, hash2)

    def test_verify_master_password(self):
        password = "correct_password"
        salt = PasswordCrypto.generate_salt()
        stored_hash = PasswordCrypto.hash_master_password(password, salt)

        self.assertTrue(PasswordCrypto.verify_master_password(password, salt, stored_hash))
        self.assertFalse(PasswordCrypto.verify_master_password("wrong_password", salt, stored_hash))


class TestPasswordSession(unittest.TestCase):

    def setUp(self):
        PasswordSession.reset_instance()

    def tearDown(self):
        PasswordSession.reset_instance()

    def test_singleton(self):
        session1 = PasswordSession.instance()
        session2 = PasswordSession.instance()
        self.assertIs(session1, session2)

    def test_initial_state(self):
        session = PasswordSession.instance()
        self.assertFalse(session.is_unlocked())

    def test_setup_and_unlock(self):
        session = PasswordSession.instance()
        password = "test_master_password"

        # Setup
        password_hash, salt = session.setup(password)
        self.assertTrue(session.is_unlocked())
        self.assertIsNotNone(password_hash)
        self.assertIsNotNone(salt)

        # Lock
        session.lock()
        self.assertFalse(session.is_unlocked())

        # Unlock with correct password
        self.assertTrue(session.unlock(password, password_hash, salt))
        self.assertTrue(session.is_unlocked())

        # Lock again
        session.lock()

        # Unlock with wrong password
        self.assertFalse(session.unlock("wrong_password", password_hash, salt))
        self.assertFalse(session.is_unlocked())

    def test_encrypt_decrypt(self):
        session = PasswordSession.instance()
        session.setup("master_password")

        plaintext = "my_secret_data"
        ciphertext, salt, iv = session.encrypt(plaintext)

        decrypted = session.decrypt(ciphertext, salt, iv)
        self.assertEqual(decrypted, plaintext)

    def test_get_key_when_locked(self):
        session = PasswordSession.instance()
        with self.assertRaises(RuntimeError):
            session.get_key()


class TestActionPassword(unittest.TestCase):

    def setUp(self):
        PasswordSession.reset_instance()

    def tearDown(self):
        PasswordSession.reset_instance()

    def test_save_restore(self):
        encrypted_data = b"encrypted_password_data"
        salt = b"0123456789abcdef"
        iv = b"123456789012"

        action = ActionPassword(encrypted_data=encrypted_data, salt=salt, iv=iv)
        saved = action.save()

        self.assertEqual(saved[0], "password")
        self.assertEqual(base64.b64decode(saved[1]), encrypted_data)
        self.assertEqual(base64.b64decode(saved[2]), salt)
        self.assertEqual(base64.b64decode(saved[3]), iv)

        # Restore
        action2 = ActionPassword()
        action2.restore(saved)
        self.assertEqual(action2.encrypted_data, encrypted_data)
        self.assertEqual(action2.salt, salt)
        self.assertEqual(action2.iv, iv)

    def test_equality(self):
        action1 = ActionPassword(encrypted_data=b"data", salt=b"salt", iv=b"iv")
        action2 = ActionPassword(encrypted_data=b"data", salt=b"salt", iv=b"iv")
        action3 = ActionPassword(encrypted_data=b"other", salt=b"salt", iv=b"iv")

        self.assertEqual(action1, action2)
        self.assertNotEqual(action1, action3)


if __name__ == "__main__":
    unittest.main()
