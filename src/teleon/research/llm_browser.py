"""src.teleon.research.llm_browser — the REAL low-cost-LLM-driven browser driver (the catalog's browse-tier component).

The expensive tier of the research descent, made real: a low-cost LLM drives a headless browser EFFICIENTLY — render a
page, ask the cheap model to extract the target field, and if it isn't there pick the single most-promising link and go
one level deeper — STOPPING as soon as the field is found, with hard caps on steps and tokens. This is selected by
``src/openharnesshub/research_catalog.select_component`` ONLY when a runner needs deep_detail/js_render/interaction that
cheaper feed/api tiers can't get (and only when affordable + the runtime is present).

Ports are INJECTED (so it's offline-testable + honest):
  * ``render(url) -> {title, text, links}``  — default shells to e2e/scrape_url.mjs (chromium). Degrades to a clear
    ``unavailable`` result if node/chromium/network is missing (never fabricates a page).
  * ``llm(prompt) -> str``                    — default is the ollama low-cost lane; if no key, a DETERMINISTIC keyword
    fallback runs instead (returns the rendered text + an honest "no LLM lane" note — never invents an answer).

Teleon may import the open layer; the OHH catalog DECLARES the component, Teleon PROVIDES this driver (same injection
pattern as the descent_brain generator). Every result is serves_truth=false and carries a receipt (steps/pages/tokens).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_RENDER_MJS = _REPO / "e2e" / "scrape_url.mjs"
_MAX_STEPS = 3            # hard cap on pages visited (bounded — the browser is the expensive tier)
_MAX_CHARS = 6000        # cap the text handed to the LLM (token discipline)


@dataclass
class BrowseResult:
    url: str
    goal: str
    found: bool
    answer: str
    pages_visited: int
    steps: int
    llm_calls: int
    approx_tokens: int
    trail: list = field(default_factory=list)
    note: str = ""
    serves_truth: bool = False

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _default_render(url: str) -> dict:
    """Render via the default browser PORT (engine-agnostic; single-sourced in browser_port.PlaywrightBrowser).
    Kept for back-compat — new code injects a BrowserPort. Returns {title,text,links} or {error:...}; never raises."""
    from src.teleon.research.browser_port import select_browser
    return select_browser("auto").render(url)


# LLM selection now goes through the model-AGNOSTIC port (src.teleon.llm_port.as_callable) — any provider, populated
# from the model index + lanes — so a future model drops in with no change here. (was a hardcoded ollama helper.)


def _deterministic_extract(goal: str, text: str) -> str:
    """No-LLM fallback: return the sentence/line best matching the goal terms (honest, not invented)."""
    terms = [w for w in re.split(r"\W+", goal.lower()) if len(w) > 2]
    if not terms or not text:
        return ""
    best, score = "", 0
    for line in re.split(r"(?<=[.!?])\s+|\n", text):
        s = sum(1 for t in terms if t in line.lower())
        if s > score:
            best, score = line.strip()[:300], s
    return best if score >= max(1, len(terms) // 2) else ""


def _pick_link(goal: str, links: list, visited: set) -> str | None:
    terms = [w for w in re.split(r"\W+", goal.lower()) if len(w) > 2]
    best, score = None, 0
    for ln in links:
        href = ln.get("href", "")
        if not href or href in visited:
            continue
        s = sum(1 for t in terms if t in (ln.get("text", "") + " " + href).lower())
        if s > score:
            best, score = href, s
    return best


class LLMBrowserDriver:
    """Low-cost-LLM-driven, bounded browser. browse(url, goal) → BrowseResult (+ receipt). serves_truth=false."""

    def __init__(self, *, render=None, browser=None, llm="auto", max_steps: int = _MAX_STEPS, max_chars: int = _MAX_CHARS):
        from src.teleon.llm_port import as_callable
        from src.teleon.research.browser_port import select_browser
        # BROWSER port (engine-agnostic): a BrowserPort, a (url)->dict callable, a name/id, or the default engine.
        if browser is not None:
            self.render = browser.render if hasattr(browser, "render") else (
                browser if callable(browser) else select_browser(browser).render)
        elif render is not None:
            self.render = render                              # back-compat: an injected render callable
        else:
            self.render = select_browser("auto").render
        # LLM port (model-agnostic): a port, a (prompt)->str callable, a name, or None — as_callable normalizes it
        # (returns None when no LLM is available → the deterministic fallback below, honest).
        self.llm = as_callable(llm)
        self.max_steps = max_steps
        self.max_chars = max_chars

    def _extract(self, goal: str, text: str) -> tuple[str, int, int]:
        """Return (answer, llm_calls, approx_tokens). LLM if available, else deterministic. 'NOT_FOUND'/'' = not found."""
        snippet = (text or "")[: self.max_chars]
        if self.llm:
            ans = (self.llm(f"GOAL: {goal}\n\nPAGE TEXT:\n{snippet}") or "").strip()
            return ans, 1, len(snippet) // 4
        return _deterministic_extract(goal, snippet), 0, 0

    def browse(self, url: str, *, goal: str, budget_steps: int | None = None) -> BrowseResult:
        steps_cap = min(self.max_steps, budget_steps or self.max_steps)
        visited: set = set()
        trail: list = []
        llm_calls = approx_tokens = 0
        current = url
        for step in range(steps_cap):
            page = self.render(current)
            visited.add(current)
            if page.get("error"):
                trail.append({"url": current, "error": page["error"]})
                # honest: can't reach the page (no network/runtime) — stop, report unavailable
                return BrowseResult(url, goal, False, "", len(visited), step + 1, llm_calls, approx_tokens,
                                    trail, note=page["error"])
            text = page.get("text", "")
            ans, calls, toks = self._extract(goal, text)
            llm_calls += calls
            approx_tokens += toks
            trail.append({"url": current, "title": page.get("title", "")[:80], "extracted": (ans or "")[:120]})
            if ans and ans.upper() != "NOT_FOUND":
                note = "" if self.llm else "no LLM lane configured — deterministic keyword extraction (honest fallback)"
                return BrowseResult(url, goal, True, ans, len(visited), step + 1, llm_calls, approx_tokens, trail, note=note)
            # not found → descend one level via the most promising link (the 'driving' decision)
            nxt = _pick_link(goal, page.get("links", []), visited)
            if not nxt:
                break
            current = nxt
        note = "target not found within step budget" + ("" if self.llm else " (no LLM lane — deterministic fallback)")
        return BrowseResult(url, goal, False, "", len(visited), len(visited), llm_calls, approx_tokens, trail, note=note)


def make_browser_component(**kw):
    """Build the injectable research component the catalog references (mirrors generators.make_descent_brain_generator).
    Returns a callable(url, goal)->dict that the operator layer wires for the catalog's `llm_driven_browser` id."""
    driver = LLMBrowserDriver(**kw)
    def run(url: str, goal: str = "the page's main content", budget_steps: int | None = None) -> dict:
        return driver.browse(url, goal=goal, budget_steps=budget_steps).as_dict()
    return run


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # Injected render + LLM ports → deterministic, offline, proves the bounded driving loop.
    pages = {
        "https://x/start": {"title": "Start", "text": "welcome. nothing useful here.",
                            "links": [{"text": "pricing details", "href": "https://x/pricing"}, {"text": "blog", "href": "https://x/blog"}]},
        "https://x/pricing": {"title": "Pricing", "text": "Our pricing is $42 per month for the pro plan.",
                              "links": []},
    }
    render = lambda u: pages.get(u, {"error": "404"})  # noqa: E731
    llm = lambda prompt: ("$42 per month" if "$42" in prompt else "NOT_FOUND")  # noqa: E731

    d = LLMBrowserDriver(render=render, llm=llm)
    r = d.browse("https://x/start", goal="monthly pricing")
    ck("LLM-driven: descends start → most-promising link (pricing) → finds the field", r.found and "$42" in r.answer)
    ck("efficient: stops as soon as found (2 pages, not the blog)", r.pages_visited == 2 and r.steps == 2)
    ck("receipt records llm_calls + approx_tokens + a trail", r.llm_calls >= 1 and isinstance(r.trail, list) and len(r.trail) == 2)
    ck("serves_truth=false", r.serves_truth is False)

    # honest degrade: no LLM lane → deterministic keyword extraction (never invents)
    d2 = LLMBrowserDriver(render=render, llm=None)
    r2 = d2.browse("https://x/start", goal="pricing month pro plan")
    ck("no-LLM fallback still finds via keyword match + flags the fallback honestly", r2.found and "no LLM lane" in r2.note)

    # honest unavailable: render error (no network/runtime) → not found + the error surfaced, NOT fabricated
    d3 = LLMBrowserDriver(render=lambda u: {"error": "render unavailable: net blocked"}, llm=llm)
    r3 = d3.browse("https://x/start", goal="anything")
    ck("render-unavailable is reported honestly (no fabricated content)", r3.found is False and "unavailable" in r3.note and r3.answer == "")

    # budget cap respected
    d4 = LLMBrowserDriver(render=render, llm=lambda p: "NOT_FOUND", max_steps=5)
    r4 = d4.browse("https://x/start", goal="zzz", budget_steps=1)
    ck("step budget is respected (1 page only)", r4.pages_visited == 1)

    print("\n" + ("PASS - llm_browser: a low-cost-LLM-driven, BOUNDED browser — descends to the target field, stops "
                  "early, caps steps+tokens, emits a receipt; degrades honestly (deterministic fallback with no LLM "
                  "lane; reports render-unavailable rather than fabricating). serves_truth=false." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
