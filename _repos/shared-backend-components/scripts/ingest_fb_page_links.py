"""ingest_fb_page_links — governed harvest of GitHub repos linked from FB feed pages (theaiempire / DeepRepo).

The DURABLE value of those posts is the GitHub links, not the FB content. Direct FB scraping is ToS-restricted
(the social_scrape plane is access-RESTRICTED); the GOVERNED fetch paths are (a) owner-paste of the post text,
or (b) fb_page_scrape via a marketplace key (RAPIDAPI_KEY / APIFY_TOKEN — env-var NAMES only, never a pasted
value). Whatever the fetch, this module does the same thing: extract + CLEAN the GitHub repo links (strip
fbclid / tracking params), dedupe, and emit repo CANDIDATES that flow into the existing repo-intake pipeline.
discovery != trust: every repo is a candidate, license-checked before adoption. serves_truth=false. No PII.

  python3 _repos/shared-backend-components/scripts/ingest_fb_page_links.py --file post.txt        # extract repos from pasted post text
  echo "<post text>" | python3 _repos/shared-backend-components/scripts/ingest_fb_page_links.py --stdin
  python3 _repos/shared-backend-components/scripts/ingest_fb_page_links.py --self-test
"""
from __future__ import annotations

import argparse
import os
import re
import sys

# the two governed FB feed pages (source pointers, not scraped content)
FB_PAGES = {
    "theaiempire": "facebook.com/theaiempire",
    "deeprepo": "facebook.com/DeepRepo",
}
# github.com/<owner>/<repo> — the char class naturally stops at '?' so fbclid/query is dropped.
_GH_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
_NON_REPO_OWNERS = {"orgs", "sponsors", "features", "about", "topics", "search", "marketplace", "settings"}


def extract_repos(text: str) -> list[str]:
    """Return sorted unique 'owner/repo' slugs from any text (tracking params stripped)."""
    repos = set()
    for owner, repo in _GH_RE.findall(text or ""):
        repo = repo.removesuffix(".git").rstrip(".")
        if owner.lower() in _NON_REPO_OWNERS or not repo:
            continue
        repos.add(f"{owner}/{repo}")
    return sorted(repos)


def fetch_status() -> dict:
    """Honest reachability of the governed fb_page_scrape fetch (env-var NAMES only; values never read here)."""
    have_rapidapi = bool(os.environ.get("RAPIDAPI_KEY"))
    have_apify = bool(os.environ.get("APIFY_TOKEN"))
    if have_rapidapi or have_apify:
        return {"fetch": "available", "via": "fb_page_scrape (RAPIDAPI_KEY)" if have_rapidapi else "fb_page_scrape (APIFY_TOKEN)"}
    return {"fetch": "unavailable", "via": "owner-paste the post text, OR set RAPIDAPI_KEY / APIFY_TOKEN (governed social_scrape)"}


def ingest(text: str, source: str = "owner_paste") -> list[dict]:
    """Repo candidates from post text. Candidate-only (discovery != trust); feeds repo-intake."""
    return [{"repo": r, "url": f"https://github.com/{r}", "source": source, "candidate": True, "serves_truth": False}
            for r in extract_repos(text)]


_SAMPLE = ("Check this out! https://github.com/nexu-io/harness-engineering-guide?fbclid=IwY2xjawSnsCB_aem_hABAu "
           "and also github.com/openai/whisper great stuff")


def _self_test() -> int:
    repos = extract_repos(_SAMPLE)
    checks = [
        ("extracts nexu-io/harness-engineering-guide", "nexu-io/harness-engineering-guide" in repos),
        ("strips the fbclid (no '?' in slug)", all("?" not in r and "fbclid" not in r for r in repos)),
        ("extracts the second repo too", "openai/whisper" in repos),
        ("both FB pages registered", set(FB_PAGES) == {"theaiempire", "deeprepo"}),
        ("ingest marks candidates (discovery!=trust)", all(c["candidate"] and not c["serves_truth"] for c in ingest(_SAMPLE))),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'XX'}] {n}")
    if bad:
        print(f"FAIL - ingest_fb_page_links: {len(bad)} failed; repos={repos}")
        return 1
    print(f"PASS - ingest_fb_page_links: cleans + extracts GitHub repos from FB posts (fbclid stripped), "
          f"governed candidate feed; fetch={fetch_status()['fetch']}; {len(checks)} assertions; serves_truth=false.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", help="a file with pasted FB post text")
    ap.add_argument("--stdin", action="store_true", help="read post text from stdin")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()
    text = ""
    if args.file:
        text = open(args.file).read()
    elif args.stdin:
        text = sys.stdin.read()
    else:
        print("FB feed pages:", ", ".join(FB_PAGES.values()))
        print("fetch:", fetch_status()["via"])
        print("provide --file <post.txt> or --stdin with the post text to extract repos.")
        return 0
    import json
    cands = ingest(text)
    print(json.dumps({"candidates": cands, "count": len(cands)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
