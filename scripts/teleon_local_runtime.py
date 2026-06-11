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

Mutations are session-gated against the identity service (realm `teleon`), the same pattern as
scripts/registry_local_service.py: the account is resolved server-side; the client never asserts
who it is. Reads are open (local demo plane). Nothing here is "truth" beyond what it really did:
deterministic code ran, receipts recorded. Port lives in architecture/local_service_registry.json.

Endpoints
  GET  /healthz                                  → {ok}
  GET  /api/teleon/<realm>/capabilities          → {capabilities: [...]}
  POST /api/teleon/<realm>/runs                  → {run} (executes NOW; session required)
  GET  /api/teleon/<realm>/runs?session_id=…     → {runs: [...]} (the account's)
  GET  /api/teleon/<realm>/evidence?run_id=…     → {receipts: [...]}

Offline, stdlib-only.  --self-test exercises the whole lifecycle in-process.
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


class Runtime:
    def __init__(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.caps_path = STATE_DIR / "capabilities.json"
        self.runs_path = STATE_DIR / "runs.jsonl"
        self.receipts_path = STATE_DIR / "receipts.jsonl"
        # ONE lock: ThreadingHTTPServer runs handlers on parallel threads, so every
        # read-modify-write of caps/runs/receipts state (and the file writes) serializes here —
        # otherwise concurrent runs race the version bump and corrupt the append-only files.
        self._lock = threading.Lock()
        if self.caps_path.exists():
            self.caps = json.loads(self.caps_path.read_text(encoding="utf-8"))
        else:
            self.caps = {cid: {"id": cid, "name": c["name"], "criteria": c["criteria"],
                               "version": 1, "status": "candidate", "last_score": None,
                               "examples": len(c["examples"])}
                         for cid, c in CAPABILITIES.items()}
            self._save_caps()
        self.runs = [json.loads(line) for line in self.runs_path.read_text(encoding="utf-8").splitlines()] \
            if self.runs_path.exists() else []

    def _save_caps(self) -> None:
        self.caps_path.write_text(json.dumps(self.caps, indent=1), encoding="utf-8")

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

    def execute(self, cap_id: str, account_id: str, mode: str = "auto", route=None) -> dict:
        """REALLY run the capability suite and apply the promotion gate.

        mode 'model' (the product path): the MODEL performs the capability per example via the
        provider-neutral chat route; one self-refine round when the gate isn't cleared, both
        attempts receipted (lossless). mode 'deterministic': the seeded reference implementation
        (the honest fallback when no model route is reachable — labeled, never disguised).
        The gate itself is deterministic on purpose: evidence judges, models build.

        GATE BASIS (train+holdout): the suite always runs in FULL, but promotion requires the
        TRAIN and the HOLDOUT pass-rates to BOTH clear PROMOTE_AT. The refine prompt may quote
        failed TRAIN inputs, never any expected output (see _refined_instruction), so a model
        cannot promote by copying an answer key. The whole read-modify-write — version bump,
        caps/runs/receipts state and file appends — serializes on self._lock because
        ThreadingHTTPServer dispatches handlers on parallel threads.
        """
        spec = CAPABILITIES[cap_id]
        route = route if route is not None else resolve_route()
        with self._lock:
            state = self.caps[cap_id]
            # version is part of the id: two rapid runs of one capability must never collide
            run_id = f"run_{int(time.time() * 1000):x}_v{state['version'] + 1}_{cap_id}"
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
            total = len(spec["examples"])
            score = round(passed / total, RATE_DECIMALS)
            # promotion needs BOTH splits ≥ PROMOTE_AT: even a fully leaked prompt could only
            # game what the prompt contains, never the holdout. Lower tiers stay on the overall
            # score, exactly as before.
            decision = ("promoted" if train_rate >= PROMOTE_AT and hold_rate >= PROMOTE_AT else
                        "candidate" if score >= CANDIDATE_AT else "rolled-back")
            state["version"] += 1
            state["status"] = decision
            state["last_score"] = score
            state["last_mode"] = executed_mode
            self._save_caps()
            run = {"run_id": run_id, "capability_id": cap_id, "capability": spec["name"],
                   "account_id": account_id, "score": score, "passed": passed, "total": total,
                   "train_pass_rate": round(train_rate, RATE_DECIMALS),
                   "holdout_pass_rate": round(hold_rate, RATE_DECIMALS),
                   # literal honesty field: no example's expected output entered any prompt —
                   # guaranteed by _refined_instruction, enforced by the parrot regression test
                   "holdout_contaminated": False,
                   "gate_basis": GATE_BASIS,
                   "decision": decision, "version": state["version"], "at": int(time.time()),
                   "mode": executed_mode, "model_id": model_id, "attempts": attempts,
                   "duration_us": sum(r["duration_us"] for r in receipts)}
            if executed_mode == "deterministic":
                # honest provenance: this gate was cleared by reference code, not a model
                run["gate_note"] = DETERMINISTIC_GATE_NOTE
            if model_note:
                run["note"] = model_note
            for r in receipts:  # every receipt carries the run's gate evidence (self-contained audit rows)
                r["train_pass_rate"] = run["train_pass_rate"]
                r["holdout_pass_rate"] = run["holdout_pass_rate"]
                r["holdout_contaminated"] = False
            self.runs.append(run)
            with self.runs_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(run) + "\n")
            with self.receipts_path.open("a", encoding="utf-8") as fh:
                for r in receipts:
                    fh.write(json.dumps(r) + "\n")
            return run

    def receipts_for(self, run_id: str) -> list[dict]:
        with self._lock:  # consistent snapshot: never read a half-appended line mid-execute()
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
        return self._send(201, {"run": RT.execute(cap_id, account, mode=mode)})

    def log_message(self, *args) -> None:  # quiet
        pass


def _self_test() -> int:
    global RT
    import tempfile
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    global STATE_DIR
    real_state = STATE_DIR
    with tempfile.TemporaryDirectory() as tmp:
        STATE_DIR = Path(tmp)
        rt = Runtime()
        ck("seeded capabilities present", len(rt.caps) == len(CAPABILITIES))
        run = rt.execute("cap-dates", "acct_test", mode="deterministic")
        ck("run really executed (all examples)", run["total"] == 4 and run["passed"] == 4)
        ck("real score → promotion gate applied", run["score"] == 1.0 and run["decision"] == "promoted")
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
        reloaded_runs = [json.loads(line) for line in
                         rt.runs_path.read_text(encoding="utf-8").splitlines()]
        disk_caps = json.loads(rt.caps_path.read_text(encoding="utf-8"))
        ck("state files intact after concurrent writes (every line parses, counts match)",
           len(reloaded_runs) == len(rt.runs)
           and disk_caps["cap-redact"]["version"] == v0 + new_n)
    STATE_DIR = real_state
    print("\n" + ("PASS — teleon_local_runtime: REAL capability execution with receipts, a "
                  "train+holdout promotion gate (no answer-key leakage), locked concurrent "
                  "state, and restart-safe persistence."
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
          f"({len(RT.caps)} capabilities, {len(RT.runs)} recorded runs, gate ≥{PROMOTE_AT})")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
