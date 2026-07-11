#!/usr/bin/env python3
"""Scaffold a new component manifest.

Usage:
  python _repos/shared-backend-components/scripts/new.py harness my-new-thing
  python _repos/shared-backend-components/scripts/new.py pipeline format-response
  python _repos/shared-backend-components/scripts/new.py rule-pack grep my-grep-pack
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# Resolve the SUBSTRATE root (the dir that holds the `scripts` package) via the scripts/_repo_paths.py sentinel —
# NOT `.aidoneright-root`, which sits at the MONOREPO root (no `scripts/` package) and breaks `from scripts.*`/
# `from src.*` on a bare `python3 _repos/shared-backend-components/scripts/<f>.py` launch. install() then
# prepends every code root (repo root + each _repos/*/backend + shared-backend-components) so both resolve.
import sys
from pathlib import Path
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()
from scripts._repo_paths import resource as _resource  # noqa: E402

import re
import sys
from datetime import date
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parent.parent
CATALOG = _resource("catalog")

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

TYPES = {
    "harness", "pipeline", "benchmark", "rule-pack", "knowledge-pack",
    "logic-pack", "tool", "persona", "adapter", "rubric", "dataset",
}


def envelope(type_: str, slug: str) -> str:
    today = date.today().isoformat()
    return dedent(f"""        id: "{type_}/{slug}"
        type: {type_}
        version: "0.0.1"
        name: "TODO: human name"
        description: |
          TODO: one paragraph plain-language description.
        authors:
          - name: "TODO"
        license: "MIT"
        industry:   ["cross_industry"]
        capability: []
        modality:   ["text"]
        lifecycle:  "experimental"
        trust_boundary: "local"
        created: "{today}"
        updated: "{today}"
        """).lstrip()


def harness_body() -> str:
    return dedent("""
        kind: "model_harness"
        tier: "primary"
        applied_layers: []
        consumes: []
        emits:    []
        logic_paths:
          - id: "main"
            label: "Main path"
            steps: []
            model_call: "required"
            verification: []
        knowledge_packs: []
        logic_packs:    []
        model_io:
          input:  "TODO"
          output: "TODO"
        model_targets:
          - id: "default"
            label: "Default"
            transport: "ollama"
            role: "TODO"
            required: false
            default: true
            trust_boundary: "local"
        input_verification: []
        output_verification: []
        privacy_boundaries:
          raw_input: "stays local"
        """)


def pipeline_body() -> str:
    return dedent("""
        task: |
          TODO: one-sentence task.
        pipeline_kind: "TODO"
        inputs: []
        outputs: []
        defaults: {}
        steps: []
        """)


def rule_pack_body(family: str) -> str:
    return dedent(f"""
        family: "{family}"
        rules: []
        """)


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    type_ = args[0]
    if type_ not in TYPES:
        print(f"unknown type {type_!r}. choose one of: {', '.join(sorted(TYPES))}", file=sys.stderr)
        return 1

    if type_ == "rule-pack":
        if len(args) < 3:
            print("rule-pack needs <family> <slug>")
            return 1
        family, slug = args[1], args[2]
        body = envelope(type_, slug) + rule_pack_body(family)
        out_dir = CATALOG / "rule-packs" / family
    else:
        slug = args[1]
        body = envelope(type_, slug)
        if type_ == "harness":
            body += harness_body()
            out_dir = CATALOG / "harnesses"
        elif type_ == "pipeline":
            body += pipeline_body()
            out_dir = CATALOG / "pipelines"
        else:
            out_dir = CATALOG / (type_ + "s")
            if type_ == "knowledge-pack":
                out_dir = CATALOG / "knowledge-packs"
            elif type_ == "logic-pack":
                out_dir = CATALOG / "logic-packs"
            elif type_ == "adapter":
                out_dir = CATALOG / "adapters"

    if not SLUG_RE.match(slug):
        print(f"slug {slug!r} is not lowercase-with-dashes", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.yaml"
    if out_path.exists():
        print(f"{out_path} already exists; aborting", file=sys.stderr)
        return 1
    out_path.write_text(body)
    print(f"wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
