import pytest
from app.core.security import encrypt_password, decrypt_password, hash_password, verify_password

def test_reversible_encryption():
    """Test that Fernet symmetric encryption successfully encrypts and decrypts passwords."""
    plain = "hunter2"
    encrypted = encrypt_password(plain)
    
    assert encrypted != plain
    assert decrypt_password(encrypted) == plain


def test_one_way_hashing():
    """Test that bcrypt one-way hashing successfully hashes and verifies passwords."""
    plain = "SuperSecret123!"
    hashed = hash_password(plain)
    
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong_password", hashed) is False
