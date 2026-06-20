#!/usr/bin/env python3
"""scripts.operator_add_allow_rules — OPERATOR-RUN ONLY.

Adds the four scoped Bash allow rules to .claude/settings.local.json so the agent can run
the code-reviewed platform handoff stack and Playwright tooling. The agent authored this
file but is hard-blocked from executing it (an agent must never expand its own permission
boundary); run it yourself:

    python3 scripts/operator_add_allow_rules.py

or inside the Claude Code session (the ! must PREFIX the command in the input box):

    ! python3 scripts/operator_add_allow_rules.py

Idempotent; prints exactly what changed. Scope: docker compose, node, npm install,
npx playwright — nothing else.
"""
from __future__ import annotations

import json
from pathlib import Path

SETTINGS = Path(__file__).resolve().parents[1] / ".claude" / "settings.local.json"
RULES = [
    "Bash(docker compose *)",
    "Bash(node *)",
    "Bash(npm install *)",
    "Bash(npx playwright *)",
]


def main() -> int:
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    allow = data.setdefault("permissions", {}).setdefault("allow", [])
    added = [rule for rule in RULES if rule not in allow]
    allow.extend(added)
    SETTINGS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"settings: {SETTINGS}")
    print(f"added   : {added if added else 'nothing — all rules already present'}")
    print(f"total allow rules: {len(allow)}")
    print("Next: tell the agent to proceed — it will bring up the stack, verify health "
          "through the gateway, open the tunnel, and record the video unprompted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
