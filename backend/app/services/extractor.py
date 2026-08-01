"""
OTP extraction engine with confidence scoring and HTML body support.

Extracts verification codes from email subject + body using layered regex
patterns with contextual keyword proximity scoring.
"""
import re
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup
from app.core.logging import get_logger

log = get_logger("services.extractor")


class OTPExtractor:
    # Known OTP sender domains — high trust
    TRUSTED_SENDERS = {
        "accounts.google.com",
        "login.yahoo.com",
        "noreply@google.com",
        "no-reply@accounts.google.com",
        "no-reply@login.yahoo.com",
    }

    # Context keywords that strongly indicate OTP content
    KEYWORDS = [
        "verification code",
        "otp",
        "security code",
        "code to sign in",
        "login code",
        "passcode",
        "one-time password",
        "authorization code",
        "confirm your identity",
        "two-factor",
        "2fa",
        "sign-in code",
    ]

    # Ordered by specificity — more specific patterns checked first
    CODE_PATTERNS = [
        # Google "G-" prefixed codes
        (r"G-(\d{4,8})", 0.95),
        # Explicit code assignment: "code is 123456", "code: ABC123"
        (r"(?:code|otp|passcode)[:\s]+([A-Z0-9]{4,8})", 0.90),
        # "Your code is" / "enter 123456"
        (r"(?:your|enter|use)\s+(?:code\s+)?(?:is\s+)?([A-Z0-9]{4,8})", 0.85),
        # Standalone numeric codes (4-8 digits)
        (r"\b(\d{4,8})\b", 0.60),
        # Alphanumeric codes (5-8 chars, uppercase)
        (r"\b([A-Z0-9]{5,8})\b", 0.50),
    ]

    def __init__(self) -> None:
        self._compiled = [(re.compile(p, re.IGNORECASE), conf) for p, conf in self.CODE_PATTERNS]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_otp_message(self, subject: str, body: str, sender: str = "") -> bool:
        """Check if a message likely contains an OTP based on keywords and sender."""
        combined = (subject + " " + body).lower()
        keyword_hit = any(kw in combined for kw in self.KEYWORDS)

        sender_domain = sender.split("@")[-1].lower() if "@" in sender else ""
        sender_trusted = sender_domain in self.TRUSTED_SENDERS or sender.lower() in self.TRUSTED_SENDERS

        return keyword_hit or sender_trusted

    def extract_code(self, subject: str, body: str, sender: str = "") -> Optional[str]:
        """Extract the single best OTP code from a message. Returns None if not an OTP message."""
        results = self.extract_all_codes(subject, body, sender)
        if results:
            return results[0][0]
        return None

    def extract_all_codes(self, subject: str, body: str, sender: str = "") -> List[Tuple[str, float]]:
        """
        Extract all candidate OTP codes with confidence scores.
        Returns list of (code, confidence) tuples sorted by confidence descending.
        """
        if not self.is_otp_message(subject, body, sender):
            return []

        # Strip HTML if present
        clean_body = self._strip_html(body)
        combined = subject + " " + clean_body

        # Boost confidence if sender is trusted
        sender_bonus = 0.05 if self._is_trusted_sender(sender) else 0.0

        found: dict[str, float] = {}

        for pattern, base_confidence in self._compiled:
            for match in pattern.finditer(combined):
                code = match.group(1)
                if len(code) < 4:
                    continue

                # Calculate proximity boost — code near a keyword gets a bump
                proximity_bonus = self._keyword_proximity_bonus(combined, match.start())
                confidence = min(base_confidence + sender_bonus + proximity_bonus, 1.0)

                # Keep highest confidence per code
                if code not in found or confidence > found[code]:
                    found[code] = confidence

        results = sorted(found.items(), key=lambda x: x[1], reverse=True)
        if results:
            log.info(
                "OTP extraction results",
                extra={"codes_found": len(results), "top_code": results[0][0], "top_confidence": results[0][1]},
            )
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _strip_html(self, text: str) -> str:
        """Strip HTML tags from email body, return plain text."""
        if "<" in text and ">" in text:
            soup = BeautifulSoup(text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        return text

    def _is_trusted_sender(self, sender: str) -> bool:
        if not sender:
            return False
        sender_lower = sender.lower()
        domain = sender_lower.split("@")[-1] if "@" in sender_lower else ""
        return domain in self.TRUSTED_SENDERS or sender_lower in self.TRUSTED_SENDERS

    def _keyword_proximity_bonus(self, text: str, match_pos: int, window: int = 80) -> float:
        """
        Give a confidence bonus if a keyword appears within `window` characters
        of the matched code position.
        """
        start = max(0, match_pos - window)
        end = min(len(text), match_pos + window)
        snippet = text[start:end].lower()

        for kw in self.KEYWORDS:
            if kw in snippet:
                return 0.10
        return 0.0
