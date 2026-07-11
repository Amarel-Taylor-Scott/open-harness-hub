#!/usr/bin/env python3
"""scripts.compiled_route_store — append-only PERSISTENCE for scripts.compiled_route_cache: the ledger
that makes the compile-once/execute-many amortization loop survive a process restart.

``CompiledRouteCache`` is deliberately in-memory ("a caller may persist ``entries`` as JSONL
(append-only)" — its own docstring). This module is that caller, and ONLY that: it adds no second cache,
no second composer, no second receipt formula. Three verbs:

  * save_entries(cache, path)   — append one JSONL row per NEW compiled artifact or per reuse-count
                                  change since the last save. Lossless: the file only ever GROWS; a
                                  re-save of unchanged state appends nothing (byte-identical file).
  * load_into(cache, path)      — rebuild the in-memory cache by replaying the ledger in file order:
                                  last-write-wins per request_key (artifact rows re-place the artifact;
                                  reuse rows re-place only the reuse count). Torn/corrupt lines are
                                  SKIPPED AND COUNTED (an append-only tail torn by a crash mid-append
                                  must never wedge a load); a tampered row (content hash mismatch) is
                                  likewise skipped and counted separately.
  * amortization_ledger(path)   — recompute the amortization receipt from the persisted ledger ALONE
                                  (fresh cache <- load_into <- ``CompiledRouteCache.amortization_receipt``),
                                  byte-identical to the live cache's receipt for the same state.

Reuse-first: the cache/engine is imported (never reimplemented), rows are read through the ONE tolerant
JSONL reader (``scripts._jsonl``), and the default path resolves through the ONE resource resolver
(``scripts._repo_paths``). Every persisted row and every summary is candidate=true / serves_truth=false —
persisting a compiled route is bookkeeping, NEVER promotion. Deterministic: no RNG, no wall-clock — row
identity is sha256 of the row's canonical content only, and append order is sorted by request_key.

    PYTHONPATH=. python3 scripts/compiled_route_store.py --self-test
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
import hashlib  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts._jsonl import iter_jsonl_tolerant  # noqa: E402  the ONE tolerant JSONL reader (never re-implement)
from scripts._repo_paths import resource as _resource  # noqa: E402  the ONE root-relative→real path resolver
from scripts.compiled_route_cache import BOUNDARY, CompiledRouteCache  # noqa: E402  the engine being persisted

# -- the ledger location (single source; callers pass path=None to use it) --------------------------
# dev-intel because a compiled-route ledger is measurement/candidate data (like the benchmark logs that
# live beside it), never catalog truth; resolved through resource() so the _repos/ migration cannot break it.
DEFAULT_LEDGER_RELATIVE_PATH = "data/dev-intel/compiled_routes/ledger.jsonl"

# -- row schema (single-typed field/kind names; a string typed twice is a string that drifts) --------
LEDGER_ROW_KIND_FIELD = "row_kind"                       # discriminator field on every ledger row
ROW_KIND_COMPILED_ARTIFACT = "compiled_route_artifact"   # a full compiled artifact (new or re-compiled)
ROW_KIND_REUSE_COUNT = "compiled_route_reuse_count"      # an ABSOLUTE reuse-count update for an existing key
LEDGER_ROW_SHA256_FIELD = "row_sha256"                   # content hash sealing each row (tamper detection)
ARTIFACT_REQUEST_KEY_FIELD = "request_key"               # the cache's content key (owned by compiled_route_cache)
ARTIFACT_REUSE_COUNT_FIELD = "reuse_count"               # the ONE mutable counter on an artifact — the only
#                                                          field the ledger ever tracks as a delta row
# 16 hex chars = 64 bits — the same width compiled_route_cache uses for request_key ids: collision-safe
# for a dev-intel ledger while keeping rows compact. Content-only (sha256 of the row body): no RNG, no clock.
LEDGER_ROW_HASH_HEX_CHARS = 16

# The receipt horizon is single-sourced from the engine's own signature default, so the ledger recompute
# and a live ``cache.amortization_receipt()`` agree by construction (never a parallel hand-typed 1000).
DEFAULT_AMORTIZATION_AT_USES: int = inspect.signature(
    CompiledRouteCache.amortization_receipt).parameters["at_uses"].default


def _resolve_ledger_path(path: str | Path | None) -> Path:
    """The ledger file to use: the caller's path, else the repo-default (resolved via resource())."""
    return Path(path) if path is not None else Path(_resource(DEFAULT_LEDGER_RELATIVE_PATH))


def _canonical_row_json(row: dict[str, Any]) -> str:
    """Canonical one-line JSON for a ledger row — sort_keys so the same content is the same bytes
    (the determinism the byte-identical gates below assert). Matches the cache's own dumps profile."""
    return json.dumps(row, sort_keys=True, default=str)


def _row_content_sha256(row: dict[str, Any]) -> str:
    """Content hash over the row MINUS its own seal field — sha256 of canonical bytes only (no clock,
    no RNG), truncated to the house 16-hex width."""
    body = {k: v for k, v in row.items() if k != LEDGER_ROW_SHA256_FIELD}
    return hashlib.sha256(_canonical_row_json(body).encode("utf-8")).hexdigest()[:LEDGER_ROW_HASH_HEX_CHARS]


def _sealed_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return the row with its content-hash seal attached."""
    return {**row, LEDGER_ROW_SHA256_FIELD: _row_content_sha256(row)}


def _artifact_identity_json(entry: dict[str, Any]) -> str:
    """An artifact's canonical identity EXCLUDING its reuse counter — used to decide whether a cache
    entry is a NEW/changed artifact (append a full artifact row) vs merely more-reused (append the
    small reuse-count row)."""
    return _canonical_row_json({k: v for k, v in entry.items() if k != ARTIFACT_REUSE_COUNT_FIELD})


def _replay_ledger(ledger_path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, int], dict[str, int]]:
    """Replay the ledger in file order (append order IS the write order — no clock needed for
    last-write-wins). Returns (artifacts by request_key, reuse count by request_key, replay stats).
    Tolerant by design: a torn tail line, a tampered row, a malformed row, or an orphan reuse row is
    skipped AND counted — never a crash, never a silent drop."""
    artifacts: dict[str, dict[str, Any]] = {}
    reuse_counts: dict[str, int] = {}
    stats = {"rows_applied": 0, "corrupt_lines_skipped": 0, "tampered_rows_skipped": 0,
             "malformed_rows_skipped": 0, "orphan_reuse_rows_skipped": 0}

    def _count_corrupt(_lineno: int, _line: str, _exc: Exception) -> None:
        stats["corrupt_lines_skipped"] += 1

    for row in iter_jsonl_tolerant(ledger_path, on_error=_count_corrupt):
        if row.get(LEDGER_ROW_SHA256_FIELD) != _row_content_sha256(row):
            stats["tampered_rows_skipped"] += 1          # the seal broke: content no longer matches its hash
            continue
        kind = row.get(LEDGER_ROW_KIND_FIELD)
        key = row.get(ARTIFACT_REQUEST_KEY_FIELD)
        if kind == ROW_KIND_COMPILED_ARTIFACT and key:
            entry = {k: v for k, v in row.items()
                     if k not in (LEDGER_ROW_KIND_FIELD, LEDGER_ROW_SHA256_FIELD)}
            artifacts[key] = entry                       # last-write-wins: a later artifact row re-places
            reuse_counts[key] = int(entry.get(ARTIFACT_REUSE_COUNT_FIELD, 0))
            stats["rows_applied"] += 1
        elif kind == ROW_KIND_REUSE_COUNT and key:
            if key in artifacts:
                reuse_counts[key] = int(row[ARTIFACT_REUSE_COUNT_FIELD])   # last-write-wins on the counter
                stats["rows_applied"] += 1
            else:
                stats["orphan_reuse_rows_skipped"] += 1  # a counter for a route this ledger never compiled
        else:
            stats["malformed_rows_skipped"] += 1         # unknown kind / missing request_key
    return artifacts, reuse_counts, stats


def save_entries(cache: CompiledRouteCache, path: str | Path | None = None) -> dict[str, Any]:
    """APPEND the delta between ``cache`` and the persisted ledger: one full artifact row per request_key
    the ledger has never seen (or whose compiled content changed — lossless: the old row stays, the new
    one wins on replay), one absolute reuse-count row per key whose counter moved. Never truncates,
    never rewrites, never reorders existing bytes; saving an unchanged cache appends nothing."""
    ledger_path = _resolve_ledger_path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    persisted_artifacts, persisted_reuse, _stats = _replay_ledger(ledger_path)
    artifact_rows = 0
    reuse_rows = 0
    lines: list[str] = []
    for key in sorted(cache.entries):                    # sorted → deterministic append order (no clock)
        entry = cache.entries[key]
        persisted = persisted_artifacts.get(key)
        if persisted is None or _artifact_identity_json(persisted) != _artifact_identity_json(entry):
            lines.append(_canonical_row_json(_sealed_row(
                {LEDGER_ROW_KIND_FIELD: ROW_KIND_COMPILED_ARTIFACT, **entry})))
            artifact_rows += 1
        elif int(entry[ARTIFACT_REUSE_COUNT_FIELD]) != persisted_reuse.get(key):
            lines.append(_canonical_row_json(_sealed_row(
                {LEDGER_ROW_KIND_FIELD: ROW_KIND_REUSE_COUNT,
                 ARTIFACT_REQUEST_KEY_FIELD: key,
                 ARTIFACT_REUSE_COUNT_FIELD: int(entry[ARTIFACT_REUSE_COUNT_FIELD]),
                 **BOUNDARY})))
            reuse_rows += 1
    if lines:
        with ledger_path.open("a", encoding="utf-8") as fh:   # "a" — the ONLY write mode in this module
            fh.write("".join(line + "\n" for line in lines))
    return {"record_type": "compiled_route_ledger_save", "ledger_path": str(ledger_path),
            "rows_appended": artifact_rows + reuse_rows,
            "artifact_rows_appended": artifact_rows, "reuse_count_rows_appended": reuse_rows,
            **BOUNDARY}


def load_into(cache: CompiledRouteCache, path: str | Path | None = None) -> dict[str, Any]:
    """Rebuild ``cache.entries`` from the ledger: replay every sealed row in file order, last-write-wins
    per request_key (for both the artifact and its reuse count). A missing ledger loads zero routes;
    corrupt / tampered / malformed / orphan rows are skipped and REPORTED in the returned summary."""
    ledger_path = _resolve_ledger_path(path)
    artifacts, reuse_counts, stats = _replay_ledger(ledger_path)
    for key, entry in artifacts.items():
        rebuilt = dict(entry)
        rebuilt[ARTIFACT_REUSE_COUNT_FIELD] = reuse_counts[key]
        cache.entries[key] = rebuilt                     # the ledger wins over any pre-existing entry
    return {"record_type": "compiled_route_ledger_load", "ledger_path": str(ledger_path),
            "routes_loaded": len(artifacts), **stats, **BOUNDARY}


def amortization_ledger(path: str | Path | None = None,
                        at_uses: int = DEFAULT_AMORTIZATION_AT_USES) -> dict[str, Any]:
    """The amortization receipt recomputed from the persisted ledger ALONE: a fresh cache is rebuilt via
    ``load_into`` and the ENGINE's own ``amortization_receipt`` runs over it — same formula, same shape,
    byte-identical to the live cache's receipt for the same persisted state. No second receipt math."""
    rebuilt = CompiledRouteCache()
    load_into(rebuilt, path)
    return rebuilt.amortization_receipt(at_uses=at_uses)


# ----------------------------------------------------------------------------------------------------
# self-test — hermetic (tempfile only), offline, deterministic; includes MUTATION + determinism gates
# ----------------------------------------------------------------------------------------------------
def _receipt_bytes(receipt: dict[str, Any]) -> bytes:
    """Canonical bytes of a receipt — what 'byte-identical' means in every gate below."""
    return _canonical_row_json(receipt).encode("utf-8")


def _self_test() -> int:
    import tempfile

    checks: list[tuple[str, bool]] = []
    # synthetic two-chain fixture (same shape as the engine's own self-test cards; all candidates)
    cards = [
        {"primitive_id": "p:norm", "title": "Normalize messy records",
         "blackbox": "Normalize and standardize messy raw records into a clean canonical schema.",
         "input_edge": "RawRecord", "output_edge": "NormalizedRecord", **BOUNDARY},
        {"primitive_id": "p:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate records by clustering near-identical normalized rows.",
         "input_edge": "NormalizedRecord", "output_edge": "DedupedRecord", **BOUNDARY},
        {"primitive_id": "p:extract", "title": "Extract entity mentions from documents",
         "blackbox": "Extract entity mentions from raw documents into structured mention records.",
         "input_edge": "Document", "output_edge": "EntityMention", **BOUNDARY},
        {"primitive_id": "p:link", "title": "Link entity mentions to canonical entities",
         "blackbox": "Link extracted entity mentions to canonical entities in the registry.",
         "input_edge": "EntityMention", "output_edge": "LinkedEntity", **BOUNDARY},
    ]
    request_a = "clean up and remove duplicate messy records"
    request_b = "extract entity mentions from documents and link them to canonical entities"

    with tempfile.TemporaryDirectory(prefix="compiled-route-store-selftest-") as td:
        # a NESTED ledger path proves the mkdir-parents contract of the default-path behavior
        ledger = Path(td) / "compiled_routes" / "ledger.jsonl"

        live = CompiledRouteCache()
        compiled_a = live.compile_once(request_a, cards=cards)
        compiled_b = live.compile_once(request_b, cards=cards)
        for _ in range(3):
            live.execute(request_a)
        live.execute(request_b)
        checks.append(("fixture compiles 2 real routes", compiled_a["route_found"] and compiled_b["route_found"]
                       and len(live.entries) == 2))

        # (a) SAVE — one artifact row per new compiled route; parent dirs created.
        save_1 = save_entries(live, ledger)
        checks.append(("first save appends exactly one artifact row per compiled route",
                       save_1["rows_appended"] == 2 and save_1["artifact_rows_appended"] == 2
                       and ledger.exists()))
        bytes_after_save_1 = ledger.read_bytes()

        # (b) DETERMINISM gate 1 — an unchanged cache re-saved appends NOTHING; the file is byte-identical.
        save_2 = save_entries(live, ledger)
        checks.append(("re-saving unchanged state appends nothing (file byte-identical)",
                       save_2["rows_appended"] == 0 and ledger.read_bytes() == bytes_after_save_1))

        # (c) LOAD into a NEW cache — reuse counts survive; the ledger-only receipt is BYTE-IDENTICAL.
        rebuilt = CompiledRouteCache()
        load_summary = load_into(rebuilt, ledger)
        live_receipt = _receipt_bytes(live.amortization_receipt())
        checks.append(("load rebuilds every route with its reuse count",
                       load_summary["routes_loaded"] == 2
                       and rebuilt.entries[compiled_a["request_key"]][ARTIFACT_REUSE_COUNT_FIELD] == 3
                       and rebuilt.entries[compiled_b["request_key"]][ARTIFACT_REUSE_COUNT_FIELD] == 1))
        checks.append(("amortization receipt recomputed from the ledger ALONE is byte-identical to live",
                       _receipt_bytes(amortization_ledger(ledger)) == live_receipt))

        # (d) DETERMINISM gate 2 — the ledger recompute itself is byte-identical twice.
        checks.append(("ledger receipt is byte-identical across two recomputes (no RNG, no clock)",
                       _receipt_bytes(amortization_ledger(ledger)) == _receipt_bytes(amortization_ledger(ledger))))

        # (e) APPEND-ONLY — more reuse then save: the file GROWS and the old bytes are an intact prefix.
        for _ in range(5):
            live.execute(request_b)
        save_3 = save_entries(live, ledger)
        bytes_after_save_3 = ledger.read_bytes()
        checks.append(("a reuse-count change appends ONE delta row (not a rewritten artifact)",
                       save_3["rows_appended"] == 1 and save_3["reuse_count_rows_appended"] == 1))
        checks.append(("append-only proven: the second save GROWS the file and never truncates "
                       "(previous bytes survive as an exact prefix)",
                       len(bytes_after_save_3) > len(bytes_after_save_1)
                       and bytes_after_save_3.startswith(bytes_after_save_1)))
        rebuilt_2 = CompiledRouteCache()
        load_into(rebuilt_2, ledger)
        checks.append(("last-write-wins per request_key: the reload sees the LATEST reuse count",
                       rebuilt_2.entries[compiled_b["request_key"]][ARTIFACT_REUSE_COUNT_FIELD] == 6
                       and _receipt_bytes(amortization_ledger(ledger))
                       == _receipt_bytes(live.amortization_receipt())))

        # (f) TORN TAIL — a corrupted trailing line (crash mid-append) is tolerated: skipped AND counted.
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write('{"torn": ')                        # a half-written row, no newline — the classic torn tail
        rebuilt_3 = CompiledRouteCache()
        load_torn = load_into(rebuilt_3, ledger)
        checks.append(("a corrupted trailing line is tolerated on load: skipped, counted, all routes intact",
                       load_torn["corrupt_lines_skipped"] == 1 and load_torn["routes_loaded"] == 2
                       and _receipt_bytes(rebuilt_3.amortization_receipt())
                       == _receipt_bytes(live.amortization_receipt())))

        # (g) MUTATION gate — a WRONG artifact must make the gates go red, both ways:
        #     (g1) tampered content with a stale seal is DETECTED (hash mismatch) and dropped;
        #     (g2) a wrong-but-resealed artifact yields a receipt that does NOT byte-match live — proving
        #          the byte-identity assertions above are real discriminators, not always-green.
        rows = [json.loads(line) for line in bytes_after_save_1.decode("utf-8").splitlines()]
        stale_seal = dict(rows[0])
        stale_seal["compile_cost_tokens"] = int(stale_seal["compile_cost_tokens"]) + 1   # mutate; keep old seal
        tampered_ledger = Path(td) / "tampered.jsonl"
        tampered_ledger.write_text(_canonical_row_json(stale_seal) + "\n"
                                   + _canonical_row_json(rows[1]) + "\n", encoding="utf-8")
        load_tampered = load_into(CompiledRouteCache(), tampered_ledger)
        checks.append(("MUTATION g1: a tampered row (content != seal) is detected, counted, and dropped",
                       load_tampered["tampered_rows_skipped"] == 1 and load_tampered["routes_loaded"] == 1))
        resealed = {k: v for k, v in stale_seal.items() if k != LEDGER_ROW_SHA256_FIELD}
        resealed_ledger = Path(td) / "resealed.jsonl"
        resealed_ledger.write_text(_canonical_row_json(_sealed_row(resealed)) + "\n"
                                   + _canonical_row_json(rows[1]) + "\n", encoding="utf-8")
        checks.append(("MUTATION g2: a wrong (resealed) artifact makes the byte-identity gate FAIL",
                       _receipt_bytes(amortization_ledger(resealed_ledger)) != live_receipt))

        # (h) GOVERNANCE — every persisted row and every summary is candidate=true / serves_truth=false.
        all_rows = [json.loads(line) for line in bytes_after_save_3.decode("utf-8").splitlines()]
        checks.append(("every ledger row is candidate=true / serves_truth=false (persistence != promotion)",
                       all(r.get("candidate") is True and r.get("serves_truth") is False for r in all_rows)
                       and save_3["serves_truth"] is False and load_torn["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - compiled_route_store: append-only JSONL ledger for the compile-once cache — save "
          "appends only new-artifact/reuse-delta rows (re-save of unchanged state appends 0; old bytes "
          "survive as an exact prefix), load rebuilds the cache last-write-wins per request_key, the "
          "amortization receipt recomputed from the ledger ALONE is byte-identical to live, a torn "
          "trailing line is skipped+counted, and a wrong artifact turns the gates red (hash-mismatch "
          "drop + receipt mismatch). Every row candidate=true / serves_truth=false.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true", help="hermetic offline proof (tempfile only)")
    ap.add_argument("--receipt", action="store_true",
                    help="print the amortization receipt recomputed from the persisted ledger alone")
    ap.add_argument("--ledger", default=None,
                    help=f"ledger path (default: {DEFAULT_LEDGER_RELATIVE_PATH} via the resource resolver)")
    ap.add_argument("--at-uses", type=int, default=DEFAULT_AMORTIZATION_AT_USES,
                    help="receipt horizon in uses (default single-sourced from the engine)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.receipt:
        print(json.dumps(amortization_ledger(args.ledger, at_uses=args.at_uses), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
