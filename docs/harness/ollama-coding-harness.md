# Ollama Cloud coding harness — opencode + aider + `./build` (GLM 5.2 + Kimi K2.7-code)

A Claude-Code-independent coding harness driven by your **Ollama Cloud** plan. Two interactive agents
(**opencode**, **aider**) and one **autonomous self-running loop** (`./build`), all on the same lane:
GLM 5.2 (frontier reasoning) + Kimi K2.7-code (coding-specialized), with Qwen3-Coder / DeepSeek-V4 / GLM-4.7
available as alternates.

## The lane (already provisioned)
- Endpoint: `https://ollama.com/v1` (OpenAI-compatible). Key: the **owner key already in the gitignored
  `.env`** (`OLLAMA_API_KEY` / `OH_LLM_API_KEY`). Nothing to add.
- `scripts/harness_env.sh` puts the lane on the environment (maps the `.env` key onto `OPENAI_API_BASE` /
  `OPENAI_API_KEY` / `OLLAMA_API_KEY`). `./build` sources it automatically; for interactive sessions:
  ```bash
  source scripts/harness_env.sh
  ```
- **Models are reasoning models** — they emit chain-of-thought in a `reasoning`/`thinking` field and the answer
  in `content`. Give them room (don't cap `max_tokens` tiny) or `content` can come back empty. opencode/aider
  default to high output limits, so this only bites raw API calls.

## 1) opencode — the interactive / agentic daily driver
Config: `opencode.json` (repo root). Provider `ollama-cloud`; two primary agents:
- **`build`** (default) → **Kimi K2.7-code** — edits files, runs commands.
- **`plan`** → **GLM 5.2** — read-only architect/reasoning.
```bash
source scripts/harness_env.sh
opencode                                   # TUI, default build agent (Kimi)
opencode --agent plan                      # switch to GLM 5.2 for design/review
opencode -m ollama-cloud/glm-5.2           # force a specific model
opencode run -m ollama-cloud/kimi-k2.7-code "implement X"   # headless one-shot
```

## 2) aider — precise, git-native edits (architect/editor split)
Config: `.aider.conf.yml` + `.aider.model.metadata.json` (repo root). Main model = **GLM 5.2 (architect,
plans)**, editor-model = **Kimi K2.7-code (writes the diff)** — aider's architect mode maps exactly to the
model split.
```bash
source scripts/harness_env.sh
aider                                       # interactive; auto-commits each accepted edit
aider --message "add a --json flag to scripts/foo.py" scripts/foo.py   # scripted one-shot
aider --no-architect --model openai/kimi-k2.7-code file.py             # single-model, Kimi only
```
The proof gate is wired as aider's `test-cmd` (`run_proofs.py`); run it with `/test` in a session or
`--auto-test` to feed failures back to the model.

## 3) `./build` — the AUTONOMOUS loop (open-model replacement for "Claude Code drives the build")
Each cycle: pick a backlog item (`data/dev-intel/proposals.jsonl`, skipping owner-gated) → drive a coding agent
to implement it → run the **proof gate** → **commit only on green, revert on red**. Marching orders:
`docs/goals/ollama-build-loop.md`.
```bash
./build test            # offline self-test (no model/git writes)
./build run --dry-run   # preview: shows the selected task + prompt, makes no edits
./build run             # ONE real cycle (edits + gate + commit/revert)
./build bg              # run continuously, detached, until ./build stop
./build status          # cycles / committed / reverted / last
./build logs            # tail the loop log
./build stop            # clean halt after the current cycle
# pass-through flags:
./build bg --harness aider --architect --max-cycles 30 --gate teleon
```

### Safety rails (in `scripts/build_loop.py`)
- **Never runs on `main`/`master`** (branch first).
- **Checkpoint-commit before each cycle** → a red cycle's `git reset --hard HEAD` discards only the agent's bad
  changes, never pre-existing work (lossless). Only *newly-created* untracked files are removed on red.
- **The proof gate is the objective arbiter**, outside the model's control. Green gates the auto-commit.
- **Owner-gated proposals are skipped** (brand/pricing/strategy/vocabulary need a human warrant — see
  `docs/codex/change-verification-contract.md`).
- Own **STOP flag** (`.agent/BUILD_STOP_REQUESTED`), separate from `./loop` and `./enrich`, so all three coexist.

### Recommended way to run it cleanly
`./loop` (the flywheel daemon) auto-commits the working tree, which can tangle with `./build`'s commits. For a
clean autonomous build session, **pause the flywheel first** (`./loop stop`), run `./build bg`, then resume the
flywheel when done. Keep an eye on the first few cycles (`./build logs`) before leaving it unattended.

## Switching the model split
| Want | opencode | aider |
|---|---|---|
| Kimi writes code (default) | `--agent build` | default (`--architect`, editor=Kimi) |
| GLM reasons / reviews | `--agent plan` | `--no-architect --model openai/glm-5.2` |
| Cheaper bulk coder | `-m ollama-cloud/qwen3-coder:480b` | `--model openai/qwen3-coder:480b` |

## Troubleshooting
- **Empty completion / no edit:** the reasoning model spent the token budget on `reasoning`. Raise the output
  limit; for raw curl, read `reasoning`/`reasoning_content` as `_llm_client.chat()` does.
- **`429` / rate limit:** the Ollama plan is throttling — back off; `./build` logs and moves on. Switch model
  (`--model glm-4.7`) or wait.
- **Auth error:** confirm `.env` has `OLLAMA_API_KEY`; `source scripts/harness_env.sh` prints `key=<set>`.
- **Model list:** `opencode models ollama-cloud` (live from your plan) — 35 models incl. glm-5.2, kimi-k2.7-code,
  qwen3-coder:480b, deepseek-v4-pro.
