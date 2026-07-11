#!/usr/bin/env python3
"""scripts.session_redundancy — an AIDevObserver DEMO: process a GROUP of Claude Code (or other) coding-session
transcripts and find REDUNDANT behavior + activity DETERMINISTICALLY (0 tokens). Sessions are stored as JSONL;
we extract the tool activity (bash commands, file reads/edits, searches) and surface what was repeated — within
a session and ACROSS sessions — so an agent (or a human) can see where effort was wasted re-doing the same thing.

This is exactly AIDevObserver's remit — review AI USAGE, not code — and the reuse thesis: don't re-run the same
command, re-read the same file, or re-implement the same thing the session already did. Findings are candidate
advice (serves_truth=false), never truth.

Detects:
  * duplicate_commands   — the same bash command run many times.
  * repeated_reads       — the same file read many times.
  * repeated_edits       — the same file edited/written many times.
  * redundant_searches   — the same grep/glob pattern searched many times.
  * cross_session_activities — an activity that recurs in MULTIPLE sessions (re-doing work across sessions).
  * redundancy_rate      — fraction of tool calls that were repeats of an earlier identical activity.

    PYTHONPATH=. python3 scripts/session_redundancy.py --self-test
    PYTHONPATH=. python3 scripts/session_redundancy.py --demo               # report over THIS project's sessions
    PYTHONPATH=. python3 scripts/session_redundancy.py --paths a.jsonl b.jsonl
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from collections import Counter, defaultdict  # noqa: E402
from typing import Any, Iterator, Optional  # noqa: E402

from scripts import session_context as _sc  # noqa: E402  REUSE: transcript discovery + byte-bounded tail

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_MIN_REPEATS = 3        # an activity is "redundant" once it occurs at least this many times
_MAX_BYTES = 800_000    # per-file byte tail (recent activity), bounds cost on huge transcripts
_MAX_LINES = 4_000      # per-file record cap
_KEY_CHARS = 200        # activity-key length cap (bash commands can be long)
#: which tool goes in which redundancy bucket — single source, extensible.
_READ_TOOLS = ("Read",)
_EDIT_TOOLS = ("Edit", "Write", "NotebookEdit", "MultiEdit")
_SEARCH_TOOLS = ("Grep", "Glob")
_CMD_TOOLS = ("Bash",)


def _activity_key(name: str, inp: dict[str, Any]) -> str:
    """The salient, normalized signature of a tool call — what makes two calls 'the same activity'."""
    if name in _CMD_TOOLS:
        return "bash: " + " ".join(str(inp.get("command", "")).split())[:_KEY_CHARS]
    if name in _READ_TOOLS + _EDIT_TOOLS:
        return f"{name.lower()}: {inp.get('file_path') or inp.get('notebook_path') or ''}"
    if name in _SEARCH_TOOLS:
        return f"{name.lower()}: {inp.get('pattern') or inp.get('query') or ''}"
    return f"{name.lower()}: " + json.dumps(inp, sort_keys=True, default=str)[:120]


def _tool_calls(record: Any) -> Iterator[tuple[str, str]]:
    """Every (tool_name, activity_key) in a transcript record — found by walking the JSON for tool_use blocks,
    so it is robust to the exact nesting of the transcript schema."""
    if isinstance(record, dict):
        if record.get("type") == "tool_use" and record.get("name"):
            yield (str(record["name"]), _activity_key(str(record["name"]),
                                                       record.get("input") if isinstance(record.get("input"), dict)
                                                       else {}))
        for value in record.values():
            yield from _tool_calls(value)
    elif isinstance(record, list):
        for item in record:
            yield from _tool_calls(item)


def _recent_records(path: Path, *, max_bytes: int = _MAX_BYTES, max_lines: int = _MAX_LINES) -> list[Any]:
    """Parse up to ``max_lines`` recent JSONL records from a byte-bounded tail (drops the first partial line)."""
    text = _sc._tail_text(path, max_bytes)
    lines = text.split("\n")
    try:
        truncated = path.stat().st_size > max_bytes
    except Exception:  # noqa: BLE001
        truncated = False
    if truncated and len(lines) > 1:
        lines = lines[1:]  # drop the partial first line ONLY when we actually cut mid-file (else it's complete)
    out: list[Any] = []
    for line in lines[-max_lines:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:  # noqa: BLE001 — a non-JSON line is skipped
            continue
    return out


def analyze_sessions(paths: list[Path], *, min_repeats: int = _MIN_REPEATS) -> dict[str, Any]:
    """The redundancy report over a GROUP of session transcripts (deterministic, 0-token)."""
    by_tool: dict[str, Counter] = defaultdict(Counter)     # tool -> Counter(activity_key -> count)
    sessions_of: dict[tuple[str, str], set] = defaultdict(set)  # (tool,key) -> {session stems}
    total_calls = 0
    for path in paths:
        stem = path.stem[:16]
        for record in _recent_records(path):
            for tool, key in _tool_calls(record):
                by_tool[tool][key] += 1
                sessions_of[(tool, key)].add(stem)
                total_calls += 1

    def _bucket(tools: tuple[str, ...]) -> list[dict[str, Any]]:
        merged: Counter = Counter()
        for tool in tools:
            merged.update(by_tool.get(tool, {}))
        return [{"activity": k, "count": c} for k, c in merged.most_common() if c >= min_repeats][:15]

    cross = [{"activity": f"{t} | {k}", "sessions": len(sess), "count": by_tool[t][k]}
             for (t, k), sess in sessions_of.items() if len(sess) >= 2]
    cross.sort(key=lambda r: (-r["sessions"], -r["count"]))
    # repeats = every occurrence beyond the first identical one (the wasted re-work)
    repeats = sum(c - 1 for tool in by_tool for c in by_tool[tool].values() if c > 1)
    return {"record_type": "session_redundancy_report", "sessions": len(paths),
            "total_tool_calls": total_calls, "distinct_activities": len(sessions_of),
            "redundancy_rate": round(repeats / total_calls, 4) if total_calls else 0.0,
            "duplicate_commands": _bucket(_CMD_TOOLS), "repeated_reads": _bucket(_READ_TOOLS),
            "repeated_edits": _bucket(_EDIT_TOOLS), "redundant_searches": _bucket(_SEARCH_TOOLS),
            "cross_session_activities": cross[:15], "min_repeats": min_repeats,
            "note": "candidate advice (serves_truth=false): activities repeated >= min_repeats within/across "
                    "sessions are where work was re-done — reuse instead of re-running/re-reading/re-implementing.",
            **BOUNDARY}


def redundancy_report(*, project_root: Optional[Path] = None, logs_dir: Optional[Path] = None,
                      max_files: int = 5, min_repeats: int = _MIN_REPEATS) -> dict[str, Any]:
    """Discover THIS project's recent session transcripts and report their redundancy."""
    paths = _sc.discover_logs(logs_dir, project_root=project_root, max_files=max_files)
    return analyze_sessions(paths, min_repeats=min_repeats)


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []

    def _tu(name: str, inp: dict) -> str:
        return json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name,
                                                                         "input": inp}]}})
    with tempfile.TemporaryDirectory() as d:
        s1 = Path(d) / "sess1.jsonl"
        s2 = Path(d) / "sess2.jsonl"
        # session 1: runs the SAME build command 4x, reads the same file 3x, greps the same pattern 3x
        s1.write_text("\n".join(
            [_tu("Bash", {"command": "python3 scripts/build.py"}) for _ in range(4)]
            + [_tu("Read", {"file_path": "/repo/config.py"}) for _ in range(3)]
            + [_tu("Grep", {"pattern": "def main"}) for _ in range(3)]
            + [_tu("Edit", {"file_path": "/repo/once.py"})]) + "\n")
        # session 2: repeats the SAME build command (cross-session redundancy) + a unique action
        s2.write_text("\n".join(
            [_tu("Bash", {"command": "python3 scripts/build.py"}) for _ in range(2)]
            + [_tu("Read", {"file_path": "/repo/other.py"})]) + "\n")

        rep = analyze_sessions([s1, s2])
        checks.append(("both sessions are processed", rep["sessions"] == 2 and rep["total_tool_calls"] >= 13))
        checks.append(("a duplicate command is detected with its count",
                       any("build.py" in x["activity"] and x["count"] >= 6 for x in rep["duplicate_commands"])))
        checks.append(("a repeated file read is detected",
                       any("config.py" in x["activity"] and x["count"] == 3 for x in rep["repeated_reads"])))
        checks.append(("a redundant search is detected",
                       any("def main" in x["activity"] and x["count"] == 3 for x in rep["redundant_searches"])))
        checks.append(("a CROSS-SESSION repeat is flagged (same build cmd in both sessions)",
                       any("build.py" in x["activity"] and x["sessions"] == 2
                           for x in rep["cross_session_activities"])))
        checks.append(("a one-off action is NOT flagged as redundant",
                       not any("once.py" in x["activity"] for x in rep["repeated_edits"])))
        checks.append(("the redundancy rate is a real fraction in [0,1]", 0.0 < rep["redundancy_rate"] <= 1.0))

        # byte-bounded parse: a huge transcript is tail-read and the recent activity still counts
        big = Path(d) / "big.jsonl"
        big.write_text("x" * 1_500_000 + "\n" + "\n".join([_tu("Bash", {"command": "echo hi"}) for _ in range(3)]))
        rep2 = analyze_sessions([big])
        checks.append(("a 1.5MB transcript is tail-parsed and its recent repeats are caught",
                       any("echo hi" in x["activity"] for x in rep2["duplicate_commands"])))

        checks.append(("determinism (byte-identical twice)",
                       json.dumps(analyze_sessions([s1, s2]), sort_keys=True)
                       == json.dumps(analyze_sessions([s1, s2]), sort_keys=True)))
        checks.append(("report is candidate/serves_truth=false", rep["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - session_redundancy: an AIDevObserver demo that processes a GROUP of coding-session "
          "transcripts and finds redundant behavior DETERMINISTICALLY (0-token) — duplicate commands, repeated "
          "reads/edits, redundant searches, and cross-session repeats, with a redundancy rate — from a "
          "byte-bounded tail so huge logs are cheap. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--demo", action="store_true", help="redundancy report over THIS project's recent sessions")
    ap.add_argument("--paths", nargs="+", metavar="JSONL", help="analyze a specific group of session files")
    ap.add_argument("--min-repeats", type=int, default=_MIN_REPEATS)
    ap.add_argument("--max-files", type=int, default=5)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.paths:
        print(json.dumps(analyze_sessions([Path(p) for p in args.paths], min_repeats=args.min_repeats),
                         indent=2, sort_keys=True))
        return 0
    if args.demo:
        print(json.dumps(redundancy_report(max_files=args.max_files, min_repeats=args.min_repeats),
                         indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
