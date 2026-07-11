#!/usr/bin/env python3
"""Build AIDevObserver primitive cards from primitive-kind family seeds."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_MANIFEST_PATH,
    AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_PATH,
    AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_PATH,
    AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_EVIDENCE_STATUS,
    AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_FAMILY,
    REPO_ROOT,
)

CATALOG_PATH = _resource(AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_PATH)
OUT_PATH = _resource(AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_MANIFEST_PATH)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: Any, *, n: int = 16) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()[:n]


def _slug(value: str) -> str:
    out = []
    prev_dash = False
    for char in value.lower():
        if char.isalnum():
            out.append(char)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-") or "primitive-kind"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(value)
    return rows


def _tokens(*values: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = _canon(value) if isinstance(value, (dict, list)) else str(value or "")
        chars: list[str] = []
        for char in text.lower():
            if char.isalnum():
                chars.append(char)
            elif chars:
                word = "".join(chars)
                chars.clear()
                if len(word) > 1 and word not in seen:
                    seen.add(word)
                    out.append(word)
        if chars:
            word = "".join(chars)
            if len(word) > 1 and word not in seen:
                seen.add(word)
                out.append(word)
    return out


def _mutation_option(row: dict[str, Any], mutator: str) -> dict[str, Any]:
    input_edge = str(row["input_edge"])
    output_edge = str(row["output_edge"])
    return {
        "mutator": mutator,
        "mutator_agent_id": f"mut:deterministic:{mutator}@1",
        "reason": f"Adapt the {row['primitive_kind']} contract without rebuilding core behavior.",
        "input_edge_before": input_edge,
        "output_edge_before": output_edge,
        "target_edge_template": {
            "input": input_edge,
            "output": output_edge,
            "mutation": mutator,
        },
        "effect_delta": "preserve_or_declare_adapter_delta",
        "preconditions": [
            "visible_edge_declared",
            "hidden_member_edges_declared",
            "effects_declared",
        ],
        "proof_obligations": row.get("proof_requirements") or [],
        "runtime_targets": row.get("runtime_targets") or [],
        "candidate": True,
        "serves_truth": False,
    }


def _quality_score(row: dict[str, Any]) -> int:
    return min(
        95,
        72
        + len(row.get("hidden_member_edges") or [])
        + len(row.get("proof_requirements") or [])
        + len(row.get("adapter_mutators") or []),
    )


def _card(row: dict[str, Any]) -> dict[str, Any]:
    primitive_kind = str(row["primitive_kind"])
    input_edge = str(row["input_edge"])
    output_edge = str(row["output_edge"])
    mutations = [_mutation_option(row, str(mutator)) for mutator in row.get("adapter_mutators") or []]
    source_ref = {
        "path": AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_PATH,
        "name": primitive_kind,
        "family_id": row.get("id"),
    }
    contract = {"input": input_edge, "output": output_edge}
    return {
        "primitive_id": f"pk:aidevexplorer.primitive_kind.{primitive_kind}@candidate",
        "kind": primitive_kind,
        "slug": f"aidevexplorer-primitive-kind-{_slug(primitive_kind)}",
        "title": row.get("title") or primitive_kind,
        "label": primitive_kind,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "contract": contract,
        "group_contract": {
            "visible_input_edge": input_edge,
            "visible_output_edge": output_edge,
            "hidden_member_edges": row.get("hidden_member_edges") or [],
            "llm_context_policy": "show_visible_edge_first; reveal hidden member edges only for route proof",
        },
        "blackbox": {
            "does": (
                f"Represent the reusable {primitive_kind} primitive family by visible edge "
                f"`{row['visible_edge']}` with effects, adapters, and proof gates attached."
            ),
            "llm_context_policy": "compact family card first; expand hidden member edges only on drilldown",
        },
        "effects": row.get("effects") or [],
        "memory": "artifact",
        "cache": "contract_hash",
        "runtime_targets": row.get("runtime_targets") or [],
        "adapter_mutators": row.get("adapter_mutators") or [],
        "mutations": mutations,
        "edge_mutation_options": mutations,
        "proof_requirements": row.get("proof_requirements") or [],
        "promotion_blockers": [
            "implementation_binding_required",
            "source_backing_required_before_promotion",
            "proof_bundle_required",
        ],
        "blocking_keys": _tokens(
            primitive_kind,
            row.get("title"),
            row.get("visible_edge"),
            row.get("hidden_member_edges"),
            row.get("effects"),
            row.get("adapter_mutators"),
            row.get("proof_requirements"),
            row.get("common_pitfalls"),
            row.get("example_tasks"),
            row.get("domains"),
        ),
        "capability_tags": ["primitive_kind_family", primitive_kind, *(row.get("domains") or [])],
        "domains": row.get("domains") or [],
        "common_pitfalls": row.get("common_pitfalls") or [],
        "example_tasks": row.get("example_tasks") or [],
        "source_ref": source_ref,
        "source_family": AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_FAMILY,
        "source_evidence_status": AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_EVIDENCE_STATUS,
        "source_digest": _sha({"source_ref": source_ref, "contract": contract}, n=24),
        "surface_visibility": "public_demo_safe_candidate",
        "readiness": "R2_primitive_kind_family_candidate",
        "trust": "candidate",
        "quality_score": _quality_score(row),
        "generated_at": _utc(),
        "candidate": True,
        "serves_truth": False,
    }


def build_cards(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = [_card(row) for row in rows]
    cards.sort(key=lambda row: str(row["primitive_id"]))
    return cards


def write_cards(cards: list[dict[str, Any]]) -> dict[str, Any]:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        "".join(json.dumps(card, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for card in cards),
        encoding="utf-8",
    )
    by_domain: dict[str, int] = {}
    for card in cards:
        for domain in card.get("domains") or []:
            by_domain[str(domain)] = by_domain.get(str(domain), 0) + 1
    manifest = {
        "record_type": "aidevexplorer_primitive_kind_cards_manifest",
        "created_at": _utc(),
        "family_catalog_path": AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_PATH,
        "cards_path": AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_PATH,
        "row_count": len(cards),
        "primitive_kinds": [card["kind"] for card in cards],
        "domain_counts": dict(sorted(by_domain.items())),
        "source_family": AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_FAMILY,
        "source_evidence_status": AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_EVIDENCE_STATUS,
        "candidate": True,
        "serves_truth": False,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = _read_jsonl(CATALOG_PATH)
        cards = build_cards(rows)
        if len(cards) != len(rows):
            raise AssertionError("card count must match family row count")
        manifest: dict[str, Any] = {
            "row_count": len(cards),
            "would_write": AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_PATH,
            "candidate": True,
            "serves_truth": False,
        }
        if not args.check_only:
            manifest = write_cards(cards)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
