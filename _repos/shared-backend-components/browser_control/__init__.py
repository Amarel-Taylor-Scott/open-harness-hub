"""browser_control — the DRIVER-NEUTRAL browser-control adapter package.

One stable command surface (``BrowserAdapter``) that many interchangeable drivers back — the MULTI-PATH law
made literal for browsers. Every adapter WRAPS the shipped read-only harness
(``scripts.primitive_browser_control_harness``): its BackendPort drivers, its TabControlAPI command plane +
receipt minter + side-effect ladder, and its ``browser_*`` extraction primitives. Nothing here re-implements
CDP, HTTP, or extraction; the only added logic is the driver-neutral adapter layer (multi-tab caching, the
non-raising ``{"supported": False, ...}`` result, a stdlib table extractor, receipt normalization).

Everything emitted is candidate-only (``candidate=true, serves_truth=false``); read-only by default; secrets
redacted. See ``docs/DRIVER_NEUTRAL_BROWSER_CONTROL.md`` and
``docs/BROWSER_CONTROL_DECISION_FRAMEWORK.md``.

    from browser_control import FakeAdapter, get_adapter
    fa = FakeAdapter(); fa.start_session(); fa.navigate("https://fixture.example/")
"""
from __future__ import annotations

from browser_control.adapter import (  # noqa: F401
    CAPABILITY_KEYS,
    RECEIPT_RECORD_TYPE,
    SIDE_EFFECT_LEVELS,
    BrowserAdapter,
    extract_tables_from_html,
    make_counter_clock,
    normalize_receipt,
)
from browser_control import safety  # noqa: F401
from browser_control.adapters.cdp_adapter import CdpAdapter  # noqa: F401
from browser_control.adapters.http_scrape_adapter import HttpScrapeAdapter  # noqa: F401
from browser_control.adapters.playwright_adapter import PlaywrightAdapter  # noqa: F401
from browser_control.fake_adapter import FakeAdapter  # noqa: F401

# ── the web-INGESTION adapters: a parallel family that fetches/parses/crawls/searches/LLM-extracts. They are
#: NOT BrowserAdapter subclasses (different, narrower surfaces) — the browser command plane is one layer, the
#: ingestion primitives are the composable layer below/around it. Module tops are stdlib-only (optional clients
#: import lazily) so these imports never require requests/httpx/scrapy/etc. to be installed.
from browser_control.crawler_adapter import CrawlerAdapter  # noqa: F401
from browser_control.fetch_adapter import FetchAdapter  # noqa: F401
from browser_control.llm_extraction_adapter import LLMExtractionAdapter  # noqa: F401
from browser_control.parser_adapter import ParserAdapter  # noqa: F401
from browser_control.search_adapter import SearchAdapter  # noqa: F401

#: name -> BrowserAdapter class (the driver-neutral command plane). Design-only drivers (puppeteer/selenium/
#: mcp/lightpanda/extension/remote_browser/browser_use) live as markdown seams under browser_control/adapters/.
ADAPTERS: dict[str, type[BrowserAdapter]] = {
    "fake": FakeAdapter,
    "http_scrape": HttpScrapeAdapter,
    "cdp": CdpAdapter,
    "playwright": PlaywrightAdapter,
}

#: name -> ingestion adapter class (fetch/parse/crawl/search/LLM-extract). A separate registry because these do
#: not share the BrowserAdapter surface; a router picks from BOTH families by need (the layered architecture).
INGESTION_ADAPTERS: dict[str, type] = {
    "fetch": FetchAdapter,
    "parser": ParserAdapter,
    "crawler": CrawlerAdapter,
    "llm_extraction": LLMExtractionAdapter,
    "search": SearchAdapter,
}


def get_adapter(name: str, **kw) -> BrowserAdapter:
    """Construct a BrowserAdapter by name (the factory a decision-framework router calls). KeyError on unknown."""
    if name not in ADAPTERS:
        raise KeyError(f"unknown browser_control adapter {name!r}; known: {sorted(ADAPTERS)}")
    return ADAPTERS[name](**kw)


def get_ingestion_adapter(name: str, **kw):
    """Construct an ingestion adapter (fetch/parser/crawler/llm_extraction/search) by name. KeyError on unknown."""
    if name not in INGESTION_ADAPTERS:
        raise KeyError(f"unknown ingestion adapter {name!r}; known: {sorted(INGESTION_ADAPTERS)}")
    return INGESTION_ADAPTERS[name](**kw)


__all__ = [
    "BrowserAdapter", "FakeAdapter", "HttpScrapeAdapter", "CdpAdapter", "PlaywrightAdapter",
    "FetchAdapter", "ParserAdapter", "CrawlerAdapter", "LLMExtractionAdapter", "SearchAdapter",
    "CAPABILITY_KEYS", "RECEIPT_RECORD_TYPE", "SIDE_EFFECT_LEVELS",
    "normalize_receipt", "extract_tables_from_html", "make_counter_clock",
    "get_adapter", "get_ingestion_adapter", "ADAPTERS", "INGESTION_ADAPTERS", "safety",
]
