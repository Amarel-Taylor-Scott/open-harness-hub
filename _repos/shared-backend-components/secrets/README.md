# Platform secrets vault (SOPS + age) — owner setup

Encrypted VALUES are committed here; the ONE age private key lives as the GitHub Environment secret
`SOPS_AGE_KEY` and decrypts in CI. The app never decrypts at runtime — SOPS only populates
`os.environ`, which the unchanged runtime seam (`credentials.env_value` → `key_holder.resolve`)
already reads. Coverage + no-leak + the seam handoff are enforced by
`../scripts/check_sops_secrets.py` (wired into `run_proofs.py`).

## One-time
1. Install: `brew install sops age` (or `apt-get install -y age` + the sops release binary).
2. Generate the age keypair: `age-keygen -o age.key` (`age.key` is the PRIVATE key — NEVER commit it).
3. Put the PUBLIC key (`age1...`) into `/.sops.yaml`, replacing the placeholder recipient.
4. Fill real values into `secrets.dev.env`, then encrypt in place: `sops -e -i secrets.dev.env`
   (commit the ciphertext; the plaintext is now gone). The key list is 1:1 with
   `architecture/credential_registry.json`; `check_sops_secrets.py` fails on any drift, so add a new
   provider by adding it to the registry first, then adding the key here.
5. Add the PRIVATE key to GitHub: repo Settings → Environments → `<surface>` → Secrets →
   new secret `SOPS_AGE_KEY` = full contents of `age.key`. Set env protection rules + required reviewers.

## Local dev (replaces a hand-kept `.env`)
```
export SOPS_AGE_KEY="$(cat age.key)"
sops exec-env secrets.dev.env 'python -m scripts.showcase --port 8080'
```
→ the NAMES land in `os.environ`; `key_holder`/`credentials.env_value` pick them up unchanged.

## Rotate a secret
`sops secrets.dev.env` (edit) → commit → re-run `deploy-secrets.yml` (or `fly secrets set`).

## Add/remove a team recipient
edit `/.sops.yaml` recipients → `sops updatekeys secrets.dev.env`.

## Leak response (MANDATORY)
A leak of `age.key` OR `SOPS_AGE_KEY` = FULL-PORTFOLIO ROTATION: regenerate the age key, re-encrypt,
rotate EVERY provider key (git history + subtree-split child repos retain old ciphertext forever).

## Invariants (enforced by `check_sops_secrets.py`)
- `secrets.dev.env` keys == `credential_registry.json` NAMES (platform/both covered; no orphans).
- This dir is excluded from every subtree split + published dist — single source
  `../scripts/deploy/publish_exclude.json` + `/.dockerignore` + this dir's `.gitattributes`
  (`export-ignore`). Never publish ciphertext.
- Never commit a real value in plaintext; `deploy.preflight.SECRET_VALUE_SIGNATURES` + this check guard it.
- The runtime seam (`credentials.env_value`/`key_holder.resolve`) is UNCHANGED — SOPS only sets env vars.
