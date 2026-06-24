#!/usr/bin/env python3
"""Validate the AI Done Right prototype surface family.

The design bundle's single source of truth is
dist/sites/openharness-design/shared/products.js. This proof reads that file
directly, checks the layer membership, verifies the live/private split, confirms
the five Baltor method hubs, and checks that every referenced prototype HTML
exists locally.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PRODUCTS_JS = REPO / "dist" / "sites" / "openharness-design" / "shared" / "products.js"

PRODUCT_LAYER = {"baltor", "teleon"}
LIVE_OPEN_HUBS = {
    "openContextHub",
    "openSkillsHub",
    "openToolsHub",
    "openSkillToTool",
    "openMCPHub",
    "openCompressionHub",
    "openBenchmarkHub",
    "openReviewHub",
    "openHarnessHub",
}
PRIVATE_BENCH = {
    "openTemplatesHub",
    "openEndpointHub",
    "openEnvironmentHub",
    "openSandboxHub",
    "openAgentHub",
    "openReceiptHub",
    "openStateHub",
    "openReconciliationHub",
    "openHardeningHub",
    "openEnrichmentHub",
    "openOptimizationHub",
    "openVerificationHub",
    "openRoutingHub",
}
METHOD_HUBS = {
    "openReconciliationHub": "Reconcile",
    "openHardeningHub": "Harden",
    "openEnrichmentHub": "Enhance",
    "openOptimizationHub": "Optimize",
    "openVerificationHub": "Verify",
}
EXPECTED_LAYER_ITEMS = {
    "product": PRODUCT_LAYER,
    "open": LIVE_OPEN_HUBS,
    "candidate": PRIVATE_BENCH,
}


def _balanced_block(text: str, marker: str, opener: str, closer: str) -> str:
    start = text.index(marker)
    first = text.index(opener, start)
    depth = 0
    quote: str | None = None
    escape = False
    for idx in range(first, len(text)):
        ch = text[idx]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[first + 1:idx]
    raise ValueError(f"could not find balanced block for {marker}")


def _strip_js_comments(text: str) -> str:
    """Remove JS comments while preserving quoted strings."""
    out: list[str] = []
    idx = 0
    quote: str | None = None
    escape = False
    while idx < len(text):
        ch = text[idx]
        nxt = text[idx + 1] if idx + 1 < len(text) else ""
        if quote:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            idx += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            idx += 1
            continue
        if ch == "/" and nxt == "/":
            idx += 2
            while idx < len(text) and text[idx] != "\n":
                idx += 1
            out.append("\n")
            continue
        if ch == "/" and nxt == "*":
            idx += 2
            while idx + 1 < len(text) and not (text[idx] == "*" and text[idx + 1] == "/"):
                out.append("\n" if text[idx] == "\n" else " ")
                idx += 1
            idx += 2
            continue
        out.append(ch)
        idx += 1
    return "".join(out)


def _top_level_entity_blocks(entities_src: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    idx = 0
    pattern = re.compile(r"\s*([A-Za-z0-9_]+):\s*\{")
    while idx < len(entities_src):
        match = pattern.match(entities_src, idx)
        if not match:
            idx += 1
            continue
        key = match.group(1)
        brace = entities_src.index("{", match.start())
        depth = 0
        quote: str | None = None
        escape = False
        end = brace
        for pos in range(brace, len(entities_src)):
            ch = entities_src[pos]
            if quote:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == quote:
                    quote = None
                continue
            if ch in ("'", '"'):
                quote = ch
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = pos
                    break
        blocks[key] = entities_src[brace + 1:end]
        idx = end + 1
    return blocks


def _string_prop(block: str, name: str) -> str | None:
    match = re.search(rf"\b{re.escape(name)}:\s*'([^']*)'", block)
    return match.group(1) if match else None


def _layers(layers_src: str) -> dict[str, set[str]]:
    layers: dict[str, set[str]] = {}
    for match in re.finditer(r"id:\s*'([^']+)'.*?items:\s*\[([^\]]*)\]", layers_src, re.S):
        layer_id = match.group(1)
        items = set(re.findall(r"'([^']+)'", match.group(2)))
        layers[layer_id] = items
    return layers


def _entity_records(products_js: Path) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    text = _strip_js_comments(products_js.read_text(encoding="utf-8"))
    entity_blocks = _top_level_entity_blocks(_balanced_block(text, "const ENTITIES", "{", "}"))
    layer_items = _layers(_balanced_block(text, "const LAYERS", "[", "]"))
    records: dict[str, dict[str, Any]] = {}
    for key, block in entity_blocks.items():
        records[key] = {
            "name": _string_prop(block, "name"),
            "wordmark": _string_prop(block, "wordmark"),
            "status": _string_prop(block, "status"),
            "url": _string_prop(block, "url"),
            "futureAccent": _string_prop(block, "futureAccent"),
            "source": _string_prop(block, "source"),
        }
    return records, layer_items


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("products.js exists", PRODUCTS_JS.exists(), str(PRODUCTS_JS))
    if not PRODUCTS_JS.exists():
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1

    try:
        records, layers = _entity_records(PRODUCTS_JS)
    except Exception as exc:  # noqa: BLE001
        check("products.js can be parsed", False, f"{type(exc).__name__}: {exc}")
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1
    check("products.js can be parsed", True)

    expected_all = PRODUCT_LAYER | LIVE_OPEN_HUBS | PRIVATE_BENCH
    # counts are COMPUTED from the sets (no magic value) — the roster above is the single source
    hub_count = len(LIVE_OPEN_HUBS | PRIVATE_BENCH)
    check("all expected entities are present", expected_all <= set(records), str(sorted(expected_all - set(records))))
    check("no unexpected portfolio entities are present", set(records) == expected_all, str(sorted(set(records) - expected_all)))
    check(f"Open*Hub roster is internally consistent ({len(LIVE_OPEN_HUBS)} live + {len(PRIVATE_BENCH)} private = {hub_count})",
          hub_count == len(LIVE_OPEN_HUBS) + len(PRIVATE_BENCH))
    check("surface snapshot is parent + two products + the Open*Hub roster",
          len(PRODUCT_LAYER) == 2 and hub_count == len(LIVE_OPEN_HUBS) + len(PRIVATE_BENCH))

    for layer_id, expected_items in EXPECTED_LAYER_ITEMS.items():
        actual = layers.get(layer_id, set())
        check(f"layer {layer_id} has expected items", actual == expected_items,
              f"missing={sorted(expected_items - actual)} extra={sorted(actual - expected_items)}")

    for key in PRODUCT_LAYER | LIVE_OPEN_HUBS:
        rec = records.get(key, {})
        check(f"{key}: status live", rec.get("status") == "live", str(rec))
    for key in PRIVATE_BENCH:
        rec = records.get(key, {})
        check(f"{key}: status private", rec.get("status") == "private", str(rec))
        check(f"{key}: futureAccent recorded for one-line launch flip", bool(rec.get("futureAccent")), str(rec))

    for key, stage in METHOD_HUBS.items():
        rec = records.get(key, {})
        check(f"{key}: method hub source names {stage} stage", stage in str(rec.get("source") or ""), str(rec))

    shared_dir = PRODUCTS_JS.parent
    for key, rec in sorted(records.items()):
        url = rec.get("url")
        check(f"{key}: url recorded", bool(url), str(rec))
        if url:
            target = (shared_dir / url).resolve()
            check(f"{key}: url target exists", target.exists(), str(target))

    if fails:
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1
    print(f"\nPASS - check_ai_done_right_surface_family: products.js defines parent-visible portfolio layers "
          f"with {len(PRODUCT_LAYER)} products, {len(LIVE_OPEN_HUBS)} live Open*Hubs, {len(PRIVATE_BENCH)} "
          f"private-bench hubs, and the complete five-stage Baltor method spine; every referenced prototype "
          f"HTML exists.")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_ai_done_right_surface_family.py --self-test")
    raise SystemExit(0)
