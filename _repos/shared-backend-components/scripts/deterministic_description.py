#!/usr/bin/env python3
"""deterministic_description — 0-token, deterministic, consistent primitive descriptions.

Owner (2026-07-11): "edges/planes where deterministic descriptions ... may help improve, save more tokens,
allow for faster." A description you can COMPUTE from the card's structure (name · capability class · typed
edges · verified recipe · dimensions) costs zero tokens, is byte-identical every run, and is instantly
searchable — versus paying an LLM per row (the description-backfill loop is ~66ms/row and the biggest tick
cost). This is the honest-ledger's robust win applied to the description plane: deterministic ⇒ free + fast +
consistent.

Emits THREE registers (the onion layers the search index already consumes), all deterministic:
  • plain      — a human sentence;
  • technical  — the typed contract + verified API symbols + provenance;
  • semantic   — a keyword bag (class · tags · edge components · recipe symbols · domain) for embedding recall.

An LLM is only ever needed for the *non-derivable* residue (nuance a template can't express); this covers the
derivable 100% at 0 tokens. Pure functions — no model, no network, no clock.

    python3 scripts/deterministic_description.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
TOKEN_COST = 0  # deterministic — no model call, ever


def _edge_words(edge: str) -> list[str]:
    """Split a typed edge 'HttpRequestSpec+RetryPolicy' into human words ['http request spec','retry policy']."""
    out = []
    for comp in str(edge).split("+"):
        words = re.sub(r"(?<!^)(?=[A-Z])", " ", comp).lower().strip()
        if words:
            out.append(words)
    return out


def _recipe_symbols(card: dict[str, Any]) -> list[str]:
    return sorted({s for r in card.get("usage_recipes", []) for s in r.get("symbols", []) if r.get("symbols")})


def describe_registers(card: dict[str, Any]) -> dict[str, str]:
    """The three deterministic description registers. Byte-identical for identical input."""
    name = str(card.get("package", {}).get("name") or card.get("title") or "capability")
    module = str(card.get("package", {}).get("module") or name)
    cls = card.get("capability_class") or (card.get("primitive_kind") or "").split(".")[-1] or "capability"
    in_words = _edge_words(card.get("input_edge", "")) or ["input"]
    out_words = _edge_words(card.get("output_edge", "")) or ["output"]
    tags = card.get("capability_tags") or []
    dims = card.get("dimensions") or {}
    syms = _recipe_symbols(card)
    recipes = card.get("usage_recipes", [])
    call = ""
    if recipes:
        call = recipes[0].get("snippet", "").splitlines()[-1].strip()

    plain = (f"{name} is a {cls.replace('_', ' ')} capability: it takes {', '.join(in_words)} and produces "
             f"{', '.join(out_words)}." + (f" Invoke with `{call}`." if call else ""))

    reg = dims.get("registry", card.get("package", {}).get("registry", ""))
    ver = dims.get("version", "")
    lic = card.get("package", {}).get("license", "")
    technical = (f"{module} [{reg}{(' ' + str(ver)) if ver else ''}]: {card.get('input_edge','')} -> "
                 f"{card.get('output_edge','')}."
                 + (f" {len(syms)} API-verified symbols: {', '.join(syms[:6])}." if syms else "")
                 + (f" License {lic}." if lic else "")
                 + (" Edge-only: code maintained upstream, not hosted." if card.get("has_code_body") is False else ""))

    semantic_terms = ([cls] + [str(t) for t in tags] + [w for e in (in_words + out_words) for w in e.split()]
                      + [s.split(".")[-1] for s in syms] + list(map(str, card.get("domains", []))))
    semantic = " ".join(dict.fromkeys(t for t in semantic_terms if t))  # dedupe, order-preserving

    return {"plain": plain, "technical": technical, "semantic": semantic}


def describe(card: dict[str, Any]) -> str:
    return describe_registers(card)["plain"]


def enrich_card(card: dict[str, Any]) -> dict[str, Any]:
    """Attach the deterministic registers to a card (0-token). Non-destructive: keeps any existing blackbox
    as `source_blackbox`, sets the plain register as the searchable description."""
    regs = describe_registers(card)
    out = dict(card)
    if card.get("blackbox") and "source_blackbox" not in out:
        out["source_blackbox"] = card["blackbox"]
    out["blackbox"] = regs["plain"]
    out["description_registers"] = regs
    out["description_token_cost"] = TOKEN_COST
    out["description_method"] = "deterministic_template"
    return out


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    card = {
        "title": "pydantic", "capability_class": "validate",
        "input_edge": "RawMapping+PydanticSchema", "output_edge": "ValidatedModel",
        "capability_tags": ["validation", "schema"], "domains": ["package_reuse"],
        "has_code_body": False,
        "package": {"name": "pydantic", "module": "pydantic", "registry": "pypi", "license": "MIT"},
        "dimensions": {"registry": "pypi", "version": "2.5"},
        "usage_recipes": [{"route": "model", "symbols": ["pydantic.BaseModel"],
                           "snippet": "import pydantic\nm = pydantic.BaseModel(...)"}],
    }
    regs = describe_registers(card)

    checks.append(("three registers produced (plain/technical/semantic)",
                   set(regs) == {"plain", "technical", "semantic"} and all(regs.values())))

    # deterministic — byte-identical
    checks.append(("byte-identical across runs (deterministic, 0-token)",
                   json.dumps(describe_registers(card), sort_keys=True)
                   == json.dumps(describe_registers(card), sort_keys=True)))

    # searchable — key terms present (edge words + class + name + recipe symbol)
    blob = " ".join(regs.values()).lower()
    checks.append(("searchable: contains class, edge words, name, and the verified recipe symbol",
                   "validate" in blob and "validated model" in blob and "pydantic" in blob
                   and "basemodel" in blob))

    # registers are DISTINCT (not the same string thrice)
    checks.append(("the three registers are distinct views",
                   len({regs["plain"], regs["technical"], regs["semantic"]}) == 3))

    # technical carries the typed contract + provenance
    checks.append(("technical register carries typed edges + verified symbol count + license",
                   "RawMapping+PydanticSchema -> ValidatedModel" in regs["technical"]
                   and "API-verified" in regs["technical"] and "MIT" in regs["technical"]))

    # enrich is non-destructive (keeps source blackbox)
    withbb = dict(card, blackbox="an old description")
    en = enrich_card(withbb)
    checks.append(("enrich non-destructive (source blackbox preserved) + 0-token method stamped",
                   en["source_blackbox"] == "an old description" and en["description_token_cost"] == 0
                   and en["blackbox"] == regs["plain"]))

    # works on a minimal/edge-case card without crashing (missing fields)
    minimal = describe_registers({"title": "x", "input_edge": "", "output_edge": ""})
    checks.append(("robust on a minimal card (empty edges → 'input'/'output' defaults)",
                   "input" in minimal["plain"] and "output" in minimal["plain"]))

    # MUTATION-style: a DIFFERENT card yields a DIFFERENT description (not a constant)
    other = describe_registers(dict(card, title="httpx", capability_class="http_client",
                                    input_edge="HttpRequestSpec", output_edge="JsonBytes",
                                    package={"name": "httpx", "module": "httpx", "registry": "pypi"}))
    checks.append(("distinct inputs → distinct descriptions (not a constant template)",
                   other["plain"] != regs["plain"]))

    ok = all(v for _, v in checks)
    print("deterministic_description — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  3 registers/card at {TOKEN_COST} tokens. plain: {regs['plain'][:90]}…")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
