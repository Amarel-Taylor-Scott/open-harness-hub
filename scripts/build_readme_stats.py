#!/usr/bin/env python3
"""Generate the accurate catalog-status block in README.md.

Replaces hand-typed counts (the "172 components / v0.3.0" drift bug, which was
~25x wrong) with numbers computed from the catalog, git, and the derived SQLite
DB. The block is fenced by markers and marked auto-generated.

Usage:
    python3 scripts/build_readme_stats.py            # rewrite the block in README
    python3 scripts/build_readme_stats.py --check     # exit 1 if README is stale

CI / validate can run --check so a stale count breaks the build instead of
rotting quietly. See docs/codex/no-magic-values.md.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import subprocess
from collections import Counter
from pathlib import Path

# Top-level scripts derive the repo root locally (matches build_catalog_db.py);
# scripts/_config.py is the shared helper for module-invoked scripts/db/*.
REPO = Path(__file__).resolve().parent.parent
CATALOG = REPO / "catalog"
SQLITE = REPO / "dist" / "catalog.sqlite"
EMIT_DIR = REPO / "scripts" / "emit"
SCRIPTS = REPO / "scripts"
CODE_TEMPLATES = REPO / "code-templates"
README = REPO / "README.md"

BEGIN = "<!-- BEGIN GENERATED:catalog-stats -->"
END = "<!-- END GENERATED:catalog-stats -->"
NOT_EMITTERS = {"__init__.py", "_lib.py", "all.py"}

# Inline computed counts: each `<!--N:key-->value<!--/N-->` in README prose is rewritten to the
# computed value, so a count stated in prose can never drift from reality (the canonical magic-value
# bug). `--check` fails on any stale inline value, exactly like the generated block.
INLINE_RE = re.compile(r"(<!--N:(\w+)-->)(.*?)(<!--/N-->)", re.S)


def _inline_counts() -> dict[str, int]:
    by_type = Counter(p.relative_to(CATALOG).parts[0] for p in _manifest_paths())
    foundry = SCRIPTS / "foundry"
    return {
        "demo_scripts": len(list(SCRIPTS.glob("demo_*.py"))),
        "foundry_modules": sum(1 for p in foundry.glob("*.py") if p.name != "__init__.py") if foundry.is_dir() else 0,
        "design_patterns": by_type.get("patterns", 0),
        "model_adapters": by_type.get("adapters", 0),
        "code_templates": sum(1 for p in CODE_TEMPLATES.iterdir() if p.is_dir() and p.name != "__pycache__") if CODE_TEMPLATES.is_dir() else 0,
        "emitters": _emitter_count(),
    }


def _splice_inline(text: str, counts: dict[str, int]) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(2)
        return f"{m.group(1)}{counts[key]}{m.group(4)}" if key in counts else m.group(0)
    return INLINE_RE.sub(repl, text)


def _manifest_paths() -> list[Path]:
    return [p for ext in ("*.yaml", "*.yml") for p in CATALOG.rglob(ext)]


def _tracked_manifest_count() -> int | None:
    try:
        out = subprocess.run(
            ["git", "ls-files", "catalog"],
            cwd=REPO, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return sum(1 for line in out.splitlines() if line.endswith((".yaml", ".yml")))


def _sqlite_counts() -> dict[str, int] | None:
    if not SQLITE.exists():
        return None
    con = sqlite3.connect(SQLITE)
    try:
        names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}

        def count(table: str) -> int:
            if table not in names:
                return 0
            return int(con.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0])

        return {
            "objects": count("artifacts"),
            "edges": count("edges"),
            "embeddings": count("embeddings"),
        }
    finally:
        con.close()


def _emitter_count() -> int:
    if not EMIT_DIR.exists():
        return 0
    return sum(1 for p in EMIT_DIR.glob("*.py") if p.name not in NOT_EMITTERS)


def render_block() -> str:
    paths = _manifest_paths()
    total = len(paths)
    by_type = Counter(p.relative_to(CATALOG).parts[0] for p in paths)
    by_type_str = " · ".join(f"{t} {n:,}" for t, n in by_type.most_common())

    tracked = _tracked_manifest_count()
    if tracked is None:
        committed_line = f"**Catalog manifests (schema-validated): {total:,}.**"
    else:
        committed_line = (
            f"**Catalog manifests (schema-validated): {total:,}** — "
            f"{tracked:,} committed to git, {total - tracked:,} machine-generated "
            f"candidates pending review/promotion."
        )

    db = _sqlite_counts()
    if db is None:
        db_line = "- **Derived query DB** (`dist/catalog.sqlite`): not built."
    else:
        emb = db["embeddings"]
        emb_note = (
            " (vector search pending — see docs/codex/billion-component-goal.md)"
            if emb == 0 else ""
        )
        db_line = (
            f"- **Loaded into the derived query DB** (`dist/catalog.sqlite`): "
            f"{db['objects']:,} objects, {db['edges']:,} relationship edges, "
            f"{emb:,} embeddings{emb_note}."
        )

    lines = [
        BEGIN,
        "<!-- Generated by scripts/build_readme_stats.py — do not edit by hand "
        "(see docs/codex/no-magic-values.md). -->",
        "",
        f"- {committed_line}",
        f"- **By type:** {by_type_str}.",
        db_line,
        f"- **Emitters** (`scripts/emit/`): {_emitter_count()}.",
        "",
        "_Counts are generated; run `python3 scripts/build_readme_stats.py` to "
        "refresh (`--check` fails on drift)._",
        END,
    ]
    return "\n".join(lines)


def _splice(text: str, block: str) -> str:
    if BEGIN not in text or END not in text:
        raise SystemExit(
            f"markers not found in {README}; add a {BEGIN} / {END} pair where the "
            "generated catalog-stats block should live."
        )
    head = text.split(BEGIN, 1)[0]
    tail = text.split(END, 1)[1]
    return head + block + tail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit 1 if README is stale")
    parser.add_argument("--self-test", action="store_true",
                        help="alias for --check (so the flywheel gate catches count drift)")
    args = parser.parse_args(argv)

    block = render_block()
    current = README.read_text(encoding="utf-8")
    updated = _splice_inline(_splice(current, block), _inline_counts())

    if args.check or args.self_test:
        if current != updated:
            print("README counts are STALE (block or inline); run scripts/build_readme_stats.py")
            return 1
        print("README counts (generated block + inline) are fresh.")
        return 0

    if current != updated:
        README.write_text(updated, encoding="utf-8")
        print("README catalog-stats block updated.")
    else:
        print("README catalog-stats block already fresh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
