"""
Security utilities for password hashing and token encryption.
Passwords are hashed with bcrypt. OAuth tokens are encrypted at rest with Fernet.
"""
from passlib.context import CryptContext
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

# ---------------------------------------------------------------------------
# Password Hashing (bcrypt)
# ---------------------------------------------------------------------------
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return _pwd_ctx.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Symmetric Token Encryption (Fernet)
# ---------------------------------------------------------------------------
def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY.encode()
    return Fernet(key)


def encrypt_token(token: str) -> str:
    """Encrypt an OAuth token (or any sensitive string) for storage."""
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Decrypt a stored OAuth token back to plaintext."""
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt token — key mismatch or corrupted data")
