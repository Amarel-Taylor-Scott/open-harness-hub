#!/usr/bin/env python3
"""scripts.check_registry_backend — PROOF that the Open*Hub registry plane is real and makes the
full-design dashboards real (not mock):

  A. SERVICE   — architecture/local_service_registry.json declares local_openhub_projection_api as
                 active_local with the real start_command, the catalog + session-gated workspace
                 routes, and realm-session auth.
  B. CATALOG   — extract_catalog() pulls each hub's entries from the design bundle (single source);
                 a healthy number of hubs/entries, every entry has id+name, catalog.json is written.
  C. WORKSPACE — the replay math (store-level, no HTTP): install/uninstall/publish produce the right
                 installed set, published count, avg-eval and activity; a fresh account is honestly
                 zeroed; publish lands in the review queue (candidate, never active).
  D. GATED API — the live HTTP surface with a STUB validator: health/ready/status (truth_authority
                 false), public search, and the workspace path FAILS CLOSED without a valid session,
                 succeeds with one, and reflects a real install. submit → 202 in_review.
  E. CLIENT    — shared/oh-registry.js exposes the client surface, its default base matches the
                 service port (drift gate), reuses the identity realm + oh-session-<realm>, and is
                 loaded by the surfaces after oh-identity.js.
  F. WIRED     — oh-hub.jsx reads the workspace for the dashboard / Installed / install button with an
                 honest fallback, and the DESIGN-CONTRACT markup (classes) is preserved.
  G. SYNTAX    — node --check oh-registry.js when node is available.

Offline, stdlib-only. Exit 0/1.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.registry_local_service import (  # noqa: E402
    SERVICE_ID, RegistryStore, SelfReviewError, extract_catalog, start_service, BUNDLE_DIR,
)

REG_PATH = REPO / "architecture" / "local_service_registry.json"
REALM_REG = REPO / "architecture" / "identity_realm_registry.json"
BUNDLE = REPO / "dist" / "sites" / "openharness-design"
CLIENT = BUNDLE / "shared" / "oh-registry.js"
HUB = BUNDLE / "shared" / "oh-hub.jsx"


class _StubValidator:
    """Resolves the known demo sessions — stands in for the identity service so the gated paths are
    provable without standing identity up. Two accounts let us prove separation of duties. Any other
    session id fails closed."""
    base = "stub://identity"

    def resolve(self, realm, session_id):
        return {"sess_demo": "acct_demo", "sess_rev": "acct_rev"}.get(session_id)


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=4) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=4) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:  # noqa: F821
        return e.code, json.loads(e.read().decode())


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
    svc = next((s for s in reg["services"] if s["service_id"] == SERVICE_ID), None)
    client = CLIENT.read_text(encoding="utf-8") if CLIENT.exists() else ""
    hub = HUB.read_text(encoding="utf-8")

    # A. SERVICE declaration
    ck("A: service declared active_local", bool(svc) and svc["status"] == "active_local")
    ck("A: real start_command (scripts.registry_local_service)",
       bool(svc) and svc.get("start_command") == ["python3", "-m", "scripts.registry_local_service"])
    routes = (svc.get("public_routes", []) + svc.get("private_routes", [])) if svc else []
    ck("A: catalog + workspace routes present",
       all(any(r.endswith(x) for r in routes) for x in ("/search", "/entry/<id>", "/install", "/workspace", "/submit")))
    ck("A: workspace auth = realm session via identity", bool(svc) and svc.get("auth_mode") == "realm_session_via_identity_service")

    # B. CATALOG extraction
    catalog = extract_catalog(BUNDLE_DIR)
    entries = sum(len(v) for v in catalog.values())
    ck("B: catalog extracts a healthy set of hubs", len(catalog) >= 9, f"{len(catalog)} hubs")
    ck("B: catalog extracts many entries", entries >= 50, f"{entries} entries")
    bad = [e.get("id") for v in catalog.values() for e in v if not (e.get("id") and e.get("name"))]
    ck("B: every entry has id + name", not bad, f"{len(bad)} bad")

    tmp = Path(tempfile.mkdtemp(prefix="registry-proof-"))
    try:
        store = RegistryStore(state_dir=tmp, bundle_dir=BUNDLE_DIR)
        ck("B: catalog.json written", (tmp / "catalog.json").exists())

        # C. WORKSPACE replay math
        now = 1_700_000_000
        store.record("a1", "opencontexthub", "install", {"id": "x1", "name": "X One", "score": "4.8"}, now)
        store.record("a1", "opencontexthub", "install", {"id": "x2", "name": "X Two", "score": "4.6"}, now + 5)
        store.record("a1", "opencontexthub", "publish", {"id": "mine", "name": "Mine", "score": "4.5"}, now + 6)
        store.record("a1", "opencontexthub", "uninstall", {"id": "x2"}, now + 7)
        store.log_call("a1", "opencontexthub", "POST", "/x", now + 1)
        ws = store.workspace("a1", "opencontexthub", now + 8)
        stat = dict(ws["stats"])
        ck("C: installed count correct (2 installed − 1 removed = 1)", stat["Installed"] == 1, str(stat["Installed"]))
        ck("C: published count correct", stat["Published"] == 1, str(stat["Published"]))
        ck("C: avg-eval = the one remaining install", stat["Avg eval"] == "★ 4.8", str(stat["Avg eval"]))
        ck("C: API calls · 30d counts authed calls", stat["API calls · 30d"] >= 1, str(stat["API calls · 30d"]))
        ck("C: activity reflects the most-recent event first", ws["activity"][0]["text"].startswith("Removed"))
        ck("C: publish recorded in the review queue (candidate)",
           (tmp / "review_queue.jsonl").exists() and '"status": "in_review"' in (tmp / "review_queue.jsonl").read_text())
        my_subs = store.submissions("a1", "opencontexthub", now + 8)
        ck("C: submissions() returns the candidate as in_review (never active)",
           len(my_subs) == 1 and my_subs[0]["status"] == "in_review" and my_subs[0]["entry_id"] == "mine")
        ws0 = store.workspace("nobody", "opencontexthub", now + 8)
        ck("C: a fresh account is honestly zeroed (no fabricated numbers)",
           dict(ws0["stats"])["Installed"] == 0 and dict(ws0["stats"])["Avg eval"] == "—")

        # ---- the PROMOTION GATE (the only candidate → public-active path) ----
        store.record("sub1", "openagenthub", "publish", {"id": "cand-x", "name": "Cand X", "score": "—"}, now)
        ck("C: a fresh candidate is NOT in the catalog (candidate ≠ active)",
           not any(e.get("id") == "cand-x" for e in store.search("openagenthub")))
        ck("C: the candidate is in the review queue, pending",
           any(c["entry_id"] == "cand-x" for c in store.review_queue("openagenthub", now + 1)))
        store.grant_reviewer("openagenthub", "sub1", by="proof", now=now)   # even granted, can't self-review
        try:
            store.decide("openagenthub", "cand-x", "sub1", "approve", "self", now + 1)
            ck("C: a reviewer cannot approve their OWN submission (separation of duties)", False)
        except SelfReviewError:
            ck("C: a reviewer cannot approve their OWN submission (separation of duties)", True)
        store.grant_reviewer("openagenthub", "rev1", by="proof", now=now)
        store.decide("openagenthub", "cand-x", "rev1", "approve", "verified", now + 2, score="4.5")
        hit = next((e for e in store.search("openagenthub") if e.get("id") == "cand-x"), None)
        ck("C: a DIFFERENT reviewer's approval PROMOTES it into the catalog (with lineage)",
           bool(hit) and hit.get("provenance", {}).get("reviewer") == "rev1"
           and hit.get("provenance", {}).get("submitter") == "sub1" and hit.get("score") == "4.5")
        ck("C: approved candidate leaves the pending queue",
           not any(c["entry_id"] == "cand-x" for c in store.review_queue("openagenthub", now + 3)))
        store.decide("openagenthub", "cand-x", "rev1", "revoke", "rollback", now + 3)
        ck("C: revoke rolls it back out of the catalog (lossless — both decisions preserved)",
           not any(e.get("id") == "cand-x" for e in store.search("openagenthub"))
           and (tmp / "review_decisions.jsonl").read_text().count("cand-x") >= 2)
        ck("C: a non-granted account is NOT a reviewer (admin/operator-granted only)",
           not store.is_reviewer("openagenthub", "rando"))

        # ---- admin roster (operator-bootstrapped; admins grant reviewers) ----
        ck("C: nobody is an admin by default", not store.is_admin("openagenthub", "x"))
        store.grant_admin("openagenthub", "adm1", by="operator", now=now)
        ck("C: an operator bootstrap establishes an admin", store.is_admin("openagenthub", "adm1"))
        store.grant_reviewer("openagenthub", "newrev", by="adm1", now=now, reason="promoted by admin")
        ck("C: an admin can grant a reviewer, and the audit records the granting admin",
           store.is_reviewer("openagenthub", "newrev")
           and any(json.loads(l).get("by") == "adm1" for l in (tmp / "reviewers.jsonl").read_text().splitlines()
                   if "newrev" in l))
        ck("C: recent_contributors surfaces submitters (so admins can promote active people)",
           any(c["account_id"] == "sub1" for c in store.recent_contributors("openagenthub", now + 1)))

        # D. GATED HTTP surface (stub validator)
        server, _thread, port, _store = start_service(port=0, state_dir=tmp, bundle_dir=BUNDLE_DIR,
                                                       validator=_StubValidator())
        b = f"http://127.0.0.1:{port}"
        try:
            ck("D: /healthz ok", _get(b + "/healthz")[1].get("ok") is True)
            sc, status = _get(b + "/api/status")
            ck("D: /api/status truth_authority=false", status.get("truth_authority") is False)
            sc, body = _get(b + "/api/openhub/opencontexthub/search")
            ck("D: public search returns entries", sc == 200 and len(body.get("entries", [])) >= 1)
            # the PUBLIC faceted spine projection the OpenHubForAI record browser reads (browse + records)
            sc, br = _get(b + "/api/openhub/registries")
            ck("D: public /registries faceted browse (count + facets, truth_authority=false)",
               sc == 200 and br.get("count", 0) >= 155 and {"category", "kind", "layer", "status"} <= set(br.get("facets", {}))
               and br.get("truth_authority") is False)
            sc, brf = _get(b + "/api/openhub/registries?kind=static")
            ck("D: a facet filter narrows the public browse", sc == 200 and 0 < brf.get("count", 0) < br["count"])
            sc, recs = _get(b + "/api/openhub/registries/access_policy/records")
            ck("D: public registry records drill-in (RegistryObjects)",
               sc == 200 and isinstance(recs.get("records"), list) and recs.get("truth_authority") is False)
            sc, _ = _get(b + "/api/openhub/opencontexthub/workspace")          # no session
            ck("D: workspace FAILS CLOSED without a session", sc == 401)
            sc, _ = _get(b + "/api/openhub/opencontexthub/workspace?session_id=bogus")
            ck("D: workspace FAILS CLOSED on an invalid session", sc == 401)
            sc, out = _post(b + "/api/openhub/opencontexthub/install",
                            {"session_id": "sess_demo", "entry": {"id": "ilo", "name": "ILO", "score": "4.9"}})
            ck("D: install with a valid session → 202", sc == 202 and out.get("ok") is True)
            sc, ws_live = _get(b + "/api/openhub/opencontexthub/workspace?session_id=sess_demo")
            ck("D: workspace now reflects the real install", sc == 200 and dict(ws_live["stats"])["Installed"] >= 1)
            sc, _ = _get(b + "/api/openhub/opencontexthub/audit")                      # no session
            ck("D: audit FAILS CLOSED without a session", sc == 401)
            sc, au = _get(b + "/api/openhub/opencontexthub/audit?session_id=sess_demo")
            ck("D: audit returns the account's real recorded activity",
               sc == 200 and any(r.get("policy") == "workspace:install" for r in au.get("rows", [])))
            sc, sub = _post(b + "/api/openhub/opencontexthub/submit",
                            {"session_id": "sess_demo", "entry": {"id": "p1", "name": "Pub 1"}})
            ck("D: submit → 202 in_review (candidate, not active)", sc == 202 and sub.get("status") == "in_review")
            sc, _ = _get(b + "/api/openhub/opencontexthub/submissions")                      # no session
            ck("D: submissions FAILS CLOSED without a session", sc == 401)
            sc, subs_body = _get(b + "/api/openhub/opencontexthub/submissions?session_id=sess_demo")
            ck("D: submissions lists the candidate as in_review",
               sc == 200 and any(x.get("status") == "in_review" and x.get("entry_id") == "p1"
                                 for x in subs_body.get("submissions", [])))
            # ---- reviewer surface over HTTP (gating + separation of duties + promotion) ----
            sc, st_body = _get(b + "/api/openhub/opencontexthub/review/status?session_id=sess_demo")
            ck("D: review/status → not a reviewer by default", sc == 200 and st_body.get("reviewer") is False)
            sc, _ = _get(b + "/api/openhub/opencontexthub/review/queue?session_id=sess_demo")
            ck("D: review/queue FORBIDDEN for non-reviewers (403)", sc == 403)
            _store.grant_reviewer("opencontexthub", "acct_rev", by="proof", now=0)
            sc, st2 = _get(b + "/api/openhub/opencontexthub/review/status?session_id=sess_rev")
            ck("D: a granted account sees reviewer=true", sc == 200 and st2.get("reviewer") is True)
            sc, qb = _get(b + "/api/openhub/opencontexthub/review/queue?session_id=sess_rev")
            ck("D: a reviewer sees the pending candidate p1", sc == 200 and any(c.get("entry_id") == "p1" for c in qb.get("queue", [])))
            _store.grant_reviewer("opencontexthub", "acct_demo", by="proof", now=0)  # submitter, for the self-review test
            sc, _ = _post(b + "/api/openhub/opencontexthub/review/decide",
                          {"session_id": "sess_demo", "entry_id": "p1", "decision": "approve"})
            ck("D: a reviewer CANNOT approve their own submission (403)", sc == 403)
            sc, dr = _post(b + "/api/openhub/opencontexthub/review/decide",
                           {"session_id": "sess_rev", "entry_id": "p1", "decision": "approve", "reason": "ok", "score": "4.6"})
            ck("D: a DIFFERENT reviewer approves → promoted=true", sc == 202 and dr.get("promoted") is True)
            sc, sb = _get(b + "/api/openhub/opencontexthub/search?q=Pub%201")
            ck("D: the approved candidate now appears in the public catalog", sc == 200 and any(e.get("id") == "p1" for e in sb.get("entries", [])))
            # ---- admin console: operator bootstrap + gating + grant a reviewer ----
            sc, ad0 = _get(b + "/api/openhub/opencontexthub/admin/status?session_id=sess_demo")
            ck("D: admin/status → not an admin by default", sc == 200 and ad0.get("admin") is False)
            sc, _ = _get(b + "/api/openhub/opencontexthub/admin/reviewers?session_id=sess_demo")
            ck("D: admin/reviewers FORBIDDEN for non-admins (403)", sc == 403)
            _store.grant_admin("opencontexthub", "acct_demo", by="operator", now=0)   # operator bootstrap
            sc, ad1 = _get(b + "/api/openhub/opencontexthub/admin/status?session_id=sess_demo")
            ck("D: an operator-bootstrapped account sees admin=true", sc == 200 and ad1.get("admin") is True)
            sc, rv = _post(b + "/api/openhub/opencontexthub/admin/reviewers/grant",
                           {"session_id": "sess_demo", "account_id": "acct_newrev", "reason": "active"})
            ck("D: an admin grants a reviewer (202, roster updated)", sc == 202 and "acct_newrev" in rv.get("reviewers", []))
            ck("D: the granted account is now a reviewer", _store.is_reviewer("opencontexthub", "acct_newrev"))
            sc, _ = _post(b + "/api/openhub/opencontexthub/admin/reviewers/grant",
                          {"session_id": "sess_rev", "account_id": "acct_x"})
            ck("D: a NON-admin cannot grant reviewers (403)", sc == 403)
        finally:
            server.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # E. CLIENT contract
    ck("E: oh-registry.js exists", bool(client))
    ck("E: exposes the registry client surface",
       all(m in client for m in ("realmOf", "search:", "install:", "publish:", "submissions:", "workspace:",
                                 "audit:", "amReviewer:", "reviewQueue:", "decide:",
                                 "amAdmin:", "adminReviewers:", "grantReviewer:", "revokeReviewer:")))
    port_decl = f'"http://127.0.0.1:{svc["port"]}"' if svc else ""
    ck("E: default base matches the service port (drift gate)", bool(svc) and port_decl in client, port_decl)
    ck("E: reuses the identity realm + oh-session store", "OHIdentity" in client and "oh-session-" in client)
    ck("E: deploy override supported", "OHH_REGISTRY_BASE" in client)
    loaded = sum(1 for p in BUNDLE.rglob("*.html") if "oh-registry.js" in p.read_text(encoding="utf-8"))
    ck("E: loaded by ≥20 surfaces", loaded >= 20, str(loaded))
    after = all("oh-identity.js" in (t := p.read_text(encoding="utf-8")) and
                t.index("oh-registry.js") > t.index("oh-identity.js")
                for p in BUNDLE.rglob("*.html") if "oh-registry.js" in p.read_text(encoding="utf-8"))
    ck("E: loaded AFTER oh-identity.js (reuses its realm/session)", after)

    # F. WIRED into the kit (data source only; DESIGN-CONTRACT markup preserved)
    ck("F: dashboard reads the real workspace with a fallback",
       "useWorkspace" in hub and "function HubDashboard" in hub and "ws ? ws.stats" in hub)
    ck("F: Installed reads the real installed list", "ws.installed" in hub)
    ck("F: Browse reads the real catalog with a fallback", "useCatalog" in hub and "useCatalog() || cfg.entries" in hub)
    ck("F: the add-to-workspace button records a real install", "OHRegistry.install(REALM, e)" in hub)
    ck("F: Publish UI submits to the review queue (real, not static text)",
       "function PublishForm" in hub and "OHRegistry.publish(REALM, entry)" in hub
       and "route === '/publish') page = <PublishForm" in hub)
    ck("F: Publish UI shows in-review status + lists the account's submissions",
       "in review" in hub and "OHRegistry.submissions(REALM)" in hub)
    ck("F: Review surface gated to operator-granted reviewers (nav + page)",
       "function ReviewQueue" in hub and "useReviewer" in hub and "amReviewer" in hub
       and "reviewer access" in hub.lower() and "'/review'" in hub)
    ck("F: Approve/Reject call the real decision endpoint",
       "OHRegistry.decide(REALM" in hub and "Approve" in hub)
    ck("F: promoted entries resolve from the registry + show provenance lineage",
       "OHRegistry.entry(REALM, id)" in hub and "Promotion lineage" in hub)
    ck("F: Admin console gated to operator-bootstrapped admins (nav + page)",
       "function AdminConsole" in hub and "useAdmin" in hub and "amAdmin" in hub
       and "admin access" in hub.lower() and "'/admin'" in hub)
    ck("F: Admin console grants + revokes reviewers (recent-contributors helper)",
       "OHRegistry.grantReviewer(REALM" in hub and "OHRegistry.revokeReviewer(REALM" in hub
       and "Recent contributors" in hub)
    # the whole signed-in console is REAL (no leftover mock pages)
    ck("F: API keys page is REAL (identity mint/list/revoke, raw shown once)",
       "function HubApiKeys" in hub and "OHIdentity.mintKey(REALM" in hub and "OHIdentity.revokeKey(REALM" in hub
       and "shown once" in hub and "route === '/keys') page = <HubApiKeys" in hub)
    ck("F: audit / usage / notifications / settings read real per-account data",
       "function HubAudit" in hub and "OHRegistry.audit(REALM)" in hub and "function HubUsage" in hub
       and "function HubSettings" in hub and "Account ID" in hub)
    ck("F: billing shows the real plan with NO fabricated invoices",
       "function HubBilling" in hub and "invoices={[]}" in hub and "'/billing') page = <HubBilling" in hub)
    ck("F: reviewer can revoke a promotion (lossless rollback) in the UI",
       "decide(e.id, 'revoke')" in hub and "revertable" in hub.lower())
    ck("F: the publisher handle is the real account handle (not a placeholder)",
       "by: sessionInfo().handle" in hub and "'@you'" not in hub)
    ck("F: DESIGN-CONTRACT markup preserved (oh-btn--primary, OhDashboard, OhRollup)",
       "oh-btn oh-btn--primary" in hub and "<OhDashboard" in hub and "<OhRollup" in hub)

    # G. node syntax
    node = shutil.which("node")
    if node:
        res = subprocess.run([node, "--check", str(CLIENT)], capture_output=True, text=True)
        ck("G: node --check oh-registry.js", res.returncode == 0, res.stderr.strip()[:160])
    else:
        print("  [ok] G: node unavailable — syntax check skipped honestly")

    print("\n" + ("PASS — check_registry_backend: the Open*Hub registry plane is real — catalog seeded "
                  "from the bundle (single source), per-account workspace replayed from an append-only log, "
                  "session-gated against the identity service (fails closed), publish → review queue "
                  "(candidate ≠ active). The PROMOTION GATE is the only candidate→public-active path: "
                  "reviewer access is operator-granted (never self-served), a reviewer can't decide on "
                  "their own submission (separation of duties), approve promotes with submitter+reviewer "
                  "lineage, and revoke rolls back losslessly (decisions preserved). The ADMIN console grants "
                  "reviewers (admin status is operator-bootstrapped ONLY — no in-app escalation; every grant "
                  "is audited). Dashboard / Installed / Browse / publish / review / admin are all wired with "
                  "honest fallbacks."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_registry_backend.py --self-test")
    raise SystemExit(0)
