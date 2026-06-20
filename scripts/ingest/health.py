#!/usr/bin/env python3
"""scripts.ingest.health — Source health check for the Open Harness Hub corpus.

Answers the operational question: are our official/government source URLs reachable
and still producing parseable facts?  This is a lightweight pre-flight and monitoring
tool — it does NOT write corpus rows.  The pipeline is:

    registry entry → fetch URL → parse_facts → health result dict

Three surfaces:
  - check_health(entry, *, fetcher=None) -> dict
      Fetch a single registry entry.  Never raises — all errors captured.
  - check_all(registry=None, *, fetcher=None) -> dict
      Runs check_health over every entry; returns aggregate counts.
  - CLI (_main): --self-test (offline) | --check (live) | --json

Run offline:   python3 -m scripts.ingest.health --self-test
Run live:      python3 -m scripts.ingest.health --check
Live + JSON:   python3 -m scripts.ingest.health --check --json
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from scripts.foundry.scrapers import (
    CannedFetcher,
    Fetcher,
    HttpFetcher,
    content_hash,
    parse_facts,
)
from scripts.ingest import load_registry

# ── public API ────────────────────────────────────────────────────────────────


def check_health(entry: dict, *, fetcher: Fetcher | None = None) -> dict:
    """Fetch *entry['url']* and report reachability + parseability.

    Returns::

        {
          url:          str,
          name:         str,
          ok:           bool,          # True iff status==200 AND ≥1 fact parsed
          status:       int | None,    # HTTP status; None on network/key error
          facts:        int,           # number of facts parse_facts() returned
          content_hash: str,           # sha256 of the raw content (empty string → hash of "")
          error:        str,           # only present when ok is False
        }

    Never raises — every exception is captured into *error*.
    """
    f = fetcher or HttpFetcher()
    url: str = entry.get("url", "")
    name: str = entry.get("name", url)
    max_facts: int = entry.get("max_facts", 200)

    status: int | None = None
    facts_count: int = 0
    chash: str = content_hash("")
    error: str | None = None

    try:
        result = f.fetch(url)
        status = result.get("status")
        content: str = result.get("content", "")
        chash = content_hash(content)
        if status == 200:
            facts_count = len(parse_facts(content, max_facts=max_facts))
    except KeyError as exc:
        # CannedFetcher raises KeyError for unknown URLs — treat as unreachable
        error = f"url not in canned pages: {exc}"
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"

    ok = (status == 200) and (facts_count >= 1) and (error is None)

    rec: dict[str, Any] = {
        "url": url,
        "name": name,
        "ok": ok,
        "status": status,
        "facts": facts_count,
        "content_hash": chash,
    }
    if not ok:
        # always include an error field when not healthy so callers can branch on it
        rec["error"] = error or (
            f"status {status}" if status != 200
            else "no facts parsed"
        )
    return rec


def check_all(
    registry: list[dict] | None = None,
    *,
    fetcher: Fetcher | None = None,
) -> dict:
    """Run check_health over every entry in *registry* (default: load from the repo path).

    Returns::

        {
          total:    int,
          healthy:  int,
          results:  list[dict],   # one per entry, same shape as check_health()
        }
    """
    entries = registry if registry is not None else load_registry()
    results = [check_health(e, fetcher=fetcher) for e in entries]
    healthy = sum(1 for r in results if r["ok"])
    return {"total": len(results), "healthy": healthy, "results": results}


# ── CLI ───────────────────────────────────────────────────────────────────────

_COL_W = 55  # truncation width for the name column in the table view


def _print_table(summary: dict) -> None:
    total = summary["total"]
    healthy = summary["healthy"]
    results = summary["results"]
    header = f"{'NAME':<{_COL_W}}  {'STATUS':>6}  {'FACTS':>5}  OK"
    print(header)
    print("-" * len(header))
    for r in results:
        name_col = r["name"][:_COL_W].ljust(_COL_W)
        status_col = str(r["status"]) if r["status"] is not None else "ERR"
        facts_col = str(r["facts"])
        ok_col = "yes" if r["ok"] else "no "
        line = f"{name_col}  {status_col:>6}  {facts_col:>5}  {ok_col}"
        if not r["ok"]:
            err = r.get("error", "")
            line += f"  ({err})"
        print(line)
    print()
    print(f"healthy: {healthy}/{total}")


# ── self-test ─────────────────────────────────────────────────────────────────

def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # ── fixture: one good page, one URL absent from the canned map ────────────
    GOOD_URL = "https://test.gov/docs/regulations"
    MISSING_URL = "https://test.gov/missing-page"

    good_content = (
        "Section 1: Covered persons must file currency transaction reports.\n\n"
        "Section 2: The threshold for reporting is PHP 500,000 per transaction.\n\n"
        "Section 3: Suspicious transaction reports must be filed within five days."
    )
    canned = CannedFetcher({GOOD_URL: good_content})

    good_entry = {
        "url": GOOD_URL,
        "name": "Test Gov Regulations",
        "gov": True,
        "license": "Public Domain",
        "source_kind": "regulation",
        "keywords": ["test", "regulation"],
    }
    missing_entry = {
        "url": MISSING_URL,
        "name": "Missing Page",
        "gov": True,
        "license": "Public Domain",
        "source_kind": "regulation",
        "keywords": ["missing"],
    }

    # ── check_health: good page ───────────────────────────────────────────────
    good_result = check_health(good_entry, fetcher=canned)
    check("good page → ok=True", good_result["ok"] is True, str(good_result))
    check("good page → status=200", good_result["status"] == 200, str(good_result))
    check("good page → facts >= 1", good_result["facts"] >= 1, str(good_result))
    check("good page → content_hash non-empty", bool(good_result["content_hash"]), str(good_result))
    check("good page → no error key", "error" not in good_result, str(good_result))

    # ── check_health: missing URL (KeyError from CannedFetcher) ──────────────
    missing_result = check_health(missing_entry, fetcher=canned)
    check("missing url → ok=False (no exception escapes)", missing_result["ok"] is False, str(missing_result))
    check("missing url → status=None", missing_result["status"] is None, str(missing_result))
    check("missing url → error captured", bool(missing_result.get("error")), str(missing_result))
    check("missing url → facts=0", missing_result["facts"] == 0, str(missing_result))

    # ── check_all: aggregate ──────────────────────────────────────────────────
    registry = [good_entry, missing_entry]
    summary = check_all(registry, fetcher=canned)
    check("check_all → total=2", summary["total"] == 2, str(summary))
    check("check_all → healthy=1 (only the good page)", summary["healthy"] == 1, str(summary))
    check("check_all → results list length=2", len(summary["results"]) == 2, str(summary))

    # ── error isolation: a second bad entry doesn't break the good one ────────
    bad_entry = {"url": "https://also-missing.gov/", "name": "Also Missing"}
    triple_summary = check_all([good_entry, missing_entry, bad_entry], fetcher=canned)
    check("three entries: healthy still=1", triple_summary["healthy"] == 1, str(triple_summary))
    check("three entries: total=3", triple_summary["total"] == 3, str(triple_summary))

    # ── content_hash is stable (same content → same hash) ────────────────────
    r2 = check_health(good_entry, fetcher=canned)
    check("content_hash stable across two calls", r2["content_hash"] == good_result["content_hash"])

    # ── empty registry ────────────────────────────────────────────────────────
    empty = check_all([], fetcher=canned)
    check("empty registry → total=0, healthy=0", empty["total"] == 0 and empty["healthy"] == 0)

    n = len(failures)
    noun = "health"
    print(f"\n{'all ' + str(9) + ' ' + noun + ' self-tests passed.' if not failures else f'{n} FAILURES: {failures}'}")
    return 0 if not failures else 1


# ── _main ─────────────────────────────────────────────────────────────────────

def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Check reachability + parseability of corpus source URLs."
    )
    p.add_argument("--self-test", action="store_true", help="run offline self-tests and exit")
    p.add_argument("--check", action="store_true", help="live health check of all registry sources (needs network)")
    p.add_argument("--json", action="store_true", dest="as_json", help="print results as JSON (with --check)")
    p.add_argument("--registry", default=None, help="path to source-registry.jsonl (default: repo default)")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.check:
        registry = load_registry(args.registry) if args.registry else load_registry()
        fetcher = HttpFetcher()
        summary = check_all(registry, fetcher=fetcher)
        if args.as_json:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            _print_table(summary)
        # exit 1 if any source is unhealthy (useful for CI health gates)
        return 0 if summary["healthy"] == summary["total"] else 1

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
