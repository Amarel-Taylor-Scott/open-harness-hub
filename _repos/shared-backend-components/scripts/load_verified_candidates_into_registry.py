#!/usr/bin/env python3
"""scripts.load_verified_candidates_into_registry — THE bridge that makes verified factory primitives usable.

The factory generates + verifies primitive candidates into
``data/dev-intel/primitive_factory/verified_candidates/<label>/verified_candidates.jsonl`` (tens of thousands of
rows). AIDevObserver's registry search (``_repos/teleon/backend/src/teleon/observer/registry_search.py``) reads a FIXED set of
edge-foundry card files — it never saw the verified factory output, so every ultracode/Ollama-fleet row sat in a
silo the product could not consume. This loader closes that gap deterministically: it maps every verified candidate
into the edge-foundry card schema and writes them to ONE registered consumable file
(``verified_factory_primitive_cards.jsonl``, wired into ``_edge_foundry_paths()``), so the rows become searchable
the moment this runs.

Discipline: offline + deterministic (ids/digests from content hashes, ``generated_at`` copied from each row's
``verified_at`` — never wall-clock); every emitted card stays ``candidate=true`` / ``serves_truth=false`` with
``trust="candidate"``; cards carry NO local filesystem paths (source refs are the public doc URLs the candidate
declared) and default to ``surface_visibility=private_internal_only`` (searchable in local/all scope, never
overclaimed on a public demo). Counts are computed into the manifest, never typed.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

VERIFIED_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "verified_candidates"
#: single registered consumable output — MUST match the path added to settings.py
#: (DEFAULT_VERIFIED_FACTORY_CARDS_PATH) and read by registry_search._verified_factory_cards_path().
OUTPUT_PATH = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "verified_factory_primitive_cards.jsonl"
MANIFEST_PATH = OUTPUT_PATH.with_name("verified_factory_primitive_cards_manifest.json")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False, "trust": "candidate"}
#: unverified model drafts → searchable in local/all scope, never surfaced as public-demo-safe (honest default).
DEFAULT_VISIBILITY = "private_internal_only"
CARD_ID_PREFIX = "prim:vf:"  # verified-factory namespace, globally unique by content hash
MAX_BLOCKING_KEYS = 24
_WORD_RE = re.compile(r"[a-z0-9]+")


def _digest(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()


def _tokens(*texts: str) -> list[str]:
    seen: list[str] = []
    for text in texts:
        for tok in _WORD_RE.findall(str(text).lower()):
            if len(tok) >= 3 and tok not in seen:
                seen.append(tok)
    return seen


def _domain_of(primitive_kind: str, dedupe_key: str) -> str:
    """First segment of the family string (e.g. 'packaging.oci_image' -> 'packaging')."""
    base = str(primitive_kind or "").strip() or str(dedupe_key or "")
    head = re.split(r"[.:/>+]", base, maxsplit=1)[0].strip()
    return head or "general"


def _quality_score(row: dict[str, Any]) -> int:
    """Deterministic completeness score 0-100 — richer contracts rank higher. No wall-clock, no randomness."""
    score = 40
    kind = row.get("kind")
    group = row.get("group_contract") if isinstance(row.get("group_contract"), dict) else {}
    hidden = group.get("hidden_member_edges") if isinstance(group, dict) else None
    if kind == "primitive_group" and isinstance(hidden, list):
        score += min(len(hidden), 6) * 3  # up to +18 for deep hidden routes
    proofs = row.get("proof_requirements")
    if isinstance(proofs, list):
        score += min(len(proofs), 6) * 2  # up to +12
    for field in ("input_edge_description", "output_edge_description"):
        if len(str(row.get(field) or "")) >= 300:
            score += 6
    if isinstance(row.get("reuse_profile"), dict):
        score += 6
    refs = row.get("source_refs")
    if isinstance(refs, list) and refs:
        score += 6
    if isinstance(row.get("edge_contract"), dict):
        score += 6
    return max(0, min(score, 100))


def _public_source_refs(row: dict[str, Any]) -> list[dict[str, str]]:
    """Only the public https doc refs the candidate declared — never a local path."""
    out: list[dict[str, str]] = []
    for ref in row.get("source_refs") or []:
        if not isinstance(ref, dict):
            continue
        url = str(ref.get("url") or "")
        if url.startswith("https://"):
            out.append({"label": str(ref.get("label") or "source"), "url": url})
    return out


def map_row(row: dict[str, Any], *, label: str, visibility: str) -> dict[str, Any] | None:
    """Map ONE verified candidate to an edge-foundry consumable card, or None if unmappable."""
    kind = row.get("kind")
    input_edge = str(row.get("input_edge") or "").strip()
    output_edge = str(row.get("output_edge") or "").strip()
    origin_id = str(row.get("primitive_id") or "").strip()
    dedupe_key = str(row.get("dedupe_key") or "").strip()
    if kind not in {"primitive", "primitive_group"} or not input_edge or not output_edge or not origin_id:
        return None

    primitive_kind = str(row.get("primitive_kind") or "")
    domain = _domain_of(primitive_kind, dedupe_key)
    source_family = "claude_fable_ultracode" if row.get("source_model") == "claude-fable-5" else (
        str(row.get("source_provider") or "model_generated").replace("/", "_")
    )
    refs = _public_source_refs(row)
    # globally unique + deterministic: label + origin id + dedupe key -> stable across re-runs, no cross-day collision.
    card_id = CARD_ID_PREFIX + _digest(label, origin_id, dedupe_key)[:20]
    slug = ".".join(_tokens(origin_id or dedupe_key)[:8]) or _digest(label, origin_id)[:12]

    card: dict[str, Any] = {
        "primitive_id": card_id,
        "origin_primitive_id": origin_id,
        "source_verification_label": label,
        "kind": "artifact.primitive_group" if kind == "primitive_group" else "route.primitive",
        "primitive_kind": primitive_kind,
        "title": str(row.get("title") or origin_id),
        "input_edge": input_edge,
        "output_edge": output_edge,
        "blackbox": row.get("blackbox") if isinstance(row.get("blackbox"), str) else (
            (row.get("contract") or {}).get("summary") if isinstance(row.get("contract"), dict) else ""
        ) or "",
        "contract": row.get("contract") if isinstance(row.get("contract"), dict) else {},
        "edge_contract": row.get("edge_contract") if isinstance(row.get("edge_contract"), dict) else {},
        "effects": row.get("effects") if isinstance(row.get("effects"), list) else [],
        "mutations": row.get("mutators") if isinstance(row.get("mutators"), list) else [],
        "runtime_targets": (
            (row.get("reuse_profile") or {}).get("implementation_surfaces")
            if isinstance(row.get("reuse_profile"), dict)
            and isinstance((row.get("reuse_profile") or {}).get("implementation_surfaces"), list)
            else ["python_function"]
        ),
        "proof_requirements": row.get("proof_requirements") if isinstance(row.get("proof_requirements"), list) else [],
        "promotion_blockers": row.get("promotion_blockers") if isinstance(row.get("promotion_blockers"), list) else [],
        "capability_tags": [domain],
        "domains": [domain],
        "blocking_keys": _tokens(row.get("title"), input_edge, output_edge, primitive_kind)[:MAX_BLOCKING_KEYS],
        "slug": slug,
        "source_family": source_family,
        # source_ref is a DICT (the search text reader calls .get("path")/.get("name")); we carry the public
        # doc url + a name, and NO local filesystem path (name is the model-drafted title, not a repo path).
        "source_ref": {
            "url": refs[0]["url"] if refs else "",
            "name": str(row.get("title") or origin_id),
            "path": "",
        },
        "source_refs": refs,
        "source_evidence_status": "source_ref_candidate",  # refs declared, not live-verified — honest
        "source_digest": _digest(*(r["url"] for r in refs))[:24] if refs else _digest(origin_id)[:24],
        "readiness": "R3_contract_known" if isinstance(row.get("edge_contract"), dict) else "R2_edge_known",
        "quality_score": _quality_score(row),
        "surface_visibility": visibility,
        "verification_level": str(row.get("verification_level") or ""),
        "generated_at": str(row.get("verified_at") or ""),  # copied, never wall-clock
        "cache": {},
        "memory": {},
        **BOUNDARY,
    }
    return card


def build_cards(*, visibility: str = DEFAULT_VISIBILITY) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read every verified_candidates label and map to deduped consumable cards. Returns (cards, stats)."""
    seen_ids: set[str] = set()
    seen_dedupe: set[str] = set()
    cards: list[dict[str, Any]] = []
    labels_read = 0
    rows_in = 0
    skipped_unmappable = 0
    collapsed_dupes = 0

    label_dirs = sorted(p for p in VERIFIED_ROOT.glob("*") if p.is_dir())
    for label_dir in label_dirs:
        f = label_dir / "verified_candidates.jsonl"
        if not f.exists():
            continue
        labels_read += 1
        label = label_dir.name
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rows_in += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                skipped_unmappable += 1
                continue
            if not isinstance(row, dict):
                skipped_unmappable += 1
                continue
            # collapse cross-lane duplicates by (kind, input_edge, output_edge, dedupe_key)
            edge_key = "::".join([
                str(row.get("kind")), str(row.get("input_edge")),
                str(row.get("output_edge")), str(row.get("dedupe_key")),
            ]).lower()
            if edge_key in seen_dedupe:
                collapsed_dupes += 1
                continue
            card = map_row(row, label=label, visibility=visibility)
            if card is None:
                skipped_unmappable += 1
                continue
            if card["primitive_id"] in seen_ids:
                collapsed_dupes += 1
                continue
            seen_dedupe.add(edge_key)
            seen_ids.add(card["primitive_id"])
            cards.append(card)

    cards.sort(key=lambda c: c["primitive_id"])  # deterministic order
    stats = {
        "record_type": "verified_factory_primitive_cards_manifest",
        "labels_read": labels_read,
        "rows_in": rows_in,
        "cards_out": len(cards),
        "collapsed_duplicates": collapsed_dupes,
        "skipped_unmappable": skipped_unmappable,
        "groups": sum(1 for c in cards if c["kind"] == "artifact.primitive_group"),
        "primitives": sum(1 for c in cards if c["kind"] == "route.primitive"),
        "surface_visibility": visibility,
        "content_sha256": hashlib.sha256(
            "\n".join(json.dumps(c, sort_keys=True, ensure_ascii=False) for c in cards).encode("utf-8")
        ).hexdigest(),
        "candidate": True,
        "serves_truth": False,
    }
    return cards, stats


def write_pack(cards: list[dict[str, Any]], stats: dict[str, Any]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        for card in cards:
            fh.write(json.dumps(card, ensure_ascii=False, sort_keys=True) + "\n")
    MANIFEST_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def self_test() -> int:
    sample = {
        "kind": "primitive_group",
        "primitive_id": "prim:uc3:catalog-ai-agent-rag:001",
        "dedupe_key": "documentbatch->normalizeddocumentset::normalize",
        "title": "Document normalization group",
        "input_edge": "DocumentBatch",
        "output_edge": "NormalizedDocumentSet+ContentHashManifest",
        "input_edge_description": "x" * 320,
        "output_edge_description": "y" * 320,
        "blackbox": "Normalizes and fingerprints documents.",
        "contract": {"summary": "s", "input": {}, "output": {}, "errors": []},
        "edge_contract": {"preconditions": [], "postconditions": []},
        "group_contract": {"hidden_member_edges": ["a->b", "b->c", "c->d"]},
        "effects": [{"type": "compute", "description": "local"}],
        "mutators": ["field_rename"],
        "proof_requirements": ["golden fixture", "candidate_boundary_gate"],
        "reuse_profile": {"implementation_surfaces": ["python", "typescript"]},
        "source_refs": [{"label": "hf", "url": "https://huggingface.co/docs"}],
        "source_model": "claude-fable-5",
        "primitive_kind": "pipeline.member_step",
        "verified_at": "2026-07-02T00:00:00Z",
        "verification_level": "L3_shape_source_proof_deduped",
    }
    card = map_row(sample, label="2026-07-02-uc03", visibility=DEFAULT_VISIBILITY)
    checks = [
        ("maps to a card", card is not None),
        ("id is verified-factory namespaced", card and card["primitive_id"].startswith(CARD_ID_PREFIX)),
        ("id is deterministic", card and card["primitive_id"] == map_row(sample, label="2026-07-02-uc03", visibility=DEFAULT_VISIBILITY)["primitive_id"]),
        ("candidate boundary held", card and card["candidate"] is True and card["serves_truth"] is False and card["trust"] == "candidate"),
        ("no local path leaked", card and "batch_runs" not in json.dumps(card) and "/home/" not in json.dumps(card)),
        ("source_ref is a dict with path/name/url (search reader calls .get)",
         card and isinstance(card["source_ref"], dict)
         and set(card["source_ref"]) >= {"path", "name", "url"} and card["source_ref"]["path"] == ""),
        ("public https source ref carried", card and card["source_ref"]["url"].startswith("https://")),
        ("blocking keys derived", card and len(card["blocking_keys"]) >= 3),
        ("generated_at copied not wall-clock", card and card["generated_at"] == "2026-07-02T00:00:00Z"),
        ("group kind mapped", card and card["kind"] == "artifact.primitive_group"),
        ("quality score in range", card and 0 <= card["quality_score"] <= 100),
        ("visibility is private_internal_only", card and card["surface_visibility"] == DEFAULT_VISIBILITY),
        ("unmappable row rejected", map_row({"kind": "junk"}, label="x", visibility=DEFAULT_VISIBILITY) is None),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        print("FAIL - load_verified_candidates_into_registry:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - load_verified_candidates_into_registry: verified candidate -> edge-foundry card mapping "
          "(deterministic ids, boundary held, no local-path leak, public refs only, blocking keys derived).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run the in-memory mapping self-test only")
    parser.add_argument("--write", action="store_true", help="build cards from verified_candidates/* and write the pack")
    parser.add_argument("--visibility", default=DEFAULT_VISIBILITY,
                        help="surface_visibility for emitted cards (default private_internal_only)")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    cards, stats = build_cards(visibility=args.visibility)
    if args.write:
        write_pack(cards, stats)
    print(json.dumps({k: v for k, v in stats.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
