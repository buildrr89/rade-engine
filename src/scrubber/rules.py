from __future__ import annotations

import re

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){2,4}\d{2,4}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._-]+\b")
TOKEN_RE = re.compile(r"\b(?:sk|rk|pk|tok)_[A-Za-z0-9_-]{8,}\b")

SENSITIVE_KEYS = {
    "name",
    "email",
    "phone",
    "address",
    "token",
    "secret",
    "session_id",
    "authorization",
    "payment",
}
