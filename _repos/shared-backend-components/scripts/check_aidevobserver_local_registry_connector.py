#!/usr/bin/env python3
"""Proof gate for the AIDevObserver local registry connector.

The connector is a minimum private-alpha slice: it indexes an explicit local
repo root into candidate-only source refs for symbols, docs, and scripts. This
checker uses a synthetic repo fixture and verifies that no absolute path or
private transcript content is emitted.
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
import os
import shutil
import sys
import tempfile
from pathlib import Path


REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
sys.path.insert(0, str(REPO))

from scripts._config import AIDEVOBSERVER_PUBLIC_DEMO_ENV  # noqa: E402
from src.teleon.observer.local_registry_connector import (  # noqa: E402
    cached_index_local_repo,
    clear_local_repo_index_cache,
    index_local_repo,
    primitive_candidates_from_local_repo,
    search_local_repo,
)
from src.teleon.observer.registry_search import (  # noqa: E402
    LOCAL_REGISTRY_ENV,
    enrich_report_with_local_registry,
    registry_search_response,
    source_ref_keys_from_value,
)


def _reuse_card(hit: dict) -> dict:
    return hit.get("reuse_card") if isinstance(hit.get("reuse_card"), dict) else {}


def _hit_source_kind(hit: dict) -> str:
    card = _reuse_card(hit)
    return str(card.get("source_kind") or hit.get("source_kind") or "")


def _is_local_registry_hit(hit: dict) -> bool:
    if _hit_source_kind(hit) in {"first_party_repo_record", "local_repo_record"}:
        return True
    source_ref = hit.get("source_ref") if isinstance(hit.get("source_ref"), dict) else {}
    card_ref = _reuse_card(hit).get("source_ref") if isinstance(_reuse_card(hit).get("source_ref"), dict) else {}
    return str(source_ref.get("registry") or card_ref.get("registry") or "") == "local_repo"


def _reuse_card_has_contract(hit: dict) -> bool:
    card = _reuse_card(hit)
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    return bool(contract.get("input") and contract.get("output"))


def _reuse_card_has_blackbox_or_edges(hit: dict) -> bool:
    card = _reuse_card(hit)
    blackbox = card.get("blackbox")
    if isinstance(blackbox, dict) and (blackbox.get("input_edge") or blackbox.get("output_edge")):
        return True
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    return bool(contract.get("input") and contract.get("output"))


def _write_fixture(root: Path) -> None:
    (root / "utils").mkdir(parents=True)
    (root / "utils" / "csv.py").write_text(
        "\n".join([
            "MAX_ROWS = 5000",
            "",
            "def read_rows(path: str, *, delimiter: str = ',') -> list[dict[str, str]]:",
            "    \"\"\"Read CSV rows with a header and max-row guard.\"\"\"",
            "    return []",
            "",
            "class Importer:",
            "    \"\"\"Importer facade for tabular files.\"\"\"",
            "",
            "    def import_file(self, path: str) -> list[dict[str, str]]:",
            "        \"\"\"Import a CSV-compatible file.\"\"\"",
            "        return read_rows(path)",
        ]),
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "Importer guide: CSV import uses utils.csv.read_rows. MAX_ROWS is defined in utils/csv.py.",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        json.dumps({"scripts": {"import:check": "python -m importer.check", "test": "pytest"}}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        "\n".join([
            "[project.scripts]",
            'importer-check = "importer.cli:main"',
        ]),
        encoding="utf-8",
    )
    (root / "CLAUDE.md").write_text(
        "\n".join([
            "# Project Instructions",
            "",
            "Before building a parser or workflow, ask AIDevObserver to find reuse in the primitive database.",
        ]),
        encoding="utf-8",
    )
    (root / "session-log.md").write_text(
        "Session memory: the importer review found an existing CSV helper and a reusable review command.",
        encoding="utf-8",
    )
    (root / "hooks.md").write_text(
        "Hook policy: use AIDevObserver PreToolUse advice as non-blocking reuse guidance.",
        encoding="utf-8",
    )
    (root / "skills" / "data-ingestion").mkdir(parents=True)
    (root / "skills" / "data-ingestion" / "SKILL.md").write_text(
        "# Data ingestion skill\nUse schema gates, CSV helpers, and artifact refs before writing new importers.",
        encoding="utf-8",
    )
    (root / "commands").mkdir()
    (root / "commands" / "review-session.md").write_text(
        "# /review-session\nRun AIDevObserver on the latest AI coding transcript and return ranked findings.",
        encoding="utf-8",
    )
    (root / "hooks").mkdir()
    (root / "hooks" / "pretooluse-aidevobserver.md").write_text(
        "# AIDevObserver PreToolUse\nNon-blocking advisory hook for reinvention and wasted context.",
        encoding="utf-8",
    )
    (root / "mcp").mkdir()
    (root / "mcp" / "aidevobserver.md").write_text(
        "# AIDevObserver MCP\nExpose list_sessions, review_session, and live_review to Claude Code.",
        encoding="utf-8",
    )
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"command": f"python3 {root}/scripts/aidevobserver_hook.py"}]}]}}),
        encoding="utf-8",
    )
    (root / "_reference").mkdir()
    (root / "_reference" / "private.py").write_text(
        "def should_not_index():\n    return 'skip reference repo'\n",
        encoding="utf-8",
    )
    (root / ".agent").mkdir()
    (root / ".agent" / "scratch.py").write_text(
        "def scratch_helper():\n    return 'skip agent scratch'\n",
        encoding="utf-8",
    )
    (root / "archive").mkdir()
    (root / "archive" / "README.md").write_text(
        "Historical README that should not become a launch primitive candidate.",
        encoding="utf-8",
    )


def _assert_no_absolute_path(serialized: str, root: Path, fails: list[str]) -> None:
    if str(root) in serialized:
        fails.append("connector leaked absolute fixture path")
    if tempfile.gettempdir() in serialized:
        fails.append("connector leaked temp directory prefix")


def _self_test() -> int:
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' - ' + detail) if detail else ''}")

    root = Path(tempfile.mkdtemp(prefix="ado_local_registry_"))
    try:
        _write_fixture(root)
        records = index_local_repo(root)
        serialized_records = json.dumps(records, sort_keys=True)

        ck("records generated", len(records) >= 6, str(len(records)))
        ck("all rows are candidate-only", all(r.get("candidate") is True and r.get("serves_truth") is False for r in records))
        ck("all rows have local_repo source refs", all((r.get("source_ref") or {}).get("registry") == "local_repo" for r in records))
        ck("records use repo-relative paths", all(not str(r.get("path", "")).startswith("/") for r in records))
        ck("reference repos are skipped", "should_not_index" not in serialized_records)
        ck("agent scratch dirs are skipped", "scratch_helper" not in serialized_records)
        ck("claude settings are skipped", ".claude" not in serialized_records and "aidevobserver_hook.py" not in serialized_records)
        ck("archive dirs are skipped", "Historical README" not in serialized_records)
        _assert_no_absolute_path(serialized_records, root, fails)

        clear_local_repo_index_cache()
        cached_once = cached_index_local_repo(root)
        (root / "late.py").write_text(
            "def late_added_helper() -> str:\n"
            "    return 'new after cache fill'\n",
            encoding="utf-8",
        )
        cached_stale = cached_index_local_repo(root)
        clear_local_repo_index_cache()
        cached_refreshed = cached_index_local_repo(root)
        ck("cached index avoids immediate repeated repo indexing",
           "late_added_helper" not in json.dumps(cached_stale, sort_keys=True),
           json.dumps(cached_stale, sort_keys=True))
        ck("clearing the cached index refreshes local repo records",
           "late_added_helper" in json.dumps(cached_refreshed, sort_keys=True),
           json.dumps(cached_refreshed, sort_keys=True))
        ck("cached index preserves candidate-only rows",
           all(r.get("serves_truth") is False for r in cached_once + cached_refreshed))

        csv_hits = search_local_repo("agent is creating parse_csv() in importer.py", root)
        csv_blob = json.dumps(csv_hits, sort_keys=True)
        ck("CSV parser query finds existing read_rows helper", "read_rows" in csv_blob, csv_blob)
        ck("CSV match carries source_ref", any((h.get("source_ref") or {}).get("name") == "read_rows" for h in csv_hits))
        _assert_no_absolute_path(csv_blob, root, fails)

        constant_hits = search_local_repo("find where MAX_ROWS is defined", root)
        constant_blob = json.dumps(constant_hits, sort_keys=True)
        ck("constant query finds MAX_ROWS", "MAX_ROWS" in constant_blob, constant_blob)
        ck("constant match is a python_constant", any(h.get("kind") == "python_constant" for h in constant_hits))
        _assert_no_absolute_path(constant_blob, root, fails)

        script_hits = search_local_repo("run importer check script", root)
        script_blob = json.dumps(script_hits, sort_keys=True)
        ck("script query finds package or pyproject command", "import:check" in script_blob or "importer-check" in script_blob, script_blob)
        ck("script rows stay candidate-only", all(h.get("serves_truth") is False for h in script_hits))
        _assert_no_absolute_path(script_blob, root, fails)

        docs_hits = search_local_repo("where is the importer guide for csv import", root)
        docs_blob = json.dumps(docs_hits, sort_keys=True)
        ck("docs query finds README snippet", "README.md" in docs_blob, docs_blob)
        _assert_no_absolute_path(docs_blob, root, fails)

        kinds = {r.get("kind") for r in records}
        ck("CLAUDE.md indexes as project context", "claude_project_context" in kinds, str(kinds))
        ck("skills/SKILL.md indexes as a Claude skill", "claude_skill" in kinds, str(kinds))
        ck("commands/*.md indexes as a Claude command", "claude_command" in kinds, str(kinds))
        ck("hooks/*.md indexes as a hook doc", "claude_hook_doc" in kinds, str(kinds))
        ck("mcp/*.md indexes as an MCP connector doc", "mcp_connector_doc" in kinds, str(kinds))
        ck("session-log.md indexes as session memory", "session_memory_doc" in kinds, str(kinds))

        command_hits = search_local_repo("review latest Claude Code session command", root)
        command_blob = json.dumps(command_hits, sort_keys=True)
        ck("command query finds /review-session doc", "review_session" in command_blob or "review-session" in command_blob, command_blob)
        mcp_hits = search_local_repo("Claude Code MCP review_session tool", root)
        mcp_blob = json.dumps(mcp_hits, sort_keys=True)
        ck("MCP query finds AIDevObserver MCP doc", "mcp_connector_doc" in mcp_blob and "aidevobserver" in mcp_blob, mcp_blob)
        _assert_no_absolute_path(command_blob + mcp_blob, root, fails)

        primitive_candidates = primitive_candidates_from_local_repo(root)
        primitive_blob = json.dumps(primitive_candidates, sort_keys=True)
        ck("source-backed primitive candidates generated", len(primitive_candidates) >= 4, str(len(primitive_candidates)))
        ck("primitive candidates are drafts, not opportunities",
           all(p.get("record_type") == "primitive_draft" for p in primitive_candidates), primitive_blob)
        ck("primitive candidates are source-backed",
           all(p.get("source_evidence_status") == "source_backed" for p in primitive_candidates), primitive_blob)
        ck("read_rows primitive candidate exists", "read_rows" in primitive_blob, primitive_blob)
        read_rows_candidate = next(
            (p for p in primitive_candidates if (p.get("source_ref") or {}).get("name") == "read_rows"),
            {},
        )
        read_rows_contract = read_rows_candidate.get("contract") or {}
        ck("read_rows primitive has annotation-derived input contract",
           "path:str" in str(read_rows_contract.get("input")) and "delimiter:str" in str(read_rows_contract.get("input")),
           str(read_rows_contract))
        ck("read_rows primitive has annotation-derived output contract",
           "list[dict[str,str]]" == str(read_rows_contract.get("output")),
           str(read_rows_contract))
        ck("read_rows primitive exposes callable surface",
           bool(read_rows_candidate.get("callable_surface", {}).get("signature")),
           str(read_rows_candidate))
        ck("read_rows primitive exposes source fingerprints",
           all((read_rows_candidate.get("source_fingerprints") or {}).get(k) for k in ("source", "contract", "primitive_record")),
           str(read_rows_candidate.get("source_fingerprints")))
        ck("read_rows primitive exposes black-box functionality",
           bool((read_rows_candidate.get("blackbox") or {}).get("does"))
           and (read_rows_candidate.get("blackbox") or {}).get("input_edge")
           and (read_rows_candidate.get("blackbox") or {}).get("output_edge"),
           str(read_rows_candidate.get("blackbox")))
        mutation_ids = {m.get("id") for m in read_rows_candidate.get("edge_mutation_options") or []}
        ck("read_rows primitive stores deterministic edge mutation options",
           {"scalar_to_sequence", "output_field_wrapper"} <= mutation_ids,
           str(read_rows_candidate.get("edge_mutation_options")))
        ck("local primitive schema is versioned",
           bool(read_rows_candidate.get("candidate_schema")),
           str(read_rows_candidate))
        ck("primitive candidates remain candidate-only",
           all(p.get("serves_truth") is False and p.get("public_export_allowed") is False for p in primitive_candidates),
           primitive_blob)
        first_kinds = [(p.get("source_ref") or {}).get("kind") for p in primitive_candidates[:8]]
        ck("primitive candidates include Claude setup surfaces before broad docs",
           any(kind in {"claude_project_context", "claude_command", "claude_skill", "mcp_connector_doc"} for kind in first_kinds),
           str(primitive_candidates[:8]))
        ck("primitive candidates still include source-backed code symbols",
           any((p.get("source_ref") or {}).get("kind") in {"python_function", "python_method", "python_class", "python_constant"} for p in primitive_candidates),
           str(primitive_candidates[:8]))
        ck("Claude command primitive candidate has workflow contract",
           "WorkflowTemplateRef" in primitive_blob,
           primitive_blob)
        ck("MCP connector primitive candidate has connector contract",
           "MCPConnectorProfileRef" in primitive_blob,
           primitive_blob)
        ck("archive primitive candidates are skipped", "archive/README.md" not in primitive_blob, primitive_blob)
        _assert_no_absolute_path(primitive_blob, root, fails)

        prev_registry_env = os.environ.get(LOCAL_REGISTRY_ENV)
        prev_public_demo_env = os.environ.get(AIDEVOBSERVER_PUBLIC_DEMO_ENV)
        try:
            os.environ.pop(LOCAL_REGISTRY_ENV, None)
            os.environ[AIDEVOBSERVER_PUBLIC_DEMO_ENV] = "1"
            st_off, off = registry_search_response("parse csv", str(root))
            ck("shared registry adapter disables local repo search in public-demo mode",
               st_off == 200
               and off.get("local_registry_enabled") is False
               and all(not _is_local_registry_hit(hit) for hit in off.get("hits", [])),
               json.dumps(off, sort_keys=True))

            os.environ.pop(AIDEVOBSERVER_PUBLIC_DEMO_ENV, None)
            os.environ[LOCAL_REGISTRY_ENV] = "1"
            st_on, on = registry_search_response("agent is creating parse_csv in importer.py", str(root))
            on_blob = json.dumps(on, sort_keys=True)
            ck("shared registry adapter returns local hits when opted in",
               st_on == 200 and on.get("local_registry_enabled") is True and "read_rows" in on_blob,
               on_blob)
            ck("shared registry adapter adds reuse cards with contracts",
               any(_reuse_card_has_contract(hit) for hit in on.get("hits", [])),
               on_blob)
            ck("shared registry adapter adds black-box edges to reuse cards",
               any(_reuse_card_has_blackbox_or_edges(hit) for hit in on.get("hits", [])),
               on_blob)
            _assert_no_absolute_path(on_blob, root, fails)

            st_edge, edge = registry_search_response(
                "batch parse many csv files into row lists",
                str(root),
                requested_input="list[str]",
                requested_output="list[list[dict[str,str]]]",
            )
            edge_blob = json.dumps(edge, sort_keys=True)
            read_edge_hit = next((h for h in edge.get("hits", []) if (h.get("source_ref") or {}).get("name") == "read_rows"), {})
            read_edge_fit = read_edge_hit.get("edge_fit") or {}
            read_edge_card = read_edge_hit.get("reuse_card") or {}
            ck("edge-aware search ranks scalar helper as deterministic batch mutation",
               st_edge == 200
               and read_edge_fit.get("fit_class") == "deterministic_edit_match"
               and "scalar_to_sequence" in (read_edge_fit.get("required_mutations") or []),
               edge_blob)
            ck("edge-aware reuse card explains required mutation to the LLM",
               "scalar_to_sequence" in ((read_edge_card.get("match_reason") or {}).get("required_mutations") or [])
               and (read_edge_card.get("input_edge") or {}).get("contract"),
               edge_blob)

            base_report = {
                "report": [{
                    "type": "reinvention",
                    "message": "This looks like a solved problem.",
                    "evidence": "Creating parse_csv() in importer.py",
                    "suggestion": "reuse the existing component",
                    "candidate": True,
                    "serves_truth": False,
                }],
                "summary": {"findings": 1},
                "serves_truth": False,
            }
            enriched = enrich_report_with_local_registry(base_report, root_value=root)
            enriched_blob = json.dumps(enriched, sort_keys=True)
            ck("shared registry adapter enriches reports with local source refs",
               (enriched.get("local_registry") or {}).get("hits_attached", 0) > 0 and "local_repo" in enriched_blob,
               enriched_blob)
            ck("shared registry adapter enriches reports with LLM-readable reuse cards",
               bool((enriched.get("report") or [{}])[0].get("reuse_cards")),
               enriched_blob)
            keys = source_ref_keys_from_value((enriched.get("report") or [{}])[0].get("source_ref"))
            ck("shared registry adapter derives metadata-only source-ref keys",
               len(keys) >= 1 and all(key.startswith("src_") for key in keys),
               str(keys))
            _assert_no_absolute_path(enriched_blob, root, fails)
        finally:
            if prev_registry_env is None:
                os.environ.pop(LOCAL_REGISTRY_ENV, None)
            else:
                os.environ[LOCAL_REGISTRY_ENV] = prev_registry_env
            if prev_public_demo_env is None:
                os.environ.pop(AIDEVOBSERVER_PUBLIC_DEMO_ENV, None)
            else:
                os.environ[AIDEVOBSERVER_PUBLIC_DEMO_ENV] = prev_public_demo_env

    finally:
        shutil.rmtree(root, ignore_errors=True)

    if fails:
        print(f"\nFAIL - aidevobserver local registry connector: {len(fails)} of {checks} assertions failed")
        return 1
    print(
        "PASS - aidevobserver local registry connector: "
        f"{checks} assertions; repo-relative symbol/doc/script candidate source_refs; serves_truth=false."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
