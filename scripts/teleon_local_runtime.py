#!/usr/bin/env python3
"""scripts.teleon_local_runtime — the LOCAL Teleon capability runtime (demo-grade, REAL execution).

Teleon's thesis, run honestly on a laptop: a capability ships only after it clears its success
criteria on real examples. This service holds a small set of REAL deterministic capabilities
(pure-Python implementations — no model calls, no network), and a "run" actually EXECUTES the
capability against its example suite right now:

  * every example execution produces a RECEIPT (input/output hashes, pass/fail, duration µs,
    train/holdout split — even example indices are TRAIN, odd are HOLDOUT);
  * the run's score is the real pass-rate; the PROMOTION GATE requires BOTH the train and the
    holdout pass-rates to clear the gate (>= 0.90 → promoted; overall >= 0.70 → candidate;
    below → rolled-back) and the capability's version/status/state update accordingly. The
    self-refine prompt may quote failed TRAIN inputs but NEVER any example's expected output,
    so a model cannot promote by parroting an answer key it saw in its own prompt;
  * everything persists to disk (restart-safe) under dist/local-services-state/teleon-runtime/.

Runs can be ASYNC (opt-in). A suite can issue up to 8 model calls × 120s, and a fronting proxy
(e.g. Fly's) cuts a connection that long — after which a blind UI retry would double-bump the
version. POST {"async": true} therefore persists a PENDING run record and returns
202 {run_id, status:"running"} at once; a background WORKER thread executes the suite and
finalizes the same run_id to a terminal status (promoted | candidate | rolled-back | failed).
Clients poll GET /runs?run_id=… for status. The PLAIN POST (no "async" flag) stays the
SYNCHRONOUS default — execute now, answer 201 with the finished run — because the generated
web/teleon/teleon-live.js client depends on exactly that contract.

Async admission is ONE RUN PER CAPABILITY AT A TIME: while a capability has an async run in
flight, the same account's re-POST gets the SAME running run back (so a proxy-cut client can
retry blind — no second run, no second version bump), and a DIFFERENT account's request is
rejected 409. Concurrency model: a global lock guards only the short read-modify-write of shared
state (caps / runs index / file appends), never the long model calls — so runs of DIFFERENT
capabilities overlap. A PER-CAPABILITY lock serializes one capability's runs end-to-end (async
and queued sync runs of the SAME cap never race its version). An optional idempotency_key on
POST returns the SAME run_id if replayed, even after the run finished. A run left "running" by a
crash is swept to "interrupted" on startup (older than RUNNING_SWEEP_STALE_S) — never stuck.

Mutations are session-gated against the identity service (realm `teleon`), the same pattern as
scripts/registry_local_service.py: the account is resolved server-side; the client never asserts
who it is. Reads are open (local demo plane). Nothing here is "truth" beyond what it really did:
deterministic code ran, receipts recorded. Port lives in architecture/local_service_registry.json.

Endpoints
  GET  /healthz                                  → {ok}
  GET  /api/teleon/<realm>/capabilities          → {capabilities: [...]}
  POST /api/teleon/<realm>/runs                  → 201 {run} — SYNC default: executes NOW, returns the
                                                   finished run (the generated UI's contract; session
                                                   required; optional idempotency_key dedupes replays)
       body {"async": true}                      → 202 {run_id, status:"running", run} immediately; the
                                                   suite runs on a worker thread. One run per capability
                                                   at a time: the same account's re-POST returns the
                                                   running run (idempotent retry), another account → 409
  GET  /api/teleon/<realm>/runs?session_id=…     → {runs: [...]} (the account's, latest status)
  GET  /api/teleon/<realm>/runs?run_id=…         → {run} (one run's current status — for polling)
  GET  /api/teleon/<realm>/evidence?run_id=…     → {receipts: [...]}

Offline, stdlib-only.  --self-test exercises the whole lifecycle in-process, plus the HTTP
contract (201 sync / 202 async / 409 busy) over an ephemeral loopback server.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # direct-file run → repo importable
from scripts.model_routes import resolve_route  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SERVICE_REGISTRY = REPO / "architecture" / "local_service_registry.json"
IDENTITY_REGISTRY = REPO / "architecture" / "identity_realm_registry.json"
STATE_DIR = REPO / "dist" / "local-services-state" / "teleon-runtime"
SERVICE_ID = "teleon_local_runtime"

PROMOTE_AT = 0.90   # the gate: promoted at or above this real pass-rate
CANDIDATE_AT = 0.70  # below the gate but workable → candidate; below this → rolled-back

# On promotion the capability is COMPILED to a deployable runtime unit and registered (the
# loop's deploy arc: gate → compile → registry → the Machines runner launches it). fly_machine
# is the default exec target on our host; the compiler also emits k8s_job/local_process — the
# unit stays portable, only the launcher differs. Compilation is a downstream deploy step: a
# compile/registry hiccup is recorded honestly on the run, never failing the promotion itself.
AUTO_COMPILE_EXEC_TARGET = "fly_machine"


def _compiled_units_path() -> Path:
    """The compiled-unit registry log — beside the runtime state it describes (the canonical
    dist/local-services-state/teleon-compiler/ in production; follows a patched STATE_DIR in
    tests, so a self-test never writes to the real registry)."""
    return STATE_DIR.parent / "teleon-compiler" / "compiled-units.jsonl"


# ZERO-OP LAUNCH (co-resident, OPT-IN): when OH_TELEON_AUTO_LAUNCH=1 AND FLY_API_TOKEN is set,
# main() runs a background thread that hands every newly-registered ACTIVE compiled unit to the
# Machines runner — the "promote → compile → register → LAUNCH, self-running" path with zero
# operator steps. OFF by default (the launch trigger stays explicit until the owner provisions
# Fly) and a no-op without a token; the runner shares THIS app's registry volume (co-resident).
AUTO_LAUNCH_ENV = "OH_TELEON_AUTO_LAUNCH"
AUTO_LAUNCH_POLL_SECONDS = 30  # match the runner's --watch cadence; the deploy lag for a promotion

# Anti answer-key-gaming split (see Runtime._refined_instruction): every capability's examples
# are deterministically split by index parity — even indices are TRAIN (their INPUTS may be
# quoted in the self-refine prompt), odd indices are HOLDOUT (never shown in ANY prompt). The
# expected OUTPUT text of any example, train or holdout, never enters a prompt at all.
TRAIN_PARITY = 0              # example index i is TRAIN iff i % 2 == TRAIN_PARITY, else HOLDOUT
TRAIN_SPLIT = "train"         # split labels on receipts — single definition, used everywhere
HOLDOUT_SPLIT = "holdout"
REFINE_SHOWN_MAX = 3          # max failed TRAIN inputs quoted in one refine prompt (prompt-size cap)
GATE_BASIS = "train+holdout"  # promotion requires BOTH split pass-rates ≥ PROMOTE_AT on the full suite
DETERMINISTIC_GATE_NOTE = "deterministic reference run — model not exercised"
RATE_DECIMALS = 2             # display rounding for scores/pass-rates; receipts keep exact pass/fail

# --- async run lifecycle -----------------------------------------------------
# A run is created PENDING (status RUNNING) at POST time, then a worker thread executes the suite
# and finalizes it to one TERMINAL status. These are the only values GET /runs ever reports.
STATUS_RUNNING = "running"            # persisted at enqueue; worker not finished yet
STATUS_INTERRUPTED = "interrupted"    # a RUNNING run a restart abandoned — swept on startup, never stuck
STATUS_FAILED = "failed"             # the worker raised before reaching the gate (honest, not silent)
# decision values double as terminal statuses: promoted | candidate | rolled-back (see execute()).
TERMINAL_STATUSES = ("promoted", "candidate", "rolled-back", STATUS_FAILED, STATUS_INTERRUPTED)
# A run still "running" longer than this when the process (re)starts was abandoned by a crash/restart
# (the worker thread does not survive a process exit) → sweep it to interrupted. Generous vs. the
# worst-case suite cost (≤ 8 model calls × ~120s ≈ 16 min) so a genuinely in-flight run is never
# mislabelled across a same-process check; only a fresh process start sweeps.
RUNNING_SWEEP_STALE_S = 30 * 60       # 30 minutes (> worst-case suite wall-clock), unit: seconds


def _example_split(index: int) -> str:
    """Deterministic split: even example indices are TRAIN, odd are HOLDOUT (never prompted)."""
    return TRAIN_SPLIT if index % 2 == TRAIN_PARITY else HOLDOUT_SPLIT


def _registry_port(service_id: str) -> int:
    for svc in json.loads(SERVICE_REGISTRY.read_text(encoding="utf-8"))["services"]:
        if svc.get("service_id") == service_id and svc.get("port"):
            return int(svc["port"])
    raise SystemExit(f"FATAL: {service_id} not declared in {SERVICE_REGISTRY}")


def _identity_port() -> int:
    return int(json.loads(IDENTITY_REGISTRY.read_text(encoding="utf-8"))["defaults"]["port"])


# ---------------------------------------------------------------------------
# the REAL deterministic capabilities (pure functions + example suites)
# ---------------------------------------------------------------------------

def _normalize_dates(text: str) -> str:
    """US-style and written dates → ISO yyyy-mm-dd (deterministic rules)."""
    months = {m: i + 1 for i, m in enumerate(
        ["january", "february", "march", "april", "may", "june", "july",
         "august", "september", "october", "november", "december"])}

    def mdy(m: re.Match) -> str:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"

    def written(m: re.Match) -> str:
        return f"{int(m.group(3)):04d}-{months[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"

    out = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", mdy, text)
    out = re.sub(r"\b([A-Za-z]+) (\d{1,2}), (\d{4})\b",
                 lambda m: written(m) if m.group(1).lower() in months else m.group(0), out)
    return out


def _redact_pii(text: str) -> str:
    out = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}", "[email]", text)
    out = re.sub(r"(?<!\d)(?:\+?1[ .\-]?)?\(?\d{3}\)?[ .\-]?\d{3}[ .\-]?\d{4}(?!\d)", "[phone]", out)
    return out


def _json_guard(text: str) -> str:
    """Parse JSON; if it fails, apply one deterministic repair (trailing commas) and re-parse.
    Returns canonical compact JSON or the literal string INVALID."""
    for candidate in (text, re.sub(r",\s*([}\]])", r"\1", text)):
        try:
            return json.dumps(json.loads(candidate), sort_keys=True, separators=(",", ":"))
        except Exception:
            continue
    return "INVALID"


def _cite_statute(text: str) -> str:
    """Normalize US statute citations '12 USC 85' / '15 u.s.c. 1692e' → '12 U.S.C. § 85'."""
    return re.sub(r"\b(\d+)\s*U\.?S\.?C\.?\s*(?:§\s*)?(\d+[a-z]?)\b", r"\1 U.S.C. § \2", text,
                  flags=re.IGNORECASE)


CAPABILITIES = {
    "cap-dates": {
        "name": "Date normalizer",
        "purpose": "Rewrite every date in the text to ISO 8601 (yyyy-mm-dd), handling US numeric (3/14/2026) and written (March 20, 2026) forms; leave everything else untouched.",
        "criteria": ["ISO 8601 out", "US + written formats", "deterministic"],
        "impl": _normalize_dates,
        "examples": [
            ("Filed 3/14/2026 and heard March 20, 2026.", "Filed 2026-03-14 and heard 2026-03-20."),
            ("Due 12/1/2025.", "Due 2025-12-01."),
            ("From July 4, 1999 to 7/5/1999.", "From 1999-07-04 to 1999-07-05."),
            ("No dates here.", "No dates here."),
        ],
    },
    "cap-redact": {
        "name": "PII redactor",
        "purpose": "Replace every email address with [email] and every phone number (any common US form, with or without +1/parentheses) with [phone]; leave all other text exactly as it is.",
        "criteria": ["emails masked", "phones masked", "exact otherwise"],
        "impl": _redact_pii,
        "examples": [
            ("Mail ada@example.com or call 415-555-0143.", "Mail [email] or call [phone]."),
            ("Reach +1 (212) 555-0100 now.", "Reach [phone] now."),
            ("Nothing sensitive.", "Nothing sensitive."),
            ("Two: a@b.co and c@d.org.", "Two: [email] and [email]."),
        ],
    },
    "cap-json-guard": {
        "name": "JSON schema guard",
        "purpose": "Parse the input as JSON (repairing at most a trailing comma); output the canonical compact form with keys sorted alphabetically and no spaces; if it cannot parse, output exactly INVALID.",
        "criteria": ["parses or repairs once", "canonical output", "flags invalid"],
        "impl": _json_guard,
        "examples": [
            ('{"b":2,"a":1}', '{"a":1,"b":2}'),
            ('{"a":1,}', '{"a":1}'),
            ('[1,2,3,]', "[1,2,3]"),
            ("not json", "INVALID"),
        ],
    },
    "cap-cite": {
        "name": "Citation formatter",
        "purpose": "Rewrite every US statute citation to the canonical form 'TITLE U.S.C. § SECTION' (e.g. '12 USC 85' or '15 u.s.c. 1692e' become '12 U.S.C. § 85' and '15 U.S.C. § 1692e'); leave already-canonical citations and all other text unchanged.",
        "criteria": ["U.S.C. canonical form", "section glyph", "idempotent"],
        "impl": _cite_statute,
        "examples": [
            ("See 12 USC 85.", "See 12 U.S.C. § 85."),
            ("Under 15 u.s.c. 1692e.", "Under 15 U.S.C. § 1692e."),
            ("Already 12 U.S.C. § 85.", "Already 12 U.S.C. § 85."),
            ("No citation.", "No citation."),
        ],
    },
}


# ---------------------------------------------------------------------------
# state + execution
# ---------------------------------------------------------------------------

def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


class CapabilityBusyError(Exception):
    """An ASYNC run was requested for a capability that already has one in flight, by a DIFFERENT
    account. (The SAME account gets the running run back instead — the idempotent retry path; see
    Runtime.submit_run.) The HTTP layer answers 409."""

    def __init__(self, cap_id: str, run_id: str) -> None:
        super().__init__(f"capability {cap_id} already has a run in flight ({run_id}); "
                         "one run per capability at a time — poll it or retry after it finishes")
        self.cap_id = cap_id
        self.run_id = run_id


class Runtime:
    def __init__(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.caps_path = STATE_DIR / "capabilities.json"
        self.runs_path = STATE_DIR / "runs.jsonl"
        self.receipts_path = STATE_DIR / "receipts.jsonl"
        # GLOBAL lock: guards only the SHORT read-modify-write of shared state (caps map, the runs
        # index, the append-only file writes) — NOT the long model calls. ThreadingHTTPServer
        # dispatches handlers on parallel threads and a background worker per run also touches this
        # state, so every such window serializes here, but two runs' model calls still overlap.
        self._lock = threading.Lock()
        # PER-CAPABILITY locks: a run holds its cap's lock for its whole lifetime (enqueue→finalize)
        # so two runs of the SAME capability serialize on its version, while DIFFERENT caps run in
        # parallel. Created lazily under _lock; never the global lock for the duration of model calls.
        self._cap_locks: dict[str, threading.Lock] = {}
        # idempotency_key → run_id, so a replayed POST returns the same run (no double version bump).
        self._idem: dict[str, str] = {}
        # ASYNC admission state: capability_id → its ONE in-flight async run_id (one run per
        # capability at a time). Registered at enqueue, cleared by the worker's finally. The same
        # account's re-POST gets the running run back (idempotent retry — a proxy-cut client can
        # retry blind without double-bumping); a DIFFERENT account raises CapabilityBusyError
        # (HTTP 409). Synchronous runs never register here — they keep their original
        # queue-on-the-cap-lock behavior. In-memory on purpose: workers don't survive a process
        # exit, so a fresh process has no in-flight runs (the startup sweep handles their records).
        self._inflight_by_cap: dict[str, str] = {}
        if self.caps_path.exists():
            self.caps = json.loads(self.caps_path.read_text(encoding="utf-8"))
        else:
            self.caps = {cid: {"id": cid, "name": c["name"], "criteria": c["criteria"],
                               "version": 1, "status": "candidate", "last_score": None,
                               "examples": len(c["examples"])}
                         for cid, c in CAPABILITIES.items()}
            self._save_caps()
        # runs.jsonl is an append-only EVENT log: a run_id appears once at enqueue (status running)
        # and again at finalize (terminal). Fold to latest-line-wins so self.runs is the live view.
        self.run_index: dict[str, dict] = {}
        self.runs: list[dict] = []
        if self.runs_path.exists():
            for line in self.runs_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                rid = rec["run_id"]
                if rid in self.run_index:
                    self.run_index[rid].update(rec)  # later line wins (e.g. running → terminal)
                else:
                    self.run_index[rid] = rec
                    self.runs.append(rec)              # ordered list aliases the index dicts
            for rid, key in ((r["run_id"], r.get("idempotency_key")) for r in self.runs):
                if key:
                    self._idem[key] = rid
        self._sweep_interrupted_runs()  # restart-safety: no run is left "running" forever

    def _save_caps(self) -> None:
        self.caps_path.write_text(json.dumps(self.caps, indent=1), encoding="utf-8")

    def _cap_lock(self, cap_id: str) -> threading.Lock:
        with self._lock:
            lk = self._cap_locks.get(cap_id)
            if lk is None:
                lk = self._cap_locks[cap_id] = threading.Lock()
            return lk

    def _persist_run(self, run: dict) -> None:
        """Append one run event and refresh the in-memory view. Caller holds self._lock."""
        rid = run["run_id"]
        existing = self.run_index.get(rid)
        if existing is None:
            self.run_index[rid] = run
            self.runs.append(run)
        else:
            existing.update(run)  # mutate in place so self.runs (which aliases it) updates too
        with self.runs_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(run) + "\n")

    def _sweep_interrupted_runs(self) -> None:
        """Startup restart-safety: a run still RUNNING after a process (re)start was abandoned by a
        crash/restart (worker threads don't survive process exit). Any RUNNING row older than
        RUNNING_SWEEP_STALE_S is rewritten to INTERRUPTED, losslessly (a new event line; the
        original enqueue line is preserved). Fresh RUNNING rows from the current process are left
        alone — they belong to live workers."""
        now = int(time.time())
        with self._lock:
            stale = [r for r in self.runs
                     if r.get("status") == STATUS_RUNNING
                     and now - int(r.get("at", now)) >= RUNNING_SWEEP_STALE_S]
            for r in stale:
                self._persist_run({**r, "status": STATUS_INTERRUPTED,
                                   "interrupted_at": now,
                                   "note": "run was RUNNING at process start — abandoned by restart"})

    @staticmethod
    def _instruction(cap_id: str) -> str:
        spec = CAPABILITIES[cap_id]
        return (f"You ARE the capability \"{spec['name']}\". {spec['purpose']} "
                f"Success criteria: {'; '.join(spec['criteria'])}. "
                "Apply the transformation to the user's input and output ONLY the transformed "
                "text — no commentary, no quotes, no code fences, no extra whitespace.")

    @staticmethod
    def _refined_instruction(cap_id: str, base: str, train_fail_inputs: list[str]) -> str:
        """Self-refine prompt — LEAK CONTROL. It may quote failed TRAIN inputs and DESCRIBE what
        a correct output must satisfy (the capability's purpose + criteria), but the expected
        OUTPUT text of ANY example (train or holdout) must never appear in any prompt: the
        holdout split exists so a model that parrots leaked answers cannot clear the gate."""
        spec = CAPABILITIES[cap_id]
        describe = ("a correct output must satisfy every success criterion "
                    f"({'; '.join(spec['criteria'])}) per the stated purpose, with nothing extra")
        if train_fail_inputs:
            shown = "\n".join(f"- {inp!r}" for inp in train_fail_inputs[:REFINE_SHOWN_MAX])
            detail = (f"your previous attempt produced wrong outputs for these inputs — "
                      f"{describe}:\n{shown}")
        else:  # only held-out examples failed; they are never disclosed, even as inputs
            detail = ("your previous attempt failed on held-out examples (their contents are "
                      f"never disclosed); re-read the purpose and apply it exactly — {describe}")
        return base + " IMPORTANT — " + detail

    def _suite(self, cap_id: str, run_id: str, attempt: int, transform) -> tuple[list[dict], int]:
        """Execute one pass over the example suite; the JUDGE (exact match) stays deterministic."""
        receipts, passed = [], 0
        for i, (inp, expected) in enumerate(CAPABILITIES[cap_id]["examples"]):
            t0 = time.perf_counter_ns()
            try:
                out = transform(inp)
            except Exception as exc:  # a real failure is a real failure
                out = f"ERROR: {exc}"
            out = "" if out is None else str(out).strip()
            us = (time.perf_counter_ns() - t0) // 1000
            ok = out == expected
            passed += ok
            receipts.append({"run_id": run_id, "attempt": attempt, "example": i,
                             "split": _example_split(i),
                             "input_sha": _sha(inp), "output_sha": _sha(out),
                             "expected_sha": _sha(expected), "pass": ok, "duration_us": us})
        return receipts, passed

    @staticmethod
    def _split_rates(receipts: list[dict]) -> tuple[float, float]:
        """(train, holdout) pass-rates over ONE attempt's receipts. An empty split fails closed
        (0.0): a gate nobody measured must never read as cleared."""
        rates = []
        for split in (TRAIN_SPLIT, HOLDOUT_SPLIT):
            rows = [r for r in receipts if r["split"] == split]
            rates.append(sum(r["pass"] for r in rows) / len(rows) if rows else 0.0)
        return rates[0], rates[1]

    def submit_run(self, cap_id: str, account_id: str, mode: str = "auto", route=None,
                   idempotency_key: str | None = None, background: bool = True) -> dict:
        """ENQUEUE a run. background=True (the ASYNC path, POST {"async": true}): return the
        PENDING record (status RUNNING) at once and execute the suite on a worker thread.
        background=False (the SYNCHRONOUS path — the server default, and what execute() wraps):
        run inline and return the TERMINAL record. The slow model calls happen OUTSIDE the global
        lock either way; only the short enqueue/finalize windows serialize.

        ASYNC ADMISSION — one run per capability at a time: while cap_id has an async run in
        flight, the SAME account's re-POST returns that running run unchanged (a proxy-cut client
        may retry blind: no second run, no new reservation, the version can never double-bump),
        and a DIFFERENT account's request raises CapabilityBusyError (HTTP 409). Synchronous runs
        skip admission and queue on the capability lock, exactly as before async existed.

        Idempotency: a replayed POST carrying the same idempotency_key returns the SAME run_id
        (and does not reserve a new version) even after the run finished, so a keyed retry can
        never double-bump either.

        Version reservation: the next version is reserved per-capability under that cap's lock so
        two runs of the SAME cap reserve distinct, contiguous versions and never race; DIFFERENT
        caps reserve in parallel. The reserved version is committed to the capability's visible
        state at finalize, after the gate decision."""
        route = route if route is not None else resolve_route()
        # ENQUEUE (fast): reserve the version + persist the pending record under the GLOBAL lock,
        # then return. The POST NEVER blocks on a model call or on another same-cap run's worker.
        with self._lock:
            if idempotency_key and idempotency_key in self._idem:
                return dict(self.run_index[self._idem[idempotency_key]])  # replay → same run
            if background:  # async admission — BEFORE reserving, so a busy cap burns no version
                inflight_id = self._inflight_by_cap.get(cap_id)
                if inflight_id is not None:
                    inflight = self.run_index.get(inflight_id, {})
                    if inflight.get("account_id") == account_id:
                        return dict(inflight)  # same-account retry → the running run, nothing new
                    raise CapabilityBusyError(cap_id, inflight_id)
            state = self.caps[cap_id]
            # Version RESERVATION is a per-cap monotonic high-water, distinct from the COMMITTED
            # version (which only advances at finalize). Reserving under the global lock guarantees
            # two runs of the SAME cap get distinct, contiguous versions and never race; different
            # caps reserve in parallel. A still-running reservation is never re-handed out.
            reserved = max(state["version"], state.get("version_reserved", state["version"])) + 1
            state["version_reserved"] = reserved
            run_id = f"run_{int(time.time() * 1000):x}_v{reserved}_{cap_id}"
            pending = {"run_id": run_id, "capability_id": cap_id,
                       "capability": CAPABILITIES[cap_id]["name"], "account_id": account_id,
                       "status": STATUS_RUNNING, "version": reserved, "mode_requested": mode,
                       "at": int(time.time())}
            if idempotency_key:
                pending["idempotency_key"] = idempotency_key
                self._idem[idempotency_key] = run_id
            if background:  # async: claim the capability's single in-flight slot
                self._inflight_by_cap[cap_id] = run_id
            self._persist_run(pending)
        if not background:  # inline path (sync default + self-test): run now, return terminal
            return self._worker_body(run_id, cap_id, account_id, mode, route, reserved)
        # Snapshot BEFORE starting the worker: pending aliases the live run_index record, and an
        # instant worker could finalize it before this function returns — the 202 must always
        # describe the ENQUEUE event (status "running"), never a race result. Pollers see live state.
        snapshot = dict(pending)
        worker = threading.Thread(
            target=self._worker_body,
            args=(run_id, cap_id, account_id, mode, route, reserved),
            name=f"teleon-run-{run_id}", daemon=True)
        worker.start()
        self._last_worker = worker  # test/observability handle; not load-bearing
        return snapshot

    def _worker_body(self, run_id: str, cap_id: str, account_id: str, mode: str, route,
                     reserved: int) -> dict:
        """Worker: hold THIS capability's lock for the run (so two runs of the SAME cap don't
        interleave their execute/finalize — DIFFERENT caps run in parallel), execute the suite, and
        finalize. The slow model calls happen inside the per-cap lock but OUTSIDE the global lock, so
        cross-cap concurrency is preserved. Version distinctness is already guaranteed by the
        reservation, so submit_run never has to block on this lock.

        The async in-flight slot is freed HERE (finally) — the one funnel every path shares
        (terminal, failed, even an error escaping finalize) — so a capability can never stay
        'busy' after its worker is gone. The pop is conditional on the run_id because sync runs
        never claim the slot and must not free someone else's."""
        try:
            with self._cap_lock(cap_id):
                return self._run_to_completion(run_id, cap_id, account_id, mode, route, reserved)
        finally:
            with self._lock:
                if self._inflight_by_cap.get(cap_id) == run_id:
                    del self._inflight_by_cap[cap_id]

    def _run_to_completion(self, run_id: str, cap_id: str, account_id: str, mode: str, route,
                           reserved: int) -> dict:
        """REALLY run the capability suite and apply the promotion gate, then FINALIZE the run.

        mode 'model' (the product path): the MODEL performs the capability per example via the
        provider-neutral chat route; one self-refine round when the gate isn't cleared, both
        attempts receipted (lossless). mode 'deterministic': the seeded reference implementation
        (the honest fallback when no model route is reachable — labeled, never disguised).
        The gate itself is deterministic on purpose: evidence judges, models build.

        The model calls below run WITHOUT the global lock (so different caps overlap); only the
        short finalize window — append receipts, commit the reserved version, rewrite the run from
        RUNNING to its terminal status — takes self._lock.

        GATE BASIS (train+holdout): the suite always runs in FULL, but promotion requires the TRAIN
        and the HOLDOUT pass-rates to BOTH clear PROMOTE_AT. The refine prompt may quote failed
        TRAIN inputs, never any expected output (see _refined_instruction), so a model cannot
        promote by copying an answer key."""
        spec = CAPABILITIES[cap_id]
        try:
            use_model = mode in ("model", "auto") and route.health()
            attempts = 0
            model_note = None
            if use_model:
                instruction = self._instruction(cap_id)
                receipts, passed = self._suite(
                    cap_id, run_id, 1,
                    lambda inp: route.complete(instruction, inp, max_tokens=300, temperature=0.0))
                attempts = 1
                train_rate, hold_rate = self._split_rates(receipts)
                if min(train_rate, hold_rate) < PROMOTE_AT:  # one self-refine round on real failures
                    train_fail_inputs = [spec["examples"][r["example"]][0] for r in receipts
                                         if not r["pass"] and r["split"] == TRAIN_SPLIT]
                    refined = self._refined_instruction(cap_id, instruction, train_fail_inputs)
                    receipts2, passed2 = self._suite(
                        cap_id, run_id, 2,
                        lambda inp: route.complete(refined, inp, max_tokens=300, temperature=0.0))
                    attempts = 2
                    train_rate2, hold_rate2 = self._split_rates(receipts2)
                    # keep the gate-better attempt's score (ties → attempt 2); ALL receipts persist
                    if (passed2, min(train_rate2, hold_rate2)) >= (passed, min(train_rate, hold_rate)):
                        passed, train_rate, hold_rate = passed2, train_rate2, hold_rate2
                    receipts = receipts + receipts2
                executed_mode, model_id = "model", route.model_id
            else:
                receipts, passed = self._suite(cap_id, run_id, 1, spec["impl"])
                attempts = 1
                train_rate, hold_rate = self._split_rates(receipts)
                executed_mode, model_id = "deterministic", None
                if mode == "model":
                    model_note = "model mode requested but no route reachable — ran the reference implementation instead"
        except Exception as exc:  # a worker crash must surface as FAILED, never leave it RUNNING
            return self._finalize_failed(run_id, cap_id, reserved, exc)

        total = len(spec["examples"])
        score = round(passed / total, RATE_DECIMALS)
        # promotion needs BOTH splits ≥ PROMOTE_AT: even a fully leaked prompt could only game what
        # the prompt contains, never the holdout. Lower tiers stay on the overall score.
        decision = ("promoted" if train_rate >= PROMOTE_AT and hold_rate >= PROMOTE_AT else
                    "candidate" if score >= CANDIDATE_AT else "rolled-back")
        run = {"run_id": run_id, "capability_id": cap_id, "capability": spec["name"],
               "account_id": account_id, "score": score, "passed": passed, "total": total,
               "train_pass_rate": round(train_rate, RATE_DECIMALS),
               "holdout_pass_rate": round(hold_rate, RATE_DECIMALS),
               # literal honesty field: no example's expected output entered any prompt —
               # guaranteed by _refined_instruction, enforced by the parrot regression test
               "holdout_contaminated": False,
               "gate_basis": GATE_BASIS,
               # decision is the terminal STATUS; "decision" is kept for back-compat with readers
               "decision": decision, "status": decision, "version": reserved,
               "at": int(time.time()),
               "mode": executed_mode, "model_id": model_id, "attempts": attempts,
               "duration_us": sum(r["duration_us"] for r in receipts)}
        if executed_mode == "deterministic":
            run["gate_note"] = DETERMINISTIC_GATE_NOTE  # honest provenance: gate cleared by code
        if model_note:
            run["note"] = model_note
        for r in receipts:  # every receipt carries the run's gate evidence (self-contained audit rows)
            r["train_pass_rate"] = run["train_pass_rate"]
            r["holdout_pass_rate"] = run["holdout_pass_rate"]
            r["holdout_contaminated"] = False
        with self._lock:  # short finalize window: commit version + status, append receipts + run
            state = self.caps[cap_id]
            state["version"] = max(state["version"], reserved)  # commit the reserved version
            state["status"] = decision
            state["last_score"] = score
            state["last_mode"] = executed_mode
            self._save_caps()
            with self.receipts_path.open("a", encoding="utf-8") as fh:
                for r in receipts:
                    fh.write(json.dumps(r) + "\n")
            self._persist_run(run)  # RUNNING → terminal (latest-line-wins)
        # The loop's deploy arc, OUTSIDE the lock (compile/registry do disk I/O): a promotion
        # compiles+registers a deployable runtime unit; a non-promotion records the next-tier
        # escalation decision (advisory — the ladder proposes, nothing auto-dispatches). Both
        # are guarded and re-persist the run with the added field; neither can change the gate.
        if decision == "promoted":
            run["compiled_unit"] = self._auto_compile_and_register(cap_id)
        else:
            run["escalation"] = self._escalation_for_failed(cap_id, run)
        with self._lock:
            self._persist_run(run)
        return run

    def _finalize_failed(self, run_id: str, cap_id: str, reserved: int, exc: Exception) -> dict:
        """Worker error path: finalize the run as FAILED (honest), commit the reserved version so
        numbering stays contiguous, but do NOT change the capability's status/score (a crash is not
        a gate verdict)."""
        run = {"run_id": run_id, "capability_id": cap_id,
               "capability": CAPABILITIES[cap_id]["name"], "version": reserved,
               "status": STATUS_FAILED, "decision": STATUS_FAILED, "at": int(time.time()),
               "error": f"{type(exc).__name__}: {exc}"}
        with self._lock:
            state = self.caps[cap_id]
            state["version"] = max(state["version"], reserved)  # keep version numbering contiguous
            self._save_caps()
            self._persist_run(run)
        return run

    def _auto_compile_and_register(self, cap_id: str) -> dict:
        """Promotion → deployable runtime unit. Reuses the compiler's OWN live-state reader (the
        single source of how a promoted capability becomes compilable) + the compiled-unit
        registry (which owns rollback_target). Returns a small projection on the run; on any
        failure returns {compiled: False, reason} — the promotion already stands."""
        try:
            from src.teleon.compiler import compile_capability, open_registry
            from src.teleon.compiler.fixtures import load_live_capability, fixture_task_spec
            capability, receipt_refs = load_live_capability(cap_id, state_dir=STATE_DIR)
            task_spec = dict(fixture_task_spec())
            task_spec["capability_id"] = cap_id
            # deterministic provenance: the promoting run's epoch handle (no clock here)
            now = capability.get("promoted_at") or f"epoch:{capability.get('version', 0)}"
            unit = compile_capability(capability, task_spec, exec_target=AUTO_COMPILE_EXEC_TARGET,
                                      now=now, receipt_refs=receipt_refs)
            registered = open_registry(log_path=_compiled_units_path()).register(unit)  # stamps rollback_target
            # register() returns the stored RECORD {kind, unit, active, rollback_target, …}
            return {"compiled": True, "unit_id": registered["unit"]["unit_id"],
                    "exec_target": AUTO_COMPILE_EXEC_TARGET,
                    "rollback_target": registered.get("rollback_target") or None}
        except Exception as exc:  # never let a deploy-step hiccup undo a real promotion
            return {"compiled": False, "reason": f"{type(exc).__name__}: {exc}"[:200]}

    def _escalation_for_failed(self, cap_id: str, run: dict) -> dict:
        """Non-promotion → the next-tier escalation decision (advisory; the ladder PROPOSES, this
        records, nothing auto-dispatches). The gate already TRIED the cheap rungs and they didn't
        clear the bar — deterministic_primitive=False (it was tried, didn't cover it) + the run's
        real attempt count as failed-LLM history — so the ladder tiers it up toward bounded
        exploration on its own logic (it reaches T3 once the LLM budget is exhausted)."""
        try:
            from src.teleon.exploration.ladder import escalation_decision, TaskClass
            attempts = max(int(run.get("attempts") or 0), 1)  # ≥1 attempt was made to reach a verdict
            history = [{"kind": "deterministic", "passed": False}]
            history += [{"kind": "llm", "passed": False} for _ in range(attempts)]
            task = TaskClass(task_id=cap_id, task_class="routine", deterministic_primitive=False)
            d = escalation_decision(task, history)
            return {"tier": d.tier, "action": d.action, "rationale": d.rationale,
                    "requires_human_boundary": d.requires_human_boundary,
                    "runtime_ref": d.runtime_ref}
        except Exception as exc:
            return {"escalated": False, "reason": f"{type(exc).__name__}: {exc}"[:200]}

    def launch_pending(self, runner=None, *, receipts_path=None, emit=lambda *_a: None) -> dict:
        """One CO-RESIDENT auto-launch pass: hand every newly-registered ACTIVE compiled unit to
        the Machines runner (same image, same registry volume — the launcher Fly can't reach as a
        separate app). With a runner (real or a fake in tests) → launches; without → an honest
        plan. Delegates to the runner's watch_once (idempotent via the per-launch receipt)."""
        from scripts.deploy.teleon_machines_runner import watch_once, RUNNER_RECEIPTS_PATH
        return watch_once(registry_log=_compiled_units_path(), runner=runner,
                          receipts_path=receipts_path or RUNNER_RECEIPTS_PATH, emit=emit)

    def execute(self, cap_id: str, account_id: str, mode: str = "auto", route=None) -> dict:
        """Synchronous entrypoint: enqueue + run inline, returning the TERMINAL run record. This
        backs the server's DEFAULT plain-POST path (and in-process callers/tests); the opt-in
        {"async": true} path uses submit_run(background=True) and is polled instead."""
        return self.submit_run(cap_id, account_id, mode=mode, route=route, background=False)

    def get_run(self, run_id: str) -> dict | None:
        with self._lock:
            run = self.run_index.get(run_id)
            return dict(run) if run else None

    def receipts_for(self, run_id: str) -> list[dict]:
        with self._lock:  # consistent snapshot: never read a half-appended line mid-finalize
            text = self.receipts_path.read_text(encoding="utf-8") if self.receipts_path.exists() else ""
        return [r for r in map(json.loads, text.splitlines()) if r["run_id"] == run_id]


def _identity_base() -> str:
    """Identity service base. Local default from the realm registry port; AIDR_IDENTITY_BASE
    overrides in container deploys (same convention as registry_local_service)."""
    return os.environ.get("AIDR_IDENTITY_BASE", f"http://127.0.0.1:{_identity_port()}").rstrip("/")


def _validate_session(realm: str, session_id: str) -> str | None:
    """Resolve the account server-side via the identity service (never trust the client)."""
    if not session_id:
        return None
    try:
        req = urllib.request.Request(
            f"{_identity_base()}/api/identity/{realm}/session/validate",
            data=json.dumps({"session_id": session_id}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("account_id") if body.get("valid") else None
    except Exception:
        return None


RT: Runtime = None  # type: ignore


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == "/healthz":
            route = resolve_route()
            return self._send(200, {"ok": True, "service": SERVICE_ID,
                                    "capabilities": len(RT.caps), "runs": len(RT.runs),
                                    "llm": {"model": route.model_id, "reachable": route.health()}})
        m = re.match(r"^/api/teleon/([a-z0-9]+)/(capabilities|runs|evidence)$", parsed.path)
        if not m:
            return self._send(404, {"error": "not found"})
        realm, what = m.group(1), m.group(2)
        if what == "capabilities":
            return self._send(200, {"capabilities": sorted(RT.caps.values(), key=lambda c: c["id"])})
        if what == "runs":
            # ?run_id=… → poll ONE run's current status (open read, like evidence: a run_id is an
            # opaque handle the 202 just handed back). ?session_id=… → the account's run list (gated).
            run_id = (qs.get("run_id") or [""])[0]
            if run_id:
                run = RT.get_run(run_id)
                return self._send(200 if run else 404,
                                  {"run": run} if run else {"error": f"unknown run {run_id}"})
            account = _validate_session(realm, (qs.get("session_id") or [""])[0])
            if not account:
                return self._send(401, {"error": "a valid realm session is required"})
            mine = [r for r in RT.runs if r["account_id"] == account]
            return self._send(200, {"runs": mine[-50:]})
        run_id = (qs.get("run_id") or [""])[0]
        return self._send(200, {"receipts": RT.receipts_for(run_id)})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        m = re.match(r"^/api/teleon/([a-z0-9]+)/runs$", parsed.path)
        if not m:
            return self._send(404, {"error": "not found"})
        realm = m.group(1)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            return self._send(400, {"error": "invalid JSON"})
        account = _validate_session(realm, str(body.get("session_id", "")))
        if not account:
            return self._send(401, {"error": "a valid realm session is required to run a capability"})
        cap_id = str(body.get("capability_id") or "cap-dates")
        if cap_id not in CAPABILITIES:
            return self._send(404, {"error": f"unknown capability {cap_id}"})
        mode = str(body.get("mode") or "auto")
        if mode not in ("auto", "model", "deterministic"):
            return self._send(400, {"error": "mode must be auto | model | deterministic"})
        idem = body.get("idempotency_key")
        idem = str(idem) if idem else None
        if body.get("async"):
            # ASYNC (opt-in): enqueue + return 202 immediately with the PENDING record (status
            # running); the suite (≤ 8 model calls × 120s) executes on a worker thread, out of any
            # fronting proxy's connection window. Poll GET /runs?run_id=… . One run per capability
            # at a time: the same account's retry gets the SAME running run back (never a second
            # run, never a double version bump); another account's concurrent request → 409.
            try:
                pending = RT.submit_run(cap_id, account, mode=mode, idempotency_key=idem,
                                        background=True)
            except CapabilityBusyError as busy:
                return self._send(409, {"error": str(busy), "capability_id": busy.cap_id,
                                        "run_id": busy.run_id})
            return self._send(202, {"run_id": pending["run_id"], "status": pending["status"],
                                    "run": pending})
        # SYNC default (backward compatible — the generated web/teleon/teleon-live.js contract):
        # execute NOW and answer 201 with the finished run. idempotency_key replays still dedupe.
        run = RT.submit_run(cap_id, account, mode=mode, idempotency_key=idem, background=False)
        return self._send(201, {"run": run})

    def log_message(self, *args) -> None:  # quiet
        pass


def _self_test() -> int:
    global RT, _validate_session
    import tempfile
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    global STATE_DIR
    real_state = STATE_DIR
    with tempfile.TemporaryDirectory() as tmp:
        # co-locate under a teleon-runtime subdir so the compiled-unit registry (STATE_DIR.parent/
        # teleon-compiler) also lands in the temp tree — the self-test never touches the real registry
        STATE_DIR = Path(tmp) / "teleon-runtime"
        rt = Runtime()
        ck("seeded capabilities present", len(rt.caps) == len(CAPABILITIES))
        run = rt.execute("cap-dates", "acct_test", mode="deterministic")
        ck("run really executed (all examples)", run["total"] == 4 and run["passed"] == 4)
        ck("real score → promotion gate applied", run["score"] == 1.0 and run["decision"] == "promoted")
        # ---- the LOOP'S DEPLOY ARC: promotion auto-compiles + registers a deployable unit ----
        cu = run.get("compiled_unit") or {}
        ck("promotion auto-compiled a runtime unit", cu.get("compiled") is True
           and str(cu.get("unit_id", "")).startswith("cru_")
           and cu.get("exec_target") == AUTO_COMPILE_EXEC_TARGET)
        from src.teleon.compiler import open_registry as _open_reg
        _reg = _open_reg(log_path=_compiled_units_path())
        _active = _reg.latest_active_for("cap-dates")
        ck("the compiled unit is in the registry (active)",
           _active is not None and _active["unit_id"] == cu.get("unit_id"))
        # a second promotion of ANOTHER cap supersedes + sets a real rollback_target (lossless
        # chain) — uses cap-redact so cap-dates' version assertions below stay intact
        cu_a = (rt.execute("cap-redact", "acct_test", mode="deterministic").get("compiled_unit") or {})
        cu_b = (rt.execute("cap-redact", "acct_test", mode="deterministic").get("compiled_unit") or {})
        ck("re-promotion registers a new unit with a real rollback_target",
           cu_a.get("compiled") is True and cu_b.get("compiled") is True
           and cu_b.get("rollback_target") == cu_a.get("unit_id"))
        # ---- the FAILURE PATH: a non-promotion records the next-tier escalation (advisory) ----
        esc = rt._escalation_for_failed("cap-dates", {"attempts": 2})
        ck("non-promotion escalates toward bounded exploration (T3, honest offline default)",
           esc.get("tier") == 3 and esc.get("action") == "dispatch_bounded_exploration"
           and esc.get("runtime_ref") == "local_emulator@v1")
        # ---- ZERO-OP LAUNCH: a launch pass hands the registered unit to the Machines runner ----
        from scripts.deploy.teleon_machines_runner import (Runner as _Rnr, RunnerMachinesAPI as _RAPI,  # noqa: N814
                                                           _runner_config as _rcfg, _FakeMachinesAPI as _FAPI,
                                                           _FakeClock as _FClk)
        _lr_clock = _FClk()
        _lr_api = _FAPI(states=["started", "stopped"], exit_code=0)
        _lr_runner = _Rnr(_lr_api, _rcfg(), clock=_lr_clock, sleep=_lr_clock.sleep,
                          receipts_path=Path(tmp) / "auto-launch-receipts.jsonl")
        _lp1 = rt.launch_pending(runner=_lr_runner, receipts_path=Path(tmp) / "auto-launch-receipts.jsonl")
        ck("auto-launch: a launch pass launches the registered active units (co-resident runner)",
           len(_lp1["launched"]) >= 1 and _lr_api.create_calls >= 1)
        _lp2 = rt.launch_pending(runner=_lr_runner, receipts_path=Path(tmp) / "auto-launch-receipts.jsonl")
        ck("auto-launch: a second pass re-launches nothing (idempotent via the launch receipt)",
           _lp2["launched"] == [])
        _lp3 = rt.launch_pending(runner=None, receipts_path=Path(tmp) / "auto-launch-plan-only.jsonl")
        ck("auto-launch: no runner (no token) → honest PLAN, never a fake launch",
           len(_lp3["planned"]) >= 1 and _lp3["launched"] == [])
        ck("deterministic run labeled honestly (gate_note + basis + split rates)",
           run["gate_note"] == DETERMINISTIC_GATE_NOTE and run["gate_basis"] == GATE_BASIS
           and run["train_pass_rate"] == 1.0 and run["holdout_pass_rate"] == 1.0
           and run["holdout_contaminated"] is False)
        ck("version bumped + status persisted", rt.caps["cap-dates"]["version"] == 2
           and rt.caps["cap-dates"]["status"] == "promoted")
        receipts = rt.receipts_for(run["run_id"])
        ck("receipts persisted with hashes + timing", len(receipts) == 4
           and all(r["input_sha"] and r["output_sha"] and r["duration_us"] >= 0 for r in receipts))
        rt2 = Runtime()
        ck("restart-safe (state reloads)", rt2.caps["cap-dates"]["version"] == 2)
        bad = _json_guard("not json")
        ck("failure path is honest (INVALID, not fabricated)", bad == "INVALID")
        for cid in CAPABILITIES:
            r = rt.execute(cid, "acct_test", mode="deterministic")
            ck(f"{cid}: reference suite passes deterministically", r["score"] == 1.0)

        # ---- the MODEL-BUILT path (fake route: plumbing + gate + refine, no network) ----
        class FakeRoute:
            model_id = "fake-test-model"
            def __init__(self):
                self.calls = 0
            def health(self):
                return True
            def complete(self, system, user, **kw):
                self.calls += 1
                out = CAPABILITIES["cap-cite"]["impl"](user)
                if "IMPORTANT" not in system and "1692e" in user:
                    return out.replace("§", "Sec.")  # attempt-1 botch → forces the refine round
                return out
        fake = FakeRoute()
        run_m = rt.execute("cap-cite", "acct_test", mode="model", route=fake)
        ck("model mode: the MODEL performed the suite", run_m["mode"] == "model"
           and run_m["model_id"] == "fake-test-model" and fake.calls == 8)
        ck("model mode: gate failed attempt 1 → self-refine recovered → promoted",
           run_m["attempts"] == 2 and run_m["score"] == 1.0 and run_m["decision"] == "promoted")
        rec_m = rt.receipts_for(run_m["run_id"])
        ck("model receipts persist BOTH attempts (lossless)",
           len(rec_m) == 8 and {r["attempt"] for r in rec_m} == {1, 2})
        ck("genuine model run: BOTH splits cleared the gate, fields honest, no gate_note",
           run_m["train_pass_rate"] == 1.0 and run_m["holdout_pass_rate"] == 1.0
           and run_m["gate_basis"] == GATE_BASIS and run_m["holdout_contaminated"] is False
           and "gate_note" not in run_m)

        class DeadRoute:
            model_id = "unreachable"
            def health(self):
                return False
        run_d = rt.execute("cap-dates", "acct_test", mode="model", route=DeadRoute())
        ck("model mode with no route → honest deterministic fallback + note",
           run_d["mode"] == "deterministic" and "note" in run_d and "gate_note" in run_d)

        # ---- ANTI-GAMING REGRESSION (the de-contamination this gate exists for) ----
        # Under the OLD refine prompt (expected outputs pasted verbatim), this route promoted
        # 4/4 on attempt 2 by copying the answer key. It must now fail the holdout and NOT promote.
        class ParrotRoute:
            """Answer-key parrot: succeeds on an example ONLY if that example's expected
            output text is visible in its prompt; otherwise it just echoes the input."""
            model_id = "answer-key-parrot"
            def __init__(self):
                self.leak_seen = False
            def health(self):
                return True
            def complete(self, system, user, **kw):
                for inp, expected in CAPABILITIES["cap-cite"]["examples"]:
                    if inp == user and expected in system:
                        self.leak_seen = True
                        return expected  # copies the key — the gamed path
                return user  # no key visible → no real skill: echo unchanged
        parrot = ParrotRoute()
        run_p = rt.execute("cap-cite", "acct_test", mode="model", route=parrot)
        ck("anti-gaming: no expected output text ever reached a prompt", not parrot.leak_seen)
        ck("anti-gaming: answer-key parrot fails the holdout and is NOT promoted",
           run_p["decision"] != "promoted" and run_p["holdout_pass_rate"] < PROMOTE_AT)
        rec_p = rt.receipts_for(run_p["run_id"])
        ck("anti-gaming: holdout receipts record the real failures",
           any(not r["pass"] and r["split"] == HOLDOUT_SPLIT for r in rec_p))
        ck("receipts carry split + gate evidence fields",
           len(rec_p) == 8 and all(r["split"] in (TRAIN_SPLIT, HOLDOUT_SPLIT)
                                   and r["holdout_contaminated"] is False
                                   and "train_pass_rate" in r and "holdout_pass_rate" in r
                                   for r in rec_p))
        ck("split rule is the deterministic even/odd parity",
           all(r["split"] == _example_split(r["example"]) for r in rec_p))

        # ---- concurrency: parallel handler threads must not corrupt versions/state ----
        workers = 2      # the reported race window: two ThreadingHTTPServer handler threads
        per_thread = 8   # rapid-fire read-modify-write cycles per thread to expose races
        v0 = rt.caps["cap-redact"]["version"]
        barrier = threading.Barrier(workers)
        errors: list[str] = []
        def hammer() -> None:
            try:
                barrier.wait()
                for _ in range(per_thread):
                    rt.execute("cap-redact", "acct_test", mode="deterministic", route=DeadRoute())
            except Exception as exc:  # pragma: no cover - only on regression
                errors.append(repr(exc))
        threads = [threading.Thread(target=hammer) for _ in range(workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        new_n = workers * per_thread
        versions = sorted(r["version"] for r in rt.runs if r["capability_id"] == "cap-redact")
        ck("concurrent executes: versions monotonic, contiguous, no duplicates",
           not errors and rt.caps["cap-redact"]["version"] == v0 + new_n
           and versions[-new_n:] == list(range(v0 + 1, v0 + new_n + 1)))
        ids = [r["run_id"] for r in rt.runs]
        ck("concurrent executes: run ids unique", len(ids) == len(set(ids)))
        # runs.jsonl is an APPEND-ONLY EVENT log (running line + terminal line per run): every line
        # must parse, and the DISTINCT run_ids on disk must equal the folded in-memory view.
        disk_lines = [json.loads(line) for line in
                      rt.runs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        disk_ids = {l["run_id"] for l in disk_lines}
        disk_caps = json.loads(rt.caps_path.read_text(encoding="utf-8"))
        ck("state files intact after concurrent writes (every line parses, distinct ids match view)",
           len(disk_ids) == len(rt.runs) and disk_ids == {r["run_id"] for r in rt.runs}
           and disk_caps["cap-redact"]["version"] == v0 + new_n)

        # ===================================================================
        #  ASYNC RUN LIFECYCLE  (the P1 work)
        # ===================================================================
        # A slow route whose model calls take SLOW_S each; one clean attempt issues SUITE_CALLS
        # model calls, so a SYNCHRONOUS run would take ≥ SUITE_CALLS × SLOW_S — an async POST that
        # returns much faster PROVES it did not block on the suite.
        SLOW_S = 0.25
        SUITE_CALLS = len(CAPABILITIES["cap-cite"]["examples"])  # one attempt = one call per example
        SUITE_MIN_SYNC_S = SUITE_CALLS * SLOW_S  # lower bound on a synchronous one-attempt suite

        def slow_route(cap: str, started=None, ended=None):
            class SlowRoute:
                model_id = "slow-fake-model"
                def health(self) -> bool:
                    return True
                def complete(self, system, user, **kw):
                    if started is not None:
                        started.append(time.perf_counter())
                    time.sleep(SLOW_S)
                    if ended is not None:
                        ended.append(time.perf_counter())
                    return CAPABILITIES[cap]["impl"](user)
            return SlowRoute()

        def poll(run_id: str, timeout: float = 30.0) -> dict:
            deadline = time.time() + timeout
            while time.time() < deadline:
                r = rt.get_run(run_id)
                if r and r["status"] in TERMINAL_STATUSES:
                    return r
                time.sleep(0.01)
            return rt.get_run(run_id)

        # (1) async POST returns FAST with a pending record — before a slow suite could finish.
        t0 = time.perf_counter()
        pend = rt.submit_run("cap-cite", "acct_test", mode="model",
                             route=slow_route("cap-cite"), background=True)
        submit_dt = time.perf_counter() - t0
        ck("async: POST returns immediately with {run_id, status:running} (well before a slow suite)",
           pend["status"] == STATUS_RUNNING and "run_id" in pend
           and submit_dt < SUITE_MIN_SYNC_S / 2)
        ck("async: a freshly-enqueued run is observable as 'running' before it finishes",
           (rt.get_run(pend["run_id"]) or {}).get("status") == STATUS_RUNNING)
        # (1b) status transitions running → terminal, receipts land, version commits.
        term = poll(pend["run_id"])
        ck("async: status transitions running → terminal (promoted) with real score + receipts",
           term["status"] == "promoted" and term["score"] == 1.0
           and len(rt.receipts_for(pend["run_id"])) == SUITE_CALLS)
        ck("async: the terminal version was committed to the capability state",
           rt.caps["cap-cite"]["version"] == term["version"])

        # (2) two DIFFERENT caps run CONCURRENTLY — their model-call windows overlap.
        sd1, ed1, sd2, ed2 = [], [], [], []
        pa = rt.submit_run("cap-dates", "acct_test", mode="model",
                           route=slow_route("cap-dates", sd1, ed1), background=True)
        pb = rt.submit_run("cap-redact", "acct_test", mode="model",
                           route=slow_route("cap-redact", sd2, ed2), background=True)
        ra, rb = poll(pa["run_id"]), poll(pb["run_id"])
        # overlap proof: the two workers' execution INTERVALS intersect — one cap started before the
        # other finished. Impossible if a single lock had serialized the slow model calls (cap B
        # would only begin after cap A's whole suite drained). Interval A = [min(sd1), max(ed1)].
        overlap = (bool(sd1 and sd2 and ed1 and ed2)
                   and max(min(sd1), min(sd2)) < min(max(ed1), max(ed2)))
        ck("async: two DIFFERENT capabilities execute concurrently (call intervals overlap)",
           overlap and ra["status"] == "promoted" and rb["status"] == "promoted")

        # (3) IDEMPOTENCY: a replayed POST with the same key returns the SAME run_id and the
        #     capability version is bumped exactly ONCE (no double-bump from a UI retry).
        v_idem = rt.caps["cap-json-guard"]["version"]
        key = "client-key-abc123"
        i1 = rt.submit_run("cap-json-guard", "acct_test", mode="deterministic",
                           idempotency_key=key, background=True)
        i2 = rt.submit_run("cap-json-guard", "acct_test", mode="deterministic",
                           idempotency_key=key, background=True)
        ti1 = poll(i1["run_id"])
        ck("async idempotency: replayed key returns the SAME run_id (no second run)",
           i1["run_id"] == i2["run_id"])
        ck("async idempotency: the capability version bumped exactly ONCE (no double-bump)",
           rt.caps["cap-json-guard"]["version"] == v_idem + 1 and ti1["status"] == "promoted")
        idem_runs = [r for r in rt.runs if r.get("idempotency_key") == key]
        ck("async idempotency: exactly one run carries the key", len(idem_runs) == 1)

        # (4) RESTART SAFETY: a process restart sweeps any stale 'running' row to 'interrupted'
        #     (older than RUNNING_SWEEP_STALE_S), never leaving it 'running' forever; a FRESH
        #     'running' row is left alone, and the sweep is lossless (original line preserved).
        stale_at = int(time.time()) - (RUNNING_SWEEP_STALE_S + 5)
        with rt._lock:
            rt._persist_run({"run_id": "run_stale_v99_cap-dates", "capability_id": "cap-dates",
                             "capability": "Date normalizer", "account_id": "acct_test",
                             "status": STATUS_RUNNING, "version": 99, "at": stale_at})
            rt._persist_run({"run_id": "run_fresh_v100_cap-dates", "capability_id": "cap-dates",
                             "capability": "Date normalizer", "account_id": "acct_test",
                             "status": STATUS_RUNNING, "version": 100, "at": int(time.time())})
        rt_restart = Runtime()  # simulate a process restart over the same state dir → startup sweep
        swept = rt_restart.get_run("run_stale_v99_cap-dates")
        kept = rt_restart.get_run("run_fresh_v100_cap-dates")
        ck("restart sweep: a stale 'running' run becomes 'interrupted' (never stuck running)",
           swept is not None and swept["status"] == STATUS_INTERRUPTED)
        ck("restart sweep: a fresh 'running' run is NOT swept (belongs to a live worker)",
           kept is not None and kept["status"] == STATUS_RUNNING)
        stale_events = [json.loads(line) for line
                        in rt_restart.runs_path.read_text(encoding="utf-8").splitlines()
                        if line.strip() and json.loads(line)["run_id"] == "run_stale_v99_cap-dates"]
        ck("restart sweep is lossless: original 'running' line preserved before 'interrupted'",
           [e["status"] for e in stale_events] == [STATUS_RUNNING, STATUS_INTERRUPTED])

        # (5) WORKER CRASH: an error escaping the suite finalizes the run 'failed' — never stuck
        #     'running' — and does NOT corrupt the capability's gate verdict.
        class HealthCrash:
            model_id = "crash"
            def health(self) -> bool:
                raise RuntimeError("route blew up")  # escapes the per-example try in _suite
        v_crash = rt.caps["cap-redact"]["version"]
        status_before = rt.caps["cap-redact"]["status"]
        crashed = rt.submit_run("cap-redact", "acct_test", mode="model",
                                route=HealthCrash(), background=False)
        ck("async crash: a worker error finalizes 'failed' (never stuck 'running'), with the error",
           crashed["status"] == STATUS_FAILED and "route blew up" in crashed.get("error", ""))
        ck("async crash: a crash does not change the capability's gate verdict, version stays contiguous",
           rt.caps["cap-redact"]["status"] == status_before
           and rt.caps["cap-redact"]["version"] == v_crash + 1)

        # ===================================================================
        #  HTTP CONTRACT: sync 201 default · async 202 opt-in · 409 busy · idempotent retry
        # ===================================================================
        # A real loopback ThreadingHTTPServer with a hermetic identity stub — this is the layer
        # the generated web/teleon/teleon-live.js (sync, expects 201 + finished {run}) and async
        # pollers actually talk to, so the status codes are asserted literally.
        import urllib.error
        sessions = {"tok-a": "acct_test", "tok-b": "acct_other"}
        real_validate, real_rt = _validate_session, RT
        _validate_session = lambda realm, sid: sessions.get(sid)  # noqa: E731 — hermetic identity
        RT = rt
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{httpd.server_address[1]}/api/teleon/local"

        def call(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
            data = json.dumps(payload).encode("utf-8") if payload is not None else None
            req = urllib.request.Request(base + path, data=data, method=method,
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status, json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as err:
                return err.code, json.loads(err.read().decode("utf-8") or "{}")

        gate = threading.Event()

        class GateRoute:  # holds a model suite in flight until the test opens the gate
            model_id = "gated-test-model"
            def health(self) -> bool:
                return True
            def complete(self, system, user, **kw):
                if not gate.wait(timeout=30):
                    raise TimeoutError("self-test gate never opened")
                return CAPABILITIES["cap-cite"]["impl"](user)

        try:
            # (6) SYNC DEFAULT unchanged — the generated teleon-live.js contract: 201 + finished run.
            cs, bs = call("POST", "/runs", {"session_id": "tok-a", "capability_id": "cap-dates",
                                            "mode": "deterministic"})
            ck("HTTP sync default: plain POST answers 201 with the FINISHED run (generated-UI contract)",
               cs == 201 and bs["run"]["decision"] == "promoted" and bs["run"]["score"] == 1.0)
            ck("HTTP: no session → 401 (mutations stay gated)",
               call("POST", "/runs", {"capability_id": "cap-dates"})[0] == 401)

            # (7) ASYNC lifecycle over HTTP: 202 {run_id, status:running} → poll → terminal.
            ca, ba = call("POST", "/runs", {"session_id": "tok-a", "async": True,
                                            "capability_id": "cap-dates", "mode": "deterministic"})
            ck("HTTP async opt-in: 202 {run_id, status:running} immediately",
               ca == 202 and ba["status"] == STATUS_RUNNING and ba["run_id"])
            done = poll(ba["run_id"])
            cg, bg = call("GET", f"/runs?run_id={ba['run_id']}")
            ck("HTTP async poll: GET runs?run_id= reaches the terminal record",
               cg == 200 and bg["run"]["status"] == "promoted"
               and bg["run"]["run_id"] == ba["run_id"] and done["status"] == "promoted")
            ck("HTTP async poll: unknown run_id → 404",
               call("GET", "/runs?run_id=run_nope")[0] == 404)

            # (8) 409 ON CONCURRENT + RETRY-NO-DOUBLE-VERSION, against a run HELD in flight by the
            #     gate (deterministic — no sleep-based timing).
            v_cite = rt.caps["cap-cite"]["version"]
            held = rt.submit_run("cap-cite", "acct_test", mode="model", route=GateRoute(),
                                 background=True)
            ck("async admission: the held run is live and 'running'",
               (rt.get_run(held["run_id"]) or {}).get("status") == STATUS_RUNNING)
            cr, br = call("POST", "/runs", {"session_id": "tok-a", "async": True,
                                            "capability_id": "cap-cite", "mode": "model"})
            ck("idempotent retry: same account + same in-flight capability → the SAME running run",
               cr == 202 and br["run_id"] == held["run_id"] and br["status"] == STATUS_RUNNING)
            co, bo = call("POST", "/runs", {"session_id": "tok-b", "async": True,
                                            "capability_id": "cap-cite", "mode": "model"})
            ck("409 on concurrent: a DIFFERENT account hits the in-flight capability",
               co == 409 and "error" in bo and bo.get("capability_id") == "cap-cite"
               and bo.get("run_id") == held["run_id"])
            gate.set()
            held_done = poll(held["run_id"])
            new_cite = [r for r in rt.runs if r["capability_id"] == "cap-cite"
                        and r.get("version", 0) > v_cite]
            ck("retry never double-bumps: ONE new run, ONE version bump, terminal promoted",
               held_done["status"] == "promoted"
               and rt.caps["cap-cite"]["version"] == v_cite + 1
               and len(new_cite) == 1 and new_cite[0]["run_id"] == held["run_id"])
            cf, bf = call("POST", "/runs", {"session_id": "tok-b", "async": True,
                                            "capability_id": "cap-cite", "mode": "deterministic"})
            freed = poll(bf["run_id"]) if cf == 202 else {}
            ck("capability freed after completion: the previously-409'd account is admitted",
               cf == 202 and bf["run_id"] != held["run_id"] and freed.get("status") == "promoted"
               and freed.get("account_id") == "acct_other")
        finally:
            gate.set()  # never leave a gated worker blocked, even if an assertion threw
            httpd.shutdown()
            httpd.server_close()
            _validate_session, RT = real_validate, real_rt
    STATE_DIR = real_state
    print("\n" + ("PASS — teleon_local_runtime: REAL capability execution with receipts, a "
                  "train+holdout promotion gate (no answer-key leakage), opt-in ASYNC runs "
                  "(202 + worker thread, one in-flight run per capability with 409 conflicts "
                  "and idempotent same-account retries that never double-bump, interrupted-"
                  "sweep), the unchanged 201 sync default, locked concurrent state, and "
                  "restart-safe persistence."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main(argv: list[str] | None = None) -> int:
    global RT
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    RT = Runtime()
    port = args.port or _registry_port(SERVICE_ID)
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")  # 0.0.0.0 only in container deploys
    httpd = ThreadingHTTPServer((bind_host, port), Handler)
    print(f"Teleon local runtime → http://{bind_host}:{port}  "
          f"({len(RT.caps)} capabilities, {len(RT.runs)} recorded runs, gate ≥{PROMOTE_AT}, "
          f"sync POST→201; async POST {{\"async\": true}}→202, poll GET /runs?run_id=…)")
    # zero-op launch (co-resident): promoted capabilities launch themselves on Fly Machines
    if os.environ.get(AUTO_LAUNCH_ENV) == "1" and os.environ.get("FLY_API_TOKEN"):
        from scripts.deploy.teleon_machines_runner import Runner, RunnerMachinesAPI, _runner_config
        _cfg = _runner_config()
        _runner = Runner(RunnerMachinesAPI(_cfg["api_base"], os.environ["FLY_API_TOKEN"], _cfg["app"]), _cfg)

        def _auto_launch_loop() -> None:
            while True:
                try:
                    RT.launch_pending(runner=_runner)
                except Exception:  # a launch hiccup must never take the runtime down
                    pass
                time.sleep(AUTO_LAUNCH_POLL_SECONDS)
        threading.Thread(target=_auto_launch_loop, name="teleon-auto-launch", daemon=True).start()
        print(f"  auto-launch ON ({AUTO_LAUNCH_ENV}=1, token present): promoted capabilities launch on Fly Machines")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
