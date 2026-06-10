# Unblock the platform run — one command (operator-only)

The agent cannot expand its own permissions (hard block, by design). You can, in seconds.
Pick ONE of the three options below.

## Option A — inside this Claude Code session (recommended)

Paste this single line into the Claude Code prompt (the leading `!` runs it as YOU):

```text
! python3 -c "import json,pathlib; p=pathlib.Path('.claude/settings.local.json'); d=json.loads(p.read_text()); a=d.setdefault('permissions',{}).setdefault('allow',[]); [a.append(r) for r in ['Bash(docker compose *)','Bash(node *)','Bash(npm install *)','Bash(npx playwright *)'] if r not in a]; p.write_text(json.dumps(d,indent=2)); print('allow rules added:', a[-4:])"
```

## Option B — from any normal terminal (same effect)

```bash
cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing
python3 - <<'EOF'
import json, pathlib
p = pathlib.Path(".claude/settings.local.json")
d = json.loads(p.read_text())
allow = d.setdefault("permissions", {}).setdefault("allow", [])
for rule in ["Bash(docker compose *)", "Bash(node *)",
             "Bash(npm install *)", "Bash(npx playwright *)"]:
    if rule not in allow:
        allow.append(rule)
p.write_text(json.dumps(d, indent=2))
print("allow rules added:", allow[-4:])
EOF
```

## Option C — skip the rules and just run the platform yourself once

```bash
cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/design_handoff_platform_productionization/production
set -a && . ./.env && set +a
docker compose up -d --build
python3 scripts/deploy.py --status
```

## What the rules allow (scope)

Only the four blocked command families — running docker compose, node, npm install,
and npx playwright. Nothing else changes; every other action stays under the
existing permission system.

## What happens immediately after (no further action from you)

The agent will, unprompted:

1. `docker compose up -d --build` the reviewed platform stack (Caddy gateway :8080 +
   platform-core :8787; code review verdict: clean — see the bundle Pass-7 log).
2. Verify every `/health` THROUGH the gateway (`deploy.py --status`) and write the
   deploy receipt.
3. Open the TryCloudflare quick tunnel and record the real URL (never invented).
4. Record the through-the-gateway browser journey video into `artifacts/e2e/videos/`.
5. Clear gap **G-11** and backlog **Phase 0.1**, then continue the queue
   (events/A-B plane → `/service/*` handshake slice → ENDPOINTS alignment), one
   proof-backed pass at a time.
