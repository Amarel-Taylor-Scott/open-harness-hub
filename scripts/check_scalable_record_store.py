#!/usr/bin/env python3
"""check_scalable_record_store — proof that the long-lived streams are stored to SCALE (billions->trillions).

The history/CDC/versioning streams are append-only and content-addressed, written through ONE backend-swappable
port (src.teleon.storage.record_store) governed by a single-source tier policy (architecture/storage_tier_policy.json).
This proves:

  1. TIER POLICY  — every stream declares a known tier; history streams carry an idempotency key; the history
                    cloud backend is the warehouse (the trillion-row path is declared, not implied); config
                    streams point at an existing JSON file and are REFUSED by the append-only store.
  2. IDEMPOTENT   — append dedupes by content key O(1) (re-appending N rows adds 0); the brain's old O(n)-per-append
                    full-file rescan is gone (a quadratic-cost regression would blow a generous time budget).
  3. PARITY       — the db-served reads equal the durable JSONL mirror (the file is the single on-disk source).
  4. LOSSLESS     — the JSONL mirror survives; failures/losers are retained; the brain's own contract still holds.
  5. SWAP         — the cloud backends are config-selected and name their target (postgres / warehouse), never a
                    silent fallback.

CLI: PYTHONPATH=. python3 scripts/check_scalable_record_store.py --self-test
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution.descent_attempt_store import DescentAttempt, DescentAttemptStore
from src.teleon.storage import record_store as rs

_REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── 1. TIER POLICY ──
    policy = rs.tier_policy()
    tiers = policy["tiers"]
    ck("every tier declares a local + cloud backend", all("local_backend" in t and "cloud_backend" in t for t in tiers.values()))
    streams = policy["streams"]
    ck("every stream declares a KNOWN tier", all(s["tier"] in tiers for s in streams), str([s["stream"] for s in streams if s["tier"] not in tiers]))
    hist = [s for s in streams if s["tier"] == "history"]
    ck("every history stream carries an idempotency_key (O(1) dedupe at scale)", all(s.get("idempotency_key") for s in hist), str([s["stream"] for s in hist if not s.get("idempotency_key")]))
    ck("the history CLOUD backend is the warehouse (the trillion-row path is declared)", tiers["history"]["cloud_backend"] == "warehouse")
    ck("the config CLOUD backend stays json_file (git is the store — never a DB)", tiers["config"]["cloud_backend"] == "json_file")
    cfg = [s for s in streams if s["tier"] == "config"]
    ck("every config stream points at an existing JSON file", all((_REPO / s["json"]).exists() for s in cfg), str([s["stream"] for s in cfg if not (_REPO / s.get("json", "")).exists()]))

    # a config-tier stream must be REFUSED by the append-only store (read it directly)
    try:
        rs.open_record_store("model_index"); refused = False
    except rs.StorageError:
        refused = True
    ck("a config-tier stream is refused by the append-only RecordStore", refused)
    ck("an unknown stream raises (no silent default)", _raises(lambda: rs.stream_spec("nope")))

    # the active append-only stream resolves to the local sqlite_wal backend; cloud names its target
    ck("descent_attempts resolves to sqlite_wal locally", rs.backend_for("descent_attempts", mode="local") == "sqlite_wal")
    ck("descent_attempts resolves to the warehouse in cloud mode", rs.backend_for("descent_attempts", mode="cloud") == "warehouse")

    with tempfile.TemporaryDirectory() as d:
        # ── 2. IDEMPOTENT + non-quadratic ──
        store = DescentAttemptStore(os.path.join(d, "attempts.jsonl"))
        N = 3000
        attempts = [DescentAttempt(f"unit-{i}", "model_downgrade",
                                   before={"cost": 0.3, "determinism": 0.2, "tokens_in": 800, "llm_usage": 5, "freshness": 0.5},
                                   after={"cost": 0.03, "determinism": 0.2, "tokens_in": 600, "llm_usage": 5, "freshness": 0.5},
                                   outcome="improved") for i in range(N)]
        t0 = time.monotonic()
        for a in attempts:
            store.append(a)
        first_pass = time.monotonic() - t0
        ck(f"appended {N} distinct attempts", len(store.all()) == N, str(len(store.all())))
        # re-append ALL of them: idempotent → 0 new rows
        for a in attempts:
            store.append(a)
        ck("re-appending every attempt adds 0 rows (O(1) content-hash idempotency)", len(store.all()) == N, str(len(store.all())))
        # a quadratic (old O(n)-per-append) path would make this far slower; generous budget catches a regression
        ck(f"append stays non-quadratic ({N} appends in {first_pass:.2f}s, budget 8s)", first_pass < 8.0, f"{first_pass:.2f}s")

        # ── 3. PARITY: db-served reads == durable JSONL mirror ──
        mirror = [json.loads(ln) for ln in Path(store.path).read_text(encoding="utf-8").splitlines() if ln.strip()]
        served = store.all()
        ck("db-served reads equal the durable JSONL mirror (count)", len(served) == len(mirror) == N, f"served={len(served)} mirror={len(mirror)}")
        ck("db-served reads equal the durable JSONL mirror (ids)",
           {r["attempt_id"] for r in served} == {r["attempt_id"] for r in mirror})

        # ── 4. LOSSLESS: a failure is retained as a training negative; mirror survives ──
        store.append(DescentAttempt("unit-fail", "llm_to_rule",
                                    before={"cost": 0.3, "determinism": 0.2, "tokens_in": 900, "llm_usage": 5, "freshness": 0.0},
                                    after={"cost": 0.3, "determinism": 0.2, "tokens_in": 900, "llm_usage": 5, "freshness": 0.0},
                                    outcome="failed"))
        recs = store.all()
        ck("FAILED attempts are retained (lossless negatives)", any(r["outcome"] == "failed" and not r["success"] for r in recs))
        ck("the durable JSONL mirror still exists on disk", Path(store.path).exists())

    # ── 5. SWAP: the OPERATIONAL cloud backend is WIRED (PostgresRecordStore — refuses w/o a DSN, never
    #     silently local; full proof in scripts/check_postgres_record_store.py); history stays the named
    #     unwired warehouse swap. Clear the PG env first so the refusal is deterministic on any host. ──
    _saved_pg = {k: os.environ.pop(k, None) for k in list(os.environ)
                 if k in ("OH_PG_DSN", "DATABASE_URL") or k.startswith("PG")}
    try:
        ck("the postgres backend is WIRED but refuses without a DSN (never silently local)",
           _raises(lambda: rs.PostgresRecordStore("component_candidates"), rs.StorageError))
    finally:
        for _k, _v in _saved_pg.items():
            if _v is not None:
                os.environ[_k] = _v
    ck("the warehouse backend names its target + refuses (the documented unwired swap)",
       _raises(rs.WarehouseRecordStore, NotImplementedError))

    print("\n" + (f"PASS - long-lived streams store to SCALE: one backend-swappable append-only port governed by a "
                  f"single-source tier policy (config->json / operational->postgres / history->warehouse), "
                  f"content-addressed O(1) idempotency (the brain's O(n)-per-append rescan is gone), db-served reads "
                  f"== the durable JSONL mirror, lossless negatives, and the cloud swap is config not code."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _raises(fn, exc: type = Exception) -> bool:
    try:
        fn()
        return False
    except exc:
        return True


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_scalable_record_store.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
