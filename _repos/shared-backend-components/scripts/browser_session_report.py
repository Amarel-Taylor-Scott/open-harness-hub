#!/usr/bin/env python3
"""scripts.browser_session_report — ADDITIVE report slice over the read-only browser harness.

Consumes a list of CapturedArtifact rows (produced by scripts.primitive_browser_control_harness — the ONLY
capture front-end; this module does NOT crawl, submit, or touch the network) and reconstructs one
browser_session_report, INCLUDING a TAB GRAPH:

    * one tab_state per captured page — page_state classified from login_wall / forms / downloads / api refs,
      auth_state from the login wall + auth markers, side_effect_risk from the harness's side_effect_controls
      (regulated when the mutation is a payment/claim/financial action), dom_hash from the CapturedArtifact
      source_hash;
    * opener relationships — a tab whose page LINKED to a child url in the same session is the child's opener;
    * popup / cross-origin transition / duplicate-tab detection over that opener graph;
    * the network / screenshot / dom / form / download surfaces + side_effect_attempts (detected-but-never-
      executed mutating controls — the harness never submits) + the candidate-primitive opportunity SEEDS the
      session implies (expanded into full rows by scripts.browser_report_to_primitive_candidates).

Reuse-first: this IMPORTS the harness's primitives (redact_secrets, browser_extract_forms,
browser_detect_login_wall, classify_trust_tier, ARTIFACT_RECORD_TYPE) — it never re-implements extraction.
Every row is candidate=true / serves_truth=false; digests + bounded units only; no raw bodies; secrets redacted.

    python3 scripts/browser_session_report.py --self-test
    python3 scripts/browser_session_report.py --demo
    python3 scripts/browser_session_report.py --from-artifacts <captured_artifacts.jsonl> --mode read_only
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

import argparse  # noqa: E402
import hashlib  # noqa: E402  (content DIGESTS only; ids stay canonical_id — the no-hashlib law is scoped to src/**)
import json  # noqa: E402
import re  # noqa: E402
import urllib.parse  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import (  # noqa: E402  reuse — never duplicate extraction
    ARTIFACT_RECORD_TYPE,
    browser_detect_login_wall,
    browser_extract_forms,
    classify_trust_tier,
    redact_secrets,
)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"browser_session_report requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
SESSION_RECORD_TYPE = "browser_session_report"
TAB_RECORD_TYPE = "tab_state"
SCHEMA_VERSION = "1.0.0"                     # version lives in metadata, never in an id/name
_DATA_SUBDIR = "data/dev-intel/browser_reports"
SESSION_REPORT_FILENAME = "browser_session_reports.jsonl"
_TITLE_CAP = 80                             # bounded title text
_TEXT_CAP = 300                            # bounded action/label text

#: canonical enums — single source; the self-test asserts the schema files carry the SAME sets (drift gate).
MODES = ("read_only", "authenticated_internal", "side_effect_allowed")
PAGE_STATES = ("not_captured", "login_wall", "form_entry", "download_page", "api_portal", "content")
AUTH_STATES = ("unknown", "logged_out", "logged_in", "mfa_required")
SIDE_EFFECT_RISKS = ("none", "read", "write", "regulated")
TRANSITION_TYPES = ("seed", "same_origin_navigation", "cross_origin_transition", "popup")
CANDIDATE_TYPES = ("page_state_classifier", "form_field_mapper", "safe_submit_gate",
                   "success_state_verifier", "dom_drift_detector",
                   "api_from_browser_endpoint_candidate", "tab_graph_builder",
                   "popup_detector", "download_origin_tracker")

# regulated side-effect lexicon (payment / claim / financial / health-admin mutations)
_REGULATED_RE = re.compile(r"\b(pay|payment|purchase|checkout|buy|order|transfer|wire|claim|refund|invoice|"
                           r"subscribe|remit|enroll|disburse)\b", re.I)
# authenticated-content markers (you are already logged in)
_LOGGED_IN_RE = re.compile(r"\b(log\s?out|sign\s?out|my account|dashboard|welcome back|signed in as)\b", re.I)
# mfa / second-factor markers
_MFA_RE = re.compile(r"\b(mfa|2fa|two-?factor|one-?time (?:code|passcode)|otp|verification code|authenticator)\b", re.I)
# oauth / login popup url shapes
_AUTH_URL_RE = re.compile(r"/(oauth2?|authorize|login|sign-?in|sso|saml|auth)(/|\?|#|$)", re.I)
_GRAPHQL_RE = re.compile(r"/graphql|graphiql", re.I)


# ── small utilities ────────────────────────────────────────────────────────────────────────────────────────────
def _host(url: str) -> str:
    return (urllib.parse.urlparse(url or "").hostname or "").lower()


def _clip(text: Any, cap: int = _TEXT_CAP) -> str:
    """Redact secrets (harness primitive) + collapse whitespace + bound. Applied to EVERY text field this
    module copies into a new row — defence in depth, since these are fresh surfaces."""
    clean, _ = redact_secrets(str(text or ""))
    return re.sub(r"\s+", " ", clean).strip()[:cap]


def _digest(value: Any) -> str:
    """Stable short content digest (hashlib is fine for digests; ids use canonical_id)."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8", "ignore")).hexdigest()[:16]


def _artifact_extract(art: dict[str, Any]) -> dict[str, Any]:
    """The extracted block for a CapturedArtifact. Full harness rows carry `extracted`; a MINIMAL row that
    carries a raw `html` field is re-extracted here with the harness's OWN primitives (browser_extract_forms +
    browser_detect_login_wall) so this consumer is robust to both shapes without duplicating extraction."""
    ex = dict(art.get("extracted") or {})
    html = art.get("html")
    if "forms" not in ex and html:
        ex["forms"] = browser_extract_forms(html)          # harness primitive — reuse, never re-implement
    if "login_wall" not in ex and html:
        ex["login_wall"] = browser_detect_login_wall(html)  # harness primitive
    ex.setdefault("forms", [])
    ex.setdefault("login_wall", False)
    ex.setdefault("side_effect_controls", [])
    ex.setdefault("downloadable_docs", [])
    ex.setdefault("api_spec_links", [])
    ex.setdefault("links_sample", [])
    ex.setdefault("readable_text", "")
    ex.setdefault("graphql", False)
    return ex


def _dom_hash(art: dict[str, Any], ex: dict[str, Any]) -> Optional[str]:
    h = art.get("source_hash")
    if h:
        return h
    html = art.get("html")
    if html:
        return "sha256:" + hashlib.sha256(str(html).encode("utf-8", "ignore")).hexdigest()
    rt = ex.get("readable_text") or ""
    return "sha256:" + hashlib.sha256(rt.encode("utf-8", "ignore")).hexdigest() if rt else None


# ── the classifiers (deterministic; D0) ──────────────────────────────────────────────────────────────────────────
def classify_page_state(art: dict[str, Any], ex: dict[str, Any]) -> str:
    if not art.get("captured"):
        return "not_captured"
    if ex.get("login_wall"):
        return "login_wall"
    forms = ex.get("forms") or []
    side = ex.get("side_effect_controls") or []
    if side or any((f.get("method") or "").lower() == "post" for f in forms):
        return "form_entry"
    if ex.get("downloadable_docs"):
        return "download_page"
    if ex.get("api_spec_links") or ex.get("graphql"):
        return "api_portal"
    if forms:
        return "form_entry"
    return "content"


def classify_auth_state(art: dict[str, Any], ex: dict[str, Any]) -> str:
    if not art.get("captured"):
        return "unknown"
    text = ex.get("readable_text") or ""
    if ex.get("login_wall"):
        return "mfa_required" if _MFA_RE.search(text) else "logged_out"
    if _LOGGED_IN_RE.search(text):
        return "logged_in"
    return "unknown"


def classify_side_effect_risk(art: dict[str, Any], ex: dict[str, Any]) -> str:
    if not art.get("captured"):
        return "none"
    side = ex.get("side_effect_controls") or []
    forms = ex.get("forms") or []
    blob = " ".join([f"{s.get('label', '')} {s.get('action', '')}" for s in side]
                    + [str(f.get("action", "")) for f in forms])
    has_write = bool(side) or any((f.get("method") or "").lower() == "post" for f in forms)
    if has_write and _REGULATED_RE.search(blob):
        return "regulated"
    if has_write:
        return "write"
    if forms or (ex.get("readable_text") or ""):
        return "read"
    return "none"


# ── tab_state construction ────────────────────────────────────────────────────────────────────────────────────────
def _tab_downloads(ex: dict[str, Any], page_host: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for u in (ex.get("downloadable_docs") or []):
        oh = _host(u)
        m = re.search(r"\.([a-z0-9]{1,6})(?:\?|#|$)", u, re.I)
        out.append({"url": u, "origin": oh or None,
                    "cross_origin": bool(oh and page_host and oh != page_host),
                    "trust_tier": classify_trust_tier(u),           # harness primitive
                    "ext": (m.group(1).lower() if m else None)})
    return out


def _tab_network_calls(art: dict[str, Any], ex: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for u in (ex.get("api_spec_links") or []):
        low = u.lower()
        kind = ("graphql" if _GRAPHQL_RE.search(u) else "postman" if "postman" in low
                else "asyncapi" if "asyncapi" in low else "grpc" if ".proto" in low else "openapi")
        out.append({"kind": kind, "url": u, "source": "page_reference", "trust_tier": classify_trust_tier(u)})
    if ex.get("graphql") and not any(c["kind"] == "graphql" for c in out):
        out.append({"kind": "graphql", "url": f"{art.get('url', '')}#graphql", "source": "page_reference",
                    "trust_tier": art.get("trust_tier") or classify_trust_tier(art.get("url", ""))})
    return out


def _tab_state(art: dict[str, Any], ex: dict[str, Any], index: int, session_id: str, context_id: str) -> dict[str, Any]:
    url = art.get("url", "")
    host = _host(url)
    dom_hash = _dom_hash(art, ex)
    return {
        "record_type": TAB_RECORD_TYPE,
        "schema_version": SCHEMA_VERSION,
        "tab_id": canonical_id("tab", session_id, str(index), dom_hash or url),  # index keeps duplicates distinct
        "context_id": context_id,
        "url": url,
        "domain": host or None,
        "trust_tier": art.get("trust_tier") or classify_trust_tier(url),
        "title": _clip(ex.get("readable_text", ""), _TITLE_CAP) or None,
        "opener_tab_id": None,          # filled by the graph pass
        "transition_type": "seed",      # filled by the graph pass
        "is_popup": False,
        "is_duplicate_of": None,
        "page_state": classify_page_state(art, ex),
        "dom_hash": dom_hash,
        "screenshot_hash": art.get("screenshot_hash") if ex.get("has_screenshot") else None,
        "accessibility_hash": art.get("accessibility_hash") if ex.get("has_accessibility_tree") else None,
        "auth_state": classify_auth_state(art, ex),
        "side_effect_risk": classify_side_effect_risk(art, ex),
        "downloads": _tab_downloads(ex, host),
        "network_calls": _tab_network_calls(art, ex),
        "n_forms": len(ex.get("forms") or []),
        "captured": bool(art.get("captured")),
        "evidence_source_hash": art.get("source_hash"),
        **BOUNDARY,
    }


# ── the tab GRAPH (opener edges, cross-origin transitions, popups, duplicates) ────────────────────────────────────
def _apply_tab_graph(tabs: list[dict[str, Any]], ex_by_tab: dict[str, dict[str, Any]]) -> dict[str, Any]:
    links_by_tab = {t["tab_id"]: list(ex_by_tab.get(t["tab_id"], {}).get("links_sample") or []) for t in tabs}
    by_id = {t["tab_id"]: t for t in tabs}
    edges: list[dict[str, Any]] = []
    openers: dict[str, str] = {}
    cross: list[dict[str, Any]] = []
    popups: list[str] = []

    for i, child in enumerate(tabs):
        parent = None
        for j, cand in enumerate(tabs):          # tabs are in capture order → first (earliest) linker = opener
            if j == i or cand["url"] == child["url"]:
                continue
            if child["url"] in links_by_tab.get(cand["tab_id"], []):
                parent = cand
                break
        if parent is None:
            child["opener_tab_id"] = None
            child["transition_type"] = "seed"
            continue
        child["opener_tab_id"] = parent["tab_id"]
        openers[child["tab_id"]] = parent["tab_id"]
        same_origin = parent.get("domain") == child.get("domain")
        is_popup = (not same_origin) and (
            child["auth_state"] in ("logged_out", "mfa_required")
            or child["page_state"] == "login_wall"
            or bool(_AUTH_URL_RE.search(child["url"]))
        )
        ttype = "popup" if is_popup else ("same_origin_navigation" if same_origin else "cross_origin_transition")
        child["transition_type"] = ttype
        if is_popup:
            child["is_popup"] = True
            popups.append(child["tab_id"])
        edges.append({"from": parent["tab_id"], "to": child["tab_id"], "transition_type": ttype})
        if not same_origin:
            cross.append({"from": parent["tab_id"], "to": child["tab_id"],
                          "from_domain": parent.get("domain"), "to_domain": child.get("domain")})

    # duplicate tabs — identical DOM digest (fallback: identical url)
    groups: dict[str, list[str]] = {}
    for t in tabs:
        groups.setdefault(t.get("dom_hash") or t["url"], []).append(t["tab_id"])
    duplicate_groups: list[list[str]] = []
    for ids in groups.values():
        if len(ids) > 1:
            duplicate_groups.append(ids)
            for dup in ids[1:]:
                by_id[dup]["is_duplicate_of"] = ids[0]

    return {"nodes": [t["tab_id"] for t in tabs], "edges": edges, "openers": openers,
            "cross_origin_transitions": cross, "popups": popups, "duplicate_groups": duplicate_groups}


# ── report-surface aggregation ────────────────────────────────────────────────────────────────────────────────────
def _form_rows(tab: dict[str, Any], ex: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for f in (ex.get("forms") or []):
        action = _clip(f.get("action", ""), _TEXT_CAP)
        method = (f.get("method") or "get").lower()
        fields = [{"name": _clip(fl.get("name", ""), _TITLE_CAP), "type": _clip(fl.get("type", ""), 40)}
                  for fl in (f.get("fields") or [])]
        post = method == "post"
        side_effect = post
        names_blob = action + " " + " ".join(fl["name"] for fl in fields)
        risk = ("regulated" if side_effect and _REGULATED_RE.search(names_blob)
                else "write" if side_effect else "read")
        form_id = canonical_id("form", tab["dom_hash"] or tab["url"], action, method,
                               *[fl["name"] for fl in fields])
        rows.append({"form_id": form_id, "tab_id": tab["tab_id"], "action": action, "method": method,
                     "fields": fields, "post": post, "side_effect": side_effect, "side_effect_risk": risk})
    return rows


def _side_effect_attempts(tab: dict[str, Any], ex: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in (ex.get("side_effect_controls") or []):
        out.append({"tab_id": tab["tab_id"], "kind": s.get("kind", "button"),
                    "action": _clip(s.get("action", ""), _TEXT_CAP), "method": (s.get("method") or ""),
                    "label": _clip(s.get("label", ""), _TITLE_CAP),
                    "side_effect_risk": tab["side_effect_risk"],
                    "executed": False, "blocked_reason": "read_only_harness_never_submits"})
    return out


# ── candidate-primitive opportunity SEEDS (the report's index; full rows built by the sibling module) ─────────────
def browser_candidate_id(candidate_type: str, session_id: str, evidence_hash: str) -> str:
    """THE single id authority for browser primitive candidates — imported by
    scripts.browser_report_to_primitive_candidates so the seed id and the full-row id always agree."""
    return canonical_id("bpc", candidate_type, session_id, evidence_hash)


def _seed(candidate_type: str, session_id: str, ref_kind: str, ref_id: Optional[str],
          evidence_refs: list[dict[str, Any]]) -> dict[str, Any]:
    return {"candidate_id": browser_candidate_id(candidate_type, session_id, _digest(evidence_refs)),
            "candidate_type": candidate_type, "evidence_refs": evidence_refs,
            "ref_kind": ref_kind, "ref_id": ref_id}


def _candidate_seeds(session_id: str, tabs: list[dict[str, Any]], forms: list[dict[str, Any]],
                     graph: dict[str, Any], downloads: list[dict[str, Any]],
                     network_artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enumerate WHICH candidate primitives this session implies (type + evidence + stable id). The sibling
    module expands each into a full browser_primitive_candidate contract row."""
    captured = [t for t in tabs if t.get("captured")]
    dom_by_tab = {t["tab_id"]: t.get("dom_hash") for t in tabs}
    sess_ev = [{"kind": "source_hash", "value": t["dom_hash"]} for t in captured if t.get("dom_hash")][:12]
    seeds: list[dict[str, Any]] = []

    if captured:
        seeds.append(_seed("page_state_classifier", session_id, "session", None,
                           sess_ev or [{"kind": "url", "value": session_id}]))
    for f in forms:
        ev = ([{"kind": "source_hash", "value": dom_by_tab.get(f["tab_id"])}] if dom_by_tab.get(f["tab_id"]) else [])
        ev.append({"kind": "form", "value": f.get("action") or f["form_id"]})
        seeds.append(_seed("form_field_mapper", session_id, "form", f["form_id"], ev))
        if f["post"] or f["side_effect"]:
            seeds.append(_seed("safe_submit_gate", session_id, "form", f["form_id"], ev))
    if (any(f["post"] or f["side_effect"] for f in forms)
            or any(t["auth_state"] in ("logged_out", "mfa_required", "logged_in") for t in captured)):
        seeds.append(_seed("success_state_verifier", session_id, "session", None, sess_ev))
    if any(t.get("dom_hash") for t in captured):
        seeds.append(_seed("dom_drift_detector", session_id, "session", None, sess_ev))
    if len(captured) >= 2:
        seeds.append(_seed("tab_graph_builder", session_id, "session", None, sess_ev))
    if len(captured) >= 2 or graph.get("cross_origin_transitions"):
        seeds.append(_seed("popup_detector", session_id, "session", None, sess_ev))
    if downloads:
        dev = [{"kind": "download", "value": d["url"]} for d in downloads][:12]
        seeds.append(_seed("download_origin_tracker", session_id, "session", None, dev or sess_ev))
    seen: set[str] = set()
    for na in network_artifacts:
        if na["url"] in seen:
            continue
        seen.add(na["url"])
        seeds.append(_seed("api_from_browser_endpoint_candidate", session_id, "network", na["url"],
                           [{"kind": "network", "value": na["url"]}, {"kind": "api_spec", "value": na["url"]}]))
    return seeds


# ── the public builder ────────────────────────────────────────────────────────────────────────────────────────────
def build_session_report(artifacts: list[dict[str, Any]], *, clock: Callable[[], float],
                         mode: str = "read_only") -> dict[str, Any]:
    """Turn a list of CapturedArtifact dicts into ONE browser_session_report (with a tab graph). `clock` is
    injected (deterministic under test — no wall time). Consumes only rows whose record_type is the harness's
    ARTIFACT_RECORD_TYPE."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    arts = [a for a in artifacts if isinstance(a, dict) and a.get("record_type") == ARTIFACT_RECORD_TYPE]
    exs = [_artifact_extract(a) for a in arts]
    dom_hashes = [_dom_hash(a, ex) for a, ex in zip(arts, exs)]

    seed_hashes = sorted(h for h in dom_hashes if h)
    session_id = canonical_id("bsr", mode, *(seed_hashes or [a.get("url", "") for a in arts] or ["empty"]))
    context_id = canonical_id("ctx", session_id)

    tabs: list[dict[str, Any]] = []
    ex_by_tab: dict[str, dict[str, Any]] = {}
    for idx, (a, ex) in enumerate(zip(arts, exs)):
        t = _tab_state(a, ex, idx, session_id, context_id)
        tabs.append(t)
        ex_by_tab[t["tab_id"]] = ex
    graph = _apply_tab_graph(tabs, ex_by_tab)

    forms: list[dict[str, Any]] = []
    side_effect_attempts: list[dict[str, Any]] = []
    network_artifacts: list[dict[str, Any]] = []
    screenshots: list[dict[str, Any]] = []
    dom_snapshots: list[dict[str, Any]] = []
    downloads: list[dict[str, Any]] = []
    for t, a in zip(tabs, arts):
        ex = ex_by_tab[t["tab_id"]]
        forms.extend(_form_rows(t, ex))
        side_effect_attempts.extend(_side_effect_attempts(t, ex))
        for c in t["network_calls"]:
            network_artifacts.append({"tab_id": t["tab_id"], **c})
        if t["screenshot_hash"]:
            screenshots.append({"tab_id": t["tab_id"], "screenshot_hash": t["screenshot_hash"], "url": t["url"]})
        if t["dom_hash"]:
            dom_snapshots.append({"tab_id": t["tab_id"], "url": t["url"], "dom_hash": t["dom_hash"],
                                  "source_bytes": int(a.get("source_bytes") or 0)})
        for d in t["downloads"]:
            downloads.append({"tab_id": t["tab_id"], **d})

    seeds = _candidate_seeds(session_id, tabs, forms, graph, downloads, network_artifacts)

    gen = float(clock())
    started = min((float(a.get("ts", 0.0)) for a in arts), default=gen)
    ended = max((float(a.get("ts", 0.0)) for a in arts), default=gen)
    report = {
        "record_type": SESSION_RECORD_TYPE,
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "generated_at": gen,
        "started_at": started,
        "ended_at": ended,
        "mode": mode,
        "contexts": [{"context_id": context_id, "mode": mode,
                      "tab_ids": [t["tab_id"] for t in tabs],
                      "origins": sorted({t["domain"] for t in tabs if t.get("domain")})}],
        "tabs": tabs,
        "visited_urls": list(dict.fromkeys(a.get("url", "") for a in arts)),
        "network_artifacts": network_artifacts,
        "screenshots": screenshots,
        "dom_snapshots": dom_snapshots,
        "forms": forms,
        "downloads": downloads,
        "side_effect_attempts": side_effect_attempts,
        "candidate_primitives": seeds,
        "tab_graph": graph,
        "stats": {
            "n_tabs": len(tabs),
            "n_captured": sum(1 for t in tabs if t.get("captured")),
            "n_forms": len(forms),
            "n_side_effect_forms": sum(1 for f in forms if f["side_effect"]),
            "n_downloads": len(downloads),
            "n_network_artifacts": len(network_artifacts),
            "n_cross_origin_transitions": len(graph["cross_origin_transitions"]),
            "n_popups": len(graph["popups"]),
            "n_duplicate_groups": len(graph["duplicate_groups"]),
            "n_candidate_primitives": len(seeds),
            "candidate_types": sorted({s["candidate_type"] for s in seeds}),
        },
        **BOUNDARY,
    }
    return report


def write_session_reports(rows: list[dict[str, Any]], out_path: Optional[Path] = None) -> Path:
    out_path = out_path or (resource(_DATA_SUBDIR) / SESSION_REPORT_FILENAME)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return out_path


# ── bundled OFFLINE fixture (single source, shared by both modules' self-tests) ───────────────────────────────────
_FIX_PORTAL_URL = "https://portal.example.com/"
_FIX_DOWNLOAD_URL = "https://portal.example.com/downloads/companion-guide"
_FIX_EXTERNAL_URL = "https://partner.example.net/blog"
_FIX_PORTAL_HTML = """<!doctype html><html><head><title>Payer Provider Portal</title></head><body>
<h1>Provider Portal</h1><p>Sign in to submit a claim. Support key: sk-live-DEMOKEYSHOULDNOTLEAK0001.</p>
<a href="/downloads/companion-guide">Companion Guide</a>
<a href="https://partner.example.net/blog">Partner blog</a>
<a href="/docs/openapi.json">OpenAPI spec</a> <a href="/graphql">GraphQL</a>
<form action="/submit-claim" method="post"><input name="member_id" type="text"><button>Submit Claim</button></form>
<form action="/search" method="get"><input name="q" type="text"><button>Search</button></form>
<input name="password" type="password"></body></html>"""
_FIX_DOWNLOAD_HTML = """<!doctype html><html><head><title>Companion Guide</title></head><body>
<h1>Companion Guide Downloads</h1><p>Download the 837 companion guide and fee schedule.</p>
<a href="/files/companion-guide.pdf">Companion Guide (PDF)</a>
<a href="/files/fee-schedule.csv">Fee schedule (CSV)</a></body></html>"""
_FIX_EXTERNAL_HTML = """<!doctype html><html><head><title>Partner Blog</title></head><body>
<h1>Integration notes</h1><p>How partners integrate with the provider portal.</p>
<a href="/more">More posts</a></body></html>"""


def fixture_artifacts(clock: Callable[[], float]) -> list[dict[str, Any]]:
    """Build the 3-page fixture as REAL CapturedArtifact rows via the harness itself (offline, injected fetch —
    no network, no browser). Reuse of the harness's own capture path guarantees we consume its exact row shape."""
    from scripts.primitive_browser_control_harness import StaticBackend, capture_artifact  # harness reuse (offline)
    pages = {_FIX_PORTAL_URL: _FIX_PORTAL_HTML, _FIX_DOWNLOAD_URL: _FIX_DOWNLOAD_HTML,
             _FIX_EXTERNAL_URL: _FIX_EXTERNAL_HTML}
    be = StaticBackend(fetch=lambda u: pages.get(u))
    robots = lambda u: "User-agent: *\nAllow: /\n"  # noqa: E731  permissive robots; no network
    return [capture_artifact(be, u, ts=clock(), robots_fetch=robots)
            for u in (_FIX_PORTAL_URL, _FIX_DOWNLOAD_URL, _FIX_EXTERNAL_URL)]


def build_fixture_session_report(*, clock: Callable[[], float], mode: str = "read_only") -> dict[str, Any]:
    """The canonical fixture report — the SINGLE source both self-tests (this module + the candidate module) use."""
    return build_session_report(fixture_artifacts(clock), clock=clock, mode=mode)


def _make_test_clock() -> Callable[[], float]:
    st = {"n": 0.0}

    def clock() -> float:
        st["n"] += 10.0
        return st["n"]

    return clock


# ── schema helpers (single-source enum drift gate + row validation) ───────────────────────────────────────────────
def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((resource("schemas") / name).read_text(encoding="utf-8"))


def _make_validator(schema_name: str):
    import warnings

    import jsonschema  # local import so the module has no hard dep unless validating
    names = ["browser_session_report.schema.json", "tab_state.schema.json",
             "browser_primitive_candidate.schema.json"]
    docs = {n: _load_schema(n) for n in names}
    base = (resource("schemas")).as_uri() + "/"
    store: dict[str, Any] = {}
    for n, d in docs.items():
        store[base + n] = d
        if "$id" in d:                      # our schemas carry an absolute $id → key the store by it too
            store[d["$id"]] = d
    with warnings.catch_warnings():         # RefResolver is deprecated but is the pattern scripts/validate.py uses
        warnings.simplefilter("ignore", DeprecationWarning)
        resolver = jsonschema.RefResolver(base_uri=base, referrer=docs[schema_name], store=store)
    return jsonschema.Draft202012Validator(docs[schema_name], resolver=resolver)


# ── self-test (offline, deterministic, mutation-gated) ────────────────────────────────────────────────────────────
def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    report = build_fixture_session_report(clock=_make_test_clock(), mode="read_only")
    tabs = {t["url"]: t for t in report["tabs"]}
    portal = tabs[_FIX_PORTAL_URL]
    dl = tabs[_FIX_DOWNLOAD_URL]
    ext = tabs[_FIX_EXTERNAL_URL]
    graph = report["tab_graph"]

    checks.append(("tab graph built (3 nodes + opener edges)",
                   len(graph["nodes"]) == 3 and len(graph["edges"]) == 2))
    checks.append(("opener tracked: same-host download page opened by the portal",
                   dl["opener_tab_id"] == portal["tab_id"] and graph["openers"].get(dl["tab_id"]) == portal["tab_id"]))
    checks.append(("opener tracked: external page opened by the portal",
                   ext["opener_tab_id"] == portal["tab_id"]))
    checks.append(("cross-origin transition flagged (portal -> external partner host)",
                   ext["transition_type"] == "cross_origin_transition" and len(graph["cross_origin_transitions"]) == 1
                   and dl["transition_type"] == "same_origin_navigation"))
    checks.append(("portal page_state=login_wall, auth_state=logged_out, side_effect_risk=regulated",
                   portal["page_state"] == "login_wall" and portal["auth_state"] == "logged_out"
                   and portal["side_effect_risk"] == "regulated"))
    checks.append(("download page classified (download_page + PDF/CSV downloads captured)",
                   dl["page_state"] == "download_page" and any(d["ext"] == "pdf" for d in dl["downloads"])))
    checks.append(("every tab has page_state + auth_state + side_effect_risk set (valid enums)",
                   all(t["page_state"] in PAGE_STATES and t["auth_state"] in AUTH_STATES
                       and t["side_effect_risk"] in SIDE_EFFECT_RISKS for t in report["tabs"])))
    checks.append(("dom_hash carried from CapturedArtifact source_hash",
                   all((t["dom_hash"] or "").startswith("sha256:") for t in report["tabs"])
                   and portal["dom_hash"] == portal["evidence_source_hash"]))
    checks.append(("side_effect_attempts recorded but NEVER executed (harness never submits)",
                   len(report["side_effect_attempts"]) >= 1
                   and all(s["executed"] is False for s in report["side_effect_attempts"])))
    checks.append(("network artifacts (openapi + graphql) surfaced from the portal",
                   {na["kind"] for na in report["network_artifacts"]} >= {"openapi", "graphql"}))
    checks.append(("candidate opportunity seeds enumerated (>=8 types incl. safe_submit_gate)",
                   len({s["candidate_type"] for s in report["candidate_primitives"]}) >= 8
                   and any(s["candidate_type"] == "safe_submit_gate" for s in report["candidate_primitives"])))
    checks.append(("report + all tabs candidate-only (serves_truth=false)",
                   report["candidate"] is True and report["serves_truth"] is False
                   and all(t["candidate"] is True and t["serves_truth"] is False for t in report["tabs"])))
    checks.append(("SECRET redaction: no sk-live token survives into the report",
                   "sk-live-DEMOKEYSHOULDNOTLEAK" not in json.dumps(report)))

    # determinism — two fresh deterministic clocks → byte-identical report
    r2 = build_fixture_session_report(clock=_make_test_clock(), mode="read_only")
    checks.append(("deterministic: identical fixture builds byte-for-byte",
                   json.dumps(report, sort_keys=True) == json.dumps(r2, sort_keys=True)))

    # MUTATION micro-check: the classifiers are REAL — flipping the input flips the output
    base_art = {"record_type": ARTIFACT_RECORD_TYPE, "url": "https://x.example.com/", "captured": True,
                "source_hash": "sha256:deadbeef", "trust_tier": "T4",
                "extracted": {"login_wall": True, "readable_text": "please sign in",
                              "side_effect_controls": [{"kind": "form", "action": "/pay", "method": "post"}],
                              "forms": [{"action": "/pay", "method": "post", "fields": []}]}}
    ex_on = _artifact_extract(base_art)
    ex_off = dict(ex_on, login_wall=False, side_effect_controls=[], forms=[])
    checks.append(("mutation gate: login_wall flip changes auth_state; removing controls changes side_effect_risk",
                   classify_auth_state(base_art, ex_on) == "logged_out"
                   and classify_auth_state(base_art, ex_off) != "logged_out"
                   and classify_side_effect_risk(base_art, ex_on) == "regulated"
                   and classify_side_effect_risk(base_art, ex_off) != "regulated"))

    # FALLBACK path — a MINIMAL raw-html row is re-extracted via the harness primitives (uses the mandated imports)
    raw_row = {"record_type": ARTIFACT_RECORD_TYPE, "url": "https://raw.example.com/", "captured": True,
               "source_hash": "sha256:cafe", "trust_tier": "T4",
               "html": "<form action='/x' method='post'><input name='a'></form><input type='password'>"}
    raw_report = build_session_report([raw_row], clock=_make_test_clock(), mode="read_only")
    raw_tab = raw_report["tabs"][0]
    checks.append(("dual-shape: raw html row re-extracted (browser_extract_forms + browser_detect_login_wall)",
                   raw_tab["n_forms"] >= 1 and raw_tab["page_state"] == "login_wall"
                   and raw_tab["auth_state"] == "logged_out"))

    # POPUP micro-check: cross-origin auth-shaped child = popup; same-origin child = not
    popup_child = {"record_type": ARTIFACT_RECORD_TYPE, "url": "https://idp.example.net/oauth2/authorize",
                   "captured": True, "source_hash": "sha256:aa", "trust_tier": "T4",
                   "extracted": {"login_wall": True, "readable_text": "sign in", "links_sample": []}}
    opener = {"record_type": ARTIFACT_RECORD_TYPE, "url": "https://app.example.com/", "captured": True,
              "source_hash": "sha256:bb", "trust_tier": "T4",
              "extracted": {"login_wall": False, "readable_text": "home",
                            "links_sample": ["https://idp.example.net/oauth2/authorize",
                                             "https://app.example.com/help"]}}
    same_child = {"record_type": ARTIFACT_RECORD_TYPE, "url": "https://app.example.com/help", "captured": True,
                  "source_hash": "sha256:cc", "trust_tier": "T4",
                  "extracted": {"login_wall": False, "readable_text": "help", "links_sample": []}}
    prep = build_session_report([opener, popup_child, same_child], clock=_make_test_clock(), mode="read_only")
    ptabs = {t["url"]: t for t in prep["tabs"]}
    checks.append(("popup detection: cross-origin auth child flagged popup; same-origin child not",
                   ptabs["https://idp.example.net/oauth2/authorize"]["is_popup"] is True
                   and ptabs["https://idp.example.net/oauth2/authorize"]["tab_id"] in prep["tab_graph"]["popups"]
                   and ptabs["https://app.example.com/help"]["is_popup"] is False))

    # DUPLICATE micro-check: two artifacts with the same DOM digest → one flagged duplicate of the other
    dup_a = {"record_type": ARTIFACT_RECORD_TYPE, "url": "https://d.example.com/a", "captured": True,
             "source_hash": "sha256:same", "trust_tier": "T4", "extracted": {"readable_text": "x", "links_sample": []}}
    dup_b = dict(dup_a, url="https://d.example.com/b")
    dup_report = build_session_report([dup_a, dup_b], clock=_make_test_clock(), mode="read_only")
    checks.append(("duplicate-tab detection: identical DOM digest grouped",
                   len(dup_report["tab_graph"]["duplicate_groups"]) == 1
                   and any(t["is_duplicate_of"] for t in dup_report["tabs"])))

    # SCHEMA conformance (Draft 2020-12; cross-file $ref to tab_state resolved) + enum single-source drift gate
    schema_ok = True
    enum_ok = True
    try:
        _make_validator("browser_session_report.schema.json").validate(report)
        sess_schema = _load_schema("browser_session_report.schema.json")
        tab_schema = _load_schema("tab_state.schema.json")
        enum_ok = (set(sess_schema["properties"]["mode"]["enum"]) == set(MODES)
                   and set(tab_schema["properties"]["page_state"]["enum"]) == set(PAGE_STATES)
                   and set(tab_schema["properties"]["auth_state"]["enum"]) == set(AUTH_STATES)
                   and set(tab_schema["properties"]["side_effect_risk"]["enum"]) == set(SIDE_EFFECT_RISKS))
    except Exception as exc:  # noqa: BLE001
        schema_ok = False
        print(f"  [..] schema validation error: {type(exc).__name__}: {exc}")
    checks.append(("report validates against browser_session_report.schema.json (+ tab_state $ref)", schema_ok))
    checks.append(("enum single-source: python constants == schema enums (drift gate)", enum_ok))

    # round-trip write to a TEMP path (no repo data-dir pollution during proofs)
    import tempfile
    tmp = Path(tempfile.mkdtemp()) / "browser_session_reports.jsonl"
    write_session_reports([report], tmp)
    wrote_ok = tmp.exists() and json.loads(tmp.read_text().splitlines()[0])["session_id"] == report["session_id"]
    checks.append(("write round-trip (jsonl append) works", wrote_ok))

    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    print(("PASS" if ok else "FAIL") + " - browser_session_report: CapturedArtifact rows -> browser_session_report "
          f"with a tab graph ({report['stats']['n_tabs']} tabs, {report['stats']['n_cross_origin_transitions']} "
          f"cross-origin, {report['stats']['n_candidate_primitives']} candidate seeds), page_state/auth_state/"
          "side_effect_risk classified, candidate-only (serves_truth=false), deterministic + schema-valid.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build a browser_session_report (+ tab graph) from CapturedArtifact rows.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--demo", action="store_true", help="build the bundled fixture report and print its summary")
    ap.add_argument("--from-artifacts", metavar="JSONL", help="a captured_artifacts.jsonl from the harness")
    ap.add_argument("--mode", default="read_only", choices=list(MODES))
    ap.add_argument("--out", metavar="JSONL", help="output path (default the browser_reports data dir)")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    import datetime as _dt
    clock = lambda: _dt.datetime.now(_dt.timezone.utc).timestamp()  # noqa: E731

    if args.demo:
        report = build_fixture_session_report(clock=clock, mode=args.mode)
        print(json.dumps(report["stats"], indent=2, sort_keys=True))
        return 0
    if args.from_artifacts:
        rows = [json.loads(ln) for ln in Path(args.from_artifacts).read_text().splitlines() if ln.strip()]
        report = build_session_report(rows, clock=clock, mode=args.mode)
        out = write_session_reports([report], Path(args.out) if args.out else None)
        print(f"built 1 session report ({report['stats']['n_tabs']} tabs, "
              f"{report['stats']['n_candidate_primitives']} candidate seeds) -> {out}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
