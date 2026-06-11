#!/usr/bin/env python3
"""scripts.identity_local_service — the LOCAL Identity & Access service for the AI Done Right portfolio.

Runs the owner-locked auth model (docs/architecture/auth-identity-kit.md) as a WORKING local backend:
ONE shared kit (src/openharnesshub/auth_kit), COMPLETELY SEPARATE + INDEPENDENT realms per product —
own accounts, own sessions, own registration; no cross-realm account; no SSO. Realms are DATA, declared
in architecture/identity_realm_registry.json (parent + Baltor + Teleon + every LIVE Open*Hub; private
bench hubs are excluded — they take internal service identity only, never public registration).

Phase-1 local MVP of docs/architecture/service-auth-and-consumption-model.md:
  * register → onboard → login → realm-scoped session (the kit's standard flow, over HTTP)
  * per-realm API keys: HASH-ONLY at rest (key_id + display prefix + blake2b ref); the raw value is
    returned exactly ONCE at mint; mint/list/revoke require a valid realm session; verify proves
    possession (for service callers)
  * an audit event for every privileged call (carrying X-AIDR-Request-Id correlation), persisted as
    an append-only audit-events.jsonl mirror over a SQLite-WAL append-log (scripts._jsonl_store):
    crash-safe + no torn-tail corruption, the jsonl stays the durable on-disk record
  * file-backed persistence under dist/identity/ (atomic replace for the realm + service-connection
    stores; no cleartext secret and no raw key is ever written to disk — the kit stores one-way
    credential refs, this service stores key hashes; the SQLite index lives off the state dir)

This is a LOCAL DEV EQUIVALENT, not production auth: blake2b refs are NOT production crypto (argon2/
bcrypt/OAuth/SSO drop in at the kit's CredentialProviderPort seam — owner-gated); CORS is wide open for
local preview only; a TryCloudflare tunnel exposes a port, it does not make this production. Offline,
stdlib-only, no installs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets as _secrets
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# SQLite-WAL append-log behind audit-events + the migration suffix (SINGLE SOURCE — defined once
# in scripts._jsonl_store, never re-typed here)
from scripts._jsonl_store import AppendLog, MIGRATED_SUFFIX  # noqa: E402
from src.openharnesshub.auth_kit import make_realm  # noqa: E402  (repo-root import, kit is the bottom layer)

REGISTRY_PATH = REPO_ROOT / "architecture" / "identity_realm_registry.json"
MAX_BODY_BYTES = 64 * 1024          # local JSON bodies only; anything bigger is not an identity call
KEY_PREFIX_DISPLAY_CHARS = 12       # how much of a raw key the list projection may reveal
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")

# -- login throttle policy (closes the unthrottled-credential-guessing gap) --
LOGIN_WINDOW_S = 300                # sliding failure window: 5 min is long enough to see scripted
                                    # guessing, short enough that a fat-fingered human heals fast
LOGIN_MAX_FAILURES = 5              # failures per (realm, identifier) inside the window before a
                                    # lockout — humans re-type a few times, scripts burn this out
LOGIN_SOURCE_MAX_FAILURES = 20      # wider budget per (realm, source addr): catches one source
                                    # SPRAYING many identifiers, with headroom for shared-NAT and
                                    # local proof traffic (existing proofs fail ≤~4 per realm)
LOCKOUT_S = 900                     # 15 min lockout (3× the window, so an expired lockout restarts
                                    # with an empty window): ~5 guesses per 15 min kills brute force


def _now() -> int:
    """Wall-clock seconds, injected into the kit as its logical clock (ttl values are in seconds)."""
    return int(time.time())


def _key_hash(realm_id: str, raw_key: str) -> str:
    """One-way ref for an API key (hash-only at rest). NOT production crypto — same seam class as the
    kit's CredentialProviderPort; a real KMS/HMAC scheme drops in when deploying."""
    return "keyref:" + hashlib.blake2b(f"apikey|{realm_id}|{raw_key}".encode(), digest_size=16).hexdigest()


class _LoginThrottle:
    """Sliding-window login limiter + lockout, keyed per (realm, identifier) AND per (realm, source
    address). Realms are independent by law (no SSO), so throttle state never bridges realms either.

    Deliberately IN-MEMORY, per-process: this service's law is one process per state dir on one
    machine, so process memory IS the whole picture. Lockouts are transient anti-bruteforce posture,
    not identity truth — persisting them to the JSON state would let a flood survive restarts as a
    durable self-DoS, so they are never written to disk. Limits are constructor parameters (defaults
    = the module policy constants) so the self-test can exercise them without env vars or sleeps."""

    _IDENTIFIER_DIM = "identifier"  # window dimension names — keep the two key spaces disjoint
    _SOURCE_DIM = "source"

    def __init__(self, window_s: int = LOGIN_WINDOW_S, max_failures: int = LOGIN_MAX_FAILURES,
                 source_max_failures: int = LOGIN_SOURCE_MAX_FAILURES,
                 lockout_s: int = LOCKOUT_S) -> None:
        self.window_s = window_s
        self.max_failures = max_failures
        self.source_max_failures = source_max_failures
        self.lockout_s = lockout_s
        self.failures: dict[tuple[str, str, str], deque[int]] = {}   # key -> failure timestamps
        self.locked_until: dict[tuple[str, str, str], int] = {}

    def _keys(self, realm_id: str, identifier: str,
              source: str) -> tuple[tuple[str, str, str], tuple[str, str, str]]:
        return ((self._IDENTIFIER_DIM, realm_id, identifier), (self._SOURCE_DIM, realm_id, source))

    def _prune(self, key: tuple[str, str, str], now: int) -> deque[int]:
        window = self.failures.setdefault(key, deque())
        while window and window[0] <= now - self.window_s:
            window.popleft()
        return window

    def locked(self, realm_id: str, identifier: str, source: str, now: int) -> bool:
        for key in self._keys(realm_id, identifier, source):
            until = self.locked_until.get(key, 0)
            if now < until:
                return True
            if until:                                  # expired lockout: drop it; the failure window
                del self.locked_until[key]             # is older than LOGIN_WINDOW_S, so it prunes clean
        return False

    def record_failure(self, realm_id: str, identifier: str, source: str, now: int) -> bool:
        """Record one failed attempt on both dimensions; True when this attempt STARTS a lockout
        (the audit hook). Only ever called while unlocked — locked attempts are rejected upstream."""
        started = False
        ident_key, source_key = self._keys(realm_id, identifier, source)
        for key, limit in ((ident_key, self.max_failures), (source_key, self.source_max_failures)):
            window = self._prune(key, now)
            window.append(now)
            if len(window) >= limit:
                self.locked_until[key] = now + self.lockout_s
                started = True
        return started

    def reset(self, realm_id: str, identifier: str, source: str, now: int) -> None:
        """A successful login clears the IDENTIFIER's window + lock. The source window is left to
        age out: one good login must not launder a spray across many other identifiers."""
        ident_key, _ = self._keys(realm_id, identifier, source)
        self.failures.pop(ident_key, None)
        self.locked_until.pop(ident_key, None)


class RealmRuntime:
    """One realm's runtime: the kit Realm + this service's API-key store + its persistence file."""

    def __init__(self, spec: dict[str, Any], defaults: dict[str, Any], state_dir: Path) -> None:
        self.spec = spec
        self.realm_id = spec["realm_id"]
        steps = tuple(spec.get("onboarding_steps") or defaults["onboarding_steps"])
        ttl = int(spec.get("session_ttl_seconds") or defaults["session_ttl_seconds"])
        self.api_key_ttl = int(spec.get("api_key_ttl_seconds") or defaults["api_key_ttl_seconds"])
        self.api_key_prefix = str(defaults.get("api_key_prefix", "ak"))
        self.realm = make_realm(self.realm_id, display_name=spec.get("display_name") or self.realm_id,
                                onboarding_steps=steps, session_ttl=ttl)
        self.api_keys: dict[str, dict[str, Any]] = {}      # key_id -> record (hash-only; never the raw key)
        self.path = state_dir / f"realm-{self.realm_id}.json"
        self._load()

    # -- persistence (atomic; refs and opaque handles only — never a cleartext secret or raw key) --
    def _load(self) -> None:
        if not self.path.exists():
            return
        state = json.loads(self.path.read_text(encoding="utf-8"))
        self.realm.restore(state)                          # realm-guarded: cross-realm snapshots are rejected
        self.api_keys = {k: dict(v) for k, v in state.get("api_keys", {}).items()}

    def save(self) -> None:
        state = self.realm.snapshot()
        state["realm_id"] = self.realm_id
        state["saved_at"] = _now()
        state["api_keys"] = self.api_keys
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)

    # -- API keys (service concern, per the consumption model; identity stays in the kit) --
    def mint_key(self, account_id: str, scopes: list[str], now: int) -> tuple[str, dict[str, Any]]:
        raw = f"{self.api_key_prefix}_{self.realm_id}_{_secrets.token_hex(16)}"
        ref = _key_hash(self.realm_id, raw)
        rec = {
            "key_id": "akid_" + ref[-12:],
            "prefix": raw[:KEY_PREFIX_DISPLAY_CHARS] + "…",
            "key_hash": ref,
            "account_id": account_id,
            "scopes": sorted(set(scopes or ["read"])),
            "created_at": now,
            "expires_at": now + self.api_key_ttl,
            "last_used_at": None,
            "revoked_at": None,
        }
        self.api_keys[rec["key_id"]] = rec
        return raw, rec

    def verify_key(self, raw_key: str, now: int) -> dict[str, Any] | None:
        ref = _key_hash(self.realm_id, raw_key)
        for rec in self.api_keys.values():
            if rec["key_hash"] == ref and rec["revoked_at"] is None and now < rec["expires_at"]:
                rec["last_used_at"] = now
                return rec
        return None

    @staticmethod
    def key_projection(rec: dict[str, Any]) -> dict[str, Any]:
        """What list/verify responses may show: never the raw key, never the stored hash."""
        return {k: rec[k] for k in ("key_id", "prefix", "account_id", "scopes", "created_at",
                                    "expires_at", "last_used_at", "revoked_at")}


class IdentityService:
    """All realms + the audit stream. One process hosts N realms the way one Postgres hosts N databases:
    every store, session, and key is realm-scoped; nothing here bridges realms (no SSO)."""

    #: service↔service scope vocabulary (STANDARDS S3 — the single source; tokens may request a subset)
    SERVICE_SCOPES = ("llm:invoke", "events:write", "registry:read", "registry:publish",
                      "serve:cited", "verify:run", "state:read", "state:write")

    def __init__(self, state_dir: Path | None = None, registry_path: Path | None = None,
                 clock: Callable[[], int] | None = None,
                 login_throttle: _LoginThrottle | None = None) -> None:
        self.registry = json.loads((registry_path or REGISTRY_PATH).read_text(encoding="utf-8"))
        defaults = self.registry["defaults"]
        self.state_dir = Path(state_dir) if state_dir else (REPO_ROOT / defaults["state_dir"])
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.default_port = int(defaults["port"])
        self.lock = threading.Lock()
        self._clock = clock or _now            # injectable so the self-test elapses windows, no sleeps
        self.login_throttle = login_throttle or _LoginThrottle()
        self.runtimes = {spec["realm_id"]: RealmRuntime(spec, defaults, self.state_dir)
                         for spec in self.registry["realms"]}
        # audit stream: an append-only audit-events.jsonl mirror over a SQLite-WAL append-log
        # (scripts._jsonl_store). The db (off the scanned state dir — disk-hygiene proofs read_text
        # every file UNDER state_dir, so no binary file may live there) is the crash-safe primary;
        # the jsonl stays the durable, externally-read record. A legacy audit-events.jsonl migrates
        # losslessly on first open. The realm stores + service-connections stay whole-document
        # atomic-replace JSON (not append-logs — the append-log abstraction does not fit them).
        self.audit_path = self.state_dir / "audit-events.jsonl"
        self.audit_log = AppendLog(self.audit_path)
        # service-to-service connections span TWO realms, so they live at the service level (NOT in a
        # realm's user store). Services legitimately cross realms; USERS never do (that's the no-SSO law).
        self.service_path = self.state_dir / "service-connections.json"
        self.service_connections: dict[str, dict[str, Any]] = {}
        if self.service_path.exists():
            self.service_connections = json.loads(self.service_path.read_text(encoding="utf-8"))

    # -- service-account auth + the /service/* handshake slice (contracts/SERVICE-CONNECTIONS.md) --
    def _service_secret(self, realm_id: str) -> str | None:
        """A realm's service-account secret comes from the environment (SERVICE_<REALM>_SECRET) —
        never stored in the repo. Unset = that realm cannot initiate a handshake (honest, no fake)."""
        return os.environ.get(f"SERVICE_{realm_id.upper()}_SECRET") or None

    def _service_ref(self, raw: str) -> str:
        return "svtref:" + hashlib.blake2b(("svc|" + raw).encode(), digest_size=16).hexdigest()

    def _save_service(self) -> None:
        tmp = self.service_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.service_connections, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.service_path)

    @staticmethod
    def _conn_projection(rec: dict[str, Any]) -> dict[str, Any]:
        return {k: rec[k] for k in ("id", "from", "to", "scopes", "note", "prefix",
                                    "created_at", "status", "receipt")}

    def service_handshake(self, frm: str, presented_secret: str, to: str, scopes: list[str],
                          note: str) -> tuple[int, dict[str, Any]]:
        if frm not in self.runtimes or to not in self.runtimes:
            return 404, {"error": "unknown from/to realm"}
        secret = self._service_secret(frm)
        if not secret:
            return 503, {"error": f"no service account for {frm!r} (set SERVICE_{frm.upper()}_SECRET) — "
                                  "not faked"}
        if presented_secret != secret:
            return 401, {"error": "service authentication failed"}
        bad = [s for s in scopes if s not in self.SERVICE_SCOPES]
        if bad:
            return 400, {"error": f"unknown scopes {bad}; allowed {list(self.SERVICE_SCOPES)}"}
        now = _now()
        raw = f"svt_{frm}_{to}_{_secrets.token_hex(16)}"
        conn_id = "svc_" + self._service_ref(raw)[-12:]
        receipt = "rcpt_" + hashlib.blake2b(f"{conn_id}|{now}".encode(), digest_size=10).hexdigest()
        rec = {"id": conn_id, "from": frm, "to": to, "scopes": sorted(set(scopes or ["llm:invoke"])),
               "note": str(note or ""), "prefix": raw[:16] + "…", "token_ref": self._service_ref(raw),
               "created_at": now, "status": "active", "revoked_at": None, "receipt": receipt}
        self.service_connections[conn_id] = rec
        self._save_service()
        # the raw token appears exactly ONCE here; only its ref is persisted
        return 201, {"connection": self._conn_projection(rec), "token": raw, "shown_once": True,
                     "receipt": receipt}

    def service_connections_for(self, realm_id: str) -> list[dict[str, Any]]:
        return [self._conn_projection(r) for r in self.service_connections.values()
                if r["from"] == realm_id or r["to"] == realm_id]

    def service_verify(self, to: str, raw_token: str) -> tuple[int, dict[str, Any]]:
        ref = self._service_ref(raw_token)
        for r in self.service_connections.values():
            if r["token_ref"] == ref and r["to"] == to and r["status"] == "active":
                return 200, {"valid": True, "from": r["from"], "to": r["to"], "scopes": r["scopes"]}
        return 401, {"valid": False}

    def service_revoke(self, realm_id: str, conn_id: str) -> tuple[int, dict[str, Any]]:
        rec = self.service_connections.get(conn_id)
        if rec is None or realm_id not in (rec["from"], rec["to"]):
            return 404, {"error": "no such connection for this realm"}
        rec["status"] = "revoked"
        rec["revoked_at"] = _now()
        receipt = "rcpt_" + hashlib.blake2b(f"{conn_id}|revoke|{rec['revoked_at']}".encode(),
                                            digest_size=10).hexdigest()
        rec["receipt"] = receipt
        self._save_service()
        return 200, {"ok": True, "id": conn_id, "receipt": receipt}

    def audit(self, realm_id: str, action: str, actor: str, outcome: str, request_id: str) -> None:
        event = {"ts": _now(), "realm": realm_id, "action": action, "actor": actor,
                 "outcome": outcome, "request_id": request_id}
        # one crash-safe SQLite commit + the audit-events.jsonl mirror line (append-log, own lock)
        self.audit_log.append(event)

    def realms_projection(self) -> list[dict[str, Any]]:
        return [{"realm_id": rt.realm_id, "display_name": rt.realm.display_name,
                 "layer": rt.spec.get("layer", "product"),
                 "onboarding_steps": list(rt.realm.onboarding_steps),
                 "session_ttl_seconds": rt.realm.session_ttl}
                for rt in self.runtimes.values()]

    # -- request handling (transport-independent; the HTTP handler is a thin shell) --
    def handle(self, method: str, realm_id: str, action: str, body: dict[str, Any],
               request_id: str, bearer: str = "", source: str = "") -> tuple[int, dict[str, Any]]:
        # service-to-service slice: spans two realms, authed by the FROM realm's service secret
        # (a Bearer header, never a user session) — handled before the per-realm user dispatch
        if action.startswith("service/"):
            status, payload = self._dispatch_service(realm_id, action, method, body, bearer)
            self.audit(realm_id, action, payload.get("connection", {}).get("from", realm_id),
                       "ok" if status < 400 else "rejected", request_id)
            return status, payload
        rt = self.runtimes.get(realm_id)
        if rt is None:
            return 404, {"error": f"unknown realm {realm_id!r}"}
        actor_box = {"actor": "anonymous"}
        try:
            with self.lock:
                status, payload = self._dispatch(rt, method, action, body, self._clock(),
                                                 actor_box, source)
        except ValueError as exc:
            status, payload = 400, {"error": str(exc)}
        self.audit(realm_id, action, actor_box["actor"],
                   "ok" if status < 400 else "rejected", request_id)
        if actor_box.pop("lockout_started", ""):
            # the lockout transition gets its OWN audit kind; the wire response stays generic 401
            self.audit(realm_id, "login/lockout", actor_box["actor"], "locked", request_id)
        return status, payload

    def _send_verify_email(self, realm: str, identifier: str, account_id: str) -> str:
        """Render a realm-branded verification email through the standardized port. Soft-imported +
        best-effort so the identity service never depends on email being present; the console
        adapter renders to the outbox and HONESTLY does not send."""
        if "@" not in identifier:
            return "skipped_non_email_identifier"
        try:
            from scripts import email_port
            # a REAL clickable verify link (relative → works on 127.0.0.1 and through a tunnel) into
            # the mailbox inbox; clicking it completes verify_identifier for real. Demo-grade: the
            # account id is the handle; a cryptographic one-time token is the prod hardening.
            rec = email_port.send(realm, "verify_email", identifier,
                                  {"verify_url": f"/mailbox/verify?realm={realm}&account={account_id}"})
            return f"{rec['mode']}:{'sent' if rec['sent'] else 'rendered_not_sent'}"
        except Exception:  # noqa: BLE001  (email must never break registration)
            return "email_port_unavailable"

    def _dispatch_service(self, realm_id: str, action: str, method: str, body: dict[str, Any],
                          bearer: str) -> tuple[int, dict[str, Any]]:
        with self.lock:
            if action == "service/handshake" and method == "POST":
                # realm_id is the FROM realm; it authenticates with its own service secret
                return self.service_handshake(realm_id, bearer, str(body.get("to", "")),
                                              list(body.get("scopes") or ["llm:invoke"]),
                                              str(body.get("note", "")))
            if action == "service/connections" and method == "GET":
                return 200, {"connections": self.service_connections_for(realm_id)}
            if action == "service/verify" and method == "POST":
                # realm_id is the TO realm validating a presented token
                return self.service_verify(realm_id, str(body.get("token", "")))
            if action == "service/revoke" and method == "POST":
                return self.service_revoke(realm_id, str(body.get("id", "")))
        return 404, {"error": f"unknown service action {action!r}"}

    def _dispatch(self, rt: RealmRuntime, method: str, action: str, body: dict[str, Any],
                  now: int, actor_box: dict[str, str], source: str = "") -> tuple[int, dict[str, Any]]:
        if action == "register" and method == "POST":
            acct = rt.realm.register(str(body.get("identifier", "")), str(body.get("secret", "")), now=now)
            rt.save()
            actor_box["actor"] = acct["account_id"]
            out = {k: acct[k] for k in ("account_id", "realm_id", "identifier", "status", "created_at")}
            out["onboarding_steps"] = list(rt.realm.onboarding_steps)
            # standardized transactional email (BUSINESS-PLANE §2): registration renders a realm-
            # branded verify_email via the email PORT. Best-effort + console adapter = never blocks
            # registration, never silently sends (Mode Protocol). Reported honestly in the response.
            out["verification_email"] = self._send_verify_email(rt.realm_id, acct["identifier"],
                                                                acct["account_id"])
            return 201, out                      # projection only — the credential ref stays server-side
        if action == "onboard" and method == "POST":
            acct = rt.realm.onboard(str(body.get("account_id", "")), str(body.get("step", "")), now=now)
            rt.save()
            actor_box["actor"] = acct["account_id"]
            return 200, {k: acct[k] for k in ("account_id", "status", "onboarding_done")}
        if action == "login" and method == "POST":
            identifier = str(body.get("identifier", ""))
            # throttle gate BEFORE the credential path: a locked identifier/source gets the SAME
            # generic 401 as a bad secret — lock state must not become an enumeration oracle
            if self.login_throttle.locked(rt.realm_id, identifier, source, now):
                return 401, {"error": "login rejected"}
            try:
                sess = rt.realm.login(identifier, str(body.get("secret", "")), now=now)
            except ValueError:
                # generic on purpose: a login surface must not enumerate accounts or failure reasons
                if self.login_throttle.record_failure(rt.realm_id, identifier, source, now):
                    actor_box["lockout_started"] = "yes"   # handle() audits this as login/lockout
                return 401, {"error": "login rejected"}
            self.login_throttle.reset(rt.realm_id, identifier, source, now)
            rt.save()
            actor_box["actor"] = sess["account_id"]
            return 200, dict(sess)
        if action == "logout" and method == "POST":
            sess = rt.realm.sessions.pop(str(body.get("session_id", "")), None)
            rt.save()
            actor_box["actor"] = (sess or {}).get("account_id", "anonymous")
            return 200, {"logged_out": bool(sess)}
        if action == "session/validate" and method == "POST":
            sid = str(body.get("session_id", ""))
            ok = rt.realm.validate_session(sid, now=now)
            if ok:
                actor_box["actor"] = rt.realm.sessions[sid]["account_id"]
            return 200, {"valid": ok, "realm_id": rt.realm_id,
                         **({"account_id": actor_box["actor"]} if ok else {})}
        if action == "api-keys/mint" and method == "POST":
            sid = str(body.get("session_id", ""))
            if not rt.realm.validate_session(sid, now=now):
                return 401, {"error": "a valid realm session is required to mint a key"}
            actor_box["actor"] = rt.realm.sessions[sid]["account_id"]
            raw, rec = rt.mint_key(actor_box["actor"], list(body.get("scopes") or []), now)
            rt.save()
            # the ONE place the raw key ever appears; it is never persisted or logged
            return 201, {"api_key": raw, "shown_once": True, **rt.key_projection(rec)}
        if action == "api-keys/list" and method == "GET":
            sid = str(body.get("session_id", ""))
            if not rt.realm.validate_session(sid, now=now):
                return 401, {"error": "a valid realm session is required"}
            actor_box["actor"] = rt.realm.sessions[sid]["account_id"]
            keys = [rt.key_projection(r) for r in rt.api_keys.values()
                    if r["account_id"] == actor_box["actor"]]
            return 200, {"api_keys": sorted(keys, key=lambda r: r["created_at"])}
        if action == "api-keys/verify" and method == "POST":
            rec = rt.verify_key(str(body.get("api_key", "")), now)
            if rec is None:
                return 401, {"valid": False}
            rt.save()                            # persists last_used_at
            actor_box["actor"] = rec["account_id"]
            return 200, {"valid": True, **rt.key_projection(rec)}
        if action == "api-keys/revoke" and method == "POST":
            sid = str(body.get("session_id", ""))
            if not rt.realm.validate_session(sid, now=now):
                return 401, {"error": "a valid realm session is required"}
            actor_box["actor"] = rt.realm.sessions[sid]["account_id"]
            rec = rt.api_keys.get(str(body.get("key_id", "")))
            if rec is None or rec["account_id"] != actor_box["actor"]:
                return 404, {"error": "no such key for this account"}
            rec["revoked_at"] = now
            rt.save()
            return 200, {"revoked": True, "key_id": rec["key_id"]}
        return 404, {"error": f"unknown action {action!r}"}


class _Handler(BaseHTTPRequestHandler):
    server_version = "AIDRIdentityLocal/1.0"
    identity: IdentityService = None  # type: ignore[assignment]  (set by start_service)

    # -- plumbing --
    def _request_id(self) -> str:
        rid = self.headers.get("X-AIDR-Request-Id", "")
        return rid if _REQUEST_ID_RE.match(rid or "") else f"req_{_secrets.token_hex(6)}"

    def _send(self, status: int, payload: dict[str, Any], request_id: str) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-AIDR-Request-Id", request_id)
        # local dev preview only — a tunnel exposes a port, it does not make this production
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AIDR-Request-Id")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict[str, Any]:
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    def _route(self, method: str) -> None:
        rid = self._request_id()
        path, _, query = self.path.partition("?")
        parts = [p for p in path.split("/") if p]
        if parts[:2] != ["api", "identity"]:
            return self._send(404, {"error": "unknown path"}, rid)
        if parts[2:] == ["health"]:
            return self._send(200, {"ok": True, "service": "identity_local",
                                    "realms": len(self.identity.runtimes)}, rid)
        if parts[2:] == ["realms"]:
            return self._send(200, {"realms": self.identity.realms_projection()}, rid)
        if len(parts) < 4:
            return self._send(404, {"error": "unknown path"}, rid)
        realm_id, action = parts[2], "/".join(parts[3:])
        body = self._body()
        if method == "GET" and action in ("api-keys", "service/connections"):
            if action == "api-keys":
                action = "api-keys/list"
            body = dict(pair.split("=", 1) for pair in query.split("&") if "=" in pair)
        bearer = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        status, payload = self.identity.handle(method, realm_id, action, body, rid, bearer,
                                               source=self.client_address[0])
        self._send(status, payload, rid)

    def do_GET(self) -> None:   # noqa: N802 (http.server API)
        self._route("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._route("POST")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(200, {"ok": True}, self._request_id())  # 200 not 204: a 204 must not carry a body

    def log_message(self, fmt: str, *args: Any) -> None:
        pass  # the audit JSONL is the record; stderr noise off for local runs


def start_service(port: int = 0, state_dir: Path | None = None,
                  registry_path: Path | None = None) -> tuple[ThreadingHTTPServer, threading.Thread, int]:
    """Start in-process (proofs + embedding). port=0 binds an ephemeral port. Caller owns shutdown()."""
    identity = IdentityService(state_dir=state_dir, registry_path=registry_path)
    handler = type("BoundHandler", (_Handler,), {"identity": identity})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, name="identity-local", daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


def _self_test() -> int:
    """Offline proof of the login throttle AND the SQLite-WAL audit engine. Throttle: wrong-secret
    failures trip a lockout that rejects even the CORRECT secret with the same generic 401, the
    lockout is audited as its own kind, success resets the identifier window, an elapsed lockout
    heals (injected clock — no sleeps), a spraying source is cut off per (realm, source), and the
    HTTP handler really plumbs the client address. State engine: a legacy pre-SQLite
    audit-events.jsonl migrates in LOSSLESSLY on startup (file preserved untouched + byte-identical
    snapshot), concurrent service calls lose/dup no audit row or account, and a restart rehydrates
    EQUAL state (audit history, accounts, a live session, an unrevoked API key).
    Temp state dir, ephemeral port, stdlib-only. Exit 0/1."""
    import shutil
    import tempfile
    import urllib.error
    import urllib.request

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    good = "-".join(("throttle", "proof", "fragment"))   # FAKE passphrase fragments, not a real secret
    clock = [1_000_000]                                  # injected logical clock (seconds)
    state_dir = Path(tempfile.mkdtemp(prefix="identity-throttle-proof-"))
    svc = IdentityService(state_dir=state_dir / "core", clock=lambda: clock[0])
    rid = "throttle-proof-001"
    src = "203.0.113.10"                                 # TEST-NET-3 documentation address

    def login(identifier: str, secret: str, source: str = src) -> tuple[int, dict[str, Any]]:
        return svc.handle("POST", "baltor", "login",
                          {"identifier": identifier, "secret": secret}, rid, source=source)

    def provision(identifier: str) -> None:
        st, acct = svc.handle("POST", "baltor", "register",
                              {"identifier": identifier, "secret": good}, rid, source=src)
        assert st == 201, f"register failed ({st}): {acct}"
        for step in acct["onboarding_steps"]:
            svc.handle("POST", "baltor", "onboard",
                       {"account_id": acct["account_id"], "step": step}, rid, source=src)

    server = thread = None
    try:
        provision("lock@example.test")
        st, _ = login("lock@example.test", good)
        ck("A: correct secret logs in before any failures", st == 200, str(st))
        results = [login("lock@example.test", good + "x") for _ in range(LOGIN_MAX_FAILURES + 1)]
        ck(f"A: {LOGIN_MAX_FAILURES + 1} wrong-secret logins all return 401",
           [s for s, _ in results] == [401] * (LOGIN_MAX_FAILURES + 1), str([s for s, _ in results]))
        ck("A: every rejection is the same generic body (no reason enumeration)",
           all(body == {"error": "login rejected"} for _, body in results))

        st, body = login("lock@example.test", good)
        ck("B: the CORRECT secret during lockout is still rejected (401)", st == 401, str(st))
        ck("B: the lockout response is byte-identical to a bad-secret response",
           body == {"error": "login rejected"})
        audit_path = state_dir / "core" / "audit-events.jsonl"
        events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
        ck("B: the lockout transition is audited as its own kind (login/lockout, locked)",
           any(e["action"] == "login/lockout" and e["outcome"] == "locked" for e in events))

        clock[0] += LOCKOUT_S + 1                        # elapse the lockout, no sleeping
        st, sess = login("lock@example.test", good)
        ck("C: after the lockout elapses the correct secret succeeds", st == 200 and "session_id" in sess,
           str(st))

        for _ in range(LOGIN_MAX_FAILURES - 1):          # success above reset the window: these
            login("lock@example.test", good + "x")       # fresh failures stay BELOW the limit
        st, _ = login("lock@example.test", good)
        ck("D: failures reset on success (a fresh sub-limit run does not lock)", st == 200, str(st))

        clock[0] += LOGIN_WINDOW_S + 1                   # clean window before the spray scenario
        provision("spray-target@example.test")
        spray_src = "198.51.100.7"                       # TEST-NET-2: the hostile source
        for i in range(LOGIN_SOURCE_MAX_FAILURES):
            login(f"ghost-{i}@example.test", good, source=spray_src)
        st_blocked, _ = login("spray-target@example.test", good, source=spray_src)
        st_clean, _ = login("spray-target@example.test", good, source=src)
        ck("E: a source spraying many identifiers is locked even with a correct secret",
           st_blocked == 401, str(st_blocked))
        ck("E: the same account from a clean source still logs in", st_clean == 200, str(st_clean))

        # F: over HTTP the handler passes client_address down — the lockout works on the wire
        server, thread, port = start_service(port=0, state_dir=state_dir / "http")
        base = f"http://127.0.0.1:{port}/api/identity/baltor"

        def post(path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            req = urllib.request.Request(base + path, method="POST",
                                         data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status, json.loads(resp.read() or b"{}")
            except urllib.error.HTTPError as err:
                return err.code, json.loads(err.read() or b"{}")

        st, acct = post("/register", {"identifier": "wire@example.test", "secret": good})
        for step in acct["onboarding_steps"]:
            post("/onboard", {"account_id": acct["account_id"], "step": step})
        wire = [post("/login", {"identifier": "wire@example.test", "secret": good + "x"})[0]
                for _ in range(LOGIN_MAX_FAILURES + 1)]
        st, body = post("/login", {"identifier": "wire@example.test", "secret": good})
        ck("F: over HTTP the lockout fires too (client address plumbed)",
           wire == [401] * (LOGIN_MAX_FAILURES + 1) and st == 401
           and body == {"error": "login rejected"}, f"{wire} then {st}")

        # G: the SQLite-WAL state engine — legacy audit migration, concurrent writes, restart equality
        mig_dir = state_dir / "mig"
        mig_dir.mkdir(parents=True)
        legacy_audit = [{"ts": 900_000 + i, "realm": "baltor", "action": "login",
                         "actor": f"acct_legacy_{i}", "outcome": "ok",
                         "request_id": f"legacy-{i:03d}"} for i in range(9)]
        audit_file = mig_dir / "audit-events.jsonl"
        with audit_file.open("w", encoding="utf-8") as fh:
            for e in legacy_audit:
                fh.write(json.dumps(e, sort_keys=True) + "\n")   # the pre-SQLite writer's exact format
        legacy_bytes = audit_file.read_bytes()
        svc_g = IdentityService(state_dir=mig_dir, clock=lambda: clock[0])
        ck("G: a legacy audit-events.jsonl (no db yet) migrates into the SQLite log on startup",
           svc_g.audit_log.count() == len(legacy_audit) and svc_g.audit_log.all() == legacy_audit,
           f"count={svc_g.audit_log.count()}")
        ck("G: the legacy audit file is preserved untouched (in place + byte-identical snapshot)",
           audit_file.read_bytes() == legacy_bytes
           and audit_file.with_name(audit_file.name + MIGRATED_SUFFIX).read_bytes() == legacy_bytes)

        # a full account flow over the migrated state (teleon realm keeps baltor's numbers clean)
        st, g_acct = svc_g.handle("POST", "teleon", "register",
                                  {"identifier": "mig@example.test", "secret": good}, rid, source=src)
        for step in g_acct["onboarding_steps"]:
            svc_g.handle("POST", "teleon", "onboard",
                         {"account_id": g_acct["account_id"], "step": step}, rid, source=src)
        _, g_sess = svc_g.handle("POST", "teleon", "login",
                                 {"identifier": "mig@example.test", "secret": good}, rid, source=src)
        _, g_key = svc_g.handle("POST", "teleon", "api-keys/mint",
                                {"session_id": g_sess["session_id"]}, rid, source=src)
        ck("G: the standard flow works over the migrated state (register→onboard→login→mint)",
           st == 201 and "session_id" in g_sess and g_key.get("shown_once") is True)

        # CONCURRENT writes through the service seam: every register = one account + one audit row
        before = svc_g.audit_log.count()
        threads_n, per_thread = 8, 25
        barrier = threading.Barrier(threads_n)
        conc_errors: list[tuple[int, int, int]] = []

        def _hammer(t: int) -> None:
            barrier.wait()
            for k in range(per_thread):                  # no "@" → the email port is never involved
                st_i, _ = svc_g.handle("POST", "baltor", "register",
                                       {"identifier": f"conc-{t}-{k}", "secret": good},
                                       f"conc-{t}-{k}", source=src)
                if st_i != 201:
                    conc_errors.append((t, k, st_i))

        workers = [threading.Thread(target=_hammer, args=(t,)) for t in range(threads_n)]
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        expected = threads_n * per_thread
        conc_rids = {e["request_id"] for e in svc_g.audit_log.all()
                     if str(e.get("request_id", "")).startswith("conc-")}
        baltor_accounts = svc_g.runtimes["baltor"].realm.accounts
        ck("G: concurrent registrations lose/dup nothing (accounts + one audit row each)",
           not conc_errors and svc_g.audit_log.count() == before + expected
           and len(conc_rids) == expected
           and sum(1 for a in baltor_accounts.values()
                   if a["identifier"].startswith("conc-")) == expected,
           f"errors={conc_errors[:2]} audit={svc_g.audit_log.count() - before} rids={len(conc_rids)}")

        # RESTART rehydration equality: a new service on the same state dir sees identical state
        svc_g2 = IdentityService(state_dir=mig_dir, clock=lambda: clock[0])
        st_sess, _ = svc_g2.handle("POST", "teleon", "session/validate",
                                   {"session_id": g_sess["session_id"]}, rid, source=src)
        _, g_verify = svc_g2.handle("POST", "teleon", "api-keys/verify",
                                    {"api_key": g_key["api_key"]}, rid, source=src)
        ck("G: a restart rehydrates EQUAL state (audit history, accounts, session, API key)",
           svc_g2.audit_log.all()[:before + expected] == svc_g.audit_log.all()[:before + expected]
           and svc_g2.runtimes["baltor"].realm.accounts == baltor_accounts
           and st_sess == 200 and g_verify.get("valid") is True,
           f"sess={st_sess} key={g_verify.get('valid')}")
    finally:
        if server is not None:
            server.shutdown()
            thread.join(timeout=5)
            services = [svc, server.RequestHandlerClass.identity]
        else:
            services = [svc]
        services += [s for s in (locals().get("svc_g"), locals().get("svc_g2")) if s is not None]
        for s in services:                     # close every SQLite handle, then remove the proof dbs
            s.audit_log.close()                # (off-state_dir index files; -wal/-shm vanish on close)
            for suffix in ("", "-wal", "-shm"):
                Path(str(s.audit_log.db_path) + suffix).unlink(missing_ok=True)
        shutil.rmtree(state_dir, ignore_errors=True)

    print("\n" + ("PASS — identity_local_service --self-test: sliding-window login throttle per "
                  "(realm, identifier) + (realm, source), lockout rejects even correct secrets with "
                  "the same generic 401, audited as login/lockout, reset on success, heals after "
                  f"{LOCKOUT_S}s, live over HTTP — and the SQLite-WAL audit engine migrates a legacy "
                  "audit-events.jsonl losslessly (preserved + snapshot), loses nothing under "
                  "concurrent registrations, and rehydrates equal state across a restart."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=None, help="default comes from the realm registry")
    parser.add_argument("--state-dir", default=None)
    parser.add_argument("--serve", action="store_true", help="run in the foreground")
    parser.add_argument("--self-test", action="store_true",
                        help="offline login-throttle proof (temp state, injected clock)")
    parser.add_argument("--bind", default=os.environ.get("OH_BIND_HOST", "127.0.0.1"),
                        help="0.0.0.0 lets the local Caddy gateway reach this host service via "
                             "host.docker.internal (public exposure still only via the gateway/tunnel); "
                             "default honors OH_BIND_HOST for container deploys")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    identity = IdentityService(state_dir=Path(args.state_dir) if args.state_dir else None)
    port = args.port if args.port is not None else identity.default_port
    if not args.serve:
        print(f"identity_local_service: {len(identity.runtimes)} realms; state {identity.state_dir}; "
              f"run with --serve --port {port}")
        return 0
    handler = type("BoundHandler", (_Handler,), {"identity": identity})
    server = ThreadingHTTPServer((args.bind, port), handler)
    pid_file = identity.state_dir / "service.pid"
    pid_file.write_text(str(os.getpid()), encoding="utf-8")
    print(f"identity_local_service on http://127.0.0.1:{port} — {len(identity.runtimes)} realms "
          f"(stop by exact pid {os.getpid()})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        pid_file.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
