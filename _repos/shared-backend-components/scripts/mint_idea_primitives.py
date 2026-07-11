#!/usr/bin/env python3
"""scripts.mint_idea_primitives — mint IDEA-primitive candidates across the knowledge axes the owner named:
computational-work types x computer-science categories x software-engineering categories x knowledge domains
(incl. geography/textbook subjects) x systems/indexes x problem->solution shapes. Each card is a REUSABLE-UNIT
IDEA seed whose blackbox NATURALLY carries concrete tokens from every axis (a CS technique + a work verb + a
concrete system/index + a domain + a problem->solution framing + an SWE concern) — substantially richer than
a bare capability-slot template, so the ideas enter the funnel as real leads, not vacuous filler.

Deterministic + governed: the axes are the single source (module constants, promotable to ``vocabularies/``);
the full axis product is computed and STRIDED to hit ``--target`` (~100K by default) with no RNG and no
wall-clock; ids are minted only by ``src.teleon.experiments.ids.canonical_id`` (data-plane law) over
(title, blackbox); every card is born ``candidate=true / serves_truth=false`` (generation is NEVER promotion).
The staged file is a NEW file next to — never equal to — the verified corpus, and the writer refuses any other
target before a byte is written.

NON-DESTRUCTIVE quality (owner law: nothing discarded): after minting, every card is scored by
``primitive_usefulness_gate`` and the placeholder/weak/pass split is REPORTED — flagged cards are ROUTED to the
enrichment queue (``enrich_minted_primitives``), never dropped. A template-shaped idea seed is a lead for
enrichment, and it may serve a different prompt session than any we test.

    PYTHONPATH=. python3 scripts/mint_idea_primitives.py --self-test
    PYTHONPATH=. python3 scripts/mint_idea_primitives.py --mint --target 100000
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/mint_gap_primitives.py) ──────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Iterator, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except Exception as exc:  # noqa: BLE001
    raise SystemExit("scripts.mint_idea_primitives requires src.teleon.experiments.ids.canonical_id "
                     f"(the ONE id authority); import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

IDEA_ID_PREFIX = "prim-idea"
IDEA_RECORD_TYPE = "idea_primitive_candidate"
IDEA_CARD_KIND = "route.primitive"
IDEA_SCHEMA_VERSION = 1
STAGED_FILENAME = "idea_primitive_candidates.jsonl"
#: verified corpus files this minter must NEVER write (single-sourced guard, matches mint_gap_primitives).
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
_READINESS_UNPROVEN = "idea_candidate_unproven"
_PROMOTION_BLOCKERS = ("source_evidence", "correctness_proof", "usefulness_or_enrichment", "license_review")
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")

# ── the AXES (single source; promotable to vocabularies/). Each entry: (key_slug, human_words...). ─────────────
# type of computational work (the verb spine)
_WORK: tuple[tuple[str, str], ...] = (
    ("parse", "parse"), ("transform", "transform"), ("index", "index"), ("search", "search"),
    ("rank", "rank"), ("aggregate", "aggregate"), ("classify", "classify"), ("cluster", "cluster"),
    ("encode", "encode"), ("compress", "compress"), ("validate", "validate"), ("route", "route"),
    ("schedule", "schedule"), ("cache", "cache"), ("replicate", "replicate"), ("reconcile", "reconcile"),
    ("deduplicate", "deduplicate"), ("summarize", "summarize"), ("extract", "extract"),
    ("simulate", "simulate"), ("optimize", "optimize"), ("stream", "stream"),
)
# categories of computer science (the technique + its concept tokens)
_CS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("algorithms", "dynamic-programming algorithm", ("recurrence", "memoization", "subproblem")),
    ("data_structures", "balanced tree structure", ("node", "rotation", "invariant")),
    ("complexity", "complexity-bounded procedure", ("amortized", "bound", "reduction")),
    ("cryptography", "authenticated-encryption scheme", ("nonce", "keystream", "mac")),
    ("distributed_systems", "consensus protocol", ("quorum", "leader", "log")),
    ("databases", "query planner", ("cardinality", "join", "predicate")),
    ("networking", "flow-control mechanism", ("window", "backpressure", "retransmit")),
    ("operating_systems", "scheduler policy", ("preemption", "quantum", "priority")),
    ("compilers", "dataflow analysis", ("lattice", "fixpoint", "liveness")),
    ("machine_learning", "gradient-boosted model", ("feature", "loss", "regularizer")),
    ("computer_graphics", "spatial-partition renderer", ("bvh", "ray", "frustum")),
    ("information_retrieval", "inverted-index retriever", ("posting", "tfidf", "bm25")),
    ("formal_methods", "invariant checker", ("precondition", "assertion", "model")),
    ("concurrency", "lock-free queue", ("cas", "hazard", "epoch")),
    ("computer_vision", "feature-detection pass", ("keypoint", "descriptor", "homography")),
    ("nlp", "sequence tagger", ("token", "span", "label")),
    ("security", "capability-based access gate", ("principal", "scope", "revocation")),
    ("architecture", "cache-coherence protocol", ("line", "snoop", "invalidate")),
    ("numerical_methods", "iterative solver", ("residual", "tolerance", "conditioning")),
    ("graph_theory", "shortest-path search", ("frontier", "relaxation", "heuristic")),
    ("automata", "finite-state recognizer", ("state", "transition", "accepting")),
    ("type_theory", "type-inference engine", ("unification", "constraint", "substitution")),
)
# categories of software engineering (the SWE concern overlay)
_SWE: tuple[tuple[str, str], ...] = (
    ("api_design", "a versioned API surface"), ("testing", "a property-test harness"),
    ("observability", "structured tracing"), ("ci_cd", "a promotion gate"),
    ("refactoring", "a behavior-preserving refactor"), ("data_modeling", "a normalized schema"),
    ("performance", "a hot-path budget"), ("deployment", "a blue-green rollout"),
    ("incident_response", "a runbook and alert"), ("dependency_mgmt", "a pinned dependency set"),
    ("documentation", "a worked example"), ("migration", "an online backfill"),
    ("feature_flags", "a guarded rollout flag"), ("code_review", "a review checklist"),
    ("resilience", "a retry-with-backoff policy"), ("config_mgmt", "a typed config surface"),
)
# knowledge domains — incl. geography and textbook subjects (the owner's "geography / textbooks" axis)
_DOMAIN: tuple[tuple[str, str], ...] = (
    ("geography", "geospatial routing tables"), ("logistics", "supply-chain shipments"),
    ("healthcare_admin", "provider directories"), ("education", "course catalogs"),
    ("finance_ops", "ledger reconciliations"), ("ecommerce", "product catalogs"),
    ("telecom", "call-detail records"), ("legal_ops", "contract clause libraries"),
    ("scientific_computing", "simulation grids"), ("civic_data", "public-records registries"),
    ("climate", "sensor time-series"), ("bioinformatics", "sequence alignments"),
    ("astronomy", "sky-survey catalogs"), ("linguistics", "annotated corpora"),
    ("economics", "input-output tables"), ("transportation", "transit schedules"),
    ("energy", "grid telemetry"), ("agriculture", "yield surveys"),
    ("manufacturing", "bill-of-materials trees"), ("cybersecurity", "threat-intel feeds"),
    ("real_estate", "parcel records"), ("sports_analytics", "play-by-play logs"),
    ("media", "content metadata"), ("textbook_cs", "algorithms-textbook exercises"),
)
# systems / indexes (the concrete substrate the work runs on)
_SYSTEM: tuple[tuple[str, str], ...] = (
    ("inverted_index", "an inverted index"), ("btree", "a B-tree index"), ("lsm_tree", "an LSM-tree store"),
    ("hash_index", "a hash index"), ("vector_index", "a vector index"), ("message_queue", "a message queue"),
    ("event_bus", "an event bus"), ("state_machine", "a state machine"), ("dag_scheduler", "a DAG scheduler"),
    ("cache_tier", "a cache tier"), ("cdc_pipeline", "a CDC pipeline"), ("bloom_filter", "a Bloom filter"),
    ("consensus_log", "a consensus log"), ("columnar_store", "a columnar store"),
    ("graph_store", "a graph store"), ("trie", "a trie"),
)
# problem -> solution shapes (the reason the primitive exists)
_PROBLEM_SOLUTION: tuple[tuple[str, str, str], ...] = (
    ("dupes", "duplicate records inflate the set", "collapse them into canonical clusters"),
    ("unstructured", "the input is unstructured text", "extract a typed, validated record"),
    ("slow_scan", "a full scan is too slow", "serve it from a precomputed index"),
    ("drift", "state drifts out of sync", "reconcile against a source of truth"),
    ("cost", "per-call cost is too high", "cascade to a cheaper deterministic path"),
    ("staleness", "cached facts go stale", "propagate changes via change-data-capture"),
    ("ambiguity", "entities are ambiguous", "resolve them with blocking and scoring"),
    ("overload", "load spikes overwhelm it", "shed and schedule under a budget"),
    ("opacity", "the result is unexplained", "attach provenance and a receipt"),
    ("fragility", "one failure cascades", "isolate with retries and a circuit breaker"),
    ("skew", "the distribution is skewed", "rebalance partitions by key"),
    ("unverifiable", "the output is unverifiable", "gate it behind a checkable proof"),
)

_STOP = frozenset("a an the for of to in on with and or via using into from as is are be that this it one".split())

#: blackbox sentence FRAMES — cycled by axis so the 100K mint does not collapse to one skeleton (measured:
#: a single frame stamped ~20% of a 100K mint; 8 varied frames spread the skeleton mass). Every frame carries
#: the same fills so validate_idea_card's substance check holds regardless of which frame a card draws.
#: fills: {cs}=cs_phrase {a_cs}=article+cs_phrase {work}=work_word {dom}=dom_phrase {sys}=sys_phrase
#: {problem} {solution} {swe}=swe_phrase {toks}=cs concept tokens.
_FRAMES: tuple[str, ...] = (
    "A reusable primitive that uses {a_cs} to {work} {dom} over {sys}: when {problem}, {solution}. "
    "Packages the work as {swe} so it composes as a typed unit. Concepts: {toks}.",
    "Given {dom} on {sys}, this unit applies {a_cs} to {work} them — because {problem}, it will {solution}. "
    "Ships with {swe}. Key concepts: {toks}.",
    "To {work} {dom} where {problem}, this primitive {solution} using {cs} on {sys}, exposed through {swe}. "
    "It leans on {toks}.",
    "{cs}, adapted to {work} {dom} over {sys}. The idea: {problem}, so {solution}. Delivered with {swe}; "
    "built around {toks}.",
    "A {work} unit for {dom}: it runs {cs} against {sys} to handle the case where {problem} by making it "
    "{solution}. Wrapped in {swe}. Concepts: {toks}.",
    "This component {work}s {dom} by pairing {a_cs} with {sys}. When {problem} it will {solution}, and it "
    "surfaces {swe}. Underlying concepts: {toks}.",
    "Idea: take {cs} and point it at {dom} on {sys} to {work} them. Rationale — {problem}; resolution — "
    "{solution}. Includes {swe}. Rests on {toks}.",
    "Reusable {work} primitive over {sys} for {dom}, implemented as {cs} and framed by {swe}. It exists "
    "because {problem}; it responds by {solution}. Concepts: {toks}.",
)


def axis_sizes() -> dict[str, int]:
    return {"work": len(_WORK), "cs": len(_CS), "swe": len(_SWE), "domain": len(_DOMAIN),
            "system": len(_SYSTEM), "problem_solution": len(_PROBLEM_SOLUTION)}


def full_product_size() -> int:
    s = axis_sizes()
    return s["work"] * s["cs"] * s["swe"] * s["domain"] * s["system"] * s["problem_solution"]


def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    return "".join(p[:1].upper() + p[1:] for p in parts if p) or "X"


def _tokens(cs_toks: tuple[str, ...], work_slug: str, system_slug: str, domain_slug: str) -> list[str]:
    """The concept tokens the card naturally carries (the verified-coverage contract shape)."""
    seen: list[str] = []
    for t in (work_slug, *cs_toks, system_slug.replace("_", " "), domain_slug.replace("_", " ")):
        for w in str(t).split():
            wl = w.lower()
            if wl not in _STOP and wl not in seen:
                seen.append(wl)
    return seen


def _idea(indices: tuple[int, int, int, int, int, int]) -> dict[str, Any]:
    wi, ci, si, di, yi, pi = indices
    work_slug, work_word = _WORK[wi]
    cs_slug, cs_phrase, cs_toks = _CS[ci]
    swe_slug, swe_phrase = _SWE[si]
    dom_slug, dom_phrase = _DOMAIN[di]
    sys_slug, sys_phrase = _SYSTEM[yi]
    ps_slug, problem, solution = _PROBLEM_SOLUTION[pi]

    title = f"{work_word.capitalize()} {dom_phrase} with {cs_phrase} over {sys_phrase}"
    # frame chosen deterministically from the axes so the skeleton mass spreads across all 8 frames
    frame = _FRAMES[(wi * 5 + ci * 3 + pi * 7 + yi) % len(_FRAMES)]
    blackbox = frame.format(cs=cs_phrase, a_cs=a_an(cs_phrase), work=work_word, dom=dom_phrase,
                            sys=sys_phrase, problem=problem, solution=solution, swe=swe_phrase,
                            toks=", ".join(cs_toks))
    tokens = _tokens(cs_toks, work_slug, sys_slug, dom_slug)
    input_edge = _camel(dom_slug, ps_slug, "input")
    output_edge = _camel(work_slug, sys_slug, "result")
    pid = canonical_id(IDEA_ID_PREFIX, title, blackbox)
    return {
        "record_type": IDEA_RECORD_TYPE, "schema_version": IDEA_SCHEMA_VERSION, "kind": IDEA_CARD_KIND,
        "primitive_id": pid, "title": title, "blackbox": blackbox,
        "input_edge": input_edge, "output_edge": output_edge, "blocking_keys": tokens,
        "capability_tags": [f"cs:{cs_slug}", f"swe:{swe_slug}", f"work:{work_slug}", f"domain:{dom_slug}",
                            f"system:{sys_slug}"],
        "contract": {"input": f"{problem} in {dom_phrase} (concepts: {', '.join(tokens)})",
                     "output": f"{solution}; a typed {work_word} result over {sys_phrase}"},
        "axes": {"work": work_slug, "cs": cs_slug, "swe": swe_slug, "domain": dom_slug,
                 "system": sys_slug, "problem_solution": ps_slug},
        "readiness": _READINESS_UNPROVEN, "promotion_blockers": list(_PROMOTION_BLOCKERS),
        "provenance": {"minter": "scripts.mint_idea_primitives", "axis_product": full_product_size()},
        **BOUNDARY,
    }


def a_an(phrase: str) -> str:
    return ("an " if phrase[:1].lower() in "aeiou" else "a ") + phrase


def _strided_indices(target: int) -> Iterator[tuple[int, int, int, int, int, int]]:
    """Walk the full 6-axis product on a fixed stride so ``target`` cards are spread evenly across every axis,
    deterministically (no RNG). Coprime-ish stride via total//target; a co-runner offset is not needed."""
    total = full_product_size()
    step = max(1, total // max(1, target))
    sizes = [len(_WORK), len(_CS), len(_SWE), len(_DOMAIN), len(_SYSTEM), len(_PROBLEM_SOLUTION)]
    count = 0
    for flat in range(0, total, step):
        if count >= target:
            break
        idx = []
        rem = flat
        for sz in reversed(sizes):
            idx.append(rem % sz)
            rem //= sz
        yield tuple(reversed(idx))  # type: ignore[misc]
        count += 1


def mint_ideas(target: int) -> list[dict[str, Any]]:
    """Mint ~``target`` idea cards, deterministic over the axes. Ids are content-hashed; a collision (two axis
    tuples yielding identical title+blackbox) raises rather than silently collapsing the count."""
    if target < 1:
        raise ValueError("target must be >= 1")
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for indices in _strided_indices(target):
        card = _idea(indices)
        if card["primitive_id"] in seen:
            raise ValueError(f"duplicate idea mint for title {card['title']!r} — axis collision")
        seen.add(card["primitive_id"])
        cards.append(card)
    return cards


def validate_idea_card(card: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if card.get("primitive_id") != canonical_id(IDEA_ID_PREFIX, card.get("title", ""), card.get("blackbox", "")):
        problems.append("primitive_id does not recompute from title+blackbox")
    for ef in ("input_edge", "output_edge"):
        if not _CAMEL_EDGE_RE.match(str(card.get(ef) or "")):
            problems.append(f"{ef} must be CamelCase")
    if not card.get("blocking_keys"):
        problems.append("blocking_keys empty")
    if card.get("serves_truth") is not False or card.get("candidate") is not True:
        problems.append("candidate boundary not stamped")
    # substance: the blackbox must carry the cs concepts + work verb + domain words (not a bare slot)
    text = f"{card.get('title','')} {card.get('blackbox','')}".lower()
    if not all(t in text for t in card.get("blocking_keys", [])[:3]):
        problems.append("blackbox does not naturally carry its leading concept tokens")
    return problems


def staged_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / STAGED_FILENAME


def write_staged(cards: list[dict[str, Any]], target_path: Optional[Path] = None) -> dict[str, Any]:
    """APPEND cards to the idea-staged file, deduped by primitive_id (a re-run appends nothing). HARD GATE:
    the resolved real target must carry STAGED_FILENAME, must not be a symlink, and must never equal a
    verified corpus file — any other target is refused before a byte is written."""
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = target_path or staged_path()
    if p.name != STAGED_FILENAME:
        raise ValueError(f"refusing to write idea cards to {p.name!r} — only {STAGED_FILENAME!r} is allowed")
    if p.is_symlink():
        raise ValueError(f"refusing to write through a symlink at {p}")
    if p.exists():
        real = p.resolve()
        if real.name in _VERIFIED_CORPUS_FILENAMES or real.name != STAGED_FILENAME:
            raise ValueError(f"resolved target {real} is not the staged file — refused")
    for c in cards:
        probs = validate_idea_card(c)
        if probs:
            raise ValueError(f"card {c.get('primitive_id')} failed validation: {probs}")
    existing = {str(r.get("primitive_id")) for r in (read_jsonl_tolerant(p) if p.exists() else [])}
    appended = 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for c in cards:
            pid = str(c["primitive_id"])
            if pid in existing:
                continue
            existing.add(pid)
            fh.write(json.dumps(c, sort_keys=True) + "\n")
            appended += 1
    return {"appended": appended, "path": str(p), "on_file": len(existing), **BOUNDARY}


def quality_report(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Score the minted ideas with the usefulness gate (NON-DESTRUCTIVE routing signal, never a filter).
    Reports the placeholder/weak/pass split so quality is honest; flagged cards route to enrichment."""
    from scripts.primitive_usefulness_gate import measure_pool  # noqa: PLC0415
    m = measure_pool(cards, "idea_primitive_mint")
    return {k: m[k] for k in ("n_cards_scored", "placeholder_rate", "weak_rate", "verdict_counts",
                              "criterion_rates", "stamped_clusters")}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = mint_ideas(500)
    checks.append(("mints the requested count deterministically", len(cards) == 500))
    checks.append(("byte-identical remint (no RNG / no wall-clock)",
                   json.dumps(cards, sort_keys=True) == json.dumps(mint_ideas(500), sort_keys=True)))
    checks.append(("every id recomputes from canonical_id over title+blackbox",
                   all(c["primitive_id"] == canonical_id(IDEA_ID_PREFIX, c["title"], c["blackbox"]) for c in cards)))
    checks.append(("ids are unique across the mint", len({c["primitive_id"] for c in cards}) == len(cards)))
    checks.append(("edges are CamelCase typed names",
                   all(_CAMEL_EDGE_RE.match(c["input_edge"]) and _CAMEL_EDGE_RE.match(c["output_edge"]) for c in cards)))
    checks.append(("every card passes validate_idea_card (substance + boundary)",
                   all(not validate_idea_card(c) for c in cards)))
    checks.append(("every card is candidate/serves_truth=false",
                   all(c["candidate"] is True and c["serves_truth"] is False for c in cards)))
    # axis breadth: a 500-card stride still touches many categories on every axis
    def _distinct(axis: str) -> int:
        return len({c["axes"][axis] for c in cards})
    checks.append(("the stride spreads across axes (>=8 CS categories, >=8 domains in 500)",
                   _distinct("cs") >= 8 and _distinct("domain") >= 8 and _distinct("work") >= 8))
    checks.append(("count is COMPUTED from the axes, never typed (product is large)",
                   full_product_size() == len(_WORK) * len(_CS) * len(_SWE) * len(_DOMAIN)
                   * len(_SYSTEM) * len(_PROBLEM_SOLUTION) and full_product_size() > 1_000_000))
    # write-staged safety: refuse a verified corpus filename outright
    import tempfile  # noqa: PLC0415
    refused = False
    try:
        write_staged(cards[:1], target_path=Path(tempfile.gettempdir()) / "verified_factory_primitive_cards.jsonl")
    except ValueError:
        refused = True
    checks.append(("write_staged REFUSES a verified corpus filename", refused))
    # write-staged append-dedupe on a tmp file with the correct name
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / STAGED_FILENAME
        a = write_staged(cards[:50], target_path=tp)
        b = write_staged(cards[:50], target_path=tp)
        checks.append(("append-dedupe: first writes N, second writes 0 (byte-stable)",
                       a["appended"] == 50 and b["appended"] == 0))
    # substance vs a bare slot: the gate should NOT flag these on no_concrete_token as hard as a bare template
    qr = quality_report(cards)
    checks.append(("quality report runs and is a routing signal (has verdict split)",
                   set(qr["verdict_counts"]) == {"pass", "weak", "placeholder"}))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - mint_idea_primitives: deterministic axis-strided idea mint (full product "
          f"{full_product_size():,}); canonical ids recompute; CamelCase edges; substance-validated; "
          f"candidate/serves_truth=false; write refuses verified corpus files; usefulness gate scores the "
          f"mint as a NON-DESTRUCTIVE routing signal. Generation is not promotion. serves_truth=false.")
    return 0


def _mint(target: int) -> int:
    cards = mint_ideas(target)
    qr = quality_report(cards)
    wrote = write_staged(cards)
    rec = {"record_type": "idea_primitive_mint_receipt", "schema_version": 1,
           "target": target, "minted": len(cards), "appended": wrote["appended"], "on_file": wrote["on_file"],
           "axis_sizes": axis_sizes(), "full_product_size": full_product_size(),
           "distinct_axis_values": {ax: len({c["axes"][ax] for c in cards}) for ax in
                                    ("work", "cs", "swe", "domain", "system", "problem_solution")},
           "quality_gate": qr,
           "routing": "placeholder/weak cards route to scripts.enrich_minted_primitives; NONE discarded",
           **BOUNDARY}
    out = resource("data") / "dev-intel" / "session_emulation" / "idea_primitive_mint_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("target", "minted", "appended", "on_file",
                                          "distinct_axis_values", "quality_gate")}, indent=2, sort_keys=True))
    print(f"\nstaged: {wrote['path']}\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mint", action="store_true")
    ap.add_argument("--target", type=int, default=100_000, help="approx number of idea cards to mint")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.mint:
        return _mint(args.target)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
