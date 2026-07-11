#!/usr/bin/env python3
"""scripts.runtime.load_scratch_into_multistore — flow loose primitive SCRATCH into the multi-substrate store.

The owner's storage vision (2026-07-04) is that a primitive's information should live in EVERY substrate at
once — the operational DB (served + vector-searchable), a git-like versioned store (fork/branch/promote
lineage), and an object bucket (durable cold blob). ``scripts.runtime.primitive_multistore.PrimitiveMultiStore``
already IS that single write path (``put_primitive`` fans one record out to all three, content-hash idempotent).

What was missing: the primitive factory writes THOUSANDS of loose scratch ``*.jsonl`` files under
``data/dev-intel/primitive_factory/**`` (daily shards, linkable cards, verified candidates, model outputs …)
plus the discovered feeds (``data/dev-intel/*candidates*.jsonl``, ``discovered_pipeline.jsonl``). Those rows are
just files on disk — they do NOT live in the durable multi-substrate store. This loader is the REUSABLE bridge:
it reads that loose JSONL and flows each row through ``put_primitive()`` so the data lands IN all three
locations, not as loose files.

Laws honored (all enforced here, not just documented):
  * REUSE-FIRST — builds nothing new; it only reads JSONL and calls the existing ``PrimitiveMultiStore``.
  * LOSSLESS — every well-formed row is preserved (candidate / serves_truth=false forced on the stored copy);
    malformed / non-object lines are COUNTED and reported, never silently dropped. The source files are the
    lineage layer and stay on disk + tracked (this loader NEVER deletes or untracks them — the store is the
    durable home, the files remain).
  * DEDUP BY CONTENT HASH — identical row content loads once (the same key ``put_primitive`` uses internally),
    so re-runs over the same scratch are idempotent no-ops.
  * CANDIDATE BOUNDARY — serves_truth=false everywhere; a stored copy is evidence of a state, never a truth claim.

    PYTHONPATH=. python3 scripts/runtime/load_scratch_into_multistore.py --self-test
    PYTHONPATH=. python3 scripts/runtime/load_scratch_into_multistore.py --dry-run data/dev-intel/primitive_factory/linkable_cards
    PYTHONPATH=. python3 scripts/runtime/load_scratch_into_multistore.py --store-root data/dev-intel/primitive_multistore_state \
        data/dev-intel/primitive_factory/linkable_cards data/dev-intel/discovered_pipeline.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

# --- cross-repo bootstrap so `src.teleon.*` resolves outside the proof harness (mirrors primitive_multistore) ---
_here = Path(__file__).resolve()
_root = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[2])
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
try:
    from scripts._repo_paths import install as _install
    _install()
except Exception:                                              # pragma: no cover - harness already has paths
    pass

from scripts.runtime.primitive_multistore import PrimitiveMultiStore  # noqa: E402  (the ONE write path, reused)
from src.teleon.storage.sync_engine import content_hash              # noqa: E402  (the shared dedup/idempotency key)

#: scratch locations the factory + discovery write to (dirs are globbed for **/*.jsonl; files are read directly).
#: Bare paths resolve under _repos/shared-backend-components/ per the repo path convention.
DEFAULT_SCRATCH_ROOTS = (
    "data/dev-intel/primitive_factory",
    "data/dev-intel/discovered_pipeline.jsonl",
    "data/dev-intel/ingested_candidates.jsonl",
    "data/dev-intel/interrogation_candidates.jsonl",
    "data/dev-intel/owner_shared_candidates.jsonl",
    "data/dev-intel/swarm_candidates.jsonl",
)
#: where the durable multi-substrate store lives by default (bare -> _repos/shared-backend-components/).
DEFAULT_STORE_ROOT = "data/dev-intel/primitive_multistore_state"
#: id fields tried in priority order; the row itself decides its identity, else we derive one from content.
ID_FIELDS = ("primitive_id", "card_id", "record_id", "shard_id", "id", "name")
#: prefix for content-derived ids when a row carries no stable id field (still deterministic + collision-safe).
DERIVED_ID_PREFIX = "scratchrow"


def resolve_scratch_root(path_str: str) -> Path:
    """Resolve a scratch path against the shared-backend-components root so bare `data/…` works from anywhere."""
    p = Path(path_str)
    return p if p.is_absolute() else (_root / p)


def iter_jsonl_files(roots) -> list[Path]:
    """Every `*.jsonl` file under the given roots (a root may be a dir -> globbed, or a file -> used directly).
    Sorted + de-duplicated so a run is deterministic and a file named twice is read once."""
    seen: dict[Path, None] = {}
    for r in roots:
        rp = resolve_scratch_root(r)
        if rp.is_dir():
            for f in rp.rglob("*.jsonl"):
                seen.setdefault(f.resolve(), None)
        elif rp.is_file() and rp.suffix == ".jsonl":
            seen.setdefault(rp.resolve(), None)
        # a missing path is not fatal (scratch is transient) — it simply contributes no rows.
    return sorted(seen)


def extract_primitive_id(row: dict, content_key: str) -> str:
    """The row's own identity if it carries one (primitive_id/card_id/…), else a deterministic content-derived
    id so an anonymous row is still addressable and stable across re-runs."""
    for field in ID_FIELDS:
        val = row.get(field)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, (int, float)):
            return str(val)
    # content_key is "sha256:<hex>"; keep it short + prefixed so derived ids are recognizable + unique.
    digest = content_key.split(":", 1)[-1][:16]
    return f"{DERIVED_ID_PREFIX}:{digest}"


def prepare_body(row: dict) -> dict:
    """The stored body = the full row with the candidate boundary forced ON (lossless: nothing is dropped, we
    only ASSERT serves_truth=false + candidate=true, which is the invariant for all generated scratch)."""
    body = dict(row)
    body["serves_truth"] = False
    body.setdefault("candidate", True)
    return body


def load_scratch_into_multistore(
    roots=DEFAULT_SCRATCH_ROOTS,
    *,
    store_root: str | Path = DEFAULT_STORE_ROOT,
    dry_run: bool = False,
    limit: int | None = None,
    verify_sample: int = 25,
) -> dict:
    """Read loose primitive scratch JSONL and flow each unique row through ``PrimitiveMultiStore.put_primitive``.

    dry_run=True computes exactly what WOULD load (files, rows, unique-by-content, malformed) WITHOUT writing.
    Returns a summary receipt (serves_truth=false). Idempotent: identical content loads once, so re-runs are
    no-ops; the store's own content-hash idempotency makes even a partial re-run safe."""
    files = iter_jsonl_files(roots)
    summary = {
        "record_type": "scratch_multistore_load_receipt",
        "dry_run": dry_run,
        "store_root": str(resolve_scratch_root(str(store_root))) if not dry_run else None,
        "files_scanned": len(files),
        "rows_read": 0,           # well-formed JSON objects seen
        "rows_loaded": 0,         # unique-by-content rows flowed into the store (or that WOULD load, if dry-run)
        "rows_deduped": 0,        # rows skipped because their content hash was already seen this run
        "malformed_lines": 0,     # lines that were not valid JSON
        "non_object_rows": 0,     # valid JSON that was not a dict (can't be a primitive body)
        "verified_in_all_locations": 0,   # of the loaded rows, how many were confirmed present in db+git+bucket
        "verify_sample_target": verify_sample if not dry_run else 0,
        "serves_truth": False,
    }

    seen_hashes: set[str] = set()
    store = None if dry_run else PrimitiveMultiStore(resolve_scratch_root(str(store_root)))
    try:
        for f in files:
            try:
                fh = f.open("r", encoding="utf-8")
            except OSError:
                continue
            with fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        summary["malformed_lines"] += 1
                        continue
                    if not isinstance(row, dict):
                        summary["non_object_rows"] += 1
                        continue
                    summary["rows_read"] += 1

                    body = prepare_body(row)
                    ch = content_hash(body)             # SAME key put_primitive uses -> dedup aligns with the store
                    if ch in seen_hashes:
                        summary["rows_deduped"] += 1
                        continue
                    seen_hashes.add(ch)

                    if limit is not None and summary["rows_loaded"] >= limit:
                        # honest partial: stop loading but keep the counts we reached (no silent cap beyond this)
                        summary["limited"] = True
                        return summary

                    if dry_run:
                        summary["rows_loaded"] += 1
                        continue

                    pid = extract_primitive_id(row, ch)
                    receipt = store.put_primitive(pid, body)
                    summary["rows_loaded"] += 1

                    # verify a bounded sample is actually retrievable from ALL three locations (proof, not faith)
                    if summary["verified_in_all_locations"] < verify_sample:
                        present = store.present_in_all_locations(pid)   # id-addressable — no handle needed
                        if present["db"] and present["git"] and present["object_store"]:
                            summary["verified_in_all_locations"] += 1
    finally:
        if store is not None:
            store.close()
    return summary


def _self_test() -> int:
    """N synthetic scratch rows in -> N retrievable from ALL three locations; dedup + idempotent re-run proven."""
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        scratch = tdp / "scratch"
        (scratch / "sub").mkdir(parents=True)
        store_root = tdp / "store"

        # N distinct primitive rows across two files + two nested dirs, plus a duplicate + a malformed line +
        # a non-object line to exercise every branch losslessly.
        rows_a = [
            {"primitive_id": "ocr.pdf_table_extract", "primitive_kind": "ocr", "input_edge": "PDF+Policy"},
            {"card_id": "lpc:abc123", "kind": "primitive_group", "input_edge": "Query+Docs"},
            {"id": "hanlp", "source": "github", "plane": "asr"},
        ]
        rows_b = [
            {"primitive_id": "rerank.cross_encoder", "primitive_kind": "reranker"},
            {"name": "anonymous_row_no_id_field", "note": "derives a content id"},
            {"primitive_id": "ocr.pdf_table_extract", "primitive_kind": "ocr", "input_edge": "PDF+Policy"},  # dup
        ]
        n_unique = 5  # 6 rows - 1 exact duplicate
        with (scratch / "a.jsonl").open("w") as fh:
            for r in rows_a:
                fh.write(json.dumps(r) + "\n")
            fh.write("\n")                                  # blank line (ignored)
            fh.write("{not valid json\n")                   # malformed (counted)
            fh.write("[1, 2, 3]\n")                          # valid JSON but not an object (counted)
        with (scratch / "sub" / "b.jsonl").open("w") as fh:
            for r in rows_b:
                fh.write(json.dumps(r) + "\n")

        # dry-run first: reports what WOULD load, writes nothing
        dry = load_scratch_into_multistore([str(scratch)], store_root=store_root, dry_run=True)
        checks.append(("dry-run finds both scratch files", dry["files_scanned"] == 2))
        checks.append(("dry-run counts unique rows (dedup applied)", dry["rows_loaded"] == n_unique))
        checks.append(("dry-run counts the duplicate row", dry["rows_deduped"] == 1))
        checks.append(("dry-run counts the malformed line, not silently dropped", dry["malformed_lines"] == 1))
        checks.append(("dry-run counts the non-object row", dry["non_object_rows"] == 1))
        checks.append(("dry-run wrote nothing (no store dir created)", not store_root.exists()))

        # real load
        res = load_scratch_into_multistore([str(scratch)], store_root=store_root, dry_run=False)
        checks.append(("real load: N unique rows in", res["rows_loaded"] == n_unique))
        checks.append(("real load: every loaded row retrievable from ALL 3 locations (db+git+bucket)",
                       res["verified_in_all_locations"] == n_unique))
        checks.append(("real load: duplicate collapsed (not double-stored)", res["rows_deduped"] == 1))

        # independent re-open of the store confirms the primitives truly persisted in all three locations
        store = PrimitiveMultiStore(store_root)
        try:
            got = store.get_primitive("ocr.pdf_table_extract")
            checks.append(("primitive is retrievable from the operational DB after load", got is not None))
            checks.append(("candidate boundary held on the stored copy", got is not None and got.get("serves_truth") is False))
            checks.append(("the git-like store holds the primitive", any(
                r.get("record_id") == "rerank.cross_encoder" for r in store.git.all())))
            checks.append(("db holds exactly the N unique rows (no dupes)", store.db.count() == n_unique))
        finally:
            store.close()

        # idempotent re-run over the SAME scratch loads nothing new (the store's content-hash idempotency holds)
        res2 = load_scratch_into_multistore([str(scratch)], store_root=store_root, dry_run=False)
        store2 = PrimitiveMultiStore(store_root)
        try:
            checks.append(("idempotent re-run: DB count unchanged", store2.db.count() == n_unique))
        finally:
            store2.close()

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - load_scratch_into_multistore:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - load_scratch_into_multistore: loose primitive scratch JSONL flows through put_primitive() into "
          "the multi-substrate store — N unique rows in -> N retrievable from ALL three locations (operational DB "
          "+ git-like store + object bucket); duplicates collapse by content hash; malformed/non-object lines are "
          "counted (lossless), not dropped; --dry-run writes nothing; re-runs are idempotent. serves_truth=false.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    ap = argparse.ArgumentParser(
        description="Flow loose primitive scratch JSONL into the multi-substrate store (db + git-like + bucket).")
    ap.add_argument("roots", nargs="*", default=list(DEFAULT_SCRATCH_ROOTS),
                    help="scratch dirs (globbed for **/*.jsonl) and/or .jsonl files. Default: the factory + feeds.")
    ap.add_argument("--store-root", default=DEFAULT_STORE_ROOT, help="durable multi-substrate store root.")
    ap.add_argument("--dry-run", action="store_true", help="report files/rows that WOULD load; write nothing.")
    ap.add_argument("--limit", type=int, default=None, help="stop after loading N unique rows (honest partial).")
    ap.add_argument("--verify-sample", type=int, default=25,
                    help="how many loaded rows to confirm present in all 3 locations (proof, bounded for speed).")
    ap.add_argument("--self-test", action="store_true", help="run the synthetic in->out proof and exit.")
    args = ap.parse_args(argv)

    roots = args.roots if args.roots else list(DEFAULT_SCRATCH_ROOTS)
    summary = load_scratch_into_multistore(
        roots, store_root=args.store_root, dry_run=args.dry_run,
        limit=args.limit, verify_sample=args.verify_sample)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
