"""observer.session_store — the normalized session model + the accept/reject OUTCOME loop (the Spotter memo §8).

A session is a time-ordered stream of events; an intervention records what the Observer surfaced AND the human's
outcome (accepted | reused | dismissed | ignored). That outcome field is the moat: a competitor with the same hooks
and the same model does NOT have your accept/reject signal — it (1) tunes per-type thresholds and (2) tells you which
heuristics/registry entries over- or under-fire.

Append-only + local-first (JSONL under data/dev-intel/observer_sessions/, the config/operational tier). Storage is a
PORT: this is the local-file fork; a sidecar (sqlite) / server (Postgres) fork keys the same records elsewhere. The
outcome is recorded as an appended event (latest-wins), so the log stays append-only (no destructive mutation —
lossless). serves_truth=false; PII-bearing content is the caller's to redact before storing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_DIR = _REPO / "data" / "dev-intel" / "observer_sessions"

OUTCOMES = ("accepted", "reused", "dismissed", "ignored")  # the accept/reject signal vocabulary (single source)
EVENT_KINDS = ("prompt", "tool_use", "tool_result", "edit", "cmd", "error", "idle", "text")


def _cid(*parts: str) -> str:
    """Content-addressed id (stable across runs — no Date.now/random; deterministic for replay/dedup)."""
    return hashlib.sha256("␟".join(parts).encode()).hexdigest()[:16]


def session_record(session_id: str, surface: str, repo: str = "", started_at: str = "", ended_at: str = "") -> dict:
    return {"record": "session", "id": session_id, "surface": surface, "repo": repo,
            "started_at": started_at, "ended_at": ended_at, "serves_truth": False}


def event_record(session_id: str, t: int, kind: str, payload: str) -> dict:
    if kind not in EVENT_KINDS:
        raise ValueError(f"unknown event kind {kind!r}; one of {EVENT_KINDS}")
    return {"record": "event", "session_id": session_id, "t": t, "kind": kind,
            "id": _cid(session_id, str(t), kind), "payload": payload[:2000], "serves_truth": False}


def intervention_record(session_id: str, t: int, type_: str, confidence: float, message: str,
                        source_ref: dict | None = None) -> dict:
    return {"record": "intervention", "session_id": session_id, "t": t, "type": type_,
            "id": _cid(session_id, str(t), type_, message), "confidence": confidence, "message": message,
            "source_ref": source_ref or {}, "outcome": None, "serves_truth": False, "candidate": True}


def outcome_record(session_id: str, intervention_id: str, outcome: str) -> dict:
    """The accept/reject SIGNAL — appended (latest-wins), never an in-place mutation (append-only + lossless)."""
    if outcome not in OUTCOMES:
        raise ValueError(f"unknown outcome {outcome!r}; one of {OUTCOMES}")
    return {"record": "outcome", "session_id": session_id, "intervention_id": intervention_id,
            "outcome": outcome, "serves_truth": False}


def _path(session_id: str) -> Path:
    return _DIR / f"{session_id}.jsonl"


def append(record: dict) -> None:
    """Append one record to its session log (append-only; creates the dir/file as needed)."""
    sid = record.get("session_id") or record.get("id")
    _DIR.mkdir(parents=True, exist_ok=True)
    with _path(sid).open("a") as f:
        f.write(json.dumps(record) + "\n")


def load(session_id: str) -> list[dict]:
    p = _path(session_id)
    return [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()] if p.exists() else []


def resolve_outcomes(records: list[dict]) -> dict:
    """Fold the append-only log into current intervention outcomes (latest outcome wins) — the tuning signal."""
    interventions = {r["id"]: r for r in records if r.get("record") == "intervention"}
    for r in records:
        if r.get("record") == "outcome" and r["intervention_id"] in interventions:
            interventions[r["intervention_id"]]["outcome"] = r["outcome"]
    return interventions


def outcome_stats(records: list[dict]) -> dict:
    """Per-type accept/reject rates — what tunes the thresholds. accepted+reused = acted; dismissed+ignored = rejected."""
    resolved = resolve_outcomes(records)
    by_type: dict[str, dict] = {}
    for iv in resolved.values():
        d = by_type.setdefault(iv["type"], {"acted": 0, "rejected": 0, "pending": 0})
        o = iv.get("outcome")
        if o in ("accepted", "reused"):
            d["acted"] += 1
        elif o in ("dismissed", "ignored"):
            d["rejected"] += 1
        else:
            d["pending"] += 1
    return by_type


def _self_test() -> int:
    fails, checks = [], 0

    def ck(name, ok):
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}")

    # build a session entirely in-memory (no disk write in the gate beyond a unique throwaway id)
    sid = "selftest_" + _cid("observer_session_store_selftest")
    recs = [
        session_record(sid, "claude_code", repo="demo"),
        event_record(sid, 0, "prompt", "let me build a custom retry"),
        intervention_record(sid, 0, "stack_reinvention", 0.82, "tenacity already does this"),
    ]
    iv_id = recs[-1]["id"]
    ck("event kind is validated", _raises(lambda: event_record(sid, 1, "bogus", "x")))
    ck("outcome value is validated", _raises(lambda: outcome_record(sid, iv_id, "bogus")))
    ck("ids are content-addressed + stable", recs[-1]["id"] == intervention_record(sid, 0, "stack_reinvention", 0.82, "tenacity already does this")["id"])
    ck("intervention starts with no outcome", recs[-1]["outcome"] is None)

    # the accept/reject signal: dismiss it, then it folds latest-wins
    recs2 = recs + [outcome_record(sid, iv_id, "dismissed")]
    resolved = resolve_outcomes(recs2)
    ck("outcome folds onto the intervention (append-only)", resolved[iv_id]["outcome"] == "dismissed")
    # a later outcome supersedes (lossless: both stay in the log)
    recs3 = recs2 + [outcome_record(sid, iv_id, "accepted")]
    ck("latest outcome wins", resolve_outcomes(recs3)[iv_id]["outcome"] == "accepted")
    ck("both outcomes preserved in the log (lossless)", sum(1 for r in recs3 if r.get("record") == "outcome") == 2)

    stats = outcome_stats(recs3)
    ck("per-type stats compute (the tuning signal)", stats["stack_reinvention"]["acted"] == 1)
    ck("every record is governed (serves_truth=false)", all(
        r.get("serves_truth") is False for r in recs3 if "serves_truth" in r))

    # round-trip through disk once (unique id, then clean up) to prove append/load
    append(session_record(sid, "claude_code"))
    append(event_record(sid, 0, "prompt", "x"))
    ck("append/load round-trips", len(load(sid)) == 2)
    _path(sid).unlink(missing_ok=True)

    if fails:
        print(f"\nFAIL - observer.session_store: {len(fails)} of {checks} failed")
        return 1
    print(f"PASS - observer.session_store: session/event/intervention schema + the accept/reject OUTCOME loop "
          f"(append-only, latest-wins, lossless) -> per-type tuning stats (the moat signal); {checks} assertions; "
          f"serves_truth=false, local-first port.")
    return 0


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except (ValueError, KeyError):
        return True
