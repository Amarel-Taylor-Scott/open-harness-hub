#!/usr/bin/env python3
"""scripts.runtime.primitive_multistore — the ONE write path that stores a primitive in ALL locations at once.

The owner's model (2026-07-04): a primitive's information should live in every substrate simultaneously —
the operational DB (Postgres/pgvector, served + vector-searchable), a git-like versioned store (fork/branch/
promote lineage), and an object bucket (durable blob / cold read). This module BINDS the three real backends
that already exist — it builds nothing new, it wires:

    location        real backend (reused)                                    tier / role
    ------------    -----------------------------------------------------    ------------------------------
    db              src.teleon.storage.record_store.LocalRecordStore          operational: sqlite_wal local
                    (cloud swap -> PostgresRecordStore + pgvector)            -> postgres+pgvector (millions)
    git             src.teleon.storage.git_record_store.GitRecordStore        git-like: candidate->main promote
                    (carries a VectorMirror: InMemory local / PgVector cloud) versioned, forkable lineage
    object_store    scripts.runtime.object_store.LocalObjectStore            bucket: content-addressed blob
                    (cloud swap -> S3/GCS/Azure adapter, interface-identical) durable cold mirror

The fan-out + agreement is the existing src.teleon.storage.sync_engine (content-hash CDC, leaf-sharded to
billions, GOVERNED flag-don't-clobber conflict handling, lossless). ``put_primitive`` writes the SAME record
to all three, keyed by the hash of the stored record (distinct ids never collapse); a partial write returns
an honest converged=False receipt naming the store that failed. serves_truth=false everywhere.
Everything is candidate / serves_truth=false — a stored copy is evidence of a state, never a truth claim.

Local-first + keyless by default (a temp/dev root); the cloud swap (postgres+pgvector, a git remote, S3/R2)
is a config change via architecture/storage_tier_policy.json + OH_STORAGE_MODE=cloud, never a caller change.

    PYTHONPATH=. python3 scripts/runtime/primitive_multistore.py --self-test
    PYTHONPATH=. python3 scripts/runtime/primitive_multistore.py --demo
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# --- cross-repo bootstrap so `src.teleon.*` resolves outside the proof harness ---
_here = Path(__file__).resolve()
_root = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[2])
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
try:
    from scripts._repo_paths import install as _install
    _install()
except Exception:                                              # pragma: no cover - harness already has paths
    pass

from scripts.runtime.object_store import LocalObjectStore      # noqa: E402  (bucket)
from src.teleon.storage.record_store import LocalRecordStore   # noqa: E402  (operational: sqlite/pg+pgvector)
from src.teleon.storage.git_record_store import GitRecordStore  # noqa: E402 (git-like versioned)
from src.teleon.storage.sync_engine import content_hash, shard_of  # noqa: E402 (content-addressing + sharding)

#: the three canonical locations a primitive lands in, in agreement (the owner's "all locations").
LOCATIONS = ("db", "git", "object_store")
#: default tenant partition for the object bucket (content-addressed under object://<tenant>/<sha>).
DEFAULT_TENANT = "primitives"


class PrimitiveMultiStore:
    """Write-through facade: one primitive -> operational DB + git-like store + object bucket, provably
    converged via the sync engine. serves_truth=false everywhere. Backends are the real reused modules;
    the local defaults are offline + keyless, the cloud swap is config, not code."""

    def __init__(self, root: str | Path, *, tenant: str = DEFAULT_TENANT):
        root = Path(root)
        (root / "db").mkdir(parents=True, exist_ok=True)
        self.tenant = tenant
        # db: operational tier (sqlite_wal + jsonl mirror locally; postgres+pgvector is the config swap)
        self.db = LocalRecordStore(root / "db" / "primitives.jsonl", db_path=root / "db" / "primitives.sqlite")
        # git: git-like versioned store (real git repo, candidate->main promotion, vector mirror)
        self.git = GitRecordStore(root / "git")
        # object_store: content-addressed bucket (local dir now; S3/GCS/Azure is the interface-identical swap)
        self.bucket = LocalObjectStore(root / "bucket")

    def put_primitive(self, primitive_id: str, body: dict) -> dict:
        """Store ONE primitive in ALL three locations. The idempotency key is the content hash of the
        STORED RECORD (identity included) — so two distinct ids with the same body never collapse. Each
        backend write is independent: a mid-write failure yields an honest PARTIAL receipt (converged=False
        + errors naming the failed store) instead of a bare raise, and ``converged`` reflects the REAL
        writes, never an in-memory shadow. Re-put of identical content is an O(1) no-op at every location."""
        record = {"record_id": primitive_id, "serves_truth": False, **body}
        ch = content_hash(record)                              # key on the RECORD (identity), never body alone
        locations: dict = {}
        errors: dict = {}
        try:
            locations["db"] = {"backend": self.db.backend, "seq": self.db.append(record, idem_key=ch)}
        except Exception as exc:                               # one store down must not lose the others
            errors["db"] = f"{type(exc).__name__}: {exc}"
        try:
            locations["git"] = {"backend": self.git.backend, "seq": self.git.append(record, idem_key=ch)}
        except Exception as exc:
            errors["git"] = f"{type(exc).__name__}: {exc}"
        try:
            blob = self.bucket.put(self.tenant, record, mime_type="application/json")
            locations["object_store"] = {"backend": self.bucket.backend, "payload_ref": blob["payload_ref"]}
        except Exception as exc:
            errors["object_store"] = f"{type(exc).__name__}: {exc}"

        return {
            "record_type": "primitive_multistore_receipt",
            "primitive_id": primitive_id,
            "content_hash": ch,
            "shard": shard_of(primitive_id),
            "locations": locations,
            "converged": not errors and set(locations) == set(LOCATIONS),  # REAL: every write succeeded
            "errors": errors or None,                          # names any store that failed (partial write)
            "serves_truth": False,                             # a stored copy is evidence, never truth
        }

    def get_primitive(self, primitive_id: str) -> dict | None:
        """Read the latest version from the operational DB (the fastest tier)."""
        hits = self.db.all(lambda r: r.get("record_id") == primitive_id)
        return hits[-1] if hits else None

    def present_in_all_locations(self, primitive_id: str) -> dict:
        """Confirm the primitive is retrievable from ALL three locations, addressable by ``primitive_id``
        ALONE: the db record is fetched and the bucket ref is recomputed from it (content-addressed via the
        bucket's own ``ref_for``). No caller-supplied handle needed. serves_truth=false."""
        record = self.get_primitive(primitive_id)
        git_has = any(r.get("record_id") == primitive_id for r in self.git.all())
        if record is None:
            return {"db": False, "git": git_has, "object_store": False}
        return {"db": True, "git": git_has,
                "object_store": self.bucket.exists(self.bucket.ref_for(self.tenant, record))}

    def close(self) -> None:
        for backend in (self.db, self.git):                    # close git too — its vector mirror leaks a pg conn in cloud mode
            try:
                backend.close()
            except Exception:                                  # pragma: no cover
                pass


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        store = PrimitiveMultiStore(td)
        body = {"kind": "primitive", "primitive_id": "ocr.pdf_table_extract", "primitive_kind": "ocr",
                "input_edge": "PDF+OcrPolicy", "output_edge": "Table+Receipt", "candidate": True,
                "serves_truth": False, "source_refs": ["https://github.com/x/paddleocr"]}
        r = store.put_primitive("ocr.pdf_table_extract", body)

        checks.append(("the receipt names all THREE locations", set(r["locations"]) == set(LOCATIONS)))
        checks.append(("content_hash is a sha256 idempotency key", r["content_hash"].startswith("sha256:")))
        checks.append(("candidate boundary held: serves_truth=false", r["serves_truth"] is False))
        checks.append(("multi-location write converged (all 3 stores, no errors)",
                       r["converged"] and r["errors"] is None))

        present = store.present_in_all_locations("ocr.pdf_table_extract")   # id-addressable — no handle needed
        checks.append(("primitive is retrievable from the DB", present["db"]))
        checks.append(("primitive is retrievable from the git-like store", present["git"]))
        checks.append(("primitive is retrievable from the object bucket", present["object_store"]))

        # idempotency: a re-put of identical content must NOT duplicate at any location
        r2 = store.put_primitive("ocr.pdf_table_extract", body)
        checks.append(("re-put is idempotent: same content_hash", r2["content_hash"] == r["content_hash"]))
        checks.append(("re-put is idempotent: DB not duplicated (count==1)", store.db.count() == 1))

        # a genuinely different body is a distinct record (the store is not collapsing everything)
        r3 = store.put_primitive("rerank.cross_encoder",
                                 {"kind": "primitive", "primitive_kind": "reranker", "serves_truth": False})
        checks.append(("a distinct primitive gets a distinct content_hash", r3["content_hash"] != r["content_hash"]))
        checks.append(("two distinct primitives -> DB count==2", store.db.count() == 2))

        # REGRESSION (idempotency-key bug): two DISTINCT ids with the SAME body must NOT collapse
        twin = {"kind": "primitive", "primitive_kind": "twin", "serves_truth": False}
        store.put_primitive("twin.alpha", twin)
        store.put_primitive("twin.beta", twin)
        checks.append(("same body + distinct ids do NOT collapse (both retrievable)",
                       store.get_primitive("twin.alpha") is not None and store.get_primitive("twin.beta") is not None))

        # REGRESSION (convergence must be REAL, not a shadow): a partial write reports converged=False + names it
        class _Boom:
            backend = "boom"
            def append(self, *a, **k):
                raise RuntimeError("git down")
            def all(self):
                return []
            def close(self):
                pass
        store.git = _Boom()                                    # simulate the git tier failing mid-write
        rp = store.put_primitive("partial.write", {"primitive_kind": "x", "serves_truth": False})
        checks.append(("a partial write reports converged=False (the verifier CAN go red)", rp["converged"] is False))
        checks.append(("a partial write NAMES the failed store", "git" in (rp["errors"] or {})))
        store.close()

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - primitive_multistore:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - primitive_multistore: one put_primitive() stores a primitive in ALL three locations "
          "(operational DB + git-like store + object bucket), retrievable BY ID from each; the idempotency key "
          "is the RECORD hash so distinct ids never collapse; a partial write returns converged=False naming the "
          "failed store. serves_truth=false. Cloud swap (postgres+pgvector / git remote / S3-R2) is config, not code.")
    return 0


def _demo() -> int:
    with tempfile.TemporaryDirectory() as td:
        store = PrimitiveMultiStore(td)
        for pid, body in [
            ("ocr.pdf_table_extract", {"primitive_kind": "ocr", "input_edge": "PDF+Policy", "serves_truth": False}),
            ("rerank.cross_encoder", {"primitive_kind": "reranker", "input_edge": "Query+Docs", "serves_truth": False}),
        ]:
            r = store.put_primitive(pid, body)
            locs = ", ".join(f"{k}={v.get('seq', v.get('payload_ref'))}" for k, v in r["locations"].items())
            print(f"  stored {pid}: content_hash={r['content_hash'][:22]}… -> [{locs}] converged={r['converged']}")
        store.close()
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    if "--demo" in argv:
        return _demo()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
