#!/usr/bin/env python3
"""scripts._jsonl — the ONE lightweight JSONL reader. Two NAMED functions make the strict-vs-tolerant
choice explicit at every call site, because the split is MEANINGFUL:

  * read_jsonl_tolerant — SKIP malformed / non-object lines (a torn tail from a crash-mid-append, a
    concurrent writer, or disk-full must never break the whole read). Use for append-only runtime logs,
    search indexes, feeds, dedup scans.
  * read_jsonl_strict — RAISE ``ValueError("<path>:<lineno> …")`` on the first bad line. Use for
    truth-bearing rows (catalog, promotion) where a silent skip would HIDE corruption.

Lightweight and stdlib-only: no SQLite, no reconcile pass (that is scripts/_jsonl_store.AppendLog, the
durable WAL — far too heavy just to read a file). This module exists so the tolerant/strict pattern is
imported once, not re-implemented per call site (it had leaked into ~150 inline loops + 5 divergent
named helpers). Guard is byte-for-byte identical everywhere it is used.

    PYTHONPATH=. python3 scripts/_jsonl.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Iterator, Optional

#: called per bad line as ``on_error(lineno, line, exc)`` — for counting / repair tickets. Optional.
OnError = Optional[Callable[[int, str, Exception], None]]


def iter_jsonl_tolerant(path: str | Path, *, on_error: OnError = None) -> Iterator[dict]:
    """Yield each JSON OBJECT in ``path``, skipping blank / malformed / non-object lines. Never raises on
    a bad line (a torn append-only tail is expected); missing file yields nothing."""
    p = Path(path)
    if not p.exists():
        return
    for lineno, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError as exc:
            if on_error is not None:
                on_error(lineno, line, exc)
            continue
        if isinstance(obj, dict):
            yield obj
        elif on_error is not None:
            on_error(lineno, line, TypeError("JSONL line is not an object"))


def read_jsonl_tolerant(path: str | Path, *, on_error: OnError = None) -> list[dict]:
    """Tolerant read into a list (see iter_jsonl_tolerant)."""
    return list(iter_jsonl_tolerant(path, on_error=on_error))


def read_jsonl_strict(path: str | Path) -> list[dict]:
    """Read every non-blank line as a JSON object; RAISE ``ValueError("<path>:<lineno> …")`` on the first
    malformed or non-object line. Missing file returns []. For truth-bearing rows."""
    p = Path(path)
    if not p.exists():
        return []
    out: list[dict] = []
    for lineno, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError as exc:
            raise ValueError(f"{p}:{lineno} invalid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"{p}:{lineno} JSONL line is not an object")
        out.append(obj)
    return out


def _self_test() -> int:
    import tempfile
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        good = Path(td) / "good.jsonl"
        good.write_text('{"a": 1}\n\n{"b": 2}\n', encoding="utf-8")
        checks.append(("tolerant reads clean file", read_jsonl_tolerant(good) == [{"a": 1}, {"b": 2}]))
        checks.append(("strict reads clean file", read_jsonl_strict(good) == [{"a": 1}, {"b": 2}]))

        torn = Path(td) / "torn.jsonl"
        torn.write_text('{"ok": 1}\n{"torn": \n42\n{"after": 2}\n', encoding="utf-8")  # a torn/partial line + a bare scalar
        seen: list[int] = []
        rows = read_jsonl_tolerant(torn, on_error=lambda n, ln, e: seen.append(n))
        checks.append(("tolerant SKIPS the torn line, keeps valid rows", rows == [{"ok": 1}, {"after": 2}]))
        checks.append(("tolerant reports bad lines to on_error", len(seen) == 2))
        try:
            read_jsonl_strict(torn)
            checks.append(("strict RAISES on the torn line", False))
        except ValueError as exc:
            checks.append(("strict RAISES path:lineno on the torn line", str(torn) in str(exc) and ":2" in str(exc)))

        checks.append(("missing file -> [] (both)", read_jsonl_tolerant(Path(td) / "nope") == [] and read_jsonl_strict(Path(td) / "nope") == []))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - _jsonl:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - _jsonl: read_jsonl_tolerant skips torn/non-object lines (append-only safe) + reports them; "
          "read_jsonl_strict raises path:lineno on the first bad line (truth-bearing rows). One shared reader.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
