#!/usr/bin/env python3
"""Foundry worker — the queue-consumer that runs the async tier (see
`docs/architecture/cloud-architecture.md`).

The web tier enqueues **partition jobs**; workers pull them and run
`Foundry.run_partition` (auto-wiring a live model route from env when present),
append the funnel ledger, and ack — with retry/dead-letter on failure. This is the
unit that scales: Phase 1 = a Render/Cloud-Run background worker; Phase 2 = a K8s
Deployment with **KEDA autoscaling on queue depth** (scale-to-zero). One container,
two commands (web vs `--serve`).

A `Queue` is a tiny protocol so the broker is swappable: ``InMemoryQueue`` (tests /
local), and in production a thin adapter over SQS / Cloud Tasks / Redis. Jobs are
plain dicts ``{"partition": str, "gaps": [gap...], "kind": str}`` — idempotent because
the foundry's content-hashing + resumable ledger converge on re-runs.

Run ``python -m scripts.foundry.worker --self-test`` (offline) or ``--demo``.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import deque
from typing import Any, Callable, Protocol, runtime_checkable

from scripts.foundry.contracts import Candidate
from scripts.foundry.model_route import from_env as route_from_env
from scripts.foundry.model_route import wire as wire_route
from scripts.foundry.pipeline import Foundry
from scripts.foundry.seeds import LEDGER_PATH, LocalSourceScout, _env, append_ledger
from scripts.foundry.sources import SourceStage

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
        self.dead: list[dict] = []

    def enqueue(self, job: dict) -> None:
        self._q.append(job)

    def pull(self) -> dict | None:
        return self._q.popleft() if self._q else None

    def ack(self, job: dict) -> None:  # nothing to do for in-memory
        pass

    def nack(self, job: dict) -> None:
        self._q.append(job)

    def dead_letter(self, job: dict) -> None:
        self.dead.append(job)

    def __len__(self) -> int:
        return len(self._q)


def _default_foundry() -> Foundry:
    """A foundry with the offline local scout; `route` wiring happens per-job in the worker."""
    return Foundry(sources=SourceStage(LocalSourceScout()))


class Worker:
    """Pulls partition jobs and runs them through the foundry, with retry + ledger."""

    def __init__(self, *, foundry_factory: Callable[[], Foundry] = _default_foundry,
                 queue: Queue | None = None, ledger_path: Any = LEDGER_PATH,
                 max_retries: int = _MAX_RETRIES, now_s: float | None = None) -> None:
        self.foundry_factory = foundry_factory
        self.queue = queue or InMemoryQueue()
        self.ledger_path = ledger_path
        self.max_retries = max_retries
        self._now_s = now_s

    def process_one(self) -> dict | None:
        """Run one job; return the ledger line, or None if the queue is empty."""
        job = self.queue.pull()
        if job is None:
            return None
        try:
            foundry = self.foundry_factory()
            route = route_from_env()
            if route is not None:
                wire_route(foundry, route)   # live measurement + real embeddings if a key is set
            seeds = [Candidate(gap=g) for g in (job.get("gaps") or [])]
            partition = job.get("partition", "")
            result = foundry.run_partition(seeds, partition=partition)
            line = append_ledger(
                self.ledger_path, kind=job.get("kind", "real"), partition=partition,
                result=result, date=time.strftime("%Y-%m-%d", time.gmtime(self._now_s)),
                env=_env(), ladder_item="worker partition",
            )
            self.queue.ack(job)
            return line
        except Exception as exc:  # noqa: BLE001 - a worker must not die on one bad job
            job["_attempts"] = int(job.get("_attempts", 0)) + 1
            if job["_attempts"] <= self.max_retries:
                self.queue.nack(job)
            else:
                dl = getattr(self.queue, "dead_letter", None)
                if callable(dl):
                    dl(job)
            return {"error": repr(exc), "partition": job.get("partition", ""), "attempts": job["_attempts"]}

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

        # retry + dead-letter on a poison job
        bad = InMemoryQueue()
        bad.enqueue({"partition": "boom", "gaps": "not-a-list"})   # gaps wrong type ⇒ raises
        bw = Worker(queue=bad, ledger_path=Path(tmp) / "l2.jsonl", max_retries=1, now_s=0)
        r1 = bw.process_one()
        check("poison job errors (not a crash)", r1 and "error" in r1, str(r1))
        check("poison job re-queued for retry", len(bad) == 1)
        bw.process_one()   # 2nd attempt > max_retries ⇒ dead-letter
        check("poison job dead-lettered after retries", len(bad.dead) == 1 and len(bad) == 0)

        # serve drains multiple jobs
        q2 = InMemoryQueue()
        for i in range(3):
            q2.enqueue({"partition": f"p{i}", "kind": "synthetic_demo", "gaps": [c.gap for c in _fixture()[1]]})
        n = Worker(foundry_factory=lambda: _fixture()[0], queue=q2, ledger_path=Path(tmp) / "l3.jsonl", now_s=0).serve()
        check("serve drains the queue", n == 3 and len(q2) == 0, str(n))

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
        # Production: pull from Redis (REDIS_URL). KEDA scales this on the queue's LLEN.
        from scripts.foundry.queues import from_env as queue_from_env
        q = queue_from_env()
        if q is None:
            print(json.dumps({"processed": 0, "note": "set REDIS_URL (+ pip install redis) for production --serve"}))
            return 0
        print(json.dumps({"processed": Worker(queue=q).serve()}))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
