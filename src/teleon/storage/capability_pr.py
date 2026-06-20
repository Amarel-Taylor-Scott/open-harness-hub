"""src.teleon.storage.capability_pr — the GitHub-FAMILIAR layer over a capability unit: branches, pull requests,
and "checks" — where the eval/lift gate IS the CI check.

The brain-blast, made concrete: a proposed capability change is a PULL REQUEST. Its diff is the code diff PLUS the
behavior diff (the eval-lift delta). Its "status check" is the governed gate: a fork may MERGE only if it does not
regress (lift_delta >= 0) AND stays within the org policy AND meets the accuracy floor — exactly a CI gate, but on
CAPABILITY CORRECTNESS, not just tests. This is the thing the agentic-git incumbents (GitHub Agent HQ, GitLab Duo,
Azure DevOps) don't have: a familiar PR/checks/merge flow whose check is *does this capability provably lift?*

Rides on any GitBackendPort (internal git OR the client's GitHub/GitLab), so the same PR workflow works wherever the
code lives; governance rides in the sidecar (client code stays clean). Pure + deterministic; serves_truth False —
the PR proposes, the check disposes. Teleon-layer; never imports baltor.
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from src.teleon.storage.git_backend_port import GitBackendPort, LocalGitBackend

#: a fork may merge only if it does not regress capability lift and stays within the accuracy floor.
_LIFT_FLOOR = 0.0          # lift_delta must be >= 0 (no regression)
_ACCURACY_FLOOR = 0.0      # accuracy must be >= this (override per repo)


@dataclass
class CapabilityPullRequest:
    pr_id: str
    unit: str
    branch: str
    title: str
    base_rev: str
    base_code: str
    head_code: str
    eval_result: dict                       # {lift_delta, accuracy, within_policy}
    governance: dict = field(default_factory=dict)
    state: str = "open"                     # open | merged | rejected
    merged_rev: str = ""

    def code_diff(self) -> str:
        return "\n".join(difflib.unified_diff(self.base_code.splitlines(), self.head_code.splitlines(),
                                              lineterm="", fromfile=f"{self.branch}~base", tofile=self.branch))

    def behavior_diff(self) -> dict:
        return {"lift_delta": self.eval_result.get("lift_delta", 0.0),
                "accuracy": self.eval_result.get("accuracy", 0.0)}


class CapabilityRepo:
    """A capability unit presented in familiar git terms (branches / PRs / checks / merge) on any backend."""

    def __init__(self, backend: GitBackendPort | None = None, *, accuracy_floor: float = _ACCURACY_FLOOR) -> None:
        self.backend = backend or LocalGitBackend("internal")
        self.accuracy_floor = accuracy_floor
        self._pr_seq = 0

    def main_head(self, unit: str):
        h = self.backend.history(unit)
        return h[-1] if h else None

    def commit_main(self, unit: str, code: str, *, message: str, now: str):
        return self.backend.commit(unit, code, message=message, now=now)

    def open_pr(self, unit: str, *, branch: str, head_code: str, eval_result: dict, title: str = "",
                governance: dict | None = None) -> CapabilityPullRequest:
        head = self.main_head(unit)
        base_rev = head.rev if head else ""
        base_code = self.backend.read(unit, base_rev) if head else ""
        self._pr_seq += 1
        return CapabilityPullRequest(
            pr_id=f"PR-{self._pr_seq}", unit=unit, branch=branch, title=title or f"update {unit}",
            base_rev=base_rev, base_code=base_code, head_code=head_code,
            eval_result=dict(eval_result), governance=dict(governance or {}))

    def checks(self, pr: CapabilityPullRequest) -> dict:
        """The 'CI' status check: the governed eval/lift gate. A fork passes only if it provably does not regress,
        stays within policy, and meets the accuracy floor."""
        ev = pr.eval_result
        reasons = []
        lift_ok = float(ev.get("lift_delta", 0.0)) >= _LIFT_FLOOR
        policy_ok = bool(ev.get("within_policy", True))
        acc_ok = float(ev.get("accuracy", 0.0)) >= self.accuracy_floor
        if not lift_ok:
            reasons.append(f"capability REGRESSES (lift_delta {ev.get('lift_delta')} < {_LIFT_FLOOR})")
        if not policy_ok:
            reasons.append("fork is OUT of org policy")
        if not acc_ok:
            reasons.append(f"accuracy {ev.get('accuracy')} < floor {self.accuracy_floor}")
        passed = lift_ok and policy_ok and acc_ok
        return {"passed": passed, "check": "teleon/eval-lift-gate",
                "summary": "capability provably lifts within policy" if passed else "; ".join(reasons),
                "reasons": reasons, "serves_truth": False}

    def merge(self, pr: CapabilityPullRequest, *, now: str) -> dict:
        """Merge the PR — ONLY if its checks pass (a fork that doesn't lift within policy cannot merge)."""
        chk = self.checks(pr)
        if not chk["passed"]:
            pr.state = "rejected"
            return {"merged": False, "pr_id": pr.pr_id, "checks": chk, "serves_truth": False}
        ref = self.backend.commit(pr.unit, pr.head_code, message=f"merge {pr.pr_id}: {pr.title}", now=now)
        if pr.governance:
            self.backend.attach_governance(pr.unit, ref.rev, pr.governance)
        pr.state = "merged"
        pr.merged_rev = ref.rev
        return {"merged": True, "pr_id": pr.pr_id, "merged_rev": ref.rev, "backend": self.backend.platform,
                "checks": chk, "governance_sidecar": dict(pr.governance), "serves_truth": False}

    def pr_view(self, pr: CapabilityPullRequest) -> dict:
        """Everything a familiar PR page would show."""
        chk = self.checks(pr)
        return {"pr_id": pr.pr_id, "unit": pr.unit, "branch": pr.branch, "title": pr.title, "state": pr.state,
                "base_rev": pr.base_rev, "checks": chk, "behavior_diff": pr.behavior_diff(),
                "code_diff": pr.code_diff(), "governance": pr.governance, "serves_truth": False}
