#!/usr/bin/env python3
"""browser_control.self_test — the OFFLINE, deterministic, MUTATION-GATED proof for the adapter package.

No network, no browser, no keys. It drives the FakeAdapter end-to-end and asserts the load-bearing contract:

  * tabs — open / list / focus / close, with the last tab protected;
  * stable state hashes — the same page yields the same sha256 tab-state hash across calls (determinism);
  * evidence — every command emits a browser_action_receipt; a state-changing one carries before != after hashes,
    and one real receipt VALIDATES against schemas/browser_action_receipt.schema.json;
  * the side-effect calculus — an act is REFUSED read-only by default; with side effects enabled, write_possible
    executes but >= 'write' requires confirmation (never auto-executes);
  * unsupported = structured, non-raising — a capability an adapter cannot back returns {"supported": False, ...}
    (proven on the bare BrowserAdapter and on the http adapter's screenshot) and NEVER raises;
  * secret hygiene — a secret-shaped token in the fixture never survives into any receipt / extract / report;
  * single-source drift gates — the receipt schema's side_effect_level enum == SIDE_EFFECT_LEVELS, and the
    capability schema's 17 flags == CAPABILITY_KEYS;
  * determinism — building the session report twice from a fresh clock is byte-identical.

Mutation-gated: each check asserts a specific behavior, so a real injected defect (redaction disabled, the gate
auto-executing a write, an adapter raising instead of returning unsupported, a schema drift) flips a check to [XX].

    python3 browser_control/self_test.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, resource  # noqa: E402

_install()

import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

from browser_control import (  # noqa: E402
    ADAPTERS,
    CAPABILITY_KEYS,
    SIDE_EFFECT_LEVELS,
    BrowserAdapter,
    FakeAdapter,
    HttpScrapeAdapter,
    make_counter_clock,
    safety,
)
from browser_control.fake_adapter import FIXTURE_CHILD, FIXTURE_HOME, FIXTURE_POPUP  # noqa: E402

_SECRET_MARKERS = ("sk-live-SHOULDNOTLEAK", "sk-live-SECRETVALUE", "Bearer abcdef", "supersecretvalue")


def _no_secret(*objs: Any) -> bool:
    blob = json.dumps(objs, default=str)
    return not any(m in blob for m in _SECRET_MARKERS)


def _fake_report_scenario(clock: Callable[[], float]) -> dict[str, Any]:
    """A fixed multi-tab scenario used for the determinism check (fresh clock -> byte-identical output)."""
    fa = FakeAdapter(clock=clock)
    fa.start_session()
    fa.navigate(FIXTURE_HOME)                         # tab0 -> HOME (links to CHILD + cross-origin POPUP)
    t1 = fa.open_tab(FIXTURE_CHILD)["tab_id"]
    fa.focus_tab(t1)
    fa.navigate(FIXTURE_CHILD)                        # tab1 -> CHILD
    t2 = fa.open_tab(FIXTURE_POPUP)["tab_id"]
    fa.focus_tab(t2)
    fa.navigate(FIXTURE_POPUP)                        # tab2 -> POPUP (cross-origin)
    return fa.build_session_report()


def self_test() -> int:  # noqa: C901 — one linear proof; readability beats decomposition here
    checks: list[tuple[str, bool]] = []

    # ── FakeAdapter: session + tabs + stable hashes + before/after receipt ─────────────────────────────────────
    fa = FakeAdapter(clock=make_counter_clock())
    started = fa.start_session()
    checks.append(("FakeAdapter start_session ok + session_id + candidate-only",
                   started.get("supported") is True and started["session_id"].startswith("bsession-")
                   and started["serves_truth"] is False))

    r_home = fa.navigate(FIXTURE_HOME)
    r_snap = fa.snapshot_tab()                         # re-capture the same page -> SAME hash
    checks.append(("stable tab-state hash: same page -> identical sha256 hash",
                   r_home["state_hash"] == r_snap["state_hash"] and r_home["state_hash"].startswith("sha256:")))

    r_child = fa.navigate(FIXTURE_CHILD)               # same tab, different page -> before != after
    rc = r_child["receipt"]
    checks.append(("action receipt carries before/after hashes (before != after on a page change)",
                   rc["before_state_hash"] == r_home["state_hash"]
                   and rc["after_state_hash"] != rc["before_state_hash"]
                   and rc["after_state_hash"] is not None))

    lt0 = fa.list_tabs()
    tid1 = fa.open_tab(FIXTURE_POPUP)["tab_id"]
    lt1 = fa.list_tabs()
    foc = fa.focus_tab(tid1)
    closed = fa.close_tab(tid1)
    closed_last = fa.close_tab("tab0")                 # only one tab left -> protected
    checks.append(("tabs: open/list/focus/close work; last tab protected",
                   len(lt0["tabs"]) == 1 and len(lt1["tabs"]) == 2 and foc["focused"] is True
                   and closed["closed"] is True and closed_last["closed"] is False))

    # ── side-effect calculus ───────────────────────────────────────────────────────────────────────────────────
    fa_ro = FakeAdapter(clock=make_counter_clock(), allow_side_effects=False)
    fa_ro.start_session()
    fa_ro.navigate(FIXTURE_HOME)
    click_ro = fa_ro.click_ref("button.submit-claim", side_effect="write")
    checks.append(("act REFUSED read-only by default (never performs the side effect)",
                   click_ro["executed"] is False and click_ro["requires_confirmation"] is True
                   and click_ro["receipt"]["verifier_result"] == "refused_read_only"))

    fa_se = FakeAdapter(clock=make_counter_clock(), allow_side_effects=True)
    fa_se.start_session()
    fa_se.navigate(FIXTURE_HOME)
    click_wp = fa_se.click_ref("button.next", side_effect="write_possible")   # < write -> executes
    click_w = fa_se.click_ref("button.pay", side_effect="write")              # >= write -> needs confirmation
    fill_secret = fa_se.fill_ref("input.key", "sk-live-SECRETVALUE1234567", side_effect="read")
    checks.append(("side-effect calculus: write_possible executes, write+ needs confirmation",
                   click_wp["executed"] is True and click_w["executed"] is False
                   and click_w["requires_confirmation"] is True))
    checks.append(("filled value redacted in the receipt (never log a secret)",
                   fill_secret["executed"] is True and _no_secret(fill_secret)))

    # ── unsupported = structured + non-raising (bare adapter and a real adapter's missing capability) ──────────
    raised = False
    try:
        u_base = BrowserAdapter().navigate("https://example.com")
        u_base2 = BrowserAdapter().capture_screenshot()
    except Exception:  # noqa: BLE001
        raised = True
        u_base = u_base2 = {}
    checks.append(("bare BrowserAdapter returns structured unsupported (never raises)",
                   raised is False and u_base.get("supported") is False and "reason" in u_base
                   and u_base2.get("supported") is False))

    http = HttpScrapeAdapter(fetch=lambda u: "<html><body><a href='/a'>a</a></body></html>"
                             if u == "https://static.example/" else None, clock=make_counter_clock())
    http.start_session()
    http.navigate("https://static.example/")
    u_shot = http.capture_screenshot()
    u_net = http.capture_network()
    txt_http = http.extract_text()
    checks.append(("http adapter: screenshot/network UNSUPPORTED (structured) but text extraction WORKS",
                   u_shot.get("supported") is False and "reason" in u_shot
                   and u_net.get("supported") is False and txt_http.get("supported") is True))

    # ── extraction + read-only surfaces on the fixture (secrets redacted end-to-end) ──────────────────────────
    fa2 = FakeAdapter(clock=make_counter_clock())
    fa2.start_session()
    fa2.navigate(FIXTURE_HOME)
    txt = fa2.extract_text()
    dom = fa2.extract_dom()
    links = fa2.extract_links()
    forms = fa2.extract_forms()
    tables = fa2.extract_tables()
    shot = fa2.capture_screenshot()
    net = fa2.capture_network()
    dl = fa2.download_artifacts()
    ws_text = fa2.wait_for_state(contains="Eligibility")
    ws_url = fa2.wait_for_state(url_is=FIXTURE_HOME)
    ws_state = fa2.wait_for_state()

    checks.append(("readable text extracted + secret redacted (>=1)",
                   txt["chars"] > 0 and txt["secrets_redacted"] >= 1 and _no_secret(txt)))
    checks.append(("DOM digest + bounded redacted DOM (no raw secret survives)",
                   dom["dom_hash"].startswith("sha256:") and _no_secret(dom)))
    checks.append(("links extracted (child + cross-origin popup + openapi + pdf)",
                   any(FIXTURE_CHILD == u for u in links["links"])
                   and any(FIXTURE_POPUP == u for u in links["links"])
                   and any("openapi.json" in u for u in links["links"])
                   and any(u.endswith(".pdf") for u in links["links"])))
    checks.append(("forms extracted (POST claim + GET search + loose password input)", forms["n_forms"] >= 2))
    checks.append(("tables extracted via the stdlib table extractor (rows present)",
                   tables["n_tables"] >= 1 and any("99213" in c for t in tables["tables"] for r in t["rows"]
                                                   for c in r)))
    checks.append(("screenshot captured (digest, no bytes stored)",
                   shot.get("supported") is True and shot["screenshot_hash"].startswith("sha256:")))
    checks.append(("network surfaces captured (openapi ref + simulated xhr)",
                   net.get("supported") is True and any(a["kind"] == "openapi" for a in net["network_artifacts"])
                   and any(a["kind"] == "xhr" for a in net["network_artifacts"])))
    checks.append(("downloadable doc listed (never fetched)", dl["n_downloads"] >= 1
                   and any(d["ext"] == "pdf" for d in dl["downloads"])))
    checks.append(("read-only verifiers pass (text / url / state)",
                   ws_text["passed"] is True and ws_url["passed"] is True and ws_state["passed"] is True))

    # ── tab graph + session report (candidate-only) ───────────────────────────────────────────────────────────
    fa3 = FakeAdapter(clock=make_counter_clock())
    fa3.start_session()
    fa3.navigate(FIXTURE_HOME)
    tchild = fa3.open_tab(FIXTURE_CHILD)["tab_id"]
    fa3.focus_tab(tchild)
    fa3.navigate(FIXTURE_CHILD)
    graph = fa3.build_tab_graph()
    report = fa3.build_session_report()
    checks.append(("tab graph built (nodes present)",
                   graph.get("supported") is True and len(graph["tab_graph"].get("nodes", [])) >= 1))
    checks.append(("session report built, candidate-only + secret-free",
                   report.get("supported") is True and report["report"]["serves_truth"] is False
                   and report["report"]["candidate"] is True and _no_secret(report)))

    # ── receipt schema validation + single-source drift gates ─────────────────────────────────────────────────
    try:
        import jsonschema
        rec_schema = json.loads(resource("schemas/browser_action_receipt.schema.json").read_text())
        jsonschema.validate(shot["receipt"], rec_schema)           # a read-only receipt
        jsonschema.validate(click_w["receipt"], rec_schema)        # a gated-write receipt
        jsonschema.validate(click_ro["receipt"], rec_schema)       # a refused receipt
        receipt_valid = True
    except Exception as exc:  # noqa: BLE001
        receipt_valid = False
        print(f"  (receipt schema validation error: {type(exc).__name__}: {exc})")
    checks.append(("emitted receipts VALIDATE against browser_action_receipt.schema.json", receipt_valid))

    rec_schema = json.loads(resource("schemas/browser_action_receipt.schema.json").read_text())
    enum = rec_schema["properties"]["side_effect_level"]["enum"]
    checks.append(("drift gate: receipt schema side_effect_level enum == SIDE_EFFECT_LEVELS",
                   list(enum) == list(SIDE_EFFECT_LEVELS)))

    cap_schema = json.loads(resource("schemas/browser_control_capability.schema.json").read_text())
    cap_props = cap_schema["properties"]["capabilities"]["properties"]
    checks.append(("drift gate: capability schema's 17 flags == CAPABILITY_KEYS",
                   set(cap_props) == set(CAPABILITY_KEYS) and len(cap_props) == 17 == len(CAPABILITY_KEYS)))

    # capabilities() advertises the full/partial profiles
    caps_fake = FakeAdapter().capabilities()
    caps_http = HttpScrapeAdapter().capabilities()
    checks.append(("capabilities(): fake backs all 17; http drops screenshot/network/click/fill",
                   caps_fake["n_supported"] == 17 and caps_http["capabilities"]["screenshot"] is False
                   and caps_http["capabilities"]["network_capture"] is False
                   and caps_http["capabilities"]["extract_text"] is True))

    # ── safety module (delegates to the harness; the one place callers read the policy) ───────────────────────
    g_ro = safety.side_effect_confirmation_gate("read_only", allow_side_effects=False)
    g_pend = safety.side_effect_confirmation_gate("write", allow_side_effects=True, confirmed=False)
    g_conf = safety.side_effect_confirmation_gate("write", allow_side_effects=True, confirmed=True)
    g_read = safety.side_effect_confirmation_gate("read", allow_side_effects=True)
    g_bad = safety.side_effect_confirmation_gate("bogus", allow_side_effects=True)
    checks.append(("safety.side_effect_confirmation_gate: refuse/pending/confirm/execute/invalid",
                   g_ro["execute"] is False and g_pend["execute"] is False and g_pend["requires_confirmation"] is True
                   and g_conf["execute"] is True and g_read["execute"] is True and g_bad["verdict"] == "invalid_level"))

    clean, n_red = safety.redact_fields({"a": "token=supersecretvalue1234", "b": {"k": "sk-live-ABCDEFGH12345"}})
    checks.append(("safety.redact_fields redacts nested secrets", n_red >= 2 and _no_secret(clean)))
    checks.append(("safety.robots_gate honors Allow/Disallow",
                   safety.robots_gate("https://x.example/p", fetch=lambda u: "User-agent: *\nAllow: /\n") is True
                   and safety.robots_gate("https://x.example/p", fetch=lambda u: "User-agent: *\nDisallow: /\n")
                   is False))

    # ── determinism: build the report twice from a fresh clock -> byte-identical ──────────────────────────────
    rep_a = _fake_report_scenario(make_counter_clock())
    rep_b = _fake_report_scenario(make_counter_clock())
    det = json.dumps(rep_a["report"], sort_keys=True) == json.dumps(rep_b["report"], sort_keys=True)
    checks.append(("determinism: session report is byte-identical across two fresh runs", det))

    # ── report ────────────────────────────────────────────────────────────────────────────────────────────────
    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    print(("PASS" if ok else "FAIL") + f" - browser_control: driver-neutral adapter package "
          f"({len(ADAPTERS)} adapters: {', '.join(sorted(ADAPTERS))}) wrapping the read-only harness; "
          f"FakeAdapter offline proof {sum(v for _, v in checks)}/{len(checks)} checks "
          "(tabs/state-hash/receipts/side-effect-gate/redaction/schema/determinism), serves_truth=false.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv or not argv:
        return self_test()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
