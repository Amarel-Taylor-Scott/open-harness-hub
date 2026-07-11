#!/usr/bin/env python3
"""scripts.buildout_forge_large — a LARGE BuildoutForge genome: a real, multi-MODULE back-office operations HTTP
API is BUILT, BOOTED as a running service, and verified by a HIDDEN HTTP oracle that drives ~27 real endpoints
(auth, RBAC, idempotent writes, pagination/filter/sort, an audit trail, CSV export, and a signature-verified
payment webhook). This is the big-surface companion to scripts/buildout_forge.py: many small modules → a genuinely
large build → realistic token output → lots of independently-reusable pure primitives to decompose.

Owner (2026-07-09): "generate a SaaS that does X ... build it out ... run against a hidden oracle ... decompose
into primitives ... rebuild with primitives injected ... measure real lift." REAL means executed: this module
starts the built app in a subprocess and drives it over real HTTP (realism level B6). Nothing passes on
plausibility. The genome is NON-INSURANCE (generic B2B operations — vendors + purchase orders), matching the
repo's ban on insurance / claims-adjacent verticals. BENCHMARK_KIND=real_project_buildout; candidate=true /
serves_truth=false.

The genome dict shape is identical to scripts/buildout_forge._GENOMES so it plugs into scripts/buildout_forge_ab
(product_family, prompt_style, stack, solution_file, http_oracle, realism_level, goal, primitive_targets, good,
bad, stub). The reference GOOD build is 11 stdlib-only files; the pure primitives it yields are listed in
primitive_targets.

Isolation note: a built app does REAL I/O (binds a localhost socket) so the primitive I/O-ban sandbox does NOT
apply here; buildouts run in an ephemeral temp workspace with a wall-clock timeout. The self-test here runs
TRUSTED reference code; UNTRUSTED (model-written) buildouts in the live lane must additionally run under
container/network isolation.

    python3 scripts/buildout_forge_large.py --self-test
    python3 scripts/buildout_forge_large.py --run --solution good   # boot the reference build + run the oracle
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402  (the oracle RUNNER + build booter, not model code)
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"  # no_proxy_gate: passes only when the built app BOOTS + a hidden HTTP oracle passes
ARTIFACT_DIR_REL = "data/dev-intel/buildout_forge"
BUILDOUT_REALISM = "B6"  # built repo boots locally AND a hidden HTTP oracle exercises real endpoints
GENOME_ID = "backoffice_ops_api__stdlib_http__v0"
_SHARED_SECRET = "backoffice-ops-secret-v0"  # single source for the demo secret (config.py + the oracle both hold it)

# ── the hidden HTTP oracle: launch the built app on a free port, drive ~27 real endpoints, check behavior. ────
#    It is the PARENT that boots `app.py` as a child and probes it; the app is never shown these fixtures. The
#    machinery (free-port pick, boot-poll with retries, terminate-in-finally, DEVNULL child stdio, one ORACLE
#    line) is copied verbatim from scripts/buildout_forge.py; only the checks are bigger. The oracle holds the
#    shared secret because it plays the external caller that signs webhooks + would sign tokens.
_HTTP_ORACLE_DRIVER = r'''
import json, os, sys, socket, subprocess, time, http.client, hashlib, hmac

SECRET = "backoffice-ops-secret-v0"   # shared secret the external caller also holds (mirrors config.py)


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _req(port, method, path, body=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    payload = json.dumps(body) if body is not None else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    c.request(method, path, body=payload, headers=h)
    r = c.getresponse()
    raw = r.read().decode() or "{}"
    c.close()
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {}
    return r.status, parsed, raw


def _bearer(tok):
    return {"Authorization": "Bearer " + (tok or "")}


port = _free_port()
proc = subprocess.Popen([sys.executable, "app.py", "--port", str(port)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.getcwd())
checks = {}
try:
    ready = False
    for _ in range(50):                                   # up to ~5s for the server to boot
        try:
            if _req(port, "GET", "/health")[0] == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.1)
    checks["server_boots"] = ready
    if ready:
        # ---- health (no auth) ----
        st, b, _ = _req(port, "GET", "/health")
        checks["health_ok"] = (st == 200 and b.get("healthy") is True and b.get("status") == "ok")

        # ---- auth: token issuance + role + failure ----
        st, b, _ = _req(port, "POST", "/auth/token", {"user": "admin", "password": "admin"})
        admin_tok = b.get("token") if isinstance(b, dict) else None
        checks["auth_admin_200"] = (st == 200 and b.get("role") == "admin" and bool(admin_tok))
        st, b, _ = _req(port, "POST", "/auth/token", {"user": "viewer", "password": "viewer"})
        viewer_tok = b.get("token") if isinstance(b, dict) else None
        checks["auth_viewer_200"] = (st == 200 and b.get("role") == "viewer" and bool(viewer_tok))
        st, b, _ = _req(port, "POST", "/auth/token", {"user": "admin", "password": "WRONG"})
        checks["auth_bad_401"] = (st == 401)

        A = _bearer(admin_tok)
        V = _bearer(viewer_tok)

        # ---- protected routes require a valid bearer ----
        st, b, _ = _req(port, "GET", "/vendors")
        checks["no_token_401"] = (st == 401)
        st, b, _ = _req(port, "GET", "/vendors", headers=_bearer("garbage.token"))
        checks["bad_token_401"] = (st == 401)

        # ---- vendor create / validation / rbac / idempotency ----
        st, b, _ = _req(port, "POST", "/vendors",
                        {"vendor_id": "V1", "name": "Acme", "email": "acme@example.com"}, headers=A)
        checks["vendor_create_201"] = (st == 201 and b.get("vendor_id") == "V1")
        st, b, _ = _req(port, "POST", "/vendors",
                        {"vendor_id": "V1", "name": "Acme", "email": "acme@example.com"}, headers=A)
        checks["vendor_dup_200"] = (st == 200 and b.get("vendor_id") == "V1")
        st, b, _ = _req(port, "POST", "/vendors", {"vendor_id": "V2", "email": "v2@example.com"}, headers=A)
        checks["vendor_missing_name_400"] = (st == 400 and b.get("error") == "validation"
                                             and "name" in (b.get("fields") or []))
        st, b, _ = _req(port, "POST", "/vendors",
                        {"vendor_id": "V3", "name": "Bad", "email": "not-an-email"}, headers=A)
        checks["vendor_bad_email_400"] = (st == 400 and "email" in (b.get("fields") or []))
        st, b, _ = _req(port, "POST", "/vendors",
                        {"vendor_id": "VX", "name": "ViewerBlocked", "email": "vx@example.com"}, headers=V)
        checks["vendor_viewer_403"] = (st == 403)

        # seed two more real vendors for list/filter/sort/export (admin)
        _req(port, "POST", "/vendors",
             {"vendor_id": "V2", "name": "Beta Industries", "email": "beta@example.com"}, headers=A)
        _req(port, "POST", "/vendors",
             {"vendor_id": "V3", "name": "Acme Corp", "email": "corp@example.com"}, headers=A)

        # ---- vendor get / 404 ----
        st, b, _ = _req(port, "GET", "/vendors/V1", headers=A)
        checks["vendor_get_200"] = (st == 200 and b.get("name") == "Acme")
        st, b, _ = _req(port, "GET", "/vendors/NOPE", headers=A)
        checks["vendor_404"] = (st == 404)

        # ---- list: total / pagination / filter / sort ----
        st, b, _ = _req(port, "GET", "/vendors", headers=A)
        checks["list_total"] = (st == 200 and b.get("total") == 3 and len(b.get("items", [])) == 3)
        st, b, _ = _req(port, "GET", "/vendors?page=1&size=2", headers=A)
        checks["list_pagination"] = (st == 200 and b.get("page") == 1 and b.get("size") == 2
                                     and len(b.get("items", [])) == 2)
        st, b, _ = _req(port, "GET", "/vendors?q=acme", headers=A)
        items = b.get("items", []) if isinstance(b, dict) else []
        checks["list_filter_q"] = (st == 200 and len(items) == 2
                                   and all("acme" in it.get("name", "").lower() for it in items))
        st, b, _ = _req(port, "GET", "/vendors?sort=name", headers=A)
        names = [it.get("name", "") for it in b.get("items", [])] if isinstance(b, dict) else []
        checks["list_sort_name"] = (st == 200 and names == sorted(names) and len(names) == 3)

        # ---- purchase orders: create / idempotency / validation ----
        st, b, _ = _req(port, "POST", "/purchase_orders",
                        {"po_id": "PO1", "vendor_id": "V1", "amount": 250.5, "idempotency_key": "k1"}, headers=A)
        checks["po_create_201"] = (st == 201 and b.get("po_id") == "PO1")
        st, b, _ = _req(port, "POST", "/purchase_orders",
                        {"po_id": "PO1", "vendor_id": "V1", "amount": 250.5, "idempotency_key": "k1"}, headers=A)
        checks["po_idempotent_200"] = (st == 200 and b.get("po_id") == "PO1")
        st, b, _ = _req(port, "POST", "/purchase_orders",
                        {"po_id": "PO2", "vendor_id": "GHOST", "amount": 10, "idempotency_key": "k2"}, headers=A)
        checks["po_bad_vendor_400"] = (st == 400 and "vendor_id" in (b.get("fields") or []))
        st, b, _ = _req(port, "POST", "/purchase_orders",
                        {"po_id": "PO3", "vendor_id": "V1", "amount": -5, "idempotency_key": "k3"}, headers=A)
        checks["po_bad_amount_400"] = (st == 400 and "amount" in (b.get("fields") or []))

        # ---- audit: admin sees mutation events; viewer forbidden ----
        st, b, _ = _req(port, "GET", "/audit", headers=A)
        aitems = b.get("items", []) if isinstance(b, dict) else []
        checks["audit_admin_200"] = (st == 200 and len(aitems) >= 1
                                     and all(set(("action", "entity", "id")) <= set(e) for e in aitems))
        st, b, _ = _req(port, "GET", "/audit", headers=V)
        checks["audit_viewer_403"] = (st == 403)

        # ---- csv export: header + a known vendor row ----
        st, b, raw = _req(port, "GET", "/vendors/export.csv", headers=A)
        checks["csv_export_200"] = (st == 200 and "vendor_id,name,email" in raw and "V1,Acme" in raw)

        # ---- webhook: valid HMAC signature 200; wrong signature 401 ----
        wh_body = {"event": "payment.succeeded", "amount": 4200}
        wh_raw = json.dumps(wh_body)
        wh_sig = hmac.new(SECRET.encode(), wh_raw.encode(), hashlib.sha256).hexdigest()
        st, b, _ = _req(port, "POST", "/webhooks/payment", wh_body, headers={"X-Signature": wh_sig})
        checks["webhook_valid_200"] = (st == 200 and b.get("ok") is True)
        st, b, _ = _req(port, "POST", "/webhooks/payment", wh_body, headers={"X-Signature": "deadbeef"})
        checks["webhook_bad_sig_401"] = (st == 401)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
oracle_pass = len(checks) >= 20 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

# ── reference GOOD buildout: a real MULTI-MODULE back-office ops service (stdlib only → boots here, no deps). ──
#    Each module is a small, independently-reusable slice; app.py is the router/server that wires them together.

_MOD_CONFIG = r'''# config — single source of the shared secret + the demo user directory. Both are mirrored by the hidden
# oracle (the external caller), which is inherent to HMAC auth: signer and verifier hold the same secret.
SECRET = "backoffice-ops-secret-v0"  # shared HMAC secret for signed tokens + webhook signatures (demo value only)

# user directory: username -> {password, role}. Two demo roles: admin (read+write) and viewer (read-only).
USERS = {
    "admin": {"password": "admin", "role": "admin"},
    "viewer": {"password": "viewer", "role": "viewer"},
}
'''

_MOD_ERRORS = r'''# errors — the single JSON error-body shape + a small catalog of named builders, so every failure path in the
# API emits one consistent {"error": <kind>, ...} envelope instead of ad-hoc dicts scattered across the handlers.


def make_error(kind, **extra):
    # Build a JSON error body: {"error": kind, ...extra}. Extra keys carry detail (e.g. fields=[...] on a 400).
    body = {"error": kind}
    body.update(extra)
    return body


def validation_error(fields):
    # 400 body for a failed validation, naming the offending fields.
    return make_error("validation", fields=fields)


def unauthorized():
    # 401 body: missing or invalid credentials / bearer token.
    return make_error("unauthorized")


def forbidden():
    # 403 body: authenticated, but the caller's role lacks permission for the route.
    return make_error("forbidden")


def not_found():
    # 404 body: no such route or resource.
    return make_error("not_found")


def bad_signature():
    # 401 body: a webhook whose HMAC signature did not verify.
    return make_error("bad_signature")
'''

_MOD_AUTH = r'''# auth — signed-token issuance + verification. A token encodes the user + role and is HMAC-signed with the
# shared SECRET, so a later request can be authenticated WITHOUT any server-side session store (a mini-JWT).
import base64
import hashlib
import hmac

from config import SECRET, USERS


def _sign(payload):
    # hex HMAC-SHA256 of the payload string under the shared secret.
    return hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def issue_token(user, role):
    # Build a signed, self-describing token: base64url("user:role") + "." + hmac-signature.
    payload = f"{user}:{role}"
    body = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"{body}.{_sign(payload)}"


def verify_token(token):
    # Verify a token's signature and return {"user", "role"}, or None if missing / malformed / tampered.
    if not token or "." not in token:
        return None
    body, signature = token.rsplit(".", 1)
    try:
        padding = "=" * (-len(body) % 4)
        payload = base64.urlsafe_b64decode((body + padding).encode()).decode()
    except Exception:
        return None
    if not hmac.compare_digest(_sign(payload), signature):
        return None
    if ":" not in payload:
        return None
    user, role = payload.split(":", 1)
    return {"user": user, "role": role}


def authenticate(user, password):
    # Return the role for valid credentials, else None.
    record = USERS.get(user or "")
    if record and record.get("password") == password:
        return record.get("role")
    return None


def parse_bearer(header):
    # Extract the raw token from an "Authorization: Bearer <token>" header, or None when absent/malformed.
    if not header or not header.startswith("Bearer "):
        return None
    return header[len("Bearer "):].strip()


def identity_from_header(header):
    # Convenience: parse the bearer token out of a header AND verify it in one call -> {"user","role"} or None.
    return verify_token(parse_bearer(header))
'''

_MOD_RBAC = r'''# rbac — role-based access control. A simple rank ladder: admin outranks viewer, so an admin passes any
# viewer-or-lower requirement while a viewer is blocked from admin-only routes (writes + the audit log).
ROLE_RANK = {"viewer": 1, "admin": 2}


def role_rank(role):
    # Numeric rank for a role name (unknown roles rank 0 = below everything).
    return ROLE_RANK.get(role, 0)


def check_role(identity, required_role):
    # True when the caller's role rank meets or exceeds the required role rank.
    if not identity:
        return False
    return role_rank(identity.get("role")) >= ROLE_RANK.get(required_role, 99)
'''

_MOD_VALIDATORS = r'''# validators — pure request-validation primitives (email shape, vendor payload, purchase-order payload).
import re

# a deliberately BASIC email shape check (not RFC 5322): non-space/non-@ local, one @, a dotted domain.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(value):
    # True only for a string matching the basic email shape.
    return bool(isinstance(value, str) and _EMAIL_RE.match(value))


def validate_vendor(payload):
    # Validate a vendor onboarding payload. Returns (ok, failed_fields).
    # Required: vendor_id, name; email must be present AND match the basic email shape.
    fields = []
    if not payload.get("vendor_id"):
        fields.append("vendor_id")
    if not payload.get("name"):
        fields.append("name")
    if not validate_email(payload.get("email")):
        fields.append("email")
    return (len(fields) == 0, fields)


def validate_po(payload, existing_vendor_ids):
    # Validate a purchase-order payload against the set of known vendor ids. Returns (ok, failed_fields).
    # Required: po_id; vendor_id must exist; amount must be a positive number (bool is rejected explicitly).
    fields = []
    if not payload.get("po_id"):
        fields.append("po_id")
    vendor_id = payload.get("vendor_id")
    if not vendor_id or vendor_id not in existing_vendor_ids:
        fields.append("vendor_id")
    amount = payload.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
        fields.append("amount")
    return (len(fields) == 0, fields)
'''

_MOD_RECORDS = r'''# records — canonical record builders. Normalize loosely-typed inbound payloads into stable stored shapes so
# downstream readers (serializers, CSV export, audit) see a consistent schema regardless of extra input keys.


def vendor_record(payload):
    # Project a vendor payload onto the canonical vendor schema (extra keys dropped).
    return {
        "vendor_id": payload.get("vendor_id"),
        "name": payload.get("name"),
        "email": payload.get("email"),
    }


def order_record(payload):
    # Project a purchase-order payload onto the canonical order schema.
    return {
        "po_id": payload.get("po_id"),
        "vendor_id": payload.get("vendor_id"),
        "amount": payload.get("amount"),
        "idempotency_key": payload.get("idempotency_key"),
    }
'''

_MOD_STORE = r'''# store — in-memory persistence primitives: an idempotent vendor store, an idempotent purchase-order store,
# and an append-only audit log. Real deployments swap these for Postgres/pgvector behind the same method names.


def audit_event(action, entity, entity_id):
    # Pure: build one audit record describing a single mutation.
    return {"action": action, "entity": entity, "id": entity_id}


class VendorStore:
    # Idempotent vendor store keyed by vendor_id.
    def __init__(self):
        self._rows = {}

    def add(self, vendor):
        # Store on first sight; return True if newly created, False on a duplicate id (no double-store).
        vendor_id = vendor["vendor_id"]
        if vendor_id in self._rows:
            return False
        self._rows[vendor_id] = dict(vendor)
        return True

    def get(self, vendor_id):
        row = self._rows.get(vendor_id)
        return dict(row) if row else None

    def all(self):
        return [dict(row) for row in self._rows.values()]

    def ids(self):
        return set(self._rows.keys())

    def count(self):
        return len(self._rows)


class PurchaseOrderStore:
    # Idempotent purchase-order store keyed by po_id, deduplicated by idempotency_key.
    def __init__(self):
        self._rows = {}
        self._by_key = {}

    def add(self, order):
        # Return (created, po_id). A repeated idempotency_key returns the original po_id and does not double-store.
        key = order.get("idempotency_key")
        if key and key in self._by_key:
            return False, self._by_key[key]
        po_id = order["po_id"]
        self._rows[po_id] = dict(order)
        if key:
            self._by_key[key] = po_id
        return True, po_id

    def get(self, po_id):
        row = self._rows.get(po_id)
        return dict(row) if row else None

    def all(self):
        return [dict(row) for row in self._rows.values()]


class AuditLog:
    # Append-only log of mutation events, one per successful write.
    def __init__(self):
        self._events = []

    def record(self, action, entity, entity_id):
        self._events.append(audit_event(action, entity, entity_id))

    def all(self):
        return [dict(event) for event in self._events]
'''

_MOD_QUERY = r'''# query — pure list-shaping primitives used by the vendor list endpoint: substring filter, sort, paginate.


def filter_contains(items, field, needle):
    # Case-insensitive substring filter over a string field. Empty needle keeps everything.
    if not needle:
        return list(items)
    lowered = needle.lower()
    return [item for item in items if lowered in str(item.get(field, "")).lower()]


def sort_by(items, field):
    # Stable sort by a string field. Empty field preserves input order.
    if not field:
        return list(items)
    return sorted(items, key=lambda item: str(item.get(field, "")))


def paginate(items, page, size):
    # Slice a page out of items. Returns (page_items, total). 1-based page; guards non-positive inputs.
    materialized = list(items)
    total = len(materialized)
    if size <= 0:
        size = 20
    if page <= 0:
        page = 1
    start = (page - 1) * size
    return materialized[start:start + size], total


def search_page(items, field, needle, sort_field, page, size):
    # Compose the whole list pipeline: substring filter -> optional sort -> paginate. Returns (page_items, total)
    # where total counts the post-FILTER set (not the page). This is the reusable "list endpoint" primitive.
    rows = filter_contains(items, field, needle)
    if sort_field:
        rows = sort_by(rows, sort_field)
    return paginate(rows, page, size)
'''

_MOD_SERIALIZERS = r'''# serializers — output-shaping primitives. csv_rows renders the vendor list as CSV text for the export route.
CSV_HEADER = "vendor_id,name,email"


def csv_rows(vendors):
    # Render vendors as CSV text: a fixed header line plus one comma-joined row per vendor, trailing newline.
    lines = [CSV_HEADER]
    for vendor in vendors:
        lines.append("{},{},{}".format(vendor.get("vendor_id", ""), vendor.get("name", ""),
                                       vendor.get("email", "")))
    return "\n".join(lines) + "\n"
'''

_MOD_WEBHOOKS = r'''# webhooks — inbound webhook signature verification. verify_hmac authenticates a raw request body against a
# hex HMAC-SHA256 signature the sender computed under the shared secret (the standard webhook auth pattern).
import hashlib
import hmac


def verify_hmac(secret, raw_body, signature):
    # Constant-time compare of the provided signature against the expected HMAC-SHA256 of the raw body.
    if not signature:
        return False
    key = secret.encode() if isinstance(secret, str) else secret
    body = raw_body if isinstance(raw_body, bytes) else str(raw_body).encode()
    expected = hmac.new(key, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
'''

_MOD_APP = r'''# app — the back-office operations API router/server. stdlib http.server only; boots with `python app.py --port
# N`. Wires the pure primitive modules (auth, rbac, validators, records, store, query, serializers, webhooks,
# errors) into a JSON HTTP surface with bearer-token auth, role-based access control, idempotent writes, an audit
# trail, CSV export, and a signature-verified payment webhook.
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from config import SECRET
from auth import issue_token, authenticate, identity_from_header
from rbac import check_role
from validators import validate_vendor, validate_po
from records import vendor_record, order_record
from store import VendorStore, PurchaseOrderStore, AuditLog
from query import search_page
from serializers import csv_rows
from webhooks import verify_hmac
from errors import validation_error, unauthorized, forbidden, not_found, bad_signature

# module-level singletons (the process-lifetime state).
_VENDORS = VendorStore()
_ORDERS = PurchaseOrderStore()
_AUDIT = AuditLog()


def _parse_json(raw):
    # Parse a JSON body defensively; malformed or empty bodies become {}.
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _first(query, key, default):
    # First value for a query-string key (parse_qs yields lists), or the default.
    values = query.get(key)
    return values[0] if values else default


def _int(value, default):
    # Best-effort int parse for query-string numbers.
    try:
        return int(value)
    except Exception:
        return default


class Handler(BaseHTTPRequestHandler):
    # ---- response + request helpers ----
    def _send(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_csv(self, code, text):
        raw = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/csv")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_raw(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        return self.rfile.read(length) if length > 0 else b""

    def _identity(self):
        # Extract + verify the bearer token; returns {"user","role"} or None.
        return identity_from_header(self.headers.get("Authorization", ""))

    # ---- GET routing ----
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/health":                                   # public: no auth
            return self._send(200, {"status": "ok", "healthy": True})
        identity = self._identity()                             # every other GET needs a valid bearer
        if identity is None:
            return self._send(401, unauthorized())
        if path == "/vendors/export.csv":
            return self._send_csv(200, csv_rows(_VENDORS.all()))
        if path == "/vendors":
            return self._list_vendors(query)
        if path == "/audit":                                    # admin-only
            if not check_role(identity, "admin"):
                return self._send(403, forbidden())
            return self._send(200, {"items": _AUDIT.all()})
        if path.startswith("/vendors/"):
            vendor = _VENDORS.get(path.rsplit("/", 1)[-1])
            return self._send(200, vendor) if vendor else self._send(404, not_found())
        return self._send(404, not_found())

    def _list_vendors(self, query):
        page = _int(_first(query, "page", "1"), 1)
        size = _int(_first(query, "size", "20"), 20)
        needle = _first(query, "q", "")
        sort_field = _first(query, "sort", "")
        items, total = search_page(_VENDORS.all(), "name", needle, sort_field, page, size)
        return self._send(200, {"items": items, "page": page, "size": size, "total": total})

    # ---- POST routing ----
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        raw = self._read_raw()                                  # read the raw body ONCE (webhook needs the bytes)
        if path == "/auth/token":                               # public: the login route
            return self._auth(raw)
        if path == "/webhooks/payment":                         # public: signature-authenticated, no bearer
            return self._webhook(raw)
        identity = self._identity()                             # every other POST needs a valid bearer ...
        if identity is None:
            return self._send(401, unauthorized())
        if not check_role(identity, "admin"):                   # ... and admin role (writes are admin-only)
            return self._send(403, forbidden())
        payload = _parse_json(raw)
        if path == "/vendors":
            return self._create_vendor(payload)
        if path == "/purchase_orders":
            return self._create_order(payload)
        return self._send(404, not_found())

    def _auth(self, raw):
        payload = _parse_json(raw)
        role = authenticate(payload.get("user"), payload.get("password"))
        if role is None:
            return self._send(401, unauthorized())
        return self._send(200, {"token": issue_token(payload.get("user"), role), "role": role})

    def _webhook(self, raw):
        signature = self.headers.get("X-Signature", "")
        if not verify_hmac(SECRET, raw, signature):
            return self._send(401, bad_signature())
        return self._send(200, {"ok": True})

    def _create_vendor(self, payload):
        ok, fields = validate_vendor(payload)
        if not ok:
            return self._send(400, validation_error(fields))
        created = _VENDORS.add(vendor_record(payload))          # idempotent on vendor_id
        if created:
            _AUDIT.record("create", "vendor", payload["vendor_id"])
        return self._send(201 if created else 200, {"vendor_id": payload["vendor_id"]})

    def _create_order(self, payload):
        ok, fields = validate_po(payload, _VENDORS.ids())
        if not ok:
            return self._send(400, validation_error(fields))
        created, po_id = _ORDERS.add(order_record(payload))     # idempotent on idempotency_key
        if created:
            _AUDIT.record("create", "purchase_order", po_id)
        return self._send(201 if created else 200, {"po_id": po_id})

    def log_message(self, *args):
        # silence default request logging (keeps child stdout clean).
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
'''

_GOOD_BUILDOUT: dict[str, str] = {
    "config.py": _MOD_CONFIG,
    "errors.py": _MOD_ERRORS,
    "auth.py": _MOD_AUTH,
    "rbac.py": _MOD_RBAC,
    "validators.py": _MOD_VALIDATORS,
    "records.py": _MOD_RECORDS,
    "store.py": _MOD_STORE,
    "query.py": _MOD_QUERY,
    "serializers.py": _MOD_SERIALIZERS,
    "webhooks.py": _MOD_WEBHOOKS,
    "app.py": _MOD_APP,
}

# a BAD buildout: a server that BOOTS but returns 200 for everything (no auth, no RBAC, no validation, no health
# flag) → server_boots=True but every behavior check fails.
_BAD_APP = r'''# a BAD build: it BOOTS but returns 200 {} with no auth, no validation, no RBAC, no health flag.
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def _ok(self):
        raw = b"{}"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self._ok()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > 0:
            self.rfile.read(length)                 # drain the body then blindly 200 everything
        self._ok()

    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
'''
_BAD_BUILDOUT: dict[str, str] = {"app.py": _BAD_APP}

# a STUB buildout: importing app.py raises → the server never boots → server_boots=False.
_STUB_BUILDOUT: dict[str, str] = {"app.py": "raise NotImplementedError('back-office ops API not built')\n"}

_GOAL_TEXT = (
    "Build a multi-module back-office operations HTTP API (Python stdlib only; boots with "
    "`python app.py --port N`; every response body is JSON unless noted). It manages vendors and purchase orders "
    "for a generic B2B operations team, with token auth, role-based access control, idempotent writes, an audit "
    "trail, CSV export, and a signature-verified payment webhook. Endpoint contract:\n"
    "- GET /health -> 200 {\"status\":\"ok\",\"healthy\":true} (no auth).\n"
    "- POST /auth/token {\"user\",\"password\"} -> 200 {\"token\",\"role\"}; admin/admin gives role \"admin\", "
    "viewer/viewer gives role \"viewer\"; bad credentials -> 401. The token must ENCODE the role and be "
    "verifiable on later requests (HMAC-signed with a hardcoded SECRET).\n"
    "- Every route EXCEPT GET /health, POST /auth/token, and POST /webhooks/payment requires a valid "
    "`Authorization: Bearer <token>`; missing/invalid -> 401.\n"
    "- RBAC: write routes (POST /vendors, POST /purchase_orders) and GET /audit require role \"admin\"; a valid "
    "viewer token on those -> 403.\n"
    "- POST /vendors {\"vendor_id\",\"name\",\"email\"} -> validate (vendor_id & name required; email must match a "
    "basic email regex) else 400 {\"error\":\"validation\",\"fields\":[...]}; else store idempotently: 201 on "
    "first create, 200 on a duplicate vendor_id (no double-store); body {\"vendor_id\":<id>}.\n"
    "- GET /vendors?page=&size=&q=&sort= -> 200 {\"items\":[...],\"page\":P,\"size\":S,\"total\":T}; q filters "
    "vendors whose name contains q (case-insensitive); sort=name sorts by name; page/size slice.\n"
    "- GET /vendors/{id} -> 200 vendor object or 404.\n"
    "- POST /purchase_orders {\"po_id\",\"vendor_id\",\"amount\",\"idempotency_key\"} -> validate: vendor_id must "
    "exist (else 400), amount must be a positive number (else 400); idempotent on idempotency_key (a repeat key "
    "returns 200 with the same po_id, no double-store); 201 on create; body {\"po_id\":<id>}.\n"
    "- GET /audit -> 200 {\"items\":[...]} (admin only; viewer -> 403), one event per mutation "
    "{\"action\",\"entity\",\"id\"}.\n"
    "- GET /vendors/export.csv -> 200 CSV body (header \"vendor_id,name,email\" + one row per vendor).\n"
    "- POST /webhooks/payment with header X-Signature = hex HMAC-SHA256(SECRET, raw_request_body) -> 200 "
    "{\"ok\":true}; wrong/missing signature -> 401.\n"
    "Structure it as many small modules (app + auth + rbac + validators + records + store + query + serializers + "
    "webhooks + errors) so each pure primitive is independently reusable."
)

# ── the BuildoutGenome (one LARGE non-insurance genome; same dict shape as buildout_forge._GENOMES) ───────────
_GENOMES: dict[str, dict[str, Any]] = {
    GENOME_ID: {
        "product_family": "backoffice_ops_saas", "prompt_style": "founder_product_brief",
        "stack": "python_stdlib_http", "solution_file": "app.py", "http_oracle": _HTTP_ORACLE_DRIVER,
        "realism_level": BUILDOUT_REALISM, "goal": _GOAL_TEXT,
        # the pure primitives this build yields (independently reusable across buildouts):
        "primitive_targets": ["validate_vendor", "validate_email", "validate_po", "paginate", "filter_contains",
                              "sort_by", "make_error", "audit_event", "csv_rows", "verify_hmac", "issue_token",
                              "verify_token"],
        "good": _GOOD_BUILDOUT, "bad": _BAD_BUILDOUT, "stub": _STUB_BUILDOUT},
}


def run_buildout(genome_id: str, files: dict[str, str], lane: str = "harness_alone",
                 extra_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Write the multi-file build to an ephemeral workspace, BOOT it, run the HIDDEN HTTP oracle, receipt.
    Never returns oracle_pass=True without the app booting + the executed HTTP oracle passing. (Same machinery
    as scripts/buildout_forge.run_buildout, over this module's larger genome.)"""
    genome = _GENOMES[genome_id]
    t0 = time.time()
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        for fname, content in (extra_files or {}).items():        # pre-installed verified-primitive package (reuse lane)
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        for fname, content in files.items():                      # the buildout's own files
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        (wsp / "oracle.py").write_text(genome["http_oracle"], encoding="utf-8")   # hidden oracle (never shown to the build)
        try:
            proc = subprocess.run([sys.executable, "-I", "oracle.py"], cwd=ws, capture_output=True,
                                  text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return {"record_type": "buildout_run_receipt", "genome_id": genome_id, "lane": lane,
                    "benchmark_kind": BENCHMARK_KIND, "realism_level": genome["realism_level"],
                    "oracle_pass": False, "error": "timeout", **BOUNDARY}
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("ORACLE ")), None)
        result = json.loads(line[len("ORACLE "):]) if line else {"checks": {}, "oracle_pass": False}
    return {"record_type": "buildout_run_receipt", "genome_id": genome_id,
            "product_family": genome["product_family"], "lane": lane, "benchmark_kind": BENCHMARK_KIND,
            "realism_level": genome["realism_level"], "n_files": len(files),
            "commands_run": [f"{Path(sys.executable).name} -I oracle.py (boots app.py + HTTP probes)"],
            "oracle_checks": result["checks"], "oracle_pass": bool(result["oracle_pass"]),
            "wall_time_s": round(time.time() - t0, 3),
            "stderr_tail": (proc.stderr or "")[-160:] if not result["oracle_pass"] else "", **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL: the reference 11-module build BOOTS and passes the hidden HTTP oracle (>=20 real
    endpoint checks); a bad build (boots but wrong behavior) FAILS; a stub build (never boots) FAILS. Real
    running service, real HTTP."""
    good = run_buildout(GENOME_ID, _GENOMES[GENOME_ID]["good"])
    assert good["oracle_pass"] is True, f"reference build must BOOT + pass the hidden HTTP oracle: {good}"
    assert good["oracle_checks"].get("server_boots") is True and all(good["oracle_checks"].values())
    assert len(good["oracle_checks"]) >= 20, f"a LARGE oracle must have >=20 checks: {len(good['oracle_checks'])}"

    bad = run_buildout(GENOME_ID, _GENOMES[GENOME_ID]["bad"])
    assert bad["oracle_pass"] is False, f"a boots-but-wrong build MUST fail the HTTP oracle (else it's fake): {bad}"
    assert bad["oracle_checks"].get("server_boots") is True, "the bad build should still boot (it fails on behavior)"

    stub = run_buildout(GENOME_ID, _GENOMES[GENOME_ID]["stub"])
    assert stub["oracle_pass"] is False and stub["oracle_checks"].get("server_boots") is False, \
        "a stub that never boots must fail with server_boots=False"

    assert BENCHMARK_KIND == "real_project_buildout" and good["realism_level"] == "B6"
    assert good["candidate"] is True and good["serves_truth"] is False
    # No-magic-values: the shared secret is mirrored in config.py (the app) and the oracle (the external caller);
    # assert both holders carry the single-source literal so a future edit to one can't silently drift.
    assert _SHARED_SECRET in _MOD_CONFIG and _SHARED_SECRET in _HTTP_ORACLE_DRIVER, "shared secret drifted across holders"
    n_prims = len(_GENOMES[GENOME_ID]["primitive_targets"])
    print(f"OK buildout_forge_large self-test: reference {good['n_files']}-file build BOOTS + passes a HIDDEN HTTP "
          f"oracle ({len(good['oracle_checks'])} real endpoint checks) in {good['wall_time_s']}s; a "
          f"boots-but-wrong build FAILS on behavior; a stub that never boots FAILS; yields {n_prims} pure "
          f"primitives; benchmark_kind=real_project_buildout realism={good['realism_level']}; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="BuildoutForge LARGE: boot a big multi-module build + a hidden HTTP oracle.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--genome", default=GENOME_ID, choices=list(_GENOMES))
    ap.add_argument("--solution", default="good", choices=["good", "bad", "stub"])
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run:
        res = run_buildout(args.genome, _GENOMES[args.genome][args.solution])
        out_dir = resource(ARTIFACT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{args.genome}_{args.solution}_receipt.json").write_text(
            json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(res, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
