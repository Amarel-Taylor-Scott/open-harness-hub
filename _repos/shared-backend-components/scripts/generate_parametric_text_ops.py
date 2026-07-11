#!/usr/bin/env python3
"""scripts.generate_parametric_text_ops — WORKABLE configured-primitives for the 'text_ops' group by PARAMETRIC PROOF.

A vocabulary of proven mutator TEMPLATES (ts_replace, ts_ljust/rjust/center/zero_pad, ts_truncate[_ellipsis],
ts_slugify, ts_split, ts_normalize_whitespace) is only a handful of callables. This module turns each proven
TEMPLATE into MANY distinct WORKABLE primitives by crossing it with a curated, deterministic parameter BINDING space
(different field-sets / widths / fills / lengths / ellipses / delimiters / realistic fixtures) — each pairing is a
SEPARATE configured-primitive, e.g. ts_replace{old:'o',new:'0'} and ts_replace{old:' ',new:'-'} are DISTINCT.

Honesty law (repo, violations reverted): serves_truth=true is set ONLY by an executed PASSING proof of THAT binding —
we EXECUTE the mutator on the fixture to compute the expected output, then re-run it through the imported
`run_primitive_proof` (which re-executes + checks fixture-behavior + determinism, and flips serves_truth false->true
ONLY on pass); a binding that fails is NEVER persisted as truth. Counts are kept SEPARATE and never conflated:
generated (enumerated triples) vs unique (after content-hash dedupe) vs proven (executed-proof passers) vs typed
(passers carrying BOTH canonical edge type ids). Rows are efficient TEMPLATE+BINDING records — NOT bloated static
files.

ADD-ONLY / flexible: a NEW parallel path. It IMPORTS the machinery (_repos/shared-backend-components/scripts/mutator_registry.py,
_repos/shared-backend-components/scripts/prove_leaves_text_string.py which registers the text templates, _repos/shared-backend-components/scripts/build_edge_type_retrofit.py) and never
edits it; it does NOT register itself in flywheel_proof_modules.py (that tuple is REPORTED). Each agent writes its OWN
shard file (no shared-JSONL write race). Deterministic + offline ONLY: no network, no LLM, no wall-clock (fixed literal
timestamp), no RNG (the parameter space is enumerated deterministically; pseudo-variety uses stable string seeds like
f"{group}:{i}", never hash()). CLI: --self-test | --write.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the machinery — never edit it (ADD-ONLY). Base registry always available.
from scripts.mutator_registry import MUTATOR_REGISTRY, apply_mutator, run_primitive_proof  # noqa: E402
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

# The text templates live in the sibling prover, which registers them into the shared MUTATOR_REGISTRY on import.
# try/except so --self-test still runs if that sibling is ever absent (we then only build templates that resolved).
try:  # pragma: no cover - exercised by presence/absence in the tree
    import scripts.prove_leaves_text_string as _text_leaves  # noqa: F401  (import triggers registration)
    _TEXT_TEMPLATES_AVAILABLE = True
except Exception:  # noqa: BLE001
    _TEXT_TEMPLATES_AVAILABLE = False

GROUP = "text_ops"
FAMILY = GROUP
# fixed literal timestamp — NO wall-clock (deterministic + offline law).
GENERATED_UTC = "2026-07-03T00:00:00Z"

OUT_DIR = _resource("data") / "dev-intel" / "parametric_primitives"
OUT_JSONL = OUT_DIR / "param_text_ops.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_text_ops.json"

# tuple this module contributes to the shared proof registry (REPORTED, not self-registered).
REGISTER_TUPLE = ("scripts/generate_parametric_text_ops.py", "scripts.generate_parametric_text_ops")


# ── curated, deterministic parameter spaces (meaningfully-distinct behaviors, not trivial noise) ──
# replace: old->new token pairs. Fixtures are BUILT to embed `old` so the replacement actually fires.
_REPLACE_OLD = [
    " ", "-", "_", ",", ".", ";", ":", "/", "o", "a", "e", "l",
    "0", "1", "&", "@", "#", "http", "www", "  ", "\t", "'",
]
_REPLACE_NEW = ["", "-", "_", " ", "+", "0", "X", ".", "/", "*"]

# pad: justify to a width with a fill char. Fixtures are SHORT (len<=2) so width>=3 always makes the fill matter.
_PAD_WIDTHS = [3, 5, 8, 10, 12, 16, 20, 24, 32, 40]
_PAD_FILLS = [" ", "0", "-", "*", ".", "_", "x", "#"]
_PAD_FIXTURES = ["5", "hi", "OK"]
_ZERO_PAD_FIXTURES = ["42", "7", "100", "8"]

# truncate: hard/ellipsis cut to a length. Fixtures are LONG (>32) so every maxlen truncates.
_TRUNC_MAXLENS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20, 24, 32]
_TRUNC_ELLIPSES = [".", "..", "...", "…", " ->", " (more)"]
_TRUNC_FIXTURES = [
    "hello world foo bar baz qux quux corge grault garply",
    "The quick brown fox jumps over the lazy dog again",
    "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMN",
]

# split: cut on a delimiter (Text -> Collection). Fixtures are BUILT to embed the delimiter.
_SPLIT_SEPS = [",", ";", "|", " ", "-", "_", ":", "/", ".", "::", ", ", " - ", "||", "\t", "="]

# slugify / normalize_ws take NO args — variety comes from a curated, deterministic corpus of realistic messy inputs.
_SLUG_LEAD = ["Ultimate", "Quick", "Modern", "Deep", "Simple", "Advanced", "Practical", "Complete", "Essential", "Hidden"]
_SLUG_KIND = ["Guide", "Handbook", "Recipe", "Toolkit", "Playbook", "Blueprint", "Primer", "Cheatsheet", "Roadmap", "Manifesto"]
_SLUG_TOPIC = ["Python", "Rust", "Postgres", "Kubernetes", "Vector Search", "Machine Learning",
               "Data Pipelines", "Edge Computing", "Observability", "Cost Control"]
_NWS_WORD_A = ["hello", "the", "raw", "user", "input", "config", "system", "final", "quick", "clean"]
_NWS_WORD_B = ["world", "quick", "brown", "value", "field", "record", "output", "answer", "result", "state"]
_NWS_WORD_C = ["today", "again", "now", "here", "done", "ready", "fixed", "parsed", "merged", "typed"]
_NWS_GAPS = ["   ", "\t", " \t ", "\n", "  \n  ", "\t\t", " \n\t ", "    "]

# stable string-seed derivation (deterministic; NEVER hash()) — used only to pick curated tokens by index.
def _seed_index(seed: str, modulus: int) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulus


def _replace_fixtures(old: str) -> list[str]:
    return [f"alpha{old}beta{old}gamma", f"lead{old}tail", f"{old}x{old}y{old}z{old}"]


def _split_fixtures(sep: str) -> list[str]:
    return [f"a{sep}b{sep}c", f"one{sep}two{sep}three{sep}four", f"{sep}x{sep}y{sep}"]


# a candidate configured-primitive: (mutator, binding, fixture, input_edge, output_edge). NO proof yet.
def enumerate_candidates() -> list[dict[str, Any]]:
    """Deterministically enumerate the FULL curated parameter space -> candidate configured-primitives."""
    cands: list[dict[str, Any]] = []

    def add(mutator: str, binding: dict[str, Any], fixture: Any, in_edge: str, out_edge: str) -> None:
        if mutator not in MUTATOR_REGISTRY:  # template unavailable (sibling absent) -> skip, stay honest
            return
        cands.append({"mutator": mutator, "binding": binding, "fixture": fixture,
                      "input_edge": in_edge, "output_edge": out_edge})

    # replace
    for old, new in itertools.product(_REPLACE_OLD, _REPLACE_NEW):
        if old == new:
            continue
        for fx in _replace_fixtures(old):
            add("ts_replace", {"old": old, "new": new}, fx, "Text", "Text")

    # pad (ljust/rjust/center take width+fill; zero_pad takes width only)
    for mut in ("ts_ljust", "ts_rjust", "ts_center"):
        for width, fill in itertools.product(_PAD_WIDTHS, _PAD_FILLS):
            for fx in _PAD_FIXTURES:
                add(mut, {"width": width, "fill": fill}, fx, "Text", "Text")
    for width in _PAD_WIDTHS:
        for fx in _ZERO_PAD_FIXTURES:
            add("ts_zero_pad", {"width": width}, fx, "Text", "Text")

    # truncate
    for maxlen in _TRUNC_MAXLENS:
        for fx in _TRUNC_FIXTURES:
            add("ts_truncate", {"maxlen": maxlen}, fx, "Text", "Text")
    for maxlen, ell in itertools.product(_TRUNC_MAXLENS, _TRUNC_ELLIPSES):
        for fx in _TRUNC_FIXTURES:
            add("ts_truncate_ellipsis", {"maxlen": maxlen, "ellipsis": ell}, fx, "Text", "Text")

    # split (Text -> Collection)
    for sep in _SPLIT_SEPS:
        for fx in _split_fixtures(sep):
            add("ts_split", {"sep": sep}, fx, "Text", "Collection")

    # slugify (Text -> TextSlug) — curated realistic titles (first 250 of the product space)
    for i, (lead, kind, topic) in enumerate(itertools.product(_SLUG_LEAD, _SLUG_KIND, _SLUG_TOPIC)):
        if i >= 250:
            break
        fixture = f"The {lead} {kind} to {topic}: Tips, Tricks & More! (#{i})"
        add("ts_slugify", {}, fixture, "Text", "TextSlug")

    # normalize_ws (Text -> Text) — curated messy-whitespace corpus (160 distinct deterministic inputs)
    for i in range(160):
        a = _NWS_WORD_A[_seed_index(f"{GROUP}:nws:a:{i}", len(_NWS_WORD_A))]
        b = _NWS_WORD_B[_seed_index(f"{GROUP}:nws:b:{i}", len(_NWS_WORD_B))]
        c = _NWS_WORD_C[_seed_index(f"{GROUP}:nws:c:{i}", len(_NWS_WORD_C))]
        g1 = _NWS_GAPS[_seed_index(f"{GROUP}:nws:g1:{i}", len(_NWS_GAPS))]
        g2 = _NWS_GAPS[_seed_index(f"{GROUP}:nws:g2:{i}", len(_NWS_GAPS))]
        fixture = f"  {a}{g1}{b}{g2}{c}  "
        add("ts_normalize_whitespace", {}, fixture, "Text", "Text")

    return cands


# ── canonical content hash over (mutator, binding, fixture) so identical bindings collapse ──
def _canonical_hash(mutator: str, binding: dict[str, Any], fixture: Any) -> str:
    payload = json.dumps({"m": mutator, "b": binding, "f": fixture}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _prove_and_type(cand: dict[str, Any]) -> dict[str, Any] | None:
    """EXECUTE the mutator to compute expected, re-prove via run_primitive_proof, TYPE via canonicalize_edge.

    Returns a persist-ready TEMPLATE+BINDING row iff the executed proof PASSES (serves_truth=true); else None.
    """
    mutator, binding, fixture = cand["mutator"], cand["binding"], cand["fixture"]
    try:
        expected, _ = apply_mutator(mutator, fixture, **binding)  # execute once -> expected output
    except Exception:  # noqa: BLE001  (bad binding/fixture -> not provable, drop honestly)
        return None
    receipt = run_primitive_proof(f"prim:param:{mutator}", mutator, fixture, expected, mutator_args=binding)
    if receipt["serves_truth"] is not True:  # a failing binding is NOT persisted as truth
        return None
    sha16 = _canonical_hash(mutator, binding, fixture)
    in_tid = canonicalize_edge(cand["input_edge"])
    out_tid = canonicalize_edge(cand["output_edge"])
    return {
        "primitive_id": f"prim:param:{mutator}:{sha16}",
        "mutator": mutator,
        "binding": binding,
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": cand["input_edge"],
        "output_edge": cand["output_edge"],
        "input_edge_type_id": in_tid,
        "output_edge_type_id": out_tid,
        "fixture_input": fixture,
        "expected_output": expected,
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
        "content_hash": sha16,
    }


def build(candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """The honest pipeline: enumerate -> dedupe -> execute-prove -> type. Returns SEPARATE counts + the rows."""
    cands = candidates if candidates is not None else enumerate_candidates()
    generated = len(cands)

    # DEDUPE by canonical content hash over (mutator, binding, fixture) BEFORE proving (collapse identical work).
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for c in cands:
        h = _canonical_hash(c["mutator"], c["binding"], c["fixture"])
        if h in seen:
            continue
        seen.add(h)
        unique.append(c)

    # EXECUTE-PROVE + TYPE each unique candidate; keep ONLY passers.
    rows: list[dict[str, Any]] = []
    for c in unique:
        row = _prove_and_type(c)
        if row is not None:
            rows.append(row)
    rows.sort(key=lambda r: r["primitive_id"])
    # dedupe again on primitive_id in case two distinct triples ever hash-collide (paranoia; keeps ids unique)
    by_id: dict[str, dict[str, Any]] = {}
    for r in rows:
        by_id.setdefault(r["primitive_id"], r)
    rows = sorted(by_id.values(), key=lambda r: r["primitive_id"])

    proven = len(rows)
    typed = sum(1 for r in rows
                if r["input_edge_type_id"] and r["input_edge_type_id"] != "Unknown"
                and r["output_edge_type_id"] and r["output_edge_type_id"] != "Unknown")
    return {
        "generated": generated,
        "unique_after_dedupe": len(unique),
        "proven": proven,
        "typed": typed,
        "rows": rows,
    }


def build_manifest(result: dict[str, Any]) -> dict[str, Any]:
    rows = result["rows"]
    per_mutator: dict[str, int] = {}
    for r in rows:
        per_mutator[r["mutator"]] = per_mutator.get(r["mutator"], 0) + 1
    return {
        "record_type": "parametric_text_ops_manifest",
        "pack_id": "parametric-text-ops",
        "generator": "scripts/generate_parametric_text_ops.py",
        "group": GROUP,
        "family": FAMILY,
        "generated_utc": GENERATED_UTC,
        # SEPARATE counts — NEVER conflated (generated lines are not active primitives).
        "generated": result["generated"],
        "unique_after_dedupe": result["unique_after_dedupe"],
        "proven": result["proven"],
        "typed": result["typed"],
        "verification_level": "L7_executed_proof",
        "templates": sorted(per_mutator),
        "proven_per_template": dict(sorted(per_mutator.items())),
        "text_templates_available": _TEXT_TEMPLATES_AVAILABLE,
        "row_counts": {OUT_JSONL.name: result["proven"]},
        "register_tuple": list(REGISTER_TUPLE),
        "note": "Each row is a configured-primitive = (proven mutator TEMPLATE) x (specific parameter BINDING) x "
                "(canonical edge types). serves_truth=true is set ONLY by an executed PASSING proof of THAT binding "
                "(run_primitive_proof); a failing binding is dropped, never persisted. Counts are separate: "
                "generated (enumerated) vs unique (deduped) vs proven (executed-proof passers) vs typed (both edge "
                "type ids). Rows are efficient TEMPLATE+BINDING records, not bloated static files.",
    }


def write_pack() -> dict[str, Any]:
    result = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in result["rows"]),
        encoding="utf-8")
    manifest = build_manifest(result)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# ── small, standalone, offline self-test ──
def _small_space() -> list[dict[str, Any]]:
    small: list[dict[str, Any]] = []
    for old, new in [(" ", "-"), ("o", "0"), (",", ";")]:
        small.append({"mutator": "ts_replace", "binding": {"old": old, "new": new},
                      "fixture": f"a{old}b{old}c", "input_edge": "Text", "output_edge": "Text"})
    for width in (5, 8):
        small.append({"mutator": "ts_ljust", "binding": {"width": width, "fill": "-"},
                      "fixture": "hi", "input_edge": "Text", "output_edge": "Text"})
    small.append({"mutator": "ts_truncate", "binding": {"maxlen": 5},
                  "fixture": "hello world foo bar", "input_edge": "Text", "output_edge": "Text"})
    small.append({"mutator": "ts_split", "binding": {"sep": ","},
                  "fixture": "a,b,c", "input_edge": "Text", "output_edge": "Collection"})
    small.append({"mutator": "ts_slugify", "binding": {},
                  "fixture": "Hello, World!", "input_edge": "Text", "output_edge": "TextSlug"})
    return small


def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    if not _TEXT_TEMPLATES_AVAILABLE:
        # honest degrade: sibling absent -> text templates not registered; nothing to prove, but the module still runs.
        print("PASS - generate_parametric_text_ops: text templates sibling absent; module imports the BASE registry "
              f"only and enumerated 0 text candidates (honest degrade). Register tuple: {REGISTER_TUPLE}.")
        return 0

    # 1. a small enumeration proves + types correctly
    small = _small_space()
    res = build(small)
    checks.append(("small space proves every well-formed binding",
                   res["proven"] == len(small) and res["generated"] == len(small)))
    checks.append(("every proven row carries BOTH canonical edge type ids + serves_truth=true",
                   res["typed"] == res["proven"] and all(
                       r["serves_truth"] is True and r["candidate"] is False
                       and r["input_edge_type_id"] and r["input_edge_type_id"] != "Unknown"
                       and r["output_edge_type_id"] and r["output_edge_type_id"] != "Unknown"
                       for r in res["rows"])))
    checks.append(("verification_level is L7_executed_proof on every row",
                   all(r["verification_level"] == "L7_executed_proof" for r in res["rows"])))
    checks.append(("edge typing is correct (split -> Collection, slugify -> TextSlug)",
                   all(r["output_edge_type_id"] == "Collection" for r in res["rows"] if r["mutator"] == "ts_split")
                   and all(r["output_edge_type_id"] == "TextSlug" for r in res["rows"] if r["mutator"] == "ts_slugify")))

    # 2. DEDUPE collapses an identical binding (inject an exact duplicate of the first candidate)
    dup_space = small + [dict(small[0])]
    res_dup = build(dup_space)
    checks.append(("dedupe collapses an identical (mutator,binding,fixture) triple",
                   res_dup["generated"] == len(small) + 1
                   and res_dup["unique_after_dedupe"] == len(small)
                   and res_dup["proven"] == len(small)))

    # 3. a deliberately-WRONG expected FAILS the proof and is never persisted
    bad = run_primitive_proof("prim:param:ts_replace:BAD", "ts_replace", "a b c", "WRONG-OUTPUT",
                              mutator_args={"old": " ", "new": "-"})
    checks.append(("a wrong-expected binding fails the executed proof (not promoted)",
                   bad["serves_truth"] is False and bad["promoted"] is False))
    bad_row = _prove_and_type({"mutator": "ts_ljust", "binding": {"width": 5, "fill": "-"},
                               "fixture": object(), "input_edge": "Text", "output_edge": "Text"})
    checks.append(("an un-runnable fixture yields no persisted row", bad_row is None))

    # 4. determinism: re-running the small build yields identical rows
    res2 = build(small)
    checks.append(("deterministic: identical rows on re-run",
                   [json.dumps(r, sort_keys=True) for r in res["rows"]]
                   == [json.dumps(r, sort_keys=True) for r in res2["rows"]]))

    # 5. distinct bindings of the SAME template are DISTINCT primitives (different ids)
    ids = {r["primitive_id"] for r in res["rows"]}
    checks.append(("distinct bindings -> distinct primitive ids", len(ids) == len(res["rows"])))

    # 6. manifest keeps the four counts SEPARATE (never conflated)
    man = build_manifest(res)
    checks.append(("manifest carries generated/unique/proven/typed as separate keys",
                   all(k in man for k in ("generated", "unique_after_dedupe", "proven", "typed"))))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - generate_parametric_text_ops:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - generate_parametric_text_ops: parametric proof works over {len(small)} sample bindings "
          f"(proven={res['proven']} typed={res['typed']}); dedupe collapses an identical binding; a wrong-expected "
          f"binding fails the executed proof and is never persisted; every row is serves_truth=true + L7_executed_proof "
          f"+ carries both edge type ids. Register tuple: {REGISTER_TUPLE}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_pack()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
