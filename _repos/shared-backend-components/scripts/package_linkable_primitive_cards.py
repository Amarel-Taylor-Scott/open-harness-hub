#!/usr/bin/env python3
"""Package verified primitive candidates into linkable primitive cards.

Verified L3 rows prove shape, source refs, and basic proof obligations. This
stage adds model-facing edge packaging so builders can retrieve one compact card
and wire code without spending generation tokens rediscovering the contract.
Cards remain candidate-only and never serve truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402
from scripts.verify_primitive_candidates import (  # noqa: E402
    _source_urls,
    _valid_public_source_url,
)

VERIFIED_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "verified_candidates"
PACKAGE_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "linkable_cards"
HIGH_LEVERAGE_EDGE_DESC_CHARS = 600
GROUP_LIKE_MIN_HIDDEN_EDGES = 3
HIGH_LEVERAGE_GROUP_HIDDEN_EDGES = 5
HIGH_LEVERAGE_SAVED_OUTPUT_TOKENS = 1500
MEDIUM_LEVERAGE_SAVED_OUTPUT_TOKENS = 800
CODING_SURFACE_TERMS = (
    "api",
    "async",
    "cache",
    "cli",
    "code",
    "contract",
    "database",
    "endpoint",
    "function",
    "http",
    "idempot",
    "json",
    "migration",
    "openapi",
    "pagination",
    "python",
    "retry",
    "schema",
    "sdk",
    "sql",
    "test",
    "typescript",
    "validation",
    "webhook",
    "worker",
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def _sha(value: Any, *, n: int = 20) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:n]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(row)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _append_index(indexes: dict[str, list[dict[str, Any]]], name: str, row: dict[str, Any]) -> None:
    indexes.setdefault(name, []).append(row)


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, "", {}, []):
        return []
    return [value]


def _approx_tokens(value: Any) -> int:
    text = _text(value, limit=50000)
    return max(1, (len(text) + 3) // 4) if text else 0


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _text(value: Any, *, limit: int = 1800) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    text = " ".join(text.replace("\n", " ").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _contract_part(row: dict[str, Any], key: str) -> Any:
    contract = row.get("contract") if isinstance(row.get("contract"), dict) else {}
    return contract.get(key)


def _edge_components(edge: Any) -> list[str]:
    text = str(edge or "")
    parts = [part.strip() for part in re.split(r"[+|,]", text) if part.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def _type_name(value: Any) -> str:
    text = re.sub(r"[^0-9A-Za-z_]+", " ", str(value or "")).strip()
    if not text:
        return "UnknownEdge"
    return "".join(part[:1].upper() + part[1:] for part in text.split())


def _derived_contract(edge: Any, *, side: str) -> dict[str, Any]:
    components = _edge_components(edge)
    direction = "input envelope" if side == "input" else "output envelope"
    return {
        "edge": edge,
        "shape": direction,
        "components": components,
        "python_type_hint": _type_name(edge),
        "typescript_type_hint": _type_name(edge),
        "serialization": "json_object_or_typed_dataclass",
        "notes": [
            "Derived from edge name because the source candidate did not declare a full schema.",
            "Treat each component as a named field or nested object until a stricter schema is promoted.",
        ],
        "candidate": True,
        "serves_truth": False,
    }


def _edge_description(row: dict[str, Any], *, side: str) -> str:
    field = f"{side}_edge_description"
    if isinstance(row.get(field), str) and row[field].strip():
        return _text(row[field], limit=1200)
    edge = str(row.get(f"{side}_edge") or "").strip()
    contract_key = "input" if side == "input" else "output"
    contract_value = _contract_part(row, contract_key) or _derived_contract(edge, side=side)
    summary = _contract_part(row, "summary")
    blackbox = row.get("blackbox")
    mutators = row.get("mutators")
    proofs = row.get("proof_requirements")
    effects = row.get("effects")
    direction = "Consumes" if side == "input" else "Produces"
    role = "caller must provide" if side == "input" else "caller can rely on receiving"
    edge_specific = (
        "Before calling, bind this edge through declared mutators and validate preconditions."
        if side == "input"
        else "After calling, validate the output contract, proof receipt, and declared failure envelope before linking downstream."
    )
    return (
        f"{direction} `{edge}`. The {role} data matching this contract fragment: "
        f"{_text(contract_value, limit=900)}. "
        f"Route purpose: {_text(summary, limit=350)}. "
        f"Blackbox behavior: {_text(blackbox, limit=350)}. "
        f"Declared effects: {_text(effects, limit=260)}. "
        f"Reusable mutators: {_text(mutators, limit=220)}. "
        f"Proof gates: {_text(proofs, limit=260)}. "
        f"{edge_specific} "
        "Adapters should preserve field names, declared types, source evidence, receipt identifiers, and error-envelope semantics unless an explicit mutator is attached."
    )


def _hidden_edges(row: dict[str, Any]) -> list[Any]:
    group_contract = row.get("group_contract") if isinstance(row.get("group_contract"), dict) else {}
    hidden = _as_list(group_contract.get("hidden_member_edges"))
    if not hidden:
        hidden = _as_list(row.get("hidden_member_edges"))
    return hidden


def _public_source_refs(row: dict[str, Any]) -> list[str]:
    return [url for url in _source_urls(row.get("source_refs")) if _valid_public_source_url(url)]


def _side_effect_class(row: dict[str, Any]) -> str:
    text = _text(row.get("effects"), limit=1200).lower()
    if any(term in text for term in ("write", "mutat", "delete", "persist", "send", "network_io")):
        return "effectful"
    if any(term in text for term in ("network", "api", "http", "quota")):
        return "network_read"
    return "pure_or_local_compute"


def _composition_hints(row: dict[str, Any]) -> dict[str, Any]:
    mutators = [str(value) for value in _as_list(row.get("mutators"))]
    proofs = [str(value) for value in _as_list(row.get("proof_requirements"))]
    return {
        "route_signature": f"{row.get('input_edge')} -> {row.get('output_edge')}",
        "consumes_edge": row.get("input_edge"),
        "produces_edge": row.get("output_edge"),
        "adapter_mutators": mutators,
        "proofs_to_run_before_linking": proofs,
        "side_effect_class": _side_effect_class(row),
        "idempotency_hint": "requires_receipt_or_key" if "idempot" in _text(row, limit=3000).lower() else "not_declared",
        "group_expansion_policy": (
            "show_visible_edge_first_expand_hidden_edges_only_for_debug"
            if row.get("kind") == "primitive_group"
            else "single_edge_primitive"
        ),
        "candidate_only": True,
        "serves_truth": False,
    }


def _declared_reuse_profile(row: dict[str, Any]) -> dict[str, Any]:
    profile = row.get("reuse_profile")
    return profile if isinstance(profile, dict) else {}


def _coding_terms(row: dict[str, Any]) -> list[str]:
    blob = " ".join([
        _text(row.get("title"), limit=400),
        _text(row.get("input_edge"), limit=400),
        _text(row.get("output_edge"), limit=400),
        _text(row.get("contract"), limit=2000),
        _text(row.get("blackbox"), limit=1000),
        _text(row.get("mutators"), limit=1000),
        _text(row.get("proof_requirements"), limit=1000),
    ]).lower()
    return [term for term in CODING_SURFACE_TERMS if term in blob]


def _reuse_class(row: dict[str, Any], hidden_edge_count: int, coding_terms: list[str], edge_desc_chars: int) -> str:
    declared = str(_declared_reuse_profile(row).get("reuse_class") or "").strip()
    if declared:
        return declared
    if row.get("kind") == "primitive_group" and coding_terms:
        return "multistep_coding_group"
    if row.get("kind") == "primitive_group":
        return "workflow_route_group"
    if hidden_edge_count >= HIGH_LEVERAGE_GROUP_HIDDEN_EDGES:
        return "workflow_route_group"
    if len(_as_list(row.get("mutators"))) >= 3:
        return "adapter_mutator_chain"
    if edge_desc_chars >= HIGH_LEVERAGE_EDGE_DESC_CHARS:
        return "long_edge_contract"
    return "atomic_edge_card"


def _leverage_profile(
    row: dict[str, Any],
    *,
    input_desc: str,
    output_desc: str,
    hidden_edges: list[Any],
    packaged_edge_contract: dict[str, Any],
) -> dict[str, Any]:
    reuse_profile = _declared_reuse_profile(row)
    edge_desc_chars = len(input_desc) + len(output_desc)
    hidden_edge_count = len(_as_list(hidden_edges))
    proof_count = len(_as_list(row.get("proof_requirements")))
    mutator_count = len(_as_list(row.get("mutators")))
    public_source_ref_count = len(_public_source_refs(row))
    contract_chars = len(_text(row.get("contract"), limit=20000))
    terms = _coding_terms(row)
    declared_saved = _int_or_zero(reuse_profile.get("estimated_saved_output_tokens"))
    output_from_scratch_estimate = (
        650
        + hidden_edge_count * 260
        + proof_count * 90
        + mutator_count * 75
        + edge_desc_chars // 7
        + contract_chars // 14
        + (450 if row.get("kind") == "primitive_group" else 0)
        + (350 if terms else 0)
    )
    estimated_saved_output_tokens = max(declared_saved, output_from_scratch_estimate)
    retrieval_context_tokens = _approx_tokens({
        "visible_edge": f"{row.get('input_edge')} -> {row.get('output_edge')}",
        "edge_contract": packaged_edge_contract,
        "hidden_member_edges": hidden_edges if row.get("kind") == "primitive_group" else [],
        "proof_requirements": row.get("proof_requirements"),
    })
    score = min(
        1000,
        hidden_edge_count * 80
        + proof_count * 30
        + mutator_count * 25
        + edge_desc_chars // 6
        + contract_chars // 20
        + (200 if row.get("kind") == "primitive_group" else 0)
        + (150 if terms else 0)
        + min(120, public_source_ref_count * 30),
    )
    reuse_class = _reuse_class(row, hidden_edge_count, terms, edge_desc_chars)
    if (
        estimated_saved_output_tokens >= HIGH_LEVERAGE_SAVED_OUTPUT_TOKENS
        and (hidden_edge_count >= HIGH_LEVERAGE_GROUP_HIDDEN_EDGES or edge_desc_chars >= HIGH_LEVERAGE_EDGE_DESC_CHARS)
    ):
        tier = "high"
    elif (
        estimated_saved_output_tokens >= MEDIUM_LEVERAGE_SAVED_OUTPUT_TOKENS
        or hidden_edge_count >= GROUP_LIKE_MIN_HIDDEN_EDGES
        or edge_desc_chars >= HIGH_LEVERAGE_EDGE_DESC_CHARS
    ):
        tier = "medium"
    else:
        tier = "basic"
    quality_gaps: list[str] = []
    if edge_desc_chars < HIGH_LEVERAGE_EDGE_DESC_CHARS:
        quality_gaps.append("short_edge_descriptions")
    if row.get("kind") == "primitive_group" and hidden_edge_count < HIGH_LEVERAGE_GROUP_HIDDEN_EDGES:
        quality_gaps.append("group_hidden_edges_below_high_leverage_target")
    if not reuse_profile:
        quality_gaps.append("reuse_profile_missing")
    return {
        "leverage_tier": tier,
        "reuse_class": reuse_class,
        "score": score,
        "estimated_saved_output_tokens": estimated_saved_output_tokens,
        "estimated_retrieval_context_tokens": retrieval_context_tokens,
        "edge_description_chars": edge_desc_chars,
        "input_edge_description_chars": len(input_desc),
        "output_edge_description_chars": len(output_desc),
        "hidden_member_edge_count": hidden_edge_count,
        "proof_requirement_count": proof_count,
        "mutator_count": mutator_count,
        "contract_chars": contract_chars,
        "public_source_ref_count": public_source_ref_count,
        "coding_surface_terms": terms,
        "quality_gaps": quality_gaps,
        "candidate": True,
        "serves_truth": False,
    }


def package_row(row: dict[str, Any], *, run_date: str) -> dict[str, Any]:
    input_desc = _edge_description(row, side="input")
    output_desc = _edge_description(row, side="output")
    hidden_edges = _hidden_edges(row)
    public_refs = _public_source_refs(row)
    edge_contract = row.get("edge_contract") if isinstance(row.get("edge_contract"), dict) else {}
    input_contract = _contract_part(row, "input") or _derived_contract(row.get("input_edge"), side="input")
    output_contract = _contract_part(row, "output") or _derived_contract(row.get("output_edge"), side="output")
    packaged_edge_contract = {
        "input_edge": row.get("input_edge"),
        "input_edge_description": input_desc,
        "input_contract": input_contract,
        "output_edge": row.get("output_edge"),
        "output_edge_description": output_desc,
        "output_contract": output_contract,
        "compile_binding": {
            "python_input_type": _type_name(row.get("input_edge")),
            "python_output_type": _type_name(row.get("output_edge")),
            "typescript_input_type": _type_name(row.get("input_edge")),
            "typescript_output_type": _type_name(row.get("output_edge")),
            "function_shape": f"({row.get('input_edge')}) -> {row.get('output_edge')}",
            "adapter_policy": "use declared mutators before generating custom glue",
            "candidate": True,
            "serves_truth": False,
        },
        "preconditions": edge_contract.get("preconditions") or ["input matches input_contract", "source refs remain reviewable"],
        "postconditions": edge_contract.get("postconditions") or ["output matches output_contract", "errors follow declared envelope"],
        "failure_modes": edge_contract.get("failure_modes") or _contract_part(row, "errors") or [],
        "composition_notes": edge_contract.get("composition_notes") or [
            "Use mutators to adapt nearby shapes instead of asking a model to rewrite glue code.",
            "Link by visible input/output edge first; inspect hidden member edges only when validating a primitive group route.",
        ],
        "candidate": True,
        "serves_truth": False,
    }
    leverage_profile = _leverage_profile(
        row,
        input_desc=input_desc,
        output_desc=output_desc,
        hidden_edges=hidden_edges,
        packaged_edge_contract=packaged_edge_contract,
    )
    embedding_text = " ".join([
        str(row.get("title") or ""),
        str(row.get("primitive_id") or ""),
        str(row.get("kind") or ""),
        f"Visible edge: {row.get('input_edge')} to {row.get('output_edge')}.",
        input_desc,
        output_desc,
        f"Contract: {_text(row.get('contract'), limit=1600)}.",
        f"Blackbox behavior: {_text(row.get('blackbox'), limit=800)}.",
        f"Effects: {_text(row.get('effects'), limit=800)}.",
        f"Mutators: {_text(row.get('mutators'), limit=700)}.",
        f"Proofs: {_text(row.get('proof_requirements'), limit=900)}.",
        f"Source refs: {' '.join(public_refs)}.",
    ])
    return {
        "record_type": "linkable_primitive_card",
        "card_id": f"lpc:{_sha({'primitive_id': row.get('primitive_id'), 'verification_id': row.get('verification_id'), 'edge': packaged_edge_contract})}",
        "run_date": run_date,
        "primitive_id": row.get("primitive_id"),
        "kind": row.get("kind"),
        "title": row.get("title"),
        "visible_edge": {
            "input": row.get("input_edge"),
            "output": row.get("output_edge"),
            "signature": f"{row.get('input_edge')} -> {row.get('output_edge')}",
            "description": f"{input_desc} {output_desc}",
        },
        "edge_contract": packaged_edge_contract,
        "group_contract": row.get("group_contract") if row.get("kind") == "primitive_group" else {},
        "hidden_member_edges": hidden_edges,
        "blackbox": row.get("blackbox"),
        "effects": row.get("effects"),
        "mutators": row.get("mutators"),
        "proof_requirements": row.get("proof_requirements"),
        "promotion_blockers": row.get("promotion_blockers"),
        "source_refs": row.get("source_refs"),
        "public_source_ref_count": len(public_refs),
        "composition_hints": _composition_hints(row),
        "reuse_profile": row.get("reuse_profile") if isinstance(row.get("reuse_profile"), dict) else {},
        "leverage_profile": leverage_profile,
        "token_saving_usage": {
            "retrieval_unit": "card_id_plus_visible_edge_plus_edge_contract",
            "builder_instruction": "Prefer linking this card by edge signature before asking an LLM to generate new glue code.",
            "context_policy": "include hidden_member_edges only for primitive_group validation or route debugging",
            "estimated_saved_output_tokens": leverage_profile["estimated_saved_output_tokens"],
            "leverage_tier": leverage_profile["leverage_tier"],
            "reuse_class": leverage_profile["reuse_class"],
            "candidate_only": True,
            "serves_truth": False,
        },
        "embedding_text": _text(embedding_text, limit=6000),
        "source_verification_id": row.get("verification_id"),
        "source_verified_at": row.get("verified_at"),
        "candidate": True,
        "serves_truth": False,
        "packaged_at": _now(),
    }


def _manifest_paths(prefix: str, run_date: str) -> list[Path]:
    if run_date:
        return [_resource(run_date) / "manifest.json"]
    return sorted(VERIFIED_ROOT.glob(prefix + "*/manifest.json"))


def package_cards(
    *,
    prefix: str,
    run_date: str,
    out_dir: Path,
    limit: int = 0,
    include_weak_source_refs: bool = False,
) -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    source_manifests = []
    for manifest_path in _manifest_paths(prefix, run_date):
        manifest = _read_json(manifest_path)
        verified_path_value = manifest.get("verified_path")
        verified_path = _resource(str(verified_path_value or ""))
        rows = _read_jsonl(verified_path)
        source_manifests.append({
            "run_date": manifest_path.parent.name,
            "manifest_path": _rel(manifest_path),
            "verified_path": _rel(verified_path),
            "verified_count": len(rows),
        })
        for row in rows:
            public_refs = _public_source_refs(row)
            if not public_refs and not include_weak_source_refs:
                rejected.append({
                    "record_type": "linkable_primitive_card_rejection",
                    "run_date": manifest_path.parent.name,
                    "primitive_id": row.get("primitive_id"),
                    "verification_id": row.get("verification_id"),
                    "errors": ["no_public_source_ref_url"],
                    "candidate": True,
                    "serves_truth": False,
                })
                continue
            cards.append(package_row(row, run_date=manifest_path.parent.name))
            if limit and len(cards) >= limit:
                break
        if limit and len(cards) >= limit:
            break
    out_dir.mkdir(parents=True, exist_ok=True)
    cards_path = out_dir / "linkable_primitive_cards.jsonl"
    rejected_path = out_dir / "rejected_linkable_cards.jsonl"
    route_index_path = out_dir / "edge_route_index.jsonl"
    input_index_path = out_dir / "input_edge_index.jsonl"
    output_index_path = out_dir / "output_edge_index.jsonl"
    group_index_path = out_dir / "primitive_group_index.jsonl"
    high_leverage_cards_path = out_dir / "high_leverage_cards.jsonl"
    high_leverage_index_path = out_dir / "high_leverage_index.jsonl"
    multistep_coding_index_path = out_dir / "multistep_coding_index.jsonl"
    manifest_path = out_dir / "manifest.json"
    _write_jsonl(cards_path, cards)
    _write_jsonl(rejected_path, rejected)
    indexes: dict[str, list[dict[str, Any]]] = {
        "route": [],
        "input": [],
        "output": [],
        "group": [],
        "high_leverage": [],
        "multistep_coding": [],
    }
    kind_counts: dict[str, int] = {}
    effect_counts: dict[str, int] = {}
    leverage_tier_counts: dict[str, int] = {}
    reuse_class_counts: dict[str, int] = {}
    estimated_saved_output_tokens_total = 0
    edge_description_char_total = 0
    high_leverage_cards: list[dict[str, Any]] = []
    multistep_group_count = 0
    long_edge_card_count = 0
    for card in cards:
        kind = str(card.get("kind") or "unknown")
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        side_effect = str((card.get("composition_hints") or {}).get("side_effect_class") or "unknown")
        effect_counts[side_effect] = effect_counts.get(side_effect, 0) + 1
        visible = card.get("visible_edge") if isinstance(card.get("visible_edge"), dict) else {}
        hints = card.get("composition_hints") if isinstance(card.get("composition_hints"), dict) else {}
        leverage = card.get("leverage_profile") if isinstance(card.get("leverage_profile"), dict) else {}
        leverage_tier = str(leverage.get("leverage_tier") or "unknown")
        reuse_class = str(leverage.get("reuse_class") or "unknown")
        leverage_tier_counts[leverage_tier] = leverage_tier_counts.get(leverage_tier, 0) + 1
        reuse_class_counts[reuse_class] = reuse_class_counts.get(reuse_class, 0) + 1
        saved_tokens = int(leverage.get("estimated_saved_output_tokens") or 0)
        edge_chars = int(leverage.get("edge_description_chars") or 0)
        hidden_edge_count = int(leverage.get("hidden_member_edge_count") or 0)
        estimated_saved_output_tokens_total += saved_tokens
        edge_description_char_total += edge_chars
        if hidden_edge_count >= GROUP_LIKE_MIN_HIDDEN_EDGES:
            multistep_group_count += 1
        if edge_chars >= HIGH_LEVERAGE_EDGE_DESC_CHARS:
            long_edge_card_count += 1
        index_base = {
            "record_type": "linkable_primitive_card_index_row",
            "card_id": card.get("card_id"),
            "primitive_id": card.get("primitive_id"),
            "kind": card.get("kind"),
            "title": card.get("title"),
            "run_date": card.get("run_date"),
            "route_signature": visible.get("signature"),
            "input_edge": visible.get("input"),
            "output_edge": visible.get("output"),
            "side_effect_class": hints.get("side_effect_class"),
            "public_source_ref_count": card.get("public_source_ref_count"),
            "leverage_tier": leverage_tier,
            "reuse_class": reuse_class,
            "leverage_score": leverage.get("score"),
            "estimated_saved_output_tokens": saved_tokens,
            "edge_description_chars": edge_chars,
            "hidden_member_edge_count": hidden_edge_count,
            "candidate": True,
            "serves_truth": False,
        }
        _append_index(indexes, "route", index_base | {
            "record_type": "linkable_primitive_route_index_row",
            "lookup_key": visible.get("signature"),
        })
        _append_index(indexes, "input", index_base | {
            "record_type": "linkable_primitive_input_edge_index_row",
            "lookup_key": visible.get("input"),
        })
        _append_index(indexes, "output", index_base | {
            "record_type": "linkable_primitive_output_edge_index_row",
            "lookup_key": visible.get("output"),
        })
        if card.get("kind") == "primitive_group":
            _append_index(indexes, "group", index_base | {
                "record_type": "linkable_primitive_group_index_row",
                "lookup_key": visible.get("signature"),
                "hidden_member_edge_count": hidden_edge_count,
            })
        if leverage_tier == "high":
            high_leverage_cards.append(card)
            _append_index(indexes, "high_leverage", index_base | {
                "record_type": "linkable_high_leverage_index_row",
                "lookup_key": visible.get("signature"),
            })
        if reuse_class == "multistep_coding_group" or (
            card.get("kind") == "primitive_group" and leverage.get("coding_surface_terms")
        ):
            _append_index(indexes, "multistep_coding", index_base | {
                "record_type": "linkable_multistep_coding_index_row",
                "lookup_key": visible.get("signature"),
                "coding_surface_terms": leverage.get("coding_surface_terms") or [],
            })
    _write_jsonl(route_index_path, indexes["route"])
    _write_jsonl(input_index_path, indexes["input"])
    _write_jsonl(output_index_path, indexes["output"])
    _write_jsonl(group_index_path, indexes["group"])
    _write_jsonl(high_leverage_cards_path, high_leverage_cards)
    _write_jsonl(high_leverage_index_path, indexes["high_leverage"])
    _write_jsonl(multistep_coding_index_path, indexes["multistep_coding"])
    manifest = {
        "record_type": "linkable_primitive_card_manifest",
        "prefix": prefix,
        "run_date": run_date,
        "out_dir": _rel(out_dir),
        "cards_path": _rel(cards_path),
        "rejected_path": _rel(rejected_path),
        "route_index_path": _rel(route_index_path),
        "input_edge_index_path": _rel(input_index_path),
        "output_edge_index_path": _rel(output_index_path),
        "primitive_group_index_path": _rel(group_index_path),
        "high_leverage_cards_path": _rel(high_leverage_cards_path),
        "high_leverage_index_path": _rel(high_leverage_index_path),
        "multistep_coding_index_path": _rel(multistep_coding_index_path),
        "card_count": len(cards),
        "rejected_count": len(rejected),
        "route_index_count": len(indexes["route"]),
        "input_edge_index_count": len(indexes["input"]),
        "output_edge_index_count": len(indexes["output"]),
        "primitive_group_index_count": len(indexes["group"]),
        "high_leverage_card_count": len(high_leverage_cards),
        "high_leverage_index_count": len(indexes["high_leverage"]),
        "multistep_coding_index_count": len(indexes["multistep_coding"]),
        "multistep_group_count": multistep_group_count,
        "long_edge_card_count": long_edge_card_count,
        "estimated_saved_output_tokens_total": estimated_saved_output_tokens_total,
        "estimated_saved_output_tokens_avg": round(estimated_saved_output_tokens_total / len(cards), 3) if cards else 0,
        "edge_description_chars_total": edge_description_char_total,
        "edge_description_chars_avg": round(edge_description_char_total / len(cards), 3) if cards else 0,
        "include_weak_source_refs": include_weak_source_refs,
        "source_manifest_count": len(source_manifests),
        "source_manifests": source_manifests,
        "kind_counts": dict(sorted(kind_counts.items())),
        "side_effect_class_counts": dict(sorted(effect_counts.items())),
        "leverage_tier_counts": dict(sorted(leverage_tier_counts.items())),
        "reuse_class_counts": dict(sorted(reuse_class_counts.items())),
        "promotion_note": "Linkable cards are packaged verified candidates; they remain candidate-only and do not serve truth.",
        "candidate": True,
        "serves_truth": False,
        "created_at": _now(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    import tempfile

    row = {
        "primitive_id": "prim:test.parse_json",
        "kind": "primitive",
        "title": "Parse JSON",
        "input_edge": "JsonText",
        "output_edge": "RecordObject",
        "contract": {"summary": "Parse JSON.", "input": {"text": "string"}, "output": {"record": "object"}, "errors": {"invalid": "Invalid JSON"}},
        "blackbox": "Parses JSON text into an object.",
        "effects": [{"type": "compute", "description": "local parse"}],
        "source_refs": [{"label": "Python json", "url": "https://docs.python.org/3/library/json.html"}],
        "mutators": ["schema_validator_inserter"],
        "proof_requirements": ["valid_json_fixture", "invalid_json_fixture"],
        "promotion_blockers": ["review_required"],
        "reuse_profile": {
            "reuse_class": "long_edge_contract",
            "estimated_saved_output_tokens": 900,
            "reusable_build_tasks": ["json api response parsing"],
            "implementation_surfaces": ["python"],
            "compile_strategy": "bind JsonText to RecordObject through json.loads",
            "linking_instructions": "Use when a caller has raw JSON text and needs a typed record envelope.",
        },
        "verification_id": "pcv:test",
        "verified_at": "2099-01-01T00:00:00+00:00",
        "candidate": True,
        "serves_truth": False,
    }
    card = package_row(row, run_date="2099-01-01")
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        manifest = {
            "record_type": "primitive_candidate_verification_manifest",
            "verified_path": str(out_dir / "verified_candidates.jsonl"),
            "candidate": True,
            "serves_truth": False,
        }
        _write_jsonl(out_dir / "verified_candidates.jsonl", [row])
        (out_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    ok = (
        card["candidate"] is True
        and card["serves_truth"] is False
        and card["edge_contract"]["input_edge_description"]
        and card["edge_contract"]["output_edge_description"]
        and card["public_source_ref_count"] == 1
        and card["leverage_profile"]["estimated_saved_output_tokens"] >= 900
        and card["token_saving_usage"]["reuse_class"] == "long_edge_contract"
        and "JsonText" in card["embedding_text"]
    )
    print("PASS - linkable primitive cards package verified rows with rich edge contracts." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    parser.add_argument("--date", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--include-weak-source-refs", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    out_dir = Path(args.out_dir) if args.out_dir else PACKAGE_ROOT / (args.date or args.prefix)
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)
    try:
        manifest = package_cards(
            prefix=args.prefix,
            run_date=args.date,
            out_dir=out_dir,
            limit=args.limit,
            include_weak_source_refs=args.include_weak_source_refs,
        )
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
