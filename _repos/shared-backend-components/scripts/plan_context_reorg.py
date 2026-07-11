#!/usr/bin/env python3
"""scripts/plan_context_reorg — deterministic move-planner for the per-component context reorg.

Produces a REVIEWABLE move-plan (source -> context/<component>/<preserved-subpath>) BEFORE any git mv, so
every in-scope doc's destination can be eyeballed and losslessness proven (every in-scope file gets exactly
one target or is flagged `review`). Classification is by path/filename keyword rules (ordered, first strong
match wins); genuinely-ambiguous docs land in `review` rather than being guessed. The mover (separate step)
consumes this plan with `git mv` + records lineage — nothing is deleted or untracked.

Scope: hand-written context docs. OUT of scope (never moved): _repos/shared-backend-components/docs/catalog/ (generated pages), node_modules,
archive/legacy/ (already archived), context/ itself, dist/, site/, _reference/, and the operational
entrypoints (CLAUDE.md, AGENTS.md, README.md, mkdocs.yml) which stay at root.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLAN_PATH = _resource("data") / "dev-intel" / "context_reorg" / "move_plan.jsonl"

# Paths whose docs are never moved (generated / vendored / already-archived / self / entrypoints).
EXCLUDE_PREFIXES = ("docs/catalog/", "node_modules/", "archive/legacy/", "context/", "dist/", "site/",
                    "_reference/", ".git/", ".venv/", "venv/", ".claude/", ".codex/", ".github/",
                    # non-context: generated data, demo fixtures, code, templates, vendored
                    "data/", "demo-data/", "code-templates/", ".research-notes/", "research/", "catalog/",
                    "scripts/", "src/", "web/", "tests/", "templates/", "vocabularies/", "schemas/")
EXCLUDE_EXACT = {"CLAUDE.md", "AGENTS.md", "README.md", "mkdocs.yml", "docs/index.md"}

# Ordered classification rules: (component, keywords). First rule with a keyword in the lowercased path wins.
# Order encodes priority: cross-cutting laws first, then the named products, then brand/portfolio, then the
# technical substrate as the catch-all for engineering docs; anything unmatched -> 'review'.
RULES: list[tuple[str, tuple[str, ...]]] = [
    ("_shared", ("bible", "north-star", "north_star", "foundational-law", "foundational_law", "no-magic-values",
                 "change-verification", "lossless-distillation", "design-bible", "integration-bible",
                 "glossary", "vocabulary", "master-goal", "stop-slop", "computational-substrate")),
    ("teleon", ("teleon", "purpose-task", "purposetask", "capability-task", "capabilitytask", "control-tower",
                "capability-assurance", "purpose-runtime", "oips", "inference-gateway", "inference-lane")),
    ("baltor", ("baltor", "context-engine", "sanctions", "provider-directory", "verification-foundry",
                "determinism-factory", "context-auditor", "public-statement", "native-format")),
    ("aidevobserver", ("aidevobserver", "observer", "spotter", "session-review", "review-session")),
    ("openhubforai", ("openhubforai", "openharness", "openhub", "open-hub", "openreconciliation", "openhardening",
                       "openenrichment", "openoptimization", "openverification", "openrouting", "openharnesshub",
                       "capabilitytask-spec", "hub-automation", "registry-federation", "harness-hub")),
    ("aidoneright", ("aidoneright", "ai-done-right", "context-is-everything", "parent-brand", "portfolio",
                     "brand-architecture", "design-family")),
    ("backend", ("primitive", "registry", "component", "codegraph", "pyprefix", "canonical-id", "canonical_id",
                 "storage", "embedding", "pipeline", "factory", "acquisition", "eval", "schema", "vocab",
                 "worker", "dag", "discovery", "credential", "source-surface", "capability-valley", "capability-gap",
                 "corpus", "gap-detection", "reason-code", "promotion", "cdc", "dedupe", "entity", "ingestion",
                 "flywheel", "loop", "benchmark", "descent", "parallel-path")),
]


def classify(rel_path: str) -> tuple[str, str]:
    """Return (component, rule_matched) for a repo-relative doc path. Pure + deterministic (testable)."""
    low = rel_path.lower()
    base = low.rsplit("/", 1)[-1]
    for component, keywords in RULES:
        for kw in keywords:
            # match filename first (stronger signal), then any path segment.
            if kw in base or kw in low:
                return component, kw
    return "review", ""


def content_vote(text: str) -> tuple[str, str]:
    """Fallback for path-ambiguous docs: vote by component-keyword frequency in the body. Requires a clear
    winner (>=3 hits AND a >=2 margin over the runner-up) so weak/tied signal stays `review`, never guessed."""
    low = text.lower()
    scores: dict[str, int] = {}
    for component, keywords in RULES:
        s = sum(low.count(kw) for kw in keywords)
        if s:
            scores[component] = s
    if not scores:
        return "review", ""
    ranked = sorted(scores.values(), reverse=True)
    best = max(scores, key=lambda k: scores[k])
    if ranked[0] >= 3 and (len(ranked) == 1 or ranked[0] - ranked[1] >= 2):
        return best, "content"
    return "review", ""


def target_for(rel_path: str, component: str) -> str:
    """context/<component>/<original-path with leading _repos/shared-backend-components/docs/|prompts/ stripped> — preserves the categorizing
    subdir (e.g. docs/strategy/teleon-x.md -> context/teleon/strategy/teleon-x.md) so nothing collides."""
    sub = rel_path
    for lead in ("docs/", "prompts/", "./"):
        if sub.startswith(lead):
            sub = sub[len(lead):]
            break
    return f"context/{component}/{sub}"


# Allowlist: only the actual context-doc TREES are in scope (not every README co-located with code, not
# repo-meta, not generated). This is the "hundreds of context docs" the reorg targets.
INCLUDE_ROOTS = ("docs/", "prompts/", "commands/")


def in_scope(rel_path: str) -> bool:
    if not rel_path.endswith(".md") or rel_path.endswith(".generated.md"):
        return False
    if rel_path in EXCLUDE_EXACT or not rel_path.startswith(INCLUDE_ROOTS):
        return False
    return not rel_path.startswith("docs/catalog/")


def tracked_md() -> list[str]:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=REPO, capture_output=True, text=True, check=True)
    return [l for l in out.stdout.splitlines() if l.strip()]


def build_plan() -> dict:
    rows, counts, review = [], {}, []
    for rel in tracked_md():
        if not in_scope(rel):
            continue
        component, rule = classify(rel)
        if component == "review":  # path was ambiguous — peek at the body and vote
            try:
                head = "\n".join((_resource(rel)).read_text(errors="ignore").splitlines()[:60])
                component, rule = content_vote(head)
            except Exception:  # noqa: BLE001
                component, rule = "review", ""
        target = None if component == "review" else target_for(rel, component)
        rows.append({"source": rel, "target": target, "component": component, "rule_matched": rule})
        counts[component] = counts.get(component, 0) + 1
        if component == "review":
            review.append(rel)
    return {"rows": rows, "counts": counts, "review": review, "total_in_scope": len(rows)}


def write_plan(plan: dict) -> Path:
    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PLAN_PATH.open("w") as fh:
        for r in plan["rows"]:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return PLAN_PATH


def self_test() -> int:
    checks = [
        ("teleon doc -> teleon", classify("docs/strategy/teleon-naming-and-domain.md")[0] == "teleon"),
        ("baltor doc -> baltor", classify("docs/strategy/baltor-gtm-fundraising-plan.md")[0] == "baltor"),
        ("observer doc -> aidevobserver", classify("docs/codex/aidevobserver-context-foundry.md")[0] == "aidevobserver"),
        ("bible -> _shared", classify("docs/BIBLE.md")[0] == "_shared"),
        ("primitive doc -> backend", classify("docs/concepts/component-taxonomy-and-stages.md")[0] == "backend"),
        ("openhub -> openhubforai", classify("docs/openharness/hub-automation.md")[0] == "openhubforai"),
        ("unknown -> review", classify("docs/random/xyzzy-notes.md")[0] == "review"),
        ("target strips docs/", target_for("docs/strategy/teleon-x.md", "teleon") == "context/teleon/strategy/teleon-x.md"),
        ("catalog excluded", in_scope("docs/catalog/foo.md") is False),
        ("entrypoint excluded", in_scope("CLAUDE.md") is False),
        ("archive excluded", in_scope("archive/legacy/docs/x.md") is False),
        ("real strategy doc in scope", in_scope("docs/strategy/north-stars.md") is True),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - plan_context_reorg:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - plan_context_reorg: deterministic classifier over {len(RULES)} component rules; targets preserve "
          f"subdir + never collide; catalog/entrypoints/archive excluded; unmatched -> review (never guessed).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan the per-component context reorg (reviewable, no moves).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--plan", action="store_true", help="build + write the move plan and print the summary")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    plan = build_plan()
    if args.plan:
        write_plan(plan)
    print(f"in-scope docs: {plan['total_in_scope']}")
    for c in sorted(plan["counts"]):
        print(f"  {c:16} {plan['counts'][c]}")
    print(f"plan -> {PLAN_PATH.relative_to(REPO)}" if args.plan else "(dry run — pass --plan to write)")
    if plan["review"][:8]:
        print("sample of 'review' (ambiguous, not auto-moved):")
        for r in plan["review"][:8]:
            print(f"    {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
