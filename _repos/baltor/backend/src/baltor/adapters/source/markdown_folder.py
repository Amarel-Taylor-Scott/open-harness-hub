#!/usr/bin/env python3
"""adapters/source/markdown_folder — MarkdownFolderAdapter (markdown vaults / Obsidian-style notes).

A markdown note folder is a SOURCE, not truth. Each ``.md`` note flows through the SAME governed path as
every other source type (see ``_repos/shared-backend-components/scripts/ingest/source_adapters.py``): note → ``source_record``;
frontmatter **scalar** fields → ``source_field`` + ``atomic_fact`` (promotion-eligible only when the
frontmatter marks the field structured/promotable); note **prose** → ``narrative_allegation`` (one per
sentence, ``claim_status=unverified_allegation``, NOT promotion-eligible — a note's claims are not facts);
``[[wikilinks]]`` → recorded as ``note_links_to`` edge candidates in artifact metadata (candidates, not
served edges); ``#tags`` → recorded as tag metadata. A ``.obsidian/`` config dir is ignored.

Governance carried by every artifact (reusing the existing ``_artifact`` helper): tenant_id, source_id,
source scope, parser_provider, content hash, parent lineage, source handle. **Default scope is
``tenant_private``** — a private vault never leaks to ``global_public`` unless a note's frontmatter
explicitly sets ``source_scope: global_public``. Frontmatter ``source_authority`` is honored per-note.

Source handle: ``ctx://tenant/<tid>/source/<sid>#note.<relpath>.<field-or-sN>``.

Deterministic + offline + stdlib only: no yaml dep (frontmatter is parsed line-by-line), no wall-clock
(time is injected via ``now``), no RNG; content hashes are content-addressed, so same input → same output.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Mapping

# Reuse the EXISTING governed helpers — do NOT re-implement artifact shape / handle base / hashing.
from scripts.ingest.source_adapters import _artifact, _base_handle, _hash, _sentences

#: directory names that are tool config, not notes — ignored during ingest.
_IGNORED_DIRS = {".obsidian", ".git", ".trash"}

#: frontmatter keys that, when truthy, mark a note's STRUCTURED frontmatter fields promotion-eligible.
#: A note's frontmatter is data the author asserted as structured; prose is always held out regardless.
_PROMOTE_KEYS = {"promotion_eligible", "promote", "structured", "verified"}

#: frontmatter keys that carry governance overrides (consumed, not emitted as facts).
_SCOPE_KEY = "source_scope"
_AUTHORITY_KEY = "source_authority"
_GLOBAL_PUBLIC = "global_public"
_TENANT_PRIVATE = "tenant_private"

#: truthy spellings accepted in frontmatter scalar parsing (stdlib, no yaml).
_TRUE = {"true", "yes", "1", "on"}
_FALSE = {"false", "no", "0", "off"}


def _wikilinks(text: str) -> list[str]:
    """Extract ``[[Target]]`` / ``[[Target|alias]]`` link targets, in first-seen order, de-duplicated."""
    out: list[str] = []
    i = 0
    while True:
        a = text.find("[[", i)
        if a < 0:
            break
        b = text.find("]]", a + 2)
        if b < 0:
            break
        inner = text[a + 2:b].split("|", 1)[0].strip()
        if inner and inner not in out:
            out.append(inner)
        i = b + 2
    return out


def _tags(text: str) -> list[str]:
    """Extract ``#tag`` tokens (alnum/_/-/ /), first-seen order, de-duplicated. Ignores ``#`` headings."""
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        # a markdown heading is "# Heading" (hash followed by a space); a tag is "#word" (no space).
        toks = line.split()
        for tok in toks:
            if not tok.startswith("#") or tok.startswith("# ") or len(tok) < 2:
                continue
            body = tok[1:]
            if body and all(c.isalnum() or c in "_-/" for c in body):
                t = "#" + body
                if t not in out:
                    out.append(t)
    return out


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a leading ``---`` YAML-ish frontmatter block from the body. STDLIB line parse, no yaml dep.

    Returns ``(frontmatter_dict, body_text)``. Only flat ``key: value`` scalars and simple
    ``key: [a, b]`` / ``key:\\n  - a`` lists are recognised; anything else is ignored (never guessed).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break
    if end is None:
        return {}, text
    fm: dict = {}
    cur_list_key: str | None = None
    for raw in lines[1:end]:
        # list item continuation:  "  - value"
        stripped = raw.strip()
        if cur_list_key is not None and stripped.startswith("- "):
            fm[cur_list_key].append(_coerce(stripped[2:].strip()))
            continue
        cur_list_key = None
        if ":" not in raw:
            continue
        key, _, val = raw.partition(":")
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        if val == "":
            # could be the start of a block list ("key:\n  - a")
            fm[key] = []
            cur_list_key = key
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [_coerce(x.strip()) for x in inner.split(",") if x.strip()] if inner else []
        else:
            fm[key] = _coerce(val)
    body = "\n".join(lines[end + 1:])
    return fm, body


def _coerce(val: str):
    """Coerce a frontmatter scalar string to bool/int/float when unambiguous; else return the string."""
    v = val.strip().strip('"').strip("'")
    low = v.lower()
    if low in _TRUE:
        return True
    if low in _FALSE:
        return False
    try:
        return int(v)
    except ValueError:
        pass
    try:
        f = float(v)
        return f
    except ValueError:
        return v


def _is_truthy(val) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip().lower() in _TRUE
    return False


def _body_paragraphs(body: str) -> list[str]:
    """Body prose, minus headings / list bullets / blank lines, as paragraph blocks (heading-grouped)."""
    paras: list[str] = []
    buf: list[str] = []

    def flush():
        if buf:
            joined = " ".join(buf).strip()
            if joined:
                paras.append(joined)
            buf.clear()

    for line in body.splitlines():
        s = line.strip()
        if not s:
            flush()
            continue
        if s.startswith("#") and (len(s) == 1 or s[1] in "# "):
            # markdown heading — a structural marker, not a prose sentence
            flush()
            continue
        if s.startswith(("- ", "* ", "> ")):
            # bullets / blockquotes: keep the text but treat each as its own paragraph line
            buf.append(s[2:].strip())
            continue
        buf.append(s)
    flush()
    return paras


def _iter_notes(payload) -> list[tuple[str, str]]:
    """Yield ``(relpath, text)`` for each ``.md`` note, ignoring tool-config dirs. Accepts a dict OR a path.

    A dict ``{relpath: text}`` is used as-is (offline fixture); a filesystem path is walked (real connector,
    same port). Results are sorted by relpath for determinism.
    """
    notes: list[tuple[str, str]] = []
    if isinstance(payload, Mapping):
        for relpath, text in payload.items():
            rp = str(relpath).replace("\\", "/")
            if _ignored(rp) or not rp.lower().endswith(".md"):
                continue
            notes.append((rp, text.decode("utf-8") if isinstance(text, bytes) else str(text)))
    else:
        root = str(payload)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _IGNORED_DIRS]
            for fn in filenames:
                if not fn.lower().endswith(".md"):
                    continue
                full = os.path.join(dirpath, fn)
                rp = os.path.relpath(full, root).replace("\\", "/")
                if _ignored(rp):
                    continue
                with open(full, "r", encoding="utf-8") as fh:
                    notes.append((rp, fh.read()))
    notes.sort(key=lambda t: t[0])
    return notes


def _ignored(relpath: str) -> bool:
    return any(part in _IGNORED_DIRS for part in relpath.split("/"))


class MarkdownFolderAdapter:
    """SourceAdapter for a markdown note folder (Obsidian-style vault). Notes are sources, not truth."""

    source_type = "markdown"
    parser_provider = "markdown_vault"

    def ingest(self, payload, *, tenant_id, source_id, scope=_TENANT_PRIVATE, authority="unknown", now=0) -> dict:
        notes = _iter_notes(payload)
        arts: list[dict] = []
        link_edges: list[dict] = []
        ignored_seen = self._ignored_count(payload)
        note_summaries: list[dict] = []

        for relpath, text in notes:
            fm, body = _parse_frontmatter(text)
            # ── per-note governance overrides (default tenant_private; honor frontmatter) ──
            note_scope = scope
            if fm.get(_SCOPE_KEY) == _GLOBAL_PUBLIC:
                note_scope = _GLOBAL_PUBLIC
            elif fm.get(_SCOPE_KEY) == _TENANT_PRIVATE:
                note_scope = _TENANT_PRIVATE
            note_authority = str(fm.get(_AUTHORITY_KEY, authority))
            promote_fm = any(_is_truthy(fm.get(k)) for k in _PROMOTE_KEYS)

            base = _base_handle(tenant_id, note_scope, source_id)
            note_handle = f"{base}#note.{relpath}"
            note_rec = _artifact("source_record", handle=note_handle, value=relpath, tenant_id=tenant_id,
                                 scope=note_scope, source_id=source_id, parent=base)
            note_rec["source_type"] = self.source_type
            note_rec["parser_provider"] = self.parser_provider
            note_rec["authority"] = note_authority
            wls = _wikilinks(text)
            tgs = _tags(text)
            note_rec["note_links_to"] = wls           # edge CANDIDATES (not served edges)
            note_rec["note_tags"] = tgs
            note_rec["relpath"] = relpath
            arts.append(note_rec)

            # ── frontmatter scalar fields → source_field + atomic_fact (governance keys excluded) ──
            for field, value in fm.items():
                if field in {_SCOPE_KEY, _AUTHORITY_KEY} | _PROMOTE_KEYS:
                    continue
                if isinstance(value, list):
                    # frontmatter list → one source_field; each scalar item a structured value
                    fh = f"{note_handle}.{field}"
                    arts.append(_artifact("source_field", handle=fh, value=value, tenant_id=tenant_id,
                                          scope=note_scope, source_id=source_id, parent=note_handle))
                    for i, item in enumerate(value):
                        arts.append(_artifact("atomic_fact", handle=f"{fh}.{i}", value=item, tenant_id=tenant_id,
                                              scope=note_scope, source_id=source_id, parent=fh,
                                              claim_status="fact", promotion_eligible=promote_fm))
                    continue
                fh = f"{note_handle}.{field}"
                arts.append(_artifact("source_field", handle=fh, value=value, tenant_id=tenant_id,
                                      scope=note_scope, source_id=source_id, parent=note_handle))
                arts.append(_artifact("atomic_fact", handle=fh, value=value, tenant_id=tenant_id,
                                      scope=note_scope, source_id=source_id, parent=fh,
                                      claim_status="fact", promotion_eligible=promote_fm))

            # ── note prose → narrative_allegation per sentence (ALWAYS held out, never promotion-eligible) ──
            si = 0
            for para in _body_paragraphs(body):
                for sent in _sentences(para):
                    arts.append(_artifact("narrative_allegation", handle=f"{note_handle}.s{si}", value=sent,
                                          tenant_id=tenant_id, scope=note_scope, source_id=source_id,
                                          parent=note_handle, claim_status="unverified_allegation",
                                          promotion_eligible=False))
                    si += 1

            # ── wikilinks → note_links_to edge candidates in metadata (candidates only) ──
            for target in wls:
                link_edges.append({"edge_type": "note_links_to", "from_note": relpath, "to_note": target,
                                   "status": "candidate", "source_handle": f"{note_handle}.link.{target}",
                                   "content_hash": _hash({"from": relpath, "to": target}),
                                   "tenant_id": tenant_id, "scope": note_scope, "source_id": source_id})

            note_summaries.append({"relpath": relpath, "scope": note_scope, "authority": note_authority,
                                   "frontmatter_fields": sorted(k for k in fm
                                                                if k not in {_SCOPE_KEY, _AUTHORITY_KEY} | _PROMOTE_KEYS),
                                   "sentences": si, "wikilinks": wls, "tags": tgs,
                                   "frontmatter_promotion_eligible": promote_fm})

        raw = {"notes": [{"relpath": r, "text": t} for r, t in notes]}
        content_hash = _hash(raw)
        # the vault-level source_record (root). Vault default scope is the adapter's scope arg.
        vault_base = _base_handle(tenant_id, scope, source_id)
        src = {"artifact_id": "source-" + _hash(raw), "artifact_type": "source_record", "claim_status": "",
               "source_handle": vault_base, "content_hash": content_hash, "parent_artifact_id": "",
               "tenant_id": tenant_id, "scope": scope, "source_id": source_id, "source_type": self.source_type,
               "parser_provider": self.parser_provider, "authority": authority, "is_source_root": True,
               "note_count": len(notes), "ignored_config_entries": ignored_seen, "ingested_at": now}
        return {"consumable": True, "source_type": self.source_type, "parser_provider": self.parser_provider,
                "source_id": source_id, "tenant_id": tenant_id, "scope": scope, "authority": authority,
                "content_hash": content_hash, "note_count": len(notes), "ignored_config_entries": ignored_seen,
                "source_artifacts": [src], "artifacts": [src] + arts, "link_edges": link_edges,
                "notes": note_summaries}

    @staticmethod
    def _ignored_count(payload) -> int:
        if isinstance(payload, Mapping):
            return sum(1 for rp in payload if _ignored(str(rp).replace("\\", "/")))
        cnt = 0
        root = str(payload)
        if os.path.isdir(root):
            for dirpath, dirnames, filenames in os.walk(root):
                rp = os.path.relpath(dirpath, root).replace("\\", "/")
                if _ignored(rp + "/x"):
                    cnt += len(filenames)
        return cnt


def _self_demo(now: int = 0) -> dict:
    """In-memory fixture demo (used by the proof / docs). Deterministic; time injected."""
    vault = {
        "reg-e-error-resolution.md": (
            "---\nsource_scope: global_public\nsource_authority: official\n"
            "regulation: Reg E\nresolution_days: 10\nstructured: true\ntags: [compliance, banking]\n---\n"
            "# Reg E Error Resolution\n\n"
            "The bank investigates a reported error. It links to [[Dispute Intake]].\n"
        ),
        "private-meeting-note.md": (
            "---\nproject: Acme\n---\n"
            "# Internal note\n\nWe think the vendor overcharged us. Follow up with [[Vendor Contract]].\n"
            "#todo #billing\n"
        ),
        ".obsidian/workspace.json": '{"main": "ignored config"}',
    }
    return MarkdownFolderAdapter().ingest(vault, tenant_id="acme", source_id="vault1", now=now)


if __name__ == "__main__":  # pragma: no cover - manual inspection only
    print(json.dumps(_self_demo(now=1_000_000), indent=2, default=str)[:1200])
