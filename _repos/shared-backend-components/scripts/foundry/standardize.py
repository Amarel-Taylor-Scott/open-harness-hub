#!/usr/bin/env python3
"""Foundry standardize — Stage 3 (deterministic; no model).

Turns a constructed draft body into a canonical, schema-valid, hashed, uniquely-
identified component. This is where the **ID & hash discipline** from `CLAUDE.md`
is enforced:

  - **content_hash** — sha256 over the canonical body MINUS the wrapper (id,
    version) and formatting/timestamps. Reordering keys, reflowing whitespace, or
    re-stamping `updated` does NOT change it; a real change to the substance DOES.
    ("Formatting changes should not create false versions; source content changes
    should be detectable even when the wrapper stays the same.")
  - **version_hash** — sha256 over the body MINUS timestamps (keeps id + version):
    identifies *this version of this component*; a real body or version change
    moves it.
  - **canonical id** — ``{type}/{slug}`` with a **stable hash suffix** derived from
    the source + slug, so daily batches don't collapse on a shared slug and the
    same source is idempotent ("Long generated IDs must include stable hash
    suffixes … never rely on truncation alone").

Schema validation reuses the **canonical** validator (`scripts.validate`) against
`schemas/{type}.schema.json` — not a reimplementation. A body that fails its schema
is culled with the reason (a construction bug, surfaced in the reject log).

Run ``python -m scripts.foundry.standardize`` for the offline self-test.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from scripts.db.catalog_row_source import iter_components_from_rows, resolve_catalog_row_dir
from scripts.foundry.contracts import LEGAL_TARGET_TYPES, BaseStage, Candidate, FoundryContext
from scripts.foundry.novelty import normalize_source_url

# Fields excluded from hashing. Timestamps/collection markers are formatting;
# id/version are the wrapper. Underscore-prefixed keys are always internal.
_FORMATTING_FIELDS = frozenset({"created", "updated", "collected_through", "frozen_at"})
_WRAPPER_FIELDS = frozenset({"id", "version"})
_DEFAULT_VERSION = "0.1.0"
_ID_HASH_LEN = 8                  # short, stable suffix appended to a slug (not an ID by itself)
_SLUG_MAX = 64                    # AGENTS.md slug rule: lowercase-with-dashes, ≤ 64 chars


# --------------------------------------------------------------------------- #
# slug + canonical id
# --------------------------------------------------------------------------- #
def slugify(name: str, max_len: int = _SLUG_MAX) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len].rstrip("-") or "draft"


def canonical_id(target_type: str, name: str, source: dict | None = None, *, stable_suffix: bool = True) -> str:
    """``{type}/{slug}`` (+ stable hash suffix for generated candidates).

    The suffix is a function of the normalized source_url + slug, so the *same
    source* yields the *same id* (idempotent re-runs) while two different sources
    that slugify alike don't collide.
    """
    base = slugify(name, _SLUG_MAX - (_ID_HASH_LEN + 1) if stable_suffix else _SLUG_MAX)
    if stable_suffix:
        key = f"{normalize_source_url((source or {}).get('source_url', ''))}|{base}"
        suffix = hashlib.sha256(key.encode("utf-8")).hexdigest()[:_ID_HASH_LEN]
        slug = f"{base}-{suffix}"
    else:
        slug = base
    return f"{target_type}/{slug}"


# --------------------------------------------------------------------------- #
# hashing (formatting-invariant)
# --------------------------------------------------------------------------- #
def _canonical_json(body: dict, drop: frozenset[str]) -> str:
    clean = {
        k: v for k, v in body.items()
        if k not in drop and not k.startswith("_") and v is not None
    }
    return json.dumps(clean, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def content_hash(body: dict) -> str:
    """sha256 of the body's *substance* (no id/version/timestamps)."""
    return hashlib.sha256(_canonical_json(body, _WRAPPER_FIELDS | _FORMATTING_FIELDS).encode("utf-8")).hexdigest()


def version_hash(body: dict) -> str:
    """sha256 identifying this version (keeps id+version; drops timestamps)."""
    return hashlib.sha256(_canonical_json(body, _FORMATTING_FIELDS).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# schema validation (reuse the canonical validator — no reimplementation)
# --------------------------------------------------------------------------- #
_SCHEMA_CACHE: dict[str, Any] | None = None


def _schemas() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        from scripts.validate import load_schemas
        _SCHEMA_CACHE = load_schemas()
    return _SCHEMA_CACHE


def schema_valid(body: dict) -> tuple[bool, list[str]]:
    """Validate against ``schemas/{type}.schema.json`` using the repo validator."""
    from scripts.validate import TYPE_TO_SCHEMA, make_validator

    t = body.get("type")
    schema_name = TYPE_TO_SCHEMA.get(t or "")
    if not schema_name:
        return False, [f"no schema registered for type {t!r}"]
    validator = make_validator(_schemas(), schema_name)
    errors = sorted(validator.iter_errors(body), key=lambda e: list(e.path))
    msgs = [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors[:5]]
    return (not errors), msgs


def sample_manifest_for_schema_validation(row_dir: Path | str | None = None) -> tuple[Path | str | None, dict | None, str]:
    """Return a known-good manifest from database rows, with YAML fallback.

    Foundry standardization should not need operational catalog YAML access just
    to prove the canonical validator works. Hosted/database-backed smokes pass a
    row directory; local static checks still fall back to seed/export manifests.
    """
    resolved_row_dir = resolve_catalog_row_dir(row_dir)
    if resolved_row_dir is not None:
        preferred_types = ("knowledge-pack", "rule-pack", "tool", "persona")
        components = iter_components_from_rows(resolved_row_dir)
        for component_type in preferred_types:
            for component in components:
                if component.type == component_type:
                    return component.source_path or component.id, component.manifest, "database_rows"
        if components:
            component = components[0]
            return component.source_path or component.id, component.manifest, "database_rows"

    repo = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
    for component_type in ("knowledge-pack", "rule-pack", "tool", "persona"):
        for path in sorted((repo / "catalog").rglob("*.yaml")):
            try:
                import yaml
                value = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(value, dict) and value.get("type") == component_type:
                return path, value, "catalog_yaml_seed_export"
    return None, None, "missing"


# --------------------------------------------------------------------------- #
# the stage
# --------------------------------------------------------------------------- #
class StandardizeStage(BaseStage):
    """Canonicalize → id → hash → schema-validate. Culls schema-invalid bodies."""

    name = "standardize"

    def __init__(self, *, now_s: float | None = None, stable_suffix: bool = True) -> None:
        # now_s lets tests pin timestamps; default = wall clock.
        self._now = time.strftime("%Y-%m-%d", time.gmtime(now_s))
        self._stable_suffix = stable_suffix

    def run(self, batch: list[Candidate], ctx: FoundryContext) -> list[Candidate]:
        for c in batch:
            if not c.alive:
                continue

            # type/vocabulary
            if c.target_type not in LEGAL_TARGET_TYPES:
                c.drop(self.name, f"vocabulary: illegal target_type {c.target_type!r}")
                continue
            body = dict(c.body or {})
            body["type"] = c.target_type

            # wrapper fields the schema expects
            name = body.get("name") or (c.gap or {}).get("summary") or c.target_type
            body.setdefault("name", name)
            cid = canonical_id(c.target_type, name, c.source, stable_suffix=self._stable_suffix)
            body["id"] = cid
            body.setdefault("version", _DEFAULT_VERSION)
            body.setdefault("lifecycle", "experimental")  # lowest real tier; the gate keeps it on promote
            if c.source.get("license"):
                body.setdefault("license", c.source["license"])
            body.setdefault("created", self._now)
            body["updated"] = self._now

            # hashes (formatting-invariant) — kept on the Candidate, NOT in the body
            c.body = body
            c.component_id = cid
            c.content_hash = content_hash(body)
            c.version_hash = version_hash(body)

            # canonical schema validation
            ok, errors = schema_valid(body)
            if not ok:
                c.drop(self.name, "schema-invalid: " + (errors[0] if errors else "unknown"))
                continue
            c.mark(self.name, "standardized", cid)
        return batch


# --------------------------------------------------------------------------- #
# self-test (offline)
# --------------------------------------------------------------------------- #
def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    body = {
        "id": "knowledge-pack/x", "type": "knowledge-pack", "version": "0.1.0",
        "name": "CSDDD article corpus", "description": "Reference extracts of CSDDD articles.",
        "created": "2026-01-01", "updated": "2026-01-01",
    }

    # formatting invariance
    reordered = {k: body[k] for k in reversed(list(body))}
    check("content_hash key-order invariant", content_hash(body) == content_hash(reordered))
    restamped = dict(body, updated="2026-05-28", created="2026-05-28")
    check("content_hash timestamp invariant", content_hash(body) == content_hash(restamped))
    check("version_hash timestamp invariant", version_hash(body) == version_hash(restamped))
    # substance change detected
    changed = dict(body, description="A different, expanded description of the corpus content.")
    check("content_hash detects substance change", content_hash(body) != content_hash(changed))
    # version bump: same content, new version → same content_hash, different version_hash
    bumped = dict(body, version="0.2.0")
    check("version bump keeps content_hash", content_hash(body) == content_hash(bumped))
    check("version bump moves version_hash", version_hash(body) != version_hash(bumped))

    # canonical id: stable + idempotent + collision-safe
    src = {"source_url": "https://eur-lex.europa.eu/csddd"}
    id1 = canonical_id("knowledge-pack", "CSDDD article corpus", src)
    id2 = canonical_id("knowledge-pack", "CSDDD article corpus", src)
    check("canonical id idempotent for same source", id1 == id2, f"{id1} vs {id2}")
    id_other_src = canonical_id("knowledge-pack", "CSDDD article corpus",
                                {"source_url": "https://example.org/other"})
    check("same slug + different source ⇒ different id", id1 != id_other_src)
    check("id has type prefix + hash suffix", id1.startswith("knowledge-pack/") and re.search(r"-[0-9a-f]{8}$", id1) is not None, id1)
    check("slug length capped", len(id1.split("/", 1)[1]) <= _SLUG_MAX)

    # schema validation MECHANISM: a junk body fails, a known-good catalog body passes
    ok_bad, errs_bad = schema_valid({"type": "knowledge-pack", "id": "knowledge-pack/junk"})
    check("schema validation catches an invalid body", not ok_bad and bool(errs_bad), str(errs_bad))
    ok_unknown, _ = schema_valid({"type": "capability-request"})
    check("no schema for non-component type", not ok_unknown)

    # validate against a REAL catalog manifest to prove we reuse the canonical schemas.
    # Database rows are preferred; YAML is retained as local seed/export fallback.
    sample_path, sample_body, sample_source = sample_manifest_for_schema_validation()
    sample = (sample_path, sample_body) if sample_body else None
    if sample:
        ok_real, errs_real = schema_valid(sample[1])
        sample_name = sample[0].name if isinstance(sample[0], Path) else str(sample[0])
        check(f"real {sample_source} {sample[1]['type']} validates ({sample_name})", ok_real, str(errs_real))
    else:
        print("  [skip] no committed manifest found to validate against")

    # the stage: a schema-valid body standardizes; a junk body is culled
    valid_body = dict(sample[1]) if sample else None
    junk = Candidate(target_type="knowledge-pack", body={"description": "no required fields"},
                     source={"source_url": "https://x.example/y", "author": "a", "license": "MIT"})
    ctx = FoundryContext()
    batch = [junk] + ([Candidate(target_type=valid_body["type"], body=dict(valid_body),
                                 source={"source_url": "https://x.example/real", "author": "a", "license": "MIT"})]
                      if valid_body else [])
    StandardizeStage(now_s=0).run(batch, ctx)
    check("junk body culled by schema", not junk.alive and any("schema-invalid" in r for r in junk.reasons), str(junk.reasons))
    if valid_body:
        good = batch[1]
        check("valid body standardized (alive + id + hashes)",
              good.alive and good.component_id and good.content_hash and good.version_hash, good.short())
        check("stage set canonical id with suffix", re.search(r"-[0-9a-f]{8}$", good.component_id) is not None, good.component_id)

    print(f"\n{'all standardize self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
