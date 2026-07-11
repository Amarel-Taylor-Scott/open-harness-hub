"""observer.sessions — Claude Code session DISCOVERY (the on-disk capture seam, zero live install).

Claude Code persists every session as a JSONL transcript at
``~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`` where ``<encoded-cwd>`` is the absolute working
directory with every NON-alphanumeric character (``/``, ``.``, ``_``, ``-`` …) rewritten to ``-`` — e.g.
``/home/u/my.proj`` -> ``-home-u-my-proj`` and ``/home/u/a_b`` -> ``-home-u-a-b`` (verified against the real
projects dir; the "/ and . only" shorthand is a subset). This module turns that convention into discovery:
which sessions belong to a project cwd, and which is the latest — so ``review``/``live`` can run with no setup.

It is the front of the same pipeline as ``capture`` (which reads a transcript into events): discover -> capture
-> route/review. Read-only and metadata-only: discovery ``stat``s files (session_id/path/mtime/project), it
never reads or republishes session CONTENT. The projects root is overridable via ``OBSERVER_PROJECTS_DIR``
(for isolated tests) but defaults to ``~/.claude/projects``. serves_truth=false.

  python3 -m src.teleon.observer.sessions --self-test
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import capture  # downstream use: from_transcript(path) reads a discovered session into events
from .capture import from_transcript  # re-exported for convenience (discover -> from_transcript -> review)

__all__ = ["encode_cwd", "discover_sessions", "latest_session", "from_transcript", "capture"]

# Claude Code's cwd->dirname encoding: collapse every non-alphanumeric char to '-' (1:1, no run-collapsing).
_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]")
_PROJECTS_ENV = "OBSERVER_PROJECTS_DIR"  # test/override hook; unset -> the real Claude Code projects root
_DEFAULT_PROJECTS = Path.home() / ".claude" / "projects"


def _projects_dir() -> Path:
    """The Claude Code projects root (``~/.claude/projects``), overridable via OBSERVER_PROJECTS_DIR for tests."""
    override = os.environ.get(_PROJECTS_ENV)
    return Path(override) if override else _DEFAULT_PROJECTS


def encode_cwd(path: str | Path) -> str:
    """Encode an absolute cwd the way Claude Code names its per-project transcript directory.

    Every non-alphanumeric character becomes '-' (so '/', '.', '_' and '-' all map to '-'). A relative path is
    resolved to absolute first (mirrors Claude Code launching from an absolute cwd)."""
    return _NON_ALNUM.sub("-", os.path.abspath(str(path)))


def discover_sessions(cwd: str | Path | None = None) -> list[dict]:
    """Discover this project's Claude Code sessions, newest first.

    Returns ``[{session_id, path, mtime, project}]`` sorted by mtime descending. ``cwd`` defaults to
    ``os.getcwd()``. Returns ``[]`` gracefully when the project has no transcript directory yet (read-only;
    metadata only — never reads session content)."""
    base = _projects_dir() / encode_cwd(cwd if cwd is not None else os.getcwd())
    if not base.is_dir():
        return []
    out: list[dict] = []
    for p in sorted(base.glob("*.jsonl")):
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue  # a vanishing/locked file must not crash discovery
        out.append({"session_id": p.stem, "path": str(p), "mtime": mtime, "project": base.name})
    out.sort(key=lambda s: s["mtime"], reverse=True)
    return out


def latest_session(cwd: str | Path | None = None) -> str | None:
    """Path of the most recently modified session for ``cwd`` (defaults to ``os.getcwd()``), or None if none."""
    sessions = discover_sessions(cwd)
    return sessions[0]["path"] if sessions else None


# --- proof ------------------------------------------------------------------------------------------------------
def _self_test() -> int:
    import json
    import tempfile

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck("encodes the documented example (/ and . -> -)", encode_cwd("/home/u/my.proj") == "-home-u-my-proj",
       encode_cwd("/home/u/my.proj"))
    ck("collapses underscores too (matches real Claude dirs)", encode_cwd("/home/u/a_b") == "-home-u-a-b")
    ck("encoding is deterministic", encode_cwd("/x/y.z") == encode_cwd("/x/y.z"))

    # isolated synthetic projects tree (unique tmp dir; never touches the real ~/.claude) -------------------------
    tmp = Path(tempfile.mkdtemp(prefix="observer_sessions_selftest_"))
    fake_cwd = "/home/tester/demo.proj"
    proj = tmp / encode_cwd(fake_cwd)
    proj.mkdir(parents=True)
    (proj / "sess-a.jsonl").write_text(json.dumps(
        {"type": "user", "message": {"role": "user", "content": "hi"}}) + "\n")
    older = proj / "sess-b.jsonl"
    older.write_text("{}\n")
    os.utime(older, (1.0, 1.0))  # force sess-b older -> sess-a must sort first

    prev = os.environ.get(_PROJECTS_ENV)
    os.environ[_PROJECTS_ENV] = str(tmp)
    try:
        found = discover_sessions(fake_cwd)
        ck("discovers both synthetic sessions", len(found) == 2, str(len(found)))
        ck("each row has the documented shape", all(
            set(s) == {"session_id", "path", "mtime", "project"} for s in found))
        ck("sorted newest-first (mtime desc)", found[0]["session_id"] == "sess-a")
        ck("latest_session returns the newest path", latest_session(fake_cwd) == str(proj / "sess-a.jsonl"))
        ck("absent project dir -> [] gracefully", discover_sessions("/no/such/project/here") == [])
        ck("absent project -> latest_session None", latest_session("/no/such/project/here") is None)
    finally:
        if prev is None:
            os.environ.pop(_PROJECTS_ENV, None)
        else:
            os.environ[_PROJECTS_ENV] = prev
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print(f"\nFAIL - observer.sessions: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - observer.sessions: Claude Code transcript discovery (encode_cwd / discover_sessions / "
          f"latest_session), newest-first, graceful-absent; {checks} assertions; serves_truth=false, read-only.")
    return 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()
    for s in discover_sessions():
        print(f"{s['session_id']}  {s['path']}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
