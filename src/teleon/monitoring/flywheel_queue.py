"""monitoring.flywheel_queue — wire the service-heartbeat Flywheel onto the DURABLE work queue (#22).

`Flywheel.tick()` detects failing surfaces and emits `ResolutionProposal` records. Held in memory, a crash loses them.
This wires them onto `scripts.work_queue` (durable SQLite: idempotent enqueue by content-hash, lease-claim, dead-letter,
expired-lease reclaim = crash-resume): each proposal is enqueued, a stateless worker drains + records it. The SAME code
runs across the 3 demo stages —
  • local : SQLite queue on disk (this module's default)
  • tunnel: identical code; the queue file lives beside the tunneled service
  • infra : swap the queue store to Postgres via the record_store port (no caller change)
serves_truth=false (proposes + records; never executes a destructive repair).

  python3 -m src.teleon.monitoring.flywheel_queue --self-test
  python3 -m src.teleon.monitoring.flywheel_queue --demo
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import work_queue  # noqa: E402
from src.teleon.monitoring.flywheel import Flywheel, HeartbeatResult  # noqa: E402

TOPIC = "flywheel_resolutions"


def enqueue_proposals(tick_result: dict, db: Path | None = None) -> int:
    """Enqueue each ResolutionProposal from a flywheel tick onto the durable queue (idempotent). Returns #new enqueued."""
    db = db or work_queue.DB
    n = 0
    for p in tick_result.get("proposals", []):
        body = p.get("body", p)
        payload = {"surface": body.get("surface"), "action": body.get("action"),
                   "status": body.get("status"), "consecutive_failures": body.get("consecutive_failures"),
                   "rationale": body.get("rationale")}
        if work_queue.enqueue(TOPIC, payload, db=db):
            n += 1
    return n


def process_resolution(payload: dict) -> None:
    """Worker handler: record/act on a resolution. Here it just records (governed); real infra dispatches the repair."""
    # serves_truth=false: a proposal is a candidate action, not an executed one.
    _ = payload.get("surface"), payload.get("action")


def drain(worker: str = "flywheel", max_items: int | None = None, db: Path | None = None) -> dict:
    """Stateless drain of ready resolutions (crash-safe: unacked items reappear after their lease). A manual
    claim→process→ack loop (not run_worker) so a bounded drain ignores the long-lived QUEUE_STOP flag + idle sleep."""
    import json
    db = db or work_queue.DB
    processed = 0
    while max_items is None or processed < max_items:
        rows = work_queue.claim(TOPIC, worker, lease=30.0, n=10, db=db)
        if not rows:
            break
        for item_id, payload in rows:
            process_resolution(json.loads(payload) if isinstance(payload, str) else payload)
            work_queue.ack(item_id, db=db)
            processed += 1
            if max_items is not None and processed >= max_items:
                break
    return {"topic": TOPIC, "processed": processed}


def _down_pinger(surface: dict, *, now: str) -> HeartbeatResult:
    return HeartbeatResult(surface=surface.get("service_id", "demo_surface"), up=False, latency_ms=None, at=now, detail="down")


def self_test() -> int:
    db = Path(tempfile.mkdtemp(prefix="fwq_")) / "q.db"
    fw = Flywheel(surfaces=[{"service_id": "demo_surface"}])

    def ready() -> int:
        return work_queue.stats(TOPIC, db=db).get(TOPIC, {}).get("ready", 0)

    # tick enough times to cross the failure threshold and emit proposals
    proposals, last = 0, None
    for i in range(6):
        last = fw.tick(_down_pinger, now=f"2026-06-25T00:00:0{i}Z")
        proposals += enqueue_proposals(last, db=db)
    assert proposals >= 1, f"flywheel should enqueue ≥1 durable resolution, got {proposals}"
    assert ready() >= 1, f"resolutions must be durably ready, got {ready()}"

    # idempotent: re-enqueuing the SAME tick result does not duplicate (content-hash)
    assert enqueue_proposals(last, db=db) == 0, "identical resolution must dedupe, not re-enqueue"

    # crash-resume: claim with a zero lease (instantly expired), then it must be reclaimable
    assert work_queue.claim(TOPIC, "w_crash", lease=0.0, n=1, db=db), "claim should hand out a ready item"
    assert work_queue.claim(TOPIC, "w_recover", lease=30.0, n=1, db=db), "unacked (crashed) item must be reclaimable"

    drain(max_items=50, db=db)
    assert ready() == 0, "drain must clear all ready resolutions"
    print(f"flywheel_queue self-test: OK ({proposals} durable resolutions · idempotent · crash-resumable · drained)")
    return 0


def demo() -> int:
    db = Path(tempfile.mkdtemp(prefix="fwq_demo_")) / "q.db"
    fw = Flywheel(surfaces=[{"service_id": "demo_surface"}])
    for i in range(6):
        enqueue_proposals(fw.tick(_down_pinger, now=f"2026-06-25T00:00:0{i}Z"), db=db)
    print("local stage — durable queue:", work_queue.stats(TOPIC, db=db))
    drain(max_items=50, db=db)
    print("after drain:", work_queue.stats(TOPIC, db=db))
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--demo" in argv:
        return demo()
    print("usage: flywheel_queue --self-test | --demo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
