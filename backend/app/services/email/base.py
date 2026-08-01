"""
Abstract base for all email connector services.
Subclasses implement provider-specific authentication and message fetching.
"""
from typing import List, Dict, Any
from abc import ABC, abstractmethod


class BaseEmailService(ABC):
    def __init__(self, credentials_data: Dict[str, Any]) -> None:
        self.credentials_data = credentials_data

    @abstractmethod
    async def authenticate(self) -> bool:
        """Validate credentials / tokens. Returns True if authenticated."""
        ...

    @abstractmethod
    async def fetch_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent inbox messages.
        Returns list of dicts with keys: id, sender, subject, body
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up any open connections."""
        ...
