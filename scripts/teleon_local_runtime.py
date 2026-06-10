#!/usr/bin/env python3
"""scripts.teleon_local_runtime — the LOCAL Teleon capability runtime (demo-grade, REAL execution).

Teleon's thesis, run honestly on a laptop: a capability ships only after it clears its success
criteria on real examples. This service holds a small set of REAL deterministic capabilities
(pure-Python implementations — no model calls, no network), and a "run" actually EXECUTES the
capability against its example suite right now:

  * every example execution produces a RECEIPT (input/output hashes, pass/fail, duration µs);
  * the run's score is the real pass-rate; the PROMOTION GATE is applied to that score
    (>= 0.90 → promoted; >= 0.70 → candidate; below → rolled-back) and the capability's
    version/status/state update accordingly;
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
import re
import sys
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parents[1]
SERVICE_REGISTRY = REPO / "architecture" / "local_service_registry.json"
IDENTITY_REGISTRY = REPO / "architecture" / "identity_realm_registry.json"
STATE_DIR = REPO / "dist" / "local-services-state" / "teleon-runtime"
SERVICE_ID = "teleon_local_runtime"

PROMOTE_AT = 0.90   # the gate: promoted at or above this real pass-rate
CANDIDATE_AT = 0.70  # below the gate but workable → candidate; below this → rolled-back


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
        "criteria": ["emails masked", "phones masked", "no model call"],
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

    def execute(self, cap_id: str, account_id: str) -> dict:
        """REALLY run the capability over its example suite; receipts + gate decision persist."""
        spec = CAPABILITIES[cap_id]
        state = self.caps[cap_id]
        run_id = f"run_{int(time.time() * 1000):x}_{cap_id}"
        receipts, passed = [], 0
        for i, (inp, expected) in enumerate(spec["examples"]):
            t0 = time.perf_counter_ns()
            try:
                out = spec["impl"](inp)
            except Exception as exc:  # a real failure is a real failure
                out = f"ERROR: {exc}"
            us = (time.perf_counter_ns() - t0) // 1000
            ok = out == expected
            passed += ok
            receipts.append({"run_id": run_id, "example": i, "input_sha": _sha(inp),
                             "output_sha": _sha(out), "expected_sha": _sha(expected),
                             "pass": ok, "duration_us": us, "deterministic": True})
        score = round(passed / len(spec["examples"]), 2)
        decision = ("promoted" if score >= PROMOTE_AT else
                    "candidate" if score >= CANDIDATE_AT else "rolled-back")
        state["version"] += 1
        state["status"] = decision
        state["last_score"] = score
        self._save_caps()
        run = {"run_id": run_id, "capability_id": cap_id, "capability": spec["name"],
               "account_id": account_id, "score": score, "passed": passed,
               "total": len(spec["examples"]), "decision": decision,
               "version": state["version"], "at": int(time.time()),
               "duration_us": sum(r["duration_us"] for r in receipts)}
        self.runs.append(run)
        with self.runs_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(run) + "\n")
        with self.receipts_path.open("a", encoding="utf-8") as fh:
            for r in receipts:
                fh.write(json.dumps(r) + "\n")
        return run

    def receipts_for(self, run_id: str) -> list[dict]:
        if not self.receipts_path.exists():
            return []
        return [r for r in map(json.loads, self.receipts_path.read_text(encoding="utf-8").splitlines())
                if r["run_id"] == run_id]


def _validate_session(realm: str, session_id: str) -> str | None:
    """Resolve the account server-side via the identity service (never trust the client)."""
    if not session_id:
        return None
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{_identity_port()}/api/identity/{realm}/session/validate",
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
            return self._send(200, {"ok": True, "service": SERVICE_ID,
                                    "capabilities": len(RT.caps), "runs": len(RT.runs)})
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
        return self._send(201, {"run": RT.execute(cap_id, account)})

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
        run = rt.execute("cap-dates", "acct_test")
        ck("run really executed (all examples)", run["total"] == 4 and run["passed"] == 4)
        ck("real score → promotion gate applied", run["score"] == 1.0 and run["decision"] == "promoted")
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
            r = rt.execute(cid, "acct_test")
            ck(f"{cid}: suite passes deterministically", r["score"] == 1.0)
    STATE_DIR = real_state
    print("\n" + ("PASS — teleon_local_runtime: REAL deterministic capability execution with "
                  "receipts, a real promotion gate, and restart-safe state."
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
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Teleon local runtime → http://127.0.0.1:{port}  "
          f"({len(RT.caps)} capabilities, {len(RT.runs)} recorded runs, gate ≥{PROMOTE_AT})")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
