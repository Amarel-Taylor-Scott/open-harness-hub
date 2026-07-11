"""check_aidevobserver_launch_readiness -- proof gate for the AIDevObserver launch readiness plan.

This checker does not claim AIDevObserver is production-ready. It verifies that
the launch-readiness contract is candidate-only, covers the required demo/alpha/
public-launch gates, references real proof commands, and that the current
observer proof commands still pass.
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_here_boot = _Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()), _here_boot.parents[1])
if str(_sbc_boot) not in _sys.path:
    _sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
CONTRACT_PATH = _resource("architecture") / "aidevobserver_launch_readiness_contract.json"
DOC_PATH = _resource("docs") / "codex" / "aidevobserver-launch-readiness-and-alpha-plan.md"
EXPECTED_CONTRACT_ID = "aidevobserver.launch_readiness.v0"
EXPECTED_CHECKER = "scripts/check_aidevobserver_launch_readiness.py"
EXPECTED_PHASES = {"demo_ready", "private_alpha", "public_launch"}
EXPECTED_PRIVATE_ALPHA_GATES = {"source_backed_primitive_candidates"}
EXPECTED_SURFACES = {
    "manual_upload",
    "replay_examples",
    "cli_review",
    "claude_project_scaffold",
    "claude_code_mcp",
    "live_pretooluse_hook",
    "vscode_extension_scaffold",
    "local_session_discovery",
}
EXPECTED_METRICS = {
    "finding_precision",
    "top_source_ref_accuracy",
    "top1_source_ref_accuracy",
    "top3_source_ref_accuracy",
    "accepted_reuse_rate",
    "outcome_memory_ranking_effect",
    "tokens_avoided_estimate_basis",
    "false_positive_rate",
    "privacy_redaction_success",
    "runtime_review_latency",
}
EXPECTED_PRIVACY_TERMS = {"No raw private transcript text", "No raw local filesystem paths", "No secrets or PII"}
DOC_TERMS = {
    "demo-ready",
    "Private Alpha",
    "Public / Commercial Launch",
    "serves_truth=false",
    "Accept / Reuse / Dismiss",
    "source-ref precision",
    "source-backed primitive candidates",
    "trycloudflare.com",
}
PROOF_TIMEOUT_SECONDS = 90


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _proof_script_exists(command: str) -> bool:
    parts = command.split()
    if len(parts) < 2:
        return False
    script = parts[1] if parts[0] == "python3" else parts[0]
    return (_resource(script)).exists()


def _run_proof(command: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command.split(),
            # sub-proof commands are SUBSTRATE-relative (python3 scripts/check_X.py) — run them from the dir
            # holding the scripts package (the sentinel dir from the bootstrap), never the monorepo root
            # (REPO), where scripts/ does not exist post-_repos-migration
            cwd=_sbc_boot,
            text=True,
            capture_output=True,
            timeout=PROOF_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # pragma: no cover - defensive proof reporting
        return False, str(exc)
    if result.returncode == 0:
        return True, result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "ok"
    detail = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    return False, detail[-1200:]


def _self_test(run_proofs: bool) -> int:
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' - ' + detail) if detail else ''}")

    ck("contract exists", CONTRACT_PATH.exists(), str(CONTRACT_PATH))
    ck("doc exists", DOC_PATH.exists(), str(DOC_PATH))
    if fails:
        print(f"\nFAIL - aidevobserver launch readiness: {len(fails)} of {checks} assertions failed")
        return 1

    contract = _load_json(CONTRACT_PATH)
    # the CONTRACT is the source of truth for where the doc lives (the context reorg moved it to
    # _repos/aidevobserver/context/); "wired" = the recorded path RESOLVES, never a hardcoded location
    contract_doc_path = REPO / str(contract.get("doc") or "")
    doc_path = contract_doc_path if contract_doc_path.is_file() else DOC_PATH
    doc = doc_path.read_text(encoding="utf-8")

    ck("contract id is expected", contract.get("contract_id") == EXPECTED_CONTRACT_ID)
    ck("contract is candidate status", contract.get("status") == "candidate")
    ck("contract remains candidate-only", contract.get("serves_truth") is False)
    ck("doc path is wired", contract_doc_path.is_file())
    ck("checker path is wired", contract.get("checker") == EXPECTED_CHECKER)

    positioning = contract.get("positioning", {})
    ck("positioning leads with reuse/token savings", "reuse" in positioning.get("lead", "").lower())
    ck("positioning does not lead with risk", "risky-command" in positioning.get("not_lead", ""))
    ck("truth boundary is explicit", "candidate" in positioning.get("truth_boundary", "").lower())

    phases = contract.get("launch_phases", [])
    phase_ids = {phase.get("id") for phase in phases if isinstance(phase, dict)}
    ck("all expected phases are present", EXPECTED_PHASES <= phase_ids, str(sorted(EXPECTED_PHASES - phase_ids)))
    for phase in phases:
        if not isinstance(phase, dict):
            ck("phase is object", False)
            continue
        phase_id = str(phase.get("id") or "<missing>")
        gates = phase.get("required_gates")
        ck(f"phase {phase_id} has label", bool(phase.get("label")))
        ck(f"phase {phase_id} has current_state", phase.get("current_state") in {"mostly_ready", "not_ready"})
        ck(f"phase {phase_id} has multiple gates", isinstance(gates, list) and len(gates) >= 5)
        if phase_id == "private_alpha" and isinstance(gates, list):
            ck(
                "private alpha gates include source-backed primitives",
                EXPECTED_PRIVATE_ALPHA_GATES <= set(gates),
                str(sorted(EXPECTED_PRIVATE_ALPHA_GATES - set(gates))),
            )

    surfaces = set(contract.get("minimum_alpha_surfaces", []))
    ck("minimum alpha surfaces are complete", EXPECTED_SURFACES <= surfaces, str(sorted(EXPECTED_SURFACES - surfaces)))

    metrics = set(contract.get("required_metric_groups", []))
    ck("required metric groups are complete", EXPECTED_METRICS <= metrics, str(sorted(EXPECTED_METRICS - metrics)))

    privacy_rules = contract.get("privacy_rules", [])
    privacy_blob = "\n".join(str(rule) for rule in privacy_rules)
    for term in EXPECTED_PRIVACY_TERMS:
        ck(f"privacy term exists: {term}", term in privacy_blob)
    ck("privacy rules mention public demo mode", "Public demo mode hides local session paths." in privacy_rules)
    ck("privacy rules keep local discovery opt-in", "Local discovery is opt-in and candidate-only." in privacy_rules)

    proof_commands = contract.get("current_proof_commands", [])
    ck("proof commands are listed", isinstance(proof_commands, list) and len(proof_commands) >= 8)
    for command in proof_commands:
        ck(f"proof command script exists: {command}", isinstance(command, str) and _proof_script_exists(command))

    for term in DOC_TERMS:
        ck(f"doc contains {term}", term in doc)
    ck("doc states not production-ready", "not public-launch-ready" in doc or "not production-ready" in doc)
    ck("doc preserves candidate-only status", "`serves_truth=false`" in doc)

    if run_proofs:
        for command in proof_commands:
            ok, detail = _run_proof(command)
            ck(f"proof passes: {command}", ok, detail)

    if fails:
        print(f"\nFAIL - aidevobserver launch readiness: {len(fails)} of {checks} assertions failed")
        return 1

    proof_mode = "with proof commands" if run_proofs else "without running proof commands"
    print(
        "PASS - aidevobserver launch readiness: "
        f"{len(phases)} phases, {len(surfaces)} surfaces, {len(metrics)} metric groups, "
        f"{len(proof_commands)} proof commands; candidate-only; {proof_mode}."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--skip-proof-commands", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        return _self_test(run_proofs=not args.skip_proof_commands)
    return _self_test(run_proofs=not args.skip_proof_commands)


if __name__ == "__main__":
    sys.exit(main())
