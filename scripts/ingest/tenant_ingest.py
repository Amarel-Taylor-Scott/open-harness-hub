#!/usr/bin/env python3
"""scripts.ingest.tenant_ingest — the SCALABLE ingestion shape: tenant-partitioned, durable, idempotent.

Wires ingestion → decomposition into the durable work queue so it scales from a local SQLite demo to
thousands of tenants × millions of documents WITHOUT a rewrite (the broker/KEDA swap lives behind the
`DurableStore` enqueue/claim contract — see `docs/architecture/worker-fleet-architecture.md`).

Shape (the invariant that makes it scale):
  enqueue(tenant_id, doc) → per-TENANT queue lane (`ingest.<tenant_id>`) → STATELESS worker claims (lease)
  → decompose into atomic facts → ack. **Exactly-once business effect** via the idempotency key
  ``<tenant_id>:<doc_id>:<content_hash>`` — re-ingesting the same document version is a no-op; a CHANGED
  version (new content hash) is a new job. Workers are interchangeable; lease expiry recovers crashes.

Deterministic + offline (time injected). Local: one SQLite file + threaded/looped workers. Scalable:
swap the queue for SQS/RabbitMQ/NATS, the worker for a KEDA-scaled Deployment, the store for Postgres —
the partition key, idempotency key, claim/ack, and DLQ semantics are identical.

CLI:
    python3 scripts/ingest/tenant_ingest.py --self-test
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Callable, Iterable, Mapping

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.foundry.scrapers import content_hash
from scripts.ingest.decompose_structured import decompose_cfpb_complaint


def queue_for(tenant_id: str) -> str:
    """Per-tenant queue lane — the partition key. One slow/huge tenant never starves another."""
    return f"ingest.{tenant_id}"


def idempotency_key(tenant_id: str, doc_id: str, record: Mapping[str, Any]) -> str:
    """Exactly-once key: a document VERSION = (tenant, doc, content hash). Re-ingest = no-op; change = new."""
    return f"{tenant_id}:{doc_id}:{content_hash(json.dumps(record, sort_keys=True, default=str))}"


def enqueue_documents(store, tenant_id: str, documents: Iterable[Mapping[str, Any]], *,
                      max_attempts: int = 5) -> dict[str, Any]:
    """Enqueue ``documents`` (each {doc_id, record}) onto the tenant lane. Idempotent per version."""
    q = queue_for(tenant_id)
    enq, dup = [], 0
    for doc in documents:
        rec = doc["record"]
        idk = idempotency_key(tenant_id, doc["doc_id"], rec)
        r = store.enqueue(q, {"tenant_id": tenant_id, "doc_id": doc["doc_id"],
                              "content_hash": idk.rsplit(":", 1)[-1], "record": rec},
                          idempotency_key=idk, max_attempts=max_attempts)
        enq.append(r["id"])
        dup += 1 if r["duplicate"] else 0
    return {"queue": q, "enqueued": len(enq), "duplicates": dup, "new": len(enq) - dup}


def process_one(store, tenant_id: str, *, now: int, worker: str = "w",
                decomposer: Callable[..., dict] = decompose_cfpb_complaint, lease_seconds: int = 60) -> dict | None:
    """Claim one job from the tenant lane, decompose it into atomic facts, ack. None if the lane is drained."""
    job = store.claim(queue_for(tenant_id), worker=worker, lease_seconds=lease_seconds, now=now)
    if not job:
        return None
    p = job["payload"]
    try:
        d = decomposer(p["record"], native_id=p["doc_id"])
    except Exception as e:  # noqa: BLE001 — a bad doc retries, then dead-letters (never blocks the lane)
        status = store.nack(job["id"], error=f"{type(e).__name__}: {e}")
        return {"doc_id": p["doc_id"], "tenant_id": tenant_id, "status": status, "error": str(e)}
    store.ack(job["id"])
    return {"doc_id": p["doc_id"], "tenant_id": tenant_id, "status": "done",
            "facts": d["fact_count"], "allegations": d["allegation_count"], "components": d["components"]}


def drain(store, tenant_id: str, *, now: int, limit: int = 100000, worker: str = "w") -> list[dict]:
    """Drain a tenant lane (a worker's claim loop). Returns the processed results."""
    out: list[dict] = []
    for _ in range(limit):
        r = process_one(store, tenant_id, now=now, worker=worker)
        if r is None:
            break
        out.append(r)
    return out


def _self_test() -> int:
    import tempfile
    import shutil
    import threading

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    from scripts.durable_store import DurableStore

    tmp = tempfile.mkdtemp(prefix="tenant-ingest-")
    store = DurableStore(str(tmp + "/d.db"))

    def rec(issue):
        return {"product": "Credit reporting or other personal consumer reports", "issue": issue,
                "company": "Bureau A", "state": "CA", "company_response": "Closed with explanation",
                "timely": "Yes", "complaint_what_happened": "Not mine. Disputed twice."}

    docsA = [{"doc_id": f"A-{i}", "record": rec(f"issue {i}")} for i in range(3)]
    docsB = [{"doc_id": f"B-{i}", "record": rec(f"issue {i}")} for i in range(2)]

    ra = enqueue_documents(store, "acme", docsA)
    rb = enqueue_documents(store, "globex", docsB)
    check("per-tenant lanes (ingest.<tenant>)", ra["queue"] == "ingest.acme" and rb["queue"] == "ingest.globex")
    check("tenants isolated: acme=3 queued, globex=2 queued",
          store.stats("ingest.acme")["queued"] == 3 and store.stats("ingest.globex")["queued"] == 2)

    # idempotency: re-enqueue the SAME versions ⇒ all duplicates, no new jobs
    again = enqueue_documents(store, "acme", docsA)
    check("re-ingest same version = no-op (3 duplicates, 0 new)", again["duplicates"] == 3 and again["new"] == 0)
    check("still 3 queued for acme (no dupes added)", store.stats("ingest.acme")["queued"] == 3)
    # a CHANGED version (new content hash) = a new job
    changed = enqueue_documents(store, "acme", [{"doc_id": "A-0", "record": rec("issue 0 EDITED")}])
    check("changed document version = new job", changed["new"] == 1 and store.stats("ingest.acme")["queued"] == 4)

    # drain acme → atomic facts; globex untouched (isolation)
    out = drain(store, "acme", now=1000)
    check("drain acme processed all 4 jobs to facts", len(out) == 4 and all(o["status"] == "done" and o["facts"] > 0 for o in out))
    check("globex lane untouched by acme drain", store.stats("ingest.globex")["queued"] == 2)
    check("acme lane fully done (queued=0, done=4)", store.stats("ingest.acme")["queued"] == 0 and store.stats("ingest.acme")["done"] == 4)

    # horizontal scale: two concurrent workers on globex must NOT double-process
    seen, lock = [], threading.Lock()

    def _w(name):
        for r in drain(store, "globex", now=2000, worker=name):
            with lock:
                seen.append(r["doc_id"])

    ts = [threading.Thread(target=_w, args=(f"w{n}",)) for n in range(3)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    check("3 concurrent workers processed each globex doc EXACTLY once (no double-process)",
          sorted(seen) == ["B-0", "B-1"], str(sorted(seen)))
    check("globex lane done (no leftovers, no dups)", store.stats("ingest.globex")["done"] == 2 and store.stats("ingest.globex")["queued"] == 0)

    # scale math (documented invariant, not a runtime claim)
    check("idempotency key = tenant:doc:content_hash", idempotency_key("t", "d", {"a": 1}).startswith("t:d:") and len(idempotency_key("t", "d", {"a": 1})) > 12)

    store.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'all tenant_ingest self-tests passed (per-tenant lanes; idempotent per doc-version; tenant isolation; concurrent workers process each doc exactly once → atomic facts).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Tenant-partitioned, durable, idempotent ingestion → atomic facts.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
