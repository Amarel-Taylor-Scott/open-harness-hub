#!/usr/bin/env python3
"""Backs `processor/draft-quality-gate`.

Deterministic pre-LLM-judge filter that rejects obviously bad drafts before
spending any LLM tokens on them. At scale (~1M drafts), this single check
saves the vast majority of judge-cost while letting the rubric do its work
only on plausible candidates.

Pass criteria (ALL must hold for `accepted: true`):
  - required envelope fields present (id, type, version, name, description,
    license, lifecycle, industry, capability, modality)
  - id format matches "{type}/{kebab-slug}" with slug ≤ 64 chars
  - no placeholder text (TODO, FIXME, lorem ipsum, XXX, REPLACE_ME, FILL_IN)
  - description ≥ 80 chars and ≤ 4000 chars
  - if attribution present, has source_url AND author AND license
  - tags is a non-empty list
  - id slug does not collide with a live catalog entry
  - YAML serializes without a parse-roundtrip difference

The gate ONLY decides accept/reject; it does NOT rate quality on a continuum.
Survivors go to `processor/llm-judge` for rubric scoring.

CLI:
    python -m scripts.processors.draft_quality_gate --self-test
    python -m scripts.processors.draft_quality_gate --check path/to/draft.yaml

Module entrypoint:
    from scripts.processors.draft_quality_gate import run
    res = run(draft_manifest={...}, live_catalog_ids={...})
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
CATALOG = _resource("catalog")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db.catalog_row_source import iter_components_from_rows, resolve_catalog_row_dir

# ─── Constants ──────────────────────────────────────────────────────────────

PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"\blorem\s+ipsum\b", re.IGNORECASE),
    re.compile(r"\bXXX\b"),  # case-sensitive — common in code comments
    re.compile(r"REPLACE[_-]?ME", re.IGNORECASE),
    re.compile(r"FILL[_-]?IN", re.IGNORECASE),
    re.compile(r"\b\?\?\?\?\b"),
    re.compile(r"<\s*placeholder\s*>", re.IGNORECASE),
]

REQUIRED_ENVELOPE_FIELDS = [
    "id",
    "type",
    "version",
    "name",
    "description",
    "license",
    "lifecycle",
    "industry",
    "capability",
    "modality",
]

ID_PATTERN = re.compile(
    r"^(harness|pipeline|benchmark|rule-pack|knowledge-pack|logic-pack|tool|"
    r"persona|adapter|rubric|dataset|schema|processor|pattern)"
    r"/[a-z0-9]+(-[a-z0-9]+)*$"
)

MIN_DESCRIPTION_CHARS = 80
MAX_DESCRIPTION_CHARS = 4000


# ─── Helpers ────────────────────────────────────────────────────────────────


def _walk_strings(node: Any):
    """Yield every string anywhere in a nested dict/list manifest."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_strings(v)


def _load_live_catalog_ids() -> set[str]:
    """Read every live catalog manifest id.

    Prefer database-shaped catalog rows. YAML remains a seed/export bootstrap
    fallback when the manifest bridge rows have not been generated.
    """
    row_dir = resolve_catalog_row_dir()
    if row_dir is not None:
        return {component.id for component in iter_components_from_rows(row_dir)}

    try:
        import yaml
    except ImportError:
        return set()
    ids: set[str] = set()
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        if isinstance(data, dict) and "id" in data:
            ids.add(data["id"])
    return ids


# ─── Gate ───────────────────────────────────────────────────────────────────


def run(
    draft_manifest: dict,
    *,
    live_catalog_ids: set[str] | None = None,
    min_description_chars: int = MIN_DESCRIPTION_CHARS,
    max_description_chars: int = MAX_DESCRIPTION_CHARS,
) -> dict[str, Any]:
    """Deterministic pre-judge filter. Cheap. Idempotent. Pure.

    Returns:
        {
          "accepted": bool,
          "reasons": [str, ...],   # populated when accepted=False
          "warnings": [str, ...],  # advisory, doesn't fail the gate
        }
    """
    if live_catalog_ids is None:
        live_catalog_ids = _load_live_catalog_ids()

    reasons: list[str] = []
    warnings: list[str] = []

    if not isinstance(draft_manifest, dict):
        return {"accepted": False, "reasons": ["draft is not a mapping"], "warnings": []}

    # Required envelope fields
    for field_name in REQUIRED_ENVELOPE_FIELDS:
        if field_name not in draft_manifest:
            reasons.append(f"missing required envelope field: {field_name}")
            continue
        val = draft_manifest[field_name]
        if val in (None, "", [], {}):
            reasons.append(f"required field is empty: {field_name}")

    # ID format + collision
    mid = draft_manifest.get("id", "")
    if not isinstance(mid, str) or not ID_PATTERN.match(mid):
        reasons.append(f"id does not match {{type}}/{{kebab-slug}} pattern: {mid!r}")
    elif mid in live_catalog_ids:
        reasons.append(f"id collides with existing live catalog entry: {mid}")
    elif "/" in mid:
        slug = mid.split("/", 1)[1]
        if len(slug) > 64:
            reasons.append(f"slug exceeds 64 chars ({len(slug)}): {slug}")
        if re.search(r"\d{4,}", slug):
            warnings.append(f"slug contains a 4+ digit run (looks auto-generated): {slug}")
        if "wikipedia" in slug.lower() or "test" in slug.lower() or "foo" in slug.lower():
            warnings.append(f"slug contains a generic word ('wikipedia'/'test'/'foo'): {slug}")

    # Description quality
    desc = draft_manifest.get("description", "")
    if isinstance(desc, str):
        desc_stripped = desc.strip()
        if len(desc_stripped) < min_description_chars:
            reasons.append(
                f"description too short ({len(desc_stripped)} < {min_description_chars} chars)"
            )
        if len(desc_stripped) > max_description_chars:
            warnings.append(
                f"description very long ({len(desc_stripped)} > {max_description_chars} chars)"
            )

    # Placeholder text anywhere in the manifest
    for s in _walk_strings(draft_manifest):
        for pat in PLACEHOLDER_PATTERNS:
            if pat.search(s):
                reasons.append(f"placeholder text matched ({pat.pattern}) in: {s[:120]!r}")
                break

    # Attribution completeness (if present)
    attr = draft_manifest.get("attribution")
    if attr is not None:
        if not isinstance(attr, dict):
            reasons.append("attribution must be an object")
        else:
            for k in ("source_url", "author", "license"):
                if not attr.get(k):
                    reasons.append(f"attribution.{k} missing or empty")

    # Tags should exist and be non-empty
    tags = draft_manifest.get("tags")
    if tags is None or tags == []:
        warnings.append("tags list missing or empty (recommended for discoverability)")

    # Lifecycle should be 'experimental' for drafts; other values trigger a curator-must-decide warning
    lifecycle = draft_manifest.get("lifecycle")
    if lifecycle and lifecycle != "experimental":
        warnings.append(
            f"draft lifecycle should be 'experimental' (got {lifecycle!r}); curator must justify promotion"
        )

    # YAML serialization roundtrip parity (catches non-serializable types, e.g. datetime objects from parsers)
    try:
        import yaml
        rt = yaml.safe_load(yaml.safe_dump(draft_manifest, sort_keys=False))
        if rt != draft_manifest:
            warnings.append("YAML roundtrip changed manifest shape (key order / type coercion)")
    except ImportError:
        pass
    except yaml.YAMLError as e:
        reasons.append(f"manifest does not yaml.safe_dump cleanly: {e}")

    accepted = len(reasons) == 0
    return {"accepted": accepted, "reasons": reasons, "warnings": warnings}


# ─── Self-test (offline) ────────────────────────────────────────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    good_draft = {
        "id": "knowledge-pack/well-formed-draft",
        "type": "knowledge-pack",
        "version": "0.1.0",
        "name": "Well-formed draft",
        "description": (
            "A test draft used by the quality gate self-test. It has enough description "
            "characters to clear the minimum threshold, names what it is, and avoids placeholder text."
        ),
        "license": "CC-BY-4.0",
        "lifecycle": "experimental",
        "industry": ["cross_industry"],
        "capability": ["retrieval"],
        "modality": ["text"],
        "tags": ["self-test"],
        "created": "2026-05-24",
        "updated": "2026-05-24",
    }

    print("[self-test] good draft accepted")
    res = run(good_draft, live_catalog_ids=set())
    check("accepted=true on well-formed draft", res["accepted"], detail=str(res["reasons"]))

    print("[self-test] placeholder text rejected")
    bad = {**good_draft, "description": good_draft["description"] + " TODO: fill in later"}
    res = run(bad, live_catalog_ids=set())
    check("rejected on TODO placeholder", not res["accepted"])
    check("reason mentions placeholder", any("placeholder" in r.lower() for r in res["reasons"]))

    print("[self-test] short description rejected")
    bad = {**good_draft, "description": "too short"}
    res = run(bad, live_catalog_ids=set())
    check("rejected on short description", not res["accepted"])

    print("[self-test] id-format rejected")
    bad = {**good_draft, "id": "knowledge-pack/INVALID_SLUG_with_underscores"}
    res = run(bad, live_catalog_ids=set())
    check("rejected on invalid id slug", not res["accepted"])

    print("[self-test] id-collision rejected")
    res = run(good_draft, live_catalog_ids={"knowledge-pack/well-formed-draft"})
    check("rejected on live-catalog id collision", not res["accepted"])

    print("[self-test] attribution incompleteness rejected")
    bad = {**good_draft, "attribution": {"source_url": "https://example.com"}}
    res = run(bad, live_catalog_ids=set())
    check("rejected on incomplete attribution", not res["accepted"])

    print("[self-test] missing required field rejected")
    bad = {k: v for k, v in good_draft.items() if k != "license"}
    res = run(bad, live_catalog_ids=set())
    check("rejected on missing license", not res["accepted"])

    print("[self-test] non-experimental lifecycle warns (but doesn't reject)")
    other = {**good_draft, "lifecycle": "stable"}
    res = run(other, live_catalog_ids=set())
    check("still accepted with 'stable' lifecycle", res["accepted"])
    check("warning emitted on non-experimental lifecycle", any("lifecycle" in w.lower() for w in res["warnings"]))

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Deterministic pre-LLM draft quality gate.")
    p.add_argument("--check", help="Path to a draft YAML to check")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.check:
        p.error("--check PATH or --self-test required")

    try:
        import yaml
    except ImportError:
        sys.stderr.write("pyyaml is required: pip install pyyaml\n")
        return 2
    draft = yaml.safe_load(Path(args.check).read_text(encoding="utf-8"))
    res = run(draft)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["accepted"] else 1


if __name__ == "__main__":
    sys.exit(_main())
