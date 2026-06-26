#!/usr/bin/env python3
"""scripts.hooks.hygiene_guard — fail-open PostToolUse advisory: catch rot/misuse AT EDIT TIME (owner 2026-06-25).

Fires after Edit/Write/MultiEdit. On the single edited file it flags (ADVISORY ONLY — never blocks the edit):
  - surfaces (web/ · dist/sites, .html/.jsx/.js): HARD placeholder tells (lorem ipsum / PLACEHOLDER) — northstar law.
  - source (.py in scripts/ · src/): a burst of bare magic numbers — nudge toward named constants (no-magic-values).
  - docs (.md): repo-path references to files that don't exist — broken/rotten context.
ALWAYS exits 0 (fail-open: any error → allow). Warnings go to stdout + .agent/hygiene-warnings.log so they persist.
This is the "keep it clean over time" half of the contract pair (the gate's check_* are the other half).
"""
import json
import os
import re
import sys
from pathlib import Path

_COMMON = {"100", "200", "204", "301", "302", "400", "401", "403", "404", "429", "500",
           "1000", "2024", "2025", "2026", "256", "384", "512", "768", "1024", "2048", "4096"}


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if data.get("tool_name") not in ("Edit", "Write", "MultiEdit"):
            return 0
        fp = (data.get("tool_input") or {}).get("file_path") or ""
        if not fp:
            return 0
        repo = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".").resolve()
        p = Path(fp)
        if not p.exists():
            return 0
        rel = str(p.resolve()).replace(str(repo) + "/", "")
        text = p.read_text(encoding="utf-8", errors="replace")
        warns: list[str] = []

        if ("web/" in rel or "dist/sites" in rel) and p.suffix in (".html", ".jsx", ".js"):
            if re.search(r"lorem ipsum|\bPLACEHOLDER\b|placeholder text", text):
                warns.append(f"northstar: placeholder/dummy content in surface {rel} — surfaces must be real, not stubs")
        elif p.suffix == ".py" and ("scripts/" in rel or "src/" in rel):
            nums = {n for n in re.findall(r"(?<![\w.])-?\d{2,}(?![\w.])", text) if n.lstrip("-") not in _COMMON}
            if len(nums) >= 20:
                warns.append(f"no-magic-values: {len(nums)} distinct bare numbers in {rel} — give the load-bearing ones named constants + a unit/rationale")
        elif p.suffix == ".md" and "archive/" not in rel:
            refs = set(re.findall(r"((?:\.\.?/)*(?:archive|scripts|src|docs|architecture|web)/[A-Za-z0-9_./-]+\.(?:py|md|json|jsx|js))(?![A-Za-z])", text))
            broken = [m for m in sorted(refs) if not any(c in m for c in "*{}<>")
                      and not ((repo / m).exists() or (p.parent / m).resolve().exists())]
            for m in broken[:3]:
                warns.append(f"rotten-context: {rel} references missing {m}")

        if warns:
            msg = "⚠️ hygiene_guard (advisory):\n" + "\n".join("  - " + w for w in warns[:5])
            print(msg)
            try:
                log = repo / ".agent" / "hygiene-warnings.log"
                log.parent.mkdir(parents=True, exist_ok=True)
                with log.open("a", encoding="utf-8") as fh:
                    fh.write(msg + "\n")
            except OSError:
                pass
    except Exception:
        return 0  # fail-open: never block an edit on a hook error
    return 0


if __name__ == "__main__":
    sys.exit(main())
