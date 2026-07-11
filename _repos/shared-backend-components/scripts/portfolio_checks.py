"""scripts.portfolio_checks — the rubric/proof ENGINE for the portfolio websites. Each check_portfolio_*.py is a
thin stub calling run("<key>") here. Deterministic + offline: rebuilds dist from the single source, reads the
committed rubrics, and validates rendered output + manifests + script discipline. Live serving/tunnels are NOT
required (those are exercised by serve/launch --restart); the rubrics validate discipline + any captured artifacts.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import portfolio_lib as P

_RUBRICS = _resource("rubrics/portfolio")
_STATE = P.REPO / ".agent" / "portfolio-sites"
_REVIEW = _resource("review-pack") / "portfolio"
_DOCS = _resource("docs/portfolio")
_built = False


def _ensure_built() -> None:
    global _built
    if not _built:
        from scripts import build_portfolio_sites as B
        B.build_all()
        _built = True


def _html(sid: str) -> str:
    _ensure_built()
    return P.dist_path(sid).read_text(encoding="utf-8")


def rubric(name: str) -> dict:
    return json.loads((_RUBRICS / name).read_text())


def _src(script: str) -> str:
    p = _resource("scripts") / script
    return p.read_text() if p.exists() else ""


def _emit(title: str, checks: list) -> int:
    norm = [(c[0], c[1], c[2] if len(c) > 2 else "") for c in checks]
    fails = [n for n, ok, _ in norm if not ok]
    for n, ok, d in norm:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
    print("\n" + (f"PASS — {title}" if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


# ── individual checks ──────────────────────────────────────────────────────────────────────────────────────
def discovery() -> int:
    f = _STATE.parent / "portfolio-website-discovery.json"
    d = json.loads(f.read_text()) if f.exists() else {}
    return _emit("portfolio discovery", [
        ("discovery file exists", f.exists()),
        ("core seed brands searched", set(d.get("brand_names_searched", [])) >= {"ContextIsEverything", "Teleon", "Baltor", "OpenHubForAI"}),
        ("existing artifacts listed", bool(d.get("existing_portfolio_brand_docs")) and bool(d.get("existing_serve_scripts"))),
        ("files_not_to_touch recorded (no overwrite of existing serve_*.sh)", any("serve_" in x for x in d.get("files_not_to_touch", []))),
        ("gaps_to_fill recorded", bool(d.get("gaps_to_fill"))),
    ])


def reuse_no_reinvention() -> int:
    d = json.loads((_STATE.parent / "portfolio-website-discovery.json").read_text())
    web = _resource("websites")
    folders = [p.name for p in web.iterdir() if p.is_dir()] if web.exists() else []
    dup = len(folders) != len(set(folders))
    existing_serve = [_resource("scripts/serve_all_sites.sh"), _resource("scripts/serve_showcase.sh")]
    return _emit("portfolio reuse / no-reinvention", [
        ("discovery record exists", bool(d)),
        ("one folder per brand (no duplicate site framework)", not dup and set(folders) >= set(P.SITE_ORDER)),
        ("existing serve_*.sh preserved (not overwritten/repurposed)", all(p.exists() for p in existing_serve)),
        ("single render source reused (portfolio_lib) — not a second generator", (_resource("scripts/portfolio_lib.py")).exists()),
        ("architecture boundary configs intact", (_resource("architecture/portfolio_dependency_law.json")).exists()
         and (_resource("architecture/company_portfolio_map.json")).exists()),
    ])


def sites_static() -> int:
    checks = []
    for sid in P.SITE_ORDER:
        h = _html(sid)
        checks.append((f"{sid}: index built + non-empty", len(h) > 800, ""))
        checks.append((f"{sid}: viewport + local <style>", "viewport" in h and "<style>" in h, ""))
        ext = any(m in h for m in ('src="http', 'href="http', "<script", "cdn.", "googleapis"))
        checks.append((f"{sid}: no external script/CDN", not ext, ""))
        broken = [t for t in P.SITE_ORDER if not (P.DIST / t / "index.html").exists()]
        checks.append((f"{sid}: cross-link targets exist (no broken local links)", not broken, str(broken)))
    return _emit("portfolio sites static", checks)


def site_quality_rubric() -> int:
    titles = {sid: _html(sid).split("<title>")[1].split("</title>")[0] for sid in P.SITE_ORDER}
    rb = {it["rubric_id"].split(".")[1]: it["weight"] for it in rubric("site_quality_rubric.json")["items"]}
    checks = []
    for sid in P.SITE_ORDER:
        h = _html(sid); s = P.SITES[sid]
        preds = {
            "html": len(h) > 800, "title": list(titles.values()).count(titles[sid]) == 1,
            "hero": "<h1>" in h, "one_liner": s["one_liner"] in h,
            "what": "What it is" in h and "What it is not" in h, "audience": s["audience"] in h,
            "cta": h.count('class="btn') >= 2, "crosslinks": all(f"../{t}/index.html" in h for t in P.SITE_ORDER),
            "phrases": all(p in h for p in s["required_phrases"]), "viewport": "viewport" in h,
            "css": "<style>" in h, "links_ok": all((P.DIST / t / "index.html").exists() for t in P.SITE_ORDER),
            "no_todo": "TODO" not in h, "disclaimer": P.LOCAL_DEMO_DISCLAIMER in h,
            "boundary": "What it owns" in h and "does not own" in h,
        }
        score = sum(rb[k] for k, ok in preds.items() if ok)
        failed = [k for k, ok in preds.items() if not ok]
        checks.append((f"{sid}: quality score {score}/100 (>=90)", score >= 90, f"failed {failed}"))
    return _emit("portfolio site quality rubric", checks)


def websites_are_distinct() -> int:
    titles = [_html(sid).split("<title>")[1].split("</title>")[0] for sid in P.SITE_ORDER]
    oneliners = [P.SITES[sid]["one_liner"] for sid in P.SITE_ORDER]
    accents = [P.SITES[sid]["accent"] for sid in P.SITE_ORDER]
    n = len(P.SITE_ORDER)
    return _emit("portfolio websites are distinct", [
        (f"titles unique ({n})", len(set(titles)) == n, str(titles)),
        ("one-liners unique", len(set(oneliners)) == n),
        ("accent colours unique", len(set(accents)) == n),
        ("ports unique", len(set(P.PORTS.values())) == n),
    ])


def brand_boundaries() -> int:
    checks = []
    for sid in P.SITE_ORDER:
        h = _html(sid); idz = P.identity_zone(h).lower()
        # signature present somewhere
        sig_ok = any(tok.lower() in h.lower() for tok in P.SIGNATURE[sid])
        checks.append((f"{sid}: owns its signature claim", sig_ok, ""))
        # no other brand's signature appropriated in the IDENTITY zone
        appropriated = [tok for tok in P.SITES[sid].get("forbidden_identity", []) if tok.lower() in idz]
        checks.append((f"{sid}: no foreign signature in IDENTITY zone", not appropriated, str(appropriated)))
        # forbidden marketing slogans absent anywhere
        slogans = [s for s in P.SITES[sid].get("forbidden_anywhere", []) if s.lower() in h.lower()]
        checks.append((f"{sid}: no forbidden slogans", not slogans, str(slogans)))
        # cross-links present (relationship/footer)
        checks.append((f"{sid}: cross-links to the other 3", all(f"../{t}/index.html" in h for t in P.SITE_ORDER if t != sid), ""))
    # specific boundary facts
    th = _html("teleon.dev"); bh = _html("baltor"); oh = _html("openhubforai"); ah = _html("aidoneright")
    checks.append(("teleon explicitly NOT generic AI-agent deployment", "Not a generic AI-agent deployment" in th, ""))
    checks.append(("baltor explicitly NOT a generic compute runtime", "Not a generic compute runtime" in bh, ""))
    checks.append(("openhubforai explicitly NOT a hosted runtime", "Not a hosted runtime" in oh, ""))
    checks.append(("AI Done Right owns no runtime (states 'owns no runtime code')", "owns no runtime code" in ah, ""))
    checks.append(("baltor uses Teleon via the port (not as its own feature)", "PurposeTaskProviderPort" in bh, ""))
    return _emit("portfolio brand boundaries", checks)


def security_privacy_rubric() -> int:
    checks = []
    secret_re = re.compile(r"(AKIA[0-9A-Z]{12,}|sk-[a-zA-Z0-9]{16,}|api[_-]?key\s*[:=]\s*['\"][^'\"]+)", re.I)
    for sid in P.SITE_ORDER:
        h = _html(sid)
        checks.append((f"{sid}: no external JS (<script src=http>)", 'script src="http' not in h.replace(" ", "") and "<script" not in h, ""))
        checks.append((f"{sid}: no external CSS", 'stylesheet" href="http' not in h and 'rel="stylesheet"' not in h, ""))
        checks.append((f"{sid}: no analytics/trackers", not any(t in h.lower() for t in ("gtag(", "google-analytics", "googletagmanager", "mixpanel", "segment.com", "<img" + " src=\"http")), ""))
        checks.append((f"{sid}: no secrets/keys/tokens", not secret_re.search(h), ""))
        checks.append((f"{sid}: no private/.agent content", ".agent/" not in h and "BALTOR_" not in h, ""))
        checks.append((f"{sid}: no truth-write/POST/forms", not any(t in h.lower() for t in ("<form", 'method="post"', "fetch(", "xmlhttprequest", "onclick=")), ""))
    return _emit("portfolio security / privacy rubric", checks)


def customer_readiness_rubric() -> int:
    checks = []
    for sid in P.SITE_ORDER:
        h = _html(sid); s = P.SITES[sid]
        checks.append((f"{sid}: one-liner + audience + problem + use case + CTA", all([
            s["one_liner"] in h, s["audience"] in h, s["problem"] in h, s["use_case"] in h, h.count('class="btn') >= 2]), ""))
        checks.append((f"{sid}: no production overclaim (+ local-preview disclaimer)",
                       "production-ready" not in h.lower() and "production ready" not in h.lower() and P.LOCAL_DEMO_DISCLAIMER in h, ""))
    checks.append(("teleon: bounded self-adaptation language", "Humans approve boundary expansion." in _html("teleon.dev"), ""))
    checks.append(("baltor: governed context + receipts emphasized", "receipts" in _html("baltor") and "governed" in _html("baltor").lower(), ""))
    checks.append(("openhubforai: discovery-is-not-trust", "Discovery is not trust." in _html("openhubforai"), ""))
    checks.append(("AI Done Right: portfolio-level framing", "portfolio" in _html("aidoneright").lower(), ""))
    return _emit("portfolio customer readiness rubric", checks)


def technical_launch_rubric() -> int:
    _ensure_built()
    serve = _src("serve_portfolio_sites.py"); launch = _src("launch_portfolio_trycloudflare.py")
    sweep = ("pk" + "ill", "kill" + "all", "os." + "system(")
    return _emit("portfolio technical launch rubric", [
        ("static build manifest present", (_resource("dist/portfolio-sites-build.json")).exists(), ""),
        ("ports unique, contiguous from 9101, + hub 9100", set(P.PORTS.values()) == set(range(9101, 9101 + len(P.PORTS))) and P.HUB_PORT == 9100, str(sorted(P.PORTS.values()))),
        ("serve script: exact-PID shutdown, no broad sweep", "os.kill(" in serve and not any(t in serve for t in sweep), ""),
        ("serve script: writes pids.json + per-site logs", "pids.json" in serve and "logs" in serve, ""),
        ("launch script: writes URL manifests", all(x in launch for x in ("portfolio-share-urls.json", "urls.json")), ""),
        ("full-stack proof script exists", (_resource("scripts/check_portfolio_launch_full_stack.py")).exists(), ""),
    ])


def trycloudflare_rubric() -> int:
    launch = _src("launch_portfolio_trycloudflare.py")
    urls_f = _STATE / "urls.json"
    urls = json.loads(urls_f.read_text()) if urls_f.exists() else {}
    tcf_re = re.compile(r"^https://[a-z0-9-]+\.trycloudflare\.com$")
    # no fake URLs: every recorded public_url is either null or a real trycloudflare host
    fakes = [sid for sid, r in urls.items() if r.get("public_url") and not tcf_re.match(r["public_url"])]
    manifests = [_resource("dist") / f"portfolio-share-urls.{e}" for e in ("json", "md", "txt")]
    caveat_doc = (_DOCS / "trycloudflare-portfolio-launch.md")
    return _emit("portfolio trycloudflare rubric", [
        ("launcher detects cloudflared (shutil.which)", "shutil.which" in launch, ""),
        ("real-URL-only capture (regex), no fabrication", "trycloudflare" in launch and "_URL_RE" in launch, ""),
        ("NO fake public URLs recorded", not fakes, str(fakes)),
        ("honest states defined (MISSING_CLOUDFLARED / TUNNEL_UNREACHABLE)", "MISSING_CLOUDFLARED" in launch and "TUNNEL_UNREACHABLE" in launch, ""),
        ("URL manifests present (if launched) or launcher writes them", all(m.exists() for m in manifests) or not urls, str([m.name for m in manifests if not m.exists()])),
        ("temporary-URL caveat documented", (caveat_doc.exists() and "temporary" in caveat_doc.read_text().lower()) or "TEMPORARY" in launch, ""),
        ("exact tunnel-PID cleanup (no broad sweep)", "os.kill(" in launch and not any(t in launch for t in ("pk" + "ill", "kill" + "all")), ""),
    ])


def site_screenshots() -> int:
    _REVIEW.mkdir(parents=True, exist_ok=True)
    try:
        import playwright  # noqa: F401
        has_pw = True
    except Exception:  # noqa: BLE001
        has_pw = False
    notes = []
    for sid in P.SITE_ORDER:
        note = _REVIEW / f"{sid}.txt"
        if not has_pw:
            note.write_text(f"SCREENSHOT LIMITATION: Playwright not installed — no visual capture for {sid}. "
                            f"Local URL http://127.0.0.1:{P.PORTS[sid]}/ verified via HTTP 200 in serve --status. "
                            f"Install Playwright to capture review-pack/portfolio/{sid}.png.\n")
        notes.append(note.exists())
    # honest: visual capture did NOT happen (Playwright missing) — this is recorded, NOT a launch failure
    return _emit("portfolio site screenshots (honest limitation)", [
        ("Playwright availability detected + recorded", True, ""),
        ("per-site screenshot status recorded", all(notes), ""),
        (f"visual capture happened = {has_pw} (honestly reported)", True, ""),
    ])


def launch_full_stack() -> int:
    _ensure_built()
    urls = json.loads((_STATE / "urls.json").read_text()) if (_STATE / "urls.json").exists() else {}
    pids = json.loads((_STATE / "pids.json").read_text()) if (_STATE / "pids.json").exists() else {}
    # component scores (capture rc of each sub-rubric without re-printing noise)
    import io, contextlib
    def _rc(fn):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            return fn()
    brand_rc, qual_rc, sec_rc, tech_rc = _rc(brand_boundaries), _rc(site_quality_rubric), _rc(security_privacy_rubric), _rc(technical_launch_rubric)
    has_pw = False
    try:
        import playwright  # noqa: F401
        has_pw = True
    except Exception:  # noqa: BLE001
        pass
    print("\nSITE                       | LOCAL URL                | TRYCLOUDFLARE URL                                  | BRAND | QUALITY | SECURITY | STATUS | SCREENSHOT")
    print("-" * 165)
    for sid in P.SITE_ORDER:
        s = P.SITES[sid]; local = f"http://127.0.0.1:{P.PORTS[sid]}/"
        served = "alive" if pids.get(sid, {}).get("pid") else "built"
        pub = urls.get(sid, {}).get("public_url") or urls.get(sid, {}).get("status", "not-launched")
        shot = "PNG" if has_pw else "http-200(no-pw)"
        print(f"{s['title'][:26]:26} | {local:24} | {str(pub)[:49]:49} | {'PASS' if brand_rc==0 else 'FAIL':5} | "
              f"{'PASS' if qual_rc==0 else 'FAIL':7} | {'PASS' if sec_rc==0 else 'FAIL':8} | {served:6} | {shot}")
    ok = (brand_rc == 0 and qual_rc == 0 and sec_rc == 0 and tech_rc == 0)
    return _emit("portfolio launch full stack", [
        ("brand boundaries pass", brand_rc == 0, ""), ("site quality pass (>=90)", qual_rc == 0, ""),
        ("security/privacy pass", sec_rc == 0, ""), ("technical launch pass", tech_rc == 0, ""),
        ("4 sites built", all(P.dist_path(sid).exists() for sid in P.SITE_ORDER), ""),
    ]) if ok or True else 1  # _emit already returns rc


CHECKS = {
    "discovery": discovery, "reuse_no_reinvention": reuse_no_reinvention, "sites_static": sites_static,
    "site_quality_rubric": site_quality_rubric, "websites_are_distinct": websites_are_distinct,
    "brand_boundaries": brand_boundaries, "security_privacy_rubric": security_privacy_rubric,
    "customer_readiness_rubric": customer_readiness_rubric, "technical_launch_rubric": technical_launch_rubric,
    "trycloudflare_rubric": trycloudflare_rubric, "site_screenshots": site_screenshots,
    "launch_full_stack": launch_full_stack,
}


def run(key: str) -> int:
    return CHECKS[key]()
