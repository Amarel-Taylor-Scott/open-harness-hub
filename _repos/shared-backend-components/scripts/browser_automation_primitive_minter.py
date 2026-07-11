#!/usr/bin/env python3
"""scripts.browser_automation_primitive_minter — mint governed primitives for the browser-automation / custom-
browser / anti-detection / CDP domain (the space we just used to unblock Gemma behind Cloudflare). Every custom
browser + fork + technique + use-case becomes a reusable primitive: undetected-chromedriver / nodriver /
Playwright-stealth / FlareSolverr / SeleniumBase-UC / Camoufox / Botasaurus x browser forks (ungoogled-chromium,
Brave, Thorium, Cromite, LibreWolf, Camoufox) x techniques (CDP Runtime.evaluate, in-page fetch, cf_clearance
reuse, TLS/JA3 spoof, navigator.webdriver patch, residential proxy, UA rotation) x use-cases (LLM API access
behind Cloudflare, session reuse, headless scraping, challenge solving).

The worked example is real: `openwebui_cdp_bridge` drives the logged-in Chrome via CDP + in-page fetch to reach
Gemma-4 past Cloudflare — that pattern is minted here as a primitive. Deterministic coprime-strided; canonical
ids; candidate/serves_truth=false; usefulness gate = NON-DESTRUCTIVE routing.

    python3 scripts/browser_automation_primitive_minter.py --self-test
    python3 scripts/browser_automation_primitive_minter.py --mint --target 20000
    python3 scripts/browser_automation_primitive_minter.py --grid-size
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Iterator, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"browser_automation_primitive_minter requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BROWSER_ID_PREFIX = "prim-browser"
BROWSER_RECORD_TYPE = "browser_automation_primitive_candidate"
STAGED_FILENAME = "browser_automation_primitive_candidates.jsonl"
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_COPRIME_STRIDE = 2147483647

# custom browsers / automation drivers (anti-detection capable)
_DRIVERS: tuple[str, ...] = (
    "undetected-chromedriver", "nodriver", "Playwright-stealth", "puppeteer-extra-stealth", "selenium-stealth",
    "SeleniumBase UC mode", "FlareSolverr", "Botasaurus", "patchright", "Camoufox", "Chrome DevTools Protocol",
    "Playwright persistent context", "curl_cffi (TLS-impersonate)", "hrequests", "DrissionPage",
)
# browser forks / builds
_FORKS: tuple[str, ...] = (
    "ungoogled-chromium", "Brave", "Chromium", "Thorium", "Cromite", "LibreWolf", "Waterfox", "Camoufox",
    "Firefox ESR", "Chrome stable", "Chrome for Testing", "Edge",
)
# techniques
_TECHNIQUES: tuple[str, ...] = (
    "CDP Runtime.evaluate in-page fetch", "reuse the cf_clearance cookie + user-agent", "auto-solve the JS challenge by reload-and-poll",
    "patch navigator.webdriver", "spoof the TLS/JA3 fingerprint", "randomize the canvas/WebGL fingerprint",
    "route through a residential proxy", "rotate the user-agent", "reuse a logged-in browser session",
    "connect over the remote-debugging port", "read the auth token from localStorage", "persist cookies across runs",
    "throttle to human-like timing", "block automation-detection scripts",
)
# use-cases
_USE_CASES: tuple[str, ...] = (
    "access an LLM API behind Cloudflare", "scrape a Cloudflare-protected site", "reuse a logged-in SaaS session",
    "run headless automation unattended", "harvest an OpenWebUI/Gemma completion", "solve a bot challenge",
    "extract a session token", "drive an authenticated dashboard", "monitor a page for changes",
    "fill and submit a protected form",
)

_STOP = frozenset("a an the for of to in on with and or via using into from as is are be that this it one".split())
_FRAMES: tuple[str, ...] = (
    "A browser-automation primitive: use {driver} (on {fork}) to {use_case} by {technique}. Typed input and "
    "output; a reusable, composable step for reaching content a plain HTTP client cannot.",
    "To {use_case}, drive {fork} via {driver} and {technique}. Reusable typed primitive.",
    "{use_case} — the '{driver}' primitive on {fork}, technique: {technique}. Composable by typed edges.",
    "With {driver} + {fork}: {technique} in order to {use_case}. A typed, owned browser primitive.",
)


def axis_sizes() -> dict[str, int]:
    return {"drivers": len(_DRIVERS), "forks": len(_FORKS), "techniques": len(_TECHNIQUES), "use_cases": len(_USE_CASES)}


def grid_size() -> int:
    s = axis_sizes()
    return s["drivers"] * s["forks"] * s["techniques"] * s["use_cases"]


_AXIS_ORDER = ("drivers", "forks", "techniques", "use_cases")


def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    return ("".join(p[:1].upper() + p[1:] for p in parts if p) or "X")[:60]


def _card(idx: tuple[int, int, int, int]) -> dict[str, Any]:
    di, fi, ti, ui = idx
    driver, fork, technique, use_case = _DRIVERS[di], _FORKS[fi], _TECHNIQUES[ti], _USE_CASES[ui]
    title = f"{driver}: {use_case} on {fork}"
    frame = _FRAMES[(di * 5 + fi * 3 + ti + ui) % len(_FRAMES)]
    blackbox = frame.format(driver=driver, fork=fork, technique=technique, use_case=use_case)
    tokens = [w.lower() for w in re.findall(r"[a-z]+", (driver + " " + use_case).lower()) if w.lower() not in _STOP][:8]
    input_edge = _camel(_camel(use_case.split()[0]), "target", "input")
    output_edge = _camel(_camel(driver.split()[0]), "result")
    pid = canonical_id(BROWSER_ID_PREFIX, title, blackbox)
    return {
        "record_type": BROWSER_RECORD_TYPE, "schema_version": 1, "kind": "route.primitive",
        "primitive_id": pid, "title": title[:180], "blackbox": blackbox[:1200],
        "input_edge": input_edge, "output_edge": output_edge, "blocking_keys": tokens,
        "browser": {"driver": driver, "fork": fork, "technique": technique, "use_case": use_case},
        "capability_tags": [f"driver:{_camel(driver).lower()}", f"fork:{_camel(fork).lower()}",
                            f"technique:{_camel(technique.split()[0]).lower()}", "browser_automation"],
        "contract": {"input": f"a target for '{use_case}'",
                     "output": f"the result of {use_case} via {driver} ({technique})"},
        "provenance": {"minter": "scripts.browser_automation_primitive_minter", "grid_size": grid_size(),
                       "worked_example": "scripts/openwebui_cdp_bridge.py"},
        "promotion_blockers": ["source_evidence", "correctness_proof", "usefulness_or_enrichment"],
        "readiness": "browser_automation_candidate_unproven", **BOUNDARY,
    }


def _strided_indices(target: int) -> Iterator[tuple[int, int, int, int]]:
    total = grid_size()
    sizes = [axis_sizes()[k] for k in _AXIS_ORDER]
    for i in range(min(target, total)):
        flat = (i * _COPRIME_STRIDE) % total
        rem = flat
        idx = []
        for sz in reversed(sizes):
            idx.append(rem % sz)
            rem //= sz
        yield tuple(reversed(idx))  # type: ignore[misc]


def mint(target: int) -> list[dict[str, Any]]:
    if target < 1:
        raise ValueError("target must be >= 1")
    cards: list[dict[str, Any]] = []
    seen: set = set()
    for idx in _strided_indices(target):
        c = _card(idx)
        if c["primitive_id"] in seen:
            raise ValueError(f"duplicate mint for {c['title']!r}")
        seen.add(c["primitive_id"])
        cards.append(c)
    return cards


def validate_card(card: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if card.get("primitive_id") != canonical_id(BROWSER_ID_PREFIX, card.get("title", ""), card.get("blackbox", "")):
        problems.append("primitive_id does not recompute")
    for ef in ("input_edge", "output_edge"):
        if not _CAMEL_EDGE_RE.match(str(card.get(ef) or "")):
            problems.append(f"{ef} not CamelCase")
    if card.get("serves_truth") is not False or card.get("candidate") is not True:
        problems.append("candidate boundary not stamped")
    text = f"{card.get('title','')} {card.get('blackbox','')}".lower()
    if not all(t in text for t in card.get("blocking_keys", [])[:2]):
        problems.append("blackbox does not carry its leading tokens")
    return problems


def staged_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / STAGED_FILENAME


def write_staged(cards: list[dict[str, Any]], target_path: Optional[Path] = None) -> dict[str, Any]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = target_path or staged_path()
    if p.name != STAGED_FILENAME:
        raise ValueError(f"refusing to write to {p.name!r} — only {STAGED_FILENAME!r} allowed")
    if p.is_symlink() or (p.exists() and p.resolve().name in _VERIFIED_CORPUS_FILENAMES):
        raise ValueError("refused: symlink or verified-corpus target")
    for c in cards:
        probs = validate_card(c)
        if probs:
            raise ValueError(f"card {c.get('primitive_id')} failed validation: {probs}")
    existing = {str(r.get("primitive_id")) for r in (read_jsonl_tolerant(p) if p.exists() else [])}
    appended = 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for c in cards:
            if str(c["primitive_id"]) in existing:
                continue
            existing.add(str(c["primitive_id"]))
            fh.write(json.dumps(c, sort_keys=True) + "\n")
            appended += 1
    return {"appended": appended, "on_file": len(existing), "path": str(p), **BOUNDARY}


def quality_report(cards: list[dict[str, Any]]) -> dict[str, Any]:
    from scripts.primitive_usefulness_gate import measure_pool  # noqa: PLC0415
    m = measure_pool(cards, "browser_automation_mint")
    return {k: m[k] for k in ("n_cards_scored", "placeholder_rate", "weak_rate", "verdict_counts", "stamped_clusters")}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("grid computed from the browser axes",
                   grid_size() == len(_DRIVERS) * len(_FORKS) * len(_TECHNIQUES) * len(_USE_CASES) and grid_size() > 5000))
    checks.append(("the real CDP-bridge worked-example primitives are representable (undetected + cf_clearance + LLM behind Cloudflare)",
                   "undetected-chromedriver" in _DRIVERS and any("cf_clearance" in t for t in _TECHNIQUES)
                   and any("LLM API behind Cloudflare" in u for u in _USE_CASES)))
    cards = mint(800)
    checks.append(("mints deterministically + byte-identical",
                   len(cards) == 800 and json.dumps(cards, sort_keys=True) == json.dumps(mint(800), sort_keys=True)))
    checks.append(("every card validates", all(not validate_card(c) for c in cards)))
    checks.append(("ids unique", len({c["primitive_id"] for c in cards}) == len(cards)))
    checks.append(("stride covers many drivers + forks + use-cases",
                   len({c["browser"]["driver"] for c in cards}) >= 10 and len({c["browser"]["fork"] for c in cards}) >= 8
                   and len({c["browser"]["use_case"] for c in cards}) >= 8))
    import tempfile  # noqa: PLC0415
    refused = False
    try:
        write_staged(cards[:1], target_path=Path(tempfile.gettempdir()) / "verified_factory_primitive_cards.jsonl")
    except ValueError:
        refused = True
    checks.append(("write_staged refuses a verified corpus filename", refused))
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / STAGED_FILENAME
        a = write_staged(cards[:50], target_path=tp)
        b = write_staged(cards[:50], target_path=tp)
        checks.append(("append-dedupe", a["appended"] == 50 and b["appended"] == 0))
    qr = quality_report(cards)
    checks.append(("usefulness gate scores the mint", set(qr["verdict_counts"]) == {"pass", "weak", "placeholder"}))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    s = axis_sizes()
    print(f"\nPASS - browser_automation_primitive_minter: {s['drivers']} drivers x {s['forks']} forks x "
          f"{s['techniques']} techniques x {s['use_cases']} use-cases = a {grid_size():,}-point grid; the CDP-"
          f"bridge worked example is a minted primitive; deterministic; NON-DESTRUCTIVE gate. serves_truth=false.")
    return 0


def _mint(target: int) -> int:
    cards = mint(target)
    qr = quality_report(cards)
    wrote = write_staged(cards)
    rec = {"record_type": "browser_automation_mint_receipt", "target": target, "minted": len(cards),
           "appended": wrote["appended"], "on_file": wrote["on_file"], "grid_size": grid_size(),
           "axis_sizes": axis_sizes(), "quality_gate": qr, **BOUNDARY}
    out = resource("data") / "dev-intel" / "session_emulation" / "browser_automation_mint_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("target", "minted", "appended", "grid_size", "quality_gate")}, indent=2, sort_keys=True))
    print(f"\nstaged: {wrote['path']}\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mint", action="store_true")
    ap.add_argument("--target", type=int, default=20_000)
    ap.add_argument("--grid-size", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.grid_size:
        print(json.dumps({"grid_size": grid_size(), "axis_sizes": axis_sizes()}, indent=2))
        return 0
    if args.mint:
        return _mint(args.target)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
