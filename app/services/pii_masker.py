"""
Signal — PII Masker
Sanitizes phone numbers, emails, Aadhaar, PAN, and credit cards before sending text to LLM.
"""

import re
from typing import Any


class PIIMasker:
    """Masks sensitive personally identifiable information (PII) before LLM calls."""

    # Regex patterns for common sensitive Indian / global PII
    PHONE_REGEX = re.compile(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b")
    AADHAAR_REGEX = re.compile(r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b")
    PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")
    CARD_REGEX = re.compile(r"\b(?:\d[ \-]*?){13,16}\b")

    @classmethod
    def mask(cls, text: str) -> tuple[str, dict[str, Any]]:
        """
        Mask PII patterns in text.
        Returns:
            sanitized_text: text with PII replaced by tokens ([PHONE_1], [AADHAAR_1])
            mapping: dict mapping tokens back to original values
        """
        if not text:
            return "", {}

        mapping: dict[str, str] = {}
        sanitized = text

        # Mask PAN numbers
        pan_count = 0
        for match in cls.PAN_REGEX.finditer(text):
            val = match.group(0)
            token = f"[PAN_{pan_count + 1}]"
            mapping[token] = val
            sanitized = sanitized.replace(val, token)
            pan_count += 1

        # Mask Aadhaar numbers
        aadhaar_count = 0
        for match in cls.AADHAAR_REGEX.finditer(sanitized):
            val = match.group(0)
            token = f"[AADHAAR_{aadhaar_count + 1}]"
            mapping[token] = val
            sanitized = sanitized.replace(val, token)
            aadhaar_count += 1

        # Mask Phone numbers
        phone_count = 0
        for match in cls.PHONE_REGEX.finditer(sanitized):
            val = match.group(0)
            token = f"[PHONE_{phone_count + 1}]"
            mapping[token] = val
            sanitized = sanitized.replace(val, token)
            phone_count += 1

        return sanitized, mapping
