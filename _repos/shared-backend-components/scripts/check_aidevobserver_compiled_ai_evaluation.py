"""check_aidevobserver_compiled_ai_evaluation -- proof gate for the AIDevObserver compiled-AI benchmark contract.

The contract is intentionally candidate-only. This checker verifies that the benchmark design covers the required
domains, industries, middleware primitives, token accounting, clean counterexamples, and security cases, then runs the
synthetic smoke sessions through the real AIDevObserver review engine.
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
import sys
from pathlib import Path
from typing import Any


REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.observer.review import review_session  # noqa: E402


CONTRACT_PATH = _resource("architecture") / "aidevobserver_compiled_ai_evaluation_contract.json"
PROMPT_PATH = REPO / ".codex" / "prompts" / "aidevobserver-compiled-ai-evaluation.md"
DOC_PATH = _resource("docs") / "codex" / "aidevobserver-compiled-ai-evaluation-plan.md"

EXPECTED_CONTRACT_ID = "aidevobserver.compiled_ai_evaluation.v0"
EXPECTED_CHECKER = "scripts/check_aidevobserver_compiled_ai_evaluation.py"
EXPECTED_PROMPT = ".codex/prompts/aidevobserver-compiled-ai-evaluation.md"
EXPECTED_DOC = "docs/codex/aidevobserver-compiled-ai-evaluation-plan.md"
MIN_FIXTURE_COUNT = 12
MIN_INDUSTRY_COUNT = 10
MAX_CLEAN_SMOKE_FINDINGS = 1

REQUIRED_SUITES = {
    "programming_session_review",
    "middleware_registry_search",
    "token_economics",
    "security_static_safety",
    "compiled_route_comparison",
    "cross_domain_programming_coverage",
}

REQUIRED_DOMAINS = {
    "frontend",
    "backend",
    "software_engineering",
    "data_science",
    "data_engineering",
    "devops",
    "security",
    "document_intelligence",
    "workflow_automation",
    "media_pipeline",
}

REQUIRED_MIDDLEWARE = {
    "observer.session.parse_transcript",
    "observer.finding.rank_by_confidence",
    "observer.token.estimate_usage",
    "observer.token.compare_model_vs_tool_route",
    "observer.security.pattern_scan",
    "observer.agentic.detect_loop_shape",
    "registry.hybrid_search",
    "registry.primitive_match",
    "registry.reinvention_guard",
    "registry.dependency_graph_query",
    "deterministic.rg_search",
    "deterministic.ast_symbol_lookup",
    "deterministic.planlock_compile_check",
    "deterministic.json_schema_validate",
    "teleon.candidate_bundle.render_compact",
    "teleon.plan_delta.validate",
    "teleon.ledger.record_candidate_event",
}

REQUIRED_TOKEN_FIELDS = {
    "session_id",
    "baseline_input_tokens",
    "baseline_output_tokens",
    "observer_middleware_tokens",
    "deterministic_tool_calls",
    "estimated_tokens_saved",
    "route_taken",
    "repeat_count_for_break_even",
}

PROMPT_TERMS = {
    "serves_truth",
    "token_accounting",
    "clean_counterexample",
    "observer_middleware_path",
    "registry.hybrid_search",
}

DOC_TERMS = {
    "AIDevObserver",
    "Teleon",
    "Baltor",
    "OpenHubForAI",
    "Test-Of-Tests",
}


def _load_contract() -> dict[str, Any]:
    with CONTRACT_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _as_ids(items: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("id")) for item in items}


def _run_smoke_session(smoke: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    report = review_session(smoke["messages"])
    repeated = review_session(smoke["messages"])
    findings = report["report"]
    found_types = {finding["type"] for finding in findings}

    if report.get("serves_truth") is not False:
        errors.append("review report must remain serves_truth=false")
    if repeated["report"] != findings:
        errors.append("review report must be deterministic on replay")
    for finding in findings:
        if finding.get("serves_truth") is not False or finding.get("candidate") is not True:
            errors.append("every smoke finding must be candidate=true and serves_truth=false")
            break

    for expected in smoke.get("expected_finding_types", []):
        if expected not in found_types:
            errors.append(f"missing expected finding type {expected!r}")

    expected_any = set(smoke.get("expected_finding_types_any_of", []))
    if expected_any and not (found_types & expected_any):
        errors.append(f"missing any expected finding type from {sorted(expected_any)}")

    max_findings = smoke.get("max_findings")
    if max_findings is not None and len(findings) > int(max_findings):
        errors.append(f"expected at most {max_findings} findings, got {len(findings)}")

    return not errors, errors


def _self_test() -> int:
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' - ' + detail) if detail else ''}")

    ck("contract file exists", CONTRACT_PATH.exists(), str(CONTRACT_PATH))
    ck("prompt file exists", PROMPT_PATH.exists(), str(PROMPT_PATH))
    ck("doc file exists", DOC_PATH.exists(), str(DOC_PATH))
    if fails:
        print(f"\nFAIL - missing required files: {len(fails)} of {checks} assertions failed")
        return 1

    contract = _load_contract()
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
    doc_text = DOC_PATH.read_text(encoding="utf-8")

    ck("contract id is expected", contract.get("contract_id") == EXPECTED_CONTRACT_ID)
    ck("contract remains candidate-only", contract.get("serves_truth") is False)
    ck("checker path is wired", contract.get("checker") == EXPECTED_CHECKER)
    ck("prompt path is wired", contract.get("prompt") == EXPECTED_PROMPT)
    ck("doc path is wired", contract.get("doc") == EXPECTED_DOC)
    ck("paper URL is recorded", contract.get("inspiration", {}).get("paper_url") == "https://arxiv.org/abs/2604.05150")

    suite_ids = _as_ids(contract.get("benchmark_suites", []))
    ck("all required benchmark suites exist", REQUIRED_SUITES <= suite_ids, str(sorted(REQUIRED_SUITES - suite_ids)))

    declared_domains = set(contract.get("required_engineering_domains", []))
    ck("all required domains are declared", REQUIRED_DOMAINS <= declared_domains,
       str(sorted(REQUIRED_DOMAINS - declared_domains)))

    declared_middleware = set(contract.get("required_middleware_primitives", []))
    ck("all required middleware primitives are declared", REQUIRED_MIDDLEWARE <= declared_middleware,
       str(sorted(REQUIRED_MIDDLEWARE - declared_middleware)))

    fixtures = contract.get("use_case_fixtures_to_generate", [])
    industries = {fixture.get("industry") for fixture in fixtures}
    fixture_domains = {fixture.get("engineering_domain") for fixture in fixtures}
    fixture_primitive_union = {
        primitive
        for fixture in fixtures
        for primitive in fixture.get("registry_primitives", [])
    }

    ck("fixture count meets minimum", len(fixtures) >= MIN_FIXTURE_COUNT, f"got {len(fixtures)}")
    ck("industry count meets minimum", len(industries) >= MIN_INDUSTRY_COUNT, f"got {len(industries)}")
    ck("fixtures cover every required domain", REQUIRED_DOMAINS <= fixture_domains,
       str(sorted(REQUIRED_DOMAINS - fixture_domains)))
    ck("fixtures exercise middleware primitives", len(fixture_primitive_union & REQUIRED_MIDDLEWARE) >= MIN_INDUSTRY_COUNT,
       f"overlap {len(fixture_primitive_union & REQUIRED_MIDDLEWARE)}")

    for fixture in fixtures:
        fixture_id = fixture.get("id", "<missing>")
        ck(f"fixture {fixture_id} has id", bool(fixture.get("id")))
        ck(f"fixture {fixture_id} has industry", bool(fixture.get("industry")))
        ck(f"fixture {fixture_id} has engineering domain", fixture.get("engineering_domain") in REQUIRED_DOMAINS)
        ck(f"fixture {fixture_id} has task", bool(fixture.get("task")))
        ck(f"fixture {fixture_id} has expected themes", bool(fixture.get("expected_observer_themes")))
        ck(f"fixture {fixture_id} has registry primitives", bool(fixture.get("registry_primitives")))
        ck(f"fixture {fixture_id} has token test", bool(fixture.get("token_test")))

    clean = contract.get("clean_counterexamples_required", [])
    security = contract.get("security_cases_required", [])
    ck("clean counterexamples are specified", len(clean) >= 3, f"got {len(clean)}")
    ck("security cases are specified", len(security) >= 5, f"got {len(security)}")

    token_fields = set(contract.get("token_accounting_schema", {}).get("required_fields", []))
    ck("token accounting fields are specified", REQUIRED_TOKEN_FIELDS <= token_fields,
       str(sorted(REQUIRED_TOKEN_FIELDS - token_fields)))

    acceptance_laws = " ".join(contract.get("acceptance_laws", []))
    ck("acceptance laws include candidate-only truth boundary",
       "candidate" in acceptance_laws and "promotion" in acceptance_laws)

    missing_prompt_terms = sorted(term for term in PROMPT_TERMS if term not in prompt_text)
    missing_doc_terms = sorted(term for term in DOC_TERMS if term not in doc_text)
    ck("prompt includes required fixture terms", not missing_prompt_terms, str(missing_prompt_terms))
    ck("doc includes required product terms", not missing_doc_terms, str(missing_doc_terms))

    smoke_sessions = contract.get("smoke_sessions", [])
    ck("smoke sessions exist", len(smoke_sessions) >= 3, f"got {len(smoke_sessions)}")
    for smoke in smoke_sessions:
        ok, errors = _run_smoke_session(smoke)
        ck(f"smoke session {smoke.get('id', '<missing>')} passes real review engine", ok, "; ".join(errors))

    clean_smoke = next((smoke for smoke in smoke_sessions if smoke.get("id") == "smoke_clean_novel_work"), None)
    if clean_smoke:
        clean_report = review_session(clean_smoke["messages"])
        ck("clean smoke remains quiet",
           len(clean_report["report"]) <= MAX_CLEAN_SMOKE_FINDINGS,
           f"got {len(clean_report['report'])}")

    if fails:
        print(f"\nFAIL - AIDevObserver compiled-AI evaluation contract: {len(fails)} of {checks} assertions failed")
        return 1

    print(
        "PASS - AIDevObserver compiled-AI evaluation contract: "
        f"{len(fixtures)} fixtures, {len(industries)} industries, {len(fixture_domains)} domains, "
        f"{len(smoke_sessions)} smoke sessions through review_session; {checks} assertions; serves_truth=false."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.parse_args()
    return _self_test()


if __name__ == "__main__":
    sys.exit(main())
