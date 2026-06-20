#!/usr/bin/env python3
"""src/baltor/native/okf_adapter — interoperate with Google's Open Knowledge Format (OKF, Apache-2.0, v0.1) at
the EDGES: import an OKF knowledge repo into governed Baltor context objects, and export governed objects back to
OKF — WITHOUT making OKF our core object. OKF is a projection (like PROV-JSON / OpenLineage), not the source of
truth.

Why this is pure upside (see docs/research/context-layer-openness-2026-06-19.md): OKF standardizes the *container*
(a directory of UTF-8 markdown files with YAML frontmatter, one concept per file, `type` required, arbitrary keys
allowed, optional reserved `index.md`/`log.md`) — but it does NOT carry verification, freshness, source-authority,
or receipts. So we:
  * IMPORT OKF as a portable substrate (consume the one open format the hyperscalers are converging on), and
  * EXPORT our objects as OKF whose frontmatter ALSO carries our assurance (verified / authoritative_source /
    freshness_status / receipt) under an arbitrary key OKF permits, plus a reserved `log.md` reconstructed from our
    CDC/freshness history. We become the only OKF producer whose files prove whether their content is true/current.

  "They standardize where context LIVES; Baltor governs whether it's TRUE." OKF rides at the edge; our object stays
  the core.

LOSSLESS DISTILLATION: import→export→import preserves the answer-critical fields, the governance sidecar, AND any
arbitrary frontmatter keys (kept in ``extra``) — OKF is never a lossy promotion. Deterministic + offline + stdlib
only (no PyYAML: a minimal frontmatter codec; the governance sidecar travels as a one-line JSON string value, which
round-trips exactly). serves_truth is always False — a format adapter never serves truth. OKF is v0.1 DRAFT /
single-vendor, so this is a CANDIDATE interop format behind the native port — discovery ≠ trust.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

#: OKF's one hard rule: every concept file MUST declare `type`. Everything else is recommended/optional.
OKF_REQUIRED_KEY = "type"
#: OKF reserved files (progressive disclosure + change history).
OKF_INDEX_FILE = "index.md"
OKF_LOG_FILE = "log.md"
#: an arbitrary frontmatter key (OKF allows arbitrary keys) carrying our assurance as a one-line JSON string —
#: this is the governance OKF itself does not mandate, riding losslessly inside a conformant OKF file.
GOVERNANCE_KEY = "x_baltor_governance_json"
#: recommended OKF scalar keys we map to/from named fields (others are preserved verbatim in ``extra``).
_KNOWN_SCALARS = ("title", "description", "resource", "timestamp")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class GovernedConcept:
    """A Baltor context object — the CORE. OKF is one projection of it, never its definition."""
    concept_id: str
    type: str
    title: str = ""
    description: str = ""
    resource: str = ""
    timestamp: str = ""
    tags: tuple = ()
    body: str = ""
    governance: dict = field(default_factory=dict)   # verified / authoritative_source / freshness_status / receipt
    extra: dict = field(default_factory=dict)         # any other OKF frontmatter keys — preserved verbatim (lossless)

    def content_hash(self) -> str:
        return _sha256(json.dumps(self.as_dict(), sort_keys=True))

    def as_dict(self) -> dict:
        return {"concept_id": self.concept_id, "type": self.type, "title": self.title,
                "description": self.description, "resource": self.resource, "timestamp": self.timestamp,
                "tags": list(self.tags), "body": self.body, "governance": dict(self.governance),
                "extra": dict(self.extra), "serves_truth": False}


# ── frontmatter codec (minimal, deterministic, lossless for the shapes we emit) ──────────────────────────────
def _fmt_scalar(v) -> str:
    return json.dumps(v) if isinstance(v, str) and (":" in v or v.strip() != v) else str(v)


def _parse_scalar(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):                      # inline list: [a, b, c]
        inner = raw[1:-1].strip()
        return tuple(p.strip().strip('"') for p in inner.split(",") if p.strip()) if inner else ()
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("{") or raw.startswith("[")):
        try:
            return json.loads(raw)
        except Exception:
            return raw.strip('"')
    return raw


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Parse `---\\nkey: value\\n---\\nbody`. Unknown keys are returned raw; body is everything after the 2nd fence."""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    fm: dict = {}
    for ln in lines[1:end]:
        if not ln.strip() or ":" not in ln:
            continue
        k, _, v = ln.partition(":")
        fm[k.strip()] = v.strip()
    body = "\n".join(lines[end + 1:])
    return fm, body.lstrip("\n")


# ── IMPORT: OKF repo → governed concepts ─────────────────────────────────────────────────────────────────────
def okf_import_file(path: str, text: str) -> GovernedConcept:
    """Parse a single OKF concept file into a GovernedConcept. Enforces OKF's `type`-required rule."""
    fm, body = _split_frontmatter(text)
    if OKF_REQUIRED_KEY not in fm or not str(fm[OKF_REQUIRED_KEY]).strip():
        raise ValueError(f"OKF concept {path!r} is missing the required `type` key")
    gov = {}
    if GOVERNANCE_KEY in fm:
        try:
            gov = json.loads(fm[GOVERNANCE_KEY])
        except Exception:
            gov = {}
    tags = _parse_scalar(fm.get("tags", "")) if "tags" in fm else ()
    known = {OKF_REQUIRED_KEY, "tags", GOVERNANCE_KEY, *_KNOWN_SCALARS}
    extra = {k: _parse_scalar(v) for k, v in fm.items() if k not in known}
    return GovernedConcept(
        concept_id=path.rsplit("/", 1)[-1].removesuffix(".md"),
        type=str(fm[OKF_REQUIRED_KEY]).strip(),
        title=str(fm.get("title", "")).strip(), description=str(fm.get("description", "")).strip(),
        resource=str(fm.get("resource", "")).strip(), timestamp=str(fm.get("timestamp", "")).strip(),
        tags=tuple(tags) if isinstance(tags, (list, tuple)) else (), body=body,
        governance=gov, extra=extra)


def okf_import(repo: dict) -> list[GovernedConcept]:
    """Import an OKF repo ({path: file_text}). Reserved files (index.md/log.md) are skipped — they are projections,
    not concepts. Returns governed concepts (the core objects)."""
    out = []
    for path in sorted(repo):
        if path.rsplit("/", 1)[-1] in (OKF_INDEX_FILE, OKF_LOG_FILE):
            continue
        if path.endswith(".md"):
            out.append(okf_import_file(path, repo[path]))
    return out


# ── EXPORT: governed concepts → OKF repo (with our assurance + a CDC log.md) ──────────────────────────────────
def _frontmatter(concept: GovernedConcept) -> str:
    rows = [f"{OKF_REQUIRED_KEY}: {concept.type}"]
    for key in _KNOWN_SCALARS:
        val = getattr(concept, key)
        if val:
            rows.append(f"{key}: {_fmt_scalar(val)}")
    if concept.tags:
        rows.append("tags: [" + ", ".join(concept.tags) + "]")
    for k in sorted(concept.extra):
        rows.append(f"{k}: {_fmt_scalar(concept.extra[k])}")
    if concept.governance:
        gov = dict(concept.governance)
        gov.setdefault("serves_truth", False)
        rows.append(f"{GOVERNANCE_KEY}: {json.dumps(gov, sort_keys=True)}")
    return "---\n" + "\n".join(rows) + "\n---\n"


def okf_export_file(concept: GovernedConcept) -> str:
    return _frontmatter(concept) + (concept.body or "")


def _build_index(concepts: list[GovernedConcept]) -> str:
    lines = ["---", "type: index", "title: Knowledge index (governed)", "---", "",
             "# Concepts (progressive disclosure)", ""]
    for c in concepts:
        gov = "✓ verified" if c.governance.get("verified") else "unverified"
        fresh = c.governance.get("freshness_status", "—")
        lines.append(f"- [{c.title or c.concept_id}]({c.concept_id}.md) — `{c.type}` · {gov} · freshness: {fresh}")
    return "\n".join(lines) + "\n"


def _build_log(concepts: list[GovernedConcept]) -> str:
    """Reconstruct OKF's reserved change-history file from our CDC/freshness history — the assurance OKF lacks."""
    lines = ["---", "type: log", "title: Change history (CDC / freshness — Baltor-governed)", "---", "",
             "# Change history", ""]
    for c in concepts:
        for ev in c.governance.get("cdc_history", []) or []:
            lines.append(f"- `{c.concept_id}`: {ev.get('kind', 'changed')} @ {ev.get('version', '?')} "
                         f"(source {ev.get('source', c.governance.get('authoritative_source', '?'))})")
    if len(lines) == 7:
        lines.append("- (no recorded source changes)")
    return "\n".join(lines) + "\n"


def okf_export(concepts: list[GovernedConcept], *, include_reserved: bool = True) -> dict:
    """Export governed concepts as an OKF repo ({path: file_text}), with our governance in frontmatter + reserved
    index.md/log.md reconstructed from our assurance history. A conformant OKF repo that ALSO proves its content."""
    repo = {f"{c.concept_id}.md": okf_export_file(c) for c in concepts}
    if include_reserved:
        repo[OKF_INDEX_FILE] = _build_index(concepts)
        repo[OKF_LOG_FILE] = _build_log(concepts)
    return repo


def round_trip(concepts: list[GovernedConcept]) -> list[GovernedConcept]:
    """import(export(x)) — must preserve every answer-critical field + the governance sidecar + arbitrary extras."""
    return okf_import(okf_export(concepts, include_reserved=True))
