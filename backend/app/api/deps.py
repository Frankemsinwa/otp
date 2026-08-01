"""
Shared FastAPI dependencies.
"""
from app.core.database import get_db  # re-export for clean imports
from app.services.extractor import OTPExtractor

# Singleton instances
_extractor: OTPExtractor | None = None


def get_extractor() -> OTPExtractor:
    """Return a singleton OTPExtractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = OTPExtractor()
    return _extractor
