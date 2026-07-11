# P1 — Async Teleon runs

**File:** `_repos/shared-backend-components/scripts/teleon_local_runtime.py` (the local Teleon capability runtime).
**Status:** done + verified (38/38 self-test checks, 5× clean, real HTTP smoke green).
**Date:** 2026-06-11.

## Problem

`POST /api/teleon/<realm>/runs` executed the **whole example suite synchronously** before
responding — up to 8 model calls × 120 s. Two concrete failures:

1. **Proxy timeout.** Fly's edge proxy cuts a connection that takes that long; the client never
   sees its result and a UI **retry double-bumps the capability version** (each POST was a real
   `execute()` that bumped `version`).
2. **No concurrency.** A single `threading.Lock` wrapped the *entire* `execute()` including the
   long model calls, so every run serialized — two unrelated capability runs blocked each other.

## Design (what changed)

A run is now a small **state machine persisted as an append-only event log**, executed on a
background worker:

```
POST /runs ──(enqueue, fast)──► persist {status:"running"} ──► 202 {run_id, status:"running"}
                                          │
                              background worker thread
                                          │
            run suite (model calls, NO global lock) ──► gate ──► persist terminal status
                                          │
GET /runs?run_id=… ◄── poll ── running | promoted | candidate | rolled-back | failed | interrupted
```

- **`submit_run(...)`** — the fast enqueue path. Under the **global lock** it (a) checks the
  idempotency map, (b) reserves the next per-cap version, (c) persists a **pending** run record
  (`status:"running"`), then returns. It spawns a daemon worker thread (`background=True`) and
  returns the pending record immediately. `execute()` is kept as the **synchronous** equivalent
  (`submit_run(..., background=False)`) for in-process callers/tests.
- **`_worker_body` / `_run_to_completion`** — the worker. Holds the **per-capability lock** for
  the run, executes the suite (the slow model calls happen here, **outside** the global lock), and
  in a short **finalize** window (global lock) appends receipts, commits the reserved version, and
  rewrites the run from `running` → its terminal status. All prior gate / refine / anti-gaming /
  lossless-receipt behaviour is unchanged — it just moved into the worker.
- **`runs.jsonl` is now an event log.** A `run_id` appears once at enqueue and again at finalize;
  on load the file is folded **latest-line-wins** into `run_index` / `runs`. This is lossless: the
  original `running` line is preserved before the terminal line (the lossless-distillation law —
  no destructive overwrite of a prior state).
- **`GET /runs`** gained `?run_id=…` → returns one run's current status (open read, like
  `evidence`: a `run_id` is the opaque handle the 202 just returned). `?session_id=…` still returns
  the account's run list (session-gated, unchanged).
- **`POST /runs`** now returns **202** `{run_id, status, run}` and reads an optional
  `idempotency_key`.

### New named constants (no magic values)

| Constant | Value | Meaning |
|---|---|---|
| `STATUS_RUNNING` | `"running"` | persisted at enqueue, worker not finished |
| `STATUS_INTERRUPTED` | `"interrupted"` | a `running` run a restart abandoned (swept on startup) |
| `STATUS_FAILED` | `"failed"` | the worker raised before the gate (honest, not silent) |
| `TERMINAL_STATUSES` | tuple | `promoted`/`candidate`/`rolled-back`/`failed`/`interrupted` |
| `RUNNING_SWEEP_STALE_S` | `30*60` | a `running` row older than this at process start = abandoned → sweep |

`RUNNING_SWEEP_STALE_S` is generous vs. the worst-case suite wall-clock (≤ 8 model calls × ~120 s
≈ 16 min) so a genuinely in-flight run is never mislabelled; only a fresh process start sweeps.

## Concurrency model (the load-bearing part)

Three layers, each guarding exactly one thing:

1. **Global `self._lock`** — guards only the **short** read-modify-write of shared state: the caps
   map, the runs index, the append-only file writes. It is **never** held across a model call. This
   is what lets two runs of *different* capabilities overlap.
2. **Per-capability lock** (`self._cap_locks[cap_id]`) — a run's worker holds its cap's lock for the
   whole execute+finalize, so two runs of the **same** capability don't interleave their
   execute/finalize. Different caps have different locks → they run in parallel.
3. **Version reservation** (`state["version_reserved"]`, a per-cap monotonic high-water) — reserved
   under the global lock at enqueue, distinct from the **committed** `version` (which advances only
   at finalize). This guarantees two same-cap runs get **distinct, contiguous** versions even when
   submitted concurrently, *without* `submit_run` ever having to block on the per-cap lock — so the
   POST never head-of-line-blocks behind another same-cap run's worker. The reserved version is
   committed (`version = max(version, reserved)`) at finalize.

Why reservation instead of "hold the cap lock in `submit_run`": holding the per-cap lock across the
worker would make a second same-cap POST block for up to ~16 min — defeating async for that case.
Reserving under the global lock keeps version distinctness while every POST stays fast.

**Restart safety.** Worker threads do not survive a process exit, so a run left `running` by a
crash/restart can never finalize itself. `Runtime.__init__` calls `_sweep_interrupted_runs()` on
startup: any `running` row older than `RUNNING_SWEEP_STALE_S` is rewritten to `interrupted`
(a new event line; the original is preserved). Fresh `running` rows from the current process are
left alone. A worker that raises *outside* the per-example try finalizes the run `failed` (carrying
the error) and commits its version so numbering stays contiguous, but does **not** change the
capability's gate verdict — a crash is not a gate decision.

**Idempotency.** `idempotency_key → run_id` is recorded under the global lock at enqueue and rebuilt
from disk on load. A replayed POST with the same key returns the **same** run record and reserves no
new version — so a UI retry can never double-bump.

## Tests — every command + PASS line

### `--self-test` (in-process, full lifecycle; 38 checks)

```
python3 _repos/shared-backend-components/scripts/teleon_local_runtime.py --self-test
```

PASS line:

```
PASS — teleon_local_runtime: REAL capability execution with receipts, a train+holdout promotion
gate (no answer-key leakage), ASYNC restart-safe runs (202 + background worker, per-cap version
serialization, idempotency, interrupted-sweep), locked concurrent state, and persistence.
```

The 13 new async checks (all `[ok]`), on top of the 25 prior gate/anti-gaming/lock checks (all
still `[ok]`):

- async: POST returns immediately with `{run_id, status:running}` (well before a slow suite)
- async: a freshly-enqueued run is observable as `running` before it finishes
- async: status transitions running → terminal (promoted) with real score + receipts
- async: the terminal version was committed to the capability state
- async: two DIFFERENT capabilities execute concurrently (call intervals overlap)
- async idempotency: replayed key returns the SAME run_id (no second run)
- async idempotency: the capability version bumped exactly ONCE (no double-bump)
- async idempotency: exactly one run carries the key
- restart sweep: a stale `running` run becomes `interrupted` (never stuck running)
- restart sweep: a fresh `running` run is NOT swept (belongs to a live worker)
- restart sweep is lossless: original `running` line preserved before `interrupted`
- async crash: a worker error finalizes `failed` (never stuck `running`), with the error
- async crash: a crash does not change the capability's gate verdict, version stays contiguous

### Repeated to catch races (5×)

```
for i in 1 2 3 4 5; do python3 _repos/shared-backend-components/scripts/teleon_local_runtime.py --self-test; done
```

All 5 → `fail_lines=0`, PASS.

### Byte-compile

```
python3 -m py_compile _repos/shared-backend-components/scripts/teleon_local_runtime.py   # PY_COMPILE_OK
```

### Same-cap concurrent-background stress (standalone, 3 trials)

8 threads × 6 concurrent `submit_run(background=True)` on one cap (48 runs):

```
trial: contig=True unique_ids=True committed=True no_running=True disk_ok=True statuses={'promoted'} total=48
```

Proves: versions stay contiguous + unique, committed version == v0+48, no run stuck `running`,
disk distinct-ids == folded view — i.e. the version reservation is race-free under real concurrent
background submits (the server path, which the in-file test exercises only inline).

### Real HTTP smoke (ephemeral port, temp state, live identity session)

Mints a **real** `teleon`-realm session against the live identity service (`:9410`), starts a
*separate* runtime on an ephemeral port (35331) with a temp state dir — **never touching the live
`:9430` service or its state** — and exercises the wire:

```
[ok] healthz ok
[ok] POST returns 202 with run_id+status:running
[ok] POST returned fast (<2s)
[ok] GET ?run_id polls to terminal (promoted)
[ok] evidence returns receipts
[ok] idempotent POST returns the SAME run_id
[ok] idempotent POST bumped cap-cite version exactly once
[ok] no session → 401
[ok] unknown run_id → 404
[ok] session-gated run list returns my runs
HTTP SMOKE: ALL PASS
```

Post-smoke: `:9430` still listening on the original pid; its `runs.jsonl`/`receipts.jsonl`/
`capabilities.json` mtimes unchanged; `git status` shows only `_repos/shared-backend-components/scripts/teleon_local_runtime.py`.

## Race-testing methodology

Concurrency bugs are nondeterministic, so the tests force the windows open rather than hoping:

- **Async-returns-fast** injects a `SlowRoute` whose every `complete()` sleeps `SLOW_S=0.25 s`. A
  synchronous one-attempt suite would take `SUITE_CALLS × SLOW_S`; the assertion requires the POST
  to return in `< SUITE_MIN_SYNC_S / 2`, which is impossible if it blocked on the suite.
- **Cross-cap overlap** records each worker's per-call start/end timestamps and asserts the two
  workers' execution **intervals intersect** (`max(min start) < min(max end)`) — true only if the
  slow calls actually ran in parallel; a single lock would force cap B to begin only after cap A's
  whole suite drained. (Interval-overlap, not "earliest end after latest start," which is wrong for
  multi-call workers.)
- **Same-cap version race** is hit two ways: the in-file test fires 2 threads × 8 inline `execute`
  through a `Barrier` and asserts versions are monotonic/contiguous/unique with no duplicate IDs;
  the standalone stress fires 8 × 6 concurrent **background** submits and re-checks the same
  invariants on disk. The `Barrier` maximizes the collision probability by releasing all threads at
  once.
- **Restart** is simulated by writing a stale `running` row (with `at` set `RUNNING_SWEEP_STALE_S+5`
  in the past) plus a fresh `running` row, then constructing a *new* `Runtime` over the same state
  dir and asserting only the stale one became `interrupted`, losslessly.
- **Worker crash** uses a route whose `health()` raises (an error that escapes the per-example
  `try` in `_suite`), asserting the run finalizes `failed` and the cap's gate verdict is untouched.
- **5× repeat** of the whole suite plus **3× repeat** of the stress trial — real sleeps, so a
  scheduling-dependent bug would surface across runs.

## Is this the best way? / what would make Teleon the real runtime backbone

This is the right shape for a **single-process, stdlib-only, offline** demo runtime: it removes the
proxy-timeout and double-bump failure modes, makes runs genuinely concurrent across capabilities,
and stays honest (every state persisted, receipts lossless, no fake URLs). Its honest limits — and
the path past them — point at the same place:

- **In-process worker threads, not a durable queue.** A run survives a *graceful* restart as
  `interrupted` (swept), but there is no automatic resume — the work is lost, only the status is
  honest. A real backbone needs a **durable work queue** (claim/lease/heartbeat/retry) so a worker
  that dies hands the run to another worker, exactly the FleetLedger atomic-claim model the worker
  fleet already uses. The event-log persistence here is deliberately queue-shaped (latest-line-wins,
  reserved-vs-committed version) so swapping the in-memory `run_index` for that ledger is additive.
- **Per-process locks don't scale past one box.** Per-cap serialization via a `threading.Lock` is
  correct for one process; across replicas the same guarantee needs a **per-capability lease in the
  ledger** (or a per-cap shard key), with the version reservation becoming a ledger sequence. The
  reservation/commit split already models exactly this, so it ports cleanly.
- **The real leverage is the capability → runtime compiler.** The deepest "best way" critique is
  that these four capabilities are *hand-written* pure-Python (`_normalize_dates`, `_redact_pii`,
  …) with hand-written example suites. Teleon becomes the runtime *backbone* — not a fixed demo —
  when a **CapabilityTask spec (CTS)** compiles into exactly this runnable shape: spec → generated
  deterministic implementation **or** governed model route, generated/curated example suite with
  the train/holdout split, the gate, receipts, and promotion, all emitted rather than authored.
  Then "add a capability" is "submit a spec," every capability arrives gate-ready and async by
  construction, and the negative-space corpus (what models can't do alone) feeds the suite. The
  async lifecycle built here is the execution substrate that compiler targets; the next increment
  is the CTS → runtime emitter (and the durable ledger under it), not more hand-written caps.

This change is small + reversible (one owned file, no schema/vocab/brand surface), warranted by the
explicit P1 task and the established repo principles (lossless persistence, no-magic-values,
session gating). Recorded here per the change-verification contract.
