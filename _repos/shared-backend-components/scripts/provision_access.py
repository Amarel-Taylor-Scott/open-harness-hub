#!/usr/bin/env python3
"""Owner provisioning CLI — register → onboard → login → mint key, with receipts.

The owner-side counterpart of the customer portals: one command provisions an account on any
identity realm (25 realms incl. the private bench), walks every onboarding step, mints a
scoped API key, verifies it, and writes an append-only receipt trail plus a shareable
onboarding bundle. Laws honored: the RAW key is printed to the terminal ONCE and never lands
in receipts, bundles, or logs (`raw_keys_never_in_artifacts`); secrets come from env/file or
are generated, never echoed back; every step's receipt carries the request id the service
logged, so the two ledgers cross-reference.

Usage (identity service must be running — python3 _repos/shared-backend-components/scripts/start_local_services.py):
  python3 _repos/shared-backend-components/scripts/provision_access.py --list-realms
  python3 _repos/shared-backend-components/scripts/provision_access.py provision --realm openhubforai \\
      --identifier owner@aidoneright.dev [--secret-env AIDR_OWNER_SECRET] \\
      [--scopes registry:read,registry:install] [--share-bundle]
  python3 _repos/shared-backend-components/scripts/provision_access.py grant-reviewer --realm openhubforai \\
      --account-id acct_… --admin-session sess_…       # registry roster, admin-gated
  python3 _repos/shared-backend-components/scripts/provision_access.py --self-test       # offline: in-process identity service

Receipts: dist/provisioning/receipts.jsonl (append-only; identifier stored as a short hash,
key as prefix-only). Share bundles: dist/provisioning/<realm>-<account>.md (no raw key).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
sys.path.insert(0, str(REPO))

RECEIPTS_PATH = _resource("dist") / "provisioning" / "receipts.jsonl"
BUNDLE_DIR = _resource("dist") / "provisioning"
DEFAULT_SCOPES = ["registry:read", "registry:install"]


def _identity_base() -> str:
    if os.environ.get("AIDR_IDENTITY_BASE"):
        return os.environ["AIDR_IDENTITY_BASE"].rstrip("/")
    registry = json.loads((_resource("architecture") / "identity_realm_registry.json").read_text(encoding="utf-8"))
    return f"http://127.0.0.1:{registry['defaults']['port']}"


def _registry_base() -> str:
    if os.environ.get("AIDR_REGISTRY_BASE"):
        return os.environ["AIDR_REGISTRY_BASE"].rstrip("/")
    services = json.loads((_resource("architecture") / "local_service_registry.json").read_text(encoding="utf-8"))
    port = next(s["port"] for s in services["services"] if s["service_id"] == "local_openhubforai_projection_api")
    return f"http://127.0.0.1:{port}"


def _post(base: str, path: str, body: dict) -> tuple[int, dict]:
    req = urllib.request.Request(f"{base}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode() or "{}")
        except Exception:
            return exc.code, {"error": "unparseable error body"}


def _get(base: str, path: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(f"{base}{path}", timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        return exc.code, {}


def _ident_hash(identifier: str) -> str:
    return hashlib.sha256(identifier.encode()).hexdigest()[:12]


def _receipt(action: str, realm: str, identifier: str, status: int, detail: dict,
             receipts_path: Path = RECEIPTS_PATH) -> dict:
    record = {
        "at": int(time.time()), "action": action, "realm": realm,
        "identifier_sha12": _ident_hash(identifier), "status": status,
        # projections only — NEVER the raw secret/key/session
        **{k: detail[k] for k in ("account_id", "key_id", "prefix", "onboarding_done", "valid",
                                  "granted", "request_id") if k in detail},
    }
    receipts_path.parent.mkdir(parents=True, exist_ok=True)
    with receipts_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def _resolve_secret(args) -> str:
    if getattr(args, "secret_env", None):
        value = os.environ.get(args.secret_env, "")
        if not value:
            raise SystemExit(f"--secret-env {args.secret_env}: env var is empty/unset")
        return value
    if getattr(args, "secret_file", None):
        return Path(args.secret_file).read_text(encoding="utf-8").strip()
    generated = f"own-{secrets.token_urlsafe(18)}"
    print(f"  generated secret (store it NOW, never persisted): {generated}")
    return generated


def provision(base: str, realm: str, identifier: str, secret: str, scopes: list[str],
              share_bundle: bool = False, receipts_path: Path = RECEIPTS_PATH,
              echo=print) -> dict:
    """register (or login if the account exists) → onboard all steps → mint + verify a key."""
    prefix = f"/api/identity/{realm}"
    status, reg = _post(base, f"{prefix}/register", {"identifier": identifier, "secret": secret})
    _receipt("register", realm, identifier, status, reg, receipts_path)
    if status == 201:
        account_id = reg["account_id"]
        steps = reg.get("onboarding_steps") or []
        echo(f"  registered {account_id} on '{realm}' ({len(steps)} onboarding steps)")
        for step in steps:
            s_status, onboarded = _post(base, f"{prefix}/onboard", {"account_id": account_id, "step": step})
            _receipt(f"onboard:{step}", realm, identifier, s_status, onboarded, receipts_path)
            if s_status != 200:
                raise SystemExit(f"onboarding step {step!r} failed ({s_status}): {onboarded}")
        echo("  onboarding complete")
    else:
        echo(f"  register → {status} ({reg.get('error', 'exists?')}); trying login as an existing account")
    status, sess = _post(base, f"{prefix}/login", {"identifier": identifier, "secret": secret})
    _receipt("login", realm, identifier, status, sess, receipts_path)
    if status != 200:
        raise SystemExit(f"login failed ({status}): {sess.get('error', sess)} — wrong secret or registration failed")
    session_id, account_id = sess["session_id"], sess["account_id"]
    echo(f"  session minted for {account_id}")
    status, minted = _post(base, f"{prefix}/api-keys/mint", {"session_id": session_id, "scopes": scopes})
    _receipt("api-keys/mint", realm, identifier, status, minted, receipts_path)
    if status != 201:
        raise SystemExit(f"key mint failed ({status}): {minted}")
    raw_key = minted["api_key"]
    status, verified = _post(base, f"{prefix}/api-keys/verify", {"api_key": raw_key})
    _receipt("api-keys/verify", realm, identifier, status, verified, receipts_path)
    if not verified.get("valid"):
        raise SystemExit("freshly minted key failed verification — service state is inconsistent")
    echo(f"\n  API KEY (shown once, prefix {minted.get('prefix', '?')}, scopes {scopes}):\n  {raw_key}\n")
    if share_bundle:
        bundle = BUNDLE_DIR / f"{realm}-{account_id}.md"
        bundle.parent.mkdir(parents=True, exist_ok=True)
        bundle.write_text(
            f"# {realm} access — {identifier}\n\n"
            f"- account: `{account_id}`\n- key id: `{minted.get('key_id')}` (prefix `{minted.get('prefix')}`)\n"
            f"- scopes: `{', '.join(scopes)}`\n- minted: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"
            f"The raw key was shown once at mint time and is NOT in this file. Sign in at the\n"
            f"{realm} surface and manage keys under Account → API keys.\n", encoding="utf-8")
        echo(f"  share bundle (no raw key): {bundle.relative_to(REPO)}")
    return {"account_id": account_id, "session_id": session_id, "key_id": minted.get("key_id"),
            "prefix": minted.get("prefix"), "raw_key": raw_key}


def grant_reviewer(realm: str, account_id: str, admin_session: str,
                   receipts_path: Path = RECEIPTS_PATH, echo=print) -> bool:
    base = _registry_base()
    status, out = _post(base, f"/api/openhubforai/{realm}/admin/reviewers/grant",
                        {"session_id": admin_session, "account_id": account_id})
    _receipt("grant-reviewer", realm, account_id, status,
             {"granted": status == 200, **out}, receipts_path)
    echo(f"  grant-reviewer {account_id} on '{realm}' → {status} {out}")
    return status == 200


def list_realms(base: str) -> int:
    status, body = _get(base, "/api/identity/realms")
    if status != 200:
        print(f"identity service unreachable at {base} ({status}) — python3 scripts/start_local_services.py")
        return 1
    realms = body.get("realms") or body
    print(json.dumps(realms, indent=2)[:4000])
    return 0


# ---------------------------------------------------------------- self-test (offline)

def _self_test() -> int:
    import tempfile
    from scripts.identity_local_service import start_service
    with tempfile.TemporaryDirectory() as tmp:
        server, thread, port = start_service(port=0, state_dir=Path(tmp) / "identity")
        base = f"http://127.0.0.1:{port}"
        receipts = Path(tmp) / "receipts.jsonl"
        quiet = lambda *_a, **_k: None  # noqa: E731
        try:
            realms_status, realms_body = _get(base, "/api/identity/realms")
            realm = (realms_body.get("realms") or [{}])[0].get("realm_id") or "openhubforai"
            identifier, secret = "owner-selftest@aidoneright.dev", "s3cret-selftest"
            first = provision(base, realm, identifier, secret, DEFAULT_SCOPES,
                              receipts_path=receipts, echo=quiet)
            second = provision(base, realm, identifier, secret, DEFAULT_SCOPES,
                               receipts_path=receipts, echo=quiet)  # idempotent re-run → login path
            lines = [json.loads(line) for line in receipts.read_text(encoding="utf-8").splitlines()]
            raw_text = receipts.read_text(encoding="utf-8")
            wrong_secret_ok = True
            try:
                provision(base, realm, identifier, "WRONG", DEFAULT_SCOPES,
                          receipts_path=receipts, echo=quiet)
                wrong_secret_ok = False
            except SystemExit:
                pass
            checks = [
                ("realms endpoint answers", realms_status == 200),
                ("provision returns account + key", bool(first["account_id"] and first["raw_key"])),
                ("re-provision is idempotent (login path, same account)",
                 second["account_id"] == first["account_id"] and second["key_id"] != first["key_id"]),
                ("receipts are append-only json with hashed identifiers",
                 len(lines) >= 8 and all("identifier_sha12" in r for r in lines)),
                ("RAW KEY NEVER IN RECEIPTS", first["raw_key"] not in raw_text
                 and second["raw_key"] not in raw_text),
                ("raw secret never in receipts", secret not in raw_text),
                ("wrong secret fails closed", wrong_secret_ok),
                ("verify receipt recorded valid=true", any(r.get("action") == "api-keys/verify"
                 and r.get("valid") for r in lines)),
            ]
        finally:
            server.shutdown()
        failed = [name for name, ok in checks if not ok]
        for name, ok in checks:
            print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        print(("PASS — " if not failed else "FAIL — ")
              + f"{len(checks) - len(failed)}/{len(checks)} provisioning self-test checks")
        return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", nargs="?", choices=["provision", "grant-reviewer"], default=None)
    parser.add_argument("--realm")
    parser.add_argument("--identifier")
    parser.add_argument("--secret-env", help="env var holding the account secret")
    parser.add_argument("--secret-file", help="file holding the account secret")
    parser.add_argument("--scopes", default=",".join(DEFAULT_SCOPES))
    parser.add_argument("--share-bundle", action="store_true")
    parser.add_argument("--account-id", help="for grant-reviewer")
    parser.add_argument("--admin-session", help="for grant-reviewer (admin realm session id)")
    parser.add_argument("--base", default=None, help="identity base (default: realm registry port)")
    parser.add_argument("--list-realms", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    base = (args.base or _identity_base()).rstrip("/")
    if args.list_realms:
        return list_realms(base)
    if args.command == "provision":
        if not (args.realm and args.identifier):
            raise SystemExit("provision needs --realm and --identifier")
        provision(base, args.realm, args.identifier, _resolve_secret(args),
                  [s for s in args.scopes.split(",") if s], share_bundle=args.share_bundle)
        print(f"  receipts → {RECEIPTS_PATH.relative_to(REPO)}")
        return 0
    if args.command == "grant-reviewer":
        if not (args.realm and args.account_id and args.admin_session):
            raise SystemExit("grant-reviewer needs --realm, --account-id, --admin-session")
        return 0 if grant_reviewer(args.realm, args.account_id, args.admin_session) else 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
