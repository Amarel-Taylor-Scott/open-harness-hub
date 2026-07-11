# ADR 0011 — Platform secrets vault: SOPS + age (encrypted-in-repo values, one age key decrypts in CI)

## Status

Proposed — 2026-07-04. Supersedes the archived `production/vault/README.md` placeholder referenced by `.gitignore`. Additive only; no existing file changes behavior.

## Context

The credential plane single-sources secret **NAMES**, never **VALUES**:

- `_repos/shared-backend-components/architecture/credential_registry.json` catalogs **26 services / 33 unique env-var NAMES** with `rule: "env-var NAMES only — never a value"`.
- The runtime seam that consumes them is `src.teleon.runtime.credentials.env_value(name)` = `os.environ.get(name) or _dotenv().get(name)` (reads `os.environ`, then the git-ignored repo `.env`). `key_holder.KeyHolder.resolve()` calls it fresh on every request; `credentials.reachable()/status()` fan it out over all 26 services on every Ops Console render. There is **zero** runtime dependency on any secrets service today — the lookup is an infallible in-process read.
- Deploy-time delivery already exists by NAME only: `scripts/deploy/generate_provider_configs.py:113 secret_keys()` expands `deploy_topology.json.secret_group_contents` (9 groups) into `fly secrets set --stage <KEY>=<value>`. `scripts/deploy/preflight.py:check_no_secret_values()` blocks literal `sk-ant-/sk-or-v1-/ghp_/AKIA` from committed configs.

What is missing is a single source of **VALUES** with lineage/rollback, and a local-dev value delivery mechanism that isn't a hand-kept `.env`.

Two grounded constraints frame the decision:

1. **A confirmed drift bug.** `credential_registry.json` holds 33 runtime NAMES; `deploy_topology.json.secret_group_contents` covers only 23. **28 registry NAMES sit in no secret group**, including the platform-only `NVIDIA_API_KEY` (model_route treats it as first in the inference chain), `OH_EMBED_API_KEY` (embeddings hard-raises without it), and `OH_LLM_HOSTED_API_KEY`. Any vault design keyed on the topology groups reproduces this silent under-provisioning; a vault keyed on the **registry NAMES** fixes it.
2. **The repo is actively subtree-split** into per-surface public child repos (commit `610dfe487`). Git history is immutable and propagates into child repos and forks — so committing secret material demands hard exclusion of the ciphertext dir from every split and every published artifact, plus a rotation-on-leak policy.

The Foundational Law admission filter #4 (**DEPTH-BEFORE-BREADTH**) and the local-first / no-paid-cloud default bar us from standing up an always-on secrets service for capability no paying vertical needs yet.

## Decision

Adopt **SOPS + age** as the platform secrets vault:

- Secret **VALUES** are stored as **age-encrypted ciphertext committed to git**, keyed field-by-field on the `credential_registry.json` env-var NAMES (dotenv format: keys visible, values encrypted). This makes the ciphertext file the single grep-auditable source of VALUES with full git lineage = rollback target, matching the repo's move-never-delete / lossless-distillation ethos.
- A **single age private key** is the only secret-zero. It lives as **one GitHub Environment secret `SOPS_AGE_KEY`** (this is the minimal, necessary slice of Path A that B rides on) and, for the solo founder, on the dev machine for local `sops exec-env`.
- **CI decrypts, then hands off to the mechanism that already exists.** A deploy workflow runs `sops exec-env` to export the NAMES into the process env and pipes them into the same `fly secrets set --stage` / provider path (`generate_provider_configs.py`). Local dev runs `sops exec-env` instead of a hand-kept `.env`. **The resolver is untouched** — `credentials.env_value()` still reads `os.environ`.
- A new proof `scripts/check_sops_secrets.py` (registered in `PROOF_MODULES`, run by `run_proofs.py --self-test`) asserts: (a) every ciphertext key ∈ `credential_registry.json` NAMES and every `key_ownership in (platform, both)` NAME is present (closing the confirmed drift), (b) the file round-trips through decrypt, (c) no plaintext secret signature is committed (reusing `preflight.SECRET_VALUE_SIGNATURES`), (d) the ciphertext dir is excluded from every subtree split and every published `dist/` artifact.

**Blast-radius mitigations (mandatory, part of this decision):** the encrypted dir is added to the subtree split-exclude and to the published-dist ignore; the committed example uses **synthetic values only**; any leak of the age key is treated as a **full-portfolio rotation** event, documented in the README.

### Fallbacks (labelled, per the multi-path development law)

- **Fallback A — GitHub Environments + provider stores.** Not discarded: it is the bootstrap host for the single `SOPS_AGE_KEY` and the deploy-time delivery target. Refuted as a standalone vault because its NAMES span two unreconciled files (registry ⟂ topology) and its audit checks group→store, never registry→group — shipping green-but-under-provisioned (28 uncovered NAMES). B's `check_sops_secrets.py` enforces the registry→coverage direction, structurally closing that hole.
- **Fallback C — Infisical self-hosted.** Deferred. Add as ONE additive resolver branch inside `credentials._env_value` the day a paying regulated vertical needs live rotate-without-restart / per-tenant dynamic secrets / audit log. Its own boot secrets would live in the SOPS file, so B is its substrate, not its rival. Refuted now: always-on crown-jewel + bootstrap paradox + hot-path fail-closed, against DEPTH-BEFORE-BREADTH.
- **Fallback D — OpenBao self-hosted.** Deferred, highest ceiling. Same resolver-branch shape as C; chosen over C only under a contractual Vault-semantics requirement (dynamic DB creds / transit / KV-versioned rollback) that funds the seal/unseal + HA + backup burden. Refuted now: heaviest ops, hot-path fail-closed in the real integration mode, feature-nullified in the safe mode.

## Consequences

Positive:
- $0, no new always-on service, no availability/deploy dependency added to the credential hot path.
- Single source of VALUES with git lineage + rollback; field-level diffs show WHICH secret changed without revealing it.
- The vault is keyed on registry NAMES, so it **fixes** the confirmed 28-NAME topology drift rather than inheriting it.
- Resolver, key_holder, and the reachability plane are unchanged; local dev gains value delivery via `sops exec-env`.
- Reuses `preflight.check_no_secret_values` and the `run_proofs` self-test harness as guardrails.

Negative / accepted:
- Static-at-deploy: rotation = edit → re-encrypt → commit → redeploy/restart (the audit's rotate-without-restart HARD tier stays unmet until Fallback C/D is warranted). Accepted under DEPTH-BEFORE-BREADTH.
- One age key is a high-value secret-zero and a solo-founder SPOF; a leak mandates full-portfolio rotation and cannot un-commit historical ciphertext. Mitigated by split/dist exclusion + rotation policy, not eliminated.
- Adding/removing a recipient re-encrypts the files; team key management is manual until a real team exists.
- No per-tenant/programmatic dynamic secrets — deferred to the resolver-branch fallbacks.