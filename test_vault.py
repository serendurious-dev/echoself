"""tests for the Vault - it must keep its promise: encrypted, and never readable
without the passphrase."""

import os
import tempfile
import unittest

from core import datastore, vault


class CryptoTest(unittest.TestCase):

    def test_roundtrip(self):
        blob = vault.encrypt(b"something private", "open sesame")
        self.assertEqual(vault.decrypt(blob, "open sesame"), b"something private")

    def test_wrong_passphrase_is_rejected(self):
        blob = vault.encrypt(b"diary", "the-real-one")
        with self.assertRaises(vault.BadPassphrase):
            vault.decrypt(blob, "a-guess")

    def test_tampering_is_caught(self):
        blob = bytearray(vault.encrypt(b"diary entry", "key"))
        blob[-1] ^= 0x01                              # flip a ciphertext bit
        with self.assertRaises(vault.BadPassphrase):
            vault.decrypt(bytes(blob), "key")

    def test_ciphertext_does_not_contain_the_plaintext(self):
        secret = b"the thing I would never say out loud"
        blob = vault.encrypt(secret, "key")
        self.assertNotIn(secret, blob)

    def test_same_text_encrypts_differently_each_time(self):
        # random salt + nonce -> no two blobs alike, no patterns to read
        a = vault.encrypt(b"same", "key")
        b = vault.encrypt(b"same", "key")
        self.assertNotEqual(a, b)

    def test_unicode_survives(self):
        blob = vault.encrypt("괜찮아, 나는 여기 있어".encode("utf-8"), "열쇠")
        self.assertEqual(vault.decrypt(blob, "열쇠").decode("utf-8"), "괜찮아, 나는 여기 있어")


class DiaryTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_create_unlock_and_add(self):
        self.assertFalse(vault.exists())
        vault.create("my passphrase")
        self.assertTrue(vault.exists())
        self.assertEqual(vault.unlock("my passphrase"), [])
        vault.add_entry("my passphrase", "today was heavy but I am still here")
        entries = vault.unlock("my passphrase")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["text"], "today was heavy but I am still here")

    def test_create_will_not_clobber(self):
        vault.create("p")
        with self.assertRaises(FileExistsError):
            vault.create("p")

    def test_a_wrong_passphrase_cannot_open_the_diary(self):
        vault.create("right")
        vault.add_entry("right", "private")
        with self.assertRaises(vault.BadPassphrase):
            vault.unlock("wrong")

    def test_the_file_on_disk_is_not_readable_text(self):
        vault.create("key")
        vault.add_entry("key", "a sentence the system must never read")
        with open(datastore.data_path(vault.VAULT_FILE), "rb") as f:
            raw = f.read()
        self.assertNotIn(b"a sentence the system must never read", raw)


if __name__ == "__main__":
    unittest.main()
