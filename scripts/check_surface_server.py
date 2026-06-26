#!/usr/bin/env python3
"""scripts.check_surface_server — proof for the ONE standardized, config-driven surface server.

Asserts the linchpin guarantees of scripts/surface_server.py without opening a real socket (drives the route
handler + render functions directly, deterministically):
  * all 5 surface ids render a home page at status 200;
  * every surface embeds the SAME canonical CSS — byte-identical except the single per-surface accent (the
    standardization point) — with the Inter font-family + the canonical token block present;
  * each home's nav links all 5 surfaces;
  * /demo renders for teleon/baltor/aidevobserver/open-star-hubs with the governed BYO copy ("never stored");
  * POST /run with no key returns a governed honest result, and a real key is redacted + never leaked;
  * open-star-hubs /browse renders facet groups with computed counts (> 0); other surfaces 404 on /browse;
  * ai-done-right home is the hub (links the other 4 as portfolio cards);
  * serves_truth = false on every surface.
Prints PASS/FAIL with a computed assertion count; exits nonzero on failure. serves_truth=false.

  python3 scripts/check_surface_server.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._surface_accents import accent as _acc  # noqa: E402
from scripts import surface_server as S  # noqa: E402
from src.teleon.registry.browse import FACET_DIMS, browse  # noqa: E402

_N = 0


def ck(cond: bool, msg: str) -> None:
    global _N
    _N += 1
    if not cond:
        raise AssertionError(msg)


def _checks() -> int:
    ids = S.surface_ids()
    ck(set(ids) == {"ai-done-right", "teleon", "aidevobserver", "baltor", "open-star-hubs"},
       f"the 5 canonical surface ids come from config: {ids}")
    brands = [S.pillar(i)["brand"] for i in ids]

    # 1) every surface renders a home page at status 200
    homes = {}
    for sid in ids:
        code, ctype, body = S.handle_get(sid, "/")
        ck(code == 200 and body.lower().startswith("<!doctype"), f"{sid} home is a 200 HTML page")
        ck(ctype == S.HTML, f"{sid} home content-type")
        homes[sid] = body

    # 2) the SAME canonical CSS on every surface — byte-identical except the accent value (standardization)
    css = {sid: S.surface_css(_acc(sid)) for sid in ids}
    stripped = {sid: c.replace(_acc(sid), "__ACCENT__") for sid, c in css.items()}
    ck(len({v for v in stripped.values()}) == 1, "every surface's CSS is byte-identical once the accent is removed")
    ck(next(iter(stripped.values())) == S._CSS_TEMPLATE, "the stripped CSS equals the single canonical template")
    for sid in ids:
        ck(css[sid].count(_acc(sid)) == 1, f"{sid}: the accent appears exactly once (only difference)")
        ck(_acc(sid) in css[sid] and "var(--accent)" in css[sid], f"{sid}: accent token defined + consumed via var()")
    ck(len({_acc(i) for i in ids}) == 5, "all five accents are distinct")
    canon = next(iter(css.values()))
    ck('font-family:"Inter"' in canon, "canonical CSS loads the Inter font-family")
    ck("--bg:#faf7f0" in canon and "--accent-ink:#ffffff" in canon and "--border:#e7e0d2" in canon,
       "canonical token block present (No-Magic-Values from oh-tokens)")
    # the canonical CSS is actually embedded in every rendered surface (not just produced in isolation)
    for sid in ids:
        ck(S.surface_css(_acc(sid)) in homes[sid], f"{sid} home embeds the canonical stylesheet")
        ck('href="https://fonts.googleapis.com/css2?family=Inter' in homes[sid], f"{sid} loads Inter from Google Fonts")

    # 3) each surface's home nav links all 5 surfaces
    for sid in ids:
        ck('<nav class="nav"' in homes[sid], f"{sid} home has the sticky nav")
        for b in brands:
            ck(b in homes[sid], f"{sid} nav links surface '{b}'")

    # 4) /demo renders for the 4 product surfaces with the governed BYO copy
    for sid in ("teleon", "baltor", "aidevobserver", "open-star-hubs"):
        code, _, body = S.handle_get(sid, "/demo")
        ck(code == 200 and body.lower().startswith("<!doctype"), f"{sid} /demo is a 200 page")
        ck("never stored" in body, f"{sid} /demo carries the governed copy 'never stored'")
        ck('id="prompt"' in body and "Run" in body, f"{sid} /demo has a prompt + run button")
        needs = bool(S.DEMOS[sid]["needs_key"])
        ck(('id="key"' in body) == needs, f"{sid} /demo shows a key field iff the demo needs one ({needs})")
    # aidevobserver needs no key
    ck(S.DEMOS["aidevobserver"]["needs_key"] is False, "aidevobserver demo needs no key (session-review)")

    # 5) POST /run governance: no key → honest needs_key; a real key → redacted + NEVER leaked
    no_key = S._run_request({"demo": "teleon", "inputs": {"prompt": "x"}})
    ck(no_key.get("status") == "needs_key" and no_key.get("ok") is False, "POST /run with no key is honest (needs_key)")
    ck(no_key.get("serves_truth") is not True, "needs_key result does not serve truth")
    leaked = "sk-secret-LEAK1234"
    with_key = S._run_request({"demo": "teleon", "byo_key": leaked, "inputs": {"prompt": "x"}})
    ck(leaked not in json.dumps(with_key), "the raw BYO key NEVER appears in the /run result")
    ck(with_key.get("key_status") == "sk-…1234", f"the key is returned only redacted: {with_key.get('key_status')}")
    ck(with_key.get("serves_truth") is False, "BYO /run result serves_truth=false")

    # 6) open-star-hubs /browse renders facet groups with computed counts (> 0); other surfaces 404
    code, _, brz = S.handle_get("open-star-hubs", "/browse")
    ck(code == 200 and brz.lower().startswith("<!doctype"), "open-star-hubs /browse is a 200 page")
    live = browse("", {})
    for dim in FACET_DIMS:
        ck(f"<h3>{dim.capitalize()}</h3>" in brz, f"/browse renders the '{dim}' facet group")
    top_cat, top_n = next(iter(live["facets"]["category"].items()))
    ck(top_n > 0 and f'<span class="ct">{top_n}</span>' in brz, f"/browse shows a computed count (> 0): {top_cat}={top_n}")
    ck(live["items"][0]["id"] in brz, "/browse renders real record cards")
    ck("serves_truth=false" in brz.lower().replace(" ", "") or "serves_truth = false" in brz, "/browse declares no-truth")
    for sid in ids:
        if sid != "open-star-hubs":
            code2, _, _ = S.handle_get(sid, "/browse")
            ck(code2 == 404, f"{sid} (not the store) 404s on /browse")
    # a facet filter through the handler narrows the set
    code3, _, narrowed_html = S.handle_get("open-star-hubs", "/browse", "kind=discovery")
    ck(code3 == 200 and 'kind: discovery' in narrowed_html, "/browse applies a facet filter from the query string")

    # 7) ai-done-right home is the hub: portfolio cards linking the other 4
    hub = homes["ai-done-right"]
    ck(hub.count('surface-card"') >= 4, "the hub renders a portfolio card per other surface")
    for sid in ids:
        if sid != "ai-done-right":
            ck(S.pillar(sid)["brand"] in hub, f"hub links the '{S.pillar(sid)['brand']}' surface")

    # 8) serves_truth = false everywhere (home · demo · browse)
    for sid in ids:
        ck("serves_truth = false" in homes[sid], f"{sid} home declares serves_truth = false")
    for sid in ("teleon", "baltor", "aidevobserver", "open-star-hubs"):
        _, _, dpage = S.handle_get(sid, "/demo")
        ck("serves_truth = false" in dpage, f"{sid} /demo declares serves_truth = false")

    # favicon: 204, no console 404
    for sid in ids:
        fcode, _, _ = S.handle_get(sid, "/favicon.ico")
        ck(fcode == 204, f"{sid} serves a 204 favicon (no console 404)")

    # invalid id → usage error (exit 2), valid id accepted (suppress its usage print for clean proof output)
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        bad = S.main(["not-a-surface"])
    ck(bad == 2, "an invalid surface id is a usage error")

    return _N


def self_test() -> int:
    try:
        n = _checks()
    except AssertionError as e:
        print(f"check_surface_server: FAIL — {e}")
        return 1
    print(f"check_surface_server: PASS ({n} assertions — 5 surfaces from ONE template, byte-identical CSS except "
          f"accent, nav links all 5, governed BYO /demo + /run, faceted /browse with computed counts, hub portfolio "
          f"index, serves_truth=false)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: check_surface_server.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
