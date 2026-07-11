#!/usr/bin/env python3
"""scripts.session_context — mine the STORED session logs + the memory bank DETERMINISTICALLY (zero tokens) to
build the ``context`` that request_intake assumes from, so the caller never hand-assembles it and the agent is
never stopped to ask what the session already knows.

Claude Code (and similar agentic tools) PERSIST full transcripts as JSONL under
``~/.claude/projects/<encoded-project>/*.jsonl``, plus a memory bank (``<project>/memory/``). This module tails
the most-recent transcripts (BYTE-BOUNDED, so a 160MB log costs the same as a 1KB one), reads the memory bank,
and runs the SAME lexicons/facets request_intake uses over the accumulated text — so a platform / technology /
integration / goal mentioned earlier in the session (or remembered) carries forward into the current request
with no LLM call and no clarifying question.

  read_session_text(...) -> the byte-bounded tail of the recent transcripts (raw, tolerant).
  read_memory_text(...)  -> the memory bank (MEMORY.md index + recent notes), bounded.
  extract_context(text)  -> {platform, technologies, integrations, entities, goals} via deterministic extractors.
  session_context(...)   -> the context dict for request_intake.intake (extracted fields + a short history excerpt).
  intake_from_session(prompt, ...) -> request_intake.intake(prompt, context=session_context(...)).

serves_truth=false — a mined context is a candidate memory of the session, never truth. Reads only the current
project's own logs/memory; extracts fields, never republishes raw log content.

    PYTHONPATH=. python3 scripts/session_context.py --self-test
    PYTHONPATH=. python3 scripts/session_context.py --context           # the deterministic context, this project
    PYTHONPATH=. python3 scripts/session_context.py --intake "now also dedupe them"
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts import query_decomposer as _decomp  # noqa: E402  REUSE: robust operation extraction (goals)
from scripts import request_intake as _intake  # noqa: E402  REUSE: field lexicons + hit matcher + intake()

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_MAX_FILES = 3          # tail this many most-recent transcripts (recency-ordered)
_MAX_TAIL_BYTES = 400_000   # per-file byte tail — bounds cost regardless of a transcript's size (a 160MB log is fine)
_MAX_MEMORY_BYTES = 60_000  # memory-bank read cap (MEMORY.md index is the gist)
_OPS_SCAN_CHARS = 12_000    # cap the (slower) operation scan to a recent slice
_HISTORY_EXCERPT = 2_000    # chars of recent session text handed to intake as a fallback signal


def _repo_root() -> Path:
    """The git project root (walk up from cwd) — its path encodes the Claude Code project dir name."""
    p = Path.cwd().resolve()
    for q in (p, *p.parents):
        if (q / ".git").exists():
            return q
    return p


def _encode_project(root: Path) -> str:
    """Claude Code encodes a project path into its logs dir name by replacing '/' and '_' with '-'."""
    return str(root).replace("/", "-").replace("_", "-")


def default_logs_dir(project_root: Optional[Path] = None) -> Path:
    """~/.claude/projects/<encoded-project> (env OH_SESSION_LOG_DIR overrides). Where Claude Code stores logs."""
    override = os.environ.get("OH_SESSION_LOG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "projects" / _encode_project(project_root or _repo_root())


def default_memory_dir(project_root: Optional[Path] = None) -> Path:
    return default_logs_dir(project_root) / "memory"


def _tail_text(path: Path, max_bytes: int) -> str:
    """The last ``max_bytes`` of a file, decoded tolerantly — O(max_bytes), independent of the file's size."""
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            if size > max_bytes:
                fh.seek(size - max_bytes)
            data = fh.read()
        return data.decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001 — an unreadable log is simply skipped, never a crash
        return ""


def discover_logs(logs_dir: Optional[Path] = None, *, project_root: Optional[Path] = None,
                  max_files: int = _MAX_FILES) -> list[Path]:
    """The most-recently-modified transcript JSONLs for the project (recency-ordered, capped)."""
    d = Path(logs_dir) if logs_dir else default_logs_dir(project_root)
    if not d.exists():
        return []
    try:
        files = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:  # noqa: BLE001
        return []
    return files[:max_files]


def read_session_text(logs_dir: Optional[Path] = None, *, project_root: Optional[Path] = None,
                      max_files: int = _MAX_FILES, max_bytes: int = _MAX_TAIL_BYTES) -> str:
    """The byte-bounded tail of the recent transcripts, concatenated (raw JSONL text — deterministic lexicon/
    facet matching does not need it parsed)."""
    return "\n".join(_tail_text(p, max_bytes) for p in discover_logs(logs_dir, project_root=project_root,
                                                                      max_files=max_files))


def read_memory_text(memory_dir: Optional[Path] = None, *, project_root: Optional[Path] = None,
                     max_bytes: int = _MAX_MEMORY_BYTES) -> str:
    """The memory bank as text — MEMORY.md (the index / gist) first, then the most-recent notes, byte-capped."""
    d = Path(memory_dir) if memory_dir else default_memory_dir(project_root)
    if not d.exists():
        return ""
    parts, budget = [], max_bytes
    index = d / "MEMORY.md"
    if index.exists():
        parts.append(_tail_text(index, budget)); budget -= min(budget, index.stat().st_size)
    try:
        notes = sorted((p for p in d.glob("*.md") if p.name != "MEMORY.md"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:  # noqa: BLE001
        notes = []
    for note in notes:
        if budget <= 0:
            break
        parts.append(_tail_text(note, budget)); budget -= min(budget, note.stat().st_size)
    return "\n".join(parts)


def extract_context(text: str) -> dict[str, Any]:
    """Deterministically extract the request-brief fields from accumulated session/memory text — 0 tokens."""
    low = text.lower()
    return {
        "platform": _intake._lexicon_hits(low, _intake._PLATFORM_LEXICON),
        "technologies": _intake._lexicon_hits(low, _intake._TECH_LEXICON),
        "integrations": _intake._lexicon_hits(low, _intake._INTEGRATION_LEXICON),
        "goals": sorted(_decomp._robust_operations(text[:_OPS_SCAN_CHARS])),
        # CamelCase identifiers of ALPHA-ONLY word parts (Upper+2 lowers, 2+ parts) — excludes hash/id tokens
        "entities": sorted({e for e in re.findall(r"\b[A-Z][a-z]{2,}(?:[A-Z][a-z]{2,})+\b", text[:_OPS_SCAN_CHARS])
                            if len(e) <= 40})[:20],
    }


def session_context(*, project_root: Optional[Path] = None, logs_dir: Optional[Path] = None,
                    memory_dir: Optional[Path] = None, include_memory: bool = True,
                    max_files: int = _MAX_FILES, max_bytes: int = _MAX_TAIL_BYTES) -> dict[str, Any]:
    """Build the ``context`` for request_intake.intake by mining the stored session logs (+ memory bank),
    deterministically. The extracted fields are what intake assumes from; a short history excerpt is a fallback."""
    session_text = read_session_text(logs_dir, project_root=project_root, max_files=max_files, max_bytes=max_bytes)
    memory_text = read_memory_text(memory_dir, project_root=project_root) if include_memory else ""
    combined = f"{session_text}\n{memory_text}"
    ctx = extract_context(combined)
    ctx["history"] = session_text[-_HISTORY_EXCERPT:]  # recent tail as a fallback signal for intake's extractors
    ctx["sources"] = {"transcripts": len(discover_logs(logs_dir, project_root=project_root, max_files=max_files)),
                      "memory_used": bool(memory_text)}
    ctx.update(BOUNDARY)
    return ctx


def intake_from_session(prompt: str, *, project_root: Optional[Path] = None, logs_dir: Optional[Path] = None,
                        memory_dir: Optional[Path] = None, **intake_kw: Any) -> dict[str, Any]:
    """Normalize a prompt with the context auto-mined from the session logs + memory — 0-token, non-blocking."""
    ctx = session_context(project_root=project_root, logs_dir=logs_dir, memory_dir=memory_dir)
    return _intake.intake(prompt, context=ctx, **intake_kw)


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as d:
        logs = Path(d) / "logs"
        mem = Path(d) / "memory"
        logs.mkdir(); mem.mkdir()
        # a synthetic transcript (JSONL) mentioning the platform/tech/integration earlier in the session
        (logs / "a.jsonl").write_text(
            json.dumps({"role": "user", "text": "build a python service on aws that reads from postgres"}) + "\n"
            + json.dumps({"role": "assistant", "text": "wired the FastAPI handler and the RateLimiter"}) + "\n")
        (mem / "MEMORY.md").write_text("- project runs on gcp with bigquery for the warehouse\n")

        # (a) deterministic extraction pulls the fields out of the stored log + memory, zero tokens
        ctx = session_context(logs_dir=logs, memory_dir=mem)
        checks.append(("platform is mined from the stored session log", "aws" in ctx["platform"]))
        checks.append(("technology is mined from the stored session log", "python" in ctx["technologies"]))
        checks.append(("integration is mined from the stored session log", "postgres" in ctx["integrations"]))
        checks.append(("the memory bank contributes context too (gcp/bigquery)",
                       "gcp" in ctx["platform"] and "bigquery" in ctx["integrations"]))
        checks.append(("a CamelCase entity is captured (RateLimiter)", "RateLimiter" in ctx["entities"]))

        # (b) fed to intake, a terse follow-up is FULLY resolved with NO questions and is ready to proceed
        r = _intake.intake("now also dedupe the records", context=ctx)
        checks.append(("a terse follow-up carries the session platform forward (assumed, not asked)",
                       "aws" in r["brief"]["platform"]["value"]
                       and not any(q["field"] == "platform" for q in r["clarifying_questions"])))
        checks.append(("the follow-up is ready + non-blocking (agent proceeds)",
                       r["ready"] is True and r["blocking"] is False))

        # (c) BYTE-BOUNDED: a huge transcript is tail-read at fixed cost, and the recent tail still matches
        big = logs / "big.jsonl"
        big.write_text("x" * 2_000_000 + "\n"
                       + json.dumps({"text": "later we moved it to kubernetes with redis"}) + "\n")
        ctx2 = session_context(logs_dir=logs, memory_dir=mem, max_bytes=50_000)
        checks.append(("a 2MB transcript is tail-read (bounded) and the RECENT context is caught",
                       "kubernetes" in ctx2["platform"] and "redis" in ctx2["integrations"]))

        # (d) determinism + graceful-empty + governance
        checks.append(("mining is deterministic (byte-identical twice)",
                       json.dumps(session_context(logs_dir=logs, memory_dir=mem), sort_keys=True)
                       == json.dumps(session_context(logs_dir=logs, memory_dir=mem), sort_keys=True)))
        empty = session_context(logs_dir=Path(d) / "nope", memory_dir=Path(d) / "nope", include_memory=True)
        checks.append(("a missing log dir degrades to an empty context (never a crash)",
                       empty["platform"] == [] and empty["serves_truth"] is False))
        checks.append(("context is candidate/serves_truth=false", ctx["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - session_context: DETERMINISTICALLY (0-token) mine the stored Claude Code transcripts "
          "(byte-bounded tail — a 160MB log costs the same as 1KB) + the memory bank, extract the request-brief "
          "fields (platform/tech/integrations/entities/goals) via the shared lexicons/facets, and hand them to "
          "request_intake as auto-assembled context — so a terse follow-up carries the session forward with no "
          "LLM call and no clarifying question. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--context", action="store_true", help="print the deterministic context mined for THIS project")
    ap.add_argument("--intake", metavar="PROMPT", default=None, help="intake a prompt with auto-mined session context")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.context:
        ctx = session_context()
        ctx.pop("history", None)  # do not echo raw log text
        print(json.dumps(ctx, indent=2, sort_keys=True))
        return 0
    if args.intake:
        print(json.dumps(intake_from_session(args.intake), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
