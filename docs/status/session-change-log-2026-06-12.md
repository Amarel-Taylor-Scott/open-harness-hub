# Session change log — 2026-06-12 → 06-13

A complete record of everything changed in this working session, written because the model switched
**Claude Fable 5 → Opus 4.8** mid-session and the owner asked for an audit of every trim/adjustment.

## TL;DR — nothing destructive happened
- **48 commits**, **+20,062 / −208 lines**, across 200 files — overwhelmingly *additive* (new tools,
  examples, services). The 208 deletions are line-level replacements (e.g. fixing a wrong count), not
  file deletions.
- **ZERO files were deleted** (`git log --diff-filter=D 5a722649..HEAD` is empty). Verified.
- **Everything is committed and reversible** via git on branch `feat/scale-goals-and-hygiene`
  (session-start HEAD = `5a722649`; `git diff 5a722649..HEAD` is the full delta; `git revert <sha>`
  undoes any single commit).
- **All gates green after every batch:** flywheel **462/462**, deploy preflight **GO**, the trimmed
  image still boots and serves all 2682 components + the SPA.
- **Commit attribution note:** every commit carries `Co-Authored-By: Claude Fable 5` (a template
  carried over from the start-of-session summary). The later work (deploy/email/docs/responsive) was
  done as Opus 4.8. No behavioural difference — flagged for transparency.

## The "trims" (the only removals — all non-destructive)

| What | Commit | What it actually did | Reversible by |
|---|---|---|---|
| **Docker image trim** | `54bb7e02` | Added 5 lines to `.dockerignore` excluding `artifacts/`, `media/`, `e2e/`, `archive/`, `*.webm` **from the built image only** (2.92GB → 1.62GB). These dirs are NOT runtime deps. **They still exist in the repo, untouched.** | deleting those `.dockerignore` lines |
| **Video archiving** | (filesystem, pre-commit) | Moved 195 *older* e2e recordings to `artifacts/e2e/videos-archive/<date>/`; kept the 21 most-recent in `artifacts/e2e/videos/`. These are **gitignored artifacts** (never in git). Nothing deleted. | `mv` them back |
| **Cohort dead-code** | `f13ed074` | Removed ONE junk placeholder line (`naive = sum(... .__class__ and 1 ...)`) that was never referenced. | `git revert f13ed074` |

If you want the image to include everything again, the only change to undo is the `.dockerignore`
block — `git revert 54bb7e02`.

## Adjustments (existing files edited — what & why)

- **README.md** (`48a1856a`): six hand-typed counts had drifted from reality (e.g. "11 demo scripts"
  but 20 exist). Replaced with inline `<!--N:key-->value<!--/N-->` markers **computed** by
  `scripts/build_readme_stats.py` and **gated** by a new flywheel proof, so they can't drift again.
  The taxonomy table was relabeled to the canonical seven-primitive model (it used forbidden
  "knowledge pack / rule pack" terms). No information removed — examples kept, counts corrected.
- **38 docs** (`48a1856a`): superseded names reconciled to the locked decisions —
  `ContextIsEverything → AI Done Right` *where it presented as the current parent brand*,
  `OCTS → CTS` (prose only), `Purpose Runtime Control Tower → Teleon Control Tower`. **Preserved
  verbatim:** the lowercase `contextiseverything` slug/paths/ids (stable identifiers),
  `architecture/brand.json` (already canonical), founding-thesis mentions, and the migration doc.
  Verified by `check_brand_canonical` (PASS) — the brand single-source is intact.
- **Deploy** (`d43b60f3`, `f11b7ef3`, `54bb7e02`): added `foundry-model` + `email-plane` secret
  groups to `architecture/deploy_topology.json` (so inference + email keys reach the right apps);
  prebuilt the catalog vector store into the `Dockerfile` (instant boot); regenerated `fly/*.toml`
  + `deploy/docker-compose.deploy.yml` from the topology (generated files; `--check` PASS).
- **scripts/email_port.py** (`d43b60f3`): implemented the real Resend/Postmark HTTP transports that
  were previously declared-but-stubbed ("transport not wired"). Keyed → real send; unkeyed →
  `NotConfigured` (unchanged honest behaviour; self-test intact).
- **scripts/identity_local_service.py** (`d43b60f3`): verify link uses `AIDR_PUBLIC_BASE` when set
  (absolute link for real email); relative fallback unchanged for dev.
- **CSS** (`ea38b096`, `9051a9bc`, `9eb0064c`, `994cdbfb`, others): responsive fixes only — mobile
  top-bar/footer overflow, pricing-grid stacking, modality-tab wrapping. No content removed.
- **scripts/showcase/server.py** (`59c42803`): added `rewrite_bundle_html` so cross-product bundle
  pages load offline from local `/vendor/` instead of a CDN. Pure addition.

## Additions (the bulk — new files/features, ~+20k lines)
11 showcase pipelines + the examples gallery; 4 e2e tools (adversarial video verifier, confused-user
explorer, QA stress harness, responsive audit); the receipt/state/llm-plane local services; the
catalog→runtime processor bridge; the foundry scorer ladder; Mistral/OpenRouter inference lanes; and
research/strategy docs. All gated in the flywheel.

## Continuation (06-13) — receipt/state/mailbox wired into the deploy topology
The 3 backend services that existed in the registry but were **not** in the cloud topology are now
deployable, and the mailbox's cross-app delivery path is wired end-to-end. All additive; no behaviour
changed for local dev (every new path is env-gated and skipped when the env var is unset).

- **`architecture/deploy_topology.json`**: added 3 backend services — `receipt` (:9426), `state`
  (:9427), `mailbox` (:9428) — each health-gated (`/healthz`), own 1GB volume, mesh-addressable. Added
  `OH_SEAM_MAILBOX_BASE: "@mailbox"` to all 4 web services and `MAILBOX_INGEST_URL: "@mailbox"` to
  identity. Regenerated `fly/*.toml` (+3 new: mailbox/receipt/state) + `deploy/docker-compose.deploy.yml`
  (generated files; `--check` PASS, preflight **GO**).
- **Why mailbox needs an HTTP ingest path:** on Fly each app has its own volume, so identity (which
  renders the verification email) and mailbox (which displays it) can't share an outbox filesystem.
  `scripts/email_port.py` ConsoleAdapter now **also** pushes the rendered mail to `MAILBOX_INGEST_URL`
  (best-effort; a mailbox hiccup is swallowed so email never blocks registration). `scripts/mailbox_local_service.py`
  gained `store_message()` + `POST /api/mailbox/ingest` to receive it. The web tier already proxied
  `/api/mailbox/` → the seam, so the reviewer's register→verify-email→click flow now works across
  separate apps. Verified with a live socket test (ingest 201 → inbox renders → bad path 404 → bad JSON 400)
  and a new deterministic self-test check (mailbox now 6/6).
- **receipt/state** are **private** server-to-server services (`is_truth:false` / `truth_authority:false`)
  with no consumer yet **by design** — "wiring into the topology" means making them deployable + reachable
  on the internal mesh (`@receipt`/`@state`), which is done. No fake consumer was invented (warrant rule).
  They share a mount path but use distinct files (`receipts.jsonl` vs `state-log.jsonl`) on separate
  per-app volumes — no collision.
- **`dist/promptfoo/*.yaml` (115 files)**: flywheel-regenerated to replace stale `TODO: replace with
  rows` placeholders with real `file://` dataset globs + row counts. **Deterministic** (identical diff
  hash across two flywheel runs) — committed separately from the wiring as housekeeping, not mixed in.

Gates after this batch: flywheel **462/462**, preflight **GO**, mailbox **6/6**, receipt **10/10**,
state **9/9**, live ingest end-to-end **PASS**.

## How to review or roll back
- Full session delta: `git diff 5a722649..HEAD`
- Any single change: `git show <sha>` then `git revert <sha>` if unwanted
- Re-verify health any time: `python3 scripts/baltor_flywheel.py --once` (expect 462/462) and
  `python3 scripts/deploy/preflight.py` (expect GO)
