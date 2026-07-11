# Repo Polish Loop Command

Copy and paste this as one line. It runs the repo polish goal forever with the
local Codex CLI and logs output to `.agent/repo-polish-loop.log`.

```bash
cd "$HOME/ai_harness_and_knowledge_facts_and_logic_website_sharing" && mkdir -p .agent && while :; do P="$(cat _repos/shared-backend-components/context/codex/repo-polish-loop-goal.md; printf '\n\nRun the repo-polish loop now. Do not ask questions. Pick the highest-impact failing gate, make durable changes, validate them, record what changed, then continue. If blocked, switch paths.')"; "$HOME/.local/bin/codex" exec -C "$PWD" -s workspace-write -m gpt-5.5 "$P" 2>&1 | tee -a .agent/repo-polish-loop.log; sleep 10; done
```

Stop it with `Ctrl-C`.

The command is under 4000 characters and relies on the local Codex config for
approval policy and reasoning effort. In this environment, `codex exec` reported
`model: gpt-5.5` and `reasoning effort: xhigh`.
