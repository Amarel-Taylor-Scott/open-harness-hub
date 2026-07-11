#!/usr/bin/env python3
"""scripts.mint_unmet_edge_producers — turn the domain benchmark's NAMED unmet edges into STAGED producer
candidate cards: the demand side of the composition gap made actionable.

The domain token-savings benchmark (data/dev-intel/domain_token_savings/summary.json) names, per domain, the
``top_unmet_edges`` — input edge types the exact-edge route compiler NEEDED but no verified producer's
``output_edge`` satisfied (CanonicalSchema, SortedList, DirectedGraph, ...; always READ from the file, never
hardcoded). Each unmet type is a measured demand signal for a producer that does not exist yet. This module
mints ONE staged producer candidate card per (domain, unmet type):

  * ``output_edge``  — the unmet type itself (what the benchmark demanded and could not find),
  * ``input_edge``   — the nearest EXISTING type the verified corpus already produces
                       (``scripts.edge_type_matcher.match_hits`` — REUSED, never reimplemented; exact ->
                       canonical -> token tiers), falling back to the domain probe's own input (the probe
                       ``intent`` recorded in rows.jsonl whose ``needed_edges`` named the type), and only
                       then to the generic raw-text type,
  * ``blackbox``     — the needed transform in words (nearest existing type -> demanded type),
  * ``provenance``   — the benchmark receipt (repo-relative path of summary.json) named as the demand
                       signal, plus the nearest-producer hits and the probe intents that demanded the edge,
  * ``primitive_id`` — the ONE id authority ``src.teleon.experiments.ids.canonical_id`` (sha256 content
                       hash over the card's meaning-bearing parts; no RNG, no wall-clock).

Cards are APPENDED to data/dev-intel/domain_token_savings/staged_producer_candidates.jsonl, deduped by
``primitive_id`` against the lines already there (a second identical run appends NOTHING). These are STAGED
candidates: every card is ``candidate=true / serves_truth=false`` with explicit ``promotion_blockers`` —
generation is NEVER promotion, and the verified corpus (verified_factory_primitive_cards.jsonl) is never
touched.

Deterministic end to end: same summary + rows + corpus -> byte-identical cards (no timestamps in any card,
key, or id). The write path REFUSES a card that violates the candidate/truth boundary or whose id does not
recompute from its content (the self-test's mutation gate proves both refusals fire).

    PYTHONPATH=. python3 scripts/mint_unmet_edge_producers.py --self-test
    python3 scripts/mint_unmet_edge_producers.py --run
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import tempfile  # noqa: E402
from typing import Any, Iterable, Optional  # noqa: E402

from scripts._jsonl import read_jsonl_tolerant  # noqa: E402  (mandated tolerant reader for append-only feeds)
from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts.edge_type_matcher import CORPUS as VERIFIED_CORPUS_PATH  # noqa: E402  single-sourced corpus path
from scripts.edge_type_matcher import build_producer_index, match_hits  # noqa: E402  THE matcher — reused
from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority (sha256 content hash)

#: every minted row/report is a candidate signal, never truth — generation is NEVER promotion (repo law).
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: the benchmark directory this module reads from and stages into (single definition; the self-test points
#: the same code at a temp dir, so the real paths appear exactly once).
BENCH_DIR: Path = _resource("data") / "dev-intel" / "domain_token_savings"
#: the three benchmark files, named ONCE so the hermetic self-test and the real run share the exact strings.
SUMMARY_FILENAME = "summary.json"
ROWS_FILENAME = "rows.jsonl"
STAGED_FILENAME = "staged_producer_candidates.jsonl"

#: typed, human-readable id prefix for minted producer candidates; the suffix is canonical_id's sha256[:16]
#: content hash, so the prefix carries meaning and the hash carries uniqueness (ID And Hash Discipline).
STAGED_ID_PREFIX = "prim:unmet"
#: record_type of every staged card — distinguishes demand-minted producer candidates from verified cards.
STAGED_RECORD_TYPE = "staged_producer_candidate"
#: mirrors the verified corpus's card kind so a future loader/matcher indexes these cards uniformly.
STAGED_CARD_KIND = "route.primitive"
#: card schema version lives in METADATA, never in a name or id (deterministic-naming law).
STAGED_SCHEMA_VERSION = 1
#: readiness label for a card whose producer is not built yet: rank 0 under edge_type_matcher._readiness_rank,
#: deliberately BELOW every built card (R1+), so ranking never prefers an unbuilt demand stub.
STAGED_READINESS_UNBUILT = "R0_demand_named"
#: how many nearest existing producers to record per unmet type — enough to show real alternatives to the
#: implementer, small enough that a card stays a compact demand record rather than a search dump.
NEAREST_PRODUCER_LIMIT = 3
#: why a staged card cannot be promoted as-is — explicit blockers keep the candidate/truth boundary readable.
STAGED_PROMOTION_BLOCKERS: tuple[str, ...] = (
    "producer_not_implemented",
    "no_proof_executed",
    "demand_signal_only",
)
#: provenance labels for HOW the card's input_edge was chosen (best matched type > the probe's own input >
#: the generic fallback) — recorded so a reviewer can weight the card without re-deriving the match.
INPUT_EDGE_FROM_NEAREST_PRODUCER = "nearest_producer_output"
INPUT_EDGE_FROM_DOMAIN_PROBE = "domain_probe_intent"
INPUT_EDGE_FROM_GENERIC_FALLBACK = "generic_text_fallback"
#: last-resort input type when neither a near producer nor a demanding probe exists: the corpus's most
#: generic raw-input type ('Text' is the universal raw edge in the verified corpus vocabulary).
GENERIC_FALLBACK_INPUT_EDGE = "Text"
#: demand-signal label used only when the summary carries no record_type of its own (the normal path READS
#: the summary's record_type, so the label is computed from the receipt, not typed here).
DEMAND_SIGNAL_DEFAULT = "domain_token_savings_benchmark"

#: shape of a well-minted id: the typed prefix + '-' + canonical_id's 16-hex sha256 suffix.
_STAGED_ID_RE = re.compile(r"^%s-[0-9a-f]{16}$" % re.escape(STAGED_ID_PREFIX))


# ── reading the demand signal ──────────────────────────────────────────────────────────────────────────────

def read_unmet_edges_by_domain(summary: dict) -> dict[str, list[str]]:
    """Per-domain NAMED unmet edge types, READ from the benchmark summary (never hardcoded). Preserves the
    file's own rank order (they are the TOP unmet edges); blank names and edge-less domains are skipped."""
    out: dict[str, list[str]] = {}
    for d in summary.get("domains", []) or []:
        domain = str(d.get("domain") or "").strip()
        composition = d.get("composition") or {}
        edges = [str(e).strip() for e in composition.get("top_unmet_edges", []) or [] if str(e).strip()]
        if domain and edges:
            out[domain] = edges
    return out


def probe_intents_demanding(rows: Iterable[dict], domain: str, unmet_edge: str) -> list[str]:
    """The domain probes' own inputs: intents of benchmark rows in ``domain`` whose ``needed_edges`` named
    ``unmet_edge``. Sorted for determinism regardless of row order; used as the input_edge fallback."""
    intents: set[str] = set()
    for r in rows:
        if str(r.get("domain") or "") != domain:
            continue
        needed = r.get("needed_edges") or []
        if isinstance(needed, list) and unmet_edge in needed:
            intent = str(r.get("intent") or "").strip()
            if intent:
                intents.add(intent)
    return sorted(intents)


# ── minting ────────────────────────────────────────────────────────────────────────────────────────────────

def _transform_blackbox(input_edge: str, output_edge: str, domain: str, input_source: str) -> str:
    """The needed transform in words — what a builder must implement to close this gap."""
    if input_source == INPUT_EDGE_FROM_NEAREST_PRODUCER:
        bridge = (f"The verified corpus already produces the near type '{input_edge}'; "
                  f"this producer converts that nearest existing type into the demanded one.")
    elif input_source == INPUT_EDGE_FROM_DOMAIN_PROBE:
        bridge = (f"No near producer exists in the verified corpus; the input is the domain probe's own "
                  f"request ('{input_edge}'), so this producer must build '{output_edge}' from that intent.")
    else:
        bridge = (f"No near producer and no recorded probe input exist; this producer must build "
                  f"'{output_edge}' from generic raw text.")
    return (f"Consumes {input_edge} and emits {output_edge}. The '{domain}' domain benchmark named "
            f"'{output_edge}' as an unmet input edge — the route compiler needed it and no verified "
            f"producer's output satisfied it. {bridge}")


def mint_producer_candidates(summary: dict, rows: list[dict], corpus_cards: list[dict],
                             *, receipt_ref: str) -> list[dict]:
    """Mint ONE staged producer candidate card per (domain, unmet edge type) named by the summary.

    Pure and deterministic over its inputs: no RNG, no wall-clock — the id is canonical_id's sha256 content
    hash over (domain, output_edge, input_edge), so the same demand always mints the same card byte-for-byte.
    Every card is stamped candidate=true / serves_truth=false (generation is never promotion)."""
    index = build_producer_index(corpus_cards)          # REUSED matcher index; never a bespoke reimplement
    demand_signal = str(summary.get("record_type") or DEMAND_SIGNAL_DEFAULT)
    domain_stats = {str(d.get("domain") or ""): (d.get("composition") or {})
                    for d in summary.get("domains", []) or []}
    cards: list[dict] = []
    seen_ids: set[str] = set()
    for domain, unmet_edges in read_unmet_edges_by_domain(summary).items():
        for unmet_edge in unmet_edges:
            hits = match_hits(unmet_edge, index, limit=NEAREST_PRODUCER_LIMIT)
            # a producer that ALREADY outputs the exact unmet string would make an identity card (T -> T);
            # prefer the best hit with a genuinely different output type and record that exactness exists.
            near = [h for h in hits if str(h.get("producer_output_edge") or "") != unmet_edge]
            exact_producer_now_exists = len(near) < len(hits)
            intents = probe_intents_demanding(rows, domain, unmet_edge)
            if near:
                input_edge = str(near[0].get("producer_output_edge"))
                input_source = INPUT_EDGE_FROM_NEAREST_PRODUCER
            elif intents:
                input_edge = intents[0]
                input_source = INPUT_EDGE_FROM_DOMAIN_PROBE
            else:
                input_edge = GENERIC_FALLBACK_INPUT_EDGE
                input_source = INPUT_EDGE_FROM_GENERIC_FALLBACK
            composition = domain_stats.get(domain, {})
            pid = canonical_id(STAGED_ID_PREFIX, domain, unmet_edge, input_edge)
            if pid in seen_ids:                          # within-batch dedupe (same demand named twice)
                continue
            seen_ids.add(pid)
            cards.append({
                "record_type": STAGED_RECORD_TYPE,
                "schema_version": STAGED_SCHEMA_VERSION,
                "kind": STAGED_CARD_KIND,
                "primitive_id": pid,
                "title": f"{input_edge} -> {unmet_edge} producer (unmet edge named by the {domain} benchmark)",
                "domain": domain,
                "input_edge": input_edge,
                "output_edge": unmet_edge,
                "blackbox": _transform_blackbox(input_edge, unmet_edge, domain, input_source),
                "readiness": STAGED_READINESS_UNBUILT,
                "promotion_blockers": list(STAGED_PROMOTION_BLOCKERS),
                "provenance": {
                    "demand_signal": demand_signal,
                    "receipt": receipt_ref,
                    "domain": domain,
                    "domain_gap_rate": composition.get("gap_rate"),
                    "domain_route_found_rate": composition.get("route_found_rate"),
                    "input_edge_source": input_source,
                    "exact_producer_now_exists": exact_producer_now_exists,
                    "nearest_producers": [
                        {k: h.get(k) for k in ("primitive_id", "producer_output_edge", "matched_via", "score")}
                        for h in hits
                    ],
                    "probe_intents": intents,
                },
                **BOUNDARY,
            })
    return cards


# ── the write gate (dedupe + boundary enforcement) ─────────────────────────────────────────────────────────

def serialize_card(card: dict) -> str:
    """Canonical one-line JSON for a card — sorted keys, compact separators, so two mints of the same demand
    are byte-identical on disk (the determinism gate compares these bytes)."""
    return json.dumps(card, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def validate_staged_card(card: dict) -> list[str]:
    """Problems that make a card unfit to stage (empty list == fit). The write path REFUSES any problem —
    this is the boundary gate the self-test mutates against."""
    problems: list[str] = []
    if card.get("candidate") is not True:
        problems.append("candidate must be True — a minted row is born a candidate")
    if card.get("serves_truth") is not False:
        problems.append("serves_truth must be False — generation is never promotion")
    pid = str(card.get("primitive_id") or "")
    if not _STAGED_ID_RE.match(pid):
        problems.append(f"primitive_id {pid!r} is not a {STAGED_ID_PREFIX}-<sha256[:16]> id")
    expected = canonical_id(STAGED_ID_PREFIX, str(card.get("domain") or ""),
                            str(card.get("output_edge") or ""), str(card.get("input_edge") or ""))
    if pid != expected:
        problems.append("primitive_id does not recompute from the card's content (tampered or stale)")
    if not str(card.get("output_edge") or "").strip():
        problems.append("output_edge (the unmet type) is required")
    if not str(card.get("blackbox") or "").strip():
        problems.append("blackbox (the needed transform) is required")
    provenance = card.get("provenance")
    if not isinstance(provenance, dict) or not str(provenance.get("receipt") or "").strip():
        problems.append("provenance.receipt (the benchmark receipt / demand signal) is required")
    return problems


def append_staged_cards(cards: list[dict], staged_path: Path) -> dict[str, Any]:
    """APPEND cards to ``staged_path``, deduped by primitive_id against the lines already there and within
    the batch. Never rewrites existing lines (append-only staging); raises on any card that fails
    validate_staged_card so an invalid card can never reach disk."""
    staged_path = Path(staged_path)
    existing_ids = {str(r.get("primitive_id") or "") for r in read_jsonl_tolerant(staged_path)}
    lines: list[str] = []
    appended = skipped = 0
    for card in cards:
        problems = validate_staged_card(card)
        if problems:
            raise ValueError(f"refusing to stage invalid card {card.get('primitive_id')!r}: {problems}")
        pid = card["primitive_id"]
        if pid in existing_ids:
            skipped += 1
            continue
        existing_ids.add(pid)
        lines.append(serialize_card(card))
        appended += 1
    if lines:
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        with open(staged_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    return {
        "record_type": "staged_producer_append_report",
        "staged_path": str(staged_path),
        "minted": len(cards),
        "appended": appended,
        "skipped_already_staged": skipped,
        "total_staged_lines": len(read_jsonl_tolerant(staged_path)),
        **BOUNDARY,
    }


# ── the run ────────────────────────────────────────────────────────────────────────────────────────────────

def _receipt_ref(summary_path: Path) -> str:
    """Repo-relative reference to the benchmark receipt (falls back to the absolute path outside the repo,
    e.g. the self-test's temp dir). Stable for a stable path — never a timestamp."""
    try:
        return str(Path(summary_path).resolve().relative_to(_sbc))
    except ValueError:
        return str(summary_path)


def run(bench_dir: Path = BENCH_DIR, corpus_path: Path = VERIFIED_CORPUS_PATH) -> dict[str, Any]:
    """Read the benchmark summary + rows and the verified corpus, mint the staged producer candidates, and
    append them (deduped) to the staging file. Returns the append report enriched with the demand read."""
    bench_dir = Path(bench_dir)
    summary_path = bench_dir / SUMMARY_FILENAME
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = read_jsonl_tolerant(bench_dir / ROWS_FILENAME)
    corpus_cards = [c for c in read_jsonl_tolerant(corpus_path) if c.get("primitive_id")]
    cards = mint_producer_candidates(summary, rows, corpus_cards, receipt_ref=_receipt_ref(summary_path))
    report = append_staged_cards(cards, bench_dir / STAGED_FILENAME)
    report["corpus_cards_indexed"] = len(corpus_cards)
    report["unmet_edges_by_domain"] = read_unmet_edges_by_domain(summary)
    return report


# ── self-test (hermetic: synthetic summary + rows + corpus in a temp dir; no real file touched) ────────────

def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def corpus_card(pid: str, inp: str, out: str) -> dict:
        return {"primitive_id": pid, "input_edge": inp, "output_edge": out, "title": f"{inp} -> {out}",
                "kind": STAGED_CARD_KIND, "quality_score": 50, "readiness": "R2_edge_known", **BOUNDARY}

    # synthetic corpus: near-variant producers for two of the unmet types, nothing near the third.
    synth_corpus = [
        corpus_card("p:schema_draft", "RawRecords", "CanonicalSchemaDraft"),
        corpus_card("p:sorted_chunk", "UnsortedItems", "SortedListChunk"),
        corpus_card("p:unrelated", "Pebble", "GravelHeap"),
    ]
    # synthetic summary: the unmet types are READ from this file — including a name that exists nowhere in
    # this module ('TotallyNovelEdgeZzqx'), proving nothing is hardcoded; one healthy domain contributes none.
    synth_summary = {
        "record_type": "synthetic_domain_benchmark",
        "domains": [
            {"domain": "alpha_domain",
             "composition": {"gap_rate": 0.5, "route_found_rate": 0.5,
                             "top_unmet_edges": ["CanonicalSchema", "TotallyNovelEdgeZzqx"]}},
            {"domain": "beta_domain",
             "composition": {"gap_rate": 1.0, "route_found_rate": 0.0, "top_unmet_edges": ["SortedList"]}},
            {"domain": "healthy_domain",
             "composition": {"gap_rate": 0.0, "route_found_rate": 1.0, "top_unmet_edges": []}},
        ],
    }
    # synthetic probe rows: only the novel edge has a recorded demanding probe (its intent is the fallback).
    synth_rows = [
        {"domain": "alpha_domain", "intent": "frobnicate the widget stream",
         "needed_edges": ["TotallyNovelEdgeZzqx"], "route_found": False, **BOUNDARY},
        {"domain": "alpha_domain", "intent": "an unrelated probe", "needed_edges": [""],
         "route_found": False, **BOUNDARY},
    ]

    with tempfile.TemporaryDirectory(prefix="mint_unmet_edge_producers_selftest_") as td:
        bench = Path(td) / "bench"
        bench.mkdir()
        (bench / SUMMARY_FILENAME).write_text(json.dumps(synth_summary, sort_keys=True), encoding="utf-8")
        (bench / ROWS_FILENAME).write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in synth_rows) + "\n", encoding="utf-8")
        corpus_path = Path(td) / "corpus.jsonl"
        corpus_path.write_text(
            "\n".join(json.dumps(c, sort_keys=True) for c in synth_corpus) + "\n", encoding="utf-8")

        # 1) run end-to-end against the temp dir (the SAME code path as --run; hermetic by construction).
        report = run(bench_dir=bench, corpus_path=corpus_path)
        staged_path = bench / STAGED_FILENAME
        staged = read_jsonl_tolerant(staged_path)
        by_output = {c["output_edge"]: c for c in staged}
        checks.append(("mints exactly one card per (domain, unmet type) READ from summary.json — "
                       "3 cards incl. the novel name; the healthy domain contributes none",
                       report["appended"] == 3 and set(by_output) ==
                       {"CanonicalSchema", "TotallyNovelEdgeZzqx", "SortedList"}))

        # 2) nearest-producer match (REUSED edge_type_matcher): the near type becomes the input_edge.
        schema_card = by_output.get("CanonicalSchema", {})
        schema_prov = schema_card.get("provenance", {})
        checks.append(("nearest existing producer supplies input_edge (CanonicalSchemaDraft -> CanonicalSchema) "
                       "and is named in provenance.nearest_producers",
                       schema_card.get("input_edge") == "CanonicalSchemaDraft"
                       and schema_prov.get("input_edge_source") == INPUT_EDGE_FROM_NEAREST_PRODUCER
                       and any(h.get("primitive_id") == "p:schema_draft"
                               for h in schema_prov.get("nearest_producers", []))))

        # 3) fallback: with no near producer, the domain probe's own input becomes the input_edge.
        novel_card = by_output.get("TotallyNovelEdgeZzqx", {})
        checks.append(("with no near producer the domain probe's input is the input_edge (probe intent)",
                       novel_card.get("input_edge") == "frobnicate the widget stream"
                       and novel_card.get("provenance", {}).get("input_edge_source")
                       == INPUT_EDGE_FROM_DOMAIN_PROBE))

        # 4) boundary + provenance law: every card candidate/serves_truth=false, receipt names the summary,
        #    and the demand-signal label is READ from the receipt (never typed).
        checks.append(("every staged card is candidate=true / serves_truth=false with a receipt-bearing "
                       "provenance and the demand signal read from the summary",
                       bool(staged) and all(
                           c.get("candidate") is True and c.get("serves_truth") is False
                           and str(c.get("provenance", {}).get("receipt") or "").endswith(SUMMARY_FILENAME)
                           and c.get("provenance", {}).get("demand_signal") == "synthetic_domain_benchmark"
                           for c in staged)))

        # 5) id discipline: typed prefix + sha256[:16] content hash, recomputable from the card itself.
        checks.append(("ids are prefix + sha256 content hash and recompute from card content",
                       bool(staged) and all(
                           _STAGED_ID_RE.match(str(c.get("primitive_id") or ""))
                           and c["primitive_id"] == canonical_id(STAGED_ID_PREFIX, c["domain"],
                                                                 c["output_edge"], c["input_edge"])
                           for c in staged)))

        # 6) DEDUPE gate: a second identical run appends NOTHING and the file bytes do not change.
        bytes_before = staged_path.read_bytes()
        report2 = run(bench_dir=bench, corpus_path=corpus_path)
        checks.append(("dedupe proven: second run appends 0 (all skipped) and the staged file is byte-identical",
                       report2["appended"] == 0 and report2["skipped_already_staged"] == 3
                       and staged_path.read_bytes() == bytes_before))

        # 7) DETERMINISM gate: two independent mints over the same inputs are byte-identical.
        summary_obj = json.loads((bench / SUMMARY_FILENAME).read_text(encoding="utf-8"))
        rows_obj = read_jsonl_tolerant(bench / ROWS_FILENAME)
        corpus_obj = [c for c in read_jsonl_tolerant(corpus_path) if c.get("primitive_id")]
        mint_a = mint_producer_candidates(summary_obj, rows_obj, corpus_obj, receipt_ref="r/summary.json")
        mint_b = mint_producer_candidates(summary_obj, rows_obj, corpus_obj, receipt_ref="r/summary.json")
        checks.append(("determinism: two mints over the same inputs serialize byte-identically",
                       [serialize_card(c) for c in mint_a] == [serialize_card(c) for c in mint_b]
                       and len(mint_a) == 3))

        # 8) MUTATION gate a: a card whose serves_truth is flipped to True MUST be rejected by the validator
        #    AND refused by the write path (a wrong artifact makes the gate go red — never vacuous).
        tampered = dict(mint_a[0])
        tampered["serves_truth"] = True
        refused = False
        try:
            append_staged_cards([tampered], Path(td) / "tampered.jsonl")
        except ValueError:
            refused = True
        checks.append(("mutation: flipping serves_truth to True is rejected by validate_staged_card and the "
                       "write path refuses it",
                       bool(validate_staged_card(tampered)) and refused
                       and not (Path(td) / "tampered.jsonl").exists()))

        # 8b) MUTATION gate b: tampering the content (output_edge) breaks the id recompute — also refused.
        retyped = dict(mint_a[0])
        retyped["output_edge"] = "SomethingElseEntirely"
        checks.append(("mutation: tampering output_edge breaks the sha256 id recompute and is rejected",
                       any("recompute" in p for p in validate_staged_card(retyped))))

        # 9) MUTATION gate c: corrupting the near producer's output in the corpus changes the minted card —
        #    proving the nearest-producer wire is live (not a hardcoded input_edge).
        broken_corpus = [dict(c) for c in corpus_obj]
        for c in broken_corpus:
            if c["primitive_id"] == "p:schema_draft":
                c["output_edge"] = "ZzqbWobbleNoise"
        mint_broken = mint_producer_candidates(summary_obj, rows_obj, broken_corpus,
                                               receipt_ref="r/summary.json")
        broken_schema = next(c for c in mint_broken if c["output_edge"] == "CanonicalSchema")
        orig_schema = next(c for c in mint_a if c["output_edge"] == "CanonicalSchema")
        checks.append(("mutation: corrupting the near producer's output flips the CanonicalSchema card to the "
                       "generic fallback and changes its content-hash id",
                       broken_schema["input_edge"] == GENERIC_FALLBACK_INPUT_EDGE
                       and broken_schema["provenance"]["input_edge_source"] == INPUT_EDGE_FROM_GENERIC_FALLBACK
                       and broken_schema["primitive_id"] != orig_schema["primitive_id"]))

        # 10) side-by-side guarantee: the run never touches the verified corpus (byte-identical after runs).
        checks.append(("the verified corpus file is never touched (byte-identical after both runs)",
                       corpus_path.read_bytes() == "\n".join(
                           json.dumps(c, sort_keys=True) for c in synth_corpus).encode("utf-8") + b"\n"))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("PASS - mint_unmet_edge_producers: the benchmark's NAMED unmet edges (read from summary.json, never "
          "hardcoded) mint deterministic sha256-id'd STAGED producer candidate cards — input_edge from the "
          "nearest verified producer (reused edge_type_matcher) or the domain probe's input, output_edge the "
          "unmet type, provenance naming the benchmark receipt; append-only with proven dedupe (second run "
          "appends 0), every card candidate/serves_truth=false, and the mutation gates go red on a tampered "
          "card, a broken id recompute, and a corrupted corpus match.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true", help="hermetic proof (synthetic summary+rows+corpus)")
    ap.add_argument("--run", action="store_true",
                    help="mint from the REAL benchmark summary + verified corpus and append (deduped)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        report = run()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
