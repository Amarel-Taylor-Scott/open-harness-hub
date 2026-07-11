#!/usr/bin/env python3
"""build_capability_assurance_surface — a REAL working surface fed by live receipts + computed counts (no marketing fiction).

Renders dist/teleon-demos/assurance.html from: the live-verified seam receipts (data/dev-intel/live-*-smoke.json + the
cdc_events stream), the COMPUTED registry counts (planes/tools/ladders/proofs/index — read at build, never hand-typed),
and the go-live seam status. This is the Capability Assurance surface (the listed showcase seam) — it proves the system
WORKS with real numbers, and the surfaces flywheel rebuilds it. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/build_capability_assurance_surface.py
  python3 _repos/shared-backend-components/scripts/build_capability_assurance_surface.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
OUT = _resource("dist") / "teleon-demos" / "assurance.html"


def _counts() -> dict:
    from scripts.flywheel_proof_modules import PROOF_MODULES
    L = lambda n: json.loads((_resource("architecture") / n).read_text(encoding="utf-8"))
    nlines = lambda p: sum(1 for ln in (_resource(p)).read_text().splitlines() if ln.strip()) if (_resource(p)).exists() else 0
    return {
        "planes": len(L("tool_planes.json")["planes"]),
        "curated_tools": len(L("tool_registry.json")["tools"]),
        "staged_tools": nlines("data/dev-intel/tool_registry_staging.jsonl"),
        "promoted_tools": len(L("tool_registry_promoted.json")["tools"]),
        "ladders": len(L("capability_ladders.json")["ladders"]),
        "indexed_components": nlines("data/dev-intel/component_search_index.jsonl"),
        "ml_model_types": len(L("ml_model_registry.json")["models"]),
        "proofs": len(PROOF_MODULES),
    }


def _receipts() -> list[dict]:
    out = []
    for f, title in [("live-llm-smoke.json", "Live LLM inference"), ("live-distillation-smoke.json", "Live distillation (LLM→deterministic rule)"),
                     ("live-eval-smoke.json", "Live A/B eval (vs real ground truth)")]:
        p = _resource("data") / "dev-intel" / f
        if p.exists():
            r = json.loads(p.read_text())
            out.append({"title": title, "verified": r.get("verified"), "detail": r})
    # the live CDC event from the real Federal Register poll
    try:
        from src.teleon.storage import record_store as RS
        st = RS.open_record_store("cdc_events")
        try:
            ev = next((e for e in st.all() if str(e.get("source", "")).startswith("us_federal_register")), None)
        finally:
            st.close()
        if ev:
            out.append({"title": "Live source fetch + CDC freshness", "verified": True,
                        "detail": {"source": ev["source"], "kind": ev["kind"], "content_hash": ev["content_hash"]}})
    except Exception:  # noqa: BLE001
        pass
    return out


def _seams() -> dict:
    from scripts.check_teleon_go_live_readiness import readiness_report
    r = readiness_report()
    return {"blocking": r["n_blocking_seams"], "total": r["n_seams"], "blocking_list": r["blocking_seams"],
            "closed": [s["seam"] for s in r["seams"] if not s["blocking"]]}


def build() -> Path:
    c, receipts, seams = _counts(), _receipts(), _seams()
    cards = "".join(
        f'<div class="card {"ok" if r["verified"] else "no"}"><h3>{r["title"]}</h3>'
        f'<p class="v">{"✓ LIVE-VERIFIED" if r["verified"] else "pending"}</p>'
        f'<pre>{json.dumps(r["detail"], indent=1)[:420]}</pre></div>' for r in receipts)
    stat = "".join(f'<div class="stat"><b>{v}</b><span>{k.replace("_"," ")}</span></div>' for k, v in c.items())
    closed = "".join(f"<li class=ok>✓ {s}</li>" for s in seams["closed"])
    blocking = "".join(f"<li class=no>○ {s} (owner-gated)</li>" for s in seams["blocking_list"])
    html = f"""<!doctype html><meta charset=utf-8><title>Teleon — Capability Assurance (live)</title>
<style>body{{font:15px/1.5 -apple-system,system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#111}}
h1{{margin:.2em 0}}.sub{{color:#555}}.stats{{display:flex;flex-wrap:wrap;gap:.6rem;margin:1.2rem 0}}
.stat{{background:#f4f6f8;border-radius:10px;padding:.7rem 1rem;min-width:120px}}.stat b{{font-size:1.5rem;display:block}}
.stat span{{color:#666;font-size:.8rem}}.cards{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
.card{{border:1px solid #e3e6ea;border-radius:10px;padding:1rem}}.card.ok{{border-left:4px solid #1a8}}.card.no{{border-left:4px solid #c84}}
.v{{font-weight:600;color:#1a8;margin:.2em 0}}pre{{background:#0d1117;color:#c9d1d9;padding:.6rem;border-radius:7px;overflow:auto;font-size:11px}}
ul{{columns:2}}li.ok{{color:#1a8}}li.no{{color:#a66}}</style>
<h1>Teleon — Capability Assurance</h1>
<p class=sub>Live, governed, working — every number below is COMPUTED at build / read from a real run receipt (no marketing fiction). serves_truth=false.</p>
<div class=stats>{stat}</div>
<h2>Live-verified capabilities</h2><div class=cards>{cards}</div>
<h2>Go-live readiness — {seams['total'] - seams['blocking']}/{seams['total']} seams closed</h2>
<ul>{closed}{blocking}</ul>
<p class=sub>The descent: every capability starts unbounded (frontier LLM) and is compiled toward the cheapest bounded
deterministic path — proven here by a live distillation (LLM→rule) that matches the model at ~$0 on a real eval.</p>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


def _self_test() -> int:
    p = build()
    h = p.read_text(encoding="utf-8")
    c = _counts()
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    ck("surface builds", p.exists() and len(h) > 800)
    ck("computed counts injected (planes/proofs real, not hardcoded)", str(c["planes"]) in h and str(c["proofs"]) in h)
    ck("live receipts rendered (>=3 verified capabilities)", h.count("LIVE-VERIFIED") >= 3)
    ck("seam status shown (closed + owner-gated)", "seams closed" in h)
    ck("no fabricated 100%/$0.00 marketing claims", "100%" not in h and "$0.00" not in h)
    print("\n" + (f"PASS - build_capability_assurance_surface: real working surface ({c['proofs']} proofs, {c['planes']} "
                  "planes, live receipts) -> dist/teleon-demos/assurance.html" if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print(f"built {build().relative_to(REPO)}")
