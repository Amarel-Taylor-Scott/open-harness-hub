#!/usr/bin/env python3
"""Validate the stored dated live OFAC receipt without touching the network.

B1 in _repos/shared-backend-components/docs/goals/yc-readiness-loop.md requires one real ``--live`` OFAC run to be
captured and citable. The live fetch itself is not a CI dependency; this check only
proves that the committed receipt is a coherent lineage record for the existing
connector and that it records the would-be-violation hold-out without committing raw
SDN names. NOTE: content_hash is the receipt's own attestation of the raw SDN bytes at
fetch time — it is NOT recomputed in CI (the raw SDN names are deliberately not committed,
privacy_redaction.raw_sdn_names_committed=false). This gate proves the receipt is internally
consistent, source/parser-bound, served-AND-held-out, and agrees with the dated evidence file —
not that the bytes were re-fetched.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import re
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.ingest.sanctions_feed_live import (
    LIVE_SANCTIONS_SOURCES,
    PARSER_ID,
    POSITIONAL_CSV_SOURCE,
)

REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECEIPT_DIR = _resource("data") / "live-receipts"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HASH_RE = re.compile(r"^[a-f0-9]{64}$")


def _latest_receipt() -> Path | None:
    receipts = sorted(RECEIPT_DIR.glob("ofac-sdn-live-*-receipt.json"))
    return receipts[-1] if receipts else None


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    path = _latest_receipt()
    check("stored dated OFAC receipt exists", path is not None)
    receipt = json.loads(path.read_text(encoding="utf-8")) if path else {}
    source = receipt.get("source_run") or {}
    verify = receipt.get("verification_run") or {}

    expected_url = LIVE_SANCTIONS_SOURCES[POSITIONAL_CSV_SOURCE]["url"]
    check("receipt is the live OFAC SDN source", source.get("source_key") == POSITIONAL_CSV_SOURCE)
    check("source URL matches connector single source", source.get("source_url") == expected_url, str(source.get("source_url")))
    check("parser matches connector parser id", source.get("parser") == PARSER_ID, str(source.get("parser")))
    check("content hash is sha256-shaped", bool(HASH_RE.match(str(source.get("content_hash") or ""))))
    check("list date is dated", bool(DATE_RE.match(str(source.get("list_date") or ""))))
    check("version embeds date and hash prefix",
          str(source.get("list_version", "")).startswith(f"OFAC-SDN-LIVE-{source.get('list_date')}+")
          and str(source.get("content_hash", "")).startswith(str(source.get("list_version", "")).split("+")[-1]))
    check("rows parsed are non-empty and skip count is accounted",
          int(source.get("rows_parsed") or 0) > 0 and int(source.get("rows_skipped") or 0) >= 0)
    # the dated EVIDENCE file (which the deck cites) must agree with this receipt on the run's identity + parsed
    # count, so the two committed artifacts can never drift (the bug: evidence said 19,065 while the run parsed 5).
    ev_path = _resource("docs") / "strategy" / "evidence" / f"ofac-live-run-{source.get('list_date')}.json"
    ev = (json.loads(ev_path.read_text(encoding="utf-8")).get("lineage") or {}) if ev_path.exists() else {}
    check("dated evidence file exists for the receipt's run date", ev_path.exists(), str(ev_path))
    check("evidence file agrees with the receipt on content_hash + list_version + rows_parsed (no drift)",
          ev.get("content_hash") == source.get("content_hash")
          and ev.get("list_version") == source.get("list_version")
          and int(ev.get("rows_parsed") or -1) == int(source.get("rows_parsed") or 0),
          f"evidence rows_parsed={ev.get('rows_parsed')} vs receipt={source.get('rows_parsed')}")
    check("verified-context flow caught a would-be sanctions violation",
          int(verify.get("claims_held_out") or 0) >= 1 and len(verify.get("would_be_violations") or []) >= 1)
    viol = (verify.get("would_be_violations") or [{}])[0]
    check("would-be violation was held out, not served",
          viol.get("serving_decision") == "held_out" and "CLEAR" in str(viol.get("detail_redacted", "")))
    # SERVE side too (not just hold-out): the receipt must prove a clean claim was actually SERVED, so the gate
    # cannot pass on a degenerate run that served nothing — it tests serve-AND-hold-out, never hold-out alone.
    served = (verify.get("served_claims") or [{}])[0]
    check("a clean claim was actually SERVED (serve-and-hold-out, not just hold-out)",
          int(verify.get("claims_served") or 0) >= 1 and served.get("serving_decision") == "served")
    redaction = receipt.get("privacy_redaction") or {}
    text = json.dumps(receipt, sort_keys=True)
    check("receipt omits raw SDN names", redaction.get("raw_sdn_names_committed") is False
          and "AEROCARIBBEAN AIRLINES" not in text and "ANGLO-CARIBBEAN" not in text)
    check("receipt output is evidence, not served truth", receipt.get("serves_truth") is False)

    print("\n" + ("PASS - check_live_ofac_receipt: the dated live OFAC receipt is internally consistent and "
                  "source/parser-bound to the connector (live fetch attested at fetch time, not re-run in CI); "
                  "it SERVED a clean claim AND held out one real would-be violation; the dated evidence file "
                  "agrees on run identity + parsed count; raw SDN names are omitted."
                  if not failures else f"{len(failures)} FAILURES: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
