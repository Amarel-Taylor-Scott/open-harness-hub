#!/usr/bin/env python3
"""scripts._json — the ONE single-document JSON reader. Two NAMED functions make the tolerant-vs-strict
choice explicit at every call site, because the split is MEANINGFUL — the same reason scripts/_jsonl.py
exists, but for a single JSON object/array FILE, not a JSONL stream:

  * read_json_or(path, default) — return ``default`` on a MISSING file OR malformed JSON. For optional
    config / state where "absent" and "not written yet" are normal. Crucially it does NOT silently mask
    corruption: a malformed EXISTING file is reported to ``on_error(path, exc)`` FIRST (so a repair ticket
    can fire) before the default is returned.
  * read_json_strict(path) — RAISE ``ValueError("<path>: …")`` on a MISSING or malformed file. For
    truth-bearing inputs (a contract, a manifest, a schema) where a silent default would HIDE a real bug.

The bug this replaces: ~80 ad-hoc ``_read_json`` / ``_load_json`` copies with DIVERGENT contracts — some
returned ``{}`` on BOTH missing and corrupt, silently swallowing corruption (exactly the failure
scripts/_jsonl.py was built to stop, for the JSONL case). One reader, one contract, imported everywhere.

Lightweight, stdlib-only. serves_truth=false — this reads a pointer/config, never truth.

    PYTHONPATH=. python3 scripts/_json.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

#: called as ``on_error(path, exc)`` when an EXISTING file is unreadable/malformed — for counting / repair
#: tickets, so corruption is observable instead of vanishing into the default. Optional.
OnError = Optional[Callable[[Path, Exception], None]]


def read_json_or(path: str | Path, default: Any = None, *, on_error: OnError = None) -> Any:
    """Parse the JSON document at ``path``. Return ``default`` when the file is MISSING (normal for
    optional state) OR malformed. A malformed EXISTING file is reported to ``on_error(path, exc)`` before
    the default is returned — the difference from the copies that returned {} on both and hid corruption."""
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        if on_error is not None:
            on_error(p, exc)
        return default


def read_json_strict(path: str | Path) -> Any:
    """Parse the JSON document at ``path``; RAISE ``ValueError("<path>: …")`` on a MISSING or malformed
    file. For truth-bearing inputs where a silent default would hide a real problem."""
    p = Path(path)
    if not p.exists():
        raise ValueError(f"{p}: file not found")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError(f"{p}: invalid JSON: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"{p}: cannot read: {exc}") from exc


def _self_test() -> int:
    import tempfile

    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        good = Path(td) / "good.json"
        good.write_text('{"a": 1, "b": [2, 3]}', encoding="utf-8")
        checks.append(("read_json_or reads a good file", read_json_or(good) == {"a": 1, "b": [2, 3]}))
        checks.append(("read_json_strict reads a good file", read_json_strict(good) == {"a": 1, "b": [2, 3]}))

        missing = Path(td) / "nope.json"
        checks.append(("read_json_or returns default on MISSING", read_json_or(missing, {"d": True}) == {"d": True}))
        checks.append(("read_json_or default is None when unspecified", read_json_or(missing) is None))

        corrupt = Path(td) / "corrupt.json"
        corrupt.write_text('{"a": 1,,,', encoding="utf-8")
        seen: list[tuple[Path, Exception]] = []
        val = read_json_or(corrupt, {"fallback": 1}, on_error=lambda p, e: seen.append((p, e)))
        checks.append(("read_json_or returns default on CORRUPT", val == {"fallback": 1}))
        checks.append(("read_json_or REPORTS corruption to on_error (does not hide it)", len(seen) == 1 and seen[0][0] == corrupt))

        # strict: raises on both missing and corrupt, naming the path (never a silent default).
        try:
            read_json_strict(missing)
            checks.append(("read_json_strict RAISES on missing", False))
        except ValueError as exc:
            checks.append(("read_json_strict RAISES on missing (names path)", str(missing) in str(exc)))
        try:
            read_json_strict(corrupt)
            checks.append(("read_json_strict RAISES on corrupt", False))
        except ValueError as exc:
            checks.append(("read_json_strict RAISES on corrupt (names path)", str(corrupt) in str(exc)))

    failed = [n for n, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - _json: read_json_or returns a default on missing/corrupt but REPORTS corruption "
          "(never silently masks it as {}); read_json_strict raises path-named errors for truth-bearing inputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
