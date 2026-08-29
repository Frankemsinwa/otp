import base64

import pytest
from cryptography.fernet import Fernet

from app.core import security


# ---------------------------------------------------------------------------
# Fixture: pin a real, valid Fernet key onto settings for the duration of a
# test so token behavior is hermetic and never depends on a local .env.
# ---------------------------------------------------------------------------
@pytest.fixture
def valid_key(monkeypatch):
    key = Fernet.generate_key().decode()  # 32-byte url-safe base64 — valid Fernet
    monkeypatch.setattr(security.settings, "ENCRYPTION_KEY", key)
    return key


# ---------------------------------------------------------------------------
# Token roundtrip — the core promise: encrypt(plain) -> decrypt == plain
# ---------------------------------------------------------------------------
def test_token_roundtrip_typical_oauth(valid_key):
    plain = "ya29.a0AbV3HZ_abcdefghijklmnopqrstuvwxyz-1234567890"
    ct = security.encrypt_token(plain)
    assert security.decrypt_token(ct) == plain


def test_token_roundtrip_empty_string(valid_key):
    ct = security.encrypt_token("")
    assert security.decrypt_token(ct) == ""


def test_token_roundtrip_unicode_and_emoji(valid_key):
    plain = "töken_🔐_café_日本語"
    ct = security.encrypt_token(plain)
    assert security.decrypt_token(ct) == plain


def test_token_roundtrip_long_payload(valid_key):
    plain = "x" * 10000
    ct = security.encrypt_token(plain)
    assert security.decrypt_token(ct) == plain


def test_token_roundtrip_special_chars(valid_key):
    plain = 'a/b+c\n\r\t"\'\\back-slash'
    ct = security.encrypt_token(plain)
    assert security.decrypt_token(ct) == plain


def test_token_roundtrip_json_blob(valid_key):
    plain = '{"access_token":"ya29.x","refresh_token":"1//abc","expiry":1700000000}'
    ct = security.encrypt_token(plain)
    assert security.decrypt_token(ct) == plain


# ---------------------------------------------------------------------------
# Encrypt is non-deterministic (random IV) but always reversible
# ---------------------------------------------------------------------------
def test_token_encrypt_is_non_deterministic(valid_key):
    ct1 = security.encrypt_token("same-plaintext")
    ct2 = security.encrypt_token("same-plaintext")
    assert ct1 != ct2
    assert security.decrypt_token(ct1) == "same-plaintext"
    assert security.decrypt_token(ct2) == "same-plaintext"


# ---------------------------------------------------------------------------
# Ciphertext shape — must not leak plaintext and must be url-safe base64
# ---------------------------------------------------------------------------
def test_ciphertext_is_not_plaintext(valid_key):
    plain = "super-secret-oauth-token"
    ct = security.encrypt_token(plain)
    assert plain not in ct


def test_ciphertext_is_urlsafe_base64(valid_key):
    ct = security.encrypt_token("anything-at-all")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")
    assert ct and all(c in allowed for c in ct)


# ---------------------------------------------------------------------------
# Shared key: encrypt_token and encrypt_password use the SAME Fernet key,
# so a token encrypted by one can be opened by the other (real behavior).
# ---------------------------------------------------------------------------
def test_token_and_password_share_key(valid_key):
    secret = "shared-secret-value"
    tok_ct = security.encrypt_token(secret)
    pw_ct = security.encrypt_password(secret)
    assert security.decrypt_password(tok_ct) == secret
    assert security.decrypt_token(pw_ct) == secret


# ---------------------------------------------------------------------------
# Token failure paths — InvalidToken must surface as ValueError
# ---------------------------------------------------------------------------
def test_decrypt_token_tampered_raises(valid_key):
    ct = security.encrypt_token("secret-value")
    pos = 20
    old = ct[pos]
    new = "A" if old != "A" else "B"
    tampered = ct[:pos] + new + ct[pos + 1:]
    with pytest.raises(ValueError):
        security.decrypt_token(tampered)


def test_decrypt_token_key_mismatch_raises(valid_key):
    # encrypt under a DIFFERENT key than the one pinned on settings
    foreign_f = Fernet(Fernet.generate_key())
    foreign_ct = foreign_f.encrypt(b"secret-value").decode()
    with pytest.raises(ValueError):
        security.decrypt_token(foreign_ct)


def test_decrypt_token_short_base64_raises(valid_key):
    short = base64.urlsafe_b64encode(b"short").decode()
    with pytest.raises(ValueError):
        security.decrypt_token(short)


def test_decrypt_token_empty_string_raises(valid_key):
    with pytest.raises(ValueError):
        security.decrypt_token("")


def test_decrypt_token_garbage_raises(valid_key):
    with pytest.raises(ValueError):
        security.decrypt_token("not-a-real-token!!!")


# ---------------------------------------------------------------------------
# Password encrypt/decrypt roundtrip (reversible symmetric path)
# ---------------------------------------------------------------------------
def test_password_roundtrip(valid_key):
    plain = "hunter2"
    ct = security.encrypt_password(plain)
    assert security.decrypt_password(ct) == plain


def test_password_roundtrip_unicode(valid_key):
    plain = "pässwörd_🔐"
    ct = security.encrypt_password(plain)
    assert security.decrypt_password(ct) == plain


def test_decrypt_password_tampered_raises(valid_key):
    ct = security.encrypt_password("hunter2")
    pos = 15
    old = ct[pos]
    new = "A" if old != "A" else "B"
    tampered = ct[:pos] + new + ct[pos + 1:]
    with pytest.raises(ValueError):
        security.decrypt_password(tampered)


# ---------------------------------------------------------------------------
# One-way password hashing (bcrypt) — verify, wrong-pw, salt uniqueness
# ---------------------------------------------------------------------------
def test_one_way_hashing():
    plain = "SuperSecret123!"
    hashed = security.hash_password(plain)
    assert hashed != plain
    assert security.verify_password(plain, hashed) is True
    assert security.verify_password("wrong_password", hashed) is False


def test_hash_is_bcrypt_format():
    hashed = security.hash_password("whatever")
    assert hashed.startswith("$2")  # bcrypt ($2b$/$2a$)


def test_same_password_hashes_differ_but_verify():
    plain = "repeated-password"
    h1 = security.hash_password(plain)
    h2 = security.hash_password(plain)
    assert h1 != h2  # salted
    assert security.verify_password(plain, h1) is True
    assert security.verify_password(plain, h2) is True


def test_hash_empty_password():
    hashed = security.hash_password("")
    assert security.verify_password("", hashed) is True
    assert security.verify_password("not-empty", hashed) is False
