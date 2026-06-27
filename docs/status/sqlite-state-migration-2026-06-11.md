# SQLite state migration — identity / registry / events — 2026-06-11

Status: **DONE + verified green** (all named gates; three pre-existing, out-of-scope check
failures documented below with evidence they predate this work).

Scope executed: the P1 consolidation item "SQLite WAL for identity/registry/events" from
`docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md`. Files owned and changed:
`scripts/identity_local_service.py`, `scripts/registry_local_service.py`,
`scripts/events_local_service.py`, plus the shared engine `scripts/_jsonl_store.py` (new) and
this report. Companion design/perf write-up: `docs/status/p1-sqlite-state-migration.md`
(same work wave; it carries the before/after perf table and the deeper design critique — this
report is the dated record with the schema, the migration proof, and the exact PASS lines).

## What changed

### New shared engine — `scripts/_jsonl_store.py` (`AppendLog`)

One SQLite-WAL-backed append-only log per durable JSONL:

- **SQLite is the crash-safe primary record.** Every `append()` is one ACID `INSERT`
  (`journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=5000ms`,
  `check_same_thread=False` + an `RLock` for the services' ThreadingHTTPServer threads).
- **The `*.jsonl` stays alive as an append-only mirror**, written from the committed row under
  the same lock — the externally contracted on-disk record keeps its exact bytes
  (`json.dumps(rec, sort_keys=True)` per line).
- **Append-only semantics via an INSERT-only table** — no `UPDATE`/`DELETE` on records, ever.
  (The only non-INSERT statement is the upsert of the single `generation` counter in `meta`.)
- **Rotation became retention queries that PRESERVE prior generations**: `rotate()` renames the
  mirror to `<name>.1` (the pre-existing one-kept-file contract, unchanged) and bumps the db
  generation; `count()`/`iter()` answer from the live generation only, while every rotated row
  STAYS in the db, queryable via `iter_generation(n)`. Net: the db now preserves generations the
  old file scheme aged out — a strict losslessness improvement.
- **Torn-tail repair**: if a crash mid-append leaves the mirror short of the db, the next open
  snapshots the torn mirror once, then rewrites it from the committed rows. (The old plain-append
  scheme silently *lost* a torn final line.)

### `scripts/events_local_service.py`

- `EventsPlane` persists through `AppendLog(events.jsonl)`: counters rebuild from the live
  generation (`self._log.iter()`), `ingest` appends through the log, `_rotate` delegates to
  `AppendLog.rotate()`. Wire behavior, caps, 429/Retry-After, and the `events.jsonl` /
  `events.jsonl.1` layout are byte-compatible.
- `ROTATED_SUFFIX` is now imported from `scripts._jsonl_store` (was a second hand-typed `".1"` —
  no-magic-values fix; one definition).

### `scripts/registry_local_service.py`

- `RegistryStore` replaced its in-memory append-through cache with six `AppendLog`s (one per
  JSONL: workspace, api_calls, review_queue, review_decisions, reviewers, admins). Reads
  (`_rows`) are db-served (never a per-request whole-file re-parse); writes commit to SQLite
  then mirror the JSONL line, both under the existing `self.lock`. `api_calls` rotation keeps
  the exact `.1` file contract while the db retains all generations.
- Side effect worth knowing: the operator roster CLI (`--grant-reviewer` etc.) now takes effect
  in a RUNNING daemon again (both processes share the WAL db; the old cache went stale on
  external writes).
- `".1"` literals in the self-test now use the imported `ROTATED_SUFFIX`.

### `scripts/identity_local_service.py`

- The audit stream (`audit-events.jsonl`) is an `AppendLog` — crash-safe, queryable, mirrored.
- **Deliberately NOT moved**: the per-realm `realm-<id>.json` snapshots and
  `service-connections.json`. They are whole-document atomic-replace (`os.replace`) JSON stores,
  not append-only logs, and they MUST remain UTF-8 text inside the state dir (see constraints).
  Their write path is unchanged.

### Self-test extensions (this report's wave; all in-file, all green)

Each service `--self-test` now ALSO proves, alongside every pre-existing check:

1. **Migration from legacy state** — a hand-written pre-SQLite state dir (the old writers' exact
   line format) migrates in on startup: replayed summaries/rosters/promotions are exact, the
   original files are preserved untouched in place AND byte-identical `.migrated` snapshots
   exist, and migration is one-time (a restart re-attaches, never re-imports).
2. **Restart rehydration equality** — a second service instance on the same state dir produces
   equal state (events: identical `summary()`; registry: identical workspace/submissions/roster/
   audit projections; identity: identical audit history + accounts, a pre-restart session still
   validates and an unrevoked API key still verifies).
3. **Concurrent writes** — 8 threads × 25 writes through the real service seams
   (`ingest`, `record`+`log_call`, `handle("register")`): zero errors, zero lost or duplicated
   rows in both the db and the JSONL mirrors, and restart equality afterwards.

The self-tests close their SQLite handles and delete their own proof dbs (no `.agent/state-index`
litter from these runs).

## Schema (one db per log, WAL)

```sql
CREATE TABLE IF NOT EXISTS records(
    seq        INTEGER PRIMARY KEY AUTOINCREMENT,  -- stable oldest→newest order across restarts
    generation INTEGER NOT NULL,                   -- live era; rotate() bumps it (rows never deleted)
    body_json  TEXT NOT NULL                       -- the exact record (sort_keys canonical JSON)
);
CREATE INDEX IF NOT EXISTS idx_records_gen ON records(generation, seq);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);  -- 'generation' counter
-- PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=5000;
```

Db location: `.agent/state-index/<stem>.<blake2b16-of-abs-jsonl-path>.db` — deterministic, one db
per log, collision-safe across state dirs, gitignored (`.agent/`).

## Why the implementation adapts the literal spec (warrant: proven constraints)

The directive said "one db per state_dir" inside the state dir and "preserve files untouched as
`.legacy`". Both were adapted, with evidence, because four NON-owned proofs and the deploy
topology make the literal form impossible without breaking gates this work must keep green:

1. **No binary file may live under a service state dir.** `check_identity_local_service_runtime.py:170`,
   `check_adversarial_auth_all_realms.py`, and `check_service_handshake_slice.py` run
   `state_dir.glob("**/*")` + `read_text(encoding="utf-8")` over EVERY file (recursive; pathlib
   glob matches dotfiles — verified empirically on this box, Python 3.14). A SQLite db/-wal/-shm
   is not valid UTF-8 (verified: `UnicodeDecodeError`). A db inside the state dir crashes them.
2. **The JSONL files must keep being written live, by name.** `check_identity...:177` parses
   `audit-events.jsonl`; `check_local_events_plane.py:73` reads `events.jsonl`;
   `check_registry_backend.py:129,160,171` reads `review_queue.jsonl`/`review_decisions.jsonl`/
   `reviewers.jsonl`; `check_identity...:174` requires `credref:` to appear in the state-dir text
   (the realm snapshots). So the text surface cannot be frozen into renamed `.legacy` files.
3. **Deploy volumes mount EXACTLY at the state dirs** (`architecture/deploy_topology.json`:
   `/app/dist/identity`, `/app/dist/registry`, `/app/dist/analytics`;
   `deploy/docker-compose.deploy.yml` likewise). Anything outside the state dir is ephemeral in
   cloud — so the on-volume JSONL must remain the durable source, and the off-volume db must be
   rebuildable from it (it is: cold start with no db re-imports from the mirror).

Mapping spec → implementation: "one db per state_dir" → one db per durable log, deterministically
derived, off the scanned tree (finer granularity, same guarantee); "preserve untouched as
`.legacy`" → the original is preserved untouched IN PLACE and additionally snapshotted
byte-identically to `<name>.migrated` (a strictly stronger preservation: the rollback copy exists
AND the contracted live file keeps serving). Lossless law: nothing deleted, lineage kept, rollback
target present, rehydration proven.

## Migration mechanics + proof

On first open per log: db empty + mirror has lines → every parseable line is INSERTed in file
order, the mirror is left in place, and `<name>.migrated` (byte-identical) is written once.
Steady-state restarts compare a cheap `COUNT(*)` to a no-parse line count (no re-parse). Proof
(from the in-file self-tests, all green):

- events: `E: a legacy events.jsonl (no db yet) migrates into the SQLite log on startup` ·
  `E: the legacy file is preserved untouched (in place + byte-identical snapshot)` ·
  `E: migration is one-time — a restart re-attaches, never re-imports`
- registry: `migration: workspace replay over the migrated rows is exact` ·
  `migration: roster + decisions replay (reviewer present, candidate promoted with lineage)` ·
  `migration: every legacy file preserved untouched (in place + byte-identical snapshot)` ·
  `migration: one-time — a restart re-attaches (no re-import) and stays EQUAL`
- identity: `G: a legacy audit-events.jsonl (no db yet) migrates into the SQLite log on startup` ·
  `G: the legacy audit file is preserved untouched (in place + byte-identical snapshot)` ·
  `G: a restart rehydrates EQUAL state (audit history, accounts, session, API key)`
- module: 1000-line legacy import with order+content equality (`_jsonl_store --self-test`).

**Operational note for the LIVE `dist/` state (do this at the next controlled restart).** The
real services are currently running pre-migration code against `dist/identity`, `dist/registry`,
`dist/analytics` (live pid files; the audit log was appending during this work). The real
migration fires automatically on the first new-code start. Sequence: stop the old processes (by
exact recorded pid, per the loop law), then start new-code services. Do NOT run pre-migration
writers against an already-migrated state dir afterwards: an old-code process appends to the
mirror without the db, and the next reconcile treats the db as authoritative and would rewrite
those externally appended mirror lines away (the single-writer law already forbids this
topology; recorded here so the upgrade window honors it).

## Exact PASS lines (this box, 2026-06-11; concurrency-bearing tests run 3×, stable)

Owned self-tests (extended):

```
PASS — identity_local_service --self-test: sliding-window login throttle per (realm, identifier) + (realm, source), lockout rejects even correct secrets with the same generic 401, audited as login/lockout, reset on success, heals after 900s, live over HTTP — and the SQLite-WAL audit engine migrates a legacy audit-events.jsonl losslessly (preserved + snapshot), loses nothing under concurrent registrations, and rehydrates equal state across a restart.
PASS — registry store self-test: SQLite-WAL append-logs serve reads (never a per-request file re-parse) with the *.jsonl mirrors intact, a legacy pre-SQLite state dir migrates in losslessly (files preserved + byte-identical snapshots, one-time), restarts rehydrate equal state, concurrent writes lose nothing, and api_calls rotation keeps one preserved previous generation (db keeps them all).
PASS — events_local_service --self-test: generation cap rotates (previous generation preserved, exactly one kept, ingest never bricked), live-only counters, transient 600/min-style cap with Retry-After that recovers, honest oversized-batch 400, truth_authority:false intact, legacy events.jsonl migrated losslessly (preserved + snapshot), restart rehydrates equal state from the SQLite-WAL log, concurrent ingest loses nothing.
PASS — _jsonl_store --self-test: SQLite-WAL append-log behind the JSONL contract — legacy jsonl migrates losslessly (every line imported, original preserved + .migrated snapshot), reads served from the db, N-thread WAL appends with no loss/dup, restart reopens with EQUAL state (O(attach), not a re-parse), rotation renames a full generation to .1 while the db keeps the rotated rows (queryable), and a torn mirror is repaired from the crash-safe db.
```

Required external gates (exit 0):

```
PASS — check_identity_local_service_runtime: registry-driven separate realms (parent+Baltor+Teleon+live hubs, products.js drift-gated), the standard flow + realm isolation over HTTP, session-gated hash-only API keys (raw shown once), restart-safe persistence, no cleartext secret or raw key on disk, audited with request-id correlation.
PASS — check_registry_backend: the Open*Hub registry plane is real — catalog seeded from the bundle (single source), per-account workspace replayed from an append-only log, session-gated against the identity service (fails closed), publish → review queue (candidate ≠ active). [...full line in the gate output...]
PASS — check_local_events_plane: registry-ported native events/A-B plane — ingest (single/batch), per-variant summary with conversion_rate, PII-guarded (rejected events never stored), restart-safe, non-truth by declaration.
PASS — 8/8 provisioning self-test checks            (scripts/provision_access.py --self-test)
PASS — check_service_handshake_slice: the /service/* contract is LIVE — env-keyed service-account handshake (no fake when unset), 8-scope vocabulary enforced, directional verify, both-realm connection lists (projection only), revoke with receipts, asymmetric grants, user-realm isolation intact, no raw token on disk.
```

## Pre-existing failures (NOT caused by this work — evidence)

Three checks in the `check_*events*`/importer family fail identically on the committed baseline;
every input they assert on is clean vs HEAD (`git status --porcelain web/
architecture/identity_realm_registry.json <check>.py` → empty), and the failing assertions never
touch the migrated state engine:

1. `check_events_beacon_wiring.py` — `2 FAILURES: ['A: index.html loads events.js', 'A: events.js
   loads after data.js']`. `web/openhubforai/index.html` was rebuilt by the full-design transplant
   (commit `5b17af2d`); the page the check describes lives on as `legacy.html`. HEAD's
   `index.html` contains zero `events.js` references (`git show HEAD:web/openhubforai/index.html |
   grep -c events.js` → 0). Sections C/D of the same check — the ones that exercise the events
   SERVICE live over HTTP — PASS.
2. `check_harness_hub_auth_wiring.py` — `2 FAILURES: ['A: index.html loads identity.js',
   'A: identity.js loads before app.js']`. Same transplant staleness (the new page loads
   `kit/oh-identity.js`).
3. `check_adversarial_auth_all_realms.py` — `1 FAILURES: ['all 12 front-end realms present']`.
   The check hand-types `len(realms) == 12`; the unmodified realm registry now declares 25 realms
   (itself a no-magic-values violation in that check). Every other assertion in it — including its
   own UTF-8 hygiene scan over the identity state dir, which would have caught a binary db — PASSES.

Fixing these requires edits to `web/openhubforai/index.html` or to the check scripts — both outside
this work's ownership, and the index.html fix is a product/design decision (wiring the old beacon
client into the transplanted React surface) that the change-verification contract reserves for
clear owner intent. Flagged for their owners.

## Law compliance summary

- **Lossless**: originals preserved in place + `.migrated` byte-identical snapshots + db keeps all
  rotated generations + torn tails now recovered instead of dropped + rehydration proven.
- **No magic values**: pragmas/suffixes/generation-start defined once in `scripts/_jsonl_store.py`
  and imported by all three services (two pre-existing hand-typed `".1"` duplicates removed).
- **Honest**: stale "append-through cache / reads from memory" wording in the registry was updated
  in the same wave; the dual-format reality (db primary, JSONL contracted mirror) and the adapted
  spec parameters are documented with their warrants, not papered over.
- **Locks kept**: each service's `threading.Lock` usage is unchanged; `AppendLog` adds its own
  `RLock` + WAL `busy_timeout` underneath.
- **Behavior/API byte-compatible**: every wire-level gate passes unchanged; mirror files keep the
  exact legacy line format and rotation layout.
