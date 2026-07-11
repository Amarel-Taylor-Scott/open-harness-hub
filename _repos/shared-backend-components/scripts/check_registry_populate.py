"""check_registry_populate — proof for the dogfood population pipeline (_repos/teleon/backend/src/teleon/registry/populate.py + tools/web_fetch.py).

Verifies the loop that GROWS registry records: repo slugs -> candidate records -> ENRICHED -> governed
(candidate-only, serves_truth=false). Offline-deterministic (no network); also checks web_fetch's honest-fail
path. This is how 'scrape interesting repos' becomes 'records in a registry'. Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry.populate import py_function_src_teleon_registry_populate__populate, py_function_src_teleon_registry_populate__repo_to_record  # noqa: E402
from src.teleon.tools.web_fetch import fetch  # noqa: E402

_SLUGS = ["nexu-io/harness-engineering-guide", "openai/whisper"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [{'ok' if ok else 'XX'}] {name}{(' — ' + detail) if detail else ''}")

    recs = py_function_src_teleon_registry_populate__populate(_SLUGS)  # offline
    ck("populate returns a record per slug", len(recs) == len(_SLUGS), str(len(recs)))
    r0 = recs[0]
    ck("record has the right id", r0["id"] == "nexu-io__harness-engineering-guide", r0["id"])
    ck("record has the github url", r0["url"] == "https://github.com/nexu-io/harness-engineering-guide")
    ck("record is candidate-only (discovery!=trust)", r0["candidate"] is True and r0["serves_truth"] is False)
    ck("record is ENRICHED", "_enrichment" in r0)
    e = r0.get("_enrichment", {})
    ck("enrichment has embedding + keywords + labels", {"embedding", "keywords", "labels", "use_cases"} <= set(e))
    ck("keywords mention the repo", any("harness" in k or "engineering" in k for k in e.get("keywords", [])),
       str(e.get("keywords")))

    # web_fetch honest-fail path (no network needed): non-http scheme -> error dict, never raises
    bad = fetch("not-a-real-url")
    ck("web_fetch rejects non-http honestly (no raise)", bad["error"] is not None and bad["text"] == "", str(bad.get("error")))
    ftp = fetch("ftp://example.com/x")
    ck("web_fetch guards scheme", ftp["error"] is not None)

    # repo_to_record is pure/deterministic
    ck("repo_to_record deterministic", py_function_src_teleon_registry_populate__repo_to_record("a/b") == py_function_src_teleon_registry_populate__repo_to_record("a/b"))

    if fails:
        print(f"\nFAIL - check_registry_populate: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_registry_populate: dogfood pipeline turns repo slugs into ENRICHED, governed "
          f"candidate records (offline-deterministic); web_fetch fails honestly; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
