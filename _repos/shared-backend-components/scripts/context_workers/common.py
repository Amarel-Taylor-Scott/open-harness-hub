"""Shared deterministic helpers for Context Fidelity workers."""
from __future__ import annotations

import hashlib
import re
from typing import Any

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
ENTITY_RE = re.compile(r"\b(?:[A-Z][a-z0-9]+|[A-Z]{2,})(?:[\s/&-]+(?:[A-Z][a-z0-9]+|[A-Z]{2,})){0,5}\b")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]{2,}")
CLAIM_SIGNAL_RE = re.compile(
    r"\b(is|are|was|were|must|shall|should|required|requires|prohibited|allowed|deadline|effective|expires|updated|current|latest|policy|rule|threshold|limit)\b",
    re.I,
)
FRAGILE_RE = re.compile(
    r"\b(current|currently|latest|recent|recently|today|now|as of|deadline|expires|price|rate|threshold|limit|may|might|could|usually|generally|soon|planned|expected)\b",
    re.I,
)
DATE_OR_NUMBER_RE = re.compile(r"\b(?:20\d{2}|\d+(?:\.\d+)?\s?(?:%|percent|days|months|years)|\$\s?\d[\d,]*)\b", re.I)
NEGATIVE_RE = re.compile(r"\b(not|must not|cannot|prohibited|forbidden|expired|revoked)\b", re.I)
POSITIVE_RE = re.compile(r"\b(required|must|shall|allowed|valid|approved|effective|active)\b", re.I)
STOP_WORDS = {
    "and", "are", "but", "for", "from", "has", "have", "into", "must", "not", "that", "the", "this",
    "with", "when", "where", "will", "would", "should", "could", "about", "after", "before",
}


def stable_hash(prefix: str, text: str, n: int) -> str:
    return f"{prefix}-{n:03d}-{hashlib.sha1(text.encode('utf-8', errors='ignore')).hexdigest()[:8]}"


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> list[str]:
    out: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        out.extend(SENTENCE_RE.split(paragraph.strip()))
    return [compact(s) for s in out if len(compact(s)) >= 20]


def chunk_text(text: str, target_chars: int = 900) -> list[dict[str, Any]]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs and text.strip():
        paragraphs = [compact(text)]
    chunks: list[dict[str, Any]] = []
    buf: list[str] = []
    size = 0
    for p in paragraphs:
        if buf and size + len(p) > target_chars:
            body = "\n\n".join(buf)
            chunks.append({"id": stable_hash("chunk", body, len(chunks) + 1), "text": body, "char_count": len(body)})
            buf, size = [], 0
        buf.append(p)
        size += len(p) + 2
    if buf:
        body = "\n\n".join(buf)
        chunks.append({"id": stable_hash("chunk", body, len(chunks) + 1), "text": body, "char_count": len(body)})
    return chunks


def entities(text: str) -> list[str]:
    found = {compact(m.group(0).strip(" .,:;()[]{}")) for m in ENTITY_RE.finditer(text)}
    stop = {"The", "This", "That", "These", "Those", "As", "According", "A", "An", "Later", "Current", "Latest", "Recruitment"}
    return sorted(
        (e for e in found if e and e not in stop and not e.lower().startswith(("according ", "as of "))),
        key=lambda s: (-len(s.split()), s.lower()),
    )


def subject(sentence: str, entity_labels: list[str]) -> str:
    lowered = sentence.lower()
    for entity in entity_labels:
        if entity.lower() in lowered:
            return entity
    words = WORD_RE.findall(sentence)
    return " ".join(words[:5]).lower() if words else "claim"
