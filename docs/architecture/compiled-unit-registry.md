# Compiled-Unit Registry — the per-capability `deploy_topology`

**Date:** 2026-06-11. **Status:** built + self-tested (22 registry checks inside the compiler `--self-test`).
**Code:** `src/teleon/compiler/registry.py` · **CLI:** `python -m src.teleon.compiler --register|--list|--rollback` ·
**Durable state:** `dist/local-services-state/teleon-compiler/compiled-units.jsonl` (the Fly volume mount).

## The gap this closes

The compiler (`src/teleon/compiler/compile.py`) turns a **promoted** capability into a `CompiledRuntimeUnit`, and
`emit.py` renders it to a Fly machine / k8s Job / local process. But until now **nothing persisted which
capability-version was compiled to which runtime.** There was no per-CAPABILITY analog of the per-SERVICE
`architecture/deploy_topology.json`: no way to ask *"what is the latest compiled unit for capability X"*, to roll
back to its predecessor, or to drive auto-deploy-on-promotion. The unit even *carries* a `rollback_target` field —
but it was **carried, never consumable**: nothing held the predecessor to roll back to.

`docs/strategy/teleon-self-improving-runtime-vision.md` (§Stage 5 GAP (d), §Stage 6) and
`docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md` (step 4) both name this exact hole as the
*"registry of promoted runtimes"* Stage 6 promised. This module **is** that registry.

## What it is — an append-only event log, folded to state

The registry is a durable, **append-only JSONL** of two record kinds, folded into current state on read:

| kind | meaning |
|---|---|
| `register` | adds a compiled unit; it becomes the **active** unit for its capability and **demotes** the prior active one (which becomes this unit's `rollback_target`). |
| `demote` | marks a unit **no longer active without deleting it** — lossless supersession. The unit stays in `history`. |

Current state — which unit is active per capability, the full history, the rollback target — is a **deterministic
fold** over the log (the latest-line-wins idiom `runs.jsonl` already uses), recomputed on construction
(rebuild-on-start) and kept in sync as events append.

### Record shape (`CompiledUnitRegistryRecord`)

A `register` record: `{kind:"register", record_version, unit:<full CompiledRuntimeUnit>, active, registered_at,
rollback_target, supersedes}`. `registered_at` is the unit's own `provenance.compiled_at` (caller-supplied — the
registry **reads no clock**). `rollback_target`/`supersedes` name the predecessor's `unit_id` (`""` for the first).
A `demote` record: `{kind:"demote", record_version, unit_id, demoted_by, reason, demoted_at}`.

## API (`CompiledUnitRegistry`)

- `register(unit, *, make_active=True)` — **idempotent by `unit_id`** (itself a pure hash of the compile inputs):
  re-registering the same unit returns the existing record, no duplicate append, no forked rollback chain. On a new
  unit it demotes the prior active unit for the capability and **stamps it as this unit's `rollback_target`** — the
  registry is the authority on the real predecessor (it overrides any caller value).
- `latest_for(cap)` — newest unit by `(capability_version, compiled_at, unit_id)`, regardless of active state.
- `latest_active_for(cap)` — the currently-**active** unit (the live runtime). Exactly one per capability.
- `history(cap)` — **every** unit ever registered (active + demoted), in deterministic order. Lossless timeline.
- `rollback_target(cap)` — **REAL rollback:** the predecessor of the active unit — the exact preserved prior unit
  the active one names. `None` when there is no predecessor (first compile); **raises `RegistryIntegrityError`**
  when the active unit names a predecessor the log cannot back (tampered/missing history — honest, never a guess).
- `rollback_to(cap)` / `mark_active(uid)` — re-activate the predecessor / any unit, demoting the current active
  one (single-active invariant holds).
- `supersede(uid)` — demote a unit by id **without deleting it** (it stays in `history`).
- `list_active()` — every active unit (one per capability) — the per-capability `deploy_topology` snapshot.

## Rollback semantics (REAL, end-to-end)

1. `register(u_v2)` for a fresh capability → `u_v2` active, `rollback_target = ""` (honest: no predecessor).
2. `register(u_v3)` → `u_v2` is **demoted** (lossless — preserved in `history`), and `u_v3.rollback_target = u_v2.unit_id`.
3. `rollback_target("cap")` returns the **exact `u_v2`**. `rollback_to("cap")` re-activates `u_v2`, demotes `u_v3`.

A capability on its first compile honestly reports **no** rollback target (exit 3 on the CLI). A tampered log fails
**loudly** rather than returning a wrong unit. This makes the compiler's long-carried `rollback_target` field
finally *consumable*, and mirrors `purpose_task.py::rollback` / `path_promotion.decide` (*promotion is always
reversible; the prior is kept as the rollback target*).

## Durability + the Fly volume path

Backed by the repo's append-log engine `scripts._jsonl_store.AppendLog`: a **SQLite-WAL primary** (crash-safe, one
ACID txn per append) behind the append-only `*.jsonl` **mirror** that is the contracted on-disk record. On a cold
start the engine **rebuilds its index from the JSONL**, so on a host whose only durable volume is the state dir —
**a Fly Machine volume** — the JSONL on the volume is the source of truth and the registry rehydrates to EQUAL
state for free. The rebuildable SQLite index lives **off** the volume under `.agent/state-index/` (gitignored), so
the state dir holds only the JSONL and a Fly-volume disk-hygiene scan never hits a binary file.

- **JSONL (the truth, on the volume):** `dist/local-services-state/teleon-compiler/compiled-units.jsonl` — the same
  `dist/local-services-state/<service>` mount pattern every Teleon local service uses (`scripts/teleon_local_runtime.py`
  `STATE_DIR = dist/local-services-state/teleon-runtime`). The registry record is the per-capability `deploy_topology`
  analog, so it lives **beside** the runtime state it describes. In `architecture/deploy_topology.json` that path is
  the `teleon-runtime` service's `state_mount: /app/dist/local-services-state` volume.

## CLI

```bash
python -m src.teleon.compiler --register <cap_id>      # compile + register (sets prior active as rollback_target; idempotent)
python -m src.teleon.compiler --register <cap_id> --exec-target fly_machine
python -m src.teleon.compiler --list                   # active units (one/capability) + full lossless history
python -m src.teleon.compiler --rollback <cap_id>      # the rollback-target unit (exit 0); honest exit 3 if none
python -m src.teleon.compiler --state-dir <dir>        # override the state dir (default: the Fly volume mount above)
```

## How it pairs with auto-compile-on-promotion + the Machines runner

```
 promote (teleon_local_runtime gate)  →  compile_capability  →  registry.register(unit)  →  emit(unit, target)  →  deploy
        status: PROMOTED                  (only promoted)         ↑ sets rollback_target      fly/k8s/local           (owner-gated)
                                                                  └ demotes prior (lossless)
```

- **Auto-compile-on-promotion (the documented wire-in — runtime calls `register()`):** when
  `scripts/teleon_local_runtime.py` promotes a capability, it should compile the promoted record and persist it:

  ```python
  # at the promotion site in scripts/teleon_local_runtime.py (the runtime owns that file — this is the seam):
  from src.teleon.compiler import compile_capability, open_registry   # Teleon→Teleon (dependency-law clean)
  unit = compile_capability(promoted_capability, task_spec, exec_target="local_process", now=promoted_at,
                            resolved_preference=resolved_pref, receipt_refs=run_receipt_refs)
  reg = open_registry()                       # default = dist/local-services-state/teleon-compiler/ (the volume)
  try:
      record = reg.register(unit)             # idempotent; stamps the prior active unit as the rollback_target
  finally:
      reg.close()
  ```

  `register_units(units, log_path=None)` is the batch convenience (register many at once). The call is **idempotent**,
  so re-running the promotion (or a daily recompile of unchanged inputs) does not grow the active set or fork the
  rollback chain.
- **The Machines runner (Stage 6, owner-gated):** a deploy step reads `registry.list_active()` for the units to
  launch and `emit(unit, exec_target)` for the concrete config (`fly machine run` / `kubectl apply` / local
  subprocess). On a bad rollout it reads `registry.rollback_target(cap)`, emits that unit, and `rollback_to(cap)`
  records the reversal — the registry is the durable record of *what is deployed and what to revert to*. Real-cloud
  activation stays owner-gated by design (all cloud vendors are `@candidate` cards today).

## Laws upheld

- **Lossless** (`docs/codex/lossless-distillation.md`): superseded units are **demoted, never deleted** — full
  history preserved + queryable; the rollback target is always a real preserved unit, never a reconstruction.
- **Deterministic:** no clock, no random. `registered_at` = the unit's own `compiled_at`; order is
  `(capability_version, compiled_at, unit_id)` — a total order, so a rebuild from the same log is byte-identical
  (proven: the JSONL is byte-identical across two independent runs).
- **Idempotent:** `register` keyed by `unit_id` (a pure hash) — a daily recompile of unchanged inputs is a no-op.
- **Honest:** the registry stores deployable PLANS (`is_truth:false` units); the FleetLedger / capability gate
  remain the source of truth about gate status. A tampered/torn log raises `RegistryIntegrityError` rather than
  silently folding to a wrong unit.
- **Dependency law:** Teleon-layer code — stdlib + `src.teleon` siblings + `scripts` tooling
  (`scripts._jsonl_store`, an offline durability engine, **not** a brand layer). It never imports `src.baltor` /
  `src.openhubforai` (proven by the compiler `--self-test` import scan **and**
  `scripts/check_portfolio_dependency_law.py --self-test`).

## Tests (run `python -m src.teleon.compiler --self-test` — `PASS — 62/62`)

The 22 registry checks (the other 40 are the pre-existing compiler invariants, all still green):

```
[ok] registry: a version bump produces a distinct unit_id (the timeline has >1 unit)
[ok] registry: register a first unit → active, empty rollback_target (no predecessor)
[ok] registry: latest_active_for returns the just-registered unit
[ok] registry: rollback_target is None on the first unit (honest, no fabricated predecessor)
[ok] registry: registering a newer unit sets the PRIOR active unit as its rollback_target (REAL rollback)
[ok] registry: the newer unit is active; the prior unit is DEMOTED (single active per capability)
[ok] registry: latest_for = newest by version (v3) regardless of active state
[ok] registry: rollback_target(cap) returns the EXACT prior unit (the field is now consumable)
[ok] registry: history preserves BOTH units (lossless — superseded is demoted, not deleted)
[ok] registry: history is deterministically ordered (by capability_version, compiled_at, unit_id)
[ok] registry: list_active has exactly one active unit for the capability (v3)
[ok] registry: re-registering the same unit is IDEMPOTENT (no duplicate append)
[ok] registry: rollback_to(cap) re-activates the predecessor (v2) and demotes v3 (REAL rollback)
[ok] registry: mark_active re-promotes a unit and demotes the previously-active one
[ok] registry: supersede demotes a unit by id WITHOUT deleting it (history length unchanged)
[ok] registry: restart rehydrates EQUAL active set (O(attach) from the durable JSONL)
[ok] registry: restart rehydrates EQUAL history (lossless across a restart)
[ok] registry: restart rehydrates the EXACT append-only log (no record loss/dup)
[ok] registry: register refuses a unit with no unit_id (honest, clear error)
[ok] registry: a tampered log (demote of a never-registered unit) is DETECTED, not silently folded
[ok] registry: rollback_target fails honestly when the named predecessor is missing from the log
[ok] registry: the durable JSONL is BYTE-IDENTICAL across two independent runs (deterministic)
```

Plus the standing gates stay green: `python -m src.teleon.compiler --check` (drift gate, 3/3 example units) and
`python3 scripts/check_portfolio_dependency_law.py --self-test`.
