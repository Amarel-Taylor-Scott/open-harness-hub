"""src.openharnesshub.intake — OWNER-PROVIDED intake: feed raw materials you supply straight into a hub's lifecycle.

Two ways content reaches a hub (both governed; both serves_truth=False until the hub's verify gate passes):
  1. DISCOVERY (autonomous) — OpenClaw/Hermes + Teleon's keep_hub_fresh search public sources on the hubs cadence.
  2. INTAKE (this module) — YOU hand the hub raw materials and it digests them:
       * **OKF** (Open Knowledge Format: markdown + YAML frontmatter) — parsed losslessly (raw kept) → a component.
       * **links** — fetched (injectable fetch port) → OKF-parsed if shaped like OKF, else a generic component.
       * **raw text / dicts** — pasted blobs or already-structured candidates.

Each material runs the SAME per-hub lifecycle as discovery (``HubEngine``): normalize → digest → (optional improve) →
verify → version. ``improve=True`` asks the hub's model port for ONE concrete improvement and stores it as a NEW
version of the same component (lossless: the raw version is preserved). Nothing serves until ``verify`` passes
(discovery≠trust). Open layer: stdlib + the engine only (the real fetch/model ports are wired by the operator CLI).
"""
from __future__ import annotations

import json
import re
from typing import Callable, Iterable

from src.openharnesshub.component_store import GLOBAL_TENANT
from src.openharnesshub.hub_engine import HubEngine


# ── OKF (Open Knowledge Format) parsing — markdown + YAML frontmatter, LOSSLESS (raw is always kept) ──────────
def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Split a `---\\nkey: value\\n---\\nbody` document. Minimal YAML (key: value, `- item` lists) so no yaml dep;
    on anything unexpected we keep the whole text as the body (lossless — never drop content)."""
    t = text.lstrip("﻿")
    if not t.startswith("---"):
        return {}, text
    parts = re.split(r"^---\s*$", t, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        return {}, text
    fm_raw, body = parts[1], parts[2]
    fm: dict = {}
    cur_key = None
    for line in fm_raw.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z0-9_.\- ]+):\s*(.*)$", line)
        if m:
            cur_key = m.group(1).strip()
            val = m.group(2).strip().strip('"\'')
            fm[cur_key] = val if val else []
        elif line.lstrip().startswith("- ") and cur_key:
            if not isinstance(fm.get(cur_key), list):
                fm[cur_key] = []
            fm[cur_key].append(line.lstrip()[2:].strip().strip('"\''))
    return fm, body


def _first_heading(md: str) -> str:
    for line in md.splitlines():
        if line.strip().startswith("#"):
            return line.lstrip("# ").strip()
    return ""


def parse_okf(text: str, *, source: str | None = None) -> dict:
    """Parse one Open Knowledge Format document into a component body. LOSSLESS: the raw text is preserved in
    ``raw_okf`` so nothing the parser doesn't understand is lost (lossless-distillation law)."""
    fm, md = _split_frontmatter(text)
    body: dict = {"raw_okf": text}
    body.update({k: v for k, v in fm.items() if k not in body})
    name = fm.get("title") or fm.get("name") or _first_heading(md) or (source or "okf-item")
    body["name"] = str(name)
    body["okf_body"] = md.strip()
    if "summary" not in body and md.strip():
        body["summary"] = md.strip().splitlines()[0][:240]
    if source:
        body["source_url"] = source
    return body


def _looks_like_okf(text: str) -> bool:
    return text.lstrip("﻿").startswith("---") and "\n---" in text[:4000]


def _default_fetch(url: str, *, timeout: float = 15.0) -> str:
    """Stdlib link fetch (injectable; replace in tests / behind a real tool). Resilient: returns '' on any failure
    so one dead link never stops intake. Login-walled sources (e.g. facebook) won't return content — paste the
    material via texts=/okf= instead."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "OpenHarnessHub-intake/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 — operator-supplied URL
            return r.read(2_000_000).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return ""


def _to_body(material, kind: str, *, fetch_fn: Callable[[str], str]) -> dict | None:
    """Turn one owner-provided material into a component body (or None to skip)."""
    if kind == "dict":
        return dict(material) if isinstance(material, dict) else None
    if kind == "okf":
        return parse_okf(str(material))
    if kind == "text":
        text = str(material).strip()
        if not text:
            return None
        return {"name": text.splitlines()[0][:120], "body_text": text,
                "summary": text.splitlines()[0][:240]}
    if kind == "link":
        url = str(material).strip()
        content = fetch_fn(url)
        if _looks_like_okf(content):
            return parse_okf(content, source=url)
        body = {"name": url, "source_url": url}
        if content:
            body["body_text"] = content[:20_000]
            body["summary"] = next((ln.strip() for ln in content.splitlines() if ln.strip()), url)[:240]
        return body
    return None


def ingest_materials(engine: HubEngine, *, dicts: Iterable = (), okf: Iterable = (), texts: Iterable = (),
                     links: Iterable = (), improve: bool = False, tenant: str = GLOBAL_TENANT,
                     fetch_fn: Callable[[str], str] | None = None) -> dict:
    """Feed OWNER-PROVIDED materials into one hub's lifecycle (digest → optional improve → verify → version).

    Returns a governed summary. Each item is a CANDIDATE (serves_truth=False) and only serves after verify passes.
    ``improve=True`` stores an additionally-improved NEW version (lossless — the raw version stays)."""
    fetch_fn = fetch_fn or _default_fetch
    items: list[dict] = []
    ingested = verified = improved = 0
    plan = [(m, "dict") for m in dicts] + [(m, "okf") for m in okf] + \
           [(m, "text") for m in texts] + [(m, "link") for m in links]
    for material, kind in plan:
        try:
            body = _to_body(material, kind, fetch_fn=fetch_fn)
            if not body:
                continue
            rec = engine.ingest(body, tenant=tenant)
            ingested += 1
            ok = engine.verify(rec)
            verified += int(ok)
            entry = {"component_id": rec["component_id"], "version": rec["version"], "kind": kind, "verified": ok}
            if improve:
                suggestion = engine.improve(rec["body"])
                rec2 = engine.ingest({**rec["body"], "improvement": suggestion, "improved_from": rec["version"]}, tenant=tenant)
                engine.verify(rec2)
                improved += 1
                entry["improved_version"] = rec2["version"]
                entry["improvement"] = suggestion
            items.append(entry)
        except Exception as e:  # noqa: BLE001 — one bad material never stops intake
            items.append({"kind": kind, "error": str(e)[:120]})
    return {"hub": engine.spec.hub_id, "tenant": tenant, "ingested": ingested, "verified": verified,
            "improved": improved, "items": items, "serves_truth": False}


__all__ = ["parse_okf", "ingest_materials"]
