#!/usr/bin/env python3
"""browser_control.ingestion_self_test — the OFFLINE, deterministic, MUTATION-GATED proof for the five
web-ingestion adapters added alongside the driver-neutral browser adapters:

    FetchAdapter · ParserAdapter · CrawlerAdapter · LLMExtractionAdapter · SearchAdapter

No public internet, no browser, no keys. FetchAdapter is exercised against the LOCAL stdlib fixture lab
(loopback only); the crawler runs over an in-memory injected site; parser/llm/search are pure/offline. It
asserts the load-bearing contract for each:

  * FetchAdapter — a real GET returns a structured record; robots.txt DISALLOW blocks a URL (never fetched);
    a 404 and a bad scheme degrade to a structured ``ok=False`` (never raises); backend selection is real.
  * ParserAdapter — extracts a TABLE, links, and metadata (title/description/lang) from the fixture HTML with
    stdlib only; secrets are redacted; a no-table page yields zero tables (the extractor is real, not always-1).
  * CrawlerAdapter — a robots ``Disallow`` skips the page (reported, never captured); flipping robots to
    Allow-all CAPTURES it (the mutation gate — the robots gate does real work); rate-limit skips are reported;
    the page cap is honored; sitemap.xml parses.
  * LLMExtractionAdapter — the offline stub fills EXACTLY the requested schema keys, marked untrusted;
    ``verify_extraction`` is a real deterministic grounding check (grounded → all_grounded True; an ungrounded
    value → flagged — the mutation gate); secrets never survive.
  * SearchAdapter — with no key set every provider reports ``available_with_credentials`` and ``search`` returns
    empty results (never calls out, never fabricates), naming the env var to set.

    python3 browser_control/ingestion_self_test.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install  # noqa: E402

_install()

import json  # noqa: E402
from typing import Any  # noqa: E402

from browser_control.adapter import make_counter_clock  # noqa: E402
from browser_control.crawler_adapter import CrawlerAdapter  # noqa: E402
from browser_control.fetch_adapter import HTTP_BACKENDS, FetchAdapter  # noqa: E402
from browser_control.llm_extraction_adapter import LLMExtractionAdapter  # noqa: E402
from browser_control.parser_adapter import ParserAdapter  # noqa: E402
from browser_control.search_adapter import SearchAdapter  # noqa: E402
from scripts.run_browser_fixture_lab import STATIC_TEXT_MARKER, _home_html, serve_in_thread  # noqa: E402

_SECRETS = ("sk-live-SHOULDNOTLEAK1234567", "supersecretvalue123456", "Bearer abcdef")
_CRAWL_HOST = "http://crawl.fixture.example"


def _no_secret(*objs: Any) -> bool:
    blob = json.dumps(objs, default=str)
    return not any(m in blob for m in _SECRETS)


def _crawl_site() -> dict[str, str]:
    """An in-memory site: home links to /a /b /private; robots disallows /private; a 2-url sitemap."""
    def page(body: str) -> str:
        return f"<!doctype html><html><head><title>t</title></head><body>{body}</body></html>"
    return {
        _CRAWL_HOST + "/": page('<a href="/a">a</a> <a href="/b">b</a> <a href="/private">secret</a>'),
        _CRAWL_HOST + "/a": page("<p>page a</p>"),
        _CRAWL_HOST + "/b": page("<p>page b</p>"),
        _CRAWL_HOST + "/private": page("<p>should be blocked</p>"),
        _CRAWL_HOST + "/robots.txt": "User-agent: *\nDisallow: /private\n",
        _CRAWL_HOST + "/sitemap.xml": ('<?xml version="1.0" encoding="UTF-8"?>'
                                       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                       f'<url><loc>{_CRAWL_HOST}/</loc></url>'
                                       f'<url><loc>{_CRAWL_HOST}/a</loc></url></urlset>'),
    }


def self_test() -> int:  # noqa: C901 — one linear proof; readability beats decomposition here
    checks: list[tuple[str, bool]] = []

    # ── FetchAdapter (loopback fixture only) ───────────────────────────────────────────────────────────────────
    httpd, url = serve_in_thread(0)
    try:
        robots = "User-agent: *\nDisallow: /private\n"
        fa = FetchAdapter(backend="urllib", robots_fetch=lambda u: robots)
        r_ok = fa.get(url + "/")
        checks.append(("FetchAdapter GET fixture -> 200, static marker present, candidate-only",
                       r_ok["supported"] is True and r_ok["ok"] is True and r_ok["status"] == 200
                       and STATIC_TEXT_MARKER in r_ok["text"] and r_ok["serves_truth"] is False))
        r_block = fa.get(url + "/private")
        checks.append(("FetchAdapter robots Disallow blocks the URL (never fetched)",
                       r_block["ok"] is False and r_block["blocked"] is True
                       and r_block["failure_mode"] == "robots_disallow" and r_block["status"] == 0))
        r_404 = fa.get(url + "/no-such-route")
        r_scheme = fa.get("ftp://nope/x")
        checks.append(("FetchAdapter degrades to structured ok=False on 404 + bad scheme (never raises)",
                       r_404["ok"] is False and r_404["failure_mode"] == "http_404"
                       and r_scheme["ok"] is False and r_scheme["failure_mode"] == "bad_scheme"))
        fa_auto = FetchAdapter(respect_robots=False)
        r_auto = fa_auto.get(url + "/")
        checks.append(("FetchAdapter backend selection is real (auto picks a present client)",
                       r_auto["ok"] is True and r_auto["backend"] in HTTP_BACKENDS
                       and fa_auto.available_backends()["urllib"] is True))
    finally:
        httpd.shutdown()
        httpd.server_close()

    # ── ParserAdapter (pure, offline) ──────────────────────────────────────────────────────────────────────────
    p = ParserAdapter()
    parsed = p.parse(_home_html(), base_url="http://fixture/")
    table_cells = [c for t in parsed["tables"] for r in t["rows"] for c in r]
    checks.append(("ParserAdapter extracts a table from the fixture (cells present)",
                   parsed["n_tables"] >= 1 and "alpha" in table_cells))
    checks.append(("ParserAdapter extracts links + metadata (openapi link, title, lang)",
                   any("openapi.json" in u for u in parsed["links"])
                   and parsed["metadata"]["title"] == "Browser Control Fixture Lab"
                   and parsed["metadata"]["lang"] == "en"))
    txt = p.extract_text(_home_html())
    checks.append(("ParserAdapter readable text includes the static marker",
                   STATIC_TEXT_MARKER in txt["text"] and txt["chars"] > 0))
    secret_txt = p.extract_text("<p>api_key: sk-live-SHOULDNOTLEAK1234567 here</p>")
    checks.append(("ParserAdapter redacts secrets in extracted text",
                   secret_txt["secrets_redacted"] >= 1 and _no_secret(secret_txt)))
    no_table = p.extract_tables("<html><body><p>no tables here</p></body></html>")
    checks.append(("ParserAdapter table extractor is real (no-table page -> 0 tables)",
                   no_table["n_tables"] == 0))

    # ── CrawlerAdapter (offline injected site) ─────────────────────────────────────────────────────────────────
    site = _crawl_site()
    fetch = site.get
    ca = CrawlerAdapter(fetch=fetch, robots_fetch=fetch, min_interval=0.0, clock=make_counter_clock(step=1.0))
    res = ca.crawl([_CRAWL_HOST + "/"], max_pages=10, min_interval=0.0)
    captured_urls = [pg["url"] for pg in res["pages"] if pg["captured"]]
    checks.append(("CrawlerAdapter robots Disallow: /private skipped, /a + /b captured",
                   (_CRAWL_HOST + "/private") in res["skipped_robots"]
                   and (_CRAWL_HOST + "/private") not in captured_urls
                   and (_CRAWL_HOST + "/a") in captured_urls and (_CRAWL_HOST + "/b") in captured_urls))
    # MUTATION GATE: flip robots to Allow-all -> the previously-blocked page is now captured
    ca_open = CrawlerAdapter(fetch=fetch, robots_fetch=lambda u: "User-agent: *\nAllow: /\n",
                             min_interval=0.0, clock=make_counter_clock(step=1.0))
    res_open = ca_open.crawl([_CRAWL_HOST + "/"], max_pages=10, min_interval=0.0)
    open_captured = [pg["url"] for pg in res_open["pages"] if pg["captured"]]
    checks.append(("CrawlerAdapter mutation gate: Allow-all robots now CAPTURES /private",
                   (_CRAWL_HOST + "/private") in open_captured and res_open["skipped_robots"] == []))
    ca_rl = CrawlerAdapter(fetch=fetch, robots_fetch=fetch, clock=make_counter_clock(step=1.0))
    res_rl = ca_rl.crawl([_CRAWL_HOST + "/"], max_pages=10, min_interval=1000.0)
    checks.append(("CrawlerAdapter rate-limit skips reported under a tight interval",
                   len(res_rl["skipped_rate_limited"]) >= 1))
    res_cap = ca.crawl([_CRAWL_HOST + "/"], max_pages=2, min_interval=0.0)
    checks.append(("CrawlerAdapter honors the page cap", res_cap["n_pages"] == 2 and res_cap["hit_page_cap"] is True))
    sm = ca.fetch_sitemap(_CRAWL_HOST + "/")
    checks.append(("CrawlerAdapter parses sitemap.xml (2 urls)",
                   sm["found"] is True and sm["n_urls"] == 2 and (_CRAWL_HOST + "/a") in sm["urls"]))
    checks.append(("CrawlerAdapter robots_allows reflects the policy",
                   ca.robots_allows(_CRAWL_HOST + "/a") is True
                   and ca.robots_allows(_CRAWL_HOST + "/private") is False))

    # ── LLMExtractionAdapter (offline stub) ────────────────────────────────────────────────────────────────────
    lx = LLMExtractionAdapter()
    src = ("Invoice total is $42.50 dated 2026-07-08. Contact billing@example.com "
           "for the API at https://api.example.com/v1.")
    schema = {"amount": "the total", "date": "iso date", "email": "contact", "title": ""}
    ex = lx.extract_schema(src, schema)
    checks.append(("LLMExtractionAdapter stub fills EXACTLY the schema keys, marked untrusted",
                   set(ex["extraction"].keys()) == set(schema) and ex["keys_match_schema"] is True
                   and ex["untrusted"] is True and ex["serves_truth"] is False))
    checks.append(("LLMExtractionAdapter stub extracts sane values (amount/date/email)",
                   ex["extraction"]["amount"] == "$42.50" and ex["extraction"]["date"] == "2026-07-08"
                   and ex["extraction"]["email"] == "billing@example.com"))
    v_ok = lx.verify_extraction({"amount": "$42.50", "date": "2026-07-08"}, src)
    v_bad = lx.verify_extraction({"amount": "$42.50", "bogus": "NOTINTEXT_XYZ"}, src)
    checks.append(("LLMExtractionAdapter verify_extraction: grounded=all_grounded True; ungrounded flagged (mutation gate)",
                   v_ok["all_grounded"] is True and v_ok["n_ungrounded"] == 0
                   and v_bad["all_grounded"] is False and v_bad["n_ungrounded"] == 1))
    qa = lx.ask_questions(src, ["what is the total amount?", "what is the contact email?"])
    prims = lx.extract_primitives(src)
    checks.append(("LLMExtractionAdapter ask_questions + extract_primitives return untrusted candidates",
                   qa["n"] == 2 and all(a["untrusted"] for a in qa["answers"])
                   and prims["n"] >= 1 and all(pr["untrusted"] for pr in prims["primitives"])))
    ex_secret = lx.extract_schema("token=supersecretvalue123456 and the name is Bob", {"name": "", "token": ""})
    caps_llm = lx.capabilities()
    checks.append(("LLMExtractionAdapter redacts secrets + capabilities() leaks none",
                   _no_secret(ex_secret) and "providers" in caps_llm and _no_secret(caps_llm)))

    # ── SearchAdapter (offline, no keys) ───────────────────────────────────────────────────────────────────────
    sa = SearchAdapter()
    provs = sa.providers()
    checks.append(("SearchAdapter lists 5 providers, all key-absent, available_with_credentials",
                   len(provs) == 5 and all(pr["key_present"] is False for pr in provs)
                   and any(pr["status"] == "available_with_credentials" for pr in provs)))
    sr = sa.search("open registry of AI primitives")
    checks.append(("SearchAdapter keyless search: available_with_credentials, empty results, names the env var",
                   sr["ok"] is False and sr["status"] == "available_with_credentials" and sr["results"] == []
                   and "TAVILY_API_KEY" in sr["reason"] and _no_secret(sr)))
    checks.append(("SearchAdapter capabilities report no key present",
                   sa.capabilities()["any_key_present"] is False))

    # ── report ─────────────────────────────────────────────────────────────────────────────────────────────────
    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    print(("PASS" if ok else "FAIL") + " - browser_control ingestion adapters "
          "(fetch/parser/crawler/llm_extraction/search): offline, mutation-gated proof "
          f"{sum(v for _, v in checks)}/{len(checks)} checks — read-only, robots-gated, secrets redacted, "
          "LLM output untrusted, search keyless=available_with_credentials, serves_truth=false.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv or not argv:
        return self_test()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
