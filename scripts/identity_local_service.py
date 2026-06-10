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
  * an audit event (JSONL) for every privileged call, carrying X-AIDR-Request-Id correlation
  * file-backed persistence under dist/identity/ (atomic replace; no cleartext secret and no raw key
    is ever written to disk — the kit stores one-way credential refs, this service stores key hashes)

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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.openharnesshub.auth_kit import make_realm  # noqa: E402  (repo-root import, kit is the bottom layer)

REGISTRY_PATH = REPO_ROOT / "architecture" / "identity_realm_registry.json"
MAX_BODY_BYTES = 64 * 1024          # local JSON bodies only; anything bigger is not an identity call
KEY_PREFIX_DISPLAY_CHARS = 12       # how much of a raw key the list projection may reveal
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")


def _now() -> int:
    """Wall-clock seconds, injected into the kit as its logical clock (ttl values are in seconds)."""
    return int(time.time())


def _key_hash(realm_id: str, raw_key: str) -> str:
    """One-way ref for an API key (hash-only at rest). NOT production crypto — same seam class as the
    kit's CredentialProviderPort; a real KMS/HMAC scheme drops in when deploying."""
    return "keyref:" + hashlib.blake2b(f"apikey|{realm_id}|{raw_key}".encode(), digest_size=16).hexdigest()


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

    def __init__(self, state_dir: Path | None = None, registry_path: Path | None = None) -> None:
        self.registry = json.loads((registry_path or REGISTRY_PATH).read_text(encoding="utf-8"))
        defaults = self.registry["defaults"]
        self.state_dir = Path(state_dir) if state_dir else (REPO_ROOT / defaults["state_dir"])
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.default_port = int(defaults["port"])
        self.lock = threading.Lock()
        self.runtimes = {spec["realm_id"]: RealmRuntime(spec, defaults, self.state_dir)
                         for spec in self.registry["realms"]}
        self.audit_path = self.state_dir / "audit-events.jsonl"
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
        with self.audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")

    def realms_projection(self) -> list[dict[str, Any]]:
        return [{"realm_id": rt.realm_id, "display_name": rt.realm.display_name,
                 "layer": rt.spec.get("layer", "product"),
                 "onboarding_steps": list(rt.realm.onboarding_steps),
                 "session_ttl_seconds": rt.realm.session_ttl}
                for rt in self.runtimes.values()]

    # -- request handling (transport-independent; the HTTP handler is a thin shell) --
    def handle(self, method: str, realm_id: str, action: str, body: dict[str, Any],
               request_id: str, bearer: str = "") -> tuple[int, dict[str, Any]]:
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
                status, payload = self._dispatch(rt, method, action, body, _now(), actor_box)
        except ValueError as exc:
            status, payload = 400, {"error": str(exc)}
        self.audit(realm_id, action, actor_box["actor"],
                   "ok" if status < 400 else "rejected", request_id)
        return status, payload

    def _send_verify_email(self, realm: str, identifier: str, account_id: str) -> str:
        """Render a realm-branded verification email through the standardized port. Soft-imported +
        best-effort so the identity service never depends on email being present; the console
        adapter renders to the outbox and HONESTLY does not send."""
        if "@" not in identifier:
            return "skipped_non_email_identifier"
        try:
            from scripts import email_port
            rec = email_port.send(realm, "verify_email", identifier,
                                  {"verify_url": f"local://{realm}/verify/{account_id[-12:]}"})
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
                  now: int, actor_box: dict[str, str]) -> tuple[int, dict[str, Any]]:
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
            try:
                sess = rt.realm.login(str(body.get("identifier", "")), str(body.get("secret", "")), now=now)
            except ValueError:
                # generic on purpose: a login surface must not enumerate accounts or failure reasons
                return 401, {"error": "login rejected"}
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
        status, payload = self.identity.handle(method, realm_id, action, body, rid, bearer)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=None, help="default comes from the realm registry")
    parser.add_argument("--state-dir", default=None)
    parser.add_argument("--serve", action="store_true", help="run in the foreground")
    parser.add_argument("--bind", default="127.0.0.1",
                        help="0.0.0.0 lets the local Caddy gateway reach this host service via "
                             "host.docker.internal (public exposure still only via the gateway/tunnel)")
    args = parser.parse_args(argv)
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
