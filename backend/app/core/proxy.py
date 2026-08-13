"""
Proxy rotation manager with sticky, round-robin, and random strategies.
Supports HTTP, HTTPS, SOCKS4, SOCKS5 proxies with auth.
"""
import json
import random
import hashlib
from typing import List, Optional, Dict
from urllib.parse import urlparse

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("core.proxy")


class ProxyManager:
    """Manages proxy pool with configurable assignment strategies."""
    
    def __init__(self):
        self._proxies: List[str] = []
        self._strategy: str = settings.PROXY_STRATEGY
        self._sticky_map: Dict[str, str] = {}  # target_email -> proxy
        self._rr_index: int = 0
        self._load_proxies()
    
    def _load_proxies(self) -> None:
        """Load proxy list from settings."""
        try:
            proxy_list = json.loads(settings.PROXY_LIST)
            if isinstance(proxy_list, list):
                # Validate each proxy URL
                valid = []
                for p in proxy_list:
                    if self._validate_proxy(p):
                        valid.append(p)
                    else:
                        log.warning(f"Invalid proxy URL skipped: {p}")
                self._proxies = valid
                log.info(f"Loaded {len(self._proxies)} valid proxies")
            else:
                log.warning("PROXY_LIST is not a valid JSON array")
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse PROXY_LIST: {e}")
    
    def _validate_proxy(self, proxy_url: str) -> bool:
        """Validate proxy URL format."""
        try:
            parsed = urlparse(proxy_url)
            return parsed.scheme in ("http", "https", "socks4", "socks5") and parsed.hostname
        except Exception:
            return False
    
    def get_proxy(self, target_email: str = "") -> Optional[str]:
        """Get a proxy based on configured strategy."""
        if not self._proxies:
            return None
        
        if self._strategy == "sticky":
            return self._get_sticky(target_email)
        elif self._strategy == "round_robin":
            return self._get_round_robin()
        elif self._strategy == "random":
            return self._get_random()
        else:
            return self._proxies[0]
    
    def _get_sticky(self, target_email: str) -> str:
        """Assign same proxy to same target consistently."""
        if target_email in self._sticky_map:
            proxy = self._sticky_map[target_email]
            if proxy in self._proxies:
                return proxy
        
        # Hash email to deterministic index
        idx = int(hashlib.md5(target_email.encode()).hexdigest(), 16) % len(self._proxies)
        proxy = self._proxies[idx]
        self._sticky_map[target_email] = proxy
        return proxy
    
    def _get_round_robin(self) -> str:
        """Cycle through proxies sequentially."""
        proxy = self._proxies[self._rr_index % len(self._proxies)]
        self._rr_index += 1
        return proxy
    
    def _get_random(self) -> str:
        """Pick random proxy each time."""
        return random.choice(self._proxies)
    
    def mark_proxy_failed(self, proxy: str) -> None:
        """Optionally remove failed proxy from pool."""
        if proxy in self._proxies:
            log.warning(f"Marking proxy as failed, removing: {proxy}")
            self._proxies.remove(proxy)
            # Clean up sticky mappings
            self._sticky_map = {k: v for k, v in self._sticky_map.items() if v != proxy}
    
    def get_httpx_proxy(self, target_email: str = "") -> Optional[Dict[str, str]]:
        """Get proxy dict formatted for httpx client."""
        proxy = self.get_proxy(target_email)
        if not proxy:
            return None
        return {
            "http://": proxy,
            "https://": proxy,
        }
    
    def get_aiohttp_proxy(self, target_email: str = "") -> Optional[str]:
        """Get proxy string for aiohttp (same format)."""
        return self.get_proxy(target_email)


# Global instance
proxy_manager = ProxyManager()