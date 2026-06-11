"""the Vault - a locally encrypted private writing space.

the one place in EchoSelf the system promises never to read. it is encrypted at
rest with the user's own passphrase, and nothing - not the ML brain, not the
logs, not the narrative - ever sees the plaintext. the system holds it. it does
not look at it (see SECURITY.md).

stdlib only, no third-party crypto, which is a deliberate constraint from the
original concept ("local encryption: hashlib, os"). the scheme:

  key      = PBKDF2-HMAC-SHA256(passphrase, salt, 200k iterations)
  keystream= SHA-256(key || nonce || counter) blocks, XORed into the plaintext
  mac      = HMAC-SHA256(key, nonce || ciphertext)   -- encrypt-then-MAC

the MAC is checked before anything is decrypted, so a wrong passphrase or a
tampered file fails loudly instead of returning garbage. this is honest local
encryption for a single user's diary; it is not claiming to be AES, and the
docstring says so on purpose.
"""

import os
import json
import hmac
import hashlib

VAULT_FILE  = "vault.dat"
_ITERATIONS = 200_000
_SALT_LEN   = 16
_NONCE_LEN  = 16
_MAC_LEN    = 32


class BadPassphrase(Exception):
    """wrong passphrase, or the file was tampered with."""


def _derive(passphrase, salt):
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, _ITERATIONS)


def _keystream(key, nonce, length):
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hashlib.sha256(key + nonce + counter.to_bytes(8, "big")).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def encrypt(plaintext, passphrase):
    salt  = os.urandom(_SALT_LEN)
    nonce = os.urandom(_NONCE_LEN)
    key   = _derive(passphrase, salt)
    stream = _keystream(key, nonce, len(plaintext))
    cipher = bytes(a ^ b for a, b in zip(plaintext, stream))
    mac    = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    return salt + nonce + mac + cipher


def decrypt(blob, passphrase):
    if len(blob) < _SALT_LEN + _NONCE_LEN + _MAC_LEN:
        raise BadPassphrase("vault file is too short to be valid")
    salt   = blob[:_SALT_LEN]
    nonce  = blob[_SALT_LEN:_SALT_LEN + _NONCE_LEN]
    mac    = blob[_SALT_LEN + _NONCE_LEN:_SALT_LEN + _NONCE_LEN + _MAC_LEN]
    cipher = blob[_SALT_LEN + _NONCE_LEN + _MAC_LEN:]
    key    = _derive(passphrase, salt)
    expected = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):     # constant-time, before decrypt
        raise BadPassphrase("wrong passphrase or tampered vault")
    stream = _keystream(key, nonce, len(cipher))
    return bytes(a ^ b for a, b in zip(cipher, stream))


# -- the diary on top of the cipher -------------------------------------------

def _path():
    from core import datastore
    return datastore.data_path(VAULT_FILE)


def _write_atomic(path, data):
    directory = os.path.dirname(os.path.abspath(path))
    tmp = os.path.join(directory, ".tmp_vault")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def exists():
    return os.path.exists(_path())


def create(passphrase):
    # a fresh, empty vault. refuses to clobber an existing one.
    if exists():
        raise FileExistsError("a vault already exists")
    _write_atomic(_path(), encrypt(json.dumps([]).encode("utf-8"), passphrase))


def unlock(passphrase):
    # the only way in. returns the list of entries, or raises BadPassphrase.
    with open(_path(), "rb") as f:
        blob = f.read()
    return json.loads(decrypt(blob, passphrase).decode("utf-8"))


def add_entry(passphrase, text, when=None):
    import datetime
    entries = unlock(passphrase)                   # verifies the passphrase first
    entries.append({"date": (when or datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"),
                    "text": text})
    _write_atomic(_path(), encrypt(json.dumps(entries, ensure_ascii=False).encode("utf-8"),
                                   passphrase))
    return entries
