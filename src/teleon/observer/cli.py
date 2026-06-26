"""observer.cli — the CLI BRIDGE: discover Claude sessions, then review or live-route them, from a terminal.

This is the thin command surface over the existing engine — ``sessions`` (discovery) + ``capture``
(transcript -> events) + ``review``/``router`` (the governed findings). Three subcommands:

  list    discovered sessions for the project cwd (metadata only).
  review  post-session report  = review_session(from_transcript(path))   — the non-invasive adoption wedge.
  live    prospective findings = route_session(events, mode) for a LIVE mode (advisory|active|enforcing);
          prints {surfaced, summary} — what the Observer WOULD interrupt with right now.

Deterministic, read-only (never writes/republishes session content), serves_truth=false. Exits non-zero with
an honest message when no session is found. Same data the MCP server (scripts/aidevobserver_mcp_server.py)
exposes to an editor; this is the human/terminal path.

  python3 -m src.teleon.observer.cli list --json
  python3 -m src.teleon.observer.cli review --latest --json
  python3 -m src.teleon.observer.cli live --latest --mode advisory --json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from .capture import from_transcript
from .review import review_session
from .router import MODES, _MODE_CAP, route_session
from .sessions import discover_sessions, latest_session

# The LIVE modes = those whose budget can surface a non-silent action (single-sourced from the router lattice,
# never hand-listed — review_only/silent_record never interrupt). Default = the gentlest live mode.
LIVE_MODES = tuple(m for m in MODES if _MODE_CAP[m] != "silent")
DEFAULT_LIVE_MODE = LIVE_MODES[0]  # "advisory"

__all__ = ["review_path", "live_path", "build_parser", "main", "LIVE_MODES", "DEFAULT_LIVE_MODE"]


# --- reusable helpers (shared by the CLI commands and the MCP server) -------------------------------------------
def review_path(path: str) -> dict:
    """Governed post-session report for one transcript file: review_session(from_transcript(path))."""
    return review_session(from_transcript(path))


def live_path(path: str, mode: str = DEFAULT_LIVE_MODE) -> dict:
    """Prospective live findings for one transcript file in a LIVE mode -> {surfaced, summary, mode, serves_truth}."""
    if mode not in LIVE_MODES:
        raise ValueError(f"live mode must be one of {LIVE_MODES}; got {mode!r}")
    r = route_session(from_transcript(path), mode=mode)
    return {"surfaced": r["surfaced"], "summary": r["summary"], "mode": r["mode"], "serves_truth": False}


def _resolve_path(args: argparse.Namespace) -> str | None:
    """--path wins; otherwise (--latest or unspecified) -> the most recent discovered session."""
    if getattr(args, "path", None):
        return args.path
    return latest_session(getattr(args, "cwd", None))


# --- commands ---------------------------------------------------------------------------------------------------
def cmd_list(args: argparse.Namespace) -> int:
    sessions = discover_sessions(args.cwd)
    if args.json:
        print(json.dumps(sessions, indent=2))
        return 0
    if not sessions:
        print("no Claude Code sessions found for this project (looked under ~/.claude/projects/<encoded-cwd>)")
        return 0
    print(f"{len(sessions)} session(s) (newest first):")
    for s in sessions:
        when = datetime.fromtimestamp(s["mtime"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        print(f"  {s['session_id']}  {when}  {s['path']}")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    path = _resolve_path(args)
    if not path:
        print("no Claude Code session found (pass --path FILE, or run from the project's cwd)", file=sys.stderr)
        return 1
    report = review_path(path)
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    s = report["summary"]
    print(f"observer review v{report['version']}  ({path})")
    print(f"  {s['findings']} finding(s): {s['reinventions']} reinvention, {s['waste_signals']} waste — by_type {s['by_type']}")
    print(f"  serves_truth={report['serves_truth']} — governed candidates (a human triages)")
    for f in report["report"]:
        print(f"  [{f['confidence']:.2f}] {f['type']} @msg#{f['message_index']}: {f['message']}")
    return 0


def cmd_live(args: argparse.Namespace) -> int:
    path = _resolve_path(args)
    if not path:
        print("no Claude Code session found (pass --path FILE, or run from the project's cwd)", file=sys.stderr)
        return 1
    out = live_path(path, args.mode)
    if args.json:
        print(json.dumps(out, indent=2))
        return 0
    s = out["summary"]
    print(f"observer live  mode={out['mode']}  ({path})")
    print(f"  would interrupt: {s['would_interrupt']} of {s['findings']} finding(s) — by_type {s['by_type']}")
    for f in out["surfaced"]:
        print(f"  -> [{f['action']}] {f['type']} @msg#{f['message_index']}: {f['message']}")
    return 0


# --- argparse ---------------------------------------------------------------------------------------------------
def _add_target(p: argparse.ArgumentParser) -> None:
    g = p.add_mutually_exclusive_group()
    g.add_argument("--latest", action="store_true", help="use the most recent discovered session (default)")
    g.add_argument("--path", help="review/route this transcript file directly")
    p.add_argument("--cwd", help="project cwd to discover sessions for (default: current directory)")
    p.add_argument("--json", action="store_true", help="print the raw result dict as JSON")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python3 -m src.teleon.observer.cli", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="discover Claude Code sessions for the project cwd")
    p_list.add_argument("--cwd", help="project cwd (default: current directory)")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=cmd_list)

    p_review = sub.add_parser("review", help="governed post-session review of a transcript")
    _add_target(p_review)
    p_review.set_defaults(func=cmd_review)

    p_live = sub.add_parser("live", help="prospective findings the Observer would surface live")
    _add_target(p_live)
    p_live.add_argument("--mode", choices=LIVE_MODES, default=DEFAULT_LIVE_MODE,
                        help=f"live restraint mode (default: {DEFAULT_LIVE_MODE})")
    p_live.set_defaults(func=cmd_live)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
