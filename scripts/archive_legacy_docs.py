#!/usr/bin/env python3
"""archive_legacy_docs — deterministically find SUPERSEDED docs and archive them LOSSLESSLY.

Part of the developer review loop: as the board (panel_review) and the team supersede documents, stale docs should
move OUT of the live tree so they stop misleading agents — but per the lossless-distillation law (docs/codex/
lossless-distillation.md), superseded != deleted. This scanner finds docs carrying explicit supersession markers in
their header and MOVES them to archive/legacy/<original path>, recording origin + reason in a manifest so every move
is reversible. NEVER deletes; dry-run by DEFAULT (mass-moving docs is a structural change — show before applying).

Detection is deterministic + conservative (header-only, strong markers) so it never archives a live doc:
  - frontmatter `status: superseded|archived|deprecated|obsolete`
  - a header line (first 40 lines) matching SUPERSEDED BY / DEPRECATED / NO LONGER CANONICAL / DO NOT USE / OBSOLETE
Excludes _reference/ (never touched/republished), archive/ itself, and anything under .git/.

  --self-test     offline proof: detection on a fixture, dry-run moves nothing, archiving is lossless + reversible
  --scan [paths]  list archive candidates (default: docs/)  [dry-run]
  --apply [paths] actually move candidates to archive/legacy/ + write the manifest (lossless)
CLI: python3 scripts/archive_legacy_docs.py --scan
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = REPO / "archive" / "legacy"
MANIFEST = ARCHIVE_ROOT / "_manifest.jsonl"
DEFAULT_SCAN = ["docs"]
EXCLUDE_PARTS = {"_reference", "archive", ".git", "node_modules", "repo_reference"}

_FRONTMATTER_STATUS = re.compile(r"^status:\s*(superseded|archived|deprecated|obsolete)\b", re.I | re.M)
_HEADER_MARKERS = re.compile(
    r"\b(superseded by|deprecated[:.]| deprecated\b|no longer canonical|do not use|this (doc|file) is obsolete|"
    r"obsolete[:.]|moved to archive|replaced by [a-z])", re.I)
_HEADER_LINES = 40


def _excluded(p: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in p.relative_to(REPO).parts)


def detect(path: Path) -> str | None:
    """Return the supersession reason for a doc, or None. Conservative: frontmatter status OR a strong header marker
    in the first %d lines.""" % _HEADER_LINES
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    head = "\n".join(text.splitlines()[:_HEADER_LINES])
    # a TOMBSTONE redirect (left at an original path after a move) is NOT a fresh candidate — never re-archive it
    # (it carries `status: archived_tombstone` + a "moved to archive" banner; re-detecting it caused archive churn).
    if re.search(r"^status:\s*archived_tombstone", head, re.I | re.M) or "Archived — moved to" in head:
        return None
    m = _FRONTMATTER_STATUS.search(head)
    if m:
        return f"frontmatter status: {m.group(1).lower()}"
    m = _HEADER_MARKERS.search(head)
    if m:
        return f"header marker: {m.group(0).strip().lower()}"
    return None


def scan(paths: list[str]) -> list[dict]:
    out = []
    for base in paths:
        root = REPO / base
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.md")):
            if _excluded(p):
                continue
            reason = detect(p)
            if reason:
                out.append({"path": str(p.relative_to(REPO)), "reason": reason})
    return out


def _git_mv(src: Path, dst: Path) -> bool:
    try:
        r = subprocess.run(["git", "mv", str(src), str(dst)], cwd=REPO, capture_output=True, text=True)
        return r.returncode == 0
    except Exception:
        return False


def apply_archive(candidates: list[dict], *, now: str = "") -> list[dict]:
    """Move each candidate to archive/legacy/<original path>, lossless: content preserved, origin recorded in the
    manifest (reversible). Uses git mv when possible (keeps history), else shutil.move."""
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    moved = []
    for c in candidates:
        src = REPO / c["path"]
        if not src.exists():
            continue
        dst = ARCHIVE_ROOT / c["path"]
        if dst.exists():
            continue                              # defense-in-depth: NEVER overwrite an already-archived file
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not _git_mv(src, dst):
            shutil.move(str(src), str(dst))
        rec = {"original_path": c["path"], "archived_path": str(dst.relative_to(REPO)),
               "reason": c["reason"], "archived_at": now or "unspecified", "reversible": True,
               "status": "archived_superseded"}
        moved.append(rec)
        with open(MANIFEST, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    write_archive_readme()
    return moved


def _referenced_live(basename: str) -> bool:
    """True if a tracked, NON-archive file still references this filename (would be a dangling ref after a move)."""
    try:
        r = subprocess.run(["git", "grep", "-l", "--", basename], cwd=REPO, capture_output=True, text=True)
    except Exception:
        return False
    for ln in r.stdout.splitlines():
        if not ln or "_manifest" in ln or ln.startswith("archive/legacy"):
            continue                                  # ignore the manifest + the archived copies themselves
        return True                                   # a live, non-archive file references it -> would dangle
    return False


def reconcile_references(*, now: str = "") -> list[dict]:
    """Avoid the fragile-context trap of dangling references: for each archived doc that LIVE files still reference,
    leave a TOMBSTONE redirect at the original path (so links resolve + the status is explicit), pointing to the
    archived copy + any successor. Lossless: the real content is in archive/legacy/; only a labeled pointer remains."""
    if not MANIFEST.exists():
        return []
    recs = [json.loads(ln) for ln in MANIFEST.read_text(encoding="utf-8").splitlines() if ln.strip()]
    tombstoned = []
    for r in recs:
        orig = REPO / r["original_path"]
        if orig.exists():
            continue                                  # path still present (already tombstoned or not moved)
        if not _referenced_live(Path(r["original_path"]).name):
            continue                                  # unreferenced — no tombstone needed
        archived = REPO / r["archived_path"]
        successor = ""
        try:
            for ln in archived.read_text(encoding="utf-8", errors="replace").splitlines()[:40]:
                if any(k in ln.lower() for k in ("superseded by", "replaced by", "see ")):
                    successor = ln.strip().lstrip("> #").strip()
                    break
        except Exception:
            pass
        orig.parent.mkdir(parents=True, exist_ok=True)
        body = (f"---\nstatus: archived_tombstone\nmoved_to: {r['archived_path']}\n---\n"
                f"# ⚠️ Archived — moved to `{r['archived_path']}`\n\n"
                f"This document was archived on {r.get('archived_at','')} (reason: {r.get('reason','')}). "
                f"It is **preserved, not deleted** — this stub keeps existing links resolving.\n\n"
                + (f"Successor / context: {successor}\n\n" if successor else "")
                + "Full content + status index: `archive/legacy/README.md`.\n")
        orig.write_text(body, encoding="utf-8")
        try:
            subprocess.run(["git", "add", str(orig.relative_to(REPO))], cwd=REPO, capture_output=True, text=True)
        except Exception:
            pass
        tombstoned.append({"path": r["original_path"], "moved_to": r["archived_path"], "successor": successor})
    return tombstoned


def write_archive_readme() -> Path:
    """Generate archive/legacy/README.md — the clearly-labeled STATUS index for everything archived (what, why,
    when, status) + how to restore. Kept current from the manifest so the archive always carries its own context."""
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    recs = []
    if MANIFEST.exists():
        recs = [json.loads(ln) for ln in MANIFEST.read_text(encoding="utf-8").splitlines() if ln.strip()]
    lines = [
        "# Archive — superseded / outdated context (PRESERVED, not deleted)",
        "",
        "> STATUS: every file here is **archived, not deleted** — moved out of the live tree so it stops misleading",
        "> humans + agents, but kept (tracked) for lineage + rollback. Per the lossless-distillation law",
        "> (docs/codex/lossless-distillation.md): superseded != deleted.",
        "",
        f"Items archived: **{len(recs)}** · source of truth: `archive/legacy/_manifest.jsonl` (one JSON record each).",
        "",
        "## What's here (status index)",
        "",
        "| status | original path | reason | archived |",
        "|---|---|---|---|",
    ]
    for r in sorted(recs, key=lambda x: x.get("original_path", "")):
        lines.append(f"| {r.get('status','archived')} | `{r.get('original_path')}` | {r.get('reason','')} | {r.get('archived_at','')} |")
    lines += [
        "",
        "## Restore an item",
        "```bash",
        "# move it back to its original path (reverse of the archive move)",
        "git mv archive/legacy/<original-path> <original-path>",
        "```",
        "The `_manifest.jsonl` records the exact `original_path` for every entry, so any archive is fully reversible.",
        "",
    ]
    readme = ARCHIVE_ROOT / "README.md"
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme


def _self_test() -> int:
    global REPO, ARCHIVE_ROOT, MANIFEST
    import tempfile
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    # detection on fixtures
    with tempfile.TemporaryDirectory() as d:
        live = Path(d) / "live.md"; live.write_text("# Current\n\nThis is the canonical doc.\n")
        sup = Path(d) / "old.md"; sup.write_text("---\nstatus: superseded\n---\n# Old\n")
        dep = Path(d) / "dep.md"; dep.write_text("# Thing\n\n> DEPRECATED: replaced by the new spec.\n")
        legacy_word = Path(d) / "ok.md"; legacy_word.write_text("# Fine\n\nWe preserve legacy path context as founding thesis.\n")
        ck("a live doc is NOT flagged", detect(live) is None)
        ck("frontmatter status: superseded IS flagged", detect(sup) is not None)
        ck("a DEPRECATED header IS flagged", detect(dep) is not None)
        ck("the bare word 'legacy' in body is NOT flagged (conservative)", detect(legacy_word) is None)
        tomb = Path(d) / "tomb.md"
        tomb.write_text("---\nstatus: archived_tombstone\nmoved_to: archive/legacy/x.md\n---\n# ⚠️ Archived — moved to `archive/legacy/x.md`\n")
        ck("a TOMBSTONE is NOT re-detected (prevents archive churn/overwrite)", detect(tomb) is None)

    # dry-run scan moves nothing; excludes _reference
    before = {str(p) for p in REPO.rglob("*.md")}
    cands = scan(DEFAULT_SCAN)
    after = {str(p) for p in REPO.rglob("*.md")}
    ck("scan is read-only (dry-run moves nothing)", before == after)
    ck("scan excludes _reference/ and archive/", not any(any(x in c["path"] for x in ("_reference/", "archive/")) for c in cands))
    print(f"  (scan found {len(cands)} archive candidate(s) under {DEFAULT_SCAN})")

    # lossless archive round-trip in a temp repo-like dir
    with tempfile.TemporaryDirectory() as d:
        _REPO, _AR, _MF = REPO, ARCHIVE_ROOT, MANIFEST
        try:
            REPO = Path(d); ARCHIVE_ROOT = REPO / "archive" / "legacy"; MANIFEST = ARCHIVE_ROOT / "_manifest.jsonl"
            (REPO / "docs").mkdir(parents=True)
            f = REPO / "docs" / "stale.md"; f.write_text("---\nstatus: archived\n---\n# Stale\nbody\n")
            content = f.read_text()
            moved = apply_archive([{"path": "docs/stale.md", "reason": "frontmatter status: archived"}], now="2026-06-21")
            ck("archive MOVES the file out of the live tree", not f.exists())
            archived = REPO / moved[0]["archived_path"]
            ck("archived content is byte-identical (lossless)", archived.exists() and archived.read_text() == content)
            ck("the manifest records origin + marks reversible (rollback target)",
               MANIFEST.exists() and json.loads(MANIFEST.read_text().splitlines()[0])["original_path"] == "docs/stale.md")
        finally:
            REPO, ARCHIVE_ROOT, MANIFEST = _REPO, _AR, _MF

    print("\n" + ("PASS - archive_legacy_docs --self-test: conservative header-only detection (no false-positive on the "
                  "word 'legacy'), dry-run by default (read-only), archiving is LOSSLESS (content preserved, origin "
                  "recorded, reversible) and never deletes."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    paths = [a for a in argv if not a.startswith("--")] or DEFAULT_SCAN
    cands = scan(paths)
    if "--apply" in argv:
        moved = apply_archive(cands)
        print(f"archived {len(moved)} doc(s) -> {ARCHIVE_ROOT.relative_to(REPO)}/ (lossless; manifest at {MANIFEST.relative_to(REPO)})")
        for m in moved:
            print(f"  {m['original_path']} -> {m['archived_path']}  ({m['reason']})")
        return 0
    print(f"archive candidates under {paths} (dry-run — use --apply to move them losslessly):")
    for c in cands:
        print(f"  [{c['reason']}] {c['path']}")
    print(f"\n{len(cands)} candidate(s). Nothing moved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
