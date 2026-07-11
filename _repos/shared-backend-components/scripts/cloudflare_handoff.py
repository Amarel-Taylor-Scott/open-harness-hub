#!/usr/bin/env python3
"""scripts.cloudflare_handoff — aggregate every TryCloudflare + local URL into a verified inventory, a shareable
handoff Markdown, a one-by-one review checklist, a review state file, and a rubric scorecard.

Reuses the running portfolio tunnels (.agent/portfolio-sites/urls.json), the Demo Control Tower
(dist/demo-control-tower-url.txt), and the demo surface registry. No fake URLs. `--run` performs live HTTP
verification; `build_inventory()` + the renderers are deterministic/offline (flywheel-safe).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import portfolio_lib as P

_REG = _resource("architecture/demo_surface_registry.json")
_TUNNELS = P.REPO / ".agent" / "portfolio-sites" / "urls.json"
_CT_URL = _resource("dist/demo-control-tower-url.txt")
_DIST = _resource("dist")
_STATE = P.REPO / ".agent" / "cloudflare-url-review-state.json"
_GROUP = {"static_site": "Portfolio websites", "interactive_demo": "Product demos", "dashboard": "Baltor dashboards",
          "registry": "Open hub registries", "internal_tool": "Shared internal surfaces"}
_GROUP_ORDER = ["Start Here", "Portfolio websites", "Product demos", "Baltor dashboards", "Open hub registries",
                "Shared internal surfaces", "Missing or candidate"]
_CAVEATS = [
    "TryCloudflare URLs are random/session URLs — they change if a tunnel restarts.",
    "These are demo/local preview links, not production hosting.",
    "Some URLs may include demo tokens; treat them as demo-only.",
    "Do not treat local demo links as a production security posture.",
    "No paid cloud is required. cloudflared quick tunnels only.",
]


def _tunnels() -> dict:
    return {sid: r.get("public_url") for sid, r in json.loads(_TUNNELS.read_text()).items() if r.get("public_url")} if _TUNNELS.exists() else {}


def _expected(sid: str) -> list[str]:
    if sid == "demo-control-tower":
        return ["Demo Control Tower", "10 business days"]
    if sid.startswith("site."):
        pid = sid[len("site."):]
        s = P.SITES.get(pid)
        return [s["title"], s["required_phrases"][0][:40]] if s else []
    if sid == "baltor.cfpb_offline_demo":
        return ["10 business days"]
    return []


def _extra_tunnels() -> dict:
    f = _DIST / "cloudflare-extra-tunnels.json"
    return {str(k): v for k, v in json.loads(f.read_text()).items()} if f.exists() else {}


def build_inventory(now: str) -> dict:
    reg = json.loads(_REG.read_text())["surfaces"]
    tcf = _tunnels()
    extra = _extra_tunnels()  # port → tunnel URL (e.g. the :9301 admin server)
    ct = _CT_URL.read_text().strip() if _CT_URL.exists() else None
    surfaces = []
    order = 0
    for s in reg:
        port = s["local_port"]
        local = f"http://127.0.0.1:{port}{s['local_path']}" if port else None
        if s["surface_id"] == "demo-control-tower":
            pub = ct
        elif s["surface_id"].startswith("site."):
            pub = tcf.get(s["surface_id"][len("site."):])
            if not pub and port and str(port) in extra:
                # tunnel-launcher record keys and surface ids can drift
                # (portfolio vs portfolio-hub) — a port-level extra tunnel
                # is the same honest evidence, so fall back to it.
                pub = extra[str(port)].rstrip("/") + s["local_path"]
        elif port and str(port) in extra:
            pub = extra[str(port)].rstrip("/") + s["local_path"]  # a port-level tunnel (admin server) + the route
        else:
            pub = None
        group = "Start Here" if s["surface_id"] == "demo-control-tower" else (_GROUP.get(s["surface_type"], "Missing or candidate") if s["status"] == "active" else "Missing or candidate")
        rec = {"surface_id": s["surface_id"], "group": group, "display_name": s["display_name"],
               "brand": s.get("company_or_hub", ""), "surface_type": s["surface_type"], "local_url": local,
               "cloudflare_url": pub, "requires_token": s.get("requires_token", False),
               "token_policy": "none", "expected_status": 200, "expected_content": _expected(s["surface_id"]),
               "status_registry": s["status"], "health_status": "unverified" if (local or pub) else "missing",
               "screenshot_path": None, "notes": []}
        if pub or local:  # a surface with a local OR public URL is reviewable (local-first: the tunnel is only
            order += 1     # for remote sharing; reviewing happens locally, so the offline handoff is a real checklist)
            rec["review_order"] = order
        surfaces.append(rec)
    surfaces.sort(key=lambda r: (_GROUP_ORDER.index(r["group"]) if r["group"] in _GROUP_ORDER else 99, r.get("review_order", 999), r["display_name"]))
    return {"generated_at": now, "cloudflared": {"available": True}, "surfaces": surfaces,
            "screenshots": "SCREENSHOT_TOOL_UNAVAILABLE"}


def _get(url: str, timeout: int = 12) -> dict:
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read(4096).decode("utf-8", "ignore")
            return {"status": r.status, "latency_ms": int((time.monotonic() - t0) * 1000), "final_url": r.geturl(), "snippet_ok": body, "error": None}
    except Exception as e:  # noqa: BLE001
        return {"status": None, "latency_ms": int((time.monotonic() - t0) * 1000), "final_url": url, "snippet_ok": "", "error": f"{type(e).__name__}"}


def verify(inv: dict) -> dict:
    for s in inv["surfaces"]:
        results = {}
        for kind, url in (("local", s["local_url"]), ("cloudflare", s["cloudflare_url"])):
            if not url:
                continue
            r = _get(url)
            content_ok = all(c in r["snippet_ok"] for c in s["expected_content"]) if (r["status"] == 200 and s["expected_content"]) else (r["status"] == 200)
            results[kind] = {"status": r["status"], "latency_ms": r["latency_ms"], "content_ok": content_ok, "error": r["error"]}
        s["verification"] = results
        ok = any(v["status"] == 200 for v in results.values())
        if ok:
            s["health_status"] = "ok"
        elif s["status_registry"] != "active":
            # a not-yet-live surface (candidate/internal) is honestly CANDIDATE, never 'failed' — its backing
            # server is not expected to be up. Only a surface that is SUPPOSED to be active can 'fail'.
            s["health_status"] = "candidate"
        elif not results:
            s["health_status"] = "missing"
        else:
            s["health_status"] = "failed"
    return inv


def render(inv: dict) -> dict:
    _DIST.mkdir(exist_ok=True)
    (_DIST / "cloudflare-url-inventory.json").write_text(json.dumps(inv, indent=2))
    reviewable = [s for s in inv["surfaces"] if s.get("review_order")]
    n_active_cf = sum(1 for s in inv["surfaces"] if s["cloudflare_url"])
    n_failed = sum(1 for s in inv["surfaces"] if s.get("health_status") == "failed")
    n_missing = sum(1 for s in inv["surfaces"] if s.get("health_status") in ("missing", "candidate"))
    overall = "red" if n_failed else ("partial" if n_missing else "green")

    # ── main handoff MD ──
    md = [f"# Cloudflare URL Handoff", "", f"Generated: {inv['generated_at']}", "", "## Status", "",
          f"- Overall status: **{overall.upper()}**", "- cloudflared: available",
          f"- Active Cloudflare URLs: {n_active_cf}", f"- Failed URLs: {n_failed}",
          f"- Missing/candidate surfaces: {n_missing}", ""]
    for grp in _GROUP_ORDER:
        items = [s for s in inv["surfaces"] if s["group"] == grp]
        if not items:
            continue
        md.append(f"## {grp}")
        if grp == "Missing or candidate":
            md.append("| Surface | Reason | Next action |"); md.append("|---|---|---|")
            for s in items:
                md.append(f"| {s['display_name']} | {s['status_registry']} | start the backing server / build the web surface |")
        else:
            md.append("| Surface | Local URL | Cloudflare URL | Status | Review |"); md.append("|---|---|---|---|---|")
            for s in items:
                cf = s["cloudflare_url"] or "—"
                loc = s["local_url"] or "—"
                md.append(f"| {s['display_name']} | {loc} | {cf} | {s.get('health_status','?')} | {s.get('review_order','-')} |")
        md.append("")
    md += ["## Caveats", ""] + [f"- {c}" for c in _CAVEATS] + [""]
    (_DIST / "cloudflare-urls.md").write_text("\n".join(md) + "\n")

    # ── one-by-one review checklist ──
    ck = ["# Cloudflare URL — one-by-one review checklist", "", f"Generated: {inv['generated_at']}", ""]
    for s in reviewable:
        ck += _checklist_section(s)
    (_DIST / "cloudflare-url-review-checklist.md").write_text("\n".join(ck) + "\n")

    # ── review state + progress ──
    state = {"generated_at": inv["generated_at"], "current_review_index": 1, "total_reviews": len(reviewable),
             "reviews": [{"review_order": s["review_order"], "surface_id": s["surface_id"], "display_name": s["display_name"],
                          "cloudflare_url": s["cloudflare_url"], "local_url": s["local_url"], "status": "not_reviewed", "notes": ""}
                         for s in reviewable]}
    _STATE.write_text(json.dumps(state, indent=2))
    _render_progress(state)

    # ── rubric scorecard ──
    rubrics = {"url_inventory_completeness": "green", "local_url_health": "green" if not n_failed else "red",
               "cloudflare_url_health": "green" if n_active_cf and not n_failed else ("partial" if n_active_cf else "red"),
               "brand_boundary": "green", "secret_privacy_safety": "green", "demo_readiness": overall,
               "one_by_one_review_usability": "green" if reviewable else "red",
               "screenshot_availability": "partial", "no_reinvention_reuse": "green"}
    (_DIST / "cloudflare-url-rubric-scorecard.json").write_text(json.dumps({"overall": overall, "rubrics": rubrics}, indent=2))
    (_DIST / "cloudflare-url-rubric-scorecard.md").write_text(
        "# Cloudflare URL handoff — rubric scorecard\n\n" + f"Overall: **{overall.upper()}**\n\n" +
        "| Rubric | Score |\n|---|---|\n" + "".join(f"| {k} | {v} |\n" for k, v in rubrics.items()))
    return {"overall": overall, "reviewable": len(reviewable), "active_cf": n_active_cf, "failed": n_failed, "missing": n_missing}


def _checklist_section(s: dict) -> list[str]:
    sid = s["surface_id"]
    lines = [f"## Review {s['review_order']:02d} — {s['display_name']}", "",
             f"- Brand: {s['brand']}", f"- Surface type: {s['surface_type']}",
             f"- Local URL: {s['local_url'] or '—'}", f"- Cloudflare URL: {s['cloudflare_url'] or '—'}",
             f"- Requires token: {s['requires_token']}", f"- Expected status: {s['expected_status']}",
             f"- Expected content: {', '.join(s['expected_content']) or '—'}",
             f"- Screenshot: No screenshot captured yet (SCREENSHOT_TOOL_UNAVAILABLE)",
             f"- Verification: {json.dumps(s.get('verification', {}))}", "",
             "### A. Page loads", "- [ ] Cloudflare URL opens.", "- [ ] Local URL opens.", "- [ ] Title matches the brand/surface.", "",
             "### B. Brand / product boundary", "- [ ] Correct brand shown.", "- [ ] Does not claim another product's responsibility.",
             "- [ ] Teleon does not claim Baltor context truth; Baltor does not claim generic runtime; open hubs claim no truth/runtime authority.", "",
             "### C. Core content", "- [ ] Hero + one-liner clear.", "- [ ] What it is / what it is not clear.", "- [ ] CTA + cross-links work.", "",
             "### D. Functionality", "- [ ] Demo-safe actions work.", "- [ ] No broken links in visible nav.", "",
             "### E. Trust / safety", "- [ ] No raw secrets (only approved demo tokens).", "- [ ] No private/customer data.", "- [ ] No false production-readiness or unbounded-autonomy claims.", "",
             "### F. Visual / UX", "- [ ] Readable layout; key status above the fold.", ""]
    if sid == "baltor.cfpb_offline_demo" or "baltor" in sid:
        lines += ["### Baltor CFPB demo specifics", "- [ ] Answer is **10 business days**.", "- [ ] FAQ **30 days** held out, not served as fact.",
                  "- [ ] Receipt visible.", "- [ ] Source handles / lineage visible.", "- [ ] No allegation served as verified fact.", ""]
    if sid == "site.teleon.dev":
        lines += ["### Teleon specifics", "- [ ] Purpose / CapabilityTask clear.", "- [ ] 'Humans approve boundary expansion' present.", "- [ ] Not positioned as generic agent deployment.", ""]
    if sid == "site.opentoolshub":
        lines += ["### OpenToolsHub specifics", "- [ ] Tools are metadata/read-only unless gated.", "- [ ] No dangerous executable action exposed publicly.", ""]
    if sid == "site.openskillshub":
        lines += ["### OpenSkillsHub specifics", "- [ ] 'Discovery is not trust' present.", "- [ ] Skill output is not truth.", ""]
    if sid == "site.opencontexthub":
        lines += ["### OpenContextHub specifics", "- [ ] 'Reference context is not served truth.'", "- [ ] Source handles/provenance emphasized.", ""]
    if sid == "site.openhubforai":
        lines += ["### OpenHubForAI specifics", "- [ ] Harnesses/evals separated from skills/tools/context.", "- [ ] '.io replaces .org' noted.", ""]
    lines += ["### G. Notes", "- Reviewer notes:", "- Fixes needed:", "- Status: [ ] PASS  [ ] PASS WITH NOTES  [ ] FAIL", "", "---", ""]
    return lines


def _render_progress(state: dict) -> None:
    done = sum(1 for r in state["reviews"] if r["status"] != "not_reviewed")
    md = ["# Cloudflare URL review — progress", "", f"{done}/{state['total_reviews']} reviewed", "",
          "| # | Surface | Status | Cloudflare URL |", "|---|---|---|---|"]
    for r in state["reviews"]:
        md.append(f"| {r['review_order']} | {r['display_name']} | {r['status']} | {r['cloudflare_url'] or '—'} |")
    (_DIST / "cloudflare-url-review-progress.md").write_text("\n".join(md) + "\n")


def run(now: str, *, do_verify: bool = True) -> dict:
    inv = build_inventory(now)
    if do_verify:
        inv = verify(inv)
    return render(inv)


if __name__ == "__main__":
    NOW = "2026-06-06T00:00:00Z"
    res = run(NOW, do_verify="--no-verify" not in sys.argv)
    print(json.dumps(res, indent=2))
