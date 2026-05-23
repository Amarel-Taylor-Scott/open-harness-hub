#!/usr/bin/env python3
"""oh-hub — Open Harness Hub command-line interface.

Ergonomic catalog access for humans + AI agents (Claude Code / Cursor /
Aider / etc).

Subcommands:
  list [TYPE]           — list artifacts (optionally filtered by type)
  describe <id>         — print artifact YAML + immediate dependencies
  search <query>        — fuzzy search across id / name / description / tags
  depends <id>          — print dependency graph
  validate              — validate all manifests
  run <pipeline-id>     — run a pipeline (forwards to run_pipeline)
  stats                 — catalog summary
  emit <id> <format>    — emit one artifact to a standards format
  industries [INDUSTRY] — list artifacts by industry vertical

Examples:
  scripts/oh_hub.py list pipeline
  scripts/oh_hub.py describe persona/esg-auditor
  scripts/oh_hub.py search forced-labor
  scripts/oh_hub.py industries esg
  scripts/oh_hub.py depends pipeline/supplier-policy-grading
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"

try:
    import yaml  # type: ignore[import]
except ImportError:
    sys.stderr.write("pyyaml is required: pip install pyyaml\n")
    sys.exit(2)


def load_catalog() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts:
            continue
        try:
            data = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and "id" in data:
            data["_path"] = str(path.relative_to(ROOT))
            out[data["id"]] = data
    return out


ARTIFACT_TYPES = [
    "harness", "pipeline", "benchmark", "rule-pack", "knowledge-pack",
    "logic-pack", "tool", "persona", "adapter", "rubric", "dataset",
    "schema", "processor", "pattern",
]


# ------------------------------------------------------------------
# Subcommand: list
# ------------------------------------------------------------------
def cmd_list(args, catalog):
    type_filter = args.type
    sort_key = args.sort
    rows = []
    for art_id, art in catalog.items():
        if type_filter and art.get("type") != type_filter:
            continue
        rows.append((art_id, art.get("name", ""), art.get("lifecycle", ""), art.get("type", "")))

    if sort_key == "name":
        rows.sort(key=lambda r: r[1])
    elif sort_key == "type":
        rows.sort(key=lambda r: (r[3], r[0]))
    else:
        rows.sort()

    if args.json:
        print(json.dumps([{"id": r[0], "name": r[1], "lifecycle": r[2], "type": r[3]} for r in rows], indent=2))
        return

    type_w = max((len(r[3]) for r in rows), default=8)
    id_w = max((len(r[0]) for r in rows), default=20)
    for r in rows:
        print(f"  {r[3]:<{type_w}}  {r[0]:<{id_w}}  {r[1]}")
    print(f"\n{len(rows)} artifact(s){' of type ' + type_filter if type_filter else ''}")


# ------------------------------------------------------------------
# Subcommand: describe
# ------------------------------------------------------------------
def _find_refs_in(obj, out):
    """Walk obj collecting strings that look like artifact ids."""
    REF_RE = re.compile(r"^(harness|pipeline|benchmark|rule-pack|knowledge-pack|logic-pack|tool|persona|adapter|rubric|dataset|schema|processor|pattern)/[a-z0-9]+(-[a-z0-9]+)*$")
    if isinstance(obj, dict):
        for v in obj.values():
            _find_refs_in(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _find_refs_in(v, out)
    elif isinstance(obj, str):
        if REF_RE.match(obj):
            out.add(obj)


def cmd_describe(args, catalog):
    art_id = args.id
    art = catalog.get(art_id)
    if art is None:
        candidates = [aid for aid in catalog if art_id in aid]
        if not candidates:
            print(f"unknown artifact {art_id!r}", file=sys.stderr)
            return 1
        if len(candidates) == 1:
            art = catalog[candidates[0]]
            art_id = candidates[0]
        else:
            print(f"ambiguous {art_id!r} — matches:", file=sys.stderr)
            for c in candidates[:10]:
                print(f"  {c}", file=sys.stderr)
            return 1

    if args.json:
        clean = {k: v for k, v in art.items() if k != "_path"}
        print(json.dumps(clean, indent=2, default=str))
        return 0

    # Pretty-print summary
    print(f"\n  {art_id}")
    print(f"  {'─' * (len(art_id) + 4)}")
    print(f"  type:        {art.get('type')}")
    print(f"  name:        {art.get('name', '')}")
    print(f"  lifecycle:   {art.get('lifecycle', '')}")
    print(f"  industries:  {', '.join(art.get('industry') or [])}")
    print(f"  capabilities:{', '.join(art.get('capability') or [])}")
    print(f"  tags:        {', '.join(art.get('tags') or [])}")
    print(f"  manifest:    {art.get('_path')}")

    desc = art.get("description", "").strip()
    if desc:
        print(f"\n  description:")
        for para in desc.split("\n\n"):
            wrapped = textwrap.fill(para.strip(), width=72, initial_indent="    ", subsequent_indent="    ")
            print(wrapped)
            print()

    # Dependencies
    refs: set[str] = set()
    _find_refs_in({k: v for k, v in art.items() if k != "_path"}, refs)
    refs.discard(art_id)
    if refs:
        print(f"  references {len(refs)} other artifact(s):")
        for ref in sorted(refs):
            status = "✓" if ref in catalog else "✗ (missing)"
            print(f"    {status} {ref}")

    return 0


# ------------------------------------------------------------------
# Subcommand: search
# ------------------------------------------------------------------
def cmd_search(args, catalog):
    query = args.query.lower()
    hits = []
    for art_id, art in catalog.items():
        haystack = " ".join([
            art_id,
            art.get("name", ""),
            art.get("description", ""),
            " ".join(art.get("tags") or []),
            " ".join(art.get("industry") or []),
            " ".join(art.get("capability") or []),
        ]).lower()
        if query in haystack:
            # crude relevance scoring
            score = haystack.count(query)
            hits.append((score, art_id, art.get("name", ""), art.get("type", "")))

    hits.sort(reverse=True)
    for score, art_id, name, art_type in hits[:args.limit]:
        print(f"  [{art_type:<14}]  {art_id:<55}  {name}")
    if not hits:
        print(f"  no matches for {query!r}")
    else:
        print(f"\n  {len(hits)} match(es) — top {min(len(hits), args.limit)} shown")


# ------------------------------------------------------------------
# Subcommand: depends
# ------------------------------------------------------------------
def cmd_depends(args, catalog):
    art_id = args.id
    if art_id not in catalog:
        print(f"unknown artifact {art_id!r}", file=sys.stderr)
        return 1

    def walk(aid, depth, visited):
        if aid in visited:
            print(f"{'  ' * depth}↻ {aid} (cycle)")
            return
        visited.add(aid)
        art = catalog.get(aid)
        if art is None:
            print(f"{'  ' * depth}✗ {aid} (missing)")
            return
        print(f"{'  ' * depth}{aid} [{art.get('type')}]")
        if depth >= args.max_depth:
            print(f"{'  ' * (depth + 1)}... (max-depth reached)")
            return
        refs: set[str] = set()
        _find_refs_in({k: v for k, v in art.items() if k != "_path"}, refs)
        refs.discard(aid)
        for ref in sorted(refs):
            walk(ref, depth + 1, visited)

    walk(art_id, 0, set())
    return 0


# ------------------------------------------------------------------
# Subcommand: validate
# ------------------------------------------------------------------
def cmd_validate(args, catalog):
    import subprocess
    proc = subprocess.run(["python3", str(ROOT / "scripts" / "validate.py")], capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


# ------------------------------------------------------------------
# Subcommand: run
# ------------------------------------------------------------------
def cmd_run(args, catalog):
    import subprocess
    cmd = ["python3", str(ROOT / "scripts" / "run_pipeline.py"), args.pipeline_id]
    if args.inputs:
        cmd += ["--inputs", args.inputs]
    if args.simulate:
        cmd += ["--simulate"]
    return subprocess.call(cmd)


# ------------------------------------------------------------------
# Subcommand: stats
# ------------------------------------------------------------------
def cmd_stats(args, catalog):
    by_type = Counter()
    by_industry = Counter()
    by_lifecycle = Counter()
    by_capability = Counter()
    for art in catalog.values():
        by_type[art.get("type", "?")] += 1
        for ind in art.get("industry") or []:
            by_industry[ind] += 1
        by_lifecycle[art.get("lifecycle", "?")] += 1
        for cap in art.get("capability") or []:
            by_capability[cap] += 1

    print(f"\n  Catalog at {ROOT.name}:")
    print(f"  ─────────────────────────")
    print(f"  total: {len(catalog)} artifacts\n")

    print("  by type:")
    for t, c in by_type.most_common():
        print(f"    {t:<16} {c:>4}")

    print("\n  by lifecycle:")
    for l, c in by_lifecycle.most_common():
        print(f"    {l:<16} {c:>4}")

    print("\n  top 10 industries:")
    for ind, c in by_industry.most_common(10):
        print(f"    {ind:<28} {c:>4}")

    print("\n  top 10 capabilities:")
    for cap, c in by_capability.most_common(10):
        print(f"    {cap:<28} {c:>4}")


# ------------------------------------------------------------------
# Subcommand: industries
# ------------------------------------------------------------------
def cmd_industries(args, catalog):
    by_ind = defaultdict(list)
    for art_id, art in catalog.items():
        for ind in art.get("industry") or []:
            by_ind[ind].append((art_id, art.get("type", "?"), art.get("name", "")))

    if args.industry:
        rows = by_ind.get(args.industry, [])
        if not rows:
            print(f"no artifacts tagged industry={args.industry!r}")
            return 1
        rows.sort()
        for art_id, art_type, name in rows:
            print(f"  [{art_type:<14}]  {art_id:<55}  {name}")
        print(f"\n  {len(rows)} artifacts in industry {args.industry!r}")
    else:
        for ind in sorted(by_ind.keys()):
            print(f"  {ind:<35} {len(by_ind[ind]):>4} artifacts")


# ------------------------------------------------------------------
# Subcommand: emit
# ------------------------------------------------------------------
def cmd_emit(args, catalog):
    import subprocess
    emit_dir = ROOT / "scripts" / "emit"
    target = emit_dir / f"{args.format}.py"
    if not target.exists():
        print(f"unknown emit format {args.format!r}", file=sys.stderr)
        print(f"available formats:", file=sys.stderr)
        for f in sorted(emit_dir.glob("*.py")):
            if f.name == "__init__.py":
                continue
            print(f"  {f.stem}", file=sys.stderr)
        return 1
    return subprocess.call(["python3", str(target), args.id])


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        prog="oh-hub",
        description="Open Harness Hub command-line interface.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="list artifacts")
    p_list.add_argument("type", nargs="?", default=None, choices=ARTIFACT_TYPES + [None])
    p_list.add_argument("--sort", choices=["id", "name", "type"], default="id")
    p_list.add_argument("--json", action="store_true")

    p_desc = sub.add_parser("describe", help="describe an artifact")
    p_desc.add_argument("id")
    p_desc.add_argument("--json", action="store_true")

    p_search = sub.add_parser("search", help="search catalog")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=20)

    p_dep = sub.add_parser("depends", help="show dependency graph")
    p_dep.add_argument("id")
    p_dep.add_argument("--max-depth", type=int, default=4)

    sub.add_parser("validate", help="validate all manifests")
    sub.add_parser("stats", help="catalog summary")

    p_run = sub.add_parser("run", help="run a pipeline")
    p_run.add_argument("pipeline_id")
    p_run.add_argument("--inputs")
    p_run.add_argument("--simulate", action="store_true")

    p_ind = sub.add_parser("industries", help="list by industry")
    p_ind.add_argument("industry", nargs="?", default=None)

    p_emit = sub.add_parser("emit", help="emit artifact to standards format")
    p_emit.add_argument("id")
    p_emit.add_argument("format")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0

    catalog = load_catalog()
    handler = {
        "list":       cmd_list,
        "describe":   cmd_describe,
        "search":     cmd_search,
        "depends":    cmd_depends,
        "validate":   cmd_validate,
        "run":        cmd_run,
        "stats":      cmd_stats,
        "industries": cmd_industries,
        "emit":       cmd_emit,
    }[args.command]
    return handler(args, catalog) or 0


if __name__ == "__main__":
    sys.exit(main())
