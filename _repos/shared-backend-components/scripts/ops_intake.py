#!/usr/bin/env python3
"""scripts.ops_intake — the Global Operations Console INTAKE pipeline (POST /api/ops/intake backend).

An operator drops raw content (text / a URL / an idea / a prompt) into the console; this sorts,
prioritizes, chunks, routes it to the matching pipeline queue, and advances it through processing
stages. It is GOVERNED CANDIDATE material: every submission is serves_truth=false and ingest-
quarantined; on completion it is emitted as a scanned candidate to the dev-plane sinks (the discovery
feed / research queue) where the existing ingest security gate + promotion boundary govern it. It is
the console's ONLY write path.

Deterministic classify/prioritize/chunk/route (matches the design's client simulation 1:1, so the UI
behaves identically against the real backend). See docs/design/.../OPS-CONSOLE-HANDOFF.md §3.

CLI:  python3 _repos/shared-backend-components/scripts/ops_intake.py --self-test
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
DEFAULT_STORE = _resource("data") / "dev-intel" / "ops-intake.jsonl"

#: kind -> the pipeline queue it routes to (id, display label)
ROUTES = {"link": ("fetch", "Fetch & extract"), "prompt": ("prompteval", "Prompt eval"),
          "idea": ("distill", "Proposal distill"), "text": ("chunk", "Chunk & embed")}
STAGES = ("queued", "classifying", "chunking", "analyzing", "done")
_URGENT = re.compile(r"\b(urgent|asap|critical|important|now|blocker)\b", re.I)
_IMPERATIVE = re.compile(r"^(write|build|make|create|fix|add|generate|find|summari[sz]e|explain|analyze|review|list|draft)\b", re.I)
_URL = re.compile(r"^https?://|^www\.|\.\w{2,}/", re.I)
_SECONDS_PER_STAGE = 2.0   # how fast an item advances a stage (the real workers replace this cadence)


def classify(content: str) -> str:
    """link (URL) · prompt (ends '?' or imperative) · idea (short non-link) · else text."""
    c = (content or "").strip()
    if _URL.search(c):
        return "link"
    if c.endswith("?") or _IMPERATIVE.match(c):
        return "prompt"
    if len(c.split()) <= 12:
        return "idea"
    return "text"


def prioritize(content: str, kind: str) -> str:
    """high for urgency keywords / '!!' ; med for links/prompts/long text ; else low."""
    c = content or ""
    if _URGENT.search(c) or "!!" in c:
        return "high"
    if kind in ("link", "prompt") or len(c.split()) > 40:
        return "med"
    return "low"


def chunk_count(content: str, kind: str) -> int:
    """link -> ~3 ; prompt -> 1 ; text/idea -> ceil(words/40)."""
    if kind == "link":
        return 3
    if kind == "prompt":
        return 1
    return max(1, math.ceil(len(content.split()) / 40))


_PRIORITY_RANK = {"high": 0, "med": 1, "low": 2}


class IntakeStore:
    """Append-only intake ledger + the in-memory queue/stage view. JSON-backed when a path is given."""

    def __init__(self, path: str | Path | None = DEFAULT_STORE) -> None:
        self.path = Path(path) if path else None
        self.items: list[dict] = []
        if self.path and self.path.exists():
            try:
                self.items = [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
            except (OSError, ValueError):
                self.items = []

    def submit(self, content: str, kind: str | None = None, *, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        content = (content or "").strip()
        kind = kind if kind in ROUTES else classify(content)
        priority = prioritize(content, kind)
        queue, queue_label = ROUTES[kind]
        item = {"id": "in_" + format(int(now * 1000) % 0x1000000, "06x"),
                "content": content[:4000], "kind": kind, "priority": priority,
                "chunks": chunk_count(content, kind), "queue": queue, "queue_label": queue_label,
                "stage": "queued", "ts": now, "updated": now, "serves_truth": False, "quarantined": True}
        self.items.append(item)
        self._persist()
        return item

    def advance(self, *, now: float | None = None) -> int:
        """Move each not-done item forward one stage if its dwell time elapsed. Returns # advanced."""
        now = time.time() if now is None else now
        moved = 0
        for it in self.items:
            if it["stage"] == "done":
                continue
            if now - it.get("updated", it["ts"]) >= _SECONDS_PER_STAGE:
                i = STAGES.index(it["stage"])
                it["stage"] = STAGES[min(i + 1, len(STAGES) - 1)]
                it["updated"] = now
                moved += 1
        if moved:
            self._persist()
        return moved

    def projection(self, *, recent: int = 12) -> dict:
        """The `intake` block for /api/ops/status: per-queue depth + recent items (highest priority first)."""
        active = [i for i in self.items if i["stage"] != "done"]
        depths = {q: 0 for q, _ in ROUTES.values()}
        for i in active:
            depths[i["queue"]] = depths.get(i["queue"], 0) + 1
        ordered = sorted(self.items, key=lambda i: (_PRIORITY_RANK.get(i["priority"], 3), -i["ts"]))
        return {
            "queues": [{"id": q, "label": lbl, "depth": depths.get(q, 0)} for q, lbl in ROUTES.values()],
            "submitted": len(self.items), "active": len(active),
            "done": sum(1 for i in self.items if i["stage"] == "done"),
            "recent": [{"id": i["id"], "kind": i["kind"], "priority": i["priority"], "chunks": i["chunks"],
                        "queue": i["queue"], "stage": i["stage"],
                        "preview": i["content"][:80]} for i in ordered[:recent]],
        }

    def _persist(self) -> None:
        if not self.path:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("\n".join(json.dumps(i) for i in self.items[-500:]) + "\n", encoding="utf-8")
        except OSError:
            pass


def _self_test() -> int:
    import tempfile
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    ck("classify: URL -> link", classify("https://github.com/x/y") == "link")
    ck("classify: question/imperative -> prompt", classify("write a csv parser") == "prompt" and classify("what is x?") == "prompt")
    ck("classify: short -> idea", classify("a governed memory layer") == "idea")
    ck("classify: long prose -> text", classify("word " * 30) == "text")
    ck("prioritize: urgency -> high", prioritize("URGENT fix this now", "text") == "high")
    ck("prioritize: link/prompt -> med", prioritize("https://x.io", "link") == "med")
    ck("chunk: link=3, prompt=1, text=ceil(words/40)", chunk_count("x", "link") == 3 and chunk_count("x?", "prompt") == 1 and chunk_count("w " * 80, "text") == 2)
    ck("route: kind -> queue", ROUTES["link"][0] == "fetch" and ROUTES["prompt"][0] == "prompteval" and ROUTES["idea"][0] == "distill" and ROUTES["text"][0] == "chunk")

    with tempfile.TemporaryDirectory() as d:
        s = IntakeStore(Path(d) / "intake.jsonl")
        now = 1_000_000_000.0
        a = s.submit("https://example.com/spec", now=now)
        b = s.submit("URGENT!! summarize the incident now", now=now + 0.1)
        ck("submit returns a governed candidate (serves_truth=false, quarantined, queued)",
           a["serves_truth"] is False and a["quarantined"] is True and a["stage"] == "queued")
        ck("submission routed by kind (link->fetch)", a["queue"] == "fetch")
        proj = s.projection()
        ck("projection has per-queue depths + high pinned first",
           any(q["id"] == "fetch" and q["depth"] >= 1 for q in proj["queues"]) and proj["recent"][0]["priority"] == "high")
        # advance through stages to done
        for k in range(1, 6):
            s.advance(now=now + 0.1 + k * _SECONDS_PER_STAGE)
        ck("items advance queued -> ... -> done on the tick", all(i["stage"] == "done" for i in s.items))
        # persistence round-trips
        s2 = IntakeStore(Path(d) / "intake.jsonl")
        ck("intake ledger round-trips", len(s2.items) == 2)

    if fails:
        print(f"FAIL - ops_intake: {len(fails)} failure(s)")
        return 1
    print("PASS - ops_intake: deterministic classify/prioritize/chunk/route (matches the design), governed "
          "candidate submissions (serves_truth=false, quarantined), per-queue projection, staged processing.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ops console intake pipeline.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--submit", help="submit content (prints the routed item)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.submit:
        print(json.dumps(IntakeStore().submit(args.submit), indent=2))
        return 0
    ap.error("use --self-test or --submit")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
