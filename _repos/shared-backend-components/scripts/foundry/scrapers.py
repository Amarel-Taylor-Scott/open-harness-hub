#!/usr/bin/env python3
"""Foundry scrapers — the freshness source surface (Stage 1, live).

The live counterpart to `seeds.LocalSourceScout`: given a confirmed gap, fetch the
authoritative source (a government / standards-body page), capture **full date +
provenance + content hash**, and emit a **dynamic** Knowledge Corpus source. This is
the engine behind the recurring-revenue layer — a scraped gov corpus is **open** content
(gov-published) but **live_subscription** delivery (the maintained, CDC-tracked feed is
the subscription; `openness.py` + `access.py` classify it exactly so).

CDC: the content hash detects when a source changes between scrapes → a change event →
revocation/refresh propagates to subscribers (the freshness alerts). The `Fetcher` is a
protocol so the network is swappable (live `HttpFetcher`; `CannedFetcher` for tests).

`WebSourceScout` is a drop-in `sources.SourceScout`, so a foundry configured with it
scrapes real sources for gaps. stdlib-only. Run `python -m scripts.foundry.scrapers
--self-test` (offline) or `--refresh` (live, needs a registry + network).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from scripts.foundry.sources import normalize_source_kind

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
DEFAULT_REGISTRY = _resource("data") / "source-registry.jsonl"   # gap-keywords → authoritative source
_MAX_FACTS = 200
_USER_AGENT = "OpenHubForAI-foundry-scraper/1.0 (+https://openhubforai.com)"


@runtime_checkable
class Fetcher(Protocol):
    def fetch(self, url: str) -> dict:
        """Return {url, status, content, fetched_at}."""
        ...


class HttpFetcher:
    """Live fetch over HTTPS (polite UA + timeout). Runs in the worker/cron with network."""

    def __init__(self, *, timeout: int = 30, now_s: float | None = None) -> None:
        self.timeout = timeout
        self._now_s = now_s

    def fetch(self, url: str) -> dict:  # pragma: no cover - network
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            raw = r.read()
            status = r.status
        text = raw.decode("utf-8", errors="replace")
        return {"url": url, "status": status, "content": text,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._now_s))}


class CannedFetcher:
    """Offline fetcher for tests/replay: a {url: content} map."""

    def __init__(self, pages: dict[str, str], *, now_s: float = 0.0) -> None:
        self.pages = pages
        self._now_s = now_s

    def fetch(self, url: str) -> dict:
        if url not in self.pages:
            raise KeyError(f"no canned page for {url}")
        return {"url": url, "status": 200, "content": self.pages[url],
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._now_s))}


def content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t]+")


def parse_facts(content: str, *, max_facts: int = _MAX_FACTS) -> list[dict]:
    """Default parser: strip tags, split into non-trivial blocks → entries. Swap per source."""
    text = _TAG.sub(" ", content or "")
    blocks = [_WS.sub(" ", b).strip() for b in re.split(r"\n\s*\n|\r\n\r\n", text)]
    return [{"text": b} for b in blocks if len(b) >= 24][:max_facts]


def detect_change(prev_hash: str | None, content: str) -> dict:
    """CDC: did the source change since last scrape? Drives refresh + revocation alerts."""
    h = content_hash(content)
    if prev_hash is None:
        return {"changed": True, "content_hash": h, "event": "new"}
    return {"changed": h != prev_hash, "content_hash": h, "event": "changed" if h != prev_hash else "unchanged"}


class WebSourceScout:
    """A live `sources.SourceScout`: match a gap to a registered authoritative URL,
    fetch it, and emit a dynamic Knowledge Corpus source with provenance + CDC."""

    def __init__(self, registry: list[dict] | None = None, *, fetcher: Fetcher | None = None) -> None:
        self.registry = registry or []
        self.fetcher = fetcher or HttpFetcher()

    def find(self, gap: dict) -> dict | None:
        haystack = " ".join([gap.get("summary", ""), " ".join(gap.get("source_hints", []) or []),
                             " ".join(gap.get("industry", []) or [])]).lower()
        for entry in self.registry:
            if not any(kw.lower() in haystack for kw in entry.get("keywords", [])):
                continue
            try:
                fetched = self.fetcher.fetch(entry["url"])
            except Exception:
                continue
            if fetched.get("status") != 200:
                continue
            facts = parse_facts(fetched["content"], max_facts=entry.get("max_facts", _MAX_FACTS))
            if not facts:
                continue
            return {
                "source_url": entry["url"], "author": entry.get("author", ""),
                "license": entry.get("license", ""), "source_kind": normalize_source_kind(entry.get("source_kind", "other")),
                "publisher_class": entry.get("publisher_class", "public_authority" if entry.get("gov") else None),
                "scraped_at": fetched["fetched_at"], "content_hash": content_hash(fetched["content"]),
                "payload": {"name": entry.get("name") or gap.get("summary", "Scraped corpus"),
                            "industry": entry.get("industry") or gap.get("industry", []),
                            "capability": ["retrieval"], "facts": facts,
                            # dynamic ⇒ access.py routes it to live_subscription (freshness = the value)
                            "freshness": "volatile"},
            }
        return None


def freshness_record(source: dict, *, prev_hash: str | None = None) -> dict:
    """A CDC/freshness row for a scraped source (subscribers get refresh/revocation alerts)."""
    cdc = detect_change(prev_hash, "")  # caller passes content via detect_change normally
    return {
        "source_url": source.get("source_url"), "scraped_at": source.get("scraped_at"),
        "content_hash": source.get("content_hash"), "freshness": "volatile",
        "status": "new" if prev_hash is None else ("changed" if source.get("content_hash") != prev_hash else "unchanged"),
    }


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    registry = [{"keywords": ["philippines", "aml"], "url": "https://bsp.gov.ph/aml",
                 "author": "Bangko Sentral ng Pilipinas", "license": "CC0-1.0", "source_kind": "regulation",
                 "gov": True, "name": "PH AML thresholds (BSP)"}]
    page_v1 = "BSP Circular 1230: cash-withdrawal scrutiny threshold is PHP 1,000,000.\n\nCovered persons must file CTRs."
    scout = WebSourceScout(registry, fetcher=CannedFetcher({"https://bsp.gov.ph/aml": page_v1}))

    gap = {"summary": "philippines aml thresholds 2026", "source_hints": ["bsp.gov.ph"], "industry": ["financial-crime"]}
    src = scout.find(gap)
    check("scout matched + fetched", bool(src) and src["source_url"] == "https://bsp.gov.ph/aml", str(src))
    check("provenance captured (author/license/scraped_at/hash)",
          src["author"] and src["license"] and src["scraped_at"] and src["content_hash"])
    check("publisher_class = public_authority (gov)", src["publisher_class"] == "public_authority")
    check("facts parsed", len(src["payload"]["facts"]) == 2, str(src["payload"]["facts"]))
    check("dynamic corpus (freshness volatile)", src["payload"]["freshness"] == "volatile")
    check("no match ⇒ None", scout.find({"summary": "unrelated topic"}) is None)

    # the scraped gov source flows into the monetization model exactly right
    from scripts.foundry.access import classify_access
    from scripts.foundry.contracts import Candidate
    from scripts.foundry.openness import classify as classify_openness
    cand = Candidate(target_type="knowledge-pack",
                     body={"name": "PH AML", "retrieval": ["keyword"], "freshness": "volatile",
                           "industry": ["financial-crime"]},
                     source=src)
    check("gov-scraped corpus ⇒ OPEN content", classify_openness(cand)["tier"] == "open", str(classify_openness(cand)))
    acc = classify_access(cand)
    check("dynamic gov corpus ⇒ live_subscription delivery", acc["delivery"] == "live_subscription", str(acc))
    check("freshness feed is billable (refresh)", "refresh" in acc["billable_events"])

    # CDC: a changed page is detected; an unchanged one isn't
    h1 = src["content_hash"]
    page_v2 = page_v1.replace("1,000,000", "2,000,000")   # the threshold moved
    check("CDC detects a changed source", detect_change(h1, page_v2)["changed"] is True)
    check("CDC: unchanged source not flagged", detect_change(h1, page_v1)["changed"] is False)

    print(f"\n{'all scrapers self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _refresh(registry_path: str) -> int:
    """Live: scrape each registered source, print provenance + CDC. Needs network + a registry."""
    p = Path(registry_path)
    if not p.exists():
        print(json.dumps({"note": f"no registry at {registry_path}; add gap-keyword→source rows to enable scraping"}))
        return 0
    registry = [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")]
    scout = WebSourceScout(registry)
    for entry in registry:
        gap = {"summary": " ".join(entry.get("keywords", [])), "source_hints": [entry["url"]]}
        src = scout.find(gap)
        print(json.dumps({"url": entry["url"], "ok": bool(src),
                          "content_hash": (src or {}).get("content_hash"),
                          "facts": len((src or {}).get("payload", {}).get("facts", []))}, sort_keys=True))
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Foundry live source scrapers (freshness engine).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--refresh", action="store_true", help="scrape registered sources (live)")
    p.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.refresh:
        return _refresh(args.registry)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
