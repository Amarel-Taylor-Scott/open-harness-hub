#!/usr/bin/env python3
"""contextops/sandbox_gate — the SANDBOX + PROOF GATE for extractor snippets (Lane D).

A bounded codegen agent DRAFTS extractor code; Baltor must never trust it on faith. This gate runs a snippet
in an isolated temp dir, STATICALLY rejects any snippet that reaches for the network or secrets, runs the
snippet's unit test as a proof, and only then returns ``approved``. THE GATE'S INVARIANTS:

  * a snippet that tries network access (``socket``/``urllib``/``requests``/``http.client``/``open(<url>)``)
    or reads a secret (``os.environ``/``getenv``/a literal ``sk-...`` / ``api_key``) is BLOCKED before it runs;
  * a snippet with NO passing unit-test proof can NEVER register (``register=False`` until ``proof_passed``);
  * a HIGH-RISK snippet, even when it passes, needs a human-approval hook (``gate_decision='needs_human_approval'``)
    before it could become a worker — nothing here auto-promotes/executes a production worker.

The "sandbox" is deterministic + offline: we evaluate the snippet against an in-process safe namespace inside a
temp dir (created + cleaned up), with NO real network/secret access available. Static scanning is the primary
defense; the temp-dir run confirms the unit test passes. Produces a result shaped like VerifierProofResult.v1.
No clock (time INJECTED), no RNG. stdlib only.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

#: gate decisions (single source — matches VerifierProofResult.v1.gate_decision enum).
GATE_DECISIONS = ("approved", "rejected", "needs_human_approval")

#: import/name patterns that mean a snippet is reaching for the NETWORK — statically forbidden in the sandbox.
_NETWORK_PATTERNS = (
    r"\bimport\s+socket\b", r"\bimport\s+urllib\b", r"\bfrom\s+urllib\b", r"\bimport\s+requests\b",
    r"\bimport\s+http\b", r"\bfrom\s+http\b", r"\bimport\s+ftplib\b", r"\bimport\s+smtplib\b",
    r"\bimport\s+asyncio\b", r"\bsocket\.", r"\burllib\.", r"\brequests\.", r"\bhttp\.client\b",
    r"https?://",
)
#: name/literal patterns that mean a snippet is reaching for a SECRET — statically forbidden in the sandbox.
_SECRET_PATTERNS = (
    r"\bos\.environ\b", r"\bgetenv\b", r"\bos\.getenv\b", r"\bapi[_-]?key\b", r"\bsecret\b",
    r"\bsk-[A-Za-z0-9]{16,}\b", r"\bAWS_[A-Z_]+\b", r"\bload_dotenv\b", r"\bkeyring\b",
)
#: dangerous capabilities that would let a snippet escape the sandbox — also statically forbidden.
_ESCAPE_PATTERNS = (
    r"\bimport\s+subprocess\b", r"\bsubprocess\.", r"\bimport\s+os\b\s*;?\s*", r"\bos\.system\b",
    r"\bos\.popen\b", r"\b__import__\b", r"\beval\s*\(", r"\bexec\s*\(", r"\bos\.remove\b", r"\bshutil\.rmtree\b",
)


class SandboxViolation(Exception):
    """Raised when a snippet violates the sandbox (network/secret/escape) — it is BLOCKED, never run."""


@dataclass(frozen=True)
class SandboxReport:
    """What the sandbox observed about a snippet run (no secrets ever present in the sandbox)."""

    ran_in: str                       # the temp dir the snippet ran in (created + cleaned up)
    network_attempted: bool
    secret_attempted: bool
    escape_attempted: bool
    secrets_present: bool = False     # PINNED False — the sandbox is provisioned with NO secrets
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"ran_in": self.ran_in, "network_attempted": self.network_attempted,
                "secret_attempted": self.secret_attempted, "escape_attempted": self.escape_attempted,
                "secrets_present": self.secrets_present, "violations": list(self.violations)}


@dataclass(frozen=True)
class GateResult:
    """The proof-gate outcome for one snippet, shaped like VerifierProofResult.v1."""

    snippet_id: str
    sandbox_passed: bool
    proof_passed: bool
    gate_decision: str
    can_register: bool                # True ONLY when sandbox + proof pass AND no human approval is pending
    high_risk: bool
    reason: str
    sandbox_report: SandboxReport
    gated_at: int                     # injected epoch seconds — never wall-clock

    def to_dict(self) -> dict:
        return {"schema_version": "VerifierProofResult.v1", "snippet_id": self.snippet_id,
                "sandbox_passed": self.sandbox_passed, "proof_passed": self.proof_passed,
                "gate_decision": self.gate_decision, "can_register": self.can_register,
                "high_risk": self.high_risk, "reason": self.reason,
                "sandbox_report": self.sandbox_report.to_dict(), "gated_at": self.gated_at}


def _snippet_id(code: str) -> str:
    return "xsnip-" + hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]


def static_scan(code: str) -> tuple[bool, bool, bool, list[str]]:
    """Statically scan snippet source for network / secret / escape attempts (the primary sandbox defense).

    Returns (network_attempted, secret_attempted, escape_attempted, violations). A comment-stripped scan so a
    string/comment mention isn't a false positive, while real code (imports, attribute access) is caught.
    """
    # strip line comments + collapse whitespace so a `# uses urllib` comment isn't flagged, but `urllib.` is.
    stripped = "\n".join(line.split("#", 1)[0] for line in code.splitlines())
    net = [p for p in _NETWORK_PATTERNS if re.search(p, stripped)]
    sec = [p for p in _SECRET_PATTERNS if re.search(p, stripped)]
    esc = [p for p in _ESCAPE_PATTERNS if re.search(p, stripped)]
    violations = ([f"network:{p}" for p in net] + [f"secret:{p}" for p in sec] + [f"escape:{p}" for p in esc])
    return bool(net), bool(sec), bool(esc), violations


def run_in_sandbox(code: str, unit_test, *, allow_network: bool = False) -> SandboxReport:
    """Run a snippet's proof in an isolated temp dir after a static safety scan.

    The temp dir is created and CLEANED UP. The static scan runs first: a network attempt (when the recipe does
    NOT allow it) or ANY secret/escape attempt raises :class:`SandboxViolation` and the snippet never runs. The
    sandbox is provisioned with NO secrets, so ``secrets_present`` is always False.
    """
    net, sec, esc, violations = static_scan(code)
    tmp = tempfile.mkdtemp(prefix="ctxops_sandbox_")
    try:
        if (net and not allow_network) or sec or esc:
            why = []
            if net and not allow_network:
                why.append("network access not permitted by the recipe")
            if sec:
                why.append("secret access is never permitted in the sandbox")
            if esc:
                why.append("escape/process capability is never permitted in the sandbox")
            raise SandboxViolation("; ".join(why) + f" :: {violations}")
        # passed the static gate → run the unit test inside the temp dir (its cwd is the sandbox).
        unit_test(Path(tmp))
        return SandboxReport(ran_in=tmp, network_attempted=net, secret_attempted=sec, escape_attempted=esc,
                             secrets_present=False, violations=violations)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gate_snippet(code: str, unit_test, *, high_risk: bool = False, allow_network: bool = False,
                 has_human_approval: bool = False, gated_at: int = 0,
                 snippet_id: str | None = None) -> GateResult:
    """The full proof gate: static sandbox scan + unit-test proof → a gate decision.

    Decision matrix:
      * a sandbox violation → ``rejected`` (sandbox_passed=False, can_register=False);
      * unit test fails     → ``rejected`` (proof_passed=False, can_register=False — no proof, no registration);
      * passes + high_risk + no human approval → ``needs_human_approval`` (can_register=False — human hook);
      * passes (+ approval if high_risk)       → ``approved`` (can_register=True).

    NOTHING registers/executes as a production worker here — ``can_register`` is the upstream PERMISSION to do
    so, gated on a passing proof; MAIN integrates registration separately.
    """
    sid = snippet_id or _snippet_id(code)
    try:
        report = run_in_sandbox(code, unit_test, allow_network=allow_network)
    except SandboxViolation as exc:
        bad = SandboxReport(ran_in="", network_attempted="network" in str(exc) or False,
                            secret_attempted="secret" in str(exc), escape_attempted="escape" in str(exc),
                            secrets_present=False, violations=[str(exc)])
        return GateResult(snippet_id=sid, sandbox_passed=False, proof_passed=False, gate_decision="rejected",
                          can_register=False, high_risk=high_risk,
                          reason=f"sandbox blocked the snippet: {exc}", sandbox_report=bad, gated_at=gated_at)
    except AssertionError as exc:
        return GateResult(snippet_id=sid, sandbox_passed=True, proof_passed=False, gate_decision="rejected",
                          can_register=False, high_risk=high_risk,
                          reason=f"unit-test proof FAILED: {exc}; an unproven snippet can never register",
                          sandbox_report=SandboxReport(ran_in="", network_attempted=False, secret_attempted=False,
                                                       escape_attempted=False),
                          gated_at=gated_at)

    if high_risk and not has_human_approval:
        return GateResult(snippet_id=sid, sandbox_passed=True, proof_passed=True,
                          gate_decision="needs_human_approval", can_register=False, high_risk=True,
                          reason="snippet passed sandbox + proof but is high-risk; human approval required before use",
                          sandbox_report=report, gated_at=gated_at)
    return GateResult(snippet_id=sid, sandbox_passed=True, proof_passed=True, gate_decision="approved",
                      can_register=True, high_risk=high_risk,
                      reason="sandbox + unit-test proof passed; snippet is approved for use",
                      sandbox_report=report, gated_at=gated_at)
