#!/usr/bin/env python3
"""Foundry worker — the queue-consumer that runs the async tier (see
`docs/architecture/cloud-architecture.md`).

The web tier enqueues **partition jobs**; workers pull them and run
`Foundry.run_partition` (auto-wiring a live model route from env when present),
append the funnel ledger, and ack — with retry/permanent-failure routing on failure. This is the
unit that scales: Phase 1 = a Render/Cloud-Run background worker; Phase 2 = a K8s
Deployment with **KEDA autoscaling on queue depth** (scale-to-zero). One container,
two commands (web vs `--serve`).

A `Queue` is a tiny protocol so the broker is swappable: ``InMemoryQueue`` (tests /
local), and in production a thin adapter over SQS / Cloud Tasks / Redis. Jobs are
plain dicts dispatched on ``kind``: partition jobs ``{"partition": str, "gaps": [gap...],
"kind": str}`` (idempotent because the foundry's content-hashing + resumable ledger
converge on re-runs) and freshness-CDC ``{"kind": "reingest", "source": registry-entry}``
jobs (re-fed through `scripts.ingest.feed`; idempotent because the store upserts by id).

Run ``python -m scripts.foundry.worker --self-test`` (offline) or ``--demo``.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

from scripts.foundry import batch_inference as batch
from scripts.foundry.contracts import Candidate
from scripts.foundry.model_route import from_env as route_from_env
from scripts.foundry.model_route import wire as wire_route
from scripts.foundry.pipeline import Foundry
from scripts.foundry.seeds import LEDGER_PATH, LocalSourceScout, _env, append_ledger
from scripts.foundry.sources import SourceStage
from scripts.foundry.store import from_env as store_from_env
from scripts.ingest.freshness import REINGEST_KIND  # the CDC job kind (single source — never retyped)

_MAX_RETRIES = 2


@runtime_checkable
class Queue(Protocol):
    def enqueue(self, job: dict) -> None: ...
    def pull(self) -> dict | None: ...
    def ack(self, job: dict) -> None: ...
    def nack(self, job: dict) -> None: ...


class InMemoryQueue:
    """Local/test broker. Production swaps a thin SQS / Cloud Tasks / Redis adapter."""

    def __init__(self) -> None:
        self._q: deque[dict] = deque()
        self.failed_permanently: list[dict] = []

    def enqueue(self, job: dict) -> None:
        self._q.append(job)

    def pull(self) -> dict | None:
        return self._q.popleft() if self._q else None

    def ack(self, job: dict) -> None:  # nothing to do for in-memory
        pass

    def nack(self, job: dict) -> None:
        self._q.append(job)

    def dead_letter(self, job: dict) -> None:
        """Compatibility alias; new code should call fail_permanently()."""
        self.fail_permanently(job)

    def fail_permanently(self, job: dict) -> None:
        self.failed_permanently.append(job)

    def __len__(self) -> int:
        return len(self._q)


def _default_foundry() -> Foundry:
    """A foundry with a REAL source scout: the live `WebSourceScout` over the source
    registry (`data/source-registry.jsonl`) when present, else the offline LocalSourceScout.
    (`route` wiring happens per-job in the worker.)"""
    from scripts.foundry.scrapers import DEFAULT_REGISTRY, WebSourceScout
    reg = Path(DEFAULT_REGISTRY)
    if reg.exists():
        registry = [json.loads(ln) for ln in reg.read_text(encoding="utf-8").splitlines()
                    if ln.strip() and not ln.startswith("#")]
        if registry:
            return Foundry(sources=SourceStage(WebSourceScout(registry)))
    return Foundry(sources=SourceStage(LocalSourceScout()))


class Worker:
    """Pulls jobs and dispatches on ``kind`` (partition → foundry, reingest → ingest.feed),
    with retry + ledger."""

    def __init__(self, *, foundry_factory: Callable[[], Foundry] = _default_foundry,
                 queue: Queue | None = None, ledger_path: Any = LEDGER_PATH,
                 store: Any = None, max_retries: int = _MAX_RETRIES, now_s: float | None = None,
                 reingest_fetcher: Any = None) -> None:
        self.foundry_factory = foundry_factory
        self.queue = queue or InMemoryQueue()
        self.ledger_path = ledger_path
        self.store = store   # a foundry.store.Store; None ⇒ skip persistence (tests/dry runs)
        self.max_retries = max_retries
        self._now_s = now_s
        # reingest-only seam: tests inject a CannedFetcher; None ⇒ feed's live HttpFetcher.
        self.reingest_fetcher = reingest_fetcher

    def process_one(self) -> dict | None:
        """Run one job; return its result line, or None if the queue is empty.

        Dispatch on ``job["kind"]``: the default/partition kinds run the foundry;
        ``reingest`` (enqueued by `scripts.ingest.freshness` CDC) re-feeds the changed
        source — previously these jobs silently no-opped through an empty partition run."""
        job = self.queue.pull()
        if job is None:
            return None
        try:
            if job.get("kind") == REINGEST_KIND:
                line = self._run_reingest(job)
            else:
                line = self._run_partition(job)
            self.queue.ack(job)
            return line
        except Exception as exc:  # noqa: BLE001 - a worker must not die on one bad job
            job["_attempts"] = int(job.get("_attempts", 0)) + 1
            if job["_attempts"] <= self.max_retries:
                self.queue.nack(job)
            else:
                fail = getattr(self.queue, "fail_permanently", None)
                if callable(fail):
                    fail(job)
                else:
                    dl = getattr(self.queue, "dead_letter", None)
                    if callable(dl):
                        dl(job)
            return {"error": repr(exc), "kind": job.get("kind", "real"),
                    "partition": job.get("partition", ""), "attempts": job["_attempts"]}

    def _run_partition(self, job: dict) -> dict:
        """The partition path: foundry run + store persist + funnel ledger.

        OPTIONAL CPU-batch lane (``scripts.foundry.batch_inference``): when ``OH_BATCH_LLM=local``
        and the job is NOT ``latency_class:"interactive"``, a local OpenAI-compatible server is
        stood up for the duration of THIS partition and the model route is pointed at it (cloud
        otherwise). Which lane actually served is recorded honestly on the ledger line
        (``served_by_lane``). When the lane is inactive (env unset) this is a pure no-op:
        ``batch.batch_server`` yields unavailable, ``route_env_override`` does nothing, and the
        path — including the ledger line — is byte-identical to the cloud-only behavior."""
        # The CPU-batch server starts ONLY when this job is batch-eligible (lane active AND not
        # latency_class:"interactive"); otherwise an unavailable lane is used (no server, no env
        # change). The provenance stamp is gated on the lane being ACTIVE (not on this job's
        # eligibility) so that while the lane is on, an interactive/degraded job is honestly
        # recorded as served_by_lane="cloud"; when the lane is entirely unset there is NO stamp,
        # keeping that path byte-identical to the cloud-only behavior.
        eligible = batch.job_wants_batch(job)
        lane_ctx = batch.batch_server() if eligible else batch.inactive_lane()
        with lane_ctx as lane:
            served_by = batch.LANE_TAG_CLOUD
            with batch.route_env_override(lane) as on_local_batch:
                if on_local_batch:
                    served_by = lane.lane_tag   # local-batch
                foundry = self.foundry_factory()
                route = route_from_env()
                if route is not None:
                    wire_route(foundry, route)   # live measurement + real embeddings if a key is set
                seeds = [Candidate(gap=g) for g in (job.get("gaps") or [])]
                partition = job.get("partition", "")
                result = foundry.run_partition(seeds, partition=partition)
            # persist the promoted row families (sqlite local / postgres cloud) — the experience DB
            if self.store is not None:
                for family, fam_rows in (result.get("rows") or {}).items():
                    if fam_rows:
                        self.store.write(family, fam_rows)
            line = append_ledger(
                self.ledger_path, kind=job.get("kind", "real"), partition=partition,
                result=result, date=time.strftime("%Y-%m-%d", time.gmtime(self._now_s)),
                env=_env(), ladder_item="worker partition",
            )
            # Provenance: stamp the serving lane whenever the batch lane is ACTIVE (records "cloud"
            # honestly for an interactive/degraded job that bypassed it). An unset lane adds no key,
            # so that path stays byte-identical to before.
            if batch.lane_active():
                line["served_by_lane"] = served_by
            return line

    def _run_reingest(self, job: dict) -> dict:
        """A freshness-CDC ``reingest`` job: re-feed the changed source through the REAL
        ingestion path (`scripts.ingest.feed.feed_source` — the handler freshness.py names),
        persisting the row families to this worker's store (None falls back to feed's
        env-default store: a reingest's whole point is persistence, so skipping it would be
        the silent no-op this dispatch removes). Honest failure routing: a missing source
        entry or a failed feed RAISES so the standard retry → failed_permanently path
        engages — a loud failure, never a silent ack. No funnel-ledger line is written
        (a feed summary is not a foundry funnel; fabricating one would lie about promotion)."""
        from scripts.ingest.feed import feed_source  # lazy: the partition path never needs ingest stages
        entry = job.get("source")
        if not isinstance(entry, dict) or not entry.get("url"):
            raise ValueError("reingest job carries no usable 'source' registry entry")
        result = feed_source(entry, fetcher=self.reingest_fetcher, store=self.store)
        if not result.get("ok"):
            raise RuntimeError(f"reingest failed for {result.get('url') or '?'}: "
                               f"{result.get('reason') or 'unknown'}")
        return {"kind": REINGEST_KIND, **result}

    def serve(self, *, max_jobs: int | None = None) -> int:
        """Drain the queue (or up to max_jobs). Returns the count processed."""
        n = 0
        while max_jobs is None or n < max_jobs:
            line = self.process_one()
            if line is None:
                break
            n += 1
        return n


def _self_test() -> int:
    import os
    import sys
    import tempfile
    from pathlib import Path

    from scripts.foundry.pipeline import _fixture

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # a job carrying the fixture's gaps; the factory provides the fixture's source scout
    fixture_foundry, seeds = _fixture()
    job = {"partition": "esg-csddd", "kind": "synthetic_demo", "gaps": [c.gap for c in seeds]}

    with tempfile.TemporaryDirectory() as tmp:
        ledger = Path(tmp) / "ledger.jsonl"
        q = InMemoryQueue()
        q.enqueue(job)
        check("queue holds the job", len(q) == 1)
        w = Worker(foundry_factory=lambda: _fixture()[0], queue=q, ledger_path=ledger, now_s=0)
        line = w.process_one()
        check("worker processed a job", line is not None and "error" not in line, str(line))
        check("queue drained after ack", len(q) == 0)
        check("ledger line written", ledger.exists() and ledger.read_text().strip())
        check("worker promoted components (offline measure)", line and line["promoted"] >= 1, str(line.get("promoted")))
        check("empty queue ⇒ process_one None", w.process_one() is None)

        # the worker PERSISTS promoted row families to the store (a real DB) — "saves to a DB"
        from scripts.foundry.store import SqliteStore
        st = SqliteStore(Path(tmp) / "store.sqlite")
        q3 = InMemoryQueue()
        q3.enqueue({"partition": "esg", "kind": "synthetic_demo", "gaps": [c.gap for c in _fixture()[1]]})
        Worker(foundry_factory=lambda: _fixture()[0], queue=q3, ledger_path=Path(tmp) / "l4.jsonl",
               store=st, now_s=0).process_one()
        check("worker persists row families to the store", st.count("normalized_object") >= 1, str(st.count("normalized_object")))
        check("store persists index_record (openness/delivery columns)", st.count("index_record") >= 1)

        # retry + permanent-failure state on a malformed job
        bad = InMemoryQueue()
        bad.enqueue({"partition": "boom", "gaps": "not-a-list"})   # gaps wrong type ⇒ raises
        bw = Worker(queue=bad, ledger_path=Path(tmp) / "l2.jsonl", max_retries=1, now_s=0)
        r1 = bw.process_one()
        check("poison job errors (not a crash)", r1 and "error" in r1, str(r1))
        check("poison job re-queued for retry", len(bad) == 1)
        bw.process_one()   # 2nd attempt > max_retries => failed_permanently
        check("malformed job failed permanently after retries", len(bad.failed_permanently) == 1 and len(bad) == 0)

        # serve drains multiple jobs
        q2 = InMemoryQueue()
        for i in range(3):
            q2.enqueue({"partition": f"p{i}", "kind": "synthetic_demo", "gaps": [c.gap for c in _fixture()[1]]})
        n = Worker(foundry_factory=lambda: _fixture()[0], queue=q2, ledger_path=Path(tmp) / "l3.jsonl", now_s=0).serve()
        check("serve drains the queue", n == 3 and len(q2) == 0, str(n))

        # ── OPTIONAL CPU-batch lane: provenance + latency-class gating (degrade-safe) ──
        # Drive a FAKE local OpenAI-compatible server through the worker (no real backend): the
        # worker must route the batch job's model calls at the local lane and stamp served_by_lane.
        import contextlib
        import subprocess as _sp

        saved_lane_env = {k: os.environ.get(k) for k in (
            batch.ENV_BATCH_LLM, batch.ENV_BATCH_BACKEND, batch.ENV_OLLAMA_BIN,
            batch.ENV_BATCH_PORT, batch.ENV_BATCH_MODEL)}
        sentinel = "WORKER-LOCAL-BATCH-OK"
        script = batch._fake_server_script(sentinel=sentinel)
        script_path = Path(tmp) / "fake_batch_server.py"
        script_path.write_text(script, encoding="utf-8")
        fport = batch._free_port()

        def _fake_spawn(argv, env=None, stdout=None, stderr=None):
            return _sp.Popen([sys.executable, str(script_path), batch.DEFAULT_BATCH_HOST, str(fport)],
                             stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)

        _orig_batch_server = batch.batch_server   # capture BEFORE patching (the fake delegates to it)

        @contextlib.contextmanager
        def _fake_batch_server(**_kw):
            with _orig_batch_server(health_timeout_s=15, _spawn=_fake_spawn) as ln:
                yield ln

        os.environ[batch.ENV_BATCH_LLM] = batch.LANE_LOCAL
        os.environ[batch.ENV_BATCH_BACKEND] = batch.BACKEND_OLLAMA
        os.environ[batch.ENV_OLLAMA_BIN] = sys.executable     # any real binary ⇒ detect() succeeds
        os.environ[batch.ENV_BATCH_PORT] = str(fport)
        os.environ[batch.ENV_BATCH_MODEL] = "fake-batch-gemma"
        try:
            batch.batch_server = _fake_batch_server   # inject the fake-server-backed lifecycle
            qb = InMemoryQueue()
            qb.enqueue({"partition": "batch-eligible", "kind": "synthetic_demo",
                        "latency_class": "batch", "gaps": [c.gap for c in _fixture()[1]]})
            bl = Worker(foundry_factory=lambda: _fixture()[0], queue=qb,
                        ledger_path=Path(tmp) / "lbatch.jsonl", now_s=0).process_one()
            check("batch lane: job served + ledgered (no crash)", bl is not None and "error" not in bl, str(bl))
            check("batch lane: served_by_lane stamped local-batch (honest provenance)",
                  bl and bl.get("served_by_lane") == batch.LANE_TAG_LOCAL_BATCH, str(bl.get("served_by_lane")))

            # an INTERACTIVE job must NOT use the batch lane even while it's active → stays cloud
            qi = InMemoryQueue()
            qi.enqueue({"partition": "interactive", "kind": "synthetic_demo",
                        "latency_class": "interactive", "gaps": [c.gap for c in _fixture()[1]]})
            il = Worker(foundry_factory=lambda: _fixture()[0], queue=qi,
                        ledger_path=Path(tmp) / "linter.jsonl", now_s=0).process_one()
            check("batch lane: interactive job stays on cloud (latency_class honored)",
                  il and il.get("served_by_lane") == batch.LANE_TAG_CLOUD, str(il.get("served_by_lane")))
        finally:
            batch.batch_server = _orig_batch_server
            for k, v in saved_lane_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

        # with the lane UNSET, a partition line carries NO served_by_lane key (byte-identical path)
        os.environ.pop(batch.ENV_BATCH_LLM, None)
        qn = InMemoryQueue()
        qn.enqueue({"partition": "cloud-only", "kind": "synthetic_demo", "gaps": [c.gap for c in _fixture()[1]]})
        nl = Worker(foundry_factory=lambda: _fixture()[0], queue=qn,
                    ledger_path=Path(tmp) / "lnolane.jsonl", now_s=0).process_one()
        check("lane unset: no served_by_lane key on the ledger line (no-op)",
              nl is not None and "served_by_lane" not in nl, str(nl))

        # ── reingest dispatch: freshness-CDC jobs are PROCESSED, never silent no-ops ──
        from scripts.foundry.scrapers import CannedFetcher
        entry = {"keywords": ["bsp.gov.ph"], "url": "https://bsp.gov.ph/aml",
                 "author": "Bangko Sentral ng Pilipinas", "license": "Government work (PH)",
                 "source_kind": "regulation", "gov": True, "name": "PH AML thresholds (BSP)"}
        page = ("BSP Circular 1230: the cash-withdrawal scrutiny threshold is PHP 1,000,000.\n\n"
                "Suspicious transactions must be reported regardless of amount.")
        qr = InMemoryQueue()
        qr.enqueue({"kind": REINGEST_KIND, "source": entry})
        st_r = SqliteStore(Path(tmp) / "reingest.sqlite")
        rl = Worker(queue=qr, ledger_path=Path(tmp) / "l5.jsonl", store=st_r, now_s=0,
                    reingest_fetcher=CannedFetcher({entry["url"]: page})).process_one()
        check("reingest job re-feeds the source for real (ok, acked)",
              rl is not None and rl.get("ok") is True and rl.get("kind") == REINGEST_KIND and len(qr) == 0, str(rl))
        check("reingest persisted corpus rows to the store",
              st_r.count("normalized_object") >= 1 and st_r.count("source_record") >= 1)
        check("reingest writes no fabricated funnel-ledger line", not (Path(tmp) / "l5.jsonl").exists())

        # a reingest that CANNOT run fails LOUD (failed_permanently), never a silent ack
        qb2 = InMemoryQueue()
        qb2.enqueue({"kind": REINGEST_KIND})                                  # no source entry at all
        rb = Worker(queue=qb2, ledger_path=Path(tmp) / "l6.jsonl", max_retries=0, now_s=0).process_one()
        check("malformed reingest errors loudly (kind tagged)",
              rb is not None and "error" in rb and rb.get("kind") == REINGEST_KIND, str(rb))
        check("malformed reingest failed permanently, not silently acked",
              len(qb2.failed_permanently) == 1 and len(qb2) == 0)
        qb3 = InMemoryQueue()
        qb3.enqueue({"kind": REINGEST_KIND, "source": entry})                 # source unreachable (404)
        rb3 = Worker(queue=qb3, ledger_path=Path(tmp) / "l7.jsonl", max_retries=0, now_s=0,
                     reingest_fetcher=CannedFetcher({})).process_one()
        check("unreachable reingest source fails loud (feed ok=False ⇒ error)",
              rb3 is not None and "error" in rb3 and len(qb3.failed_permanently) == 1, str(rb3))

    print(f"\n{'all worker self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _demo() -> int:
    from scripts.foundry.pipeline import _fixture
    q = InMemoryQueue()
    q.enqueue({"partition": "esg-csddd", "kind": "synthetic_demo", "gaps": [c.gap for c in _fixture()[1]]})
    line = Worker(foundry_factory=lambda: _fixture()[0], queue=q, now_s=0).process_one()
    print(json.dumps(line, indent=2))
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Foundry queue worker — runs partition jobs.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--demo", action="store_true", help="enqueue the fixture partition + process it")
    p.add_argument("--serve", action="store_true", help="drain a configured queue (production: wire a real Queue)")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.demo:
        return _demo()
    if args.serve:
        # local: durable SqliteQueue + SqliteStore; cloud: RedisQueue + Postgres — env-selected.
        from scripts.foundry.queues import from_env as queue_from_env
        q = queue_from_env()
        n = Worker(queue=q, store=store_from_env()).serve()
        print(json.dumps({"processed": n, "queue": type(q).__name__, "store": store_from_env().backend}))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
