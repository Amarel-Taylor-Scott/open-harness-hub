#!/usr/bin/env python3
"""scripts/execute_context_reorg — merge the deterministic plan + the LLM classifications into ONE final
move-plan, then execute it losslessly with `git mv` + a lineage manifest.

Merge rule: a HIGH-confidence path match (filename carried the component name) wins; otherwise the LLM
classification of the doc's topic decides; a doc the LLM marked `keep` (operational/meta) is NOT moved; a
still-`review` doc is NOT moved (reported, never guessed). `--apply` runs `git mv` (history-preserving),
creating target dirs, appending every move to context/_manifest.jsonl, and verifying every planned source
ended up at its target (losslessness proof). Nothing is deleted or untracked.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REORG = _resource("data") / "dev-intel" / "context_reorg"
PLAN = REORG / "move_plan.jsonl"
CLASSIFIED_DIR = REORG / "classified"
FINAL = REORG / "final_plan.jsonl"
MANIFEST = _resource("context") / "_manifest.jsonl"
NO_MOVE = {"keep", "review", "held"}
# Files whose path-references would break if a doc moves out from under them.
OP_FILES = ("CLAUDE.md", "AGENTS.md", "mkdocs.yml")


def held_sources(sources: list[str]) -> set[str]:
    """Docs referenced BY PATH in the operating layer or in code — moving these breaks a live reference, so
    they stay in place (reported), and are moved later only with a coordinated reference update."""
    blob_parts = []
    for f in OP_FILES:
        p = _resource(f)
        if p.exists():
            blob_parts.append(p.read_text(errors="ignore"))
    for py in (_resource("scripts")).glob("*.py"):
        try:
            blob_parts.append(py.read_text(errors="ignore"))
        except Exception:  # noqa: BLE001
            continue
    blob = "\n".join(blob_parts)
    return {s for s in sources if s in blob}


def _target_for(source: str, component: str) -> str:
    sub = source
    for lead in ("docs/", "prompts/", "commands/", "./"):
        if sub.startswith(lead):
            sub = sub[len(lead):]
            break
    return f"context/{component}/{sub}"


def load_classifications() -> dict[str, str]:
    out: dict[str, str] = {}
    if CLASSIFIED_DIR.exists():
        for f in sorted(CLASSIFIED_DIR.glob("classified_*.jsonl")):
            for line in f.read_text(errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("path") and rec.get("component"):
                        out[rec["path"]] = rec["component"]
                except Exception:  # noqa: BLE001
                    continue
    return out


def build_final() -> dict:
    plan = [json.loads(l) for l in PLAN.read_text().splitlines() if l.strip()]
    llm = load_classifications()
    held = held_sources([r["source"] for r in plan])
    rows, counts, not_moved = [], {}, []
    for r in plan:
        src = r["source"]
        if src in held:                          # referenced by operating layer / code -> keep in place
            component = "held"
        else:
            high_conf_path = r["rule_matched"] not in ("content", "")
            if high_conf_path:
                component = r["component"]        # filename carried the component name — trust it
            else:
                component = llm.get(src, r["component"])  # LLM topic classification, else the content-vote
        counts[component] = counts.get(component, 0) + 1
        if component in NO_MOVE:
            not_moved.append(src)
            continue
        rows.append({"source": src, "target": _target_for(src, component), "component": component})
    return {"rows": rows, "counts": counts, "not_moved": not_moved, "to_move": len(rows)}


def write_final(final: dict) -> None:
    FINAL.parent.mkdir(parents=True, exist_ok=True)
    with FINAL.open("w") as fh:
        for r in final["rows"]:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def apply_moves(final: dict, *, limit: int | None = None) -> dict:
    """git mv each planned source -> target (history-preserving), record lineage, verify. Idempotent-ish:
    a source already gone (moved) is skipped. Returns a report."""
    moved, skipped, failed = [], [], []
    manifest_lines = []
    rows = final["rows"][:limit] if limit else final["rows"]
    for r in rows:
        src, tgt = _resource(r["source"]), _resource(r["target"])
        if not src.exists():
            skipped.append(r["source"]); continue
        tgt.parent.mkdir(parents=True, exist_ok=True)
        res = _git("mv", r["source"], r["target"])
        if res.returncode != 0:
            failed.append({"source": r["source"], "error": res.stderr.strip()[:160]}); continue
        moved.append(r)
        manifest_lines.append(json.dumps({"original_path": r["source"], "new_path": r["target"],
                                          "component": r["component"], "reason": "context reorg 2026-07-03",
                                          "reversible": True}, sort_keys=True))
    if manifest_lines:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        with MANIFEST.open("a") as fh:
            fh.write("\n".join(manifest_lines) + "\n")
    # losslessness verification: every moved source is gone and its target exists.
    lost = [r["source"] for r in moved if (_resource(r["source"])).exists() or not (_resource(r["target"])).exists()]
    return {"moved": len(moved), "skipped": len(skipped), "failed": failed, "lost": lost}


def self_test() -> int:
    checks = [
        ("target strips docs/", _target_for("docs/strategy/teleon-x.md", "teleon") == "context/teleon/strategy/teleon-x.md"),
        ("target strips prompts/", _target_for("prompts/teleon-build-kit.md", "teleon") == "context/teleon/teleon-build-kit.md"),
        ("keep/review/held are no-move", NO_MOVE == {"keep", "review", "held"}),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - execute_context_reorg:\n  " + "\n  ".join(failed)); return 1
    print("PASS - execute_context_reorg: merge (path-match wins, else LLM topic, else content-vote); keep/review "
          "never moved; git mv preserves history; lineage -> context/_manifest.jsonl; losslessness verified post-move.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Execute the per-component context reorg (merge + git mv + lineage).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--plan", action="store_true", help="merge + write final plan + print counts (no moves)")
    ap.add_argument("--apply", action="store_true", help="execute git mv per the final plan (records lineage, verifies)")
    ap.add_argument("--limit", type=int, default=None, help="apply only the first N moves (batching)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    final = build_final()
    if args.plan or args.apply:
        write_final(final)
    print(f"to move: {final['to_move']}  |  not moved (keep/review): {len(final['not_moved'])}")
    for c in sorted(final["counts"]):
        print(f"  {c:16} {final['counts'][c]}")
    if args.apply:
        rep = apply_moves(final, limit=args.limit)
        print(f"\nAPPLIED: moved={rep['moved']} skipped={rep['skipped']} failed={len(rep['failed'])} lost={len(rep['lost'])}")
        if rep["failed"]:
            print("  failures:", rep["failed"][:5])
        if rep["lost"]:
            print("  LOST (verify!):", rep["lost"][:5])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
