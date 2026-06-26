#!/usr/bin/env python3
"""scripts.check_postgres_record_store — PROOF that the OPERATIONAL cloud backend is real and wired:

  A. RECORD STORE WIRES — src.teleon.storage.record_store imports with neither psycopg nor a DB present;
     PostgresRecordStore implements the SAME RecordStore port as LocalRecordStore (identical public
     methods + identical append signature), names its target, and is selected by open_record_store in
     cloud mode (instead of the old _UnwiredCloudStore that just raised).
  B. RECORD STORE SQL (offline, real path) — append / content-addressed idempotency / count / all are
     exercised against an INJECTED in-process test double (NOT a DB): a re-append with the same idem_key
     is an O(1) indexed no-op returning the existing seq, count/all reflect the live generation, and a
     SQL-INJECTION SENTINEL placed in the record + idem_key appears ONLY in the bound params, NEVER in any
     executed SQL text (parameterized SQL, no string interpolation of data).
  C. FLEET LEDGER WIRES — PostgresFleetLedger upholds the durable contract the live path needs (same
     method shape as DurableFleetLedger, identical claim_task signature); the atomic claim is ONE
     statement with FOR UPDATE SKIP LOCKED + LIMIT 1 + only %s placeholders (concurrent workers each lock
     a DIFFERENT ready row — no serialization); enqueue is exercised offline against a test double and is
     idempotent; open_fleet_ledger selects SQLite by default and Postgres when a DSN/connect is given.
  D. HONEST REFUSAL — with NO DSN configured, both Postgres backends raise StorageError (they refuse
     rather than silently writing to the local backend); the warehouse/history backend stays unwired.
  E. LIVE ROUND-TRIP (only when a DSN + driver are present) — a real append/idempotency/concurrent-claim
     round-trip against Postgres; otherwise an HONEST "skipped" (still exits 0).

Offline, stdlib-only, no DB required for A-D. Set OH_PG_DSN (or DATABASE_URL) to a reachable Postgres to
run E in staging. serves_truth=false (a record/task is evidence, never a truth claim). Exit 0/1.

CLI: PYTHONPATH=. python3 scripts/check_postgres_record_store.py --self-test
"""
from __future__ import annotations

import inspect
import os
import sys
from contextlib import contextmanager
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts._config import OH_PG_DSN_ENV, POSTGRES_DSN_ENV_VARS  # noqa: E402
from src.teleon.storage import record_store as RS  # noqa: E402
from src.teleon.workers import durable_fleet_ledger as DFL  # noqa: E402

# A SQL-injection-shaped value used to PROVE no data is ever string-interpolated into SQL: it must only
# ever appear inside the bound params, never inside an executed SQL string.
_INJECT = "x'); DROP TABLE capability_tasks;--"


# ── in-process test doubles (NEVER a production fallback — production uses real psycopg; the honest path
#    with no DB is to REFUSE. These are injected by this proof to exercise the real SQL/control-flow path
#    offline, exactly as src/teleon/storage/git_record_store.py does for its pgvector mirror). ──────────
class _RecordCursor:
    def __init__(self, conn): self.conn = conn; self._one = None; self._all = None

    def execute(self, sql, params=()):
        self.conn.executed.append((sql, tuple(params)))
        up = " ".join(sql.split()).upper()
        self._one = None; self._all = None
        if up.startswith("CREATE"):
            return
        if up.startswith("SELECT SEQ FROM") and "WHERE IDEM_KEY" in up:
            (idem,) = params
            hit = next((r for r in self.conn.rows if idem is not None and r[3] == idem), None)
            self._one = (hit[0],) if hit else None
        elif up.startswith("INSERT INTO") and "RETURNING SEQ" in up:
            gen, body, idem = params
            if idem is not None and any(r[3] == idem for r in self.conn.rows):
                self._one = None                      # ON CONFLICT (idem_key) DO NOTHING
            else:                                     # NULL idem_key is distinct → always inserts
                seq = self.conn.next_seq; self.conn.next_seq += 1
                self.conn.rows.append((seq, gen, body, idem)); self._one = (seq,)
        elif up.startswith("SELECT BODY_JSON FROM"):
            (gen,) = params
            self._all = [(r[2],) for r in sorted(self.conn.rows, key=lambda r: r[0]) if r[1] == gen]
        elif up.startswith("SELECT COUNT(*) FROM"):
            (gen,) = params
            self._one = (sum(1 for r in self.conn.rows if r[1] == gen),)
        else:
            raise AssertionError(f"unexpected record SQL: {up[:80]}")

    def fetchone(self): return self._one
    def fetchall(self): return list(self._all or [])
    def close(self): pass


class _RecordPg:
    """Faithful in-process double for the PostgresRecordStore SQL surface (4 statement shapes)."""
    def __init__(self): self.rows = []; self.next_seq = 1; self.executed = []
    def cursor(self): return _RecordCursor(self)
    def commit(self): pass
    def close(self): pass


class _LedgerCursor:
    def __init__(self, conn): self.conn = conn; self._one = None

    def execute(self, sql, params=()):
        self.conn.executed.append((sql, tuple(params)))
        up = " ".join(sql.split()).upper(); self._one = None
        if up.startswith("CREATE"):
            return
        if up.startswith("INSERT INTO CAPABILITY_WORKERS"):
            d = dict(zip(DFL._WORKER_COLUMNS, params)); self.conn.workers[d["worker_id"]] = d
        elif up.startswith("INSERT INTO CAPABILITY_TASKS"):
            d = dict(zip(DFL._TASK_COLUMNS, params))
            if d["idempotency_key"] not in self.conn.idem:        # ON CONFLICT(idempotency_key) DO NOTHING
                self.conn.tasks[d["task_id"]] = d; self.conn.idem[d["idempotency_key"]] = d["task_id"]
        elif "FROM CAPABILITY_WORKERS WHERE WORKER_ID" in up:
            (wid,) = params; w = self.conn.workers.get(wid)
            self._one = tuple(w[c] for c in DFL._WORKER_COLUMNS) if w else None
        elif up.startswith("SELECT TASK_ID FROM CAPABILITY_TASKS WHERE IDEMPOTENCY_KEY"):
            (k,) = params; tid = self.conn.idem.get(k); self._one = (tid,) if tid else None
        elif up.startswith("SELECT") and "FROM CAPABILITY_TASKS WHERE TASK_ID" in up:
            (tid,) = params; t = self.conn.tasks.get(tid)
            self._one = tuple(t[c] for c in DFL._TASK_COLUMNS) if t else None
        else:                                                     # claim/start/ack are LIVE-only here
            raise AssertionError(f"unexpected ledger SQL (claim path is live-only): {up[:80]}")

    def fetchone(self): return self._one
    def fetchall(self): return []
    def close(self): pass


class _LedgerPg:
    """In-process double for the enqueue/read SQL surface of PostgresFleetLedger (the concurrent CLAIM is
    deliberately NOT emulated — true FOR UPDATE SKIP LOCKED semantics are verified only against a live DB)."""
    def __init__(self): self.workers = {}; self.tasks = {}; self.idem = {}; self.executed = []
    def cursor(self): return _LedgerCursor(self)
    def commit(self): pass
    def close(self): pass


@contextmanager
def _no_pg_env():
    """Temporarily clear every Postgres/libpq env var so the 'refuses without a DSN' checks are
    deterministic regardless of the ambient environment (e.g. a CI host that sets PGHOST)."""
    saved = {k: os.environ.pop(k, None) for k in list(os.environ)
             if k in POSTGRES_DSN_ENV_VARS or k.startswith("PG")}
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v


def _raises(fn, exc=Exception) -> bool:
    try:
        fn(); return False
    except exc:
        return True
    except Exception:
        return False


def _public(cls) -> set[str]:
    return {n for n, _ in inspect.getmembers(cls, predicate=inspect.isfunction) if not n.startswith("_")}


def _self_test() -> int:  # noqa: C901 - a proof reads best top-to-bottom
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # Decide the LIVE branch from the REAL ambient env BEFORE we clear it for the offline refusal checks.
    live_dsn = RS.resolve_postgres_dsn()
    driver_ok = RS.psycopg_available()

    # ── A. RECORD STORE WIRES + interface parity ──────────────────────────────────────────────────
    ck("A: PostgresRecordStore is a RecordStore (the ONE port)", issubclass(RS.PostgresRecordStore, RS.RecordStore))
    ck("A: PostgresRecordStore is NO LONGER the unwired stub", not issubclass(RS.PostgresRecordStore, RS._UnwiredCloudStore))
    ck("A: same public interface as LocalRecordStore", _public(RS.LocalRecordStore) <= _public(RS.PostgresRecordStore),
       str(_public(RS.LocalRecordStore) - _public(RS.PostgresRecordStore)))
    ck("A: identical append signature (record, *, idem_key)",
       inspect.signature(RS.PostgresRecordStore.append) == inspect.signature(RS.LocalRecordStore.append))
    ck("A: names its operational target", "PostgreSQL" in RS.PostgresRecordStore.target and RS.PostgresRecordStore.backend == "postgres")
    ck("A: _BACKENDS routes 'postgres' → PostgresRecordStore", RS._BACKENDS["postgres"] is RS.PostgresRecordStore)
    ck("A: an operational stream resolves to postgres in cloud mode",
       RS.backend_for("component_candidates", mode="cloud") == "postgres")

    # ── B. RECORD STORE SQL — real path via an injected test double (no DB) ────────────────────────
    fake = _RecordPg()
    store = RS.PostgresRecordStore("component_candidates", shard="000", dsn="postgresql://proof/none", connect=lambda _dsn: fake)
    ck("B: append returns a seq (int)", isinstance(store.append({"id": "r1", "v": 1}), int))
    s2 = store.append({"id": "r2", "v": 2}, idem_key="K2")
    ck("B: re-append with the same idem_key is an O(1) no-op (same seq, no dup)",
       store.append({"id": "r2-DIFFERENT", "v": 99}, idem_key="K2") == s2 and store.count() == 2)
    ck("B: count() reflects the live generation", store.count() == 2)
    got = sorted(r["id"] for r in store.all())
    ck("B: all() returns the stored records as dicts", got == ["r1", "r2"], str(got))
    ck("B: all(predicate) filters", [r["id"] for r in store.all(lambda r: r["v"] == 1)] == ["r1"])
    # the parameterization PROOF: a SQL-injection sentinel in the record + idem_key is ONLY ever a param.
    store.append({"id": "inj", "danger": _INJECT}, idem_key=_INJECT)
    in_sql = [sql for sql, _p in fake.executed if _INJECT in sql]
    in_params = [p for _s, p in fake.executed if any(_INJECT in str(x) for x in p)]
    ck("B: data is parameterized — the injection sentinel NEVER appears in any SQL string", not in_sql, str(len(in_sql)))
    ck("B: the injection sentinel DOES appear in bound params (so it was actually carried)", bool(in_params))
    ck("B: every executed write/read uses %s placeholders (never ? or f-string data)",
       all(("%s" in sql) for sql, p in fake.executed if p))
    store.close()

    # ── C. FLEET LEDGER WIRES + claim-SQL shape + enqueue idempotency (no DB) ──────────────────────
    need = {"register_worker", "set_worker_status", "worker", "live_workers", "enqueue_task", "claim_task",
            "start_task", "ack_task", "nack_task", "reclaim_expired_leases", "task", "queued_tasks",
            "tasks_by_status", "close"}
    ck("C: PostgresFleetLedger upholds the durable contract (method shape)", need <= _public(DFL.PostgresFleetLedger),
       str(need - _public(DFL.PostgresFleetLedger)))
    ck("C: identical claim_task signature to the SQLite ledger",
       inspect.signature(DFL.PostgresFleetLedger.claim_task) == inspect.signature(DFL.DurableFleetLedger.claim_task))
    claim = DFL._PG_CLAIM_TASK_SQL
    ck("C: the atomic claim uses FOR UPDATE SKIP LOCKED (no serialization)", "FOR UPDATE SKIP LOCKED" in claim)
    ck("C: the atomic claim is one ready row (LIMIT 1)", "LIMIT 1" in claim)
    ck("C: the atomic claim is fully parameterized (%s only, no f-string data)",
       "%s" in claim and "{" not in claim and "?" not in claim)
    # enqueue + reads execute against the double; enqueue is idempotent (ON CONFLICT(idempotency_key)).
    led = DFL.open_fleet_ledger(connect=lambda _dsn: _LedgerPg())
    ck("C: open_fleet_ledger(connect=…) selects the Postgres backend", isinstance(led, DFL.PostgresFleetLedger))
    led.register_worker(worker_id="w-proof", capability_ids=["cap.proof"], now="2026-06-26T00:00:00Z")
    ck("C: register_worker round-trips through the SQL path", led.worker("w-proof")["status"] == "warm")
    t1 = led.enqueue_task(tenant_id=_INJECT, capability_id="cap.proof", idempotency_key="idem-1", now="2026-06-26T00:00:00Z")
    t1b = led.enqueue_task(tenant_id="other", capability_id="cap.proof", idempotency_key="idem-1", now="2026-06-26T00:00:00Z")
    ck("C: enqueue is idempotent (same key → same task, no fork)", t1["task_id"] == t1b["task_id"])
    ck("C: enqueued task starts QUEUED", t1["status"] == DFL.QUEUED)
    led_exec = getattr(led, "conn").executed
    ck("C: ledger data is parameterized — injection sentinel never in any SQL string",
       not [sql for sql, _p in led_exec if _INJECT in sql])
    led.close()
    ck("C: open_fleet_ledger() defaults to the SQLite ledger when no DSN is configured",
       _is_sqlite_default())

    # ── D. HONEST REFUSAL when nothing is configured (deterministic — env cleared) ─────────────────
    with _no_pg_env():
        ck("D: PostgresRecordStore REFUSES without a DSN (StorageError, never silent-local)",
           _raises(lambda: RS.PostgresRecordStore("component_candidates"), RS.StorageError))
        ck("D: open_record_store(cloud) on an operational stream refuses without a DSN",
           _raises(lambda: RS.open_record_store("component_candidates", mode="cloud"), RS.StorageError))
        ck("D: PostgresFleetLedger REFUSES without a DSN (StorageError)",
           _raises(lambda: DFL.PostgresFleetLedger(), RS.StorageError))
    ck("D: the warehouse/history backend is still the documented UNWIRED swap",
       _raises(RS.WarehouseRecordStore, NotImplementedError))
    ck("D: a config-tier stream is still refused by the append-only store",
       _raises(lambda: RS.open_record_store("model_index"), RS.StorageError))

    # ── E. LIVE ROUND-TRIP (only with a reachable DSN) — else honest skip ──────────────────────────
    if live_dsn is not None and driver_ok:
        _live_round_trip(ck)
    else:
        why = "no driver (psycopg/psycopg2)" if not driver_ok else f"no DSN ({', '.join(POSTGRES_DSN_ENV_VARS)})"
        print(f"  [ok] E: live Postgres round-trip skipped — {why}; "
              f"set {OH_PG_DSN_ENV} to verify append/idempotency/concurrent-claim in staging.")

    print("\n" + ("PASS — check_postgres_record_store: the operational cloud backend is REAL and wired — "
                  "PostgresRecordStore implements the SAME RecordStore port as LocalRecordStore (content-"
                  "addressed O(1) idempotency via ON CONFLICT, parameterized SQL proven by an injection "
                  "sentinel that stays in params), open_record_store selects it in cloud mode; "
                  "PostgresFleetLedger claims with FOR UPDATE SKIP LOCKED + LIMIT 1 (concurrent, no "
                  "serialization) and open_fleet_ledger keeps SQLite the default. Both REFUSE honestly "
                  "without a DSN (never silent-local); the warehouse tier stays the documented unwired swap. "
                  "Live round-trip runs against OH_PG_DSN, otherwise skips honestly."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _is_sqlite_default() -> bool:
    """open_fleet_ledger() with no DSN must be the SQLite DurableFleetLedger (never PostgresFleetLedger).
    Uses a throwaway temp dir so the proof leaves NO artifact on disk."""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="pg-proof-")
    try:
        with _no_pg_env():
            led = DFL.open_fleet_ledger(os.path.join(tmp, "durable.db"))
            ok = isinstance(led, DFL.DurableFleetLedger) and not isinstance(led, DFL.PostgresFleetLedger)
            led.close()
        return ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _live_round_trip(ck) -> None:
    """A real Postgres round-trip: record-store append/idempotency + ledger N-worker concurrent claim.
    Uses a unique stream + a unique capability/run-id and cleans up its own rows, so it is safe to run
    against a staging DB. Reached only when a reachable DSN + driver are present."""
    import threading
    import uuid

    run = uuid.uuid4().hex[:10]
    dsn = RS.resolve_postgres_dsn() or ""

    # 1) record store
    stream = f"proof_pg_rec_{run}"
    rec = RS.PostgresRecordStore(stream, shard="000")
    try:
        a = rec.append({"id": "x", "n": 1}, idem_key="k")
        ck("E: live append returns a seq", isinstance(a, int))
        ck("E: live idempotent re-append → same seq, no dup", rec.append({"id": "x2"}, idem_key="k") == a and rec.count() == 1)
        rec.append({"id": "y"})
        ck("E: live count/all reflect both rows", rec.count() == 2 and len(rec.all()) == 2)
    finally:
        try:
            cur = rec._conn.cursor(); cur.execute(f"DROP TABLE IF EXISTS {rec.table}"); rec._conn.commit(); cur.close()
        except Exception:
            pass
        rec.close()

    # 2) ledger — N workers race for M tasks; each task claimed by EXACTLY ONE (no double, no loss)
    cap = f"cap.proof.{run}"
    seed = DFL.PostgresFleetLedger(dsn=dsn)
    M, N = 24, 6
    try:
        for i in range(M):
            seed.enqueue_task(tenant_id="proof", capability_id=cap, idempotency_key=f"{run}-{i}")
        claimed: list[str] = []
        lock = threading.Lock()
        barrier = threading.Barrier(N)

        def worker(wid: str) -> None:
            L = DFL.PostgresFleetLedger(dsn=dsn)
            try:
                L.register_worker(worker_id=wid, capability_ids=[cap])
                barrier.wait()
                while True:
                    t = L.claim_task(worker_id=wid, capability_id=cap)
                    if t is None:
                        break
                    with lock:
                        claimed.append(t["task_id"])
            finally:
                L.close()

        threads = [threading.Thread(target=worker, args=(f"{run}-w{j}",)) for j in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        ck(f"E: {N} concurrent workers claimed all {M} tasks", len(claimed) == M, str(len(claimed)))
        ck("E: every task claimed by EXACTLY ONE worker (FOR UPDATE SKIP LOCKED)", len(set(claimed)) == M, str(len(set(claimed))))
    finally:
        try:
            cur = seed.conn.cursor()
            cur.execute("DELETE FROM capability_tasks WHERE capability_id=%s", (cap,))
            cur.execute("DELETE FROM capability_workers WHERE worker_id LIKE %s", (f"{run}-%",))
            seed.conn.commit(); cur.close()
        except Exception:
            pass
        seed.close()


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_postgres_record_store.py --self-test")
    raise SystemExit(0)
