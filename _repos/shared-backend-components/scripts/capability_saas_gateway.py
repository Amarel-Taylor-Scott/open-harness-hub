#!/usr/bin/env python3
"""capability_saas_gateway — the hosted SaaS surface: remote MCP + agent API + signup/keys + metering, one process.

Owner (2026-07-10): "build this out into a SaaS, fully working, start to finish … I can provide you with a GitHub
token, a Fly.io token." This gateway is that product surface, assembled ENTIRELY from engines that already exist
(reuse-first; no parallel implementations):

  signup/keys   -> scripts.identity_local_service embedded IN-PROCESS (register -> onboard -> login -> mint, the
                   exact provision_access flow); raw key returned ONCE, only hashes persist.
  POST /mcp     -> MCP over HTTP (JSON-RPC POST, Bearer key): capability_retrieval_mcp_server.dispatch — the same
                   7 tools local Claude Code uses, now remote. Hosted default scope=governed (the bundled corpus).
  POST /v1/agent-> the deterministic agent tool (capability_agent_tool.handle_request) with tenant-denied actions
                   (provisioning + waterfall.apply stay owner-only) and per-tenant ledgers.
  metering      -> every authed request appends an invocation receipt in the billing_ledger shape
                   (model_class=capability_tool_call); GET /v1/usage = live rollup + billing_plane draft invoice.
  plans/limits  -> capability_free / capability_pro (DRAFT pricing, owner-confirmable) with per-day request
                   limits enforced 429; while payments are disabled, upgrade records the plan and returns the
                   draft invoice. With the three STRIPE_* deployment secrets set, /v1/billing/checkout opens a
                   hosted Stripe Checkout, the signed /v1/billing/webhook flips the plan, and /v1/upgrade
                   becomes 402 payment-required — /v1/billing/status COMPUTES the state (never a faked charge).

Every response is a governed candidate (serves_truth=false). Raw keys and secrets never land in receipts, logs,
or state files (enforced by the self-test, which walks every persisted file). Deploy: scripts/
build_capability_saas_bundle.py assembles the Fly.io bundle; scripts/deploy_capability_saas.py ships it when
FLY_API_TOKEN is present.

    PYTHONPATH=. python3 scripts/capability_saas_gateway.py --self-test
    PYTHONPATH=. python3 scripts/capability_saas_gateway.py --serve --port 8080 --data-dir /data
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets as _secrets
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from scripts._repo_paths import install as _install  # noqa: E402

_install()  # all code roots (src.openhubforai auth kit, src.teleon, …) — a hosted process starts from anywhere

SERVICE_NAME = "taedri-gateway"
SERVICE_VERSION = "0.3.0"   # 0.3.0: Stripe payments seam (checkout + signed webhook), env-gated
#: env overrides (deployment config; defaults are the local dev values). TAEDRI_* is the product-facing
#: name (owner 2026-07-11: no acronyms — this product is Taedri under aidonerightcorp); the legacy OH_SAAS_*
#: names (OpenHub-era substrate branding) remain ACCEPTED fallbacks so already-deployed machines, images,
#: and secrets keep working. All documentation uses only the TAEDRI_* names.
DATA_DIR_ENVIRONMENT_VARIABLE = "TAEDRI_DATA_DIR"
LEGACY_DATA_DIR_ENVIRONMENT_VARIABLE = "OH_SAAS_DATA_DIR"
REALM_ENVIRONMENT_VARIABLE = "TAEDRI_REALM"
LEGACY_REALM_ENVIRONMENT_VARIABLE = "OH_SAAS_REALM"
GOVERNED_ONLY_ENVIRONMENT_VARIABLE = "TAEDRI_GOVERNED_ONLY"   # "1" (hosted default) -> search scope=governed
LEGACY_GOVERNED_ONLY_ENVIRONMENT_VARIABLE = "OH_SAAS_GOVERNED_ONLY"


def _environment_setting(preferred: str, legacy: str, default: str = "") -> str:
    """Product-named environment variable first, legacy OpenHub-era name second, then the default."""
    return os.environ.get(preferred) or os.environ.get(legacy) or default


_DEFAULT_DATA_DIR = _REPO / "data" / "dev-intel" / "capability_saas_gateway"
#: renamed from "openhubforai" 2026-07-11 (pre-customer; receipts already on a volume keep their original
#: realm label — lossless — and can be re-labeled at the first real billing export if ever needed)
_DEFAULT_REALM = "taedri"
MAX_BODY_BYTES = 1_000_000          # control-plane requests are small; bodies stay bounded
_KEY_VERIFY_CACHE_SECONDS = 60      # in-process verified-key cache (identity stays the authority)
_SIGNUP_SCOPES = ["registry:read", "registry:install"]
MODEL_CLASS_TOOL_CALL = "capability_tool_call"   # billing_ledger class for gateway invocations (v1 rate 0.0)

#: PLAN LIMITS (requests/day) — the gateway-enforced side of the plan; prices live in billing_plane.PLANS
#: (single source for money). DRAFT pricing pending owner confirmation; limits are deliberately generous-free.
PLAN_REQUEST_LIMITS_PER_DAY: dict[str, int] = {"capability_free": 200, "capability_pro": 20_000}
DEFAULT_PLAN = "capability_free"

#: CONTRIBUTOR BONUS (owner 2026-07-10: "free or discounted tier if people share their data or primitives into
#: the large corpus … shown as a bonus after someone has reached their limit — continue using this by submitting
#: anonymized data"). DRAFT amounts, owner-confirmable like all pricing. Contributions are ANONYMIZED (contributor
#: = digest, identity fields stripped) and CANDIDATE-ONLY intake — a shared card never enters the serving corpus
#: without the owner promotion path.
CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD = 5
CONTRIBUTOR_BONUS_DAILY_CAP = 200
#: identity-shaped fields stripped from shared cards before persistence (exact-name denylist; `blocking_keys`
#: and other content fields stay).
_CONTRIBUTION_STRIPPED_FIELDS = {"email", "account_id", "owner", "owner_key", "api_key", "secret", "key_id",
                                 "tenant", "user"}

#: PUBLIC TRIAL KEY (owner 2026-07-10: "a free trial key that is limited to 100 calls per day and can be
#: publicly accessible and included in the trial notebook (it should have rate limits and abuse detection)").
#: The key is public BY DESIGN (it ships in the Kaggle notebook), so the protections are limits, not secrecy:
#: a SHARED pool of TRIAL_REQUEST_LIMIT_PER_DAY requests/day, a per-IP daily slice so one caller cannot drain
#: the pool, a READ-ONLY action surface (upgrade/contribute/reuse-outcome writes denied), and abuse receipts
#: (IP digests only, never raw IPs) for over-cap callers.
TRIAL_PUBLIC_KEY = "ak_trial_taedri_public_notebook"
TRIAL_KEY_ENVIRONMENT_VARIABLE = "TAEDRI_TRIAL_KEY"   # deployment override; default is the public constant
LEGACY_TRIAL_KEY_ENVIRONMENT_VARIABLE = "OH_SAAS_TRIAL_KEY"
TRIAL_PLAN = "capability_trial"
TRIAL_REQUEST_LIMIT_PER_DAY = 100
TRIAL_PER_IP_LIMIT_PER_DAY = 25
#: agent actions the shared trial key may call (read-only surface; everything else points to signup). Includes
#: the read-only composition + network views so the trial notebook can demo groups/frameworks/remix/integrate
#: and grid search.
TRIAL_ALLOWED_ACTIONS = {"actions.list", "retrieval.search", "retrieval.compose", "corpus.status",
                         "composition.groups", "composition.frameworks", "composition.remix",
                         "composition.integrate", "network.list", "network.grid_search",
                         "deployment.estimate", "deployment.profile_network",
                         "capability.search", "capability.get", "capability.remix", "capability.stats",
                         "capability.analytics", "capability.reuse"}  # capability.add stays tenant-only
#: MCP tools denied on the trial key (writes; the 7-tool read surface stays open).
TRIAL_DENIED_MCP_TOOLS = {"record_reuse_outcome"}

#: STRIPE payments seam (owner-gated activation; a charge is never faked). Env NAMES only — the values live in
#: deployment secrets (fly secrets / GitHub Actions secrets), never in code or the repo. Payments stay DISABLED
#: (plans recorded, nothing charged) until ALL THREE are set on the deployment; /v1/billing/status COMPUTES the
#: state from env presence so prose can never drift from reality.
STRIPE_API_KEY_ENVIRONMENT_VARIABLE = "STRIPE_API_KEY"
STRIPE_PRICE_ID_PRO_ENVIRONMENT_VARIABLE = "STRIPE_PRICE_ID_PRO"
STRIPE_WEBHOOK_SECRET_ENVIRONMENT_VARIABLE = "STRIPE_WEBHOOK_SECRET"
STRIPE_API_BASE_URL = "https://api.stripe.com"
STRIPE_WEBHOOK_TOLERANCE_SECONDS = 300   # Stripe's recommended replay window for signed webhook timestamps
PRO_PLAN = "capability_pro"

#: NEWS (owner 2026-07-10: "have a news/blog section of the page"). Newest first. Entries are shipped-fact only —
#: each row states something that actually went live; marketing futures don't belong here.
TAEDRI_NEWS: list[dict[str, str]] = [
    {"date": "2026-07-10", "title": "A public trial key + example Kaggle notebook",
     "body": "Try Taedri with zero signup: a shared read-only trial key (100 requests/day pooled, per-address "
             "slice, abuse-logged) ships inside an example Kaggle notebook that searches, reuse-guards, and "
             "composes against this deployment."},
    {"date": "2026-07-10", "title": "Share into the corpus, keep going free",
     "body": "Hit your daily limit? POST /v1/contribute shares anonymized primitives into the shared corpus and "
             "grants bonus requests the same day. Contributions stay candidate-only until reviewed."},
    {"date": "2026-07-10", "title": "A containerized user machine for CI-grade emulation",
     "body": "taedri-emulator: one docker run exercises the whole product — API lifecycle, MCP protocol, a real "
             "claude-CLI connect, and a real Chromium browser journey — with an optional watchable VNC desktop."},
    {"date": "2026-07-10", "title": "TAEDRI is the product",
     "body": "The hosted capability gateway has a name. Same thesis as always: this already exists — don't "
             "rebuild it. Retrieval, reuse guard, and deterministic composition over a governed corpus."},
    {"date": "2026-07-10", "title": "The working user loop is live",
     "body": "Signup, sessions, a dashboard, private primitives (searchable only by you), tenant logs, usage "
             "with draft invoices, and a same-origin test console at /console."},
]

#: agent-tool actions a TENANT may not call (owner-only surfaces: cloud spend + vector-spend writes).
TENANT_DENIED_ACTIONS = {"provision.plan", "provision.preflight", "provision.status", "provision.apply",
                         "waterfall.apply"}
#: ADMINISTRATOR key (set via `fly secrets set TAEDRI_ADMIN_KEY=…`): unlocks /v1/admin/* — primitive CRUD (append-only
#: overlay + tombstones, never destructive), reindex, and ledger export. Unset -> admin surface is disabled.
OWNER_KEY_ENVIRONMENT_VARIABLE = "TAEDRI_ADMIN_KEY"
LEGACY_OWNER_KEY_ENVIRONMENT_VARIABLE = "OH_SAAS_OWNER_KEY"
_MAX_CARDS_PER_ADMIN_POST = 10_000   # bounded admin batches; bulk loads loop
_SESSION_COOKIE_NAME = "taedri_session"
_SESSION_TTL_SECONDS = 3600          # matches the identity realm session TTL default
_MAX_CARDS_PER_TENANT_POST = 500     # private-primitive batch bound (tenants; owner bulk uses /v1/admin)
_MAX_LOG_ROWS = 500                  # /v1/logs page bound


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _digest16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class CapabilitySaasGateway:
    """All state + wiring for one gateway process (embedded identity, receipts, rate counters, fixtures)."""

    def __init__(self, data_dir: Optional[Path] = None, fixtures: Optional[dict] = None) -> None:
        self.data_dir = Path(data_dir or _environment_setting(DATA_DIR_ENVIRONMENT_VARIABLE,
                                                              LEGACY_DATA_DIR_ENVIRONMENT_VARIABLE)
                             or _DEFAULT_DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.realm = _environment_setting(REALM_ENVIRONMENT_VARIABLE, LEGACY_REALM_ENVIRONMENT_VARIABLE,
                                          _DEFAULT_REALM)
        self.fixtures = fixtures or {}
        self.receipts_path = self.data_dir / "invocations.jsonl"
        self.tenants_path = self.data_dir / "tenants.json"
        self._tenants_lock = threading.Lock()
        self._rate_lock = threading.Lock()
        self._rate_counters: dict[tuple[str, str], int] = {}       # (key_id, date) -> requests today
        self._verify_cache: dict[str, tuple[dict, float]] = {}     # sha256(raw key) -> (record, expires)
        # embedded identity service (the REAL engine, in-process, own state dir; hashes only on disk)
        from scripts.identity_local_service import start_service  # noqa: PLC0415
        self._identity_server, self._identity_thread, identity_port = start_service(
            port=0, state_dir=self.data_dir / "identity")
        self._identity_base = f"http://127.0.0.1:{identity_port}"

    # ---------------------------------------------------------------- identity plumbing (reuse, not rebuild)
    def _identity_post(self, path: str, body: dict) -> tuple[int, dict]:
        request = urllib.request.Request(self._identity_base + path,
                                         data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as error:  # type: ignore[attr-defined]
            return error.code, json.loads(error.read().decode("utf-8") or "{}")

    def signup(self, email: str, secret: str = "") -> dict:
        """register -> onboard every step -> login -> mint key (the provision_access flow, one call).
        Returns the RAW key + generated secret ONCE — neither is persisted in cleartext anywhere."""
        identifier = email.strip().lower()
        if "@" not in identifier or len(identifier) > 320:
            return {"ok": False, "error": "signup requires a valid `email`"}
        secret = secret or _secrets.token_hex(12)
        prefix = f"/api/identity/{self.realm}"
        status, registered = self._identity_post(f"{prefix}/register",
                                                 {"identifier": identifier, "secret": secret})
        if status in (200, 201) and registered.get("account_id"):
            for step in registered.get("onboarding_steps") or []:
                self._identity_post(f"{prefix}/onboard", {"account_id": registered["account_id"], "step": step})
        status, session = self._identity_post(f"{prefix}/login", {"identifier": identifier, "secret": secret})
        if status != 200 or not session.get("session_id"):
            return {"ok": False, "error": "signup failed at login (existing account with a different secret?)"}
        status, minted = self._identity_post(f"{prefix}/api-keys/mint",
                                             {"session_id": session["session_id"], "scopes": _SIGNUP_SCOPES})
        if status not in (200, 201) or not minted.get("api_key"):
            return {"ok": False, "error": f"key mint failed ({status})"}
        account_id = str(session.get("account_id") or registered.get("account_id") or "")
        with self._tenants_lock:
            tenants = self._load_tenants()
            tenants.setdefault(account_id, {"plan": DEFAULT_PLAN, "email_digest": _digest16(identifier),
                                            "created": _now_iso()})
            self._save_tenants(tenants)
        return {"ok": True, "account_id": account_id, "key_id": minted.get("key_id"),
                "api_key": minted["api_key"],   # shown ONCE — never persisted in cleartext
                "account_secret": secret,        # shown ONCE — store it; needed to mint more keys
                "plan": DEFAULT_PLAN, "realm": self.realm,
                "requests_per_day": PLAN_REQUEST_LIMITS_PER_DAY[DEFAULT_PLAN],
                "endpoints": {"mcp": "/mcp", "agent": "/v1/agent", "usage": "/v1/usage"},
                "candidate": True, "serves_truth": False}

    def verify_key(self, raw_key: str) -> Optional[dict]:
        if not raw_key:
            return None
        cache_id = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        cached = self._verify_cache.get(cache_id)
        if cached and cached[1] > time.monotonic():
            return cached[0]
        status, verified = self._identity_post(f"/api/identity/{self.realm}/api-keys/verify",
                                               {"api_key": raw_key})
        if status != 200 or not verified.get("valid"):
            return None
        self._verify_cache[cache_id] = (verified, time.monotonic() + _KEY_VERIFY_CACHE_SECONDS)
        return verified

    # ---------------------------------------------------------------- tenants / plans / rate limits
    def _load_tenants(self) -> dict:
        if self.tenants_path.exists():
            try:
                return json.loads(self.tenants_path.read_text())
            except json.JSONDecodeError:
                pass
        return {}

    def _save_tenants(self, tenants: dict) -> None:
        tmp = self.tenants_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(tenants, indent=2, sort_keys=True))
        os.replace(tmp, self.tenants_path)

    def tenant_plan(self, account_id: str) -> str:
        plan = self._load_tenants().get(account_id, {}).get("plan", DEFAULT_PLAN)
        return plan if plan in PLAN_REQUEST_LIMITS_PER_DAY else DEFAULT_PLAN

    def set_plan(self, account_id: str, plan: str) -> dict:
        if plan not in PLAN_REQUEST_LIMITS_PER_DAY:
            return {"ok": False, "error": f"unknown plan {plan!r}; known {sorted(PLAN_REQUEST_LIMITS_PER_DAY)}"}
        with self._tenants_lock:
            tenants = self._load_tenants()
            tenants.setdefault(account_id, {"created": _now_iso()})["plan"] = plan
            self._save_tenants(tenants)
        return {"ok": True, "account_id": account_id, "plan": plan,
                "requests_per_day": PLAN_REQUEST_LIMITS_PER_DAY[plan]}

    def _daily_limit(self, plan: str) -> int:
        override = self.fixtures.get("requests_per_day_override")
        return int(override) if override else PLAN_REQUEST_LIMITS_PER_DAY[plan]

    def check_rate_limit(self, key_id: str, plan: str, bonus: int = 0) -> tuple[bool, int, int]:
        """(allowed, used_today, limit). Counter seeds from today's persisted receipts (restart-safe);
        `bonus` = contributor bonus requests earned today (account-level), added on top of the plan limit."""
        date = _today()
        with self._rate_lock:
            counter_key = (key_id, date)
            if counter_key not in self._rate_counters:
                self._rate_counters[counter_key] = sum(
                    1 for r in self._load_receipts()
                    if r.get("key_id") == key_id and str(r.get("ts", "")).startswith(date))
            used = self._rate_counters[counter_key]
            limit = self._daily_limit(plan) + max(0, bonus)
            if used >= limit:
                return False, used, limit
            self._rate_counters[counter_key] = used + 1
            return True, used + 1, limit

    # ------------------------------------------------- contributor bonus (share into the corpus, keep going)
    def _contributions_path(self) -> Path:
        return self.data_dir / "corpus_contributions.jsonl"

    def _contributor_bonus_path(self) -> Path:
        return self.data_dir / "contributor_bonus.json"

    def bonus_requests_today(self, account_id: str) -> int:
        """Bonus requests this account earned today by contributing (persisted; capped at grant time)."""
        try:
            granted = json.loads(self._contributor_bonus_path().read_text())
        except (OSError, json.JSONDecodeError):
            granted = {}
        return int(granted.get(account_id, {}).get(_today(), 0))

    def contribute_to_corpus(self, account_id: str, cards: list) -> dict:
        """Owner directive 2026-07-10: share anonymized primitives -> bonus requests today. Contributions are
        ANONYMIZED (contributor = digest16(account_id); identity-shaped fields stripped) and CANDIDATE-ONLY —
        they land in corpus_contributions.jsonl for owner review, never directly in the serving corpus."""
        if not isinstance(cards, list) or not cards:
            return {"ok": False, "error": "body must be {cards: [...]}"}
        if len(cards) > _MAX_CARDS_PER_TENANT_POST:
            return {"ok": False, "error": f"batch too large (max {_MAX_CARDS_PER_TENANT_POST})"}
        contributor = _digest16(account_id)
        accepted, rejected = 0, []
        with self._contributions_path().open("a") as handle:
            for card in cards:
                if not isinstance(card, dict) or not str(card.get("primitive_id") or "").strip():
                    rejected.append(str(card)[:80])
                    continue
                anonymized = {k: v for k, v in card.items() if k not in _CONTRIBUTION_STRIPPED_FIELDS}
                handle.write(json.dumps({"contributor": contributor, "card": anonymized,
                                         "shared_at": _now_iso(), "status": "pending_review",
                                         "candidate": True, "serves_truth": False}, sort_keys=True) + "\n")
                accepted += 1
        with self._rate_lock:
            try:
                granted = json.loads(self._contributor_bonus_path().read_text())
            except (OSError, json.JSONDecodeError):
                granted = {}
            today_row = granted.setdefault(account_id, {})
            before = int(today_row.get(_today(), 0))
            earned = min(CONTRIBUTOR_BONUS_DAILY_CAP,
                         before + accepted * CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD)
            granted[account_id] = {_today(): earned}   # keep only today (yesterday's bonus expired anyway)
            self._contributor_bonus_path().write_text(json.dumps(granted, sort_keys=True))
        return {"ok": True, "accepted": accepted, "rejected": rejected[:10],
                "bonus_requests_today": earned, "bonus_added_now": earned - before,
                "daily_bonus_cap": CONTRIBUTOR_BONUS_DAILY_CAP,
                "note": "thank you — contributions are anonymized (contributor digest only), stay candidate-only "
                        "until owner review, and never serve as truth without promotion",
                "candidate": True, "serves_truth": False}

    # ------------------------------------------------- public trial key (shared pool + per-IP slice + abuse log)
    def trial_key(self) -> str:
        return _environment_setting(TRIAL_KEY_ENVIRONMENT_VARIABLE, LEGACY_TRIAL_KEY_ENVIRONMENT_VARIABLE,
                                    TRIAL_PUBLIC_KEY)

    def _abuse_events_path(self) -> Path:
        return self.data_dir / "abuse_events.jsonl"

    def _record_abuse(self, kind: str, ip_digest: str, detail: str = "") -> None:
        """Abuse receipts carry IP DIGESTS only — enough to see repeat offenders, never the raw address."""
        with self._abuse_events_path().open("a") as handle:
            handle.write(json.dumps({"ts": _now_iso(), "kind": kind, "ip_digest": ip_digest,
                                     "detail": detail[:120], "candidate": True, "serves_truth": False},
                                    sort_keys=True) + "\n")

    def check_trial_limits(self, client_ip: str) -> tuple[bool, int, int, str]:
        """(allowed, used_today, limit, blocked_reason). The shared pool seeds from persisted receipts
        (restart-safe); the per-IP slice is in-memory per process (honest limitation: a restart forgets IP
        counts for the rest of the day — the pool cap still bounds total spend)."""
        date = _today()
        ip_digest = _digest16(client_ip or "unknown")
        pool_limit = int(self.fixtures.get("trial_pool_override") or TRIAL_REQUEST_LIMIT_PER_DAY)
        ip_limit = int(self.fixtures.get("trial_ip_override") or TRIAL_PER_IP_LIMIT_PER_DAY)
        with self._rate_lock:
            pool_counter = ("trial-public", date)
            ip_counter = (f"trial-ip-{ip_digest}", date)
            if pool_counter not in self._rate_counters:
                self._rate_counters[pool_counter] = sum(
                    1 for r in self._load_receipts()
                    if r.get("key_id") == "trial-public" and str(r.get("ts", "")).startswith(date))
            pool_used = self._rate_counters[pool_counter]
            ip_used = self._rate_counters.get(ip_counter, 0)
            if pool_used >= pool_limit:
                self._record_abuse("trial_pool_exhausted", ip_digest, f"pool {pool_used}/{pool_limit}")
                return False, pool_used, pool_limit, "the shared trial pool is exhausted for today"
            if ip_used >= ip_limit:
                self._record_abuse("trial_ip_cap", ip_digest, f"ip {ip_used}/{ip_limit}")
                return False, ip_used, ip_limit, "this address used its trial slice for today"
            self._rate_counters[pool_counter] = pool_used + 1
            self._rate_counters[ip_counter] = ip_used + 1
            return True, pool_used + 1, pool_limit, ""

    def trial_usage(self) -> dict:
        date = _today()
        with self._rate_lock:
            used = self._rate_counters.get(("trial-public", date), 0)
        return {"plan": TRIAL_PLAN, "key": "shared public trial key", "requests_today": used,
                "requests_per_day": int(self.fixtures.get("trial_pool_override") or
                                        TRIAL_REQUEST_LIMIT_PER_DAY),
                "per_ip_per_day": int(self.fixtures.get("trial_ip_override") or TRIAL_PER_IP_LIMIT_PER_DAY),
                "note": "the trial key is shared and read-only — sign up free for your own "
                        f"{PLAN_REQUEST_LIMITS_PER_DAY[DEFAULT_PLAN]} requests/day: POST /v1/signup {{email}}",
                "candidate": True, "serves_truth": False}

    # ---------------------------------------------------------------- metering (billing_ledger receipt shape)
    def meter(self, key_id: str, kind: str, request_bytes: int, response_bytes: int) -> None:
        receipt = {"receipt_id": f"inv-{_digest16(f'{key_id}|{kind}|{_now_iso()}|{_secrets.token_hex(4)}')}",
                   "ts": _now_iso(), "realm": self.realm, "key_id": key_id,
                   "model_class": MODEL_CLASS_TOOL_CALL,
                   "input_tokens": max(1, request_bytes // 4), "output_tokens": max(1, response_bytes // 4),
                   "kind": kind, "candidate": True, "serves_truth": False}
        with self.receipts_path.open("a") as handle:
            handle.write(json.dumps(receipt, sort_keys=True) + "\n")

    def _load_receipts(self) -> list[dict]:
        if not self.receipts_path.exists():
            return []
        return [json.loads(line) for line in self.receipts_path.read_text().splitlines() if line.strip()]

    def usage(self, verified: dict) -> dict:
        key_id = str(verified.get("key_id") or "")
        account_id = str(verified.get("account_id") or "")
        plan = self.tenant_plan(account_id)
        mine = [r for r in self._load_receipts() if r.get("key_id") == key_id]
        today = sum(1 for r in mine if str(r.get("ts", "")).startswith(_today()))
        from scripts import billing_ledger, billing_plane  # noqa: PLC0415
        month_statement = billing_ledger.statement(mine, realm=self.realm, month=_month())
        invoice = billing_plane.draft_invoice({"id": account_id, "realm": self.realm, "plan": plan},
                                              mine, month=_month())
        return {"account_id": account_id, "key_id": key_id, "plan": plan,
                "requests_today": today, "requests_per_day": self._daily_limit(plan),
                "bonus_requests_today": self.bonus_requests_today(account_id),
                "requests_month": len([r for r in mine if str(r.get("ts", "")).startswith(_month())]),
                "month_statement": month_statement, "draft_invoice": invoice,
                "note": "invoice is a DRAFT from the receipt ledger; " + self.billing_status()["note"],
                "candidate": True, "serves_truth": False}

    # ---------------------------------------------------------------- payments (Stripe seam — env-gated, never faked)
    def billing_status(self) -> dict:
        """Computed payment state — presence of the three STRIPE_* deployment secrets, never a hand-typed claim."""
        values = {name: os.environ.get(name, "") for name in (
            STRIPE_API_KEY_ENVIRONMENT_VARIABLE, STRIPE_PRICE_ID_PRO_ENVIRONMENT_VARIABLE,
            STRIPE_WEBHOOK_SECRET_ENVIRONMENT_VARIABLE)}
        missing = sorted(name for name, value in values.items() if not value)
        api_key = values[STRIPE_API_KEY_ENVIRONMENT_VARIABLE]
        mode = "disabled" if not api_key else ("live" if api_key.startswith("sk_live_") else "test")
        return {"payments_enabled": not missing, "mode": mode,
                "missing_environment_variables": missing,
                "checkout": "POST /v1/billing/checkout (Bearer key or session) -> hosted Stripe Checkout URL",
                "webhook": "POST /v1/billing/webhook (Stripe-signed; flips the tenant plan on completed checkout)",
                "note": ("payments are LIVE via Stripe Checkout — a paid plan is entered only through a "
                         "completed, webhook-verified checkout" if not missing else
                         "payments are not enabled yet: plans are recorded, nothing is charged — set the "
                         "missing deployment secrets to activate Stripe Checkout"),
                "candidate": True, "serves_truth": False}

    def _stripe_post(self, path: str, fields: dict[str, str]) -> tuple[int, dict]:
        """Form-encoded Stripe API call (stdlib only). fixtures['stripe_transport'] overrides for hermetic tests."""
        transport = self.fixtures.get("stripe_transport")
        if transport is not None:
            return transport(path, fields)
        request = urllib.request.Request(
            STRIPE_API_BASE_URL + path, data=urllib.parse.urlencode(fields).encode("utf-8"), method="POST",
            headers={"Authorization": f"Bearer {os.environ.get(STRIPE_API_KEY_ENVIRONMENT_VARIABLE, '')}",
                     "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.status, json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as error:  # type: ignore[attr-defined]
            try:
                return error.code, json.loads(error.read().decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return error.code, {"error": "stripe error body was not json"}

    def create_checkout(self, verified: dict, base_url: str) -> tuple[int, dict]:
        """Start a hosted Stripe Checkout for the pro plan. Disabled -> honest 503 pointer, never a fake charge."""
        status = self.billing_status()
        if not status["payments_enabled"]:
            return 503, {"ok": False, **status}
        account_id = str(verified.get("account_id") or "")
        fields = {"mode": "subscription",
                  "line_items[0][price]": os.environ.get(STRIPE_PRICE_ID_PRO_ENVIRONMENT_VARIABLE, ""),
                  "line_items[0][quantity]": "1",
                  "client_reference_id": account_id,
                  "metadata[account_id]": account_id,
                  "subscription_data[metadata][account_id]": account_id,
                  "success_url": base_url + "/dashboard?checkout=success",
                  "cancel_url": base_url + "/dashboard?checkout=cancelled"}
        email = str(verified.get("email") or "")
        if email:
            fields["customer_email"] = email
        code, session = self._stripe_post("/v1/checkout/sessions", fields)
        if code != 200 or not session.get("url"):
            return 502, {"ok": False, "error": f"stripe checkout create failed ({code})",
                         "stripe_error": (session.get("error") or {}).get("message", "")[:200],
                         "candidate": True, "serves_truth": False}
        self.meter(str(verified.get("key_id") or ""), "billing:checkout_created", 0, 0)
        return 200, {"ok": True, "checkout_url": session["url"], "session_id": str(session.get("id") or ""),
                     "plan": PRO_PLAN, "mode": status["mode"],
                     "note": "complete payment on the Stripe-hosted page; the signed webhook flips your plan",
                     "candidate": True, "serves_truth": False}

    @staticmethod
    def _verify_stripe_signature(payload: bytes, signature_header: str, secret: str) -> bool:
        """Constant-time verification of Stripe's `t=<ts>,v1=<hmac>` webhook scheme with a replay window."""
        pairs = [part.split("=", 1) for part in signature_header.split(",") if "=" in part]
        timestamp = next((value.strip() for key, value in pairs if key.strip() == "t"), "")
        candidates = [value.strip() for key, value in pairs if key.strip() == "v1"]
        if not timestamp.isdigit() or not candidates:
            return False
        if abs(time.time() - int(timestamp)) > STRIPE_WEBHOOK_TOLERANCE_SECONDS:
            return False
        expected = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("utf-8") + payload,
                            hashlib.sha256).hexdigest()
        return any(hmac.compare_digest(expected, candidate) for candidate in candidates)

    def stripe_webhook(self, payload: bytes, signature_header: str) -> tuple[int, dict]:
        """Stripe-signed events: completed checkout -> pro plan; deleted subscription -> back to the free plan."""
        secret = os.environ.get(STRIPE_WEBHOOK_SECRET_ENVIRONMENT_VARIABLE, "")
        if not secret:
            return 503, {"ok": False, **self.billing_status()}
        if not self._verify_stripe_signature(payload, signature_header, secret):
            return 400, {"ok": False, "error": "invalid stripe signature", "candidate": True,
                         "serves_truth": False}
        try:
            event = json.loads(payload.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return 400, {"ok": False, "error": "webhook payload was not json", "candidate": True,
                         "serves_truth": False}
        kind = str(event.get("type") or "")
        data = (event.get("data") or {}).get("object") or {}
        handled = "ignored"
        if kind == "checkout.session.completed":
            account_id = str(data.get("client_reference_id")
                             or (data.get("metadata") or {}).get("account_id") or "")
            if account_id:
                self.set_plan(account_id, PRO_PLAN)
                self.meter(f"stripe:{account_id}", "billing:plan_upgraded_paid", len(payload), 0)
                handled = f"plan -> {PRO_PLAN}"
        elif kind == "customer.subscription.deleted":
            account_id = str((data.get("metadata") or {}).get("account_id") or "")
            if account_id:
                self.set_plan(account_id, DEFAULT_PLAN)
                self.meter(f"stripe:{account_id}", "billing:plan_downgraded_cancelled", len(payload), 0)
                handled = f"plan -> {DEFAULT_PLAN}"
        return 200, {"ok": True, "received": kind or "unknown", "handled": handled,
                     "candidate": True, "serves_truth": False}

    # ---------------------------------------------------------------- MCP + agent dispatch (reused engines)
    def mcp_dispatch(self, request: dict) -> Optional[dict]:
        from scripts import capability_retrieval_mcp_server as _mcp  # noqa: PLC0415
        method = request.get("method")
        params = request.get("params") or {}
        # hosted default: the bundled governed corpus (explicit scope in the request always wins)
        if (method == "tools/call" and isinstance(params, dict)
                and params.get("name") == "primitive_search"
                and _environment_setting(GOVERNED_ONLY_ENVIRONMENT_VARIABLE,
                                         LEGACY_GOVERNED_ONLY_ENVIRONMENT_VARIABLE, "1") == "1"):
            arguments = dict(params.get("arguments") or {})
            arguments.setdefault("scope", "governed")
            request = {**request, "params": {**params, "arguments": arguments}}
            params = request["params"]
        if "index" in self.fixtures and method == "tools/call":  # hermetic proof lane (never reachable via JSON)
            result = _mcp._handle_tools_call_for_test(params, index=self.fixtures["index"])
            return {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
        serving_index = self._loaded_serving_index()
        if (serving_index is not None and method == "tools/call"
                and isinstance(params, dict) and params.get("name") == "primitive_search"):
            # the /data serving index (admin CRUD + reindex output) outranks the image-baked default
            result = _mcp._handle_tools_call_for_test(params, index=serving_index)
            return {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
        return _mcp.dispatch(request)

    def agent_dispatch(self, request: dict) -> dict:
        from scripts import capability_agent_tool as _agent  # noqa: PLC0415
        action = str(request.get("action") or "")
        if action in TENANT_DENIED_ACTIONS:
            return {"ok": False, "action": action, "result": None, "auth_mode": "tenant",
                    "error": f"action {action!r} is owner-only on the hosted gateway (tenant allowlist)",
                    "candidate": True, "serves_truth": False}
        args = dict(request.get("args") or {})
        include_mine = bool(args.pop("include_mine", False))
        account_id = str(request.get("_account_id") or "")
        # hosted default mirrors the MCP lane: serve the bundled governed corpus (explicit scope always wins)
        if (action == "retrieval.search"
                and _environment_setting(GOVERNED_ONLY_ENVIRONMENT_VARIABLE,
                                         LEGACY_GOVERNED_ONLY_ENVIRONMENT_VARIABLE, "1") == "1"):
            args.setdefault("scope", "governed")
        agent_fixtures = {"usage_ledger_path": self.data_dir / "tenant_usage" / "events.jsonl"}
        if "index" in self.fixtures:
            agent_fixtures["index"] = self.fixtures["index"]
        envelope = _agent.handle_request({"action": action, "args": args}, fixtures=agent_fixtures)
        if (include_mine and account_id and action == "retrieval.search" and envelope.get("ok")
                and isinstance(envelope.get("result"), dict)):
            mine = self.search_mine(account_id, str(args.get("query") or ""), int(args.get("limit") or 10))
            public_hits = envelope["result"].get("results") or []
            envelope["result"]["results"] = mine + public_hits   # private first, clearly labeled — never dropped
            envelope["result"]["private_hits"] = len(mine)
        return envelope

    # ---------------------------------------------------------------- sessions (login -> cookie -> dashboard)
    def _identity_get(self, path: str) -> tuple[int, dict]:
        try:
            with urllib.request.urlopen(self._identity_base + path, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as error:  # type: ignore[attr-defined]
            return error.code, json.loads(error.read().decode("utf-8") or "{}")

    def _sessions_path(self) -> Path:
        return self.data_dir / "sessions.json"

    def _load_sessions(self) -> dict:
        if self._sessions_path().exists():
            try:
                return json.loads(self._sessions_path().read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def login_session(self, email: str, secret: str) -> dict:
        """Identity login -> a gateway session (cookie value = the identity session id; only its HASH persists)."""
        status, session = self._identity_post(f"/api/identity/{self.realm}/login",
                                              {"identifier": email.strip().lower(), "secret": secret})
        if status != 200 or not session.get("session_id"):
            return {"ok": False, "error": "login failed — check email and account secret"}
        sessions = self._load_sessions()
        sessions[_digest16(session["session_id"])] = {
            "account_id": session.get("account_id"), "identity_session_id": session["session_id"],
            "expires_at": time.time() + _SESSION_TTL_SECONDS}
        self._sessions_path().write_text(json.dumps(sessions))
        return {"ok": True, "session_id": session["session_id"], "account_id": session.get("account_id"),
                "expires_in_seconds": _SESSION_TTL_SECONDS, "candidate": True, "serves_truth": False}

    def resolve_session(self, cookie_value: str) -> Optional[dict]:
        if not cookie_value:
            return None
        record = self._load_sessions().get(_digest16(cookie_value))
        if not record or record.get("expires_at", 0) < time.time():
            return None
        return record

    def logout_session(self, cookie_value: str) -> None:
        sessions = self._load_sessions()
        sessions.pop(_digest16(cookie_value), None)
        self._sessions_path().write_text(json.dumps(sessions))

    def account_key_ids(self, record: dict) -> list[str]:
        status, listed = self._identity_get(
            f"/api/identity/{self.realm}/api-keys?session_id={record.get('identity_session_id', '')}")
        if status != 200:
            return []
        return [row.get("key_id", "") for row in listed.get("api_keys", []) if row.get("key_id")]

    # ---------------------------------------------------------------- tenant logs (own receipts only)
    def tenant_logs(self, key_ids: list[str], *, kind_prefix: str = "", limit: int = _MAX_LOG_ROWS) -> dict:
        wanted = set(key_ids)
        rows = [r for r in self._load_receipts()
                if r.get("key_id") in wanted and str(r.get("kind", "")).startswith(kind_prefix)]
        rows = rows[-max(1, min(limit, _MAX_LOG_ROWS)):]
        return {"ok": True, "rows": list(reversed(rows)), "count": len(rows),
                "note": "your own request receipts only (kind, byte-derived token equivalents; no bodies)",
                "candidate": True, "serves_truth": False}

    # ---------------------------------------------------------------- private primitives (per-tenant overlay)
    def _tenant_overlay_dir(self, account_id: str) -> Path:
        return self.data_dir / "tenant_overlays" / account_id

    def my_primitives_add(self, account_id: str, cards: list) -> dict:
        if not isinstance(cards, list) or not cards:
            return {"ok": False, "error": "body must be {cards: [...]}"}
        if len(cards) > _MAX_CARDS_PER_TENANT_POST:
            return {"ok": False, "error": f"batch too large (max {_MAX_CARDS_PER_TENANT_POST})"}
        directory = self._tenant_overlay_dir(account_id)
        directory.mkdir(parents=True, exist_ok=True)
        accepted, rejected = 0, []
        with (directory / "cards.jsonl").open("a") as handle:
            for card in cards:
                if not isinstance(card, dict) or not str(card.get("primitive_id") or "").strip():
                    rejected.append(str(card)[:80])
                    continue
                handle.write(json.dumps({**card, "candidate": True, "serves_truth": False,
                                         "visibility": "private", "added_at": _now_iso()},
                                        sort_keys=True) + "\n")
                accepted += 1
        self._tenant_index_cache.pop(account_id, None)
        return {"ok": True, "accepted": accepted, "rejected": rejected[:10], "visibility": "private",
                "note": "governance bits force-stripped; private cards are searchable only by you "
                        "(include_mine=true)", "candidate": True, "serves_truth": False}

    def my_primitives_list(self, account_id: str) -> dict:
        cards, tombstoned = self._tenant_cards(account_id)
        return {"ok": True, "count": len(cards), "cards": cards[:200], "tombstoned": sorted(tombstoned),
                "candidate": True, "serves_truth": False}

    def my_primitives_remove(self, account_id: str, primitive_id: str) -> dict:
        if not primitive_id.strip():
            return {"ok": False, "error": "primitive_id required"}
        directory = self._tenant_overlay_dir(account_id)
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / "tombstones.jsonl").open("a") as handle:
            handle.write(json.dumps({"primitive_id": primitive_id, "removed_at": _now_iso()}) + "\n")
        self._tenant_index_cache.pop(account_id, None)
        return {"ok": True, "tombstoned": primitive_id, "note": "hidden from your searches; never erased",
                "candidate": True, "serves_truth": False}

    def _tenant_cards(self, account_id: str) -> tuple[list[dict], set[str]]:
        directory = self._tenant_overlay_dir(account_id)
        tombstoned = set()
        tombstones = directory / "tombstones.jsonl"
        if tombstones.exists():
            tombstoned = {json.loads(line)["primitive_id"]
                          for line in tombstones.read_text().splitlines() if line.strip()}
        cards: dict[str, dict] = {}
        cards_file = directory / "cards.jsonl"
        if cards_file.exists():
            for line in cards_file.read_text().splitlines():
                if line.strip():
                    card = json.loads(line)
                    card_id = str(card.get("primitive_id") or "")
                    if card_id and card_id not in tombstoned:
                        cards[card_id] = card   # later append (new version) supersedes, losslessly on disk
        return list(cards.values()), tombstoned

    _tenant_index_cache: dict[str, dict] = {}

    def search_mine(self, account_id: str, query: str, limit: int) -> list[dict]:
        """Search the tenant's private overlay (tiny per-tenant index, cached until their next write)."""
        cards, _tombstoned = self._tenant_cards(account_id)
        if not cards:
            return []
        if account_id not in self._tenant_index_cache:
            from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
            self._tenant_index_cache[account_id] = build_index(cards)
        from scripts.build_primitive_search_index import search_with_stats  # noqa: PLC0415
        hits, _stats = search_with_stats(query, limit, index=self._tenant_index_cache[account_id])
        return [{**hit, "visibility": "private"} for hit in hits]

    # ---------------------------------------------------------------- OWNER admin: primitive CRUD + reindex
    def is_owner(self, raw_key: str) -> bool:
        import hmac as _hmac  # noqa: PLC0415
        configured = _environment_setting(OWNER_KEY_ENVIRONMENT_VARIABLE,
                                          LEGACY_OWNER_KEY_ENVIRONMENT_VARIABLE)
        return bool(configured) and _hmac.compare_digest(raw_key, configured)

    def _overlay_path(self) -> Path:
        return self.data_dir / "corpus_overlay" / "added_cards.jsonl"

    def _tombstones_path(self) -> Path:
        return self.data_dir / "corpus_overlay" / "removed_ids.jsonl"

    def _serving_index_path(self) -> Path:
        return self.data_dir / "serving_index.json"

    def admin_add_primitives(self, cards: list) -> dict:
        """Append-only overlay CRUD: every card is FORCED candidate=true/serves_truth=false on write (a client
        can never flip the truth bit), id-required, bounded batch. Searchable after /v1/admin/reindex."""
        if not isinstance(cards, list) or not cards:
            return {"ok": False, "error": "body must be {cards: [...]} with at least one card"}
        if len(cards) > _MAX_CARDS_PER_ADMIN_POST:
            return {"ok": False, "error": f"batch too large (max {_MAX_CARDS_PER_ADMIN_POST}); loop batches"}
        path = self._overlay_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        accepted, rejected = 0, []
        with path.open("a") as handle:
            for card in cards:
                if not isinstance(card, dict) or not str(card.get("primitive_id") or "").strip():
                    rejected.append(str(card)[:80])
                    continue
                handle.write(json.dumps({**card, "candidate": True, "serves_truth": False,
                                         "overlay_added_at": _now_iso()}, sort_keys=True) + "\n")
                accepted += 1
        return {"ok": True, "accepted": accepted, "rejected": rejected[:10], "overlay_path": str(path),
                "note": "appended to the overlay (lossless); run POST /v1/admin/reindex to serve them",
                "candidate": True, "serves_truth": False}

    def admin_remove_primitive(self, primitive_id: str) -> dict:
        """Tombstone, never delete (lossless law): the id is skipped at the next reindex; history survives."""
        if not primitive_id.strip():
            return {"ok": False, "error": "primitive_id required"}
        path = self._tombstones_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as handle:
            handle.write(json.dumps({"primitive_id": primitive_id, "removed_at": _now_iso()}) + "\n")
        return {"ok": True, "tombstoned": primitive_id, "note": "skipped at next reindex; never erased",
                "candidate": True, "serves_truth": False}

    def admin_reindex(self) -> dict:
        """Rebuild the serving index (image corpus + overlay − tombstones) into /data in a background thread.
        The running process serves the new index on its next start (scale-to-zero wake or machine restart)."""
        if getattr(self, "_reindex_state", {}).get("running"):
            return {"ok": False, "error": "reindex already running", "status": self._reindex_state}
        self._reindex_state = {"running": True, "started": _now_iso(), "done": False}

        def _work() -> None:
            try:
                from scripts.build_primitive_search_index import SOURCE_CARD_FILES, build_index  # noqa: PLC0415
                tombstoned = {json.loads(line)["primitive_id"]
                              for line in (self._tombstones_path().read_text().splitlines()
                                           if self._tombstones_path().exists() else []) if line.strip()}
                cards: dict[str, dict] = {}
                corpus_files = self.fixtures.get("reindex_corpus_files")
                if corpus_files is None:
                    corpus_files = list(SOURCE_CARD_FILES)
                for file in [*corpus_files, self._overlay_path()]:
                    file = Path(file)
                    if not file.exists():
                        continue
                    with file.open() as handle:
                        for line in handle:
                            if not line.strip():
                                continue
                            card = json.loads(line)
                            card_id = str(card.get("primitive_id") or "")
                            if card_id and card_id not in tombstoned:
                                cards[card_id] = card   # later rows (overlay updates) supersede earlier, losslessly
                index = build_index(list(cards.values()))
                tmp = self._serving_index_path().with_suffix(".tmp")
                tmp.write_text(json.dumps(index))
                os.replace(tmp, self._serving_index_path())
                self._reindex_state = {"running": False, "done": True, "finished": _now_iso(),
                                       "indexed_cards": len(cards), "tombstoned": len(tombstoned),
                                       "serving_index": str(self._serving_index_path()),
                                       "note": "served on next process start (scale-to-zero wake or restart)"}
            except Exception as error:  # noqa: BLE001
                self._reindex_state = {"running": False, "done": False, "error": str(error)[:300]}

        threading.Thread(target=_work, name="admin-reindex", daemon=True).start()
        return {"ok": True, "status": self._reindex_state, "candidate": True, "serves_truth": False}

    def admin_reindex_status(self) -> dict:
        return {"ok": True, "status": getattr(self, "_reindex_state", {"running": False, "done": False}),
                "serving_index_present": self._serving_index_path().exists(),
                "candidate": True, "serves_truth": False}

    def admin_export_ledgers(self) -> dict:
        """The PC↔cloud loop: pull usage/request/invocation ledgers down so the LOCAL waterfall can promote."""
        out: dict[str, list] = {}
        for label, path in (("invocations", self.receipts_path),
                            ("tenant_usage", self.data_dir / "tenant_usage" / "events.jsonl"),
                            ("overlay_added", self._overlay_path()),
                            ("tombstones", self._tombstones_path())):
            out[label] = ([json.loads(line) for line in path.read_text().splitlines() if line.strip()]
                          if path.exists() else [])
        return {"ok": True, **{k: v for k, v in out.items()},
                "counts": {k: len(v) for k, v in out.items()}, "candidate": True, "serves_truth": False}

    def _loaded_serving_index(self):
        """The /data serving index (built by admin_reindex) if present — loaded once, preferred over the
        image-baked default so overlay CRUD survives deploys and serves after a wake/restart."""
        if not hasattr(self, "_serving_index_cache"):
            self._serving_index_cache = None
            path = self._serving_index_path()
            if path.exists():
                try:
                    self._serving_index_cache = json.loads(path.read_text())
                except (json.JSONDecodeError, OSError):
                    self._serving_index_cache = None
        return self._serving_index_cache

    def warm_serving_index(self) -> None:
        """Load the heavy governed index at BOOT instead of on a user's first search. Warrant: the 2026-07-10
        containerized prod run measured cold first-search > 240s (two journeys timed out at the guard) — the
        Fly machine wakes ON the request, so lazy loading makes the first user pay the whole load. Called as a
        daemon thread from --serve only; hermetic tests (fixture index) skip the heavy load."""
        started = time.monotonic()
        self._loaded_serving_index()
        if "index" not in self.fixtures:
            from scripts.build_primitive_search_index import search_with_stats  # noqa: PLC0415
            search_with_stats("boot warmup", 1)   # index=None -> loads + caches the persisted default index
        self.index_warm_seconds = round(time.monotonic() - started, 2)

    def health(self) -> dict:
        index_dir = _REPO / "catalog" / "knowledge-packs" / "data" / "primitive-search-index"
        return {"ok": True, "service": SERVICE_NAME, "version": SERVICE_VERSION, "realm": self.realm,
                "governed_index_present": index_dir.exists(), "identity": "embedded",
                "index_warm": hasattr(self, "index_warm_seconds"),
                "index_warm_seconds": getattr(self, "index_warm_seconds", None),
                "plans": sorted(PLAN_REQUEST_LIMITS_PER_DAY), "candidate": True, "serves_truth": False}

    def pricing(self) -> dict:
        from scripts.billing_plane import PLANS  # noqa: PLC0415  money lives in ONE place
        return {"plans": [{"plan": name, **spec, "requests_per_day": PLAN_REQUEST_LIMITS_PER_DAY[name]}
                          for name, spec in sorted(PLANS.items()) if name in PLAN_REQUEST_LIMITS_PER_DAY],
                "contributor_bonus": {
                    "how": "POST /v1/contribute {cards: [...]} — share anonymized primitives into the shared corpus",
                    "bonus_requests_per_accepted_card": CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD,
                    "daily_bonus_cap": CONTRIBUTOR_BONUS_DAILY_CAP,
                    "note": "DRAFT, owner-confirmable; contributions are anonymized (contributor digest only) and "
                            "candidate-only — never served without owner promotion"},
                "pricing_status": ("live — Stripe Checkout active (the charged amount is the Stripe Price object)"
                                   if self.billing_status()["payments_enabled"]
                                   else "draft — owner-confirmable before Stripe activation"),
                "billing": self.billing_status(),
                "candidate": True, "serves_truth": False}

    def shutdown(self) -> None:
        self._identity_server.shutdown()


_LANDING_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Taedri — This Already Exists, Don't Rebuild It</title>
<style>body{{font-family:system-ui;max-width:760px;margin:3rem auto;padding:0 1rem;line-height:1.5}}
code,pre{{background:#f4f4f4;padding:.15rem .35rem;border-radius:4px}}pre{{padding:.75rem;overflow-x:auto}}</style>
</head><body>
<h1>Taedri</h1>
<p><b>This Already Exists — Don't Rebuild It.</b> Hosted MCP + agent API for verified capability retrieval.</p>
<p>Retrieve verified capabilities instead of regenerating them: primitive search, exact lookup, the reinvention
guard, and deterministic composition — as a remote MCP server plus a deterministic agent API. Every result is a
governed candidate (<code>serves_truth=false</code>).</p>
<h2>Get a key</h2>
<pre>curl -s -X POST {base}/v1/signup -d '{{"email":"you@example.com"}}'</pre>
<h2>Connect Claude Code</h2>
<pre>claude mcp add --transport http taedri {base}/mcp \\
  --header "Authorization: Bearer YOUR_API_KEY"</pre>
<h2>Deterministic agent API</h2>
<pre>curl -s -X POST {base}/v1/agent -H "Authorization: Bearer YOUR_API_KEY" \\
  -d '{{"action":"retrieval.search","args":{{"query":"parse csv header"}}}}'</pre>
<h2>Hit your daily limit? Share, and keep going</h2>
<p>Contribute anonymized primitives into the shared corpus and earn bonus requests the same day
(+{bonus_per_card} per accepted card, up to +{bonus_cap}/day): <code>POST /v1/contribute</code>.
Contributions are anonymized and stay candidate-only until reviewed.</p>
<h2>News</h2>
{news_items}
<p><a href="/news">All updates →</a></p>
<p><a href="/setup">Set up your agent</a> · <a href="/docs">Docs</a> · <a href="/v1/pricing">Pricing</a> ·
<a href="/news">News</a> · <a href="/status">Status</a> · <a href="/console">Test console</a> ·
usage: <code>GET /v1/usage</code></p>
</body></html>"""


def _render_news_items(entries: list[dict[str, str]]) -> str:
    """Shared renderer for the landing digest and /news (single source: TAEDRI_NEWS)."""
    return "\n".join(f"<p><b>{entry['title']}</b> <small>({entry['date']})</small><br>{entry['body']}</p>"
                     for entry in entries)


_NEWS_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>News — Taedri</title>
<style>body{{font-family:system-ui;max-width:760px;margin:3rem auto;padding:0 1rem;line-height:1.5}}
code,pre{{background:#f4f4f4;padding:.15rem .35rem;border-radius:4px}}small{{color:#666}}</style>
</head><body>
<h1>Taedri news</h1>
<p>What shipped, when — every entry is something live on this deployment. <a href="/">← home</a> ·
<a href="/news.rss">RSS</a></p>
{news_items}
<p><a href="/">Home</a> · <a href="/v1/pricing">Pricing</a> · <a href="/console">Test console</a></p>
</body></html>"""


def _render_news_rss(entries: list[dict[str, str]], base: str) -> str:
    """RSS 2.0 from the same TAEDRI_NEWS constant (single source; escaped)."""
    import html as _html  # noqa: PLC0415
    items = "\n".join(
        f"<item><title>{_html.escape(e['title'])}</title>"
        f"<description>{_html.escape(e['body'])}</description>"
        f"<pubDate>{e['date']}</pubDate><guid isPermaLink=\"false\">taedri-news-{e['date']}-{i}</guid></item>"
        for i, e in enumerate(entries))
    return ("<?xml version=\"1.0\" encoding=\"UTF-8\"?><rss version=\"2.0\"><channel>"
            f"<title>Taedri news</title><link>{_html.escape(base or '/')}/news</link>"
            "<description>What shipped on Taedri, newest first.</description>"
            f"{items}</channel></rss>")


_DOCS_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Docs — Taedri</title>
<style>body{{font-family:system-ui;max-width:760px;margin:3rem auto;padding:0 1rem;line-height:1.5}}
code,pre{{background:#f4f4f4;padding:.15rem .35rem;border-radius:4px}}pre{{padding:.75rem;overflow-x:auto}}
small{{color:#666}}</style>
</head><body>
<h1>Taedri docs</h1>
<p>Everything here runs against the same public API your agent uses — the console has no private endpoints.
<a href="/">← home</a></p>
<h2>Quickstart</h2>
<p><b>No signup?</b> Try instantly with the shared public trial key <code>{trial_key}</code> —
{trial_pool} requests/day shared across everyone, {trial_ip_slice}/day per address, read-only. The
<a href="/news">example Kaggle notebook</a> uses it.</p>
<ol>
<li>Sign up with an email. You get an API key and an account secret, each shown exactly once (hashes only
are stored):<pre>curl -s -X POST {base}/v1/signup -d '{{"email":"you@example.com"}}'</pre></li>
<li>Connect your agent:<pre>claude mcp add --transport http taedri {base}/mcp \\
  --header "Authorization: Bearer YOUR_API_KEY"</pre></li>
<li>Prefer plain HTTP? The same functions are deterministic agent actions:
<pre>curl -s -X POST {base}/v1/agent -H "Authorization: Bearer YOUR_API_KEY" \\
  -d '{{"action":"retrieval.search","args":{{"query":"parse csv header"}}}}'</pre></li>
</ol>
<h2>The {tool_count} MCP tools</h2>
{tool_rows}
<h2>Rate limits &amp; plans</h2>
{plan_rows}
<p>Prices live at <a href="/v1/pricing">/v1/pricing</a> (draft until billing goes live). Hit the limit? The
429 carries <code>Retry-After</code> + <code>X-RateLimit-*</code> headers, an upgrade pointer, and the
share-to-continue lane: <code>POST /v1/contribute</code> grants +{bonus_per_card} requests per accepted
anonymized card (up to +{bonus_cap}/day), candidate-only until reviewed.</p>
<h2>Errors &amp; designed waits</h2>
<p><code>401</code> — missing/invalid key; sign up or check the Bearer header. <code>429</code> — daily plan
limit; see above. <b>Cold wake</b> — the first search after a machine wake loads the full governed index;
the server warms it at boot and <a href="/healthz">/healthz</a> reports <code>index_warm</code>, but a search
that lands mid-warm waits instead of failing. Every response carries <code>candidate</code> /
<code>serves_truth</code> — results are governed candidates until promoted, never silently upgraded.</p>
<p><a href="/">Home</a> · <a href="/news">News</a> · <a href="/status">Status</a> ·
<a href="/console">Test console</a></p>
</body></html>"""

_STATUS_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Status — Taedri</title>
<style>body{{font-family:system-ui;max-width:760px;margin:3rem auto;padding:0 1rem;line-height:1.5}}
code{{background:#f4f4f4;padding:.15rem .35rem;border-radius:4px}}small{{color:#666}}</style>
</head><body>
<h1>Taedri status</h1>
<p>{headline}</p>
{component_rows}
<p><small>Raw: <a href="/healthz">/healthz</a>. Incident notes will appear here.</small></p>
<p><a href="/">Home</a> · <a href="/docs">Docs</a> · <a href="/news">News</a></p>
</body></html>"""

#: SETUP recipes, one per agent harness (single source — each snippet is rendered from the live {base}). Every
#: harness that speaks MCP-over-HTTP connects the SAME way (add server + Bearer header); the config SHAPE differs.
#: Add a harness = one row. (owner 2026-07-10: "a verify-it-works / setup page — Claude Code, Codex, Hermes,
#: OpenClaw, etc.")
SETUP_HARNESSES: list[dict[str, str]] = [
    {"id": "claude-code", "name": "Claude Code",
     "body": 'One command adds the 7 tools (after signup, your key is inlined):\n'
             'claude mcp add --transport http taedri {base}/mcp \\\n'
             '  --header "Authorization: Bearer YOUR_API_KEY"\n'
             'Then: claude mcp list   # → taedri ✓ Connected'},
    {"id": "codex", "name": "Codex CLI",
     "body": '# ~/.codex/config.toml — an MCP-over-HTTP server entry\n'
             '[mcp_servers.taedri]\n'
             'transport = "http"\n'
             'url = "{base}/mcp"\n'
             'headers = {{ Authorization = "Bearer YOUR_API_KEY" }}'},
    {"id": "hermes", "name": "Hermes (agentic bot)",
     "body": '# hermes config — register the remote MCP server\n'
             'mcp:\n'
             '  taedri:\n'
             '    transport: http\n'
             '    url: {base}/mcp\n'
             '    headers: {{ Authorization: "Bearer YOUR_API_KEY" }}'},
    {"id": "openclaw", "name": "OpenClaw",
     "body": '# openclaw servers.json — same MCP-over-HTTP contract\n'
             '{{ "mcpServers": {{ "taedri": {{\n'
             '  "transport": "http", "url": "{base}/mcp",\n'
             '  "headers": {{ "Authorization": "Bearer YOUR_API_KEY" }} }} }} }}'},
    {"id": "http", "name": "Any agent / plain HTTP",
     "body": '# no MCP client needed — the same functions as a deterministic agent action:\n'
             'curl -s -X POST {base}/v1/agent -H "Authorization: Bearer YOUR_API_KEY" \\\n'
             '  -d \'{{"action":"retrieval.search","args":{{"query":"parse csv header"}}}}\''},
    {"id": "python", "name": "Python / Kaggle (trial key, no signup)",
     "body": 'import requests\n'
             'BASE, KEY = "{base}", "ak_trial_taedri_public_notebook"   # public read-only trial key\n'
             'r = requests.post(f"{{BASE}}/v1/agent", headers={{"Authorization": f"Bearer {{KEY}}"}},\n'
             '                  json={{"action":"retrieval.search","args":{{"query":"exponential backoff"}}}})\n'
             'print(r.json())'},
]


def _render_setup_cards(base: str) -> str:
    return "\n".join(
        f'<h3>{h["name"]}</h3><pre>{h["body"].format(base=base)}</pre>' for h in SETUP_HARNESSES)


_SETUP_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Set up &amp; verify — Taedri</title>
<style>body{{font-family:system-ui;max-width:800px;margin:3rem auto;padding:0 1rem;line-height:1.5}}
code,pre{{background:#f4f4f4;padding:.15rem .35rem;border-radius:4px}}pre{{padding:.75rem;overflow-x:auto;
white-space:pre-wrap}}h3{{margin:1.4rem 0 .3rem}}small{{color:#666}}.ok{{color:#187d1a}}</style>
</head><body>
<h1>Set up Taedri in your agent</h1>
<p>Every agent that speaks MCP-over-HTTP connects the same way — add the server, send a Bearer header. Pick yours.
Need a key first? <a href="/console">Open the console</a> and sign up (or use the public trial key below).</p>
<h2>1 · Get a key</h2>
<pre>curl -s -X POST {base}/v1/signup -d '{{"email":"you@example.com"}}'   # key + secret shown once (hashes only)</pre>
<p>Prefer zero signup? Use the shared read-only trial key <code>ak_trial_taedri_public_notebook</code>
(100 requests/day pooled).</p>
<h2>2 · Connect your harness</h2>
{setup_cards}
<h2>3 · Verify it works</h2>
<p>Run one search — you should get results in well under a second on a warm server:</p>
<pre>curl -s -X POST {base}/v1/agent -H "Authorization: Bearer YOUR_API_KEY" \\
  -d '{{"action":"retrieval.search","args":{{"query":"exponential backoff with jitter"}}}}'</pre>
<p>Live checks: <a href="/verify">/verify</a> (JSON self-check) · <a href="/status">/status</a> ·
<a href="/healthz">/healthz</a> (shows <code>index_warm</code>). A first search right after a cold wake loads
the index; the server warms it at boot, so a warm server answers fast.</p>
<p><a href="/">Home</a> · <a href="/docs">Docs</a> · <a href="/console">Console</a> · <a href="/news">News</a></p>
</body></html>"""

_PAGE_STYLE = """<style>body{font-family:system-ui;max-width:560px;margin:3rem auto;padding:0 1rem;
background:#0d1117;color:#e6edf3}input{background:#161b22;color:#e6edf3;border:1px solid #30363d;
border-radius:6px;padding:.55rem;width:100%;box-sizing:border-box;margin:.25rem 0}
button{background:#238636;color:#fff;border:0;border-radius:6px;padding:.55rem 1rem;cursor:pointer;margin-top:.5rem}
a{color:#58a6ff}pre{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:.7rem;overflow-x:auto}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem;margin:.6rem 0}</style>"""

_LOGIN_HTML = f"""<!doctype html><html><head><meta charset="utf-8"><title>Log in — Taedri</title>{_PAGE_STYLE}
</head><body><h1>taedri</h1><p>Log in with your email and account secret (shown once at signup).</p>
<input id="email" placeholder="you@example.com"><input id="secret" type="password" placeholder="account secret">
<button onclick="login()">Log in</button> <a href="/">home</a> <a href="/console">console</a>
<pre id="out"></pre><script>
async function login(){{
  const r=await fetch('/v1/session',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{email:document.getElementById('email').value,
                          secret:document.getElementById('secret').value}})}});
  const d=await r.json();
  if(d.ok){{location.href='/dashboard'}}else{{document.getElementById('out').textContent=JSON.stringify(d,null,2)}}
}}</script></body></html>"""

_DASHBOARD_HTML = f"""<!doctype html><html><head><meta charset="utf-8"><title>Dashboard — Taedri</title>{_PAGE_STYLE}
</head><body><h1>taedri dashboard</h1>
<div class="card"><b>Account</b> <code>__ACCOUNT_ID__</code> · plan <b>__PLAN__</b></div>
<div class="card"><b>__N_KEYS__</b> API key(s) · <b>__REQUESTS__</b> recent request(s)
 · <b>__MY_COUNT__</b> private primitive(s)</div>
<div class="card"><a href="/console">Open the console</a> · <a href="/v1/logs">My logs (JSON)</a> ·
<a href="/v1/my/primitives">My primitives (JSON)</a> · <a href="/v1/pricing">Pricing</a> ·
<a href="/news">News</a></div>
<button onclick="fetch('/v1/session/logout',{{method:'POST'}}).then(()=>location.href='/')">Log out</button>
</body></html>"""

_CONSOLE_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Taedri Console</title>
<style>
body{font-family:system-ui;max-width:920px;margin:1.5rem auto;padding:0 1rem;background:#0d1117;color:#e6edf3}
h1{font-size:1.3rem}h2{font-size:1rem;margin:1.2rem 0 .4rem;color:#7ee787}
input,textarea,select{background:#161b22;color:#e6edf3;border:1px solid #30363d;border-radius:6px;
padding:.45rem;font-family:ui-monospace,monospace;font-size:.85rem;width:100%;box-sizing:border-box}
button{background:#238636;color:#fff;border:0;border-radius:6px;padding:.45rem .9rem;margin:.2rem .3rem .2rem 0;
cursor:pointer;font-size:.85rem}button.alt{background:#1f6feb}button.warn{background:#9e6a03}
pre{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:.7rem;overflow-x:auto;
white-space:pre-wrap;word-break:break-word;font-size:.78rem;max-height:340px;overflow-y:auto}
.row{display:flex;gap:.5rem;flex-wrap:wrap}.row>*{flex:1;min-width:180px}small{color:#8b949e}
</style></head><body>
<h1>Taedri console <small>(everything runs same-origin against this deployment)</small></h1>

<h2>1 · Account & key</h2>
<div class="row"><input id="email" placeholder="you@example.com">
<input id="key" placeholder="API key (auto-filled by signup; stored in localStorage)"></div>
<button onclick="signup()">Sign up → mint key</button>
<button class="alt" onclick="call('GET','/v1/usage')">Usage & draft invoice</button>
<button class="alt" onclick="call('GET','/v1/pricing')">Pricing</button>
<button class="alt" onclick="call('GET','/healthz')">Health</button>
<button class="warn" onclick="call('POST','/v1/upgrade',{plan:'capability_pro'})">Upgrade → pro</button>

<h2>2 · Remote MCP (the 7 tools over HTTP)</h2>
<div class="row"><input id="q" value="parse csv header rows"><input id="pid" placeholder="primitive_id for get"></div>
<button onclick="mcp('initialize',{})">initialize</button>
<button onclick="mcp('tools/list',{})">tools/list</button>
<button onclick="mcpCall('primitive_search',{query:val('q'),limit:5})">primitive_search</button>
<button onclick="mcpCall('primitive_get',{primitive_id:val('pid')})">primitive_get</button>
<button onclick="mcpCall('find_reuse',{message:val('q')})">find_reuse (reinvention guard)</button>
<button onclick="mcpCall('capability_compose',{request:val('q')})">capability_compose</button>
<button onclick="mcpCall('primitive_corpus_status',{})">corpus_status</button>

<h2>3 · Deterministic agent API</h2>
<div class="row"><select id="action">
<option>actions.list</option><option>retrieval.search</option><option>retrieval.compose</option>
<option>corpus.status</option><option>usage.report</option><option>waterfall.levels</option>
<option>waterfall.plan</option><option>learning.status</option><option>environment.profile</option>
</select><input id="args" value='{"query":"parse csv header rows"}'></div>
<button onclick="agent()">Run action</button>

<h2>4 · Administrator <small>(needs the TAEDRI_ADMIN_KEY secret)</small></h2>
<input id="okey" placeholder="owner key (stored in localStorage)">
<textarea id="cards" rows="3" placeholder='[{"primitive_id":"prim:mine:1","title":"My primitive","blackbox":"...","blocking_keys":["mine"]}]'></textarea>
<button class="warn" onclick="admin('POST','/v1/admin/primitives',{cards:JSON.parse(val('cards')||'[]')})">Add primitives</button>
<button class="warn" onclick="admin('POST','/v1/admin/primitives/remove',{primitive_id:val('pid')})">Tombstone id</button>
<button class="warn" onclick="admin('POST','/v1/admin/reindex',{})">Reindex</button>
<button class="alt" onclick="admin('GET','/v1/admin/reindex')">Reindex status</button>
<button class="alt" onclick="admin('GET','/v1/admin/ledgers')">Export ledgers</button>

<h2>5 · Contribute to the shared corpus <small>(earn bonus requests — the keep-going lane at your limit)</small></h2>
<textarea id="share" rows="3" placeholder='[{"primitive_id":"prim:mine:1","title":"My primitive","blackbox":"..."}]'></textarea>
<button onclick="call('POST','/v1/contribute',{cards:JSON.parse(val('share')||'[]')})">Share → earn bonus</button>

<h2>Output</h2><pre id="out">ready — sign up to begin. serves_truth=false on everything.</pre>
<script>
const out=document.getElementById('out');
const val=id=>document.getElementById(id).value.trim();
document.getElementById('key').value=localStorage.getItem('capKey')||'';
document.getElementById('okey').value=localStorage.getItem('capOwnerKey')||'';
function show(x){out.textContent=typeof x==='string'?x:JSON.stringify(x,null,2)}
async function http(method,path,body,key){
  const headers={'Content-Type':'application/json'};
  if(key)headers['Authorization']='Bearer '+key;
  const r=await fetch(path,{method,headers,body:body===undefined?undefined:JSON.stringify(body)});
  let d;try{d=await r.json()}catch(e){d={raw:await r.text()}}
  return {status:r.status,body:d};
}
async function signup(){
  const r=await http('POST','/v1/signup',{email:val('email')});
  if(r.body.api_key){document.getElementById('key').value=r.body.api_key;
    localStorage.setItem('capKey',r.body.api_key)}
  show(r);
}
async function call(method,path,body){show('…');show(await http(method,path,body,val('key')))}
async function mcp(method,params){show('…');
  show(await http('POST','/mcp',{jsonrpc:'2.0',id:1,method,params},val('key')))}
async function mcpCall(name,args){
  show('… (first search after a wake loads the 557K-doc index — up to ~40s)');
  const r=await http('POST','/mcp',{jsonrpc:'2.0',id:1,method:'tools/call',
    params:{name,arguments:args}},val('key'));
  try{r.parsed=JSON.parse(r.body.result.content[0].text)}catch(e){}
  show(r.parsed||r);
}
async function agent(){show('…');let a={};try{a=JSON.parse(val('args')||'{}')}catch(e){}
  show(await http('POST','/v1/agent',{action:val('action'),args:a},val('key')))}
async function admin(method,path,body){localStorage.setItem('capOwnerKey',val('okey'));show('…');
  show(await http(method,path,method==='GET'?undefined:body,val('okey')))}
</script></body></html>"""


def _taedri_routes() -> set:
    try:
        from scripts import taedri_web  # noqa: PLC0415
        return set(taedri_web.ROUTES)
    except Exception:  # noqa: BLE001
        return set()


_TAEDRI_ROUTES = _taedri_routes()
#: the 18 governed domains shown on the Landing/Browse counter (matches the corpus partitioner).
_STATS_DOMAINS = ["database", "auth", "http", "etl", "ml", "cloud", "messaging", "observability", "algorithms",
                  "geo/time", "testing", "files", "frontend", "nlp", "scraping", "finance", "healthcare", "general"]
_STATS_CACHE: dict = {}


def _public_stats_domains() -> dict:
    """Public, keyless corpus stats for the Landing/Browse counter — the honest SERVED-index count, computed
    from the built lexical index manifest (no key, no heavy federation scan). Cached."""
    override = os.environ.get("OH_STATS_COUNT")  # ops can pin the public marketing count; also enables testing
    if override:
        return {"primitives": int(override), "domains": _STATS_DOMAINS, "candidate": True, "serves_truth": False}
    if "primitives" not in _STATS_CACHE:
        n = 0
        try:
            root = Path(__file__).resolve().parent.parent
            mani = root / "catalog" / "knowledge-packs" / "data" / "primitive-search-index" / "manifest.json"
            if mani.exists():
                n = int(json.loads(mani.read_text()).get("n_docs", 0))
        except Exception:  # noqa: BLE001
            n = 0
        _STATS_CACHE["primitives"] = n
    return {"primitives": _STATS_CACHE["primitives"], "domains": _STATS_DOMAINS,
            "candidate": True, "serves_truth": False}


class _GatewayHandler(BaseHTTPRequestHandler):
    gateway: CapabilitySaasGateway = None  # type: ignore[assignment]  set by start_gateway

    # -------------------------------------------------------------- plumbing
    def _cors_headers(self) -> dict:
        """CORS so a browser origin (the Taedri web app / Workbench live mode) can call /mcp + /v1/* with a
        Bearer key held in memory. Origin is env-overridable (OH_CORS_ORIGIN); default '*' is safe because we
        authorize with a Bearer key, never cookies, on the cross-origin surface. See HANDOFF ticket 28."""
        origin = os.environ.get("OH_CORS_ORIGIN", "*")
        return {"Access-Control-Allow-Origin": origin, "Vary": "Origin",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Authorization, Content-Type",
                "Access-Control-Max-Age": "86400"}

    def do_OPTIONS(self) -> None:  # noqa: N802 — CORS preflight
        self.send_response(204)
        for name, value in self._cors_headers().items():
            self.send_header(name, value)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send(self, code: int, payload: Any, content_type: str = "application/json",
              extra_headers: Optional[dict] = None) -> int:
        body = payload if isinstance(payload, bytes) else json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in self._cors_headers().items():
            self.send_header(name, value)
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)
        return len(body)

    def _session_cookie(self) -> str:
        for part in self.headers.get("Cookie", "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == _SESSION_COOKIE_NAME:
                return value
        return ""

    def _account_id(self) -> Optional[str]:
        """Account resolution for tenant-scoped surfaces: session cookie first, Bearer key second."""
        record = self.gateway.resolve_session(self._session_cookie())
        if record:
            return str(record.get("account_id") or "") or None
        verified = self.gateway.verify_key(self._bearer())
        if verified:
            return str(verified.get("account_id") or "") or None
        return None

    def _body(self) -> tuple[dict, int]:
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
        self._raw_body = b""   # kept for signature verification (webhooks HMAC the exact raw bytes)
        if length <= 0:
            return {}, 0
        raw = self.rfile.read(length)
        self._raw_body = raw
        try:
            parsed = json.loads(raw.decode("utf-8") or "{}")
            return (parsed if isinstance(parsed, dict) else {}), len(raw)
        except json.JSONDecodeError:
            return {}, len(raw)

    def _bearer(self) -> str:
        return self.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    def _client_ip(self) -> str:
        """Real caller address behind the Fly proxy (Fly-Client-IP), then the first XFF hop, then the socket."""
        return (self.headers.get("Fly-Client-IP")
                or (self.headers.get("X-Forwarded-For", "").split(",")[0].strip())
                or (self.client_address[0] if self.client_address else ""))

    def _authed(self) -> Optional[dict]:
        bearer = self._bearer()
        if bearer and bearer == self.gateway.trial_key():
            # the public notebook key: no identity record, read-only surface, shared+per-IP limits
            return {"key_id": "trial-public", "account_id": "trial-public", "trial": True}
        verified = self.gateway.verify_key(bearer)
        if verified is None:
            self._send(401, {"error": "missing or invalid API key (Authorization: Bearer <key>); "
                                      "sign up: POST /v1/signup {email}", "serves_truth": False})
        return verified

    def _rate_checked(self, verified: dict) -> bool:
        if verified.get("trial"):
            allowed, used, limit, reason = self.gateway.check_trial_limits(self._client_ip())
            if not allowed:
                self._send(429, {"error": f"trial limit reached ({used}/{limit}): {reason}",
                                 "plan": TRIAL_PLAN,
                                 "sign_up_free": "POST /v1/signup {\"email\":\"you@example.com\"} — your own "
                                                 f"{PLAN_REQUEST_LIMITS_PER_DAY[DEFAULT_PLAN]} requests/day, "
                                                 "free", "serves_truth": False},
                           extra_headers={"Retry-After": "3600", "X-RateLimit-Limit": str(limit),
                                          "X-RateLimit-Remaining": "0"})
            return allowed
        account_id = str(verified.get("account_id") or "")
        plan = self.gateway.tenant_plan(account_id)
        bonus = self.gateway.bonus_requests_today(account_id)
        allowed, used, limit = self.gateway.check_rate_limit(str(verified.get("key_id") or ""), plan, bonus)
        if not allowed:
            import datetime as _datetime  # noqa: PLC0415
            now = _datetime.datetime.now(_datetime.timezone.utc)
            midnight = (now + _datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            retry_after_seconds = max(1, int((midnight - now).total_seconds()))
            self._send(429, {"error": f"daily request limit reached ({used}/{limit} on {plan})",
                             "plan": plan, "upgrade": "POST /v1/upgrade {\"plan\":\"capability_pro\"}",
                             "continue_free": "keep going today by sharing anonymized primitives into the shared "
                                              "corpus: POST /v1/contribute {\"cards\":[...]} grants "
                                              f"+{CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD} requests per "
                                              f"accepted card (up to +{CONTRIBUTOR_BONUS_DAILY_CAP}/day); "
                                              "contributions stay candidate-only until reviewed",
                             "serves_truth": False},
                       extra_headers={"Retry-After": str(retry_after_seconds),
                                      "X-RateLimit-Limit": str(limit),
                                      "X-RateLimit-Remaining": "0",
                                      "X-RateLimit-Reset": str(retry_after_seconds)})
        return allowed

    # -------------------------------------------------------------- routes
    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        # Taedri web app (the Claude Design handoff): a designed screen overrides the hand-built stub for its
        # route, but only when the screen file is present on disk — so the app takes over route-by-route as
        # screens land. Wired to this same gateway's endpoints (same-origin).
        if path in _TAEDRI_ROUTES:
            try:
                from scripts import taedri_web  # noqa: PLC0415
                html = taedri_web.render_route(path)
            except Exception:  # noqa: BLE001
                html = None
            if html is not None:
                self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                return
        if path == "/v1/stats/domains":
            self._send(200, _public_stats_domains())
            return
        if path.startswith("/v1/admin/"):
            if not self._owner_authed():
                return
            if path == "/v1/admin/reindex":
                self._send(200, self.gateway.admin_reindex_status())
            elif path == "/v1/admin/ledgers":
                self._send(200, self.gateway.admin_export_ledgers())
            else:
                self._send(404, {"error": "unknown admin path", "serves_truth": False})
            return
        if path == "/v1/logs":
            account_id = self._account_id()
            if not account_id:
                self._send(401, {"error": "log in or send your API key", "serves_truth": False})
                return
            record = self.gateway.resolve_session(self._session_cookie())
            if record:
                key_ids = self.gateway.account_key_ids(record)
            else:
                verified = self.gateway.verify_key(self._bearer()) or {}
                key_ids = [str(verified.get("key_id") or "")]
            query = dict(pair.split("=", 1) for pair in self.path.partition("?")[2].split("&") if "=" in pair)
            self._send(200, self.gateway.tenant_logs(key_ids, kind_prefix=query.get("kind", ""),
                                                     limit=int(query.get("limit", _MAX_LOG_ROWS))))
            return
        if path == "/v1/my/primitives":
            account_id = self._account_id()
            if not account_id:
                self._send(401, {"error": "log in or send your API key", "serves_truth": False})
                return
            self._send(200, self.gateway.my_primitives_list(account_id))
            return
        if path == "/login":
            self._send(200, _LOGIN_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/dashboard":
            record = self.gateway.resolve_session(self._session_cookie())
            if not record:
                self._send(302, b"", "text/plain", extra_headers={"Location": "/login"})
                return
            account_id = str(record.get("account_id") or "")
            key_ids = self.gateway.account_key_ids(record)
            logs = self.gateway.tenant_logs(key_ids, limit=10)
            mine = self.gateway.my_primitives_list(account_id)
            page = (_DASHBOARD_HTML.replace("__ACCOUNT_ID__", account_id)
                    .replace("__PLAN__", self.gateway.tenant_plan(account_id))
                    .replace("__N_KEYS__", str(len(key_ids)))
                    .replace("__REQUESTS__", str(logs["count"]))
                    .replace("__MY_COUNT__", str(mine["count"])))
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/console":
            self._send(200, _CONSOLE_HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/news":
            page = _NEWS_HTML.format(news_items=_render_news_items(TAEDRI_NEWS))
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/news.rss":
            host = self.headers.get("Host", "")
            base = f"https://{host}" if host and "127.0.0.1" not in host and "localhost" not in host else ""
            self._send(200, _render_news_rss(TAEDRI_NEWS, base).encode("utf-8"),
                       "application/rss+xml; charset=utf-8")
        elif path == "/docs":
            from scripts.capability_retrieval_mcp_server import TOOLS  # noqa: PLC0415  computed, never typed
            host = self.headers.get("Host", "")
            base = f"https://{host}" if host and "127.0.0.1" not in host and "localhost" not in host else ""
            tool_rows = "\n".join(
                f"<p><b><code>{tool['name']}</code></b> — {str(tool.get('description', '')).split('. ')[0]}.</p>"
                for tool in TOOLS)
            plan_rows = "\n".join(f"<p><b>{plan}</b> — {limit:,} requests / day</p>"
                                  for plan, limit in sorted(PLAN_REQUEST_LIMITS_PER_DAY.items()))
            page = _DOCS_HTML.format(base=base, tool_count=len(TOOLS), tool_rows=tool_rows,
                                     plan_rows=plan_rows,
                                     bonus_per_card=CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD,
                                     bonus_cap=CONTRIBUTOR_BONUS_DAILY_CAP,
                                     trial_key=self.gateway.trial_key(),
                                     trial_pool=TRIAL_REQUEST_LIMIT_PER_DAY,
                                     trial_ip_slice=TRIAL_PER_IP_LIMIT_PER_DAY)
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/status":
            health = self.gateway.health()
            headline = ("All systems operational" if health.get("ok") and health.get("governed_index_present")
                        else "Degraded — see components below")
            component_rows = "\n".join(
                f"<p>{'✓' if bool(value) else '✗'} <b>{label}</b> <code>{value}</code></p>"
                for label, value in (("gateway", health.get("service")),
                                     ("version", health.get("version")),
                                     ("identity", health.get("identity")),
                                     ("governed index present", health.get("governed_index_present")),
                                     ("index warm", health.get("index_warm")),
                                     ("plans", ", ".join(health.get("plans", [])))))
            page = _STATUS_HTML.format(headline=headline, component_rows=component_rows)
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/setup":
            host = self.headers.get("Host", "")
            base = f"https://{host}" if host and "127.0.0.1" not in host and "localhost" not in host else ""
            page = _SETUP_HTML.format(base=base, setup_cards=_render_setup_cards(base))
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/verify":
            # a JSON self-check the setup page links: is the server up + warm, and does a search actually
            # return? Uses the trial key so it works with no signup; times the search so cold-start is visible.
            health = self.gateway.health()
            checks: dict[str, Any] = {"gateway_ok": bool(health.get("ok")),
                                      "governed_index_present": bool(health.get("governed_index_present")),
                                      "index_warm": bool(health.get("index_warm"))}
            started = time.monotonic()
            try:
                probe = self.gateway.mcp_dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                   "params": {"name": "primitive_search",
                                                              "arguments": {"query": "parse csv header", "limit": 1,
                                                                            "scope": "governed"}}})
                hits = json.loads(probe["result"]["content"][0]["text"]).get("results", [])
                checks["search_returned"] = len(hits) > 0
            except Exception as error:  # noqa: BLE001
                checks["search_returned"] = False
                checks["search_error"] = str(error)[:160]
            checks["search_seconds"] = round(time.monotonic() - started, 2)
            self._send(200, {"verified": all(v for k, v in checks.items()
                                             if k in ("gateway_ok", "governed_index_present", "search_returned")),
                             "checks": checks, "harnesses": [h["id"] for h in SETUP_HARNESSES],
                             "note": "a warm server answers the probe search in well under a second; a cold "
                                     "first search loads the index. serves_truth=false", "serves_truth": False})
        elif path == "/":
            host = self.headers.get("Host", "")
            base = f"https://{host}" if host and "127.0.0.1" not in host and "localhost" not in host else ""
            page = _LANDING_HTML.format(base=base,
                                        news_items=_render_news_items(TAEDRI_NEWS[:3]),
                                        bonus_per_card=CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD,
                                        bonus_cap=CONTRIBUTOR_BONUS_DAILY_CAP)
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        elif path in ("/healthz", "/health"):
            self._send(200, self.gateway.health())
        elif path == "/v1/pricing":
            self._send(200, self.gateway.pricing())
        elif path == "/v1/billing/status":
            self._send(200, self.gateway.billing_status())
        elif path == "/v1/usage":
            verified = self._authed()
            if verified is not None:
                self._send(200, self.gateway.trial_usage() if verified.get("trial")
                           else self.gateway.usage(verified))
        else:
            self._send(404, {"error": "unknown path", "serves_truth": False})

    def _owner_authed(self) -> bool:
        if self.gateway.is_owner(self._bearer()):
            return True
        self._send(403, {"error": "administrator key required (TAEDRI_ADMIN_KEY); the admin surface is "
                                  "administrator-only", "serves_truth": False})
        return False

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        body, request_bytes = self._body()
        if path.startswith("/v1/admin/"):
            if not self._owner_authed():
                return
            if path == "/v1/admin/primitives":
                self._send(200, self.gateway.admin_add_primitives(body.get("cards")))
            elif path == "/v1/admin/primitives/remove":
                self._send(200, self.gateway.admin_remove_primitive(str(body.get("primitive_id") or "")))
            elif path == "/v1/admin/reindex":
                self._send(200, self.gateway.admin_reindex())
            else:
                self._send(404, {"error": "unknown admin path", "serves_truth": False})
            return
        if path == "/v1/signup":
            result = self.gateway.signup(str(body.get("email") or ""), str(body.get("secret") or ""))
            self._send(200 if result.get("ok") else 400, result)
            return
        if path == "/v1/session":
            result = self.gateway.login_session(str(body.get("email") or ""), str(body.get("secret") or ""))
            if result.get("ok"):
                cookie = (f"{_SESSION_COOKIE_NAME}={result['session_id']}; HttpOnly; Path=/; "
                          f"Max-Age={_SESSION_TTL_SECONDS}; SameSite=Lax")
                self._send(200, result, extra_headers={"Set-Cookie": cookie})
            else:
                self._send(401, result)
            return
        if path == "/v1/session/logout":
            self.gateway.logout_session(self._session_cookie())
            self._send(200, {"ok": True},
                       extra_headers={"Set-Cookie": f"{_SESSION_COOKIE_NAME}=; Max-Age=0; Path=/"})
            return
        if path in ("/v1/my/primitives", "/v1/my/primitives/remove"):
            account_id = self._account_id()
            if not account_id:
                self._send(401, {"error": "log in (POST /v1/session) or send your API key", "serves_truth": False})
                return
            if path == "/v1/my/primitives":
                self._send(200, self.gateway.my_primitives_add(account_id, body.get("cards")))
            else:
                self._send(200, self.gateway.my_primitives_remove(account_id, str(body.get("primitive_id") or "")))
            return
        if path == "/v1/contribute":
            # deliberately NOT rate-gated: this is the escape hatch a tenant reaches AT the limit.
            account_id = self._account_id()
            if not account_id:
                self._send(401, {"error": "log in (POST /v1/session) or send your API key", "serves_truth": False})
                return
            result = self.gateway.contribute_to_corpus(account_id, body.get("cards"))
            self._send(200 if result.get("ok") else 400, result)
            return
        if path == "/v1/billing/webhook":
            # Stripe calls this; the HMAC signature IS the auth (verified over the exact raw bytes).
            code, result = self.gateway.stripe_webhook(getattr(self, "_raw_body", b""),
                                                       self.headers.get("Stripe-Signature", ""))
            self._send(code, result)
            return
        verified = self._authed()
        if verified is None:
            return
        if path == "/v1/billing/checkout":
            if verified.get("trial"):
                self._send(403, {"error": "the shared trial key cannot start a checkout — sign up free "
                                          "first: POST /v1/signup {email}", "serves_truth": False})
                return
            scheme = self.headers.get("X-Forwarded-Proto", "http").split(",")[0].strip() or "http"
            host = self.headers.get("Host") or f"127.0.0.1:{self.server.server_address[1]}"
            code, result = self.gateway.create_checkout(verified, f"{scheme}://{host}")
            self._send(code, result)
            return
        if path == "/mcp":
            if verified.get("trial"):
                params = body.get("params") or {}
                tool_name = str(params.get("name") or "") if isinstance(params, dict) else ""
                if body.get("method") == "tools/call" and tool_name in TRIAL_DENIED_MCP_TOOLS:
                    self.gateway._record_abuse("trial_denied_tool", _digest16(self._client_ip() or "unknown"),
                                               tool_name)
                    self._send(200, {"jsonrpc": "2.0", "id": body.get("id"),
                                     "error": {"code": -32001,
                                               "message": f"{tool_name} is a write tool — the shared trial key "
                                                          "is read-only; sign up free: POST /v1/signup"}})
                    return
            if not self._rate_checked(verified):
                return
            try:
                response = self.gateway.mcp_dispatch(body) or {"jsonrpc": "2.0", "id": body.get("id"),
                                                               "result": {}}
            except Exception as error:  # noqa: BLE001  a paid endpoint returns JSON errors, never dropped sockets
                response = {"jsonrpc": "2.0", "id": body.get("id"),
                            "error": {"code": -32603, "message": f"internal error: {str(error)[:200]}"}}
            sent = self._send(200, response)
            self.gateway.meter(str(verified.get("key_id")), f"mcp:{body.get('method', '?')}", request_bytes, sent)
        elif path == "/v1/agent":
            if verified.get("trial") and str(body.get("action") or "") not in TRIAL_ALLOWED_ACTIONS:
                self.gateway._record_abuse("trial_denied_action", _digest16(self._client_ip() or "unknown"),
                                           str(body.get("action") or ""))
                self._send(200, {"ok": False, "action": str(body.get("action") or ""), "result": None,
                                 "error": "the shared trial key is read-only; allowed actions: "
                                          f"{sorted(TRIAL_ALLOWED_ACTIONS)} — sign up free for the full "
                                          "surface: POST /v1/signup {email}",
                                 "candidate": True, "serves_truth": False})
                return
            if not self._rate_checked(verified):
                return
            try:
                envelope = self.gateway.agent_dispatch({**body, "_account_id": verified.get("account_id")})
            except Exception as error:  # noqa: BLE001
                envelope = {"ok": False, "action": str(body.get("action") or ""), "result": None,
                            "error": f"internal error: {str(error)[:200]}", "candidate": True,
                            "serves_truth": False}
            sent = self._send(200, envelope)
            self.gateway.meter(str(verified.get("key_id")), f"agent:{body.get('action', '?')}",
                               request_bytes, sent)
        elif path == "/v1/upgrade":
            if verified.get("trial"):
                self._send(403, {"error": "the shared trial key has no account to upgrade — sign up free "
                                          "first: POST /v1/signup {email}", "serves_truth": False})
                return
            target_plan = str(body.get("plan") or "")
            if target_plan != DEFAULT_PLAN and self.gateway.billing_status()["payments_enabled"]:
                # money is live: a paid plan is entered ONLY through a completed, webhook-verified checkout
                self._send(402, {"ok": False, "payment_required": True, "plan": target_plan,
                                 "checkout": "POST /v1/billing/checkout -> complete the hosted Stripe page",
                                 "candidate": True, "serves_truth": False})
                return
            result = self.gateway.set_plan(str(verified.get("account_id") or ""), str(body.get("plan") or ""))
            if result.get("ok"):
                result["usage_after_upgrade"] = self.gateway.usage(verified)
            self._send(200 if result.get("ok") else 400, result)
        else:
            self._send(404, {"error": "unknown path", "serves_truth": False})

    def log_message(self, *args: Any) -> None:  # receipts are the record; stderr stays quiet
        return


def start_gateway(port: int = 0, data_dir: Optional[Path] = None,
                  fixtures: Optional[dict] = None) -> tuple[ThreadingHTTPServer, threading.Thread, int,
                                                            CapabilitySaasGateway]:
    gateway = CapabilitySaasGateway(data_dir=data_dir, fixtures=fixtures)
    handler = type("BoundGatewayHandler", (_GatewayHandler,), {"gateway": gateway})
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    thread = threading.Thread(target=server.serve_forever, name=SERVICE_NAME, daemon=True)
    thread.start()
    return server, thread, server.server_address[1], gateway


# ====================================================================================================================
def _http(method: str, url: str, body: Optional[dict] = None, key: str = "") -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(url, method=method, headers=headers,
                                     data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            try:
                return response.status, json.loads(raw)
            except json.JSONDecodeError:
                return response.status, {"_raw": raw[:400]}
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read().decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return error.code, {}


def _self_test() -> int:
    import tempfile
    checks: list[tuple[str, bool, str]] = []
    saved = {k: os.environ.get(k) for k in (DATA_DIR_ENVIRONMENT_VARIABLE, "OH_AGENT_TOOL_DATA_DIR",
                                            "OH_LEARNING_DATA_DIR")}
    server = None
    try:
        with tempfile.TemporaryDirectory() as sandbox:
            os.environ["OH_AGENT_TOOL_DATA_DIR"] = str(Path(sandbox) / "agent")
            os.environ["OH_LEARNING_DATA_DIR"] = str(Path(sandbox) / "learning")
            from scripts.capability_retrieval_mcp_server import _synthetic_search_index
            server, _thread, port, gateway = start_gateway(
                port=0, data_dir=Path(sandbox) / "saas",
                fixtures={"index": _synthetic_search_index(), "requests_per_day_override": 6})
            base = f"http://127.0.0.1:{port}"

            # (1) landing + console + health + pricing are up.
            code_home, _ = _http("GET", base + "/")
            code_health, health = _http("GET", base + "/healthz")
            code_pricing, pricing = _http("GET", base + "/v1/pricing")
            console_request = urllib.request.Request(base + "/console")
            with urllib.request.urlopen(console_request, timeout=10) as console_response:
                console_html = console_response.read().decode("utf-8")
            checks.append(("landing/console/healthz/pricing respond; pricing lists the capability plans",
                           code_home == 200 and code_health == 200 and health["ok"] and code_pricing == 200
                           and "Taedri console" in console_html and "/v1/admin/reindex" in console_html
                           and {p["plan"] for p in pricing["plans"]} == set(PLAN_REQUEST_LIMITS_PER_DAY),
                           json.dumps(pricing)[:200]))

            # (2) SIGNUP end-to-end through the real identity engine; raw key + secret returned once.
            code, signup = _http("POST", base + "/v1/signup", {"email": "dev@example.com"})
            api_key = signup.get("api_key", "")
            checks.append(("signup mints a real key via the embedded identity flow",
                           code == 200 and signup["ok"] and api_key.startswith("ak_")
                           and signup["plan"] == DEFAULT_PLAN and signup["account_secret"], json.dumps(signup)[:200]))

            # (3) auth is enforced: no key / wrong key -> 401.
            code_none, _ = _http("POST", base + "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            code_bad, _ = _http("POST", base + "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                                key="ak_wrong")
            checks.append(("missing/invalid key -> 401", code_none == 401 and code_bad == 401, ""))

            # (4) MCP over HTTP: initialize, tools/list (7 tools), tools/call primitive_search hits the target.
            _c, init = _http("POST", base + "/mcp",
                             {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, key=api_key)
            _c, listed = _http("POST", base + "/mcp",
                               {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, key=api_key)
            _c, called = _http("POST", base + "/mcp",
                               {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                "params": {"name": "primitive_search",
                                           "arguments": {"query": "ofac sanctions screening entityrecord",
                                                         "limit": 5}}}, key=api_key)
            search = json.loads(called["result"]["content"][0]["text"])
            checks.append(("remote MCP works: initialize + 7 tools + search returns the target primitive",
                           init["result"]["serverInfo"]["name"] == "capability-retrieval"
                           and len(listed["result"]["tools"]) == 7
                           and search["results"][0]["primitive_id"] == "prim:test:target",
                           json.dumps(search)[:200]))

            # (5) deterministic agent API + tenant denial of owner-only actions.
            _c, agent_ok = _http("POST", base + "/v1/agent",
                                 {"action": "retrieval.search", "args": {"query": "ofac sanctions screening"}},
                                 key=api_key)
            _c, denied = _http("POST", base + "/v1/agent", {"action": "provision.apply",
                                                            "args": {"confirm": True}}, key=api_key)
            checks.append(("agent API serves search; provisioning is owner-only for tenants",
                           agent_ok["ok"] and agent_ok["result"]["results"]
                           and denied["ok"] is False and "owner-only" in denied["error"],
                           json.dumps(denied)[:200]))

            # (6) usage + metering + draft invoice from the billing plane (plan base price, no fake charge).
            code, usage = _http("GET", base + "/v1/usage", key=api_key)
            checks.append(("usage reports metered requests + a draft invoice from billing_plane",
                           code == 200 and usage["requests_today"] >= 4
                           and usage["draft_invoice"]["status"] == "draft"
                           and usage["plan"] == DEFAULT_PLAN, json.dumps(usage)[:240]))

            # (7) upgrade records the plan; invoice reflects the pro base price.
            _c, upgraded = _http("POST", base + "/v1/upgrade", {"plan": "capability_pro"}, key=api_key)
            checks.append(("upgrade to capability_pro recorded; draft invoice carries the pro base price",
                           upgraded["ok"] and upgraded["plan"] == "capability_pro"
                           and upgraded["usage_after_upgrade"]["draft_invoice"]["total_cents"] > 0,
                           json.dumps(upgraded)[:200]))

            # (7b) payments seam: DISABLED by default (honest 503, nothing charged); with the three STRIPE_*
            #      secrets set (fixture transport, no network) checkout returns the hosted URL, /v1/upgrade
            #      becomes 402 payment-required, and ONLY a correctly-signed webhook flips the plan — a bad
            #      signature is rejected and changes nothing (the verifier can go RED).
            account_id = usage["account_id"]
            code_bstatus, bstatus = _http("GET", base + "/v1/billing/status")
            code_disabled, disabled = _http("POST", base + "/v1/billing/checkout", {}, key=api_key)
            checks.append(("payments disabled by default: status computes the 3 missing secrets; checkout "
                           "refuses honestly with 503",
                           code_bstatus == 200 and bstatus["payments_enabled"] is False
                           and len(bstatus["missing_environment_variables"]) == 3
                           and code_disabled == 503 and disabled["ok"] is False,
                           json.dumps(bstatus)[:200]))
            stripe_env = {STRIPE_API_KEY_ENVIRONMENT_VARIABLE: "sk_test_selftest",
                          STRIPE_PRICE_ID_PRO_ENVIRONMENT_VARIABLE: "price_selftest_pro",
                          STRIPE_WEBHOOK_SECRET_ENVIRONMENT_VARIABLE: "whsec_selftest"}
            saved_stripe = {name: os.environ.get(name) for name in stripe_env}
            os.environ.update(stripe_env)
            gateway.fixtures["stripe_transport"] = lambda stripe_path, fields: (
                200, {"id": "cs_test_1", "url": "https://checkout.stripe.com/c/pay/cs_test_1",
                      "price_used": fields.get("line_items[0][price]")})
            try:
                code_checkout, checkout = _http("POST", base + "/v1/billing/checkout", {}, key=api_key)
                _c, upgrade_gated = _http("POST", base + "/v1/upgrade", {"plan": "capability_pro"},
                                          key=api_key)
                checks.append(("payments enabled: checkout returns the hosted Stripe URL; /v1/upgrade is "
                               "402 payment-required (no free flip)",
                               code_checkout == 200 and checkout["ok"]
                               and checkout["checkout_url"].startswith("https://checkout.stripe.com/")
                               and upgrade_gated.get("payment_required") is True
                               and "checkout" in upgrade_gated, json.dumps(checkout)[:200]))

                def _webhook_post(payload_bytes: bytes, signature: str) -> tuple[int, dict]:
                    hook = urllib.request.Request(base + "/v1/billing/webhook", data=payload_bytes,
                                                  method="POST",
                                                  headers={"Content-Type": "application/json",
                                                           "Stripe-Signature": signature})
                    try:
                        with urllib.request.urlopen(hook, timeout=15) as hook_response:
                            return hook_response.status, json.loads(
                                hook_response.read().decode("utf-8") or "{}")
                    except urllib.error.HTTPError as hook_error:  # type: ignore[attr-defined]
                        return hook_error.code, json.loads(hook_error.read().decode("utf-8") or "{}")

                gateway.set_plan(account_id, DEFAULT_PLAN)   # observable flip target
                event_payload = json.dumps({"type": "checkout.session.completed",
                                            "data": {"object": {"client_reference_id": account_id}}}
                                           ).encode("utf-8")
                timestamp = str(int(time.time()))
                good_signature = "t=" + timestamp + ",v1=" + hmac.new(
                    b"whsec_selftest", f"{timestamp}.".encode("utf-8") + event_payload,
                    hashlib.sha256).hexdigest()
                code_bad, _bad = _webhook_post(event_payload, f"t={timestamp},v1=deadbeef")
                plan_after_bad = gateway.tenant_plan(account_id)
                code_good, hooked = _webhook_post(event_payload, good_signature)
                plan_after_good = gateway.tenant_plan(account_id)
                checks.append(("webhook: bad signature -> 400 and NO plan change; signed completed-checkout "
                               "flips the plan to pro",
                               code_bad == 400 and plan_after_bad == DEFAULT_PLAN
                               and code_good == 200 and hooked["ok"]
                               and plan_after_good == PRO_PLAN, json.dumps(hooked)[:200]))
            finally:
                for name, value in saved_stripe.items():
                    if value is None:
                        os.environ.pop(name, None)
                    else:
                        os.environ[name] = value
                gateway.fixtures.pop("stripe_transport", None)

            # (8) rate limit enforced (fixture limit 6): drive past it -> 429 with upgrade pointer.
            last_code = 200
            for _i in range(8):
                last_code, last = _http("POST", base + "/v1/agent", {"action": "actions.list"}, key=api_key)
                if last_code == 429:
                    break
            checks.append(("daily plan limit enforced with 429 + upgrade pointer",
                           last_code == 429 and "limit" in last.get("error", ""), str(last_code)))

            # (8b) the limit-hit BONUS lane (owner 2026-07-10): the 429 itself carries the share-to-continue
            #      offer; contributing anonymized cards grants bonus requests TODAY and unblocks the next call;
            #      stored contributions carry a contributor digest, no identity fields, candidate-only flags.
            checks.append(("the 429 carries the share-to-continue offer (continue_free -> /v1/contribute)",
                           "/v1/contribute" in last.get("continue_free", ""), json.dumps(last)[:220]))
            _c, shared = _http("POST", base + "/v1/contribute",
                               {"cards": [{"primitive_id": "prim:shared:1", "title": "Shared retry with jitter",
                                           "blackbox": "Exponential backoff with jitter.",
                                           "email": "dev@example.com", "account_id": "acc-should-strip"},
                                          {"primitive_id": "prim:shared:2", "title": "Shared csv sniffer",
                                           "blackbox": "Sniffs csv dialects."}]}, key=api_key)
            code_after_bonus, _after = _http("POST", base + "/v1/agent", {"action": "actions.list"}, key=api_key)
            contribution_rows = [json.loads(line) for line in
                                 gateway._contributions_path().read_text().splitlines() if line.strip()]
            checks.append(("contribute grants the bonus (2 cards -> +{}) and the next request passes again"
                           .format(2 * CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD),
                           shared["ok"] and shared["accepted"] == 2
                           and shared["bonus_added_now"] == 2 * CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD
                           and code_after_bonus == 200, json.dumps(shared)[:200]))
            checks.append(("contributions are ANONYMIZED candidate rows (16-hex contributor digest; email/"
                           "account_id stripped; serves_truth=false)",
                           len(contribution_rows) == 2
                           and all(len(r["contributor"]) == 16 and r["contributor"] != "acc-should-strip"
                                   for r in contribution_rows)
                           and all("email" not in r["card"] and "account_id" not in r["card"]
                                   for r in contribution_rows)
                           and all(r["candidate"] is True and r["serves_truth"] is False
                                   for r in contribution_rows), json.dumps(contribution_rows)[:240]))

            # (8c) the news/blog surface (owner 2026-07-10): landing digest + share pitch; /news renders every
            #      TAEDRI_NEWS entry; pricing exposes the contributor bonus (amounts from the ONE constant).
            with urllib.request.urlopen(base + "/", timeout=10) as landing_response:
                landing_html = landing_response.read().decode("utf-8")
            with urllib.request.urlopen(base + "/news", timeout=10) as news_response:
                news_html = news_response.read().decode("utf-8")
            # `/` now serves the DESIGNED Taedri Landing (Claude Design handoff overrides the stub); the news
            # digest + share-to-continue pitch moved to /news + the 429 contributor offer (tested in 8b). Here:
            # the designed hero is served, /news renders every entry, pricing still exposes the contributor bonus.
            checks.append(("landing serves the designed Taedri hero; /news renders every entry; "
                           "pricing exposes the contributor bonus",
                           "This already exists" in landing_html and "taedri" in landing_html
                           and all(entry["title"] in news_html for entry in TAEDRI_NEWS)
                           and pricing["contributor_bonus"]["bonus_requests_per_accepted_card"]
                           == CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD,
                           news_html[:200]))

            # (8d) public site surfaces: /docs computed from the live TOOLS registry + plan constants;
            #      /status renders health; /news.rss is well-formed from the same news constant; the 429
            #      carried standard Retry-After / X-RateLimit-* headers.
            from scripts.capability_retrieval_mcp_server import TOOLS as _mcp_tools
            with urllib.request.urlopen(base + "/docs", timeout=10) as docs_response:
                docs_html = docs_response.read().decode("utf-8")
            with urllib.request.urlopen(base + "/status", timeout=10) as status_response:
                status_html = status_response.read().decode("utf-8")
            with urllib.request.urlopen(base + "/news.rss", timeout=10) as rss_response:
                rss_type = rss_response.headers.get("Content-Type", "")
                rss_xml = rss_response.read().decode("utf-8")
            rate_headers_request = urllib.request.Request(base + "/v1/agent", method="POST",
                                                          data=json.dumps({"action": "actions.list"}).encode(),
                                                          headers={"Content-Type": "application/json",
                                                                   "Authorization": f"Bearer {api_key}"})
            # burn the bonus-extended budget down to the wall again so the header check sees a real 429
            retry_after_header = ""
            for _i in range(2 * CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD + 2):
                try:
                    with urllib.request.urlopen(rate_headers_request, timeout=10):
                        pass
                except urllib.error.HTTPError as http_error:
                    if http_error.code == 429:
                        retry_after_header = http_error.headers.get("Retry-After", "")
                        break
            checks.append(("/docs computed from TOOLS + plans; /status renders health; /news.rss well-formed; "
                           "429 carries Retry-After",
                           all(tool["name"] in docs_html for tool in _mcp_tools)
                           and str(len(_mcp_tools)) in docs_html
                           and all(plan in docs_html for plan in PLAN_REQUEST_LIMITS_PER_DAY)
                           and "Taedri status" in status_html and "governed index present" in status_html
                           and rss_xml.startswith("<?xml") and "<rss" in rss_xml and "rss+xml" in rss_type
                           and all(entry["title"] in rss_xml for entry in TAEDRI_NEWS)
                           and retry_after_header.isdigit() and int(retry_after_header) >= 1,
                           json.dumps({"retry_after": retry_after_header, "rss_type": rss_type})[:200]))

            # (8d-2) the SETUP + VERIFY surfaces (owner 2026-07-10): /setup renders a per-harness recipe for
            #        every SETUP_HARNESSES row (Claude Code / Codex / Hermes / OpenClaw / HTTP / Python), and
            #        /verify is a JSON self-check (gateway up + search returns) usable with no signup.
            with urllib.request.urlopen(base + "/setup", timeout=10) as setup_response:
                setup_html = setup_response.read().decode("utf-8")
            _c, verify_json = _http("GET", base + "/verify")
            # /verify RUNS a probe search (search_seconds present) + reports gateway/index health + the harness
            # list. (search_returned depends on the corpus — here the fixture; the REAL governed index returns
            # hits, verified live at 0.3s/5 results — so assert the endpoint SHAPE + that the probe executed.)
            checks.append(("/setup renders a recipe for EVERY harness (Claude Code/Codex/Hermes/OpenClaw/HTTP/"
                           "Python, each snippet from the live base); /verify is a well-formed self-check that "
                           "runs a probe search and reports health + the harness list",
                           all(h["name"] in setup_html for h in SETUP_HARNESSES)
                           and "claude mcp add" in setup_html and "mcp_servers.taedri" in setup_html
                           and verify_json.get("checks", {}).get("gateway_ok") is True
                           and isinstance(verify_json.get("checks", {}).get("search_seconds"), (int, float))
                           and {h["id"] for h in SETUP_HARNESSES} == set(verify_json.get("harnesses", [])),
                           json.dumps(verify_json.get("checks"))[:160]))

            # (8e) the boot warmer flips health honestly (fixture lane skips the heavy corpus load).
            warm_before = gateway.health()["index_warm"]
            gateway.warm_serving_index()
            warm_after = gateway.health()
            checks.append(("warm_serving_index flips health.index_warm false->true and records seconds",
                           warm_before is False and warm_after["index_warm"] is True
                           and isinstance(warm_after["index_warm_seconds"], float),
                           json.dumps(warm_after)[:160]))

            # (8f) the PUBLIC TRIAL KEY (owner 2026-07-10): works with no signup; read-only (denied agent
            #      action + denied MCP write tool are refused with a signup pointer AND abuse-receipted);
            #      per-IP slice then the shared pool block with 429s; trial usage reports the pool; upgrade
            #      is refused; abuse receipts carry IP digests only.
            trial = gateway.trial_key()
            _c, trial_ok = _http("POST", base + "/v1/agent", {"action": "actions.list"}, key=trial)
            _c, trial_denied = _http("POST", base + "/v1/agent", {"action": "learning.status"}, key=trial)
            _c, trial_tool_denied = _http("POST", base + "/mcp",
                                          {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                           "params": {"name": "record_reuse_outcome", "arguments": {}}},
                                          key=trial)
            _c, trial_usage_body = _http("GET", base + "/v1/usage", key=trial)
            code_up, _trial_upgrade = _http("POST", base + "/v1/upgrade", {"plan": "capability_pro"}, key=trial)
            checks.append(("trial key: works signup-free; read-only denials point to signup; usage reports "
                           "the shared pool; upgrade refused 403",
                           trial_ok["ok"] is True and trial_denied["ok"] is False
                           and "sign up" in trial_denied["error"]
                           and "read-only" in trial_tool_denied["error"]["message"]
                           and trial_usage_body["plan"] == TRIAL_PLAN
                           and trial_usage_body["requests_per_day"] == TRIAL_REQUEST_LIMIT_PER_DAY
                           and code_up == 403,
                           json.dumps({"denied": trial_denied, "usage": trial_usage_body})[:240]))
            gateway.fixtures["trial_ip_override"] = 3       # tiny slices so the caps are provable offline
            gateway.fixtures["trial_pool_override"] = 5
            trial_codes = []
            for _i in range(5):
                trial_code, trial_last = _http("POST", base + "/v1/agent", {"action": "actions.list"}, key=trial)
                trial_codes.append(trial_code)
            abuse_rows = [json.loads(line) for line in
                          gateway._abuse_events_path().read_text().splitlines() if line.strip()]
            ip_cap_rows = [r for r in abuse_rows if r["kind"] == "trial_ip_cap"]
            checks.append(("trial abuse detection: per-IP slice blocks with 429 + abuse receipts hold IP "
                           "DIGESTS only (raw address nowhere)",
                           429 in trial_codes and ip_cap_rows
                           and all(len(r["ip_digest"]) == 16 and "127.0.0.1" not in json.dumps(r)
                                   for r in abuse_rows)
                           and any(r["kind"] == "trial_denied_action" for r in abuse_rows),
                           json.dumps(abuse_rows[-2:])[:240]))
            gateway.fixtures.pop("trial_ip_override", None)
            gateway.fixtures.pop("trial_pool_override", None)

            # (9) SECRET HYGIENE: the raw key + account secret appear in NO persisted file.
            leaks = []
            for root in (Path(sandbox), ):
                for file in root.rglob("*"):
                    if file.is_file():
                        try:
                            text = file.read_text()
                        except (UnicodeDecodeError, OSError):
                            continue
                        if api_key in text or signup["account_secret"] in text:
                            leaks.append(str(file))
            checks.append(("raw key + account secret persisted NOWHERE (hashes only)", not leaks, str(leaks)))

            # (10b) OWNER admin: tenant 403; owner adds a card (truth bit force-stripped), tombstones another,
            #       reindexes (overlay-only fixture corpus), and a FRESH gateway on the same /data volume
            #       serves the added card through /mcp — the full remote-CRUD loop, offline.
            owner_secret = "owner-test-key-abcdef0123456789"
            os.environ[OWNER_KEY_ENVIRONMENT_VARIABLE] = owner_secret
            _code_denied, tenant_denied = _http("POST", base + "/v1/admin/primitives", {"cards": []}, key=api_key)
            code_add, added = _http("POST", base + "/v1/admin/primitives",
                                    {"cards": [{"primitive_id": "prim:test:overlay1",
                                                "title": "Overlay parse EDI 837 claim batches",
                                                "blackbox": "Parses EDI 837 claim batches into rows.",
                                                "input_edge": "Edi837File", "output_edge": "ClaimRowList",
                                                "blocking_keys": ["edi", "claim", "parse"],
                                                "serves_truth": True},   # client lie -> must be stripped
                                               {"primitive_id": "prim:test:overlay2", "title": "Overlay two",
                                                "blackbox": "Second overlay card.",
                                                "blocking_keys": ["overlay", "two"]}]}, key=owner_secret)
            overlay_rows = [json.loads(line) for line in
                            (gateway._overlay_path().read_text().splitlines()) if line.strip()]
            _c, _tomb = _http("POST", base + "/v1/admin/primitives/remove",
                              {"primitive_id": "prim:test:overlay2"}, key=owner_secret)
            gateway.fixtures["reindex_corpus_files"] = []   # overlay-only rebuild: tiny + offline
            _http("POST", base + "/v1/admin/reindex", {}, key=owner_secret)
            for _ in range(60):
                _c, reindex_status = _http("GET", base + "/v1/admin/reindex", key=owner_secret)
                if reindex_status["status"].get("done") or reindex_status["status"].get("error"):
                    break
                time.sleep(0.5)
            checks.append(("admin gate: tenant 403; owner add strips the truth bit; tombstone + reindex complete",
                           tenant_denied.get("error", "").startswith("administrator key required")
                           and code_add == 200 and added["accepted"] == 2
                           and all(r["serves_truth"] is False for r in overlay_rows)
                           and reindex_status["status"].get("done") is True
                           and reindex_status["status"].get("indexed_cards") == 1,
                           json.dumps({"denied": tenant_denied, "status": reindex_status})[:280]))

            server2, _t2, port2, gateway2 = start_gateway(port=0, data_dir=Path(sandbox) / "saas")
            base2 = f"http://127.0.0.1:{port2}"
            _c, signup2 = _http("POST", base2 + "/v1/signup", {"email": "dev2@example.com"})
            _c, served = _http("POST", base2 + "/mcp",
                               {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                                "params": {"name": "primitive_search",
                                           "arguments": {"query": "parse edi 837 claim batches", "limit": 3}}},
                               key=signup2["api_key"])
            served_body = json.loads(served["result"]["content"][0]["text"])
            _c, ledgers = _http("GET", base + "/v1/admin/ledgers", key=owner_secret)
            server2.shutdown()
            os.environ.pop(OWNER_KEY_ENVIRONMENT_VARIABLE, None)
            checks.append(("fresh gateway on the same volume serves the overlay card; tombstoned card absent; "
                           "ledgers export",
                           served_body["results"]
                           and served_body["results"][0]["primitive_id"] == "prim:test:overlay1"
                           and all(h["primitive_id"] != "prim:test:overlay2" for h in served_body["results"])
                           and ledgers["counts"]["invocations"] >= 5, json.dumps(served_body)[:280]))

            # (10c) THE WORKING USER LOOP: session login -> dashboard; private primitives add -> include_mine
            #       search (private first, labeled) -> tombstone hides; /v1/logs returns own receipts only.
            gateway.fixtures["requests_per_day_override"] = 100   # the 429 check above exhausted the tiny budget
            login_code, login_body = _http("POST", base + "/v1/session",
                                           {"email": "dev@example.com", "secret": signup["account_secret"]})
            session_cookie = f"{_SESSION_COOKIE_NAME}={login_body.get('session_id', '')}"
            dash_request = urllib.request.Request(base + "/dashboard", headers={"Cookie": session_cookie})
            with urllib.request.urlopen(dash_request, timeout=10) as dash_response:
                dashboard_html = dash_response.read().decode("utf-8")
            redirect_check = urllib.request.Request(base + "/dashboard")
            try:
                with urllib.request.urlopen(redirect_check, timeout=10) as anon:
                    anon_redirected = anon.status in (302,) or "Log in" in anon.read().decode("utf-8")
            except urllib.error.HTTPError as redirect_error:
                anon_redirected = redirect_error.code == 302
            _c, my_add = _http("POST", base + "/v1/my/primitives",
                               {"cards": [{"primitive_id": "prim:mine:edi", "title": "My EDI 837 claim parser",
                                           "blackbox": "Parses EDI 837 claims.", "blocking_keys": ["edi", "claim"],
                                           "serves_truth": True}]}, key=api_key)
            _c, my_search = _http("POST", base + "/v1/agent",
                                  {"action": "retrieval.search",
                                   "args": {"query": "parse edi 837 claim batches", "include_mine": True}},
                                  key=api_key)
            _c, _tombstone = _http("POST", base + "/v1/my/primitives/remove",
                                   {"primitive_id": "prim:mine:edi"}, key=api_key)
            _c, my_after = _http("GET", base + "/v1/my/primitives", key=api_key)
            _c, my_logs = _http("GET", base + "/v1/logs", key=api_key)
            my_rows = [json.loads(line) for line in
                       (gateway._tenant_overlay_dir(login_body.get("account_id", ""))
                        / "cards.jsonl").read_text().splitlines() if line.strip()]
            checks.append(("working loop: session login -> dashboard (anon redirected); private add strips truth "
                           "bit; include_mine surfaces it first; tombstone hides; logs return own receipts",
                           login_code == 200 and login_body["ok"] and "taedri dashboard" in dashboard_html
                           and anon_redirected and my_add["ok"] and my_add["accepted"] == 1
                           and all(r["serves_truth"] is False for r in my_rows)
                           and my_search["result"]["private_hits"] == 1
                           and my_search["result"]["results"][0]["primitive_id"] == "prim:mine:edi"
                           and my_search["result"]["results"][0]["visibility"] == "private"
                           and my_after["count"] == 0 and my_logs["ok"] and my_logs["count"] >= 1,
                           json.dumps({"login": login_body, "search0": my_search.get("result", {}).get("results",
                                       [{}])[0], "after": my_after, "logs": my_logs.get("count")})[:400]))

            # (10) receipts exist in the billing_ledger shape and the statement accepts them.
            from scripts import billing_ledger
            receipts = gateway._load_receipts()
            statement = billing_ledger.statement(receipts, realm=gateway.realm, month=_month())
            checks.append((f"invocation receipts ({len(receipts)}) statement cleanly via billing_ledger",
                           len(receipts) >= 5 and statement["receipts"] == len(receipts)
                           and MODEL_CLASS_TOOL_CALL in statement["by_class"], json.dumps(statement)[:200]))
    finally:
        if server is not None:
            server.shutdown()
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - capability_saas_gateway: hosted SaaS end-to-end OFFLINE — signup->key "
          f"(real identity engine, hashes only) -> Bearer-authed remote MCP (7 tools) + deterministic agent API "
          f"(owner-only actions denied) -> metering receipts -> usage/draft-invoice (billing_plane) -> plan "
          f"upgrade -> 429 rate limit -> share-to-continue contributor bonus + news surface. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:300]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Hosted capability SaaS gateway (MCP over HTTP + agent API).")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--data-dir", default="")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.serve:
        _server, thread, port, _gateway = start_gateway(
            port=args.port, data_dir=Path(args.data_dir) if args.data_dir else None)
        # boot-time warmer: the 2026-07-10 containerized prod run measured cold first-search > 240s — load the
        # governed index NOW (daemon; requests during the warm window still answer, just slower).
        threading.Thread(target=_gateway.warm_serving_index, name="boot-index-warmer", daemon=True).start()
        print(json.dumps({"service": SERVICE_NAME, "version": SERVICE_VERSION, "port": port,
                          "endpoints": ["/", "/setup", "/verify", "/docs", "/news", "/news.rss", "/status",
                                        "/healthz", "/v1/pricing", "/v1/signup", "/mcp", "/v1/agent",
                                        "/v1/usage", "/v1/upgrade", "/v1/contribute"],
                          "serves_truth": False}))
        thread.join()
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
