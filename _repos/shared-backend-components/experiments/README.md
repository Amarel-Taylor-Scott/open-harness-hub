# experiments/ — Baltor skunkworks

A sandbox to **try new things fast** without endangering the proven core. Experiments here may be
messy, unproven, use the network, or pull in heavy/uninstalled deps — that's the point.

## The contract (enforced by `scripts/check_experiments_isolation.py`, a flywheel proof)
1. **No proven module imports `experiments/`.** Nothing in `scripts/` that the flywheel watches
   (`baltor_flywheel.PROOF_MODULES`) may `import experiments…`. So a broken experiment can NEVER turn
   the flywheel red or break the live demo. (The guard fails if this is violated.)
2. **Experiments may import the core freely** (`from scripts.context_graph import …`) and **emit onto
   the shared event bus** (`scripts.context_events.EventBus`) so a new idea shows up **live on
   `/dashboard`** alongside the proven engines — wire the admin server's shared `BUS` in, or run with
   your own bus.
3. **Real-or-labeled-SEAM still applies.** If a dep isn't installable on this host (Python 3.14, no
   pip → vendor to `/tmp/baltor-vendor` or label it a seam), print the exact next command; do not fake.

## Layout
- `_template/` — copy this to start a new experiment (it emits onto the bus → visible on the dashboard).
- `masfactory_context_swarm/` — Track B bakeoff seed: a Vibe-Graphing graph over the existing
  `context_swarm` agents (see `docs/research/masfactory.md`). Offline it runs the REAL swarm on the
  bus and records the MASFactory install seam; it does not fake a MASFactory run.

## Graduation path (skunkworks → proven core)
experiment proves valuable → harden it into a `scripts/…` module with an offline deterministic
`--self-test` → add it to `baltor_flywheel.PROOF_MODULES` → (if it produces dashboard value) wire it
into the admin server's `run_full_pipeline`. Only then does it become load-bearing.

## Run one
```bash
python3 experiments/_template/experiment.py
python3 experiments/masfactory_context_swarm/run.py
```
