# Vault — secrets handling (S8, decided Pass 6)

**Decision: SOPS + age** for this stage of the project. Reviewed against the field:

| Option | Verdict | Why |
|---|---|---|
| **SOPS + age** | **adopt** | File-based, offline, zero servers to run. Secrets live encrypted *in the repo* (`vault/secrets.enc.yaml`); the age private key lives only on your machine (`~/.config/aidr/age.key`). Perfect for local-first + one operator + agents; diffable, backed up with the repo, no SaaS dependency. |
| HashiCorp Vault / OpenBao | later | The right answer when there are services that must fetch secrets dynamically at runtime with leases/rotation. Running a Vault server today is more ops than the whole platform. OpenBao (the open fork) is the candidate when this graduates. |
| Infisical / Doppler | pass | Good DX but a SaaS account becomes the root of trust — conflicts with the local-first, no-external-dependency goal. |
| Plain `.env` | floor | What we had: fine, but unencrypted at rest and easy to leak into backups. Stays as the escape hatch (`just vault-export` falls back to it). |

## The flow

```bash
just vault-init      # once: generates the age keypair OUTSIDE the repo, prints the public key
# put the public key into .sops.yaml (committed):
#   creation_rules:
#     - path_regex: vault/.*\.enc\.yaml$
#       age: <your-age-public-key>
just vault-edit      # opens secrets in $EDITOR via sops; saved ciphertext-only
just vault-export    # decrypts → .env (gitignored) for compose + services
```

What goes in the vault: `CORE_JWT_SECRET`, `CORE_SIGNING_SECRET`, every
`SERVICE_<ID>_SECRET`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, tunnel tokens.

## Rules (binding, S8)

1. The age **private key never enters the repo** or the vault. Losing it = re-mint
   every secret (they're all re-mintable by design — raw-once keys, re-handshakes).
2. Only `*.enc.yaml` ciphertext is committed. `.env` stays gitignored; gitleaks in
   `just lint` is the backstop.
3. Per-service injection stays env-based (compose `environment:`) — services never
   read the vault directly, so swapping SOPS → OpenBao later touches ONE recipe
   (`vault-export`), nothing else.
4. No fake secrets: `vault-export` with no vault falls back to your existing `.env`
   and says so; nothing invents values.

## Graduation triggers
- A second human operator → shared age recipients (sops supports multiple keys).
- Runtime secret rotation / leases needed → OpenBao server, same env-injection seam.
- Cloud deploy via terraform → terraform reads the same sops file (carlpett/sops provider).
