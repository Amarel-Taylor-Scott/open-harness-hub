# P1 — SQLite (WAL) state engines for the three shared local services

Status: **DONE + verified** (2026-06-11). Owner of this work: the agent that owns
`scripts/identity_local_service.py`, `scripts/registry_local_service.py`,
`scripts/events_local_service.py`, and the new `scripts/_jsonl_store.py`. Nothing else was touched.

## Goal (as scoped)

Convert the three shared services from JSON-file / JSONL in-process state to **SQLite (WAL mode)** so
they are multi-machine-safer and have no O(n)-per-request reparse, **without breaking any public
behavior, self-test, or the on-disk durability contract** (the P1 "SQLite state engines" item). Laws
honored: no-magic-values, LOSSLESS (append-only logs stay append-only; existing JSONL files are
MIGRATED, never dropped), honest behavior, surgical diffs.

## The binding constraint that shaped the design (read this first)

The naive reading — "replace the `*.jsonl` files with a SQLite DB inside each state dir" — is
**impossible** without breaking checks this work does not own. Two hard walls, both proven empirically
before any code was written:

1. **The `*.jsonl` files are an externally-contracted on-disk artifact.** Non-owned proofs read them
   back **by exact name as UTF-8 text / JSON-lines**:
   - `check_identity_local_service_runtime.py:177` parses `audit-events.jsonl` as JSON lines;
   - `check_local_events_plane.py:73` reads `events.jsonl` text and asserts a rejected payload is absent;
   - `check_registry_backend.py:129,160,171` reads `review_queue.jsonl` / `review_decisions.jsonl` /
     `reviewers.jsonl` by name and asserts content.
   So the JSONL cannot be removed or turned into a frozen `.migrated` backup — it must keep being
   written live.

2. **A binary SQLite file inside a service state dir crashes the disk-hygiene scanners.** THREE
   non-owned proofs do `state_dir.glob('**/*')` + `read_text(encoding="utf-8")` over **every** file
   under the state dir (`check_identity_local_service_runtime.py:170`,
   `check_adversarial_auth_all_realms.py:117`, `check_service_handshake_slice.py:125`). A SQLite WAL
   database's `-wal` and `-shm` sidecars are **not valid UTF-8** — verified: `read_text('utf-8')` raises
   `UnicodeDecodeError` on them. Those scans run **while the service is up** (inside the `try`, before
   the `finally: server.shutdown()`), so the sidecars exist and the scan would crash. Therefore no
   SQLite file (and no `-wal`/`-shm`) may live under `dist/identity`, `dist/registry`, or
   `dist/analytics`.

These two walls + "don't change the Fly deploy topology / volume mounts" are jointly over-constrained
for a *primary-on-volume* SQLite store. The design below is the one that satisfies **all** of them.

## The design: SQLite WAL is the engine; JSONL stays the durable contract; the DB lives off the scanned tree

New module `scripts/_jsonl_store.py` (471 lines) provides **`AppendLog`** — a SQLite-WAL-backed
append-only log that keeps the `*.jsonl` as an append-only **mirror**:

- The **SQLite table is the crash-safe primary** record. Each `append()` is one ACID transaction
  (`PRAGMA journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=5000` — the house profile from
  `scripts/durable_store.py`). A committed row survives a process kill mid-write; a torn line can never
  wedge it.
- The **`*.jsonl` text file stays an append-only mirror**, written from the committed row inside the
  same lock — so the durability contract and every external reader keep working byte-for-byte.
- The **SQLite DB lives OUTSIDE the service state dir**, under `.agent/state-index/<stem>.<hash>.db`
  (off every disk-hygiene scan; `.agent/` is gitignored). The DB filename is a blake2b hash of the
  **absolute** jsonl path, so distinct state dirs (incl. per-proof temp dirs) get distinct DBs.
- The DB is a **rebuildable index**: on a cold start with no DB it re-imports from the `*.jsonl`. So
  even on a Fly machine whose only volume is the state dir (and where `.agent/` is ephemeral), the
  **JSONL on the volume remains the source of truth** and the index is rebuilt for free on boot. The
  deploy topology needs **zero** changes — confirmed against `architecture/deploy_topology.json`
  mounts (`/app/dist/identity`, `/app/dist/registry`, `/app/dist/analytics`), all unchanged.

This is exactly the LOSSLESS posture (`docs/codex/lossless-distillation.md`): the SQLite layer is a
**derived index that never replaces the raw JSONL**; migration imports every line and **preserves the
original** plus a `.migrated` snapshot (rollback target); rotation renames a full generation to `.1`
(one kept) while the DB retains every rotated row, queryable via `iter_generation`.

### `AppendLog` API (the shape that swaps to Postgres later)

`append(record)->seq` · `iter(predicate=None)` / `all(predicate=None)` · `count()` (live generation) ·
`rotate()->generation` (jsonl→`.1` + DB generation bump) · `iter_generation(n)` · `close()`. Module
constants are all named with rationale (no magic values): `STATE_INDEX_DIR`, `_DB_PATH_HASH_CHARS`,
the three `_PRAGMA_*`, `ROTATED_SUFFIX`, `MIGRATED_SUFFIX`, `GENERATION_START`.

## What changed, per file (line ranges)

### `scripts/_jsonl_store.py` — NEW (471 lines)
The whole module. Key parts: `AppendLog.__init__` opens the WAL DB + reconciles with the JSONL;
`_reconcile_with_jsonl` (the migration + torn-repair logic, made hot-path-cheap — see perf below);
`append` / `iter` / `count` / `rotate` / `iter_generation`; a thorough `--self-test`.

### `scripts/events_local_service.py` (net ~0 lines; 51 changed)
- `:40` import `AppendLog`.
- `:75` `EventsPlane.__init__` opens `self._log = AppendLog(self.path)` (the `events.jsonl` mirror).
- `:90` counters rebuild from `self._log.iter()` instead of re-reading the file line by line.
- `:120` `_rotate` calls `self._log.rotate()` (was `os.replace`).
- `:159` `ingest` appends via `self._log.append(evt)` (was a raw file-open write).
- Docstring persistence note updated. `self.path` / `self.rotated_path` retained (the proofs read them).

### `scripts/registry_local_service.py` (net −2 lines; 76 changed)
- `:64` import `AppendLog`.
- `:203` `RegistryStore.__init__` builds `self._logs: dict[Path, AppendLog]` (one per JSONL) — replaces
  the old `self._cache: dict[Path, list[dict]]` append-through cache.
- `:250` `_rows(path)` returns `self._logs[path].all()` (DB-served — still no per-request file re-parse).
- `:255` `_append(path, rec)` calls `self._logs[path].append(rec)`.
- `:264` `_rotate_calls_locked` calls `self._logs[self.calls_path].rotate()`.
- `:270` `log_call` checks `self._logs[self.calls_path].count()` for the rotation bound.
- Removed the now-unused `_load_jsonl` static method (the append-log parses internally).
- Docstring persistence note updated.

### `scripts/identity_local_service.py` (net +12 lines; 21 changed)
- `:47` import `AppendLog`.
- `:235` `IdentityService.__init__` opens `self.audit_log = AppendLog(self.audit_path)`.
- `:315` `audit(...)` appends via `self.audit_log.append(event)` (was a raw file-open write).
- Docstring updated. **Deliberately unchanged:** the per-realm `realm-<id>.json` snapshots and
  `service-connections.json` are whole-document atomic-replace JSON, **not** append-logs — the
  append-log abstraction (append/iter/count/rotate) does not fit them, and they must stay readable
  text for the hygiene scanners. They keep their existing `os.replace` atomic-write path.

## The migration mechanism (LOSSLESS)

On first `AppendLog` open for a given jsonl, `_reconcile_with_jsonl` compares a cheap DB `COUNT(*)`
against a cheap non-blank-line count of the mirror:

- **DB empty, JSONL has lines** → legacy import: every parseable line is inserted into the DB in file
  order, the **legacy `*.jsonl` is left in place**, and it is additionally snapshotted to
  `<name>.migrated` (byte-identical, a rollback target; never overwritten once written).
- **DB ahead of a torn/short mirror** (crash mid-append left a torn tail) → the DB is authoritative;
  the pre-repair mirror is snapshotted to `.migrated`, then rewritten atomically from the DB rows so
  external readers see every committed row. (The old plain text-append silently *dropped* a torn final
  line — losing the last record. This now recovers it.)
- **In agreement** → no-op (the common steady-state restart).

Unparseable lines are skipped exactly as the services' old loaders skipped them (a torn tail never
wedges startup). Rotation is lossless: `*.jsonl`→`*.jsonl.1` (one kept), DB keeps the rotated rows.

## Every verification command + its PASS line

Each was run **3×** (flakiness check, esp. the concurrency test). All green every run.

| Command | Result (last line) |
|---|---|
| `python3 -m py_compile` on all 4 touched files | COMPILE OK (all 4) |
| `python3 scripts/_jsonl_store.py --self-test` | `PASS — _jsonl_store --self-test: … migrates losslessly … N-thread WAL appends with no loss/dup … restart reopens with EQUAL state (O(attach), not a re-parse) … rotation … torn mirror is repaired …` (3/3) |
| `python3 scripts/identity_local_service.py --self-test` | `PASS — identity_local_service --self-test: sliding-window login throttle … live over HTTP.` (3/3) |
| `python3 scripts/registry_local_service.py --self-test` | `PASS — registry store self-test: … reads from memory, restart rehydrates equal state … rotation keeps one preserved previous generation.` (3/3) |
| `python3 scripts/events_local_service.py --self-test` | `PASS — events_local_service --self-test: generation cap rotates … live-only counters … Retry-After that recovers … truth_authority:false intact.` (3/3) |
| `python3 scripts/provision_access.py --self-test` | `PASS — 8/8 provisioning self-test checks` (3/3) |
| `python3 scripts/check_identity_local_service_runtime.py --self-test` | `PASS — check_identity_local_service_runtime: … restart-safe persistence, no cleartext secret or raw key on disk, audited …` (3/3) |
| `python3 scripts/check_registry_backend.py --self-test` | `PASS — check_registry_backend: … per-account workspace replayed from an append-only log … PROMOTION GATE … revoke rolls back losslessly …` (3/3) |
| `python3 scripts/check_local_events_plane.py --self-test` | `PASS — check_local_events_plane: … PII-guarded … restart-safe, non-truth by declaration.` (3/3) |
| `python3 scripts/check_service_handshake_slice.py --self-test` | `PASS — check_service_handshake_slice: … no raw token on disk.` (3/3) |

Additional bespoke proofs (each PASS):

- **REAL 1000-line legacy migration** (prompt-mandated), per service: pre-seed a 1000-line legacy
  JSONL in a temp state dir → start the service → all 1000 imported, the original is preserved, the
  `.migrated` backup is **byte-identical**, reads are correct, fresh writes continue, and **no binary
  DB lands in the state dir**. → `REAL MIGRATION TEST PASS`.
- **Hard SIGKILL durability**: a child process appends 500 rows then is `SIGKILL`ed (no clean
  shutdown, no checkpoint); a fresh reopen recovers all 500 via WAL, ordered, mirror repaired. →
  `HARD-KILL DURABILITY PASS`.
- **Live 3-service E2E**: identity + registry + events running together over HTTP; cross-service
  session auth (registry validates a realm session against identity) works; the audit mirror records
  privileged calls; a restart rehydrates session state. → `E2E 3-SERVICE LIVE SMOKE PASS`.
- **No-binary-in-state-dir proof**: after a real identity run that fires an audit event, the state dir
  contains only `audit-events.jsonl` + `realm-baltor.json`, and **every** file `read_text('utf-8')`
  succeeds (the hygiene-scan invariant).

## Perf — before / after (measured on this box; best-of-5)

The relevant win is **startup rehydration** (the per-start O(n) full re-parse the services did) and
the removal of corruption-on-crash. Steady-state reopen now does an indexed `COUNT(*)` + a no-parse
newline scan instead of `json.loads` on every line:

| rows | OLD whole-file JSONL re-parse | NEW reopen (SQLite attach) | speedup |
|---:|---:|---:|---:|
| 1,000 | 2.0 ms | 0.5 ms | 3.7× |
| 10,000 | 21.9 ms | 2.9 ms | 7.5× |
| 50,000 | 137.0 ms | 18.7 ms | 7.3× |

Append throughput is ~30 µs/record (one WAL-committed INSERT + one mirror line) — well within the
services' request budget. 8-thread concurrent appends show **no loss and no duplicates** under WAL.

> **Honest caveat recorded during the work:** the FIRST cut of `_reconcile_with_jsonl` parsed BOTH the
> DB rows and the JSONL lines at every start to detect a torn mirror — that made the restart ~2×
> *slower* than the old re-parse (a regression on the exact metric this item targets). It was fixed to
> compare a cheap DB `COUNT(*)` vs a no-parse non-blank line count, parsing only in the rare
> legacy-import / torn-repair branches. The table above is the fixed path. (Caught by benchmarking, not
> by a green check — a reminder that "it's green" is necessary, not sufficient.)

## Anything deferred / not done

- **Per-request read cost was already O(1)** before this work (registry had an append-through cache;
  events/identity-audit never re-parsed per request). So the headline win here is **startup +
  crash-safety + a Postgres-ready abstraction**, not a per-request-reparse fix on the hot path. The
  item's framing ("no O(n)-per-request reparse") is satisfied (reads are DB-served), but the honest
  marginal gain is at startup.
- **`.agent/state-index/` litter from temp-dir tests.** Because DB paths are keyed by absolute jsonl
  path, each test temp dir leaves a small (~24 KB) gitignored DB behind. Real services use stable names
  and reuse one DB; this is pure test litter. Pruned at the end of this run. A periodic sweep that
  drops DBs whose source jsonl no longer exists would tidy this; not worth the complexity now.
- **The whole-document identity stores** (`realm-*.json`, `service-connections.json`) were
  intentionally NOT moved (not append-logs; the abstraction doesn't fit; they must stay UTF-8 text).

## "Is this the best way?" — critique (incl. should this be Postgres-from-the-start?)

**Within the stated constraints, yes — but the constraints, not the engineering, are the ceiling.**

- **Should the SQLite DB be the primary on the volume instead of an off-volume rebuildable index?**
  That is the *stronger* design (no rebuild-on-cold-start, true single source of truth in SQLite). It
  is **blocked today** by two non-owned proofs that `read_text('utf-8')` every file under the state dir
  and would crash on a `-wal`/`-shm` sidecar. Making SQLite primary-on-volume requires an **owner
  decision** on one of: (a) teach those two hygiene scanners to skip binary files (a 1-line guard each,
  but they're outside this work's scope), or (b) give the DB its own sub-volume / mount. Per the
  change-verification contract, an agent does not unilaterally edit other agents' proofs or change the
  deploy topology to force this — so the index-alongside-JSONL design is the warranted choice. **This
  is the real P1 follow-up**: get owner sign-off to relax the hygiene scan, then make SQLite primary.

- **Should this be Postgres from the start?** No, not for these services. They are explicitly the
  **local-dev / single-machine** plane (the deploy law forbids `fly scale count > 1` on them; WAL is
  single-writer-node). Postgres is already staged in the topology as **phase-2** for the *staged-row
  load target* (`scripts.db.*`), not for the auth/registry/events control plane. Standing up Postgres
  for these would add an external dependency, break offline/stdlib-only operation, and contradict the
  topology's own `phase` note. The `AppendLog` API (`append`/`iter`/`count`/`rotate` over a SQL table)
  **is** the seam where a Postgres backend drops in later, when/if these services ever need multi-node
  — which is the prompt's "prepares the Postgres swap" goal, achieved without the premature dependency.

- **Is the dual-write (DB + JSONL mirror) a liability?** It is the deliberate price of keeping the
  externally-contracted JSONL alive. The DB is written first (the ACID commit) and the mirror second,
  under one lock; a crash between them leaves the DB right and the mirror is repaired from it on the
  next start — never the reverse, so there is **no mirror line without a committed DB row**. The
  failure mode is one-directional and self-healing, which is the correct invariant.

- **Net:** the change removes the corruption-on-crash risk, makes restart 3–7× cheaper, keeps every
  byte of the durability contract, needs zero deploy changes, and lands the Postgres-ready abstraction
  — the maximum available without an owner call to relax a sibling proof.
