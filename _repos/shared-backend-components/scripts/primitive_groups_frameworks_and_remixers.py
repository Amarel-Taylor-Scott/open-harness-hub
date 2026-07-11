#!/usr/bin/env python3
"""primitive_groups_frameworks_and_remixers — the composition layer OVER existing primitive cards.

Owner (2026-07-10): "have groups of primitives, primitive frameworks, primitive remixers, deterministic
primitive remixers, deterministic primitive integrators, and other tools/methods." This module adds five
first-class, receipt-backed record families on top of any card list (worked example: the 55-card
corporate-records pack), each behind a ZOO table (multi-path law — extending any of them is a new row,
never a rewrite):

  1. PRIMITIVE GROUPS       — computed typed collections (`GROUP_BUILDERS`): by family, by pack, by
                              consumed/produced edge type. Groups carry member ids + edge signatures.
  2. PRIMITIVE FRAMEWORKS   — ordered stage scaffolds (`FRAMEWORKS`) whose stages select members by
                              deterministic predicates; INSTANTIATED per scope (e.g. one governed-scraping
                              pipeline per source family) with honest coverage gaps, never invented members.
  3. PRIMITIVE REMIXERS     — `REMIX_TRANSFORMS`, a zoo of card→variant transforms. v1 ships the
                              DETERMINISTIC subset (0-token, applicability-gated, double-run byte-identical);
                              an `llm_seam` row marks where model-backed remixing plugs in (not runnable here).
  4. DETERMINISTIC REMIXES  — every variant carries lineage {parent_card_id, transform_id} and a fresh
                              canonical_id; the flagship transform is `edge_vocabulary_align`, the measured
                              chainability lever (independently-minted edge names never chain exactly).
  5. DETERMINISTIC INTEGRATORS — `INTEGRATORS` compile composite primitives through EXACT edge routes
                              (reuses scripts.primitive_runtime.compose_route — never a second composer).
                              Refusals are honest receipts; the self-test proves the raw pack REFUSES and the
                              edge-aligned remix corpus INTEGRATES the same request in 2 exact steps.

Everything emitted is `candidate=true, serves_truth=false` (generation is never promotion); remixes and
composites are NEW derived rows next to their parents — the raw layer is never touched (lossless law).

    PYTHONPATH=. python3 scripts/primitive_groups_frameworks_and_remixers.py --self-test
    PYTHONPATH=. python3 scripts/primitive_groups_frameworks_and_remixers.py --build
    PYTHONPATH=. python3 scripts/primitive_groups_frameworks_and_remixers.py --demo
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_groups_frameworks_and_remixers requires canonical_id; import failed: {exc}")

OUT_DIR = _SBC / "data" / "dev-intel" / "primitive_factory" / "composition_layer"
GROUPS_PATH = OUT_DIR / "primitive_groups.jsonl"
FRAMEWORKS_PATH = OUT_DIR / "primitive_frameworks.jsonl"
INSTANCES_PATH = OUT_DIR / "framework_instances.jsonl"
REMIXES_PATH = OUT_DIR / "remixed_primitive_cards.jsonl"
INTEGRATIONS_PATH = OUT_DIR / "integrated_primitive_cards.jsonl"
MANIFEST_PATH = OUT_DIR / "composition_layer_manifest.json"
GROUP_ID_PREFIX = "pgrp"
FRAMEWORK_ID_PREFIX = "pfwk"
INSTANCE_ID_PREFIX = "pfwi"
REMIX_ID_PREFIX = "prmx"
INTEGRATION_ID_PREFIX = "pint"
_CANDIDATE_BITS = {"candidate": True, "serves_truth": False}
_PLACEHOLDER_MARKERS = ("todo", "tbd", "lorem", "fixme")


def default_cards() -> list[dict[str, Any]]:
    """The worked-example corpus: the corporate-records pack, regenerated deterministically (no file dep)."""
    from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
    return build_cards()


def _card_text(card: dict[str, Any]) -> str:
    return f"{card.get('title', '')} {card.get('blackbox', '')}".lower()


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# 1 · PRIMITIVE GROUPS — computed typed collections. Add a builder = add a row.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _group_rows(builder: str, keyed: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for key, members in sorted(keyed.items()):
        member_ids = sorted(c["card_id"] for c in members)
        rows.append({"group_id": canonical_id(GROUP_ID_PREFIX, builder, key),
                     "record_type": "primitive_group", "builder": builder, "key": key,
                     "member_count": len(member_ids), "member_ids": member_ids,
                     "consumes_edges": sorted({c["input_edge"] for c in members}),
                     "produces_edges": sorted({c["output_edge"] for c in members}),
                     "schema_version": "1", **_CANDIDATE_BITS})
    return rows


def _by_field(cards: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    keyed: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        keyed.setdefault(str(card.get(field) or "unspecified"), []).append(card)
    return keyed


GROUP_BUILDERS: dict[str, Callable[[list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]] = {
    "by_family": lambda cards: _by_field(cards, "family"),
    "by_pack": lambda cards: _by_field(cards, "pack"),
    "by_consumed_edge": lambda cards: _by_field(cards, "input_edge"),
    "by_produced_edge": lambda cards: _by_field(cards, "output_edge"),
}


def build_groups(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for builder, fn in sorted(GROUP_BUILDERS.items()):
        rows.extend(_group_rows(builder, fn(cards)))
    return rows


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# 2 · PRIMITIVE FRAMEWORKS — ordered stage scaffolds; stages select members deterministically.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#: stage selector = ANY of the listed lowercase tokens appearing in title+blackbox (deterministic predicate).
FRAMEWORKS: dict[str, dict[str, Any]] = {
    "governed_scraping_framework": {
        "description": "The full governed acquisition motion for one records source: policy gate before any "
                       "fetch, budgeted fetching, incremental enumeration, parsing, normalization, linking, "
                       "and provenance/CDC — instantiated per source family.",
        "stages": [
            {"stage": "policy_gate", "tokens": ["policy gate", "tos", "robots", "preflight", "access-policy",
                                                "access restriction"], "required": True},
            {"stage": "rate_budget", "tokens": ["rate budget", "token bucket", "fee-budget", "quota",
                                                "rate-budget"], "required": True},
            {"stage": "enumerate_or_search", "tokens": ["enumerat", "search", "index", "watcher"],
             "required": True},
            {"stage": "fetch", "tokens": ["fetch"], "required": False},
            {"stage": "parse_extract", "tokens": ["parse", "extractor", "parser", "ingest"], "required": True},
            {"stage": "normalize", "tokens": ["normaliz", "crosswalk", "mapper"], "required": True},
            {"stage": "link_dedupe", "tokens": ["link", "dedupe", "cluster", "resolve"], "required": False},
            {"stage": "provenance_cdc", "tokens": ["receipt", "watermark", "provenance", "cdc", "audit"],
             "required": True},
            {"stage": "review", "tokens": ["review"], "required": False},
        ],
    },
    "entity_resolution_framework": {
        "description": "Cross-source entity convergence: normalize source records to canonical entities, "
                       "route by jurisdiction, link and cluster conservatively, and surface conflicts as "
                       "review tickets — never an auto-merge.",
        "stages": [
            {"stage": "normalize", "tokens": ["normaliz", "canonical"], "required": True},
            {"stage": "route", "tokens": ["router", "jurisdiction"], "required": True},
            {"stage": "link", "tokens": ["link", "resolve", "crosswalk"], "required": True},
            {"stage": "cluster", "tokens": ["dedupe", "cluster"], "required": True},
            {"stage": "review", "tokens": ["review", "conflict"], "required": True},
            {"stage": "provenance", "tokens": ["provenance", "chain", "receipt"], "required": True},
        ],
    },
}


def framework_rows() -> list[dict[str, Any]]:
    rows = []
    for name, spec in sorted(FRAMEWORKS.items()):
        rows.append({"framework_id": canonical_id(FRAMEWORK_ID_PREFIX, name),
                     "record_type": "primitive_framework", "name": name,
                     "description": spec["description"],
                     "stages": [{"stage": s["stage"], "required": s["required"]} for s in spec["stages"]],
                     "stage_count": len(spec["stages"]), "schema_version": "1", **_CANDIDATE_BITS})
    return rows


def instantiate_framework(name: str, cards: list[dict[str, Any]],
                          scope_family: Optional[str] = None) -> dict[str, Any]:
    """Fill a framework's stages from a card list (scope family first, cross_source spine as fallback).
    Coverage is HONEST: an unfilled stage is a listed gap, never an invented member."""
    spec = FRAMEWORKS[name]
    in_scope = [c for c in cards if scope_family is None or c.get("family") in (scope_family, "cross_source")]
    stage_members: dict[str, list[str]] = {}
    for stage in spec["stages"]:
        hits = [c for c in in_scope if any(token in _card_text(c) for token in stage["tokens"])]
        preferred = [c for c in hits if scope_family is None or c.get("family") == scope_family]
        chosen = preferred or hits
        stage_members[stage["stage"]] = sorted(c["card_id"] for c in chosen)
    missing = [s["stage"] for s in spec["stages"] if not stage_members[s["stage"]]]
    missing_required = [s["stage"] for s in spec["stages"] if s["required"] and not stage_members[s["stage"]]]
    return {"instance_id": canonical_id(INSTANCE_ID_PREFIX, name, scope_family or "all"),
            "record_type": "primitive_framework_instance", "framework": name,
            "scope_family": scope_family or "all",
            "stage_members": stage_members,
            "stages_filled": sum(1 for m in stage_members.values() if m),
            "stage_count": len(spec["stages"]),
            "missing_stages": missing, "missing_required_stages": missing_required,
            "complete": not missing_required, "schema_version": "1", **_CANDIDATE_BITS}


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# 3+4 · PRIMITIVE REMIXERS — a zoo of card→variant transforms; v1 = the deterministic subset.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#: THE chainability lever: independently-minted edge names never chain exactly (measured at 112K — exact
#: cross-card joins = 0), so aligned variants map near-miss edges onto shared canonical types. The served table
#: (`CANONICAL_EDGE_ALIGNMENTS`) is now `curated_seed ∪ promoted_candidate_rows` (gap 2.1 emit-loop): the seed
#: below is the human-curated set; propose_edge_alignments emits candidate_for_review rows, and a human PROMOTES
#: sound ones into the governed file (`PROMOTED_ALIGNMENTS_PATH`) — so alignment scales past hand-curation
#: speed WITHOUT letting a proposal auto-serve (the candidate/truth boundary holds; promotion is a human act).
_CURATED_EDGE_ALIGNMENTS_SEED: dict[str, str] = {
    "OfficerDirectorRowBatch": "OfficerRowBatch",
    "NonprofitOfficerRowBatch": "OfficerRowBatch",
    "UkOfficerRowBatch": "OfficerRowBatch",
    "StateEntityCandidateBatch": "SourceEntityRecordBatch",
    "AggregatorEntityCandidateBatch": "SourceEntityRecordBatch",
    "UkCompanyProfileRecord": "SourceEntityRecordBatch",
    "FederalRegistrationRecordBatch": "SourceEntityRecordBatch",
    # ── added 2026-07-10 from the network-buildout workflow, each INDEPENDENTLY re-verified as an
    #    output-payload → output-payload same-shape alias (unsound input-contract→payload proposals were
    #    REJECTED; the audit is in the fold-in commit). ──
    "AssignmentPartyRowBatch": "PatentConveyanceRowBatch",   # USPTO conveyance rows carry the assignor/assignee parties
    "ExclusionCdcEventBatch": "RegistryChangeEventBatch",    # a SAM debarment CDC event IS a registry change event
    "EdgarSearchHitBatch": "EdgarFilingReferenceBatch",      # full-text hits are filing references (+ relevance extras)
}

#: governed store of PROMOTED candidate alignments (JSONL, one {from_edge,to_edge,status:"promoted"} per line).
#: A human promotes a gated proposal here; nothing writes it automatically. Absent/empty by default -> the
#: served table equals the curated seed (no behavior change until something is promoted).
PROMOTED_ALIGNMENTS_PATH = OUT_DIR / "promoted_edge_alignments.jsonl"
_PAYLOAD_SUFFIXES = ("Batch", "Bundle", "Record", "Document", "Row", "Map", "Edge", "Facts", "List")


def _is_payload_edge(edge: str) -> bool:
    """Local payload-role check (mirrors edge_alignment_gate.edge_role's payload class) — a load-time
    defense-in-depth so a tampered promoted file can never inject an input-contract→payload alias."""
    return isinstance(edge, str) and edge.endswith(_PAYLOAD_SUFFIXES) and not edge.endswith("Reference") \
        or (isinstance(edge, str) and edge.endswith("Reference") and "Filing" in edge)


def _load_promoted_alignments() -> dict[str, str]:
    """Read the governed promoted-alignment store: rows with status=='promoted' that STILL pass a local
    payload→payload role check and do not collide with the curated seed's keys. Never raises."""
    promoted: dict[str, str] = {}
    try:
        text = PROMOTED_ALIGNMENTS_PATH.read_text()
    except OSError:
        return promoted
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        frm, to, status = row.get("from_edge"), row.get("to_edge"), row.get("status")
        if (status == "promoted" and frm and to and frm != to and frm not in _CURATED_EDGE_ALIGNMENTS_SEED
                and _is_payload_edge(frm) and _is_payload_edge(to)):
            promoted[frm] = to
    return promoted


def load_canonical_edge_alignments() -> dict[str, str]:
    """The served alignment table = curated seed ∪ promoted candidate rows (recomputed on demand)."""
    return {**_CURATED_EDGE_ALIGNMENTS_SEED, **_load_promoted_alignments()}


#: computed once at import (seed ∪ promoted). Consumers keep importing this name unchanged.
CANONICAL_EDGE_ALIGNMENTS: dict[str, str] = load_canonical_edge_alignments()


def promote_alignment(from_edge: str, to_edge: str) -> dict[str, Any]:
    """Promote a candidate alignment into the governed store — the human emit-loop step. Runs the soundness
    gate first (never promote an unsound alias); appends only if admissible. This is the ONLY writer; proposing
    is not promoting."""
    from scripts.edge_alignment_gate import screen  # noqa: PLC0415  the soundness authority
    verdict = screen([(from_edge, to_edge)], existing=load_canonical_edge_alignments())[0]
    if not verdict["admissible"]:
        return {"promoted": False, "reason": verdict["reason"], "candidate": True, "serves_truth": False}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with PROMOTED_ALIGNMENTS_PATH.open("a") as handle:
        handle.write(json.dumps({"from_edge": from_edge, "to_edge": to_edge, "status": "promoted",
                                 "gate_reason": verdict["reason"]}, sort_keys=True) + "\n")
    return {"promoted": True, "from_edge": from_edge, "to_edge": to_edge,
            "candidate": True, "serves_truth": False}

#: jurisdiction exemplar swaps (only where the source text literally names the exemplar).
_JURISDICTION_SWAPS = [("Delaware/California/New York", "Texas/Florida/Illinois"),
                       ("Delaware", "Texas"), ("California", "Florida"), ("New York", "Illinois")]
#: cadence swaps for windowed/delta sources (literal token, applicability-gated).
_CADENCE_SWAPS = [("daily", "weekly"), ("daily", "monthly")]


def _remix_row(parent: dict[str, Any], transform_id: str, params: str,
               fields: dict[str, Any]) -> dict[str, Any]:
    variant_id = canonical_id(REMIX_ID_PREFIX, parent["card_id"], transform_id, params)
    return {**parent, **fields, "card_id": variant_id, "primitive_id": variant_id,
            "record_type": "remixed_primitive_candidate", "remix_kind": "deterministic",
            "lineage": {"parent_card_id": parent["card_id"], "transform_id": transform_id,
                        "params": params, "deterministic": True},
            "schema_version": "1", **_CANDIDATE_BITS}


def _edge_align_apply(card: dict[str, Any]) -> list[dict[str, Any]]:
    new_in = CANONICAL_EDGE_ALIGNMENTS.get(card["input_edge"], card["input_edge"])
    new_out = CANONICAL_EDGE_ALIGNMENTS.get(card["output_edge"], card["output_edge"])
    if (new_in, new_out) == (card["input_edge"], card["output_edge"]):
        return []
    note = (f" Edge-aligned variant for exact composition: consumes {new_in}, produces {new_out} "
            f"(canonical edge vocabulary).")
    return [_remix_row(card, "edge_vocabulary_align", f"{new_in}->{new_out}",
                       {"title": f"{card['title']} (edge-aligned)",
                        "blackbox": card["blackbox"] + note,
                        "input_edge": new_in, "output_edge": new_out,
                        "composition_hints": {"consumes_edge": new_in, "produces_edge": new_out,
                                              "candidate_only": True}})]


def _text_swap_apply(card: dict[str, Any], transform_id: str,
                     swaps: list[tuple[str, str]], families: set[str]) -> list[dict[str, Any]]:
    if card.get("family") not in families:
        return []
    variants = []
    for old, new in swaps:
        if old in card["title"] or old.lower() in card["blackbox"].lower():
            title = card["title"].replace(old, new)
            blackbox = card["blackbox"].replace(old, new).replace(old.lower(), new.lower())
            if (title, blackbox) == (card["title"], card["blackbox"]):
                continue
            variants.append(_remix_row(card, transform_id, f"{old}->{new}",
                                       {"title": title if title != card["title"]
                                        else f"{card['title']} ({new} cadence)",
                                        "blackbox": blackbox}))
    return variants


REMIX_TRANSFORMS: dict[str, dict[str, Any]] = {
    "edge_vocabulary_align": {"kind": "deterministic", "apply": _edge_align_apply},
    "jurisdiction_exemplar_swap": {"kind": "deterministic",
                                   "apply": lambda c: _text_swap_apply(
                                       c, "jurisdiction_exemplar_swap", _JURISDICTION_SWAPS,
                                       {"state_sos", "ucc_filings"})},
    "cadence_swap": {"kind": "deterministic",
                     "apply": lambda c: _text_swap_apply(c, "cadence_swap", _CADENCE_SWAPS,
                                                         {"sec_edgar", "uspto", "gleif_lei", "sam_gov"})},
    "llm_paraphrase_remix": {"kind": "llm_seam", "apply": None,
                             "note": "model-backed remixing plugs in here (opt-in, never in the 0-token lane)"},
}


def build_remixes(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for card in cards:
        for _name, transform in sorted(REMIX_TRANSFORMS.items()):
            if transform["kind"] != "deterministic":
                continue   # seams are declared, not silently run
            for variant in transform["apply"](card):
                if variant["card_id"] in seen:
                    continue
                seen.add(variant["card_id"])
                rows.append(variant)
    return rows


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# 5 · DETERMINISTIC INTEGRATORS — composite primitives through EXACT edge routes (reused composer).
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _as_components(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"component_id": c["card_id"], "input_edge": c["input_edge"], "output_edge": c["output_edge"],
             "operation": c["title"], "cost": 1} for c in cards
            if c.get("input_edge") and c.get("output_edge")]


def integrate_exact_route(cards: list[dict[str, Any]], start: str, goal: str) -> dict[str, Any]:
    """Compile ONE composite primitive from an exact edge route, or an honest refusal receipt."""
    from scripts.primitive_runtime import compose_route  # noqa: PLC0415  the ONE composer — never a second
    result = compose_route(start, goal, _as_components(cards))
    if not result.get("route_found"):
        return {"integration_id": canonical_id(INTEGRATION_ID_PREFIX, "refusal", start, goal),
                "record_type": "integration_refusal_receipt", "start_edge": start, "goal_edge": goal,
                "route_found": False, "skipped_reason": result.get("skipped_reason", ""),
                "composer_path": result.get("composer_path", ""), "schema_version": "1", **_CANDIDATE_BITS}
    steps = result["ordered_route"]
    by_id = {c["card_id"]: c for c in cards}
    member_ids = [s["component_id"] for s in steps]
    titles = [by_id[m]["title"] for m in member_ids if m in by_id]
    return {"integration_id": canonical_id(INTEGRATION_ID_PREFIX, start, goal, *member_ids),
            "record_type": "integrated_primitive_candidate", "integrator": "exact_edge_route",
            "title": f"Integrated pipeline: {start} → {goal} ({len(steps)} exact steps)",
            "blackbox": "Deterministically integrated composite — each hop chains on exact canonical edge "
                        "equality, compiled by the shared route composer (a lookup, not a generation): "
                        + " → ".join(titles) + ".",
            "input_edge": start, "output_edge": goal, "edge_path": result["edge_path"],
            "member_ids": member_ids, "step_count": len(steps),
            "composer_path": result.get("composer_path", ""),
            "lineage": {"integrator": "exact_edge_route", "members": member_ids, "deterministic": True},
            "schema_version": "1", **_CANDIDATE_BITS}


#: integration demos: (start_edge, goal_edge) — refused on the raw pack, unlocked by edge alignment.
INTEGRATION_DEMOS: list[tuple[str, str]] = [
    ("ProxyStatementDocument", "OfficerDedupeClusterBatch"),
    ("StateEntitySearchRequest", "CanonicalEntityRowBatch"),
]

INTEGRATORS: dict[str, Any] = {
    "exact_edge_route": integrate_exact_route,
    # framework_pipeline: chain a framework instance's stages where adjacent edges align — next row to add.
}


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# Build + manifest (all counts computed).
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def build(write: bool = True) -> dict[str, Any]:
    cards = default_cards()
    groups = build_groups(cards)
    frameworks = framework_rows()
    families = sorted({c["family"] for c in cards})
    instances = [instantiate_framework("governed_scraping_framework", cards, scope_family=f)
                 for f in families if f != "cross_source"]
    instances.append(instantiate_framework("entity_resolution_framework", cards))
    remixes = build_remixes(cards)
    augmented = cards + remixes
    integrations = [integrate_exact_route(augmented, s, g) for s, g in INTEGRATION_DEMOS]
    refusals = [integrate_exact_route(cards, s, g) for s, g in INTEGRATION_DEMOS]

    outputs = {GROUPS_PATH: groups, FRAMEWORKS_PATH: frameworks, INSTANCES_PATH: instances,
               REMIXES_PATH: remixes, INTEGRATIONS_PATH: integrations + refusals}
    manifest = {"record_type": "composition_layer_manifest",
                "counts": {path.name: len(rows) for path, rows in sorted(outputs.items())},
                "base_cards": len(cards), "families": families,
                "remix_transforms": sorted(REMIX_TRANSFORMS),
                "integrators": sorted(INTEGRATORS),
                "integrations_found": sum(1 for r in integrations if r.get("route_found", True)
                                          and r["record_type"] == "integrated_primitive_candidate"),
                "integrations_refused_on_raw_pack": sum(1 for r in refusals
                                                        if r["record_type"] == "integration_refusal_receipt"),
                "source_ref": "owner-intent:groups-frameworks-remixers-integrators:2026-07-10",
                **_CANDIDATE_BITS}
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for path, rows in outputs.items():
            path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return {"manifest": manifest, "groups": groups, "frameworks": frameworks, "instances": instances,
            "remixes": remixes, "integrations": integrations, "refusals": refusals}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    cards = default_cards()
    built = build(write=True)
    groups, remixes = built["groups"], built["remixes"]
    instances, integrations, refusals = built["instances"], built["integrations"], built["refusals"]

    by_family = [g for g in groups if g["builder"] == "by_family"]
    checks.append(("groups: by_family PARTITIONS the pack exactly (member sum == card count; lossless)",
                   sum(g["member_count"] for g in by_family) == len(cards)
                   and len(by_family) == len({c["family"] for c in cards}),
                   f"{len(by_family)} groups over {len(cards)} cards"))
    all_rows = groups + built["frameworks"] + instances + remixes + integrations + refusals
    id_fields = [next(v for k, v in row.items() if k.endswith("_id")) for row in all_rows]
    checks.append(("every emitted row candidate-only with a unique canonical id",
                   len(set(id_fields)) == len(id_fields)
                   and all(r["candidate"] is True and r["serves_truth"] is False for r in all_rows), ""))

    sec = next(i for i in instances if i["scope_family"] == "sec_edgar")
    boi = next(i for i in instances if i["scope_family"] == "fincen_boi")
    checks.append(("frameworks: sec_edgar instance fills >= 6/9 governed-scraping stages; sparse families "
                   "report gaps honestly (never invented members)",
                   sec["stages_filled"] >= 6 and isinstance(boi["missing_stages"], list)
                   and all(set(i["missing_stages"]) >= set(i["missing_required_stages"]) for i in instances),
                   f"sec_edgar {sec['stages_filled']}/{sec['stage_count']}; boi missing {boi['missing_stages']}"))

    checks.append((f"deterministic remixes: {len(remixes)} variants, every one carries lineage "
                   "{parent, transform} + a fresh id + changed content",
                   len(remixes) >= 10
                   and all(r["lineage"]["parent_card_id"] != r["card_id"] and r["lineage"]["deterministic"]
                           and r["remix_kind"] == "deterministic" for r in remixes)
                   and all(json.dumps(r, sort_keys=True) != "" for r in remixes), str(len(remixes))))
    parents = {c["card_id"]: c for c in cards}
    checks.append(("remix honesty: every variant differs from its parent (title, blackbox, or edges)",
                   all((r["title"], r["blackbox"], r["input_edge"], r["output_edge"])
                       != ((p := parents[r["lineage"]["parent_card_id"]])["title"], p["blackbox"],
                           p["input_edge"], p["output_edge"]) for r in remixes), ""))

    first_bytes = REMIXES_PATH.read_bytes()
    build(write=True)
    checks.append(("deterministic: double build byte-identical (remixes file)",
                   first_bytes == REMIXES_PATH.read_bytes(), ""))

    checks.append(("integrator honesty: RAW pack REFUSES both demos (independently-minted edges never chain "
                   "exactly) with receipted reasons",
                   all(r["record_type"] == "integration_refusal_receipt" and not r["route_found"]
                       for r in refusals), json.dumps(refusals)[:160]))
    checks.append(("remix→integrate unlock: edge-aligned corpus compiles BOTH demos as exact 2-step "
                   "composites with member lineage (0-token, reused composer)",
                   all(r["record_type"] == "integrated_primitive_candidate" and r["step_count"] == 2
                       and len(r["member_ids"]) == 2 and r["lineage"]["deterministic"]
                       for r in integrations), json.dumps(integrations)[:200]))

    checks.append(("zoo openness: transforms/integrators/builders are tables (adding = one row); the llm "
                   "seam is declared, kind-labeled, and NOT silently run",
                   REMIX_TRANSFORMS["llm_paraphrase_remix"]["kind"] == "llm_seam"
                   and all(t["kind"] in ("deterministic", "llm_seam") for t in REMIX_TRANSFORMS.values())
                   and callable(GROUP_BUILDERS["by_family"]) and callable(INTEGRATORS["exact_edge_route"]),
                   ""))
    checks.append(("no placeholder text in any emitted row",
                   all(marker not in json.dumps(r).lower() for r in all_rows
                       for marker in _PLACEHOLDER_MARKERS), ""))
    manifest = json.loads(MANIFEST_PATH.read_text())
    checks.append(("manifest counts computed == emitted rows",
                   manifest["counts"][REMIXES_PATH.name] == len(remixes)
                   and manifest["counts"][GROUPS_PATH.name] == len(groups)
                   and manifest["integrations_found"] == len(INTEGRATION_DEMOS)
                   and manifest["integrations_refused_on_raw_pack"] == len(INTEGRATION_DEMOS), ""))

    # EMIT-LOOP (gap 2.1): the served table = curated_seed ∪ PROMOTED candidate rows. By default (no promoted
    # file) it equals the seed; promote_alignment gates then appends; an unsound promotion is refused. Uses a
    # temp store so the real governed file is untouched.
    import tempfile  # noqa: PLC0415
    global PROMOTED_ALIGNMENTS_PATH
    saved_path = PROMOTED_ALIGNMENTS_PATH
    with tempfile.TemporaryDirectory() as tmp:
        PROMOTED_ALIGNMENTS_PATH = Path(tmp) / "promoted.jsonl"
        seed_only = load_canonical_edge_alignments()
        refused = promote_alignment("SomeQueryRequest", "OfficerRowBatch")   # input-contract source -> refused
        ok_promo = promote_alignment("VendorOfficerRowBatch", "OfficerRowBatch")   # sound payload→payload
        after = load_canonical_edge_alignments()
        emit_ok = (seed_only == _CURATED_EDGE_ALIGNMENTS_SEED and refused["promoted"] is False
                   and ok_promo["promoted"] is True
                   and after.get("VendorOfficerRowBatch") == "OfficerRowBatch"
                   and len(after) == len(_CURATED_EDGE_ALIGNMENTS_SEED) + 1)
    PROMOTED_ALIGNMENTS_PATH = saved_path
    checks.append(("emit-loop: served table = curated seed by default; promote_alignment GATES (unsound "
                   "refused) then appends a sound row that the loader unions in — alignment scales past "
                   "hand-curation without auto-serving",
                   emit_ok, f"seed={len(_CURATED_EDGE_ALIGNMENTS_SEED)}"))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_groups_frameworks_and_remixers: composition layer over "
          f"{len(cards)} cards — {len(groups)} groups ({len(GROUP_BUILDERS)} builders), "
          f"{len(built['frameworks'])} frameworks "
          f"({len(instances)} instances), {len(remixes)} deterministic remixes (lineage-carrying), "
          f"{len(INTEGRATION_DEMOS)} exact-route integrations (refused raw, unlocked by edge alignment). "
          f"candidate-only. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:220]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Groups, frameworks, remixers, and deterministic "
                                                 "integrators over primitive cards.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--demo", action="store_true", help="print the remix→integrate unlock story")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.build:
        result = build(write=True)
        print(json.dumps(result["manifest"], indent=2, sort_keys=True))
        return 0
    if args.demo:
        cards = default_cards()
        for start, goal in INTEGRATION_DEMOS:
            raw = integrate_exact_route(cards, start, goal)
            aligned = integrate_exact_route(cards + build_remixes(cards), start, goal)
            print(json.dumps({"request": f"{start} -> {goal}",
                              "raw_pack": raw.get("skipped_reason") or raw["record_type"],
                              "aligned": {"steps": aligned.get("step_count"),
                                          "members": aligned.get("member_ids")}}, indent=2))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
