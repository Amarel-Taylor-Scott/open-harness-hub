#!/usr/bin/env python3
"""repo_intake_strategize — send over many GitHub repos → decompose + strategize integration (governed candidates).

The owner's ask: feed lots of github pages/repos; tools process, decompose, and strategize how these repos (or
variations, or our own code) could be improved + integrated. This CLI:
  1. NORMALIZES messy input (strips fbclid/tracking, splits concatenated URLs) → clean (owner, repo) list
  2. FETCHES public metadata + README via the GitHub API (the cheapest research component — no scraping)
  3. DECOMPOSES (what/lang/license/deps/readme) + STRATEGIZES (disposition + integration idea + descent axes)
  4. WRITES a governed candidate feed (data/capability-candidates/discovered-feed-repo-strategize.json)

Governance (scripts/ingest_github_signal_intake convention): discovery≠trust; every repo is a CANDIDATE, nothing
promoted; COPYLEFT/UNSTATED licenses are NEVER adoptable (technique-only). serves_truth=false. Logic lives in
src/teleon/repo_strategy (pure, offline-testable); this is the operator surface (live fetch + feed write).

  PYTHONPATH=. python3 scripts/repo_intake_strategize.py --run                 # the owner's default repos, live
  PYTHONPATH=. python3 scripts/repo_intake_strategize.py --run --urls "<url> <url>"
  PYTHONPATH=. python3 scripts/repo_intake_strategize.py --run --file repos.txt --offline
  PYTHONPATH=. python3 scripts/repo_intake_strategize.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
_FEED = REPO / "data" / "capability-candidates" / "discovered-feed-repo-strategize.json"

#: the owner's 2026-06-21 shared repos (clean; normalize() also accepts the raw fbclid/concatenated form).
DEFAULT_URLS = """
https://github.com/saurabhaloneai/History-of-Deep-Learning
https://github.com/awizemann/harness
https://github.com/BuildGreatProducts/plaid
https://github.com/inngest/agent-kit
https://github.com/DemchaAV/GraphCompose
https://github.com/Picrew/awesome-agent-harness
"""


def fetch_repo_meta(owner: str, repo: str, *, timeout: int = 12):
    """Fetch public metadata + README via the GitHub API (resilient: (None, err) on 404/rate-limit/no-network)."""
    import base64
    import urllib.request
    api = f"https://api.github.com/repos/{owner}/{repo}"
    hdr = {"User-Agent": "OpenHarnessHub-repo-intake/1.0", "Accept": "application/vnd.github+json"}
    try:
        with urllib.request.urlopen(urllib.request.Request(api, headers=hdr), timeout=timeout) as r:  # noqa: S310
            j = json.loads(r.read())
        meta = {"name": j.get("name"), "description": j.get("description"), "language": j.get("language"),
                "topics": j.get("topics") or [], "license": (j.get("license") or {}).get("spdx_id") or "",
                "stars": j.get("stargazers_count") or 0}
        readme = ""
        try:
            with urllib.request.urlopen(urllib.request.Request(api + "/readme", headers=hdr), timeout=timeout) as r:  # noqa: S310
                rj = json.loads(r.read())
                if rj.get("content"):
                    readme = base64.b64decode(rj["content"]).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001 — README optional
            pass
        return meta, readme
    except Exception as e:  # noqa: BLE001
        return None, str(e)[:120]


def process(urls_text: str, *, fetch=fetch_repo_meta, live: bool = True) -> list[dict]:
    from src.teleon.repo_strategy import normalize_repo_urls, build_record
    records = []
    for r in normalize_repo_urls(urls_text):
        if live:
            meta, readme_or_err = fetch(r["owner"], r["repo"])
            rec = build_record(r["owner"], r["repo"], r["url"], meta,
                               readme_or_err if meta is not None else "", fetched=meta is not None)
            if meta is None:
                rec["note"] = f"unreachable: {readme_or_err}"
        else:
            rec = build_record(r["owner"], r["repo"], r["url"], None, fetched=False)
        records.append(rec)
    return records


def write_feed(records: list[dict], path: Path = _FEED) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"generated_by": "scripts/repo_intake_strategize.py", "serves_truth": False,
               "governance": "discovery≠trust; candidates only; copyleft/unstated never adoptable",
               "count": len(records), "adoptable_count": sum(1 for r in records if r.get("adoptable")),
               "records": records}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _print_summary(records: list[dict]) -> None:
    for r in records:
        if not r.get("fetched"):
            print(f"  {r['owner']}/{r['repo']:<24} [not fetched] {r.get('note', '')}")
            continue
        s = r["strategy"]
        print(f"  {r['owner']}/{r['repo']:<24} {r['disposition']:<14} → {s['feeds_hub']:<18} "
              f"{r['decompose']['license_class']:<10} adoptable={r['adoptable']}")
        print(f"       idea: {s['integration_idea']}")


def _self_test() -> int:
    from src.teleon.repo_strategy import normalize_repo_urls
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # 1. normalize the owner's MESSY input (fbclid + a concatenated pair) -> 6 distinct repos
    messy = ("https://github.com/saurabhaloneai/History-of-Deep-Learning?fbclid=IwY2xjawSlYjNle"
             "https://github.com/awizemann/harness?fbclid=IwY2xjawSlYjhl, "
             "https://github.com/BuildGreatProducts/plaid?fbclid=x, https://github.com/inngest/agent-kit?fbclid=y, "
             "https://github.com/DemchaAV/GraphCompose?fbclid=z, https://github.com/Picrew/awesome-agent-harness?fbclid=q")
    repos = normalize_repo_urls(messy)
    names = {(r["owner"], r["repo"]) for r in repos}
    ck("normalize strips fbclid + SPLITS the concatenated pair → 6 clean repos", len(repos) == 6 and
       ("awizemann", "harness") in names and ("saurabhaloneai", "History-of-Deep-Learning") in names, str(sorted(names)))
    ck("a github /topics/ path is NOT mistaken for a repo", normalize_repo_urls("github.com/topics/llm") == [])

    # 2. decompose + strategize with an INJECTED fetcher (deterministic, offline) — license governance
    canned = {
        ("o", "permissive"): ({"name": "permissive", "description": "an agent harness", "language": "Python",
                               "topics": ["agent", "harness"], "license": "MIT", "stars": 10}, "pip install foo"),
        ("o", "copyleft"): ({"name": "copyleft", "description": "a rag graph tool", "language": "Py",
                             "topics": ["rag", "graph"], "license": "AGPL-3.0", "stars": 5}, ""),
        ("o", "unstated"): ({"name": "unstated", "description": "a tool", "language": "Go",
                             "topics": [], "license": "", "stars": 1}, ""),
    }
    fetch = lambda owner, repo: canned[(owner, repo)]  # noqa: E731
    recs = process("github.com/o/permissive github.com/o/copyleft github.com/o/unstated", fetch=fetch, live=True)
    by = {r["repo"]: r for r in recs}
    ck("permissive (MIT) → ADOPT-CANDIDATE + adoptable + maps to a hub",
       by["permissive"]["disposition"] == "ADOPT-CANDIDATE" and by["permissive"]["adoptable"] is True
       and by["permissive"]["strategy"]["feeds_hub"] in ("OpenHarnessHub", "OpenAgentHub"))
    ck("copyleft (AGPL) → CONSIDER (technique-only) + NOT adoptable",
       by["copyleft"]["disposition"] == "CONSIDER" and by["copyleft"]["adoptable"] is False)
    ck("unstated license → WATCH + NOT adoptable", by["unstated"]["disposition"] == "WATCH" and by["unstated"]["adoptable"] is False)
    ck("decompose captures a dependency signal from the README", "foo" in by["permissive"]["decompose"]["dependency_signals"])

    # 3. offline mode: records honestly marked not-fetched (no fabrication)
    off = process("github.com/o/x", live=False)
    ck("offline mode marks records not-fetched (honest, no fabrication)", off[0]["fetched"] is False and "decompose" not in off[0])

    # 4. feed shape (write to temp, read back)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = write_feed(recs, Path(d) / "feed.json")
        payload = json.loads(p.read_text())
        ck("feed writes serves_truth=false + counts (incl. adoptable_count)",
           payload["serves_truth"] is False and payload["count"] == 3 and payload["adoptable_count"] == 1)

    print("\n" + ("PASS - repo_intake_strategize: messy URLs → clean repos → decompose + strategize (disposition + "
                  "integration idea + axes) as GOVERNED candidates; copyleft/unstated never adoptable; offline is "
                  "honest; feed serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--run" in argv:
        def _val(flag, default=""):
            return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default
        if "--file" in argv:
            text = Path(_val("--file")).read_text(encoding="utf-8")
        else:
            text = _val("--urls") or DEFAULT_URLS
        live = "--offline" not in argv
        records = process(text, live=live)
        path = write_feed(records)
        print(f"processed {len(records)} repos (live={live}); feed → {path.relative_to(REPO)}\n")
        _print_summary(records)
        adoptable = [f"{r['owner']}/{r['repo']}" for r in records if r.get("adoptable")]
        print(f"\nADOPT-CANDIDATEs (permissive + on-thesis): {adoptable or 'none'} — serves_truth=false; nothing promoted.")
        return 0
    print("usage: repo_intake_strategize.py --run [--urls '<u> <u>' | --file F] [--offline] | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
