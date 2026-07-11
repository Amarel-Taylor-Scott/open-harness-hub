# Go-Live & CI/CD Checklist — AI Done Right portfolio

> Owner-facing runbook. Generated 2026-07-04 from a full-portfolio audit + the launch-readiness
> drive. **Headline finding: CI/CD needs essentially ZERO custom secrets** — all 6 workflows run on
> the auto-provisioned `GITHUB_TOKEN`; a grep of `.github/` finds no `secrets.*`. The blocker was
> never keys — it was migration drift, now largely fixed. `[✓ done]` = fixed this session;
> `[owner]` = needs you.

## Current state

- Proof suite: **844/844 green** on the pinned Python 3.11 (was falsely "843 green" — one committed
  3.12-only syntax error + two hidden pyprefix bugs, all fixed).
- CI workflows: re-pathed for the `_repos/` layout + a `compileall` 3.11 syntax gate added, so they
  no longer go red on merge.
- Vault: **SOPS + age** built and gate-green (ADR 0011). Fragility guardrails + the deploy preflight
  import-gate fixed. Multi-substrate primitive store (pg/pgvector + git-like + bucket) wired.

## Part A — Get CI/CD green (zero custom secrets)

1. `[owner]` **Push the branch + open a PR to `main`.** `feat/scale-goals-and-hygiene` is far ahead;
   pages/emit/release only fire on push to `main`. Remote is still personal
   `Amarel-Taylor-Scott/open-harness-hub` — optionally migrate it to the `AIDoneRight` org.
2. `[owner]` **Repo Settings → Actions → General → Workflow permissions = "Read and write".**
   `emit.yml` force-pushes `dist-published`; `release.yml` creates Releases via the built-in token.
   Default read-only makes both 403. This is a toggle, **not a secret**.
3. `[owner]` **Repo Settings → Pages → Source = "GitHub Actions".** `pages.yml` deploys MkDocs via
   OIDC. If the repo is private, Pages needs a paid plan — else make it public.
4. `[owner]` **Keep the Actions "Secrets and variables" page EMPTY for CI.** Verified: zero
   `secrets.*` in any workflow. Model/Fly/Cloudflare keys are **deploy-time** secrets set in the
   HOST dashboard, never in GitHub Actions. `[✓ done]` workflow paths + compileall gate.

## Part B — The vault (runtime secrets) — `[owner]`, one-time

5. `age-keygen -o age.key` → put the **public** key in `.sops.yaml` (replace the placeholder).
6. Put the **private** key in a GitHub **Environment** secret named `SOPS_AGE_KEY` (never committed).
7. Edit `_repos/shared-backend-components/secrets/secrets.dev.env` with your real values, then
   `sops -e -i secrets/secrets.dev.env`. Keys stay grep-visible; values are encrypted. `.github/
   workflows/deploy-secrets.yml` decrypts them in CI. `[✓ done]` policy, template, gate, CI workflow.

## Part C — First public deploy (pick the cheapest that works)

8. `[owner]` **$0 now:** deploy a static surface from `dist/sites/` to **Cloudflare Pages** (free) for
   an immediate public URL. **Full backend at lowest cost:** one **Hetzner** CX22/CPX11 (~€4–5/mo)
   running `docker compose -f _repos/shared-backend-components/deploy/docker-compose.deploy.yml`, or
   **Fly** (per-app).
9. `[owner]` **Host auth:** Fly → `fly auth login` then `fly tokens create org -x 720h` → `FLY_API_TOKEN`.
10. `[owner]` **Showcase token:** every public web app needs `OH_SHOWCASE_TOKEN` — `openssl rand -hex 32`,
    set it per app (`fly secrets set OH_SHOWCASE_TOKEN=…`).
11. `[owner]` **DNS:** Cloudflare token scoped `Zone:DNS:Edit`; CNAME each domain (aidoneright.dev /
    baltor.ai / teleon.dev / openhubforai.*) → `<app>.fly.dev` (proxied) or the VPS IP.

## Part D — Model plane (all optional; surfaces run on the deterministic fallback with NO key)

12. `[owner, optional]` To enable live LLM, set **one** of `NVIDIA_API_KEY` (build.nvidia.com, free
    eval credits, resolved first), `OLLAMA_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY` as a
    HOST secret (not GitHub Actions).

## Part E — Verify

13. `PYTHONPATH=. python3 _repos/shared-backend-components/scripts/deploy/preflight.py` must print GO.
    `[✓ done]` the false NO-GO (a PYTHONPATH artifact). Remaining NO-GO is **real** config drift (a
    stale generated fly doc + a missing queue-key watch file) — a genuine pre-deploy fix, tracked below.

## Remaining engineering follow-ups (not owner-blocking)

- **Repo split:** `shared-backend-components` is 26 GB / 82,880 tracked files (90% of the repo). Move
  the loose primitive scratch **through the new multi-substrate store** (pg/pgvector + git-like +
  bucket), then git-subtree-split the per-product backends. (Owner decided: never untrack — load into
  the store or archive, keep tracked.)
- **Deploy config drift:** regenerate `fly/README.generated.md` + the k8s/compose queue-key watch files.
- **Vault chokepoint:** 49 scattered `os.environ` reads bypass `key_holder.resolve` — funnel them
  through the one seam so a rotating/per-tenant vault becomes trivial (env-injection works today).
- **Stale facts:** `MIGRATION-STATUS.md` line 12 + the CLAUDE.md `22/9` registry count (recompute).
