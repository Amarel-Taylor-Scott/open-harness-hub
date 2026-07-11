# Operations Handbook — CI/CD · deployment · infrastructure management (index)

One page that ties the operational system together. Each piece is canonical elsewhere;
this is the map an operator (or Claude Code) works from daily.

## The system at a glance

| Layer | Tool | Canonical doc |
|---|---|---|
| Pipeline (CI) | GitHub Actions calling `just` stages ONLY (S5a) | `ci/github-actions.yaml` · STANDARDS S5 |
| Local = CI | `justfile`: lint · test · build · package · smoke · bench | `justfile` |
| Deploy | `scripts/deploy.py` — orient→plan→act→verify→receipt, incremental | `One-Click Runbook` · S5b (host pulls, CI never SSHes) |
| Topology | `services.json` — THE manifest (routes, kinds, health, budgets) | Pass 6 runbook |
| Routes | `scripts/gen_caddy.py` (generated gateway; `--check` drift gate) | same |
| Tunnel | `scripts/tunnel.sh` (quick) → terraform named tunnels (L1) | `terraform/main.tf` |
| Secrets | SOPS + age vault; env-injection seam | `vault/README.md` · S8 |
| Monitoring | /health + `just bench` → uptime-kuma → Prom (ladder) | S11 · GRADUATION.md |
| Cost/latency | budgets in manifest; bench + deploy receipts in `dist/` | S11 · latency_probe.py |
| Growth path | L0–L3 ladder + scenarios S-A…S-J | GRADUATION.md · SCENARIOS.md |
| Money | pro-forma + business plane adapters | `business/PRO-FORMA.md` · contracts/BUSINESS-PLANE.md |
| Marketing | GTM plan, channel playbooks | `business/MARKETING.md` |

## Operating cadences (adopt with the loop)

- **Per pass:** update pass log + G-ledger; every claim names its proof (S10).
- **Weekly:** `just bench` (latency vs budgets) · PMF funnel review per realm
  (activation events) · flaky-check triage (fix or delete within the week).
- **Monthly:** cost review — actuals vs PRO-FORMA.md; any ceiling breach needs a
  recorded decision (S10 violation otherwise) · dependency/action-pin refresh.
- **At every level change (L0→L1→L2→L3):** re-run the SCENARIOS.md math; record the
  trigger that justified the move; verify the reversal path still works.

## Runbooks (the short list)

- **Tunnel died:** expected (quick tunnels are ephemeral). `just tunnel`. Graduate to
  L1 named tunnel when churn costs > 30 min/week.
- **Service unhealthy after deploy:** deploy.py already failed loud. Check
  `dist/deploy-receipts.jsonl` for what changed; `just deploy --force <id>` after fix;
  host services print their own restart command.
- **Rollback:** containers are images — `docker compose up -d` the previous tag
  (deploy receipts record what shipped). State is append-only by design (S12), so
  rolling code back never corrupts data.
- **Secret leaked:** revoke + re-mint (everything is raw-once/hash-only by design);
  rotate the age key if the vault itself leaked; gitleaks in `just lint` is the backstop.
- **Cost spike:** LLM receipts attribute spend per key — find the key, check quota
  (G-4 until quotas land), revoke if abusive. Infra: check bench receipts + uptime-kuma
  before resizing anything.
