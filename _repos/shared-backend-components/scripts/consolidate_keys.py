#!/usr/bin/env python3
"""scripts.consolidate_keys — gather every API key / token on this machine into ONE master markdown file.

Owner-requested (2026-07-09): "create a single MD file with all of my keys and tokens." This walks the known key
locations (the gitignored `.agent/` pools, `~/.kaggle/`, a repo `.env`, `.agent/env.providers`) and writes a single
consolidated `.agent/ALL_KEYS.md`.

SAFETY (non-negotiable):
  * The output goes into `.agent/`, which is gitignored — it can never be committed.
  * This script prints ONLY filenames + entry counts to stdout — NEVER key values.
  * It refuses to write the master file anywhere that isn't gitignored.
  * It masks nothing in the FILE itself (the whole point is a usable key file), but the file is written 0600.

    python3 scripts/consolidate_keys.py            # write .agent/ALL_KEYS.md (safe summary to stdout)
    python3 scripts/consolidate_keys.py --dry-run  # show what WOULD be gathered (names + counts only)
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

_HERE = Path(__file__).resolve()
HOME = Path(os.path.expanduser("~"))

# ALL `.agent/` dirs up the tree (there are two: shared-backend-components/.agent and the monorepo-root/.agent that
# holds the provider pools) + ~/.agent. Nearest-first; deepest listed last.
_AGENT_DIRS = [p / ".agent" for p in _HERE.parents if (p / ".agent").is_dir()]
if (HOME / ".agent").is_dir() and (HOME / ".agent") not in _AGENT_DIRS:
    _AGENT_DIRS.append(HOME / ".agent")
# the canonical/main agent dir (for writing the master file) = the one holding the most *keys* files (the root pools)
_MAIN_AGENT = max(_AGENT_DIRS, key=lambda d: len(list(d.glob("*keys*.txt"))), default=_HERE.parents[2] / ".agent")
_ROOT = _MAIN_AGENT.parent

# (label, filename-in-.agent OR absolute path, kind) — kind: pool | env | raw | json
SOURCES = [
    ("OpenRouter", "openrouter_keys.txt", "pool"), ("Mistral", "mistral_keys.txt", "pool"),
    ("Ollama Cloud", "ollama_keys.txt", "pool"), ("SambaNova", "sambanova_keys.txt", "pool"),
    ("Together", "together_keys.txt", "pool"), ("Groq", "groq_keys.txt", "pool"),
    ("Cerebras", "cerebras_keys.txt", "pool"), ("NVIDIA NIM", "nvidia_nim_keys.txt", "pool"),
    ("GitHub token", "github_token.txt", "pool"), ("Gemini", "gemini_keys.txt", "pool"),
    ("RapidAPI", "rapidapi_keys.txt", "pool"), ("HuggingFace", "hf_keys.txt", "pool"),
    ("Render", "render_keys.txt", "pool"), ("Reka", "reka_keys.txt", "pool"),
    ("Featherless", "featherless_keys.txt", "pool"), ("GMI", "gmi_keys.txt", "pool"),
    ("Provider .env block", "env.providers", "env"),
    ("Kaggle access_token", HOME / ".kaggle" / "access_token", "raw"),
    ("Kaggle kaggle.json", HOME / ".kaggle" / "kaggle.json", "json"),
    ("Repo .env", _ROOT / ".env", "env"),
]


def _resolve(name_or_path) -> list[Path]:
    """A bare filename resolves across ALL .agent/ dirs; an absolute Path resolves to itself."""
    if isinstance(name_or_path, Path):
        return [name_or_path]
    return [d / name_or_path for d in _AGENT_DIRS]


def _entries_from(path: Path, kind: str) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if kind in ("pool", "env"):
        return [ln.rstrip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    return [ln for ln in lines if ln.strip()]


def _entries(name_or_path, kind: str) -> tuple[list[str], Path | None]:
    """Merge unique entries for a source across all candidate locations; return (entries, first-source-path)."""
    seen: set[str] = set()
    merged: list[str] = []
    src: Path | None = None
    for cand in _resolve(name_or_path):
        rows = _entries_from(cand, kind)
        if rows and src is None:
            src = cand
        for r in rows:
            if r not in seen:
                seen.add(r)
                merged.append(r)
    return merged, src


def _assert_gitignored(target: Path) -> None:
    """Refuse to write the master file unless its directory is gitignored. Uses the RELIABLE empirical probe (a fresh
    file that does NOT show as untracked in `git status` is ignored) — `git check-ignore` gives false negatives for
    files under a directory-pattern rule."""
    import subprocess
    d = target.parent
    probe = d / ".gitignore_probe_tmp"
    try:
        probe.write_text("x", encoding="utf-8")
        r = subprocess.run(["git", "-C", str(_ROOT), "status", "--porcelain", str(probe)],
                           capture_output=True, text=True, timeout=15)
        untracked = r.stdout.strip().startswith("??")  # '??' => NOT ignored; empty => ignored
    except FileNotFoundError:
        untracked = False  # git absent — .agent/ is the conventional gitignored dir; proceed
    finally:
        try:
            probe.unlink()
        except OSError:
            pass
    if untracked:
        raise SystemExit(f"REFUSING to write {target} — {d} is NOT gitignored (a probe file showed as untracked). "
                         f"Add it to .gitignore first.")


def build(dry_run: bool = False) -> dict:
    target = _MAIN_AGENT / "ALL_KEYS.md"
    present, missing = [], []
    blocks: list[str] = [
        "# ALL KEYS & TOKENS — master file",
        "",
        f"> Consolidated by `scripts/consolidate_keys.py` from {len(_AGENT_DIRS)} .agent dir(s). Lives in gitignored",
        "> `.agent/` — never committed. One section per source. Re-run to refresh. Do NOT paste into chat/PRs/logs.",
        "",
    ]
    for label, name_or_path, kind in SOURCES:
        rows, src = _entries(name_or_path, kind)
        if rows:
            present.append((label, src, len(rows)))
            rel = src
            try:
                rel = src.relative_to(_ROOT)
            except (ValueError, AttributeError):
                pass
            blocks.append(f"## {label}")
            blocks.append(f"_source: `{rel}` · {len(rows)} entr{'y' if len(rows) == 1 else 'ies'}_")
            blocks.append("```")
            blocks.extend(rows)
            blocks.append("```")
            blocks.append("")
        else:
            missing.append((label, name_or_path))

    if not dry_run:
        _assert_gitignored(target)
        target.write_text("\n".join(blocks) + "\n", encoding="utf-8")
        try:
            os.chmod(target, 0o600)  # owner read/write only
        except OSError:
            pass
    return {"target": target, "present": present, "missing": missing, "dry_run": dry_run}


def main() -> None:
    ap = argparse.ArgumentParser(description="Consolidate all API keys/tokens into one gitignored master MD file.")
    ap.add_argument("--dry-run", action="store_true", help="show what would be gathered (names+counts only)")
    args = ap.parse_args()
    r = build(dry_run=args.dry_run)
    # SAFE stdout: names + counts ONLY, never values
    print(("DRY RUN — would write" if r["dry_run"] else "WROTE") + f" {r['target']} (mode 0600, gitignored)")
    print(f"\nsources found ({len(r['present'])}):")
    for label, _path, n in r["present"]:
        print(f"  ✓ {label}: {n} entr{'y' if n == 1 else 'ies'}")
    if r["missing"]:
        print(f"\nnot present ({len(r['missing'])}):")
        for label, _path in r["missing"]:
            print(f"  – {label}")
    print("\n(no key values are printed; open the master file directly to view them)")


if __name__ == "__main__":
    main()
