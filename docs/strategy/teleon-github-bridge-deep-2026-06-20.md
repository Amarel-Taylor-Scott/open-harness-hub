# Teleon × git/GitHub — the bridge, explored from every angle (2026-06-20)

> Deep exploration of the brain-blast: **a Teleon capability unit IS a git repo; meet teams where their code
> lives, keep the governed abstraction on top.** Each angle below is backed by a working, proof-gated primitive
> (`git_backend_port`, `capability_pr`, `git_platform_operation_map`, `check_capability_pr_workflow`). Honesty:
> the competitive-landscape angle is working-knowledge (the live news sweep was rate-limited); re-verify dates.

## The one-line thesis
Microsoft/GitHub/GitLab/Cursor/Amazon are rebuilding git for the agentic era — making code **storage** and
**execution** first-class for agents. None of them govern whether the resulting capability is **correct, lifts, or
is safe.** Teleon rides *above* git: a capability unit is a familiar repo with branches/PRs/checks/merge, and the
**CI check is the eval-lift gate.** Familiar UI/UX removes the adoption barrier; the governed abstraction is the bonus.

## Angle 1 — Storage flexibility (bring-your-own-git)
`GitBackendPort` backs a unit's storage/versioning/diffs on our **internal git OR the client's GitHub / GitLab /
Gitea / Bitbucket**, same abstraction. A regulated client keeps their capability code in *their* repo under *their*
controls; a startup uses ours. One port, any backend. (`check_git_backend_port`.)

## Angle 2 — Adoption via familiarity
Every operation maps to a native git-platform term (`git_platform_operation_map`): **Pull Request == Merge Request**,
**Checks == Pipelines**, branches/commits/tags/notes are identical. A developer already knows the UI/UX — zero
learning curve. We ship a familiar repo/PR view (`capability-repo-demo.html`) that looks like a GitHub repo page.

## Angle 3 — The governed abstraction (the bonus nobody else has)
A capability **Pull Request** carries a *code diff AND a behavior diff* (the eval-lift Δ). Its **status check is the
governed gate**: a fork merges only if it **provably does not regress (lift_delta ≥ 0), stays within org policy, and
meets the accuracy floor.** A regression or an out-of-policy fork **cannot merge** — CI, but on *capability
correctness*, not just tests. (`check_capability_pr_workflow`.)

## Angle 4 — The competitive landscape (re-verify)
GitHub **Agent HQ** / Copilot coding agent (agent-authored PRs, agent identity), GitLab **Duo**, Azure DevOps +
agents, Cursor background agents, Amazon **Kiro/Q/CodeCatalyst** — all racing to let agents *write and run* code in
the repo. The white space they leave: **no eval-lift gate, no portable receipt of capability correctness, no
provider-neutral governance above the platform.** We integrate *with* them (store in their platform) rather than
competing on storage.

## Angle 5 — Data-separation law (why this is safe)
Governed metadata (lift / receipt / provenance) rides in a **notes sidecar** (`refs/notes/teleon/governance`), never
in the client's code blob — so their repo stays clean. **Tenant-private lineage stays in Teleon's control plane and
need not enter the client's repo at all.** A backend is a storage choice, never a source of truth (`serves_truth=false`).

## Angle 6 — Migration / mirror
Internal git is the canonical store; on **promotion**, push the governed snapshot to the client's platform (mirror),
or vice-versa. The port makes internal↔client a config flip, not a rewrite. Live external pushes are owner-gated
(network + client creds) with an offline mirror (DEFER GATE).

## Angle 7 — Agent-authored PRs (the autonomous loop, governed)
The self-optimizing unit can **open its own PR** for a proposed fork (e.g. distill-to-deterministic-rule); the
eval-lift gate auto-runs as the check; it **merges only if it lifts within policy.** Fully autonomous capability
improvement, but every change is a reviewable, gated, receipted PR — agent velocity *with* governance.

## Angle 8 — The "checks" reframe
CI checks ask "do the tests pass?" Our check asks **"does this capability provably lift and stay safe?"** That single
reframe turns the familiar PR flow into a governance plane — and it's portable across GitHub/GitLab/Gitea.

## Risks to own
- Live platform calls need the client's creds + respect their ToS/rate-limits → owner-gated, offline-mirrored.
- The data-separation law is load-bearing: never let tenant-private lineage land in the client's repo (sidecar +
  control-plane only).
- The landscape moves weekly — re-run the agentic-git news sweep (rate-limited this turn).

## What's built (proof-gated)
`src/teleon/storage/git_backend_port.py` · `src/teleon/storage/capability_pr.py` ·
`architecture/git_platform_operation_map.json` · `scripts/check_git_backend_port.py` ·
`scripts/check_capability_pr_workflow.py` (+ the familiar UI at `dist/sites/opencontexthub/capability-repo-demo.html`).
