#!/usr/bin/env python3
"""Build the Benchmark Lab adapter catalog.

Turns the owner-provided external benchmark brief (240 LLM / agentic
coding-and-development benchmark tracks, grouped into five families) into a
machine-readable registry so the Benchmark Lab can drive each benchmark with
and WITHOUT the primitive-first route stack (the edge-first composition
program, W7).

Every row is a CANDIDATE benchmark *adapter demand*, not a verified,
runnable benchmark. Names arrive from an external brief; each must pass a
BenchmarkSource -> BenchmarkTask -> adapter verification step before any
score derived from it may be trusted. Rows therefore carry
``candidate=true`` / ``serves_truth=false`` and an evidence-status of
``unverified_intake_names_require_adapter_verification``.

The catalog single-sources three things the plan needs:

* the benchmark families + the tracks the owner enumerated (deduped, stable
  ids derived from the name so a re-run never collapses or renumbers rows);
* the comparison ARMS every task is run under (A0..A8) so baseline vs
  primitive-first is apples-to-apples;
* the DEPTH metric ladder (L1 edge card .. L7 full source) so the headline
  claim can be "solved at contract depth, never read full source".

Reuse, don't rebuild: this catalog is the demand side. The supply side
(BenchmarkSource / BenchmarkTask / Scorecard records + the actual arms) lives
in the benchmark plan and the experiments engine; this file only emits the
typed catalog + a self-test.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    BENCHMARK_LAB_ADAPTER_CATALOG_EVIDENCE_STATUS,
    BENCHMARK_LAB_ADAPTER_CATALOG_MANIFEST_PATH,
    BENCHMARK_LAB_ADAPTER_CATALOG_ROWS_PATH,
    BENCHMARK_LAB_ADAPTER_CATALOG_SOURCE_FAMILY,
    REPO_ROOT,
)

OUT_PATH = _resource(BENCHMARK_LAB_ADAPTER_CATALOG_ROWS_PATH)
MANIFEST_PATH = _resource(BENCHMARK_LAB_ADAPTER_CATALOG_MANIFEST_PATH)

# ── Comparison arms (single source; the plan's A-column) ──────────────────
# Every benchmark task is run under each arm so token/proof/depth deltas are
# measured against the SAME task, not across tasks.
COMPARISON_ARMS: list[dict[str, str]] = [
    {"arm": "A0", "label": "reference", "desc": "human-authored or reference solution (ground truth)"},
    {"arm": "A1", "label": "baseline_agent", "desc": "AI coding agent, no primitive search, no repo search"},
    {"arm": "A2", "label": "agent_repo_search", "desc": "AI coding agent with repo/docs/context search only"},
    {"arm": "A3", "label": "observer_review_only", "desc": "AIDevObserver review-only, no compile"},
    {"arm": "A4", "label": "primitive_template_fill", "desc": "primitive-first deterministic template fill"},
    {"arm": "A5", "label": "candidate_bundle_plandelta", "desc": "CandidateBundle + compact PlanDelta"},
    {"arm": "A6", "label": "deterministic_remix", "desc": "deterministic remix repair (adapter plans)"},
    {"arm": "A7", "label": "llm_micro_repair", "desc": "targeted LLM micro-repair of a near-match route"},
    {"arm": "A8", "label": "source_codegen_fallback", "desc": "source-level codegen fallback (read implementation)"},
]

# ── Disclosure-depth ladder (single source; the nested-doll doctrine) ─────
# The headline claim is not pass/fail; it is "how shallow could the agent stay".
DEPTH_LADDER: list[dict[str, str]] = [
    {"level": "L1_EDGE", "desc": "visible input/output edge + blackbox + effects + proof status"},
    {"level": "L2_CONTRACT", "desc": "input/output schemas, errors, idempotency, auth"},
    {"level": "L3_BEHAVIOR", "desc": "preconditions, postconditions, invariants, minimal examples"},
    {"level": "L4_ROUTE", "desc": "hidden member edges, mutators, substitution slots"},
    {"level": "L5_PROOF", "desc": "fixtures, receipts, coverage, known failures"},
    {"level": "L6_SOURCE_SLICE", "desc": "targeted source/test/doc slices only"},
    {"level": "L7_FULL_SOURCE", "desc": "full implementation / docs (rare, escalation only)"},
]

# ── Metrics every scorecard must carry (single source) ────────────────────
SCORECARD_METRICS: list[str] = [
    "task_completion",
    "unit_test_pass",
    "golden_output_match",
    "planner_input_tokens",
    "planner_output_tokens",
    "source_context_tokens",
    "runtime_llm_tokens",
    "peak_resident_memory_mb",
    "wall_clock_seconds",
    "break_even_transactions",
    "primitive_recall_at_k",
    "route_recall_at_k",
    "false_positive_route_rate",
    "negative_memory_suppression_rate",
    "known_chain_reuse_rate",
    "compile_success",
    "proof_success",
    "contract_violation_count",
    "remix_success",
    "planlock_digest_stability",
    "source_escalation_depth",
    "duplicate_code_avoided",
    "side_effect_declaration_accuracy",
    "security_policy_violation_rate",
]

# ── Families + tracks (the owner's 240-row brief, transcribed) ────────────
# Each family entry: key, title, the primitive-thesis reason it matters, and
# the enumerated track names. Ids are derived from the name (slug + short
# hash) so re-runs are deterministic and never collapse.
FAMILIES: list[dict[str, Any]] = [
    {
        "key": "A_coding_repo_swe_terminal",
        "title": "Coding, repository, software-engineering, and terminal coding",
        "matters": "most direct test of 'does the system avoid rereading/rebuilding code?' — source-escalation depth is the headline metric here",
        "tracks": [
            "HumanEval", "HumanEval+", "MBPP", "MBPP+", "APPS", "CodeContests",
            "Project CodeNet", "MultiPL-E HumanEval", "MultiPL-E MBPP", "HumanEval-X",
            "MBXP", "DS-1000", "ODEX", "CoNaLa", "CoNaLa-mined", "BigCodeBench Full",
            "BigCodeBench Hard", "BigCodeBench Complete", "BigCodeBench Instruct",
            "LiveCodeBench Generation", "LiveCodeBench Self-Repair",
            "LiveCodeBench Code Execution", "LiveCodeBench Test Output Prediction",
            "CRUXEval-I", "CRUXEval-O", "ClassEval", "CoderEval", "DevEval", "BioCoder",
            "SciCode", "CodeXGLUE Clone Detection", "CodeXGLUE Defect Detection",
            "CodeXGLUE Cloze Test", "CodeXGLUE Code Completion Line",
            "CodeXGLUE Code Completion Token", "CodeXGLUE Code Refinement",
            "CodeXGLUE Code Translation", "CodeXGLUE NL Code Search",
            "CodeXGLUE Text-to-Code", "CodeXGLUE Code Summarization",
            "CodeXGLUE Documentation Translation", "CodeSearchNet", "CoSQA",
            "SWE-bench Full", "SWE-bench Lite", "SWE-bench Verified",
            "SWE-bench Multimodal", "SWE-bench Multilingual", "SWE-bench Pro",
            "SWE-smith Python", "SWE-smith Go", "SWE-smith Rust", "SWE-smith C++",
            "SWE Atlas Codebase Q&A", "SWE Atlas Test Writing", "SWE Atlas Refactoring",
            "RepoBench-R", "RepoBench-C", "RepoBench-P", "CrossCodeEval",
            "CrossCodeEval Python", "CrossCodeEval Java", "CrossCodeEval TypeScript",
            "CrossCodeEval C#", "RepoEval", "LongCodeBench Comprehension",
            "LongCodeBench Repair", "Terminal-Bench 1.0", "Terminal-Bench 2.0",
            "Terminal-Bench 2.1", "Terminal-Bench 3.0", "Terminal-Bench Hard",
            "c-CRAB Code Review Agent Benchmark",
            "Code Review Agent Benchmark repair pass", "Defects4J", "BugsInPy",
            "QuixBugs", "ManyBugs", "IntroClass", "Codeflaws",
        ],
    },
    {
        "key": "B_function_calling_tool_use_workflow",
        "title": "Function calling, API/tool use, and workflow-agent",
        "matters": "the primitive card IS a generalized tool contract — these test tool selection, schema compression, argument binding, and abstention",
        "tracks": [
            "BFCL v1", "BFCL v2", "BFCL v3", "BFCL v4 Agentic", "BFCL Simple",
            "BFCL Multiple", "BFCL Parallel", "BFCL Parallel Multiple",
            "BFCL Relevance / No-call", "BFCL Executable Python", "BFCL Executable Java",
            "BFCL Executable JavaScript", "BFCL REST", "BFCL SQL",
            "BFCL Multi-turn Missed Parameter", "BFCL Multi-turn Missed Function",
            "BFCL Memory / Long-context", "BFCL Web-search Agentic",
            "BFCL Format Sensitivity", "API-Bank Planning", "API-Bank Retrieval",
            "API-Bank Calling", "API-Bank Tool Dialogues", "ToolBench / ToolLLM",
            "StableToolBench", "ToolSandbox", "HammerBench", "ToolACE", "APIGen",
            "TRAJECT-Bench", "ToolBench-X", "ToolPrivacyBench", "tau-bench Airline",
            "tau-bench Retail", "tau-bench Banking", "tau-bench Telecom",
            "tau2-bench Airline", "tau2-bench Retail", "tau2-bench Banking",
            "tau2-bench Telecom",
        ],
    },
    {
        "key": "C_web_os_desktop_mobile_company_agent",
        "title": "Web, browser, desktop, mobile, and simulated-company agent",
        "matters": "tests whether primitive routes can replace brittle browser/OS agent wandering with deterministic wrappers",
        "tracks": [
            "WebArena", "VisualWebArena", "MiniWoB++", "WebShop", "Mind2Web",
            "Online-Mind2Web", "WebVoyager", "WebLINX", "WebBench Open",
            "WebBench Full", "BrowserGym WebArena", "BrowserGym VisualWebArena",
            "BrowserGym MiniWoB", "BrowserGym WorkArena", "WorkArena", "WorkArena++",
            "WorkArena Service Catalog", "WorkArena Incident Management",
            "WorkArena Knowledge Base", "TheAgentCompany Full", "TheAgentCompany GitLab",
            "TheAgentCompany OwnCloud", "TheAgentCompany RocketChat",
            "TheAgentCompany Coding Tasks", "TheAgentCompany Communication Tasks",
            "OSWorld Full", "OSWorld File I/O", "OSWorld Office/Spreadsheet",
            "OSWorld Browser-Desktop Handoff", "OSWorld Multi-app Workflow",
            "OSWorld-MCP", "AndroidWorld Full", "AndroidWorld App Tasks",
            "AndroidWorld UI Navigation", "MobileWorld", "AppWorld Normal",
            "AppWorld Challenge", "AppWorld State Tests", "AppWorld Collateral Damage",
            "AgentBench Multi-environment",
        ],
    },
    {
        "key": "D_data_science_ml_document_table_rag_retrieval",
        "title": "Data science, ML engineering, document extraction, tables, RAG, and retrieval",
        "matters": "highest primitive-value family — profiling, schema inference, leakage scans, metric parsing, extraction, and retrieval are rebuilt constantly by real teams",
        "tracks": [
            "MLE-bench Full", "MLE-bench 24h Agent Run", "MLE-bench One-shot Run",
            "MLE-bench Grading Scripts", "DSBench Data Analysis", "DSBench Data Modeling",
            "MLAgentBench General", "MLAgentBench CIFAR-10", "MLAgentBench BabyLM",
            "MLRC-Bench", "PaperBench", "Kaggle Titanic", "Kaggle House Prices",
            "Kaggle Spaceship Titanic", "Kaggle Digit Recognizer",
            "Kaggle NLP Disaster Tweets", "Kaggle Home Credit Default Risk",
            "Kaggle Santander Customer Transaction", "Kaggle Porto Seguro Safe Driver",
            "Kaggle Rossmann Store Sales", "Kaggle M5 Forecasting",
            "Kaggle Mercari Price Suggestion", "Kaggle Quora Insincere Questions",
            "Kaggle Jigsaw Toxic Comment", "Kaggle SIIM-ISIC Melanoma",
            "Kaggle Cassava Leaf Disease", "Kaggle PetFinder.my",
            "Kaggle IEEE-CIS Fraud Detection", "Kaggle Instacart Market Basket",
            "Kaggle Avito Demand Prediction", "DrivenData Competitions",
            "OpenML Benchmark Suites", "AutoML Benchmark", "TabularBench",
            "DocILE KILE", "DocILE LIR", "FUNSD", "CORD", "SROIE", "XFUND", "DocVQA",
            "InfographicVQA", "ChartQA", "PlotQA", "WikiTableQuestions", "TabFact",
            "FeTaQA", "TabMWP", "TableBench", "RAGBench", "BEIR", "MTEB Retrieval",
            "LoTTE", "MIRACL", "RULER", "LongBench v2", "Needle-in-a-Haystack",
        ],
    },
    {
        "key": "E_security_devsecops_incident_infra_agent",
        "title": "Cybersecurity, DevSecOps, incident response, and infrastructure-agent",
        "matters": "defensive use only — tests secure-code detection, patching, incident triage, and whether primitives expose effects/credentials/privacy boundaries",
        "defensive_only": True,
        "tracks": [
            "CyberSecEval 1", "CyberSecEval 2", "CyberSecEval 3", "CyberSecEval 4",
            "CyberSecEval AutoPatchBench", "CyberSecEval Prompt Injection",
            "CyberSecEval Insecure Code", "CyberSecEval Canary Exploit", "Cybench",
            "InterCode-CTF", "NYU CTF Bench", "CTFusion", "CTFTiny", "CTF-Dojo",
            "CyberGym", "3CB", "CTI-REALM", "CyberMetric", "GDM CTF",
            "Cyber Defense Benchmark", "ITBench Kubernetes RCA",
            "ITBench Incident Triage", "Terminal-Bench Security Tasks",
        ],
    },
]

# The 40 tracks the owner said to run first (prioritized ingestion order).
PRIORITY_FIRST_40: list[str] = [
    "BFCL v4 Agentic", "API-Bank Planning", "ToolSandbox", "TRAJECT-Bench",
    "ToolPrivacyBench", "tau-bench Airline", "tau2-bench Telecom",
    "SWE-bench Verified", "SWE-bench Lite", "SWE-bench Multilingual",
    "SWE-bench Multimodal", "SWE Atlas Codebase Q&A", "SWE Atlas Test Writing",
    "SWE Atlas Refactoring", "c-CRAB Code Review Agent Benchmark", "RepoBench-R",
    "RepoBench-C", "CrossCodeEval", "LongCodeBench Comprehension",
    "Terminal-Bench 2.0", "BigCodeBench Hard", "LiveCodeBench Self-Repair",
    "CodeXGLUE NL Code Search", "CodeXGLUE Code Refinement", "OSWorld Full",
    "AppWorld Challenge", "AndroidWorld Full", "WebBench Open", "Online-Mind2Web",
    "WorkArena", "TheAgentCompany Full", "MLE-bench Full", "DSBench Data Analysis",
    "MLAgentBench General", "DocILE KILE", "DocILE LIR", "RAGBench", "BEIR",
    "CyberSecEval AutoPatchBench", "Cyber Defense Benchmark",
]


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _slug(name: str) -> str:
    s = name.lower()
    s = s.replace("+", "plus").replace("#", "sharp").replace("/", " ")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def _row_id(family_key: str, name: str) -> str:
    digest = hashlib.sha256(f"{family_key}::{name}".encode("utf-8")).hexdigest()[:12]
    return f"bench.{_slug(name)}.{digest}"


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    priority = set(PRIORITY_FIRST_40)
    for family in FAMILIES:
        fam_key = str(family["key"])
        for track in family["tracks"]:
            row = {
                "record_type": "benchmark_lab_adapter_demand",
                "benchmark_id": _row_id(fam_key, track),
                "name": track,
                "family_key": fam_key,
                "family_title": family["title"],
                "family_matters": family["matters"],
                "defensive_only": bool(family.get("defensive_only", False)),
                "priority_first_40": track in priority,
                "source": "owner_provided_external_brief",
                "source_family": BENCHMARK_LAB_ADAPTER_CATALOG_SOURCE_FAMILY,
                "evidence_status": BENCHMARK_LAB_ADAPTER_CATALOG_EVIDENCE_STATUS,
                "adapter_state": "unbuilt",
                "next": "build BenchmarkSource adapter -> emit BenchmarkTask fixtures -> verify runnable before any score is trusted",
                "candidate": True,
                "serves_truth": False,
            }
            rows.append(row)
    rows.sort(key=lambda r: (r["family_key"], r["name"]))
    return rows


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, int] = {}
    for row in rows:
        by_family[row["family_key"]] = by_family.get(row["family_key"], 0) + 1
    payload = json.dumps(
        {"rows": rows, "arms": COMPARISON_ARMS, "depth": DEPTH_LADDER, "metrics": SCORECARD_METRICS},
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return {
        "record_type": "benchmark_lab_adapter_catalog_manifest",
        "generated_utc": _today_utc(),
        "generator": "scripts/build_benchmark_lab_adapter_catalog.py",
        "source": "owner_provided_external_brief (240-track benchmark inventory)",
        "source_family": BENCHMARK_LAB_ADAPTER_CATALOG_SOURCE_FAMILY,
        "evidence_status": BENCHMARK_LAB_ADAPTER_CATALOG_EVIDENCE_STATUS,
        "total_tracks": len(rows),
        "family_count": len(FAMILIES),
        "tracks_by_family": by_family,
        "priority_first_40": len(PRIORITY_FIRST_40),
        "comparison_arm_count": len(COMPARISON_ARMS),
        "depth_level_count": len(DEPTH_LADDER),
        "scorecard_metric_count": len(SCORECARD_METRICS),
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        "wired_into": "docs/benchmarks/edge-first-composition-benchmark-plan.md (W7)",
        "boundary": "candidate=true; serves_truth=false; names are unverified intake until an adapter is built and verified",
        "candidate": True,
        "serves_truth": False,
    }


def write_catalog() -> dict[str, Any]:
    rows = build_rows()
    manifest = build_manifest(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def self_test() -> int:
    rows = build_rows()
    # Deterministic ids, no collisions.
    ids = [r["benchmark_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate benchmark_id (id derivation collided)"
    # Names unique within the catalog (the brief had no intentional dupes).
    names = [r["name"] for r in rows]
    assert len(names) == len(set(names)), "duplicate benchmark name in catalog"
    # The brief promised "at least 200"; hold the floor.
    assert len(rows) >= 200, f"expected >=200 tracks, got {len(rows)}"
    # Every family represented.
    fam_keys = {r["family_key"] for r in rows}
    assert len(fam_keys) == len(FAMILIES), "family missing from rows"
    # Truth boundary on every row.
    assert all(r["candidate"] and not r["serves_truth"] for r in rows), "truth boundary violated"
    assert all(r["adapter_state"] == "unbuilt" for r in rows), "no row may claim a built adapter yet"
    # Priority set is a real subset of the catalog names.
    missing = sorted(set(PRIORITY_FIRST_40) - set(names))
    assert not missing, f"priority-40 names absent from catalog: {missing}"
    assert len(PRIORITY_FIRST_40) == len(set(PRIORITY_FIRST_40)) == 40, "priority-40 must be 40 unique names"
    # Arms A0..A8 present and ordered.
    arms = [a["arm"] for a in COMPARISON_ARMS]
    assert arms == [f"A{i}" for i in range(9)], f"arms must be A0..A8, got {arms}"
    # Depth ladder monotonic L1..L7.
    assert [d["level"] for d in DEPTH_LADDER][0] == "L1_EDGE"
    assert [d["level"] for d in DEPTH_LADDER][-1] == "L7_FULL_SOURCE"
    assert len(DEPTH_LADDER) == 7, "depth ladder must be L1..L7"
    # Manifest counts reconcile with rows (no magic values).
    manifest = build_manifest(rows)
    assert manifest["total_tracks"] == len(rows)
    assert sum(manifest["tracks_by_family"].values()) == len(rows)
    # Defensive-only families must be flagged on their rows.
    for family in FAMILIES:
        if family.get("defensive_only"):
            fam_rows = [r for r in rows if r["family_key"] == family["key"]]
            assert fam_rows and all(r["defensive_only"] for r in fam_rows), "defensive-only flag not propagated"
    print(f"OK: benchmark-lab adapter catalog self-test passed ({len(rows)} tracks, {len(FAMILIES)} families).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="validate the catalog without writing")
    parser.add_argument("--write", action="store_true", help="write catalog + manifest to disk")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_catalog()
    print(
        f"wrote {manifest['total_tracks']} tracks across {manifest['family_count']} families -> {OUT_PATH}"
    )
    # Always validate what we just wrote.
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
