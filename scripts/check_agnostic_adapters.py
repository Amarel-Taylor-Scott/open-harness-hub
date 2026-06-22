#!/usr/bin/env python3
"""check_agnostic_adapters — model-/tool-AGNOSTIC ports scale to FUTURE LLMs + browsers with zero component change.

The owner's requirement (2026-06-21): more LLMs and more browsers will keep arriving, so every component depends on an
agnostic adapter/port, and the selectable options are POPULATED FROM our registries. This proves it:
  * the LLM port enumerates from the model index + provider lanes; the browser port from the browsing registry;
  * a model_id selects its provider lane; a registry browser maps to its engine's adapter; an unwired engine is honest;
  * THE DROP-IN TEST: register a brand-new "future" LLM + a "future" browser in ONE line each, and an UNCHANGED
    LLMBrowserDriver drives them — i.e. a 2027 model/browser needs no component edit.
serves_truth=false.

  python3 scripts/check_agnostic_adapters.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _self_test() -> int:
    from src.teleon.llm_port import (available_llms, select_llm, register_llm_adapter, CallableLLM, as_callable)
    from src.teleon.research.browser_port import (available_browsers, select_browser, register_browser_adapter,
                                                  CallableBrowser, NotWiredBrowser)
    from src.teleon.research.llm_browser import LLMBrowserDriver
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    al, ab = available_llms(), available_browsers()
    ck("LLM port is POPULATED FROM registries (model-index models + provider lanes)",
       len(al["models"]) >= 5 and len(al["lanes"]) >= 1 and "auto" in al["adapters"])
    ck("browser port is POPULATED FROM the browsing registry (>= 20 browsers)",
       len(ab["registry_browsers"]) >= 20 and "chromium" in ab["engine_adapters"])
    ck("a model_id from the index selects its PROVIDER lane (agnostic)", select_llm("claude-opus-4-8").name == "provider:anthropic")
    ck("a registry browser maps to its ENGINE adapter (chromium → playwright)", select_browser("crawl4ai").name == "playwright")
    ck("a declared-but-UNWIRED engine is honest (NotWired, never fabricates)",
       isinstance(select_browser("webdriver_bidi"), NotWiredBrowser) and "not wired" in select_browser("webdriver_bidi").render("x")["error"])
    ck("no LLM available → as_callable returns None (caller's deterministic path, honest)", as_callable("deterministic") is None)

    # ── THE DROP-IN TEST: a FUTURE LLM + a FUTURE browser register in one line; the UNCHANGED driver uses them ──
    register_llm_adapter("future_llm_2027",
                         lambda: CallableLLM(lambda p: "$99/mo" if "$99" in p else "NOT_FOUND", name="future_llm_2027"))
    register_browser_adapter("future_browser_2027",
                             lambda: CallableBrowser(lambda u: {"title": "Future", "text": "the plan is $99/mo here", "links": []},
                                                     name="future_browser_2027"))
    ck("a FUTURE LLM is now selectable (registered, populated)", "future_llm_2027" in available_llms()["adapters"]
       and select_llm("future_llm_2027").available() is True)
    ck("a FUTURE browser is now selectable (registered)", "future_browser_2027" in available_browsers()["name_adapters"])
    # the SAME driver class, UNCHANGED, driven by the future LLM + future browser
    driver = LLMBrowserDriver(browser=select_browser("future_browser_2027"), llm="future_llm_2027")
    r = driver.browse("https://x/start", goal="monthly price $99")
    ck("the UNCHANGED LLMBrowserDriver drives the future LLM + future browser end-to-end (future-proof)",
       r.found and "$99" in r.answer)
    register_browser_adapter("future_engine_2027", lambda: CallableBrowser(lambda u: {"text": ""}), engine=True)
    ck("a FUTURE engine adapter registers too (every registry browser on it reuses it, zero code)",
       "future_engine_2027" in available_browsers()["engine_adapters"])

    # the consuming component depends on the PORTS, not a hardcoded provider/engine
    src = (REPO / "src" / "teleon" / "research" / "llm_browser.py").read_text()
    ck("the browser component depends on the ports (as_callable + select_browser), not a hardcoded provider",
       "as_callable" in src and "select_browser" in src and "resolve_provider" not in src)

    print("\n" + ("PASS - check_agnostic_adapters: LLMs + browsers are behind model-/engine-AGNOSTIC ports populated "
                  "from the registries; a model_id maps to its lane, a registry browser to its engine; a FUTURE LLM + "
                  "FUTURE browser drop in via one-line registration and an UNCHANGED component drives them. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
