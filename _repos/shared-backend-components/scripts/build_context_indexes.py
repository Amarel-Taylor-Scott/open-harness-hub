#!/usr/bin/env python3
"""scripts/build_context_indexes — the deterministic context/MD INDEX maintainer for the `_repos/` layout.

Every derived index here is COMPUTED from the single source of truth
(`_repos/dev-rules-context/contracts/surface-registry.json` + each repo's `interface.json` + the on-disk
`context/` trees), never hand-typed — so the indexes never drift from the actual docs as the org grows.
It is a deterministic agent, not an LLM: offline, no network, no git, byte-identical on every rerun.

It regenerates three families of derived files (ADD-ONLY — it writes derived index files and the marked
region of the README; it never deletes or rewrites a source doc):

  (a) `_repos/<surface>/context/INDEX.md`  — per repo, every doc in that repo's `context/` tree listed
      with a one-line HOOK pulled from the doc itself (sorted by path → deterministic).
  (b) the computed region of `_repos/README.md` — the per-repo doc counts + the repo table — spliced
      BETWEEN generated markers so reruns are idempotent (the surrounding hand-written prose is untouched).
  (c) `_repos/INDEX.md`                     — the top-level map: every surface → its README / CLAUDE /
      EDGES / interface (+ its context index), read straight from the registry + the folders on disk.

`--write` regenerates. `--check` verifies everything is in sync WITHOUT writing (CI gate — non-zero if a
derived file is stale). `--self-test` is a pure offline proof on a tiny synthetic tree: indexes generate,
are sorted, and a rerun produces BYTE-IDENTICAL output (the determinism gate) + a mutation gate.

No hardcoded surface/repo names live in the logic — the surface set is read from the registry. No magic
values — every literal is a named constant.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
import tempfile
from pathlib import Path

# --- Locations (structural, not surface-specific) ---------------------------------------------------------
REPO = Path(__file__).resolve().parents[1]
REPOS_DIRNAME = "_repos"
REPOS = _resource(REPOS_DIRNAME)
# the single source of truth, relative to the _repos root (same file the edge-graph tools read).
REGISTRY_RELPARTS = ("dev-rules-context", "contracts", "surface-registry.json")

CONTEXT_DIRNAME = "context"
INDEX_FILENAME = "INDEX.md"
README_FILENAME = "README.md"
INTERFACE_FILENAME = "interface.json"
DOC_GLOB = "*.md"
# per-repo structural landmark files the top-level index maps each surface to (published entry points).
LANDMARK_FILENAMES = ("README.md", "CLAUDE.md", "EDGES.md", "interface.json")
CONTEXT_INDEX_RELPATH = f"{CONTEXT_DIRNAME}/{INDEX_FILENAME}"

# --- Display bounds (cosmetic truncation only; the FULL text always lives in the source) ------------------
HOOK_MAX_CHARS = 160       # one-line hook echoed next to a doc in a context INDEX
ROLE_MAX_CHARS = 90        # a surface's registry role, shown in the README table cell
ELLIPSIS = "…"        # single-char truncation marker (deterministic)

# --- Generated-region markers (idempotent splice into an otherwise hand-written README) -------------------
GEN_BEGIN = "<!-- BEGIN GENERATED: {tag} (build_context_indexes.py — do not hand-edit) -->"
GEN_END = "<!-- END GENERATED: {tag} -->"
README_TABLE_TAG = "repo-table"
README_ANCHOR = "## The repos"   # the region is spliced right after this heading on first run

# markdown-cell separators (kept as constants so the table shape has one definition).
NEWLINE = "\n"
CELL_PIPE_SUB = "/"        # a stray '|' inside a cell would break the table; substitute deterministically.
DEP_JOIN = " · "      # " · " between dependency ids
EMPTY_CELL = "—"      # "—"


# ==========================================================================================================
# Source-of-truth readers
# ==========================================================================================================
def _registry_path(repos_dir: Path) -> Path:
    return repos_dir.joinpath(*REGISTRY_RELPARTS)


def load_registry(repos_dir: Path = REPOS) -> dict:
    return json.loads(_registry_path(repos_dir).read_text())


def surfaces_sorted(reg: dict) -> list[str]:
    """The surface set comes from the registry — never a hardcoded list. Sorted for determinism."""
    return sorted(reg.get("surfaces", {}))


def context_dir(repos_dir: Path, surface: str) -> Path:
    return repos_dir / surface / CONTEXT_DIRNAME


def context_docs(repos_dir: Path, surface: str) -> list[Path]:
    """Every doc in a repo's context tree, sorted by path, EXCLUDING the generated INDEX.md (so a doc count
    is stable across the run that first creates INDEX.md — the key determinism invariant)."""
    cdir = context_dir(repos_dir, surface)
    if not cdir.is_dir():
        return []
    return sorted(p for p in cdir.rglob(DOC_GLOB) if p.is_file() and p.name != INDEX_FILENAME)


def doc_count(repos_dir: Path, surface: str) -> int:
    return len(context_docs(repos_dir, surface))


def interface_version(repos_dir: Path, surface: str) -> str:
    p = repos_dir / surface / INTERFACE_FILENAME
    if not p.exists():
        return ""
    try:
        return str(json.loads(p.read_text()).get("interface_version", ""))
    except (OSError, ValueError):
        return ""


# ==========================================================================================================
# One-line hook extraction (deterministic, offline)
# ==========================================================================================================
def _oneline(line: str) -> str:
    """Collapse a markdown line to plain single-line text: strip leading blockquote/heading/list markers and
    inline emphasis, collapse whitespace. Deterministic — the same input always yields the same output."""
    s = line
    while s[:1] in {">", "#", "-", "*", " "}:
        s = s[1:]
        s = s.lstrip() if s[:1] == " " else s
    s = s.replace("`", "").replace("**", "").replace("__", "")
    return " ".join(s.split())


def _truncate(s: str, limit: int) -> str:
    return s if len(s) <= limit else s[: limit - 1].rstrip() + ELLIPSIS


def extract_hook(path: Path) -> str:
    """A doc's one-line hook: the first non-heading, non-empty line (blockquote/STATUS lines count); falls
    back to the H1 title if the doc is only headings. Pure function of file bytes → deterministic."""
    title = ""
    try:
        text = path.read_text()
    except OSError:
        return ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if not title:
                title = _oneline(line)
            continue
        hook = _oneline(line)
        if hook:
            return _truncate(hook, HOOK_MAX_CHARS)
    return _truncate(title, HOOK_MAX_CHARS)


# ==========================================================================================================
# Renderers (each returns the full byte-deterministic content of one derived file / region)
# ==========================================================================================================
def render_context_index(surface: str, reg: dict, docs_with_hooks: list[tuple[str, str]]) -> str:
    role = _oneline(reg["surfaces"].get(surface, {}).get("role", ""))
    lines = [
        f"# Context index — `{surface}`",
        "",
        "> Generated by `scripts/build_context_indexes.py` from this repo's actual `context/` tree — do not",
        "> hand-edit; rerun the maintainer. Every doc below carries a one-line hook pulled from the doc itself.",
        "",
        f"**Role:** {role or EMPTY_CELL}",
        "",
        f"**Docs indexed:** {len(docs_with_hooks)}",
        "",
    ]
    if docs_with_hooks:
        for rel, hook in docs_with_hooks:
            lines.append(f"- **{rel}** — {hook}" if hook else f"- **{rel}**")
    else:
        lines.append("- (no docs yet)")
    return NEWLINE.join(lines) + NEWLINE


def render_readme_region(reg: dict, repos_dir: Path) -> str:
    """The COMPUTED region of the README: a summary line (surface count + total docs, computed — never
    hand-typed) plus the repo table with per-repo doc counts. Ends with a trailing newline."""
    surfaces = surfaces_sorted(reg)
    total_docs = sum(doc_count(repos_dir, s) for s in surfaces)
    summary = (f"_{len(surfaces)} surfaces · {total_docs} context docs indexed — computed from "
               f"`{'/'.join(REGISTRY_RELPARTS)}` + the on-disk `context/` trees, never hand-counted._")
    header = "| Surface → GitHub repo | Role | Depends on | Docs |\n|---|---|---|---|"
    rows = []
    for s in surfaces:
        spec = reg["surfaces"][s]
        repo = spec.get("repo", "")
        role = _truncate(_oneline(spec.get("role", "")), ROLE_MAX_CHARS).replace("|", CELL_PIPE_SUB)
        deps = DEP_JOIN.join(spec.get("may_depend_on", []) or []) or EMPTY_CELL
        docs = str(doc_count(repos_dir, s)) if context_dir(repos_dir, s).is_dir() else EMPTY_CELL
        rows.append(f"| **{s}** → `{repo}` | {role} | {deps} | {docs} |")
    return summary + NEWLINE + NEWLINE + header + NEWLINE + NEWLINE.join(rows) + NEWLINE


def render_top_index(reg: dict, repos_dir: Path) -> str:
    surfaces = surfaces_sorted(reg)
    total_docs = sum(doc_count(repos_dir, s) for s in surfaces)
    lines = [
        f"# `{REPOS_DIRNAME}/` index — every surface → its landmark files",
        "",
        "> Generated by `scripts/build_context_indexes.py` from "
        f"`{'/'.join(REGISTRY_RELPARTS)}` + the on-disk repo folders. Maps each surface to its README /",
        "> CLAUDE / EDGES / interface (+ context index). Do not hand-edit — rerun the maintainer.",
        "",
        f"**{len(surfaces)} surfaces · {total_docs} context docs.**",
        "",
    ]
    for s in surfaces:
        spec = reg["surfaces"][s]
        repo = spec.get("repo", "")
        ver = interface_version(repos_dir, s)
        heading = f"## `{s}` → `{repo}`" + (f" (interface {ver})" if ver else "")
        lines.append(heading)
        links = [f"[{fn}]({s}/{fn})" for fn in LANDMARK_FILENAMES if (repos_dir / s / fn).exists()]
        if context_dir(repos_dir, s).is_dir():
            links.append(f"[{CONTEXT_INDEX_RELPATH}]({s}/{CONTEXT_INDEX_RELPATH})")
        lines.append("- " + (DEP_JOIN.join(links) if links else "(no landmark files)"))
        exposes = spec.get("exposes", []) or []
        lines.append(f"- exposes: {', '.join(exposes) or EMPTY_CELL}")
        lines.append("")
    return NEWLINE.join(lines) + NEWLINE


# ==========================================================================================================
# Idempotent README splice
# ==========================================================================================================
def _markers(tag: str) -> tuple[str, str]:
    return GEN_BEGIN.format(tag=tag), GEN_END.format(tag=tag)


def _strip_leading_table(rest: str) -> str:
    """Drop leading blank lines + a contiguous markdown table at the start of `rest` (removes the stale
    hand-written table on first splice) and any blank lines right after it."""
    lines = rest.split(NEWLINE)
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        i += 1
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    return NEWLINE.join(lines[i:])


def splice_generated_block(text: str, tag: str, block: str) -> str:
    """Insert/replace `block` between the tag's markers. If the markers already exist, replace between them
    in place (idempotent); otherwise insert right after README_ANCHOR (removing the stale table there), or
    append if the anchor is absent. Rerunning is byte-identical because `block` is deterministic."""
    begin, end = _markers(tag)
    if not block.endswith(NEWLINE):
        block += NEWLINE
    region = begin + NEWLINE + block + end
    bi = text.find(begin)
    if bi != -1:
        ei = text.find(end, bi)
        if ei != -1:
            return text[:bi] + region + text[ei + len(end):]
    anchor = README_ANCHOR + NEWLINE
    ai = text.find(anchor)
    if ai == -1:
        sep = "" if text.endswith(NEWLINE) else NEWLINE
        return text + sep + NEWLINE + region + NEWLINE
    after = ai + len(anchor)
    rest = _strip_leading_table(text[after:])
    return text[:after] + NEWLINE + region + NEWLINE + NEWLINE + rest


# ==========================================================================================================
# Build orchestration
# ==========================================================================================================
def _planned_outputs(repos_dir: Path, reg: dict) -> list[tuple[Path, str]]:
    """Compute (path, new-content) for every derived file, without writing. Order: context indexes first
    (so their existence is settled), then the top index, then the README region."""
    outputs: list[tuple[Path, str]] = []
    for s in surfaces_sorted(reg):
        cdir = context_dir(repos_dir, s)
        if not cdir.is_dir():
            continue
        docs = [(p.relative_to(cdir).as_posix(), extract_hook(p)) for p in context_docs(repos_dir, s)]
        outputs.append((cdir / INDEX_FILENAME, render_context_index(s, reg, docs)))
    outputs.append((repos_dir / INDEX_FILENAME, render_top_index(reg, repos_dir)))
    readme = repos_dir / README_FILENAME
    if readme.exists():
        region = render_readme_region(reg, repos_dir)
        outputs.append((readme, splice_generated_block(readme.read_text(), README_TABLE_TAG, region)))
    return outputs


def build_all(repos_dir: Path, reg: dict, write: bool) -> dict:
    outputs = _planned_outputs(repos_dir, reg)
    changed: list[str] = []
    for path, content in outputs:
        existing = path.read_text() if path.exists() else None
        if existing != content:
            changed.append(path.relative_to(repos_dir.parent).as_posix())
            if write:
                path.write_text(content)
    return {
        "indexed_files": [p.relative_to(repos_dir.parent).as_posix() for p, _ in outputs],
        "changed": sorted(changed),
        "all_in_sync": not changed,
    }


# ==========================================================================================================
# Self-test — pure, offline, on a tiny synthetic tree (mutation + determinism gates)
# ==========================================================================================================
def _make_synthetic_tree(root: Path) -> dict:
    """Build a minimal but representative _repos tree: a registry with two surfaces (one with a context
    tree incl. a subdir, one without), landmark files, and a README with a stale hand table to be replaced."""
    reg = {
        "surfaces": {
            "zeta-surface": {   # deliberately not first alphabetically, to prove sorting is by registry
                "repo": "org-zeta", "role": "the zeta role, arbitrary name — proves no hardcoded surfaces",
                "kind": "product", "exposes": ["/api/zeta"], "may_depend_on": ["alpha-surface"],
            },
            "alpha-surface": {
                "repo": "org-alpha", "role": "the alpha substrate", "kind": "substrate",
                "exposes": ["registry"], "may_depend_on": [],
            },
        },
        "forbidden_edges": [],
    }
    reg_path = root.joinpath(*REGISTRY_RELPARTS)
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(json.dumps(reg))
    # alpha: context tree with a nested doc + landmark files
    a_ctx = root / "alpha-surface" / CONTEXT_DIRNAME
    (a_ctx / "sub").mkdir(parents=True, exist_ok=True)
    (a_ctx / "blackbox.md").write_text("# Alpha blackbox\n\n**Purpose.** Alpha is the substrate everyone uses.\n")
    (a_ctx / "sub" / "deep-note.md").write_text("# Deep note\n\n> STATUS: a nested doc hook line.\n")
    for fn in LANDMARK_FILENAMES:
        (root / "alpha-surface" / fn).write_text("{}" if fn.endswith(".json") else f"# alpha {fn}\n")
    (root / "alpha-surface" / INTERFACE_FILENAME).write_text(json.dumps({"interface_version": "0.1.0"}))
    # zeta: landmark files but NO context dir (must still appear in README table + top index, docs = —)
    (root / "zeta-surface").mkdir(parents=True, exist_ok=True)
    for fn in LANDMARK_FILENAMES:
        (root / "zeta-surface" / fn).write_text("{}" if fn.endswith(".json") else f"# zeta {fn}\n")
    # README with the anchor + a stale hand-written table that the splice must remove
    (root / README_FILENAME).write_text(
        "# repos\n\nIntro prose.\n\n## The repos\n\n"
        "| Folder | Old |\n|---|---|\n| stale | row |\n\n"
        "## Keep this section\n\nTrailing prose stays.\n"
    )
    return reg


def _snapshot(paths: list[Path]) -> dict[str, str]:
    return {p.as_posix(): (p.read_text() if p.exists() else "\0MISSING") for p in paths}


def self_test() -> int:
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / REPOS_DIRNAME
        root.mkdir()
        reg = _make_synthetic_tree(root)

        res1 = build_all(root, reg, write=True)
        all_out = [Path(td) / p for p in res1["indexed_files"]]

        # (1) a context INDEX generated for the surface WITH docs, listing docs sorted, with hooks.
        a_index = (root / "alpha-surface" / CONTEXT_DIRNAME / INDEX_FILENAME).read_text()
        checks.append(("alpha context index generated + names its docs",
                       "blackbox.md" in a_index and "sub/deep-note.md" in a_index))
        checks.append(("hook pulled from doc body (not the heading)",
                       "Alpha is the substrate everyone uses" in a_index))
        checks.append(("docs listed in sorted order (blackbox before sub/deep-note)",
                       a_index.index("blackbox.md") < a_index.index("sub/deep-note.md")))

        # (2) top-level index maps EVERY surface to its landmarks (sorted: alpha before zeta).
        top = (root / INDEX_FILENAME).read_text()
        checks.append(("top index maps both surfaces to README + interface",
                       "`alpha-surface`" in top and "`zeta-surface`" in top
                       and f"[{README_FILENAME}](alpha-surface/{README_FILENAME})" in top))
        checks.append(("top index sorts surfaces by registry key",
                       top.index("`alpha-surface`") < top.index("`zeta-surface`")))
        checks.append(("no-context surface still appears in top index",
                       "`zeta-surface`" in top))

        # (3) README region spliced between markers; computed counts present; stale table removed.
        readme = (root / README_FILENAME).read_text()
        begin, end = _markers(README_TABLE_TAG)
        checks.append(("README markers present + surrounding prose kept",
                       begin in readme and end in readme and "Trailing prose stays." in readme))
        checks.append(("README stale hand table removed", "| stale | row |" not in readme))
        checks.append(("README table has a computed doc count for alpha (2 docs)",
                       "| **alpha-surface** →" in readme and "| 2 |" in readme))
        checks.append(("README shows em-dash docs cell for the no-context surface",
                       f"| {EMPTY_CELL} |" in readme))

        # (4) DETERMINISM / IDEMPOTENCY gate — a second write is byte-identical.
        snap1 = _snapshot(all_out)
        build_all(root, reg, write=True)
        snap2 = _snapshot(all_out)
        checks.append(("rerun produces byte-identical output (determinism gate)", snap1 == snap2))

        # (5) creating INDEX.md did not change any count → --check is in sync after a write.
        checks.append(("--check reports in-sync after write (INDEX.md excluded from counts)",
                       build_all(root, reg, write=False)["all_in_sync"]))

        # (6) MUTATION gate — editing a source doc makes --check report drift (verifier can go red).
        (root / "alpha-surface" / CONTEXT_DIRNAME / "blackbox.md").write_text(
            "# Alpha blackbox\n\n**Purpose.** MUTATED hook text.\n")
        checks.append(("mutation to a source doc is detected by --check",
                       not build_all(root, reg, write=False)["all_in_sync"]))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - build_context_indexes:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - build_context_indexes: per-repo context INDEX.md (docs + one-line hooks), the README repo "
          "table + doc counts (spliced between generated markers), and the top-level _repos/INDEX.md are all "
          "computed from the surface-registry + context trees; sorted, byte-deterministic, mutation-gated.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate the _repos context/MD indexes from the single sources.")
    ap.add_argument("--self-test", action="store_true", help="pure offline proof on a synthetic tree")
    ap.add_argument("--write", action="store_true", help="regenerate every derived index file")
    ap.add_argument("--check", action="store_true", help="verify in sync WITHOUT writing (CI gate)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    reg = load_registry(REPOS)
    rep = build_all(REPOS, reg, write=args.write)
    print(f"  indexed {len(rep['indexed_files'])} derived file(s); "
          f"{len(rep['changed'])} {'written' if args.write else 'stale'}"
          + (f" (e.g. {rep['changed'][0]})" if rep["changed"] else ""))
    if args.check and not rep["all_in_sync"]:
        print("FAIL - build_context_indexes: derived indexes are stale (rerun with --write):\n  "
              + "\n  ".join(rep["changed"]))
        return 1
    print(f"PASS - build_context_indexes: context indexes {'regenerated' if args.write else 'verified'} "
          "in sync from the surface-registry + context trees.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
