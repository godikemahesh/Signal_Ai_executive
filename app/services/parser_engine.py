"""
Signal — Email Parser Engine
Extracts plain text, HTML, subject, senders, recipients, and snippet from raw email data.
"""

import base64
from typing import Any, Optional
from bs4 import BeautifulSoup
import html2text


class ParserEngine:
    """Parses raw Gmail API payload into clean text and structured attributes."""

    @staticmethod
    def parse_gmail_message(message_payload: dict[str, Any]) -> dict[str, Any]:
        """Extract clean text content, headers, and metadata from Gmail message payload."""
        headers_list = message_payload.get("payload", {}).get("headers", [])
        headers = {h["name"].lower(): h["value"] for h in headers_list}

        subject = headers.get("subject", "(No Subject)")
        from_raw = headers.get("from", "")
        sender_email, sender_name = ParserEngine._parse_email_address(from_raw)

        to_raw = headers.get("to", "")
        cc_raw = headers.get("cc", "")
        date_str = headers.get("date", "")

        snippet = message_payload.get("snippet", "")

        # Extract plain text and HTML bodies
        plain_body, html_body = ParserEngine._extract_body(message_payload.get("payload", {}))

        clean_text = plain_body
        if not clean_text and html_body:
            clean_text = ParserEngine._html_to_plain_text(html_body)

        if not clean_text:
            clean_text = snippet

        return {
            "gmail_message_id": message_payload.get("id"),
            "gmail_thread_id": message_payload.get("threadId"),
            "sender_email": sender_email.lower(),
            "sender_name": sender_name,
            "to_recipients": [t.strip() for t in to_raw.split(",") if t.strip()],
            "cc_recipients": [c.strip() for c in cc_raw.split(",") if c.strip()],
            "subject": subject,
            "snippet": snippet,
            "body_plain": clean_text,
            "body_html": html_body,
            "gmail_internal_date": int(message_payload.get("internalDate", 0)),
        }

    @staticmethod
    def _parse_email_address(raw_header: str) -> tuple[str, str]:
        """Parse 'John Doe <john@example.com>' into ('john@example.com', 'John Doe')."""
        if "<" in raw_header and ">" in raw_header:
            name_part, email_part = raw_header.rsplit("<", 1)
            email = email_part.replace(">", "").strip()
            name = name_part.replace('"', "").replace("'", "").strip()
            return email, name
        return raw_header.strip(), ""

    @staticmethod
    def _extract_body(payload: dict[str, Any]) -> tuple[str, str]:
        """Recursively extract plain text and HTML content from MIME payload parts."""
        plain_text = ""
        html_text = ""

        mime_type = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data", "")

        if body_data:
            decoded = base64.urlsafe_b64decode(body_data.encode("UTF-8")).decode("utf-8", errors="ignore")
            if mime_type == "text/plain":
                plain_text += decoded
            elif mime_type == "text/html":
                html_text += decoded

        parts = payload.get("parts", [])
        for part in parts:
            p_plain, p_html = ParserEngine._extract_body(part)
            plain_text += p_plain
            html_text += p_html

        return plain_text, html_text

    @staticmethod
    def _html_to_plain_text(html_content: str) -> str:
        """Convert HTML content to clean readable plain text."""
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        h.ignore_emphasis = True
        return h.handle(html_content).strip()
