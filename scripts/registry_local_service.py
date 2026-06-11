#!/usr/bin/env python3
"""scripts.registry_local_service — the LOCAL Open*Hub registry plane (fulfils the
``local_openhub_projection_api`` service declared in architecture/local_service_registry.json).

This is the data backend that makes the full-design dashboards REAL instead of mock: the kit's
OhDashboard / Installed / EntryDetail read per-account workspace state from here, and Browse can
read the public catalog from here. Two cleanly separated surfaces:

  PUBLIC catalog (read-only projection of what Browse already shows) — seeded by extracting each
  hub's ``entries`` array from the design bundle (single source; no hand-retyped catalog):
    GET  /api/openhub/<realm>/search?q=     entries for a hub (optional substring filter)
    GET  /api/openhub/<realm>/entry/<id>    one entry
    GET  /api/openhub/catalog               {realm: entry_count} across the bundle

  PER-ACCOUNT workspace (session-gated; the real numbers behind the dashboard) — append-only,
  the account is resolved by VALIDATING the realm session against the identity service
  (cross-service auth, never trusting a client-supplied account id):
    POST /api/openhub/<realm>/install       {session_id, entry}     record an install
    POST /api/openhub/<realm>/uninstall     {session_id, entry_id}  record an uninstall
    POST /api/openhub/<realm>/submit        {session_id, entry}      publish -> REVIEW QUEUE
    GET  /api/openhub/<realm>/workspace?session_id=   the dashboard summary (real)

  GET /healthz /readyz /version /api/status   (Cloud-Run-like service contract)

LAW (mirrors the registry's law + the repo's promotion boundary):
  * truth_authority = False — this is a projection/workspace store, never a truth source.
  * submit lands in a REVIEW QUEUE (candidate, status=in_review), never the public-active catalog
    (discovery is not trust; candidate != active).
  * no secrets stored; the raw session id is never persisted (only the resolved account id is).
  * append-only JSONL; the workspace summary is REPLAYED from the log (no destructive state).
    Each log is a SQLite-WAL append-log (scripts._jsonl_store): the db (off the scanned state dir)
    is the crash-safe primary + the O(attach) rehydration index, while the *.jsonl stays the durable,
    externally-read on-disk record. Reads are db-served (never an O(n) per-request file re-parse); a
    restart reopens the db (no whole-file re-parse) and a pre-existing legacy jsonl is migrated
    losslessly. SINGLE-MACHINE LAW: one service process owns state_dir (WAL is single-writer-node).
  * api_calls.jsonl is size-rotated (API_CALLS_ROTATE_LINES) keeping exactly one previous
    generation (.1, preserved — lossless); counters rebuild from the live generation only.

Run ``python3 -m scripts.registry_local_service --self-test`` for the offline store proof
(cache-after-write, restart rehydration, rotation); the full service/HTTP proof remains
``scripts/check_registry_backend.py``.

Offline, stdlib-only. Port + identity port come from the registries (single source, drift-gated by
scripts/check_registry_backend.py).
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts._jsonl_store import AppendLog  # noqa: E402  (SQLite-WAL append-log behind each jsonl)

SERVICE_ID = "local_openhub_projection_api"
REGISTRY_PATH = REPO_ROOT / "architecture" / "local_service_registry.json"
IDENTITY_REGISTRY_PATH = REPO_ROOT / "architecture" / "identity_realm_registry.json"
BUNDLE_DIR = REPO_ROOT / "dist" / "sites" / "openharness-design"
VERSION = "1.0"

MAX_BODY_BYTES = 256 * 1024
CALL_WINDOW_DAYS = 30            # the "· 30d" window on the dashboard stat
CALL_WINDOW_SECONDS = CALL_WINDOW_DAYS * 24 * 60 * 60
FREE_TIER_CALL_CAP = 1000        # calls/30d that map to a full usage meter on the free tier
ENTRY_FIELDS = ("id", "name", "by", "facet", "score", "installs", "ver", "desc")
ACTIVITY_LIMIT = 8               # most-recent events shown on the dashboard
REVIEW_DECISIONS = ("approve", "reject", "revoke")   # approve = promote; revoke = rollback
# Size bound for the hot api_calls.jsonl (it grows per authed request, unbounded otherwise).
# At this many lines the live log rotates to exactly ONE preserved previous generation
# (api_calls.jsonl.1) — far above CALL_WINDOW/FREE_TIER scale, so the 30d meter stays usable.
API_CALLS_ROTATE_LINES = 50_000


class SelfReviewError(Exception):
    """A reviewer attempted to decide on a candidate they submitted (separation of duties)."""


def _registry_port() -> int:
    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    svc = next(s for s in reg["services"] if s["service_id"] == SERVICE_ID)
    return int(svc["port"])


def _identity_base() -> str:
    """Identity service base — port is the single source in the realm registry (drift-gated)."""
    port = int(json.loads(IDENTITY_REGISTRY_PATH.read_text(encoding="utf-8"))["defaults"]["port"])
    return os.environ.get("AIDR_IDENTITY_BASE", f"http://127.0.0.1:{port}").rstrip("/")


# ---------------------------------------------------------------------------
# catalog extraction — the bundle's hub `entries:` arrays are the single source
# ---------------------------------------------------------------------------
_ENTRY_OBJ_RE = re.compile(r"\{[^{}]*\}")
_FIELD_RE = re.compile(r"(\w+)\s*:\s*'((?:[^'\\]|\\.)*)'")


def _unescape(s: str) -> str:
    return s.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def _extract_entries_array(src: str) -> str | None:
    """Return the text inside the first top-level ``entries: [ ... ]`` (bracket-matched)."""
    m = re.search(r"entries\s*:\s*\[", src)
    if not m:
        return None
    i = m.end() - 1  # at the '['
    depth = 0
    for j in range(i, len(src)):
        c = src[j]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return src[i + 1:j]
    return None


def extract_catalog(bundle_dir: Path) -> dict[str, list[dict]]:
    """{realm -> [entry, ...]} by parsing every <hub>/<hub>-main.jsx in the bundle.

    realm == the hub directory name (the kit derives the same id from brand.name). Best-effort:
    a hub that fails to parse is simply absent (logged by the caller via the returned counts), and
    the UI falls back to its in-file entries — never a fake catalog.
    """
    catalog: dict[str, list[dict]] = {}
    for jsx in sorted(bundle_dir.glob("*/*-main.jsx")):
        realm = jsx.parent.name
        body = _extract_entries_array(jsx.read_text(encoding="utf-8"))
        if not body:
            continue
        entries: list[dict] = []
        for obj in _ENTRY_OBJ_RE.findall(body):
            fields = {k: _unescape(v) for k, v in _FIELD_RE.findall(obj)}
            if fields.get("id") and fields.get("name"):
                entries.append({k: fields[k] for k in ENTRY_FIELDS if k in fields})
        if entries:
            catalog[realm] = entries
    return catalog


# ---------------------------------------------------------------------------
# session validation (cross-service) — resolves a realm session to an account id
# ---------------------------------------------------------------------------
class SessionValidator:
    """Resolves (realm, session_id) -> account_id by asking the identity service. Injectable so the
    proof can run the gated paths without standing the identity service up."""

    def __init__(self, base: str | None = None) -> None:
        self.base = (base or _identity_base()).rstrip("/")

    def resolve(self, realm: str, session_id: str) -> str | None:
        if not realm or not session_id:
            return None
        url = f"{self.base}/api/identity/{realm}/session/validate"
        data = json.dumps({"session_id": session_id}).encode()
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                body = json.loads(resp.read().decode("utf-8") or "{}")
        except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
            return None
        return body.get("account_id") if body.get("valid") else None


# ---------------------------------------------------------------------------
# the store — append-only workspace log; the dashboard summary is replayed from it
# ---------------------------------------------------------------------------
class RegistryStore:
    def __init__(self, state_dir: Path | None = None, bundle_dir: Path | None = None,
                 rotate_calls_lines: int = API_CALLS_ROTATE_LINES) -> None:
        self.state_dir = Path(state_dir) if state_dir else (REPO_ROOT / "dist" / "registry")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_path = self.state_dir / "workspace.jsonl"      # install/uninstall/publish
        self.calls_path = self.state_dir / "api_calls.jsonl"          # every authed request
        self.review_path = self.state_dir / "review_queue.jsonl"      # publish submissions (candidates)
        self.decisions_path = self.state_dir / "review_decisions.jsonl"  # reviewer decisions (append-only)
        self.reviewers_path = self.state_dir / "reviewers.jsonl"      # reviewer roster grants/revokes
        self.admins_path = self.state_dir / "admins.jsonl"           # admin roster (operator-bootstrapped)
        self.catalog_path = self.state_dir / "catalog.json"
        self.lock = threading.Lock()
        self.rotate_calls_lines = rotate_calls_lines  # injectable so the self-test proves rotation cheaply
        # SQLite-WAL APPEND-LOG per JSONL (scripts._jsonl_store): the db (off the scanned state dir)
        # is the crash-safe primary + the O(attach) rehydration index; the *.jsonl stays the durable,
        # externally-read on-disk record. Reads are db-served (never an O(n) per-request file
        # re-parse); writes commit one ACID row then mirror the jsonl line — both under self.lock. A
        # restart reopens the db instead of re-parsing whole files; a pre-existing legacy jsonl is
        # migrated losslessly on first open. SINGLE-MACHINE LAW: exactly one service process owns
        # state_dir (deploy law — never `fly scale count >1` on stateful apps; WAL is single-writer-
        # node). busy_timeout makes a concurrent reader/writer WAIT, not error.
        self._logs: dict[Path, AppendLog] = {
            p: AppendLog(p)
            for p in (self.workspace_path, self.calls_path, self.review_path,
                      self.decisions_path, self.reviewers_path, self.admins_path)
        }
        self.catalog = self._load_or_build_catalog(bundle_dir or BUNDLE_DIR)
        # operator bootstrap seam: AIDR_REGISTRY_ADMINS="realm:account_id,realm2:acct" seeds admins
        # without a file write (handy for deploys). The file roster + this env allowlist are unioned;
        # admins are NEVER established from inside the app (no in-app privilege escalation).
        self._env_admins: set[tuple[str, str]] = set()
        for pair in (os.environ.get("AIDR_REGISTRY_ADMINS") or "").split(","):
            if ":" in pair:
                r, a = pair.split(":", 1)
                if r.strip() and a.strip():
                    self._env_admins.add((r.strip(), a.strip()))

    def _load_or_build_catalog(self, bundle_dir: Path) -> dict[str, list[dict]]:
        if self.catalog_path.exists():
            try:
                return json.loads(self.catalog_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        catalog = extract_catalog(bundle_dir) if bundle_dir.exists() else {}
        self.catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True), encoding="utf-8")
        return catalog

    def catalog_counts(self) -> dict[str, int]:
        return {realm: len(entries) for realm, entries in sorted(self.catalog.items())}

    def search(self, realm: str, q: str = "") -> list[dict]:
        # the live catalog = the immutable bundle SEED + promoted (reviewer-approved) community entries.
        entries = list(self.catalog.get(realm, [])) + self.promoted(realm)
        if not q:
            return entries
        ql = q.lower()
        return [e for e in entries if ql in json.dumps(e).lower()]

    def entry(self, realm: str, entry_id: str) -> dict | None:
        seed = next((e for e in self.catalog.get(realm, []) if e.get("id") == entry_id), None)
        if seed:
            return seed
        return next((e for e in self.promoted(realm) if e.get("id") == entry_id), None)

    def _rows(self, path: Path) -> list[dict]:
        """THE read path for every JSONL-backed query: the live-generation rows from the append-log's
        SQLite index (an indexed scan of an attached db — never a per-request whole-file re-parse).
        The log already returns a fresh list, safe to iterate while another request thread appends."""
        return self._logs[path].all()

    def _append(self, path: Path, rec: dict) -> None:
        """Append-through (caller MUST hold self.lock): one crash-safe SQLite commit, then the
        durable *.jsonl mirror line — the append-log does both atomically under its own lock."""
        self._logs[path].append(rec)

    def _rotate_calls_locked(self) -> None:
        """Size-based rotation for the API-call log (caller holds self.lock): rename the live file
        to ``api_calls.jsonl.1`` and start a fresh live generation. Exactly ONE previous generation
        is kept on disk, PRESERVED — rotation never truncates in place (lossless); a later rotation
        replaces ``.1`` (the deliberate retention bound for this operational request log), and the
        db retains every rotated row (queryable). Counters/summaries (e.g. the 30d meter) rebuild
        from the live generation only — an honest floor, never a fabricated number."""
        self._logs[self.calls_path].rotate()           # api_calls.jsonl → .1 + db generation bump

    def log_call(self, account_id: str, realm: str, method: str, path: str, now: int) -> None:
        with self.lock:
            self._append(self.calls_path, {"ts": now, "account_id": account_id, "realm": realm,
                                           "method": method, "path": path})
            if self._logs[self.calls_path].count() >= self.rotate_calls_lines:
                self._rotate_calls_locked()

    def record(self, account_id: str, realm: str, action: str, entry: dict, now: int) -> dict:
        """action in {install, uninstall, publish}. entry is a client-supplied SNAPSHOT (id/name/
        score/...); we keep only the known display fields, never trusting extra payload."""
        clean = {k: entry.get(k) for k in ENTRY_FIELDS if entry.get(k) is not None}
        rec = {"ts": now, "account_id": account_id, "realm": realm, "action": action,
               "entry_id": clean.get("id") or entry.get("entry_id"), "entry": clean}
        with self.lock:
            self._append(self.workspace_path, rec)
            if action == "publish":
                self._append(self.review_path, {**rec, "status": "in_review",
                                                "note": "candidate — never public-active until it clears review"})
        return rec

    def _events_for(self, account_id: str, realm: str) -> list[dict]:
        return [rec for rec in self._rows(self.workspace_path)
                if rec.get("account_id") == account_id and rec.get("realm") == realm]

    def _calls_30d(self, account_id: str, realm: str, now: int) -> int:
        # Counts the LIVE generation only (post-rotation the meter is an honest floor — see
        # _rotate_calls_locked; the rotation bound is far above the free-tier cap anyway).
        cutoff = now - CALL_WINDOW_SECONDS
        return sum(1 for rec in self._rows(self.calls_path)
                   if (rec.get("account_id") == account_id and rec.get("realm") == realm
                       and int(rec.get("ts", 0)) >= cutoff))

    @staticmethod
    def _ago(ts: int, now: int) -> str:
        d = max(0, now - int(ts))
        if d < 60:
            return "just now"
        if d < 3600:
            return f"{d // 60}m ago"
        if d < 86400:
            return f"{d // 3600}h ago"
        return f"{d // 86400}d ago"

    def workspace(self, account_id: str, realm: str, now: int) -> dict:
        """The real dashboard summary — replayed from the append-only log for this account+realm."""
        events = self._events_for(account_id, realm)
        installed: dict[str, dict] = {}
        published = 0
        for rec in events:
            act, eid, entry = rec.get("action"), rec.get("entry_id"), rec.get("entry") or {}
            if act == "install" and eid:
                installed[eid] = entry
            elif act == "uninstall" and eid:
                installed.pop(eid, None)
            elif act == "publish":
                published += 1
        inst_list = list(installed.values())
        scores = [float(e["score"]) for e in inst_list if str(e.get("score", "")).replace(".", "", 1).isdigit()]
        avg_eval = round(sum(scores) / len(scores), 1) if scores else None
        calls = self._calls_30d(account_id, realm, now)

        icon = {"install": "⬡", "uninstall": "⊖", "publish": "↥"}
        verb = {"install": "Installed", "uninstall": "Removed", "publish": "Published"}
        activity = [{"icon": icon.get(r["action"], "•"),
                     "text": f"{verb.get(r['action'], r['action'])} {(r.get('entry') or {}).get('name') or r.get('entry_id') or ''}".strip(),
                     "when": self._ago(r["ts"], now)}
                    for r in sorted(events, key=lambda r: r.get("ts", 0), reverse=True)[:ACTIVITY_LIMIT]]
        if not activity:
            activity = [{"icon": "◷", "text": "No activity yet — install an entry to get started", "when": ""}]

        usage_pct = min(100, round(calls / FREE_TIER_CALL_CAP * 100)) if FREE_TIER_CALL_CAP else 0
        return {
            "ok": True, "realm": realm, "account_id": account_id, "truth_authority": False,
            "stats": [["Installed", len(inst_list)], ["API calls · 30d", calls],
                      ["Published", published], ["Avg eval", f"★ {avg_eval}" if avg_eval is not None else "—"]],
            "installed": inst_list,
            "published_count": published,
            "activity": activity,
            "plan": {"name": "Free", "usagePct": usage_pct, "usageLabel": "API calls used"},
        }

    def submissions(self, account_id: str, realm: str, now: int) -> list[dict]:
        """The account's review-queue submissions (candidates), newest first. A submission stays
        in_review until it clears review — it is NEVER public-active here (discovery ≠ trust)."""
        out = []
        for rec in self._rows(self.review_path):
            if rec.get("account_id") == account_id and rec.get("realm") == realm:
                entry = rec.get("entry") or {}
                out.append({"entry_id": rec.get("entry_id"), "name": entry.get("name") or rec.get("entry_id"),
                            "facet": entry.get("facet"), "ver": entry.get("ver"),
                            "status": rec.get("status", "in_review"), "ts": rec.get("ts"),
                            "when": self._ago(rec.get("ts", now), now)})
        out.sort(key=lambda r: r.get("ts", 0), reverse=True)
        return out

    # ---- roster helper (one replay for both reviewer + admin rosters) --------
    def _replay_roster(self, path: Path, realm: str) -> set[str]:
        """Current members of an append-only grant/revoke roster for a realm (latest action wins)."""
        state: dict[str, str] = {}
        for rec in self._rows(path):
            if rec.get("realm") == realm and rec.get("account_id"):
                state[rec["account_id"]] = rec.get("action")
        return {a for a, act in state.items() if act == "grant"}

    # ---- reviewer roster (granted by an ADMIN or the operator; NEVER self-granted) ----
    def grant_reviewer(self, realm: str, account_id: str, by: str, now: int, reason: str = "") -> None:
        with self.lock:
            self._append(self.reviewers_path, {"ts": now, "realm": realm, "account_id": account_id,
                                               "action": "grant", "by": by, "reason": (reason or "").strip()[:240]})

    def revoke_reviewer(self, realm: str, account_id: str, by: str, now: int, reason: str = "") -> None:
        with self.lock:
            self._append(self.reviewers_path, {"ts": now, "realm": realm, "account_id": account_id,
                                               "action": "revoke", "by": by, "reason": (reason or "").strip()[:240]})

    def list_reviewers(self, realm: str) -> set[str]:
        return self._replay_roster(self.reviewers_path, realm)

    def is_reviewer(self, realm: str, account_id: str) -> bool:
        return bool(account_id) and account_id in self.list_reviewers(realm)

    # ---- admin roster (operator-bootstrapped ONLY; admins grant reviewers) ----
    def grant_admin(self, realm: str, account_id: str, by: str, now: int) -> None:
        with self.lock:
            self._append(self.admins_path, {"ts": now, "realm": realm, "account_id": account_id,
                                            "action": "grant", "by": by})

    def revoke_admin(self, realm: str, account_id: str, by: str, now: int) -> None:
        with self.lock:
            self._append(self.admins_path, {"ts": now, "realm": realm, "account_id": account_id,
                                            "action": "revoke", "by": by})

    def list_admins(self, realm: str) -> set[str]:
        return self._replay_roster(self.admins_path, realm) | {a for (r, a) in self._env_admins if r == realm}

    def is_admin(self, realm: str, account_id: str) -> bool:
        return bool(account_id) and account_id in self.list_admins(realm)

    def recent_contributors(self, realm: str, now: int, limit: int = 12) -> list[dict]:
        """Distinct accounts who've submitted candidates in this realm (the people most likely to be
        made reviewers) — so an admin can grant active contributors without copy-pasting account ids."""
        agg: dict[str, dict] = {}
        for rec in self._rows(self.review_path):
            if rec.get("realm") == realm and rec.get("account_id"):
                a = agg.setdefault(rec["account_id"], {"account_id": rec["account_id"], "submissions": 0, "ts": 0})
                a["submissions"] += 1
                a["ts"] = max(a["ts"], rec.get("ts", 0))
        out = sorted(agg.values(), key=lambda r: r["ts"], reverse=True)[:limit]
        for r in out:
            r["last_when"] = self._ago(r["ts"], now)
        return out

    # ---- review queue + decisions (the ONLY path candidate → public-active) --
    def _latest_submissions(self, realm: str) -> dict[str, dict]:
        subs: dict[str, dict] = {}
        for rec in self._rows(self.review_path):
            if rec.get("realm") == realm and rec.get("entry_id"):
                subs[rec["entry_id"]] = rec       # latest submission per entry wins
        return subs

    def _latest_decisions(self, realm: str) -> dict[str, dict]:
        dec: dict[str, dict] = {}
        for rec in self._rows(self.decisions_path):
            if rec.get("realm") == realm and rec.get("entry_id"):
                dec[rec["entry_id"]] = rec        # latest decision per entry wins
        return dec

    def review_queue(self, realm: str, now: int) -> list[dict]:
        """Candidates awaiting a decision (no terminal approve/reject yet), oldest first (FIFO)."""
        subs, dec = self._latest_submissions(realm), self._latest_decisions(realm)
        out = []
        for eid, rec in subs.items():
            latest = dec.get(eid)
            if latest and latest.get("decision") in ("approve", "reject"):
                continue
            entry = rec.get("entry") or {}
            out.append({"entry_id": eid, "name": entry.get("name") or eid, "facet": entry.get("facet"),
                        "ver": entry.get("ver"), "desc": entry.get("desc"),
                        "submitter": rec.get("account_id"), "submitted_when": self._ago(rec.get("ts", now), now),
                        "ts": rec.get("ts")})
        out.sort(key=lambda r: r.get("ts", 0))
        return out

    def decide(self, realm: str, entry_id: str, reviewer_account: str, decision: str,
               reason: str | None, now: int, score: str | None = None) -> dict:
        """Record a reviewer decision (append-only). approve → promotes the candidate to the catalog;
        reject/revoke are PRESERVED, never deleting the candidate (lossless; revoke = rollback target).
        Separation of duties: a reviewer may NOT decide on a candidate they submitted."""
        if decision not in REVIEW_DECISIONS:
            raise ValueError(f"decision must be one of {REVIEW_DECISIONS}")
        sub = self._latest_submissions(realm).get(entry_id)
        if not sub:
            raise KeyError("no such candidate in this realm")
        submitter = sub.get("account_id")
        if submitter and submitter == reviewer_account:
            raise SelfReviewError("a reviewer cannot review their own submission (separation of duties)")
        rec = {"ts": now, "realm": realm, "entry_id": entry_id, "decision": decision,
               "reviewer_account": reviewer_account, "reason": (reason or "").strip()[:400],
               "submitter_account": submitter, "submit_ts": sub.get("ts"), "entry": sub.get("entry") or {}}
        if score:
            rec["score"] = str(score)
        with self.lock:
            self._append(self.decisions_path, rec)
        return rec

    def promoted(self, realm: str) -> list[dict]:
        """The active community catalog = candidates whose LATEST decision is 'approve'. Each carries
        provenance lineage (submitter + reviewer + timestamps + reason) — governance, not just data."""
        out = []
        for eid, rec in self._latest_decisions(realm).items():
            if rec.get("decision") != "approve":
                continue
            entry = {k: v for k, v in (rec.get("entry") or {}).items() if k in ENTRY_FIELDS}
            entry["id"] = eid
            entry.setdefault("name", eid)
            entry["score"] = rec.get("score") or entry.get("score") or "—"   # reviewer eval > submitted > none
            entry.setdefault("by", "@community")
            entry.setdefault("installs", "0")
            entry["provenance"] = {"origin": "community-reviewed", "submitter": rec.get("submitter_account"),
                                   "reviewer": rec.get("reviewer_account"), "approved_ts": rec.get("ts"),
                                   "submit_ts": rec.get("submit_ts"), "reason": rec.get("reason")}
            out.append(entry)
        return out

    def audit(self, account_id: str, realm: str, now: int, limit: int = 30) -> list[dict]:
        """The account's REAL registry activity — its workspace actions + any review decisions it made,
        newest first, shaped for the audit log. Every row is a recorded event (no fabrication)."""
        rows = []
        ws_map = {"install": ("Installed", "⬡", "workspace:install"),
                  "uninstall": ("Removed", "⊖", "workspace:uninstall"),
                  "publish": ("Submitted for review", "↥", "registry:submit")}
        for rec in self._events_for(account_id, realm):
            ev = ws_map.get(rec.get("action"), (rec.get("action"), "•", "registry"))
            rows.append({"ts": rec.get("ts", 0), "ev": ev[0], "icon": ev[1],
                         "target": (rec.get("entry") or {}).get("name") or rec.get("entry_id") or "",
                         "policy": ev[2], "ok": True})
        dec_map = {"approve": ("Promoted to catalog", "✓", "review:approve", True),
                   "reject": ("Rejected candidate", "⊘", "review:reject", False),
                   "revoke": ("Revoked promotion", "↩", "review:revoke", True)}
        for rec in self._rows(self.decisions_path):
            if rec.get("realm") == realm and rec.get("reviewer_account") == account_id:
                ev = dec_map.get(rec.get("decision"), (rec.get("decision"), "•", "review", True))
                rows.append({"ts": rec.get("ts", 0), "ev": ev[0], "icon": ev[1],
                             "target": (rec.get("entry") or {}).get("name") or rec.get("entry_id"),
                             "policy": ev[2], "ok": ev[3]})
        rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
        for r in rows:
            r["t"] = self._ago(r["ts"], now)
        return rows[:limit]


# ---------------------------------------------------------------------------
# HTTP surface
# ---------------------------------------------------------------------------
class _Handler(BaseHTTPRequestHandler):
    store: RegistryStore = None       # type: ignore[assignment]
    validator: SessionValidator = None  # type: ignore[assignment]

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")   # local preview only
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AIDR-Request-Id")
        self.end_headers()
        self.wfile.write(body)

    def _now(self) -> int:
        return int(time.time())

    def _auth(self, realm: str, session_id: str, method: str, path: str):
        """Resolve the session to an account id and log the authed call. Returns account_id or None."""
        account_id = self.validator.resolve(realm, session_id)
        if account_id:
            self.store.log_call(account_id, realm, method, path, self._now())
        return account_id

    # ---- routing -------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        parts = urlsplit(self.path)
        path = parts.path
        qs = parse_qs(parts.query)
        if path == "/healthz":
            return self._send(200, {"ok": True, "service": SERVICE_ID})
        if path == "/readyz":
            return self._send(200, {"ready": True, "hubs": len(self.store.catalog)})
        if path == "/version":
            return self._send(200, {"service": SERVICE_ID, "version": VERSION})
        if path == "/api/status":
            return self._send(200, {"ok": True, "service": SERVICE_ID, "hubs": len(self.store.catalog),
                                    "entries": sum(len(v) for v in self.store.catalog.values()),
                                    "truth_authority": False, "note": "projection + per-account workspace; never truth"})
        if path == "/api/openhub/catalog":
            return self._send(200, {"hubs": self.store.catalog_counts()})

        seg = path.strip("/").split("/")     # api/openhub/<realm>/<action>...
        if len(seg) >= 4 and seg[0] == "api" and seg[1] == "openhub":
            realm, action = seg[2], seg[3]
            if action == "search":
                return self._send(200, {"realm": realm, "entries": self.store.search(realm, (qs.get("q") or [""])[0])})
            if action == "entry" and len(seg) >= 5:
                e = self.store.entry(realm, seg[4])
                return self._send(200 if e else 404, e or {"error": "no such entry"})
            if action in ("workspace", "submissions", "audit"):
                account_id = self._auth(realm, (qs.get("session_id") or [""])[0], "GET", path)
                if not account_id:
                    return self._send(401, {"ok": False, "error": "a valid realm session is required"})
                if action == "submissions":
                    return self._send(200, {"realm": realm,
                                            "submissions": self.store.submissions(account_id, realm, self._now())})
                if action == "audit":
                    return self._send(200, {"realm": realm, "rows": self.store.audit(account_id, realm, self._now())})
                return self._send(200, self.store.workspace(account_id, realm, self._now()))
            if action == "review" and len(seg) >= 5:
                account_id = self._auth(realm, (qs.get("session_id") or [""])[0], "GET", path)
                if not account_id:
                    return self._send(401, {"ok": False, "error": "a valid realm session is required"})
                if seg[4] == "status":                              # any signed-in user may check (→ bool)
                    return self._send(200, {"realm": realm, "reviewer": self.store.is_reviewer(realm, account_id)})
                if seg[4] == "queue":                               # the pending queue is reviewer-only
                    if not self.store.is_reviewer(realm, account_id):
                        return self._send(403, {"ok": False, "error": "reviewer access required"})
                    return self._send(200, {"realm": realm, "queue": self.store.review_queue(realm, self._now())})
            if action == "admin" and len(seg) >= 5:
                account_id = self._auth(realm, (qs.get("session_id") or [""])[0], "GET", path)
                if not account_id:
                    return self._send(401, {"ok": False, "error": "a valid realm session is required"})
                if seg[4] == "status":                              # any signed-in user may check (→ bool)
                    return self._send(200, {"realm": realm, "admin": self.store.is_admin(realm, account_id)})
                if seg[4] == "reviewers":                           # the roster view is admin-only
                    if not self.store.is_admin(realm, account_id):
                        return self._send(403, {"ok": False, "error": "admin access required"})
                    return self._send(200, {"realm": realm,
                                            "reviewers": sorted(self.store.list_reviewers(realm)),
                                            "contributors": self.store.recent_contributors(realm, self._now())})
        return self._send(404, {"error": "unknown path"})

    def _read_json(self):
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def _handle_decide(self, realm: str, path: str) -> None:
        """POST /api/openhub/<realm>/review/decide — the promotion gate (reviewer-only)."""
        try:
            payload = self._read_json()
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON"})
        account_id = self._auth(realm, str(payload.get("session_id") or ""), "POST", path)
        if not account_id:
            return self._send(401, {"ok": False, "error": "a valid realm session is required"})
        if not self.store.is_reviewer(realm, account_id):
            return self._send(403, {"ok": False, "error": "reviewer access required"})
        decision = str(payload.get("decision") or "")
        if decision not in REVIEW_DECISIONS:
            return self._send(400, {"ok": False, "error": f"decision must be one of {REVIEW_DECISIONS}"})
        try:
            rec = self.store.decide(realm, str(payload.get("entry_id") or ""), account_id, decision,
                                    payload.get("reason"), self._now(), score=payload.get("score"))
        except SelfReviewError as e:
            return self._send(403, {"ok": False, "error": str(e)})
        except KeyError:
            return self._send(404, {"ok": False, "error": "no such candidate in this realm"})
        promoted = decision == "approve"
        return self._send(202, {"ok": True, "decision": decision, "entry_id": rec["entry_id"], "promoted": promoted,
                                "note": ("promoted to the catalog — now public-active, with lineage to the "
                                         "submitter + reviewer" if promoted else
                                         "recorded; the candidate is preserved (lossless), not deleted")})

    def _handle_admin_reviewer(self, realm: str, op: str, path: str) -> None:
        """POST /api/openhub/<realm>/admin/reviewers/<grant|revoke> — admin-only reviewer management.
        The acting ADMIN's account id is recorded as the grantor (audit). Admins are never created
        here — only reviewers — so the console can't escalate privilege past the operator root."""
        try:
            payload = self._read_json()
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON"})
        account_id = self._auth(realm, str(payload.get("session_id") or ""), "POST", path)
        if not account_id:
            return self._send(401, {"ok": False, "error": "a valid realm session is required"})
        if not self.store.is_admin(realm, account_id):
            return self._send(403, {"ok": False, "error": "admin access required"})
        target = str(payload.get("account_id") or "").strip()
        if not target:
            return self._send(400, {"ok": False, "error": "account_id is required"})
        reason = payload.get("reason")
        if op == "grant":
            self.store.grant_reviewer(realm, target, by=account_id, now=self._now(), reason=reason or "")
        else:
            self.store.revoke_reviewer(realm, target, by=account_id, now=self._now(), reason=reason or "")
        return self._send(202, {"ok": True, "op": op, "account_id": target,
                                "reviewers": sorted(self.store.list_reviewers(realm))})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        seg = path.strip("/").split("/")
        if (len(seg) == 5 and seg[0] == "api" and seg[1] == "openhub"
                and seg[3] == "review" and seg[4] == "decide"):
            return self._handle_decide(seg[2], path)
        if (len(seg) == 6 and seg[0] == "api" and seg[1] == "openhub"
                and seg[3] == "admin" and seg[4] == "reviewers" and seg[5] in ("grant", "revoke")):
            return self._handle_admin_reviewer(seg[2], seg[5], path)
        if not (len(seg) == 4 and seg[0] == "api" and seg[1] == "openhub"):
            return self._send(404, {"error": "unknown path"})
        realm, action = seg[2], seg[3]
        if action not in ("install", "uninstall", "submit"):
            return self._send(404, {"error": "unknown action"})
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON"})
        account_id = self._auth(realm, str(payload.get("session_id") or ""), "POST", path)
        if not account_id:
            return self._send(401, {"ok": False, "error": "a valid realm session is required"})
        if action == "uninstall":
            rec = self.store.record(account_id, realm, "uninstall",
                                    {"id": payload.get("entry_id")}, self._now())
        else:
            entry = payload.get("entry") or {}
            if not entry.get("id"):
                return self._send(400, {"ok": False, "error": "entry.id is required"})
            rec = self.store.record(account_id, realm, "publish" if action == "submit" else "install",
                                    entry, self._now())
        out = {"ok": True, "recorded": {"action": rec["action"], "entry_id": rec["entry_id"], "ts": rec["ts"]}}
        if action == "submit":
            out["status"] = "in_review"
            out["note"] = "candidate — appears publicly only after it clears review (discovery ≠ trust)"
        return self._send(202, out)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(200, {"ok": True})

    def log_message(self, fmt, *args):  # the JSONL is the record
        pass


def start_service(port: int = 0, state_dir: Path | None = None, bundle_dir: Path | None = None,
                  validator: SessionValidator | None = None):
    store = RegistryStore(state_dir=state_dir, bundle_dir=bundle_dir)
    handler = type("BoundHandler", (_Handler,), {"store": store, "validator": validator or SessionValidator()})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, name=SERVICE_ID, daemon=True)
    thread.start()
    return server, thread, server.server_address[1], store


_ROSTER_COMMANDS = ("--grant-reviewer", "--revoke-reviewer", "--list-reviewers",
                    "--grant-admin", "--revoke-admin", "--list-admins")


def _roster_cli(args: list[str]) -> int:
    """Operator-only roster management (local, file-based). It writes to the same append-only roster
    the running daemon replays, so a change takes effect live. Reviewer status is also grantable by an
    admin through the in-app console; ADMIN status is operator-ONLY here — the root of trust, never
    set from inside the app. Usage:
      python3 -m scripts.registry_local_service --grant-admin    <realm> <account_id>   (bootstrap)
      python3 -m scripts.registry_local_service --grant-reviewer <realm> <account_id>
      python3 -m scripts.registry_local_service --list-admins | --list-reviewers [<realm>]
    """
    cmd = args[0]
    store = RegistryStore()
    now = int(time.time())
    kind = "admin" if "admin" in cmd else "reviewer"
    path = store.admins_path if kind == "admin" else store.reviewers_path
    lister = store.list_admins if kind == "admin" else store.list_reviewers
    if cmd in ("--list-reviewers", "--list-admins"):
        realm = args[1] if len(args) > 1 else None
        realms = [realm] if realm else sorted({json.loads(l).get("realm")
                  for l in (path.read_text(encoding="utf-8").splitlines() if path.exists() else [])})
        for r in realms:
            print(f"{r} {kind}s: {sorted(lister(r))}")
        return 0
    if len(args) < 3:
        print(f"usage: python3 -m scripts.registry_local_service {cmd} <realm> <account_id>")
        return 2
    realm, account_id = args[1], args[2]
    grant = cmd.startswith("--grant")
    fn = {("admin", True): store.grant_admin, ("admin", False): store.revoke_admin,
          ("reviewer", True): store.grant_reviewer, ("reviewer", False): store.revoke_reviewer}[(kind, grant)]
    fn(realm, account_id, by="operator-cli", now=now)
    print(f"{'granted' if grant else 'revoked'} {kind} {account_id} on realm '{realm}' "
          f"(recorded to {path})")
    return 0


def _self_test() -> int:
    """Offline store proof for the hot-path cache + rotation (the HTTP/service proof stays in
    scripts/check_registry_backend.py): cache serves after writes, a restart (new RegistryStore
    on the same state_dir) rehydrates equal state, rotation preserves the previous generation."""
    import shutil
    import tempfile

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = Path(tempfile.mkdtemp(prefix="registry-selftest-"))
    no_bundle = tmp / "no-bundle"   # nonexistent ⇒ empty catalog (store proof needs no design bundle)
    now = 1_700_000_000
    rotate_at = 5                   # tiny injected bound so rotation is provable in milliseconds
    try:
        sd = tmp / "state"
        store = RegistryStore(state_dir=sd, bundle_dir=no_bundle, rotate_calls_lines=rotate_at)

        # ── 1) append-through: reads reflect writes immediately ─────────────────
        store.record("a1", "r1", "install", {"id": "x1", "name": "X One", "score": "4.0"}, now)
        store.record("a1", "r1", "publish", {"id": "c1", "name": "Cand"}, now + 1)
        store.log_call("a1", "r1", "GET", "/w", now + 2)
        ws = store.workspace("a1", "r1", now + 3)
        stats = dict(ws["stats"])
        ck("cache serves writes immediately (installed/published/calls)",
           stats["Installed"] == 1 and stats["Published"] == 1 and stats["API calls · 30d"] == 1, str(stats))

        # reads are MEMORY-served: blank the durable files; the live store still answers.
        # (Disk stays the durable source for RESTART — restored + proven right below.)
        ws_bytes, call_bytes = store.workspace_path.read_bytes(), store.calls_path.read_bytes()
        store.workspace_path.write_text("", encoding="utf-8")
        store.calls_path.write_text("", encoding="utf-8")
        again = dict(store.workspace("a1", "r1", now + 3)["stats"])
        ck("reads served from memory, not a per-request file re-parse",
           again["Installed"] == 1 and again["API calls · 30d"] == 1, str(again))
        store.workspace_path.write_bytes(ws_bytes)   # restore the durable layer (lossless)
        store.calls_path.write_bytes(call_bytes)

        # review/roster flows ride the same cache (decide reads submissions from memory)
        store.grant_reviewer("r1", "rev1", by="t", now=now + 4)
        store.decide("r1", "c1", "rev1", "approve", "ok", now + 5, score="4.2")
        ck("review flow over the cache promotes the candidate",
           any(e.get("id") == "c1" for e in store.promoted("r1")))

        # ── 2) restart: a NEW store on the same state_dir rehydrates EQUAL state ─
        store2 = RegistryStore(state_dir=sd, bundle_dir=no_bundle, rotate_calls_lines=rotate_at)
        ck("restart rehydrates an equal workspace summary",
           store2.workspace("a1", "r1", now + 6) == store.workspace("a1", "r1", now + 6))
        ck("restart rehydrates submissions + roster + decisions",
           store2.submissions("a1", "r1", now + 6) == store.submissions("a1", "r1", now + 6)
           and store2.is_reviewer("r1", "rev1")
           and store2.audit("rev1", "r1", now + 6) == store.audit("rev1", "r1", now + 6))

        # ── 3) rotation: live → .1 (preserved), counters rebuild from live only ──
        rot_dir = tmp / "rot"
        rs = RegistryStore(state_dir=rot_dir, bundle_dir=no_bundle, rotate_calls_lines=rotate_at)
        for i in range(rotate_at + 2):                      # 5 trigger the rotation, 2 land live
            rs.log_call("a1", "r1", "GET", f"/c{i}", now + i)
        prev = rs.calls_path.with_name(rs.calls_path.name + ".1")
        ck("rotation triggered at the line bound", prev.exists())
        prev_lines = prev.read_text(encoding="utf-8").splitlines()
        live_lines = rs.calls_path.read_text(encoding="utf-8").splitlines()
        ck("previous generation preserved losslessly (rotation never truncates)",
           len(prev_lines) == rotate_at and "/c0" in prev_lines[0], f"{len(prev_lines)} lines")
        ck("live generation holds only the post-rotation tail",
           len(live_lines) == 2 and "/c5" in live_lines[0], f"{len(live_lines)} lines")
        ck("counters rebuild from the live generation only", rs._calls_30d("a1", "r1", now + 9) == 2)
        rs2 = RegistryStore(state_dir=rot_dir, bundle_dir=no_bundle, rotate_calls_lines=rotate_at)
        ck("restart after rotation rehydrates the live generation only",
           rs2._calls_30d("a1", "r1", now + 9) == 2)
        # a second rotation REPLACES .1 (exactly one previous generation — the retention bound)
        for i in range(rotate_at - 2):
            rs.log_call("a1", "r1", "GET", f"/d{i}", now + 10 + i)
        ck("second rotation keeps exactly one previous generation (.1 replaced, no .2)",
           "/d2" in prev.read_text(encoding="utf-8")
           and not prev.with_name(prev.name.replace(".1", ".2")).exists()
           and rs._calls_30d("a1", "r1", now + 20) == 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + ("PASS — registry store self-test: append-through cache serves reads from memory, "
                  "restart rehydrates equal state from the durable JSONL, api_calls rotation keeps "
                  "one preserved previous generation."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--self-test":
        return _self_test()
    if args and args[0] in _ROSTER_COMMANDS:
        return _roster_cli(args)
    port = _registry_port()
    store = RegistryStore()
    handler = type("BoundHandler", (_Handler,), {"store": store, "validator": SessionValidator()})
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")  # 0.0.0.0 only in container deploys
    server = ThreadingHTTPServer((bind_host, port), handler)
    pid_file = REPO_ROOT / ".agent" / "local-services" / f"{SERVICE_ID}.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()), encoding="utf-8")
    entries = sum(len(v) for v in store.catalog.values())
    print(f"{SERVICE_ID} on http://127.0.0.1:{port} — {len(store.catalog)} hubs / {entries} catalog "
          f"entries; identity at {store and SessionValidator().base} (stop by exact pid {os.getpid()})")
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
