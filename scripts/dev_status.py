#!/usr/bin/env python3
"""scripts.dev_status — assemble the DEVELOPMENT status feed for the dev/flywheel dashboard.

This is the BUILDER's view, distinct from the end-to-end ops/admin dashboard (which shows the
*product* firing) and any user dashboard. It reads the artifacts the autonomous loop already
produces — `.agent/flywheel-health.jsonl` (per-tick proof health), `.agent/baltor-goal-loop-log.md`
(pass receipts), `research/future-ideas.md` (backlog), `e2e/artifacts/review-pack/REVIEW-latest.md`
(latest review) — and returns one JSON the dashboard polls. Pure parsers (text → data) so they are
unit-testable; `build_dev_status()` does the file IO. No 2nd server, no new state: the admin server
serves this at `/api/dev/status`.

CLI:
    python3 scripts/dev_status.py             # print the assembled dev status (JSON)
    python3 scripts/dev_status.py --self-test  # offline deterministic proof of the parsers
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
HEALTH_LOG = _REPO / ".agent" / "flywheel-health.jsonl"
RECEIPTS = _REPO / ".agent" / "baltor-goal-loop-log.md"
BACKLOG = _REPO / "research" / "future-ideas.md"
REVIEW_LATEST = _REPO / "e2e" / "artifacts" / "review-pack" / "REVIEW-latest.md"
CATALOG = _REPO / "catalog"
_REGISTRY_EXTS = (".yaml", ".yml", ".json", ".md")

#: how many recent items each section caps at (single source).
HISTORY_TICKS = 30
RECENT_PASSES = 25

_PASS_RE = re.compile(r"^##\s+(.*\S)\s*$")
_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_CID_RE = re.compile(r"\b(C\d+)\b")
_BACKLOG_ITEM_RE = re.compile(r"^\s*\d+\.\s+\*\*(.+?)\*\*")
_SECTION_RE = re.compile(r"^##\s+(.*\S)\s*$")
_REVIEW_OVERALL_RE = re.compile(r"\*\*Overall:\s*(\d+)/(\d+)\s*checks passed\s*—\s*(.+?)\*\*")
_REVIEW_WHEN_RE = re.compile(r"^#\s+.*\(([^)]+)\)")


# ── pure parsers (text → data) ───────────────────────────────────────────────
def parse_health(lines: list[str]) -> dict:
    """Latest health record + a compact history of (ts, green_count, total, all_green)."""
    recs = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            recs.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    if not recs:
        return {"latest": None, "history": []}
    latest = recs[-1]
    proofs = sorted(
        ({"label": k, "ok": bool(v.get("ok")), "detail": v.get("detail", "")}
         for k, v in (latest.get("results") or {}).items()),
        key=lambda p: (p["ok"], p["label"]),  # failures first, then alphabetical
    )
    history = [{"ts": r.get("ts"), "green_count": r.get("green_count"),
                "total": r.get("total"), "all_green": bool(r.get("all_green"))}
               for r in recs[-HISTORY_TICKS:]]
    return {
        "latest": {"ts": latest.get("ts"), "all_green": bool(latest.get("all_green")),
                   "green_count": latest.get("green_count"), "total": latest.get("total"),
                   "proofs": proofs, "red": [p["label"] for p in proofs if not p["ok"]]},
        "history": history,
    }


def parse_passes(text: str) -> list[dict]:
    """Pass receipts (newest first): id (CNN), date, title — from the loop log's '## ' headers."""
    out = []
    for ln in text.splitlines():
        m = _PASS_RE.match(ln)
        if not m:
            continue
        head = m.group(1)
        date = (_DATE_RE.search(head) or [None]) and (_DATE_RE.search(head).group(1) if _DATE_RE.search(head) else None)
        cid = _CID_RE.search(head)
        title = head
        if "—" in head:
            title = head.split("—", 1)[1].strip()
        out.append({"id": cid.group(1) if cid else None, "date": date, "title": title})
    return list(reversed(out))[:RECENT_PASSES]


def parse_backlog(text: str) -> list[dict]:
    """Backlog items with section (P0/P1/…) + status (done/parked/open)."""
    out = []
    section = ""
    for ln in text.splitlines():
        sm = _SECTION_RE.match(ln)
        if sm:
            section = sm.group(1)
            continue
        im = _BACKLOG_ITEM_RE.match(ln)
        if not im:
            continue
        title = im.group(1).rstrip(".")
        low = ln.lower()
        status = ("done" if ("✅" in ln or " done" in low) else
                  "parked" if ("owner" in low or "out-of-scope" in low or "sign-off" in low) else "open")
        out.append({"section": section, "title": title, "status": status})
    return out


def parse_review(text: str) -> dict:
    m = _REVIEW_OVERALL_RE.search(text)
    w = _REVIEW_WHEN_RE.search(text)
    if not m:
        return {"passed": None, "total": None, "verdict": None, "when": (w.group(1) if w else None)}
    return {"passed": int(m.group(1)), "total": int(m.group(2)),
            "verdict": m.group(3).strip(), "when": (w.group(1) if w else None)}


def _registry() -> dict:
    """Component/context + tool registry: file counts per catalog type (the substrate made visible)."""
    types: dict[str, int] = {}
    if CATALOG.is_dir():
        for sub in sorted(p for p in CATALOG.iterdir() if p.is_dir()):
            types[sub.name] = sum(1 for f in sub.rglob("*") if f.is_file() and f.suffix in _REGISTRY_EXTS)
    return {"types": types, "total": sum(types.values()), "type_count": len(types)}


def _mcp() -> dict:
    """MCP / gateway bridges registered as adapters (+ whether the manifest scanner is wired)."""
    gw = CATALOG / "adapters" / "gateway"
    servers = sorted(p.name for p in gw.glob("*.y*ml")) if gw.is_dir() else []
    return {"servers": servers, "count": len(servers),
            "scanner": "scripts/scan_mcp_manifests.py" if (_REPO / "scripts" / "scan_mcp_manifests.py").exists() else None}


def _durable() -> dict:
    """Read the durable store (the source of truth) as a projection: mode, event count, queue stats, status."""
    import os
    db = os.environ.get("BALTOR_DURABLE_DB", "") or str(_REPO / ".agent" / "durable.db")
    if not Path(db).exists():
        return {"mode": "off", "db": db, "events": 0, "queues": {}, "status": "off", "error": ""}
    try:
        from scripts.durable_store import DurableStore
        s = DurableStore(db)
        out = {"mode": "on", "db": db, "events": s.event_count(), "queues": s.queue_overview(),
               "status": s.get_meta("durable_status", "unknown"), "error": s.get_meta("durable_error", "")}
        s.close()
        return out
    except Exception as e:  # noqa: BLE001
        return {"mode": "error", "db": db, "events": 0, "queues": {}, "status": "red", "error": f"{type(e).__name__}: {e}"}


def _pipelines() -> dict:
    """Projection of the Pipeline Runtime: registered manifests + run ledger (the source of truth)."""
    import os
    from scripts.pipeline_runtime.specs import discover
    sp = discover()
    out: dict = {"registered": [{"ref": s.ref, "status": s.status} for s in sp.values()],
                 "active": sum(1 for s in sp.values() if s.status == "active"),
                 "experimental": sum(1 for s in sp.values() if s.status == "experimental")}
    db = os.environ.get("BALTOR_DURABLE_DB", "") or str(_REPO / ".agent" / "durable.db")
    if Path(db).exists():
        try:
            from scripts.durable_store import DurableStore
            from scripts.pipeline_runtime.store import PipelineLedger
            s = DurableStore(db)
            led = PipelineLedger(s)
            out["overview"] = led.overview()
            out["recent_runs"] = led.list_runs(limit=8)
            s.close()
        except Exception as e:  # noqa: BLE001
            out["error"] = f"{type(e).__name__}: {e}"
    return out


def _engines_from_health(health: dict) -> dict:
    """Derive the connected-engine count from the check_event_integration proof detail (single source)."""
    detail = ""
    latest = health.get("latest") or {}
    for p in latest.get("proofs", []):
        if p["label"] == "check_event_integration":
            detail = p.get("detail", "")
            break
    m = re.search(r"([A-Za-z]+)\s+modules CONNECTED", detail)
    return {"phrase": (m.group(0) if m else None)}


# ── file IO ──────────────────────────────────────────────────────────────────
def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def build_dev_status() -> dict:
    health = parse_health(_read(HEALTH_LOG).splitlines())
    return {
        "flywheel": health.get("latest"),
        "history": health.get("history", []),
        "engines": _engines_from_health(health),
        "passes": parse_passes(_read(RECEIPTS)),
        "backlog": parse_backlog(_read(BACKLOG)),
        "review": parse_review(_read(REVIEW_LATEST)),
        "registry": _registry(),
        "mcp": _mcp(),
        "durable": _durable(),
        "pipelines": _pipelines(),
        "sources": {  # so the dashboard can show provenance of every panel (no hidden magic)
            "flywheel": ".agent/flywheel-health.jsonl",
            "passes": ".agent/baltor-goal-loop-log.md",
            "backlog": "research/future-ideas.md",
            "review": "e2e/artifacts/review-pack/REVIEW-latest.md",
            "registry": "catalog/",
            "mcp": "catalog/adapters/gateway/",
        },
    }


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # parse_health: failures sorted first; history compacted
    lines = [
        json.dumps({"ts": "t1", "all_green": False, "green_count": 1, "total": 2,
                    "results": {"a": {"ok": True, "detail": "ok-a"}, "b": {"ok": False, "detail": "boom-b"}}}),
        json.dumps({"ts": "t2", "all_green": True, "green_count": 2, "total": 2,
                    "results": {"a": {"ok": True, "detail": "ok-a"}, "b": {"ok": True, "detail": "ok-b"}}}),
        "not json — skipped",
    ]
    h = parse_health(lines)
    check("health latest = newest record", h["latest"]["ts"] == "t2" and h["latest"]["green_count"] == 2)
    check("health history compacted, bad line skipped", len(h["history"]) == 2 and h["history"][0]["ts"] == "t1")
    h_red = parse_health(lines[:1])
    check("red proof listed (failures first)", h_red["latest"]["red"] == ["b"] and h_red["latest"]["proofs"][0]["label"] == "b")

    passes = parse_passes("## 2026-06-04 · Pass C17 — research\nblah\n## 2026-06-05 · Pass C18 — reporter\n")
    check("passes newest-first w/ id+date+title", passes[0]["id"] == "C18" and passes[0]["date"] == "2026-06-05" and passes[0]["title"] == "reporter")

    bl = parse_backlog("## P0\n1. **Do thing.** ✅ DONE rest\n2. **Other thing.** needs owner sign-off\n## P2\n3. **Open one.** just text\n")
    check("backlog parses section+status", bl[0]["status"] == "done" and bl[1]["status"] == "parked" and bl[2]["section"] == "P2" and bl[2]["status"] == "open")

    rv = parse_review("# Baltor — Review Pack (2026-06-05T00:51:29Z)\n\n**Overall: 6/6 checks passed — ALL GREEN ✅**\n")
    check("review parses passed/total/when", rv["passed"] == 6 and rv["total"] == 6 and rv["when"].startswith("2026-06-05"))

    eng = _engines_from_health({"latest": {"proofs": [{"label": "check_event_integration", "detail": "… Nine modules CONNECTED."}]}})
    check("engines phrase derived", eng["phrase"] == "Nine modules CONNECTED")

    reg = _registry()
    check("registry counts real catalog types (>=5 types, total>0)", reg["type_count"] >= 5 and reg["total"] > 0, str(reg))
    mcp = _mcp()
    check("mcp lists gateway bridge(s) + scanner wired", mcp["count"] >= 1 and bool(mcp["scanner"]), str(mcp))

    # end-to-end on the REAL repo artifacts (must run + have a green flywheel today)
    real = build_dev_status()
    check("real build_dev_status runs", isinstance(real, dict) and "flywheel" in real)
    check("real flywheel record present + green_count > 0",
          real["flywheel"] is not None and (real["flywheel"]["green_count"] or 0) > 0,
          str(real.get("flywheel") and real["flywheel"].get("green_count")))
    check("real passes parsed (>=1)", len(real["passes"]) >= 1)
    check("real build has registry + mcp", "registry" in real and "mcp" in real and real["registry"]["total"] > 0)
    check("real build has durable projection (mode/status/events)",
          "durable" in real and {"mode", "status", "events", "queues"} <= set(real["durable"]))
    check("real build has pipelines projection (registered manifests)",
          "pipelines" in real and real["pipelines"]["active"] >= 1 and any(r["ref"].startswith("cfpb_structured_ingest@") for r in real["pipelines"]["registered"]))

    print(f"\n{'all dev_status self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Assemble the development status feed for the dev/flywheel dashboard.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    print(json.dumps(build_dev_status(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
