#!/usr/bin/env python3
"""Scaffold a Claude-style AIDevObserver project integration pack.

The generated files mirror the project shape commonly used by Claude Code and
agentic dev frameworks: CLAUDE.md, skills, slash command docs, hook docs, MCP
docs, and optional .claude settings. The command is conservative by default:
it prints what it would create unless --write is provided, and it never
overwrites an existing file unless --force is provided.

Proof:
  python3 _repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --self-test
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# Resolve the SUBSTRATE root via the scripts/_repo_paths.py sentinel — NOT `.aidoneright-root` (MONOREPO root,
# no `scripts/` package). install() prepends every code root so this file's deferred `from src.teleon.observer...`
# resolves on a bare `python3 _repos/shared-backend-components/scripts/<f>.py` launch.
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()  # prepend all code roots so the deferred `from src.teleon.observer...` resolves


FRAMEWORK_SKILLS = {
    "generic": ("project-reviewer", "data-ingestion", "frontend-quality", "release-proof"),
    "frontend": ("project-reviewer", "frontend-quality", "component-a11y", "release-proof"),
    "python": ("project-reviewer", "data-ingestion", "api-contracts", "release-proof"),
    "data": ("project-reviewer", "data-ingestion", "model-eval", "release-proof"),
    "workflow": ("project-reviewer", "workflow-distillation", "integration-review", "release-proof"),
    "media": ("project-reviewer", "media-qc", "artifact-routing", "release-proof"),
}


@dataclass(frozen=True, slots=True)
class TemplateFile:
    path: str
    content: str


def _skill_text(name: str) -> str:
    title = name.replace("-", " ").title()
    return "\n".join([
        f"# {title}",
        "",
        "Purpose:",
        "Help the agent reuse existing helpers, templates, workflows, and primitive routes before creating new code.",
        "",
        "Use when:",
        "- a new helper, adapter, parser, workflow, component, data pipeline, or eval harness is requested;",
        "- the agent appears to be rebuilding a common capability;",
        "- a proof or quality gate should exist before handoff.",
        "",
        "Required behavior:",
        "1. Search local repo and registry surfaces first.",
        "2. Prefer an existing primitive or route when confidence is high.",
        "3. If no route exists, describe the primitive candidate and required proof.",
        "4. Treat findings as candidate advice, not automatic truth.",
        "",
    ])


def _templates(framework: str) -> list[TemplateFile]:
    skills = FRAMEWORK_SKILLS[framework]
    files = [
        TemplateFile("CLAUDE.md", "\n".join([
            "# Project Instructions",
            "",
            "## AIDevObserver",
            "",
            "Before building a new helper, workflow, parser, scraper, API adapter, data pipeline, UI quality gate, or model/eval harness:",
            "",
            "1. Search existing repo helpers and registry primitives first.",
            "2. Prefer an existing route over recreating a utility.",
            "3. If a new helper is needed, keep the contract explicit and testable.",
            "4. Run a session review before shipping substantial AI-generated work.",
            "5. Treat AIDevObserver findings as candidate advice, not automatic truth.",
            "",
            "Steering rule:",
            "Do not reinvent code or workflows the primitive database already knows.",
            "",
        ])),
        TemplateFile("session-log.md", "\n".join([
            "# Session Log",
            "",
            "Keep short human summaries here. Do not paste raw private transcripts, secrets, or PII.",
            "",
            "- Latest review:",
            "- Accepted reuse findings:",
            "- Dismissed false positives:",
            "",
        ])),
        TemplateFile("hooks.md", "\n".join([
            "# Hook Policy",
            "",
            "AIDevObserver hooks are non-blocking and read-only by default.",
            "",
            "Use hooks for:",
            "- reinvention hints;",
            "- wasted-context hints;",
            "- cheaper registry-route hints.",
            "",
            "Do not use hooks as promotion or truth gates.",
            "",
        ])),
        TemplateFile("commands/review-session.md", "\n".join([
            "# /review-session",
            "",
            "Review the latest explicit or discoverable AI coding session with AIDevObserver.",
            "",
            "Suggested command:",
            "`python3 -m src.teleon.observer.cli review --latest --json`",
            "",
            "Return top findings, likely reuse routes, candidate status, and next action.",
            "",
        ])),
        TemplateFile("commands/find-reuse.md", "\n".join([
            "# /find-reuse",
            "",
            "Before implementing a new helper or workflow, search local repo surfaces and registry primitives for a reusable route.",
            "",
            "Look for matching contracts, framework role, tests, proof evidence, and known-good templates.",
            "",
        ])),
        TemplateFile("commands/refresh-primitives.md", "\n".join([
            "# /refresh-primitives",
            "",
            "Refresh local source-backed primitive candidates for this repository.",
            "",
            "Suggested command:",
            "`python3 scripts/aidevobserver_context_foundry_loop.py --once --local-repo-root . --local-repo-limit 40`",
            "",
            "Expected output: candidate primitive drafts with source refs, contracts, fingerprints, proof requirements, and serves_truth=false.",
            "",
        ])),
        TemplateFile("commands/review-output.md", "\n".join([
            "# /review-output",
            "",
            "Review final generated work before merge or handoff.",
            "",
            "Check for recreated helpers, avoidable context, missing tests/proofs, reusable primitive candidates, and public artifact privacy.",
            "",
        ])),
        TemplateFile("hooks/pretooluse-aidevobserver.md", "\n".join([
            "# AIDevObserver PreToolUse Hook",
            "",
            "Mode: non-blocking advisory.",
            "",
            "Install:",
            "`python3 scripts/aidevobserver_hook.py --install --write`",
            "",
            "The hook should surface likely reinvention, wasted context, or cheaper registry routes. It should fail open.",
            "",
        ])),
        TemplateFile("hooks/posttooluse-session-note.md", "\n".join([
            "# PostToolUse Session Note",
            "",
            "Optional policy for appending short metadata-only notes after important actions.",
            "",
            "Do not write raw transcript text, secrets, or local absolute paths into shared docs.",
            "",
        ])),
        TemplateFile("hooks/stop-session-summary.md", "\n".join([
            "# Stop Session Summary",
            "",
            "At the end of an AI coding session, summarize accepted reuse findings, dismissed findings, created primitive candidates, and required proofs.",
            "",
        ])),
        TemplateFile("mcp/connections.md", "\n".join([
            "# MCP Connections",
            "",
            "Document MCP servers used by this project. Keep secrets out of this file.",
            "",
            "- AIDevObserver: see `mcp/aidevobserver.md`.",
            "",
        ])),
        TemplateFile("mcp/aidevobserver.md", "\n".join([
            "# AIDevObserver MCP",
            "",
            "Purpose: expose AIDevObserver review tools to Claude Code through MCP.",
            "",
            "Tools:",
            "- `list_sessions`",
            "- `review_session`",
            "- `live_review`",
            "",
            "Setup:",
            "`claude mcp add aidevobserver -- python3 scripts/aidevobserver_mcp_server.py`",
            "",
            "Trust: read-only, candidate findings only, serves_truth=false.",
            "",
        ])),
    ]
    for skill in skills:
        files.append(TemplateFile(f"skills/{skill}/SKILL.md", _skill_text(skill)))
    return files


def scaffold(target: Path, *, framework: str, write: bool, force: bool) -> dict[str, list[str]]:
    created: list[str] = []
    skipped: list[str] = []
    planned: list[str] = []
    for template in _templates(framework):
        dest = target / template.path
        rel = template.path
        if not write:
            planned.append(rel)
            continue
        if dest.exists() and not force:
            skipped.append(rel)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(template.content, encoding="utf-8")
        created.append(rel)
    return {"planned": planned, "created": created, "skipped": skipped}


def _self_test() -> int:
    from src.teleon.observer.local_registry_connector import index_local_repo, primitive_candidates_from_local_repo

    root = Path(tempfile.mkdtemp(prefix="ado_project_scaffold_"))
    fails: list[str] = []
    try:
        dry = scaffold(root, framework="python", write=False, force=False)
        if dry["created"] or not dry["planned"]:
            fails.append("dry-run did not only plan files")
        result = scaffold(root, framework="python", write=True, force=False)
        expected = {
            "CLAUDE.md",
            "commands/review-session.md",
            "hooks/pretooluse-aidevobserver.md",
            "mcp/aidevobserver.md",
            "skills/api-contracts/SKILL.md",
        }
        if not expected.issubset(set(result["created"])):
            fails.append("scaffold did not create expected files")
        second = scaffold(root, framework="python", write=True, force=False)
        if not second["skipped"]:
            fails.append("second scaffold did not skip existing files")
        records = index_local_repo(root)
        kinds = {record.get("kind") for record in records}
        for kind in ("claude_project_context", "claude_skill", "claude_command", "claude_hook_doc", "mcp_connector_doc", "session_memory_doc"):
            if kind not in kinds:
                fails.append(f"connector did not index scaffold kind {kind}")
        primitives = primitive_candidates_from_local_repo(root, limit=80)
        blob = json.dumps(primitives, sort_keys=True)
        if "WorkflowTemplateRef" not in blob or "MCPConnectorProfileRef" not in blob:
            fails.append("scaffolded docs did not produce expected primitive contracts")
        if str(root) in json.dumps(records, sort_keys=True) + blob:
            fails.append("scaffold or connector leaked absolute temp path")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    if fails:
        print("FAIL - aidevobserver project scaffold")
        for fail in fails:
            print(f"  - {fail}")
        return 1
    print("PASS - aidevobserver project scaffold: generated Claude-compatible pack and connector-indexed it.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", default=".", help="target project root")
    parser.add_argument("--framework", choices=sorted(FRAMEWORK_SKILLS), default="generic")
    parser.add_argument("--write", action="store_true", help="write files; otherwise print the planned file list")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    target = Path(args.target).expanduser().resolve()
    result = scaffold(target, framework=args.framework, write=args.write, force=args.force)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif args.write:
        print(f"AIDevObserver project scaffold written to {target}")
        print(f"  created: {len(result['created'])}")
        print(f"  skipped: {len(result['skipped'])}")
    else:
        print(f"AIDevObserver project scaffold dry run for {target}")
        for path in result["planned"]:
            print(f"  {path}")
        print("\nRe-run with --write to create these files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
