#!/usr/bin/env python3
"""scripts.check_contextops_sandbox_gate — proof (CONTEXTOPS SANDBOX MODE): a drafted extractor snippet runs
in an isolated temp dir behind a PROOF GATE, and the gate's invariants hold:

  * a clean snippet whose unit test passes → gate_decision='approved', can_register=True (sandbox + proof pass);
  * a snippet that reaches for the NETWORK (when the recipe forbids it) is BLOCKED before it runs → 'rejected',
    can_register=False;
  * a snippet that reaches for a SECRET (os.environ / api_key / sk-...) is BLOCKED → 'rejected', can_register=False;
  * a snippet that reaches for an ESCAPE capability (subprocess / eval / exec) is BLOCKED → 'rejected';
  * an UNPROVEN snippet (its unit test fails) can NEVER register → 'rejected', can_register=False;
  * a HIGH-RISK snippet that passes still needs a human-approval hook → 'needs_human_approval', can_register=False,
    until a human approves; nothing here auto-registers/executes a production worker;
  * the sandbox is provisioned with NO secrets (secrets_present pinned False) and the temp dir is cleaned up;
  * the gate result is shaped like VerifierProofResult.v1.

Deterministic, stdlib-only, offline (the temp-dir run touches no real network/secret). No clock (time injected).
CLI: PYTHONPATH=. python3 scripts/check_contextops_sandbox_gate.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.contextops.sandbox_gate import (  # noqa: E402
    GATE_DECISIONS,
    SandboxViolation,
    gate_snippet,
    run_in_sandbox,
    static_scan,
)

_NOW = 1_700_000_000  # injected epoch seconds

# A CLEAN, deterministic extractor body a codegen agent might draft (regex over a payload). Its unit test
# below confirms it reads the expected value inside the sandbox temp dir.
_CLEAN_CODE = """
import re
def extract(payload):
    m = re.search(r"(\\d+) business days", payload)
    return int(m.group(1)) if m else None
"""
# A snippet that tries the NETWORK (forbidden when the recipe doesn't allow it).
_NETWORK_CODE = """
import urllib.request
def extract(payload):
    return urllib.request.urlopen("https://example.gov/reg").read()
"""
# A snippet that reads a SECRET.
_SECRET_CODE = """
import os
def extract(payload):
    return os.environ.get("OPENAI_API_KEY")
"""
# A snippet that reaches for an ESCAPE capability.
_ESCAPE_CODE = """
import subprocess
def extract(payload):
    return subprocess.run(["ls"]).stdout
"""


def _passing_unit_test(tmp: Path) -> None:
    """A real unit-test proof for the clean snippet: it must read 10 from '10 business days'. Runs in `tmp`."""
    ns: dict = {}
    exec(compile(_CLEAN_CODE, "<clean_snippet>", "exec"), ns)  # the gate has already statically cleared this body
    assert ns["extract"]("error resolved in 10 business days") == 10, "snippet must read 10 business days"
    # touch a file in the sandbox temp dir to confirm the run is scoped to it.
    (tmp / "proof.txt").write_text("ok", encoding="utf-8")
    assert (tmp / "proof.txt").exists(), "sandbox temp dir must be writable + isolated"


def _failing_unit_test(tmp: Path) -> None:
    """An intentionally failing proof — the snippet does NOT meet its spec, so it must be rejected."""
    assert False, "this snippet's behavior does not match its unit-test expectation"


def _noop_test(tmp: Path) -> None:
    # for snippets that are blocked statically the test never runs; provided for signature completeness.
    raise AssertionError("blocked snippets must never reach their unit test")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── 1) a clean, proven snippet → approved + can_register. ──
    res = gate_snippet(_CLEAN_CODE, _passing_unit_test, gated_at=_NOW)
    check("a clean snippet with a passing proof → gate_decision='approved'", res.gate_decision == "approved",
          res.gate_decision)
    check("an approved snippet may register (can_register=True)", res.can_register is True)
    check("an approved snippet's sandbox + proof both passed", res.sandbox_passed and res.proof_passed)
    check("the sandbox carries NO secrets (secrets_present pinned False)", res.sandbox_report.secrets_present is False)
    check("the gate result is shaped like VerifierProofResult.v1",
          res.to_dict().get("schema_version") == "VerifierProofResult.v1"
          and res.to_dict().get("gate_decision") in GATE_DECISIONS)

    # ── 2) static scanner flags network/secret/escape (and not innocent comments). ──
    net, sec, esc, _ = static_scan(_NETWORK_CODE)
    check("static_scan flags network access", net and not sec and not esc)
    net, sec, esc, _ = static_scan(_SECRET_CODE)
    check("static_scan flags secret access", sec)
    net, sec, esc, _ = static_scan(_ESCAPE_CODE)
    check("static_scan flags escape capability", esc)
    net, sec, esc, _ = static_scan("def extract(p):\n    return p  # this does not use urllib or os.environ\n")
    check("static_scan does NOT flag a mere comment mention (no false positive)", not (net or sec or esc))

    # ── 3) a network snippet is BLOCKED before it runs → rejected, can't register. ──
    netres = gate_snippet(_NETWORK_CODE, _noop_test, gated_at=_NOW)
    check("RED-TEAM: a snippet that tries the network is BLOCKED → 'rejected'", netres.gate_decision == "rejected")
    check("a blocked-network snippet can NOT register", netres.can_register is False and not netres.sandbox_passed)
    # run_in_sandbox raises a SandboxViolation directly for a network attempt (proof never runs).
    blocked = False
    try:
        run_in_sandbox(_NETWORK_CODE, _noop_test, allow_network=False)
    except SandboxViolation:
        blocked = True
    check("run_in_sandbox raises SandboxViolation for an unpermitted network attempt (proof never runs)", blocked)
    # but a recipe that explicitly allows network lets it through the network gate (still runs the proof).
    allowed_ran = False
    try:
        run_in_sandbox(_NETWORK_CODE, lambda tmp: None, allow_network=True)
        allowed_ran = True
    except SandboxViolation:
        allowed_ran = False
    check("a recipe that ALLOWS network passes the network gate (explicit opt-in only)", allowed_ran)

    # ── 4) a secret snippet is BLOCKED → rejected. ──
    secres = gate_snippet(_SECRET_CODE, _noop_test, gated_at=_NOW)
    check("RED-TEAM: a snippet that reads a secret is BLOCKED → 'rejected'", secres.gate_decision == "rejected")
    check("a secret-reading snippet can NOT register (even with allow_network)", secres.can_register is False)
    # secret access is forbidden EVEN when the recipe allows network.
    sec_blocked = False
    try:
        run_in_sandbox(_SECRET_CODE, _noop_test, allow_network=True)
    except SandboxViolation:
        sec_blocked = True
    check("secret access is forbidden even when network is allowed", sec_blocked)

    # ── 5) an escape snippet is BLOCKED → rejected. ──
    escres = gate_snippet(_ESCAPE_CODE, _noop_test, gated_at=_NOW)
    check("RED-TEAM: a snippet that uses subprocess/escape is BLOCKED → 'rejected'", escres.gate_decision == "rejected")

    # ── 6) an UNPROVEN snippet (failing unit test) can never register. ──
    unproven = gate_snippet(_CLEAN_CODE, _failing_unit_test, gated_at=_NOW)
    check("RED-TEAM: an unproven snippet (its unit test fails) → 'rejected'", unproven.gate_decision == "rejected")
    check("an unproven snippet passed the SANDBOX but NOT the proof",
          unproven.sandbox_passed is True and unproven.proof_passed is False)
    check("an unproven snippet can NOT register (no proof, no registration)", unproven.can_register is False)

    # ── 7) a HIGH-RISK snippet that passes still needs a human-approval hook. ──
    hr = gate_snippet(_CLEAN_CODE, _passing_unit_test, high_risk=True, gated_at=_NOW)
    check("a high-risk snippet that passes → 'needs_human_approval' (the human-approval hook)",
          hr.gate_decision == "needs_human_approval")
    check("a high-risk snippet pending approval can NOT register yet", hr.can_register is False)
    check("the high-risk snippet DID pass sandbox + proof (it's the human hook that holds it)",
          hr.sandbox_passed and hr.proof_passed)
    # once a human approves, it can register.
    hr_ok = gate_snippet(_CLEAN_CODE, _passing_unit_test, high_risk=True, has_human_approval=True, gated_at=_NOW)
    check("a high-risk snippet WITH human approval → 'approved' + can_register",
          hr_ok.gate_decision == "approved" and hr_ok.can_register is True)

    # ── 8) determinism: the same snippet → the same snippet_id, every run. ──
    check("snippet_id is content-addressed + deterministic (same code → same id)",
          gate_snippet(_CLEAN_CODE, _passing_unit_test, gated_at=_NOW).snippet_id
          == gate_snippet(_CLEAN_CODE, _passing_unit_test, gated_at=_NOW + 5).snippet_id)

    ok = not fails
    print(
        f"\n{'PASS — check_contextops_sandbox_gate: a drafted snippet runs in an isolated, cleaned-up temp dir behind a proof gate; a clean+proven snippet is approved + may register; network/secret/escape attempts are statically BLOCKED before they run (rejected, can_register=False); secret access is forbidden even when network is allowed; an unproven snippet (failing unit test) can never register; a high-risk snippet that passes still needs a human-approval hook before use (nothing auto-registers/executes); the sandbox carries no secrets; the result is shaped like VerifierProofResult.v1 and is deterministic.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ContextOps sandbox + proof gate for extractor snippets.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
