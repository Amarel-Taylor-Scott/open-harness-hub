# Run & share the showcase (Gemma 4 + public URL) + run the overnight build loop

Two things this page covers:

1. **Run the paste-to-flow showcase locally** with Gemma 4 intelligence and a
   public `trycloudflare.com` URL you can send to a tester.
2. **Run the autonomous build loop** (`/loop /goal`) for hours — gym, overnight —
   without it stopping early.

---

## 1. Run & share the showcase

One command:

```bash
bash scripts/serve_showcase.sh
```

It auto-starts Ollama if installed, auto-detects your Gemma 4 model, prints the
local URL, and (if `cloudflared` is installed) opens a public tunnel and prints:

```
═══════════════════════════════════════════════════════════════
  PUBLIC URL  →  https://<random>.trycloudflare.com
  send this to your tester · saved to dist/showcase-tunnel-url.txt
═══════════════════════════════════════════════════════════════
```

Flags: `--port 8080`, `--model <ollama-tag>`, `--cpu` (force CPU), `--no-tunnel`.

### Prerequisites (installed to `~/.local`, no sudo)

The showcase site itself is **stdlib-only** — `python3 scripts/serve_builder.py`
works with zero installs (deterministic explainer, local URL only). For Gemma 4
intelligence and a public URL you need two binaries; ensure `~/.local/bin` is on
your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"   # add to ~/.bashrc to make permanent
```

- **cloudflared** (public URL):
  ```bash
  mkdir -p ~/.local/bin && curl -L \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o ~/.local/bin/cloudflared && chmod +x ~/.local/bin/cloudflared
  ```
- **Ollama + Gemma 4** (intelligence):
  ```bash
  curl -L https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64.tar.zst \
    -o /tmp/ollama.tar.zst && mkdir -p ~/.local && tar --zstd -C ~/.local -xf /tmp/ollama.tar.zst
  ollama serve &              # the launcher will also start this for you
  ollama pull gemma4
  ```

### GPU vs CPU
Ollama uses your NVIDIA GPU automatically when the driver is present (verify with
`nvidia-smi`) and falls back to CPU otherwise. An RTX 3060 (12 GB) runs `gemma4`
on GPU; `--cpu` forces CPU (slower, always works). The launcher prints which mode
it's in.

### If you don't see the public URL
`cloudflared` isn't installed/on PATH — install it (above) and re-run. The site
still serves locally at `http://127.0.0.1:8000` meanwhile.

---

## 2. Run the autonomous build loop overnight — `/loop /goal`

`/goal` is the build prompt (mission, capability-lift bar, phases, the six
supervisor gates, the work menu). `/direction` is its resilience contract — **no
terminal state, no early stop, branch on every block**. Both live in
`.claude/commands/` (Claude Code) and `.codex/prompts/` (Codex).

To run it continuously while you're away, wrap it in `/loop`:

```
/loop /goal
```

- `/loop /goal` — self-paced: the agent runs a `/goal` cycle, records a ledger
  entry, then schedules the next cycle and continues. Ideal for gym/overnight.
- `/loop 30m /goal` — fixed cadence (a cycle ~every 30 min).

Why it won't stop early: `/goal` + `/direction` define no completion state —
"task done" → next menu item, "phase complete" → next phase, "blocked/error" →
roll back to green and switch paths, "waiting on something external" → do other
work now. It only ends on your interrupt or a hard safety violation. Progress is
checkpointed in `.research-notes/autonomous-session-ledger.md` so it resumes
cleanly after any compaction or restart.

What it works on (already queued in the ledger): real embeddings (P1), the
premium pipeline grader, the Python-library → component standard, and more
capability-lift verticals — each as small, validated, committed batches.

> Tip: keep this Claude Code session open (or use the `/schedule` skill to run
> `/goal` as a scheduled remote routine) so the loop keeps firing while you sleep.
