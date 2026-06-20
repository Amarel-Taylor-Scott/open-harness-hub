# Teleon as a governed abstraction over git + a capability's many implementations (2026-06-20)

> Two linked brain-blasts, each now backed by a working, proof-gated primitive. The connective thesis: **meet
> teams where their code and tools already live, and keep the governed abstraction above.** Honesty note: the
> competitive-landscape sweep below is from working knowledge — the live news fan-out was rate-limited this turn;
> re-verify the dated claims before quoting externally.

## 1. The brain-blast: Teleon capability units ARE abstractions of git primitives

A capability unit's storage, versioning, diffs, branches, and metadata *are* git primitives. Meanwhile the
incumbents are rebuilding git/code platforms for the agentic era — GitHub (Agent HQ / Copilot coding agent,
agent-authored PRs, agent identity), Microsoft (Azure DevOps + agents), GitLab (Duo), and challengers (Cursor
background agents, Amazon Kiro / Q Developer / CodeCatalyst, Replit, Devin). **They are making code *storage* and
*execution* first-class for agents — none of them govern whether the resulting capability is correct, lifts, or is
safe.** Same wedge as everywhere else: *they store and run code; Baltor governs whether the capability is true.*

**The bridge (built):** `src/teleon/storage/git_backend_port.py` — one pluggable `GitBackendPort` so a capability
unit's storage/versioning/diffs work on our **internal git OR the client's GitHub / GitLab / Gitea / Bitbucket**,
behind the same abstraction. Two invariants make it safe:
- **Governance rides in a SIDECAR** (`refs/notes/teleon/governance`) — the client's code stays clean; receipts /
  measured lift / provenance never pollute their repo, and tenant-private lineage need not live there at all.
- **A backend is a storage choice, not a source of truth** (`serves_truth=false`); promotion/verification happen
  in Teleon's control plane wherever the bytes rest.
- Live external calls are **owner-gated** (network + the client's creds) with an offline mirror (the DEFER GATE).

**Why it's a huge bonus:** familiar git UI/UX + "store it in your own GitHub" removes the adoption barrier, while
the governed abstraction (the thing nobody else has) rides on top. Proof: `check_git_backend_port` (12 checks).

**Creative extensions (next):** a Teleon "PR" = a proposed capability fork carrying its lift/receipt in the notes
sidecar; semantic diffs of capability *behavior* (eval-delta), not just text; a familiar repo/branch/PR UI surface
over the abstraction; mirror-on-promote (internal canonical + push the governed snapshot to the client's platform).

## 2. The second brain-blast: a capability has MANY implementations (tools × models × keys)

A capability (entity-resolution, grounded-search, image-processing, …) is facilitated by a **variety of
implementation options** — internal repos, libraries, API hubs, models, LLMs — in different combinations. Built:
`architecture/capability_implementation_registry.json` (**9 capabilities × 25 options**) + the selector
`src/teleon/inference/implementation_selector.py`:
- each option declares its **tools / models / API-keys (by NAME, env refs only) + cost tier + determinism ceiling**;
- `select_implementation(capability, available_keys, objective)` picks the best **combination** for a tenant by
  what keys/models they actually have + their objective (cheapest capable / most deterministic), excludes options
  whose keys are missing, and returns ordered **fallbacks**. A key *unlocks* an option; `require_deterministic`
  admits only deterministic ones. Proof: `check_capability_implementation_registry`.

This is the runtime answer to *"a list of tools, API keys, models that can facilitate each capability in a variety
of combinations"* — and it composes with the descent (pick the cheapest/most-deterministic implementation) and the
model index (freshness-governed model choice).

## 3. The workspace inventory as a seed source

The operator's `/home/username/code_projects` (187 folders, ~50 products) is a goldmine of working implementations.
Staged as a governed candidate feed (`data/capability-candidates/discovered-feed-workspace-inventory-2026-06-20.json`,
**15 products** → registry capabilities): bq-entity-resolution → entity-resolution; giga-trader → quant-forecasting;
llm-safety-framework + gemma4_comp → trafficking-safety-eval; email_info_digesting → inbox-digest; Real-ESRGAN /
image_gen_v1 → image-processing; web_animation / ManimML → video-generation; agency_email_scraper → lead-discovery;
duecare-journey-android → on-device-llm; etc. **Discovery ≠ trust** — extract/clean-room the governed capability and
screen gap/lift before promotion; do not vendor wholesale.

## Risks / what to verify
- The agentic-git landscape moves weekly — re-run the live news sweep (it was rate-limited this turn).
- "Store in the client's GitHub" must respect *their* governance + the data-separation law (tenant-private lineage
  stays in our control plane, never their repo) — enforced by the sidecar design.
- The implementation registry is candidate-stage: each option needs its own license/lift intake before promotion.
