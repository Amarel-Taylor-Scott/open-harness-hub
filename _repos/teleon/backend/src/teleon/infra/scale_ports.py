"""src.teleon.infra.scale_ports — infra SCALE-DECISION ports: each heavy backend behind ONE agnostic seam.

Why (scale review 2026-06-25, _repos/shared-backend-components/context/architecture/scale-architecture-review-2026-06-25.md): the planned
scale (billions->trillions, high write throughput, semantic search at scale) needs a substrate SWAP off
single-node JSONL — durable orchestration, an OLTP/OLAP split, ANN vector search, and a CDC/event-log
spine. We do NOT couple callers to any one product. Each role is an agnostic PORT (mirroring
:mod:`src.teleon.llm_port` and the tier swap in :mod:`src.teleon.storage.record_store`):

    role          real backend   storage tier   purpose
    -----------   ------------   ------------   -------------------------------------------------------
    orchestrator  Temporal       operational    durable workflow orchestration (loops -> queue+workers)
    oltp          PostgreSQL     operational    indexed hot OLTP rows + relationships
    olap          ClickHouse     history        columnar OLAP aggregates over the event log
    vector        Vespa          operational    ANN semantic search at scale (learned embeddings)
    stream        Redpanda       history        the CDC / event-log SPINE (Kafka API) — replayable

Each role has: a Protocol (``available()`` + the core ops); a REAL adapter that is HONEST-UNAVAILABLE —
``available()`` is False and every op REFUSES (raises :class:`InfraUnavailable`, NEVER a fabricated
result) when the client lib OR the connection endpoint env is absent; and a LOCAL in-memory fallback
(always available, deterministic) so the descent still runs offline. :func:`select_infra` picks the real
adapter when it is configured, else the local fallback — and SAYS which (``port.is_fallback``).

The backend is a config choice, not a code rewrite: swapping in real Temporal/Postgres/ClickHouse/Vespa/
Redpanda is setting the lib + endpoint env, never a caller change. serves_truth=false (infrastructure
moves/queries/indexes records; it is never itself a source of truth). Teleon layer — never imports baltor.

  port = select_infra("vector")          # real Vespa if pyvespa+VESPA_ENDPOINT, else local brute-force ANN
  port.upsert("p1", [0.1, 0.2], {"label": "near"})
  hits = port.search([0.1, 0.2], k=3)    # [{"id", "score", "payload"}, ...]
  infra_status()                         # honest per-role: backend, configured?, selected real|fallback, why

  PYTHONPATH=. python3 _repos/teleon/backend/src/teleon/infra/scale_ports.py --self-test
  PYTHONPATH=. python3 _repos/teleon/backend/src/teleon/infra/scale_ports.py --status
"""
from __future__ import annotations

import importlib
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SERVES_TRUTH = False  # infrastructure moves/queries/indexes records; it is never a source of truth.


class InfraUnavailable(RuntimeError):
    """Raised by a REAL adapter when its backend isn't configured (client lib OR endpoint env absent) or
    a live call fails — the HONEST signal so callers fall back to the local in-memory port. NEVER a
    fabricated result."""

    def __init__(self, role: str, reason: str):
        self.role, self.reason = role, reason
        super().__init__(f"infra role {role!r} unavailable: {reason}")


@dataclass(frozen=True)
class _RoleSpec:
    role: str                 # the agnostic role name callers select by
    backend: str              # the real backend product this role maps to
    libs: tuple[str, ...]     # client libs that satisfy the role (first importable wins)
    envs: tuple[str, ...]     # connection endpoint env vars (first set wins)
    tier: str                 # the storage_tier_policy tier this role serves
    purpose: str


#: single source of the role -> (real backend, client libs, endpoint envs, tier) mapping.
_ROLES: dict[str, _RoleSpec] = {
    "orchestrator": _RoleSpec(
        "orchestrator", "Temporal", ("temporalio",), ("TEMPORAL_ADDRESS", "TEMPORAL_HOST"),
        "operational", "durable workflow orchestration (loops -> durable queue + stateless workers)"),
    "oltp": _RoleSpec(
        "oltp", "PostgreSQL", ("psycopg", "psycopg2"), ("POSTGRES_DSN", "DATABASE_URL"),
        "operational", "indexed hot OLTP rows + relationships (the current active product rows)"),
    "olap": _RoleSpec(
        "olap", "ClickHouse", ("clickhouse_connect",), ("CLICKHOUSE_URL", "CLICKHOUSE_DSN"),
        "history", "columnar OLAP aggregates over the append-only event log (analytics at scale)"),
    "vector": _RoleSpec(
        "vector", "Vespa", ("vespa",), ("VESPA_ENDPOINT", "VESPA_URL"),
        "operational", "ANN semantic search at scale (learned embeddings, indexed from CDC)"),
    "stream": _RoleSpec(
        "stream", "Redpanda", ("confluent_kafka", "kafka"), ("REDPANDA_BROKERS", "KAFKA_BOOTSTRAP_SERVERS"),
        "history", "the CDC / event-log SPINE (Kafka API) — immutable, replayable source-of-record"),
}


def _norm(role: str) -> str:
    r = str(role).strip().lower()
    if r not in _ROLES:
        raise ValueError(f"unknown infra role {role!r}; known: {sorted(_ROLES)}")
    return r


# -- the role Protocols (the agnostic seams callers depend on) ------------------------------------
@runtime_checkable
class InfraPort(Protocol):
    role: str
    backend: str
    is_fallback: bool
    def available(self) -> bool: ...


@runtime_checkable
class OrchestratorPort(InfraPort, Protocol):
    """Durable workflow orchestration (Temporal). The local fallback runs ``fn`` in-process synchronously;
    the real adapter starts the registered workflow ``name`` (``fn`` is the local-only implementation)."""
    def start_workflow(self, name: str, fn: Callable[[dict], dict] | None, payload: dict,
                       *, run_id: str | None = None) -> str: ...
    def result(self, run_id: str) -> dict: ...
    def signal(self, run_id: str, name: str, payload: dict) -> None: ...


@runtime_checkable
class OltpPort(InfraPort, Protocol):
    """Transactional key/row store (PostgreSQL)."""
    def put(self, table: str, key: str, row: dict) -> None: ...
    def get(self, table: str, key: str) -> dict | None: ...
    def query(self, table: str, predicate: Callable[[dict], bool] | None = None) -> list[dict]: ...


@runtime_checkable
class OlapPort(InfraPort, Protocol):
    """Columnar analytics store (ClickHouse). ``aggregate`` op in {"count", "sum"}; group_by None -> {"_all": v}."""
    def insert(self, table: str, rows: list[dict]) -> int: ...
    def aggregate(self, table: str, *, group_by: str | None = None,
                  measure: str | None = None, op: str = "count") -> dict: ...


@runtime_checkable
class VectorPort(InfraPort, Protocol):
    """ANN vector store (Vespa). ``search`` returns [{"id", "score", "payload"}, ...] best-first."""
    def upsert(self, id: str, vector: list[float], payload: dict | None = None) -> None: ...
    def search(self, vector: list[float], k: int = 5) -> list[dict]: ...


@runtime_checkable
class StreamPort(InfraPort, Protocol):
    """Append-only event log / CDC spine (Redpanda, Kafka API). ``consume`` advances a per-group offset."""
    def produce(self, topic: str, key: str, value: dict) -> int: ...
    def consume(self, topic: str, group: str, *, max_items: int = 10) -> list[dict]: ...


# -- the REAL adapters (honest-unavailable; never fake) -------------------------------------------
class _Real:
    """Shared probe for a real backend: ``available()`` iff a client lib is importable AND an endpoint
    env is set (deterministic, no network I/O — the cheap honest signal, like ProviderLLM.available()).
    Ops call ``_require()`` first; if unavailable they raise :class:`InfraUnavailable`, never fake."""

    is_fallback = False

    def __init__(self, spec: _RoleSpec):
        self._spec = spec
        self.role = spec.role
        self.backend = spec.backend

    def _lib(self) -> str | None:
        for m in self._spec.libs:
            try:
                importlib.import_module(m)
                return m
            except Exception:  # noqa: BLE001 — a missing/broken client lib is simply "not present"
                continue
        return None

    def _endpoint(self) -> str | None:
        for v in self._spec.envs:
            val = os.environ.get(v)
            if val:
                return val
        return None

    def available(self) -> bool:
        return bool(self._endpoint()) and bool(self._lib())

    def reason(self) -> str:
        if not self._endpoint():
            return f"no endpoint configured (set one of {', '.join(self._spec.envs)})"
        if not self._lib():
            return f"client lib not importable (need one of {', '.join(self._spec.libs)})"
        return "configured"

    def _require(self) -> None:
        if not self.available():
            raise InfraUnavailable(self.role, self.reason())

    def _fail(self, op: str, exc: Exception) -> InfraUnavailable:
        return InfraUnavailable(self.role, f"{self.backend} configured but {op} failed: {exc}")


class TemporalOrchestrator(_Real):
    def start_workflow(self, name, fn, payload, *, run_id=None):  # noqa: ARG002 — fn is local-fallback-only
        self._require()
        try:
            import asyncio
            from temporalio.client import Client  # type: ignore

            async def _run() -> str:
                client = await Client.connect(self._endpoint())
                handle = await client.start_workflow(
                    name, payload, id=run_id or name,
                    task_queue=os.environ.get("TEMPORAL_TASK_QUEUE", "teleon"))
                return handle.id

            return asyncio.run(_run())
        except Exception as e:  # noqa: BLE001
            raise self._fail("start_workflow", e) from e

    def result(self, run_id):
        self._require()
        try:
            import asyncio
            from temporalio.client import Client  # type: ignore

            async def _run():
                client = await Client.connect(self._endpoint())
                return await client.get_workflow_handle(run_id).result()

            out = asyncio.run(_run())
            return out if isinstance(out, dict) else {"result": out}
        except Exception as e:  # noqa: BLE001
            raise self._fail("result", e) from e

    def signal(self, run_id, name, payload):
        self._require()
        try:
            import asyncio
            from temporalio.client import Client  # type: ignore

            async def _run() -> None:
                client = await Client.connect(self._endpoint())
                await client.get_workflow_handle(run_id).signal(name, payload)

            asyncio.run(_run())
        except Exception as e:  # noqa: BLE001
            raise self._fail("signal", e) from e


class PostgresOltp(_Real):
    # auto-created backend-independent KV table so put/get/query work without caller-supplied DDL.
    _DDL = "CREATE TABLE IF NOT EXISTS teleon_kv (tbl text, k text, row jsonb, PRIMARY KEY (tbl, k))"

    def _conn(self):
        return importlib.import_module(self._lib()).connect(self._endpoint())

    def put(self, table, key, row):
        self._require()
        try:
            import json as _json
            conn = self._conn()
            try:
                cur = conn.cursor()
                cur.execute(self._DDL)
                cur.execute(
                    "INSERT INTO teleon_kv (tbl, k, row) VALUES (%s, %s, %s) "
                    "ON CONFLICT (tbl, k) DO UPDATE SET row = EXCLUDED.row",
                    (table, key, _json.dumps(row)))
                conn.commit()
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001
            raise self._fail("put", e) from e

    def get(self, table, key):
        self._require()
        try:
            conn = self._conn()
            try:
                cur = conn.cursor()
                cur.execute(self._DDL)
                cur.execute("SELECT row FROM teleon_kv WHERE tbl = %s AND k = %s", (table, key))
                hit = cur.fetchone()
            finally:
                conn.close()
            return _as_dict(hit[0]) if hit else None
        except Exception as e:  # noqa: BLE001
            raise self._fail("get", e) from e

    def query(self, table, predicate=None):
        self._require()
        try:
            conn = self._conn()
            try:
                cur = conn.cursor()
                cur.execute(self._DDL)
                cur.execute("SELECT row FROM teleon_kv WHERE tbl = %s", (table,))
                rows = [_as_dict(r[0]) for r in cur.fetchall()]
            finally:
                conn.close()
            return [r for r in rows if (predicate is None or predicate(r))]
        except Exception as e:  # noqa: BLE001
            raise self._fail("query", e) from e


class ClickHouseOlap(_Real):
    def _client(self):
        return importlib.import_module("clickhouse_connect").get_client(dsn=self._endpoint())

    def insert(self, table, rows):
        self._require()
        try:
            import json as _json
            client = self._client()
            client.command(
                f"CREATE TABLE IF NOT EXISTS {table} (payload String) ENGINE = MergeTree ORDER BY tuple()")
            client.insert(table, [[_json.dumps(r)] for r in rows], column_names=["payload"])
            return len(rows)
        except Exception as e:  # noqa: BLE001
            raise self._fail("insert", e) from e

    def aggregate(self, table, *, group_by=None, measure=None, op="count"):
        self._require()
        try:
            client = self._client()
            if op == "count":
                expr = "count()"
            elif op == "sum":
                expr = f"sum(JSONExtractFloat(payload, '{measure}'))"
            else:
                raise ValueError(f"unsupported op {op!r}")
            if group_by is None:
                return {"_all": client.query(f"SELECT {expr} FROM {table}").result_rows[0][0]}
            grp = f"JSONExtractString(payload, '{group_by}')"
            rows = client.query(f"SELECT {grp} AS g, {expr} FROM {table} GROUP BY g").result_rows
            return {str(g): v for g, v in rows}
        except Exception as e:  # noqa: BLE001
            raise self._fail("aggregate", e) from e


class VespaVector(_Real):
    def _app(self):
        from vespa.application import Vespa  # type: ignore
        return Vespa(url=self._endpoint())

    def upsert(self, id, vector, payload=None):
        self._require()
        try:
            schema = os.environ.get("VESPA_SCHEMA", "doc")
            fields = dict(payload or {})
            fields["embedding"] = {"values": [float(x) for x in vector]}
            self._app().feed_data_point(schema=schema, data_id=id, fields=fields)
        except Exception as e:  # noqa: BLE001
            raise self._fail("upsert", e) from e

    def search(self, vector, k=5):
        self._require()
        try:
            schema = os.environ.get("VESPA_SCHEMA", "doc")
            body = {
                "yql": f"select * from {schema} where {{targetHits:{int(k)}}}nearestNeighbor(embedding, q)",
                "input.query(q)": [float(x) for x in vector],
                "hits": int(k),
            }
            resp = self._app().query(body=body)
            hits = getattr(resp, "hits", []) or []
            return [{"id": h.get("id"), "score": h.get("relevance"),
                     "payload": h.get("fields", {})} for h in hits][:k]
        except Exception as e:  # noqa: BLE001
            raise self._fail("search", e) from e


class RedpandaStream(_Real):
    def produce(self, topic, key, value):
        self._require()
        try:
            import json as _json
            from confluent_kafka import Producer  # type: ignore
            p = Producer({"bootstrap.servers": self._endpoint()})
            p.produce(topic, key=str(key), value=_json.dumps(value))
            p.flush(10)
            return 0  # the broker assigns the real offset; the caller reads it from the consumer
        except Exception as e:  # noqa: BLE001
            raise self._fail("produce", e) from e

    def consume(self, topic, group, *, max_items=10):
        self._require()
        try:
            import json as _json
            from confluent_kafka import Consumer  # type: ignore
            c = Consumer({"bootstrap.servers": self._endpoint(), "group.id": group,
                          "auto.offset.reset": "earliest", "enable.auto.commit": True})
            c.subscribe([topic])
            out: list[dict] = []
            try:
                for _ in range(max_items):
                    msg = c.poll(1.0)
                    if msg is None or msg.error():
                        break
                    out.append({"key": (msg.key() or b"").decode() or None,
                                "value": _as_dict(_json.loads(msg.value())), "offset": msg.offset()})
            finally:
                c.close()
            return out
        except Exception as e:  # noqa: BLE001
            raise self._fail("consume", e) from e


# -- the LOCAL in-memory fallbacks (always available, deterministic — the descent still runs) ------
class LocalOrchestrator:
    role, backend, is_fallback = "orchestrator", "in_memory_orchestrator", True

    def __init__(self):
        self._results: dict[str, dict] = {}
        self._signals: dict[str, list] = {}
        self._seq = 0

    def available(self) -> bool:
        return True

    def start_workflow(self, name, fn, payload, *, run_id=None):
        self._seq += 1
        rid = run_id or f"{name}-{self._seq:06d}"
        try:
            out = fn(dict(payload)) if callable(fn) else dict(payload)
        except Exception as e:  # noqa: BLE001 — a failed workflow is recorded, not crashed
            out = {"error": str(e)}
        self._results[rid] = out if isinstance(out, dict) else {"result": out}
        return rid

    def result(self, run_id):
        if run_id not in self._results:
            raise KeyError(f"unknown run_id {run_id!r}")
        return dict(self._results[run_id])

    def signal(self, run_id, name, payload):
        self._signals.setdefault(run_id, []).append({"name": name, "payload": dict(payload)})


class LocalOltp:
    role, backend, is_fallback = "oltp", "in_memory_oltp", True

    def __init__(self):
        self._t: dict[str, dict[str, dict]] = {}

    def available(self) -> bool:
        return True

    def put(self, table, key, row):
        self._t.setdefault(table, {})[key] = dict(row)

    def get(self, table, key):
        hit = self._t.get(table, {}).get(key)
        return dict(hit) if hit is not None else None

    def query(self, table, predicate=None):
        return [dict(r) for r in self._t.get(table, {}).values() if (predicate is None or predicate(r))]


class LocalOlap:
    role, backend, is_fallback = "olap", "in_memory_olap", True

    def __init__(self):
        self._t: dict[str, list[dict]] = {}

    def available(self) -> bool:
        return True

    def insert(self, table, rows):
        self._t.setdefault(table, []).extend(dict(r) for r in rows)
        return len(rows)

    def aggregate(self, table, *, group_by=None, measure=None, op="count"):
        rows = self._t.get(table, [])

        def _val(group: list[dict]):
            if op == "count":
                return len(group)
            if op == "sum":
                return float(sum(float(r.get(measure, 0) or 0) for r in group))
            raise ValueError(f"unsupported op {op!r}")

        if group_by is None:
            return {"_all": _val(rows)}
        buckets: dict[str, list[dict]] = {}
        for r in rows:
            buckets.setdefault(str(r.get(group_by)), []).append(r)
        return {k: _val(v) for k, v in buckets.items()}


class LocalVector:
    role, backend, is_fallback = "vector", "in_memory_vector", True

    def __init__(self):
        self._items: dict[str, tuple[list[float], dict]] = {}

    def available(self) -> bool:
        return True

    def upsert(self, id, vector, payload=None):
        self._items[id] = ([float(x) for x in vector], dict(payload or {}))

    def search(self, vector, k=5):
        q = [float(x) for x in vector]
        scored = [{"id": i, "score": _cosine(q, vec), "payload": dict(pl)}
                  for i, (vec, pl) in self._items.items()]
        scored.sort(key=lambda d: (-d["score"], d["id"]))  # deterministic: score desc, then id
        return scored[:max(0, int(k))]


class LocalStream:
    role, backend, is_fallback = "stream", "in_memory_stream", True

    def __init__(self):
        self._topics: dict[str, list[dict]] = {}
        self._offsets: dict[tuple[str, str], int] = {}

    def available(self) -> bool:
        return True

    def produce(self, topic, key, value):
        log = self._topics.setdefault(topic, [])
        offset = len(log)
        log.append({"key": key, "value": dict(value), "offset": offset})
        return offset

    def consume(self, topic, group, *, max_items=10):
        log = self._topics.get(topic, [])
        start = self._offsets.get((topic, group), 0)
        batch = log[start:start + max(0, int(max_items))]
        self._offsets[(topic, group)] = start + len(batch)
        return [dict(m) for m in batch]


# -- the selector / registry ----------------------------------------------------------------------
_REAL_ADAPTERS: dict[str, Callable[[_RoleSpec], InfraPort]] = {
    "orchestrator": TemporalOrchestrator,
    "oltp": PostgresOltp,
    "olap": ClickHouseOlap,
    "vector": VespaVector,
    "stream": RedpandaStream,
}
_LOCAL_FALLBACKS: dict[str, Callable[[], InfraPort]] = {
    "orchestrator": LocalOrchestrator,
    "oltp": LocalOltp,
    "olap": LocalOlap,
    "vector": LocalVector,
    "stream": LocalStream,
}


def real_adapter(role: str) -> InfraPort:
    """The REAL backend adapter for a role (honest-unavailable when its lib/endpoint is absent)."""
    spec = _ROLES[_norm(role)]
    return _REAL_ADAPTERS[spec.role](spec)


def local_fallback(role: str) -> InfraPort:
    """The LOCAL in-memory fallback for a role (always available, deterministic)."""
    return _LOCAL_FALLBACKS[_norm(role)]()


def select_infra(role: str, *, prefer: str = "auto") -> InfraPort:
    """Pick the port for a role. ``prefer='auto'`` (default) returns the real adapter when it is
    configured, else the local fallback; ``'local'`` forces the fallback; ``'real'`` forces the real
    adapter (even if unavailable, so callers can introspect). The choice is honest — read
    ``port.is_fallback`` to know whether the real backend was used."""
    r = _norm(role)
    if prefer == "local":
        return local_fallback(r)
    real = real_adapter(r)
    if prefer == "real":
        return real
    return real if real.available() else local_fallback(r)


def infra_status() -> dict:
    """Honest per-role status: backend, tier, purpose, whether the real backend is configured, which
    port :func:`select_infra` would pick, and why. serves_truth=false."""
    roles: dict[str, dict] = {}
    for r, spec in _ROLES.items():
        real = real_adapter(r)
        configured = real.available()
        chosen = select_infra(r)
        roles[r] = {
            "backend": spec.backend,
            "tier": spec.tier,
            "purpose": spec.purpose,
            "real_configured": configured,
            "is_fallback": chosen.is_fallback,
            "selected": (f"real:{spec.backend}" if not chosen.is_fallback
                         else f"local-fallback:{chosen.backend}"),
            "note": "real backend configured" if configured else real.reason(),
            "libs": list(spec.libs),
            "envs": list(spec.envs),
        }
    return {"serves_truth": SERVES_TRUTH, "roles": roles}


def available_infra() -> dict:
    """Compact registry view: each role -> {backend, tier, configured}. serves_truth=false."""
    return {"serves_truth": SERVES_TRUTH, "roles": {
        r: {"backend": s.backend, "tier": s.tier, "configured": real_adapter(r).available()}
        for r, s in _ROLES.items()}}


# -- helpers --------------------------------------------------------------------------------------
def _cosine(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(x * x for x in a[:n]))
    nb = math.sqrt(sum(x * x for x in b[:n]))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _as_dict(value: Any) -> dict:
    """Coerce a stored payload (already-dict from jsonb, or a JSON string) to a dict — never fabricates."""
    if isinstance(value, dict):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        import json as _json
        loaded = _json.loads(value)
        if isinstance(loaded, dict):
            return loaded
    raise TypeError(f"expected a dict payload, got {type(value).__name__}")


# -- self-test (deterministic + OFFLINE: all real backends forced unavailable) --------------------
def _assert_refuses(label: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except InfraUnavailable:
        return
    raise AssertionError(f"{label}: real adapter must raise InfraUnavailable (honest-unavailable), not return a result")


def self_test() -> int:
    # OFFLINE determinism: clear every endpoint env so all real backends are unavailable regardless of
    # what's installed locally (no client lib import, no network I/O on the tested path). Restored after.
    saved: dict[str, str | None] = {}
    for spec in _ROLES.values():
        for v in spec.envs:
            saved[v] = os.environ.pop(v, None)
    try:
        # 1) every real adapter is HONEST-UNAVAILABLE with no endpoint, and the selector falls back + SAYS so.
        for r in _ROLES:
            real = real_adapter(r)
            assert real.available() is False, f"{r}: real adapter must be unavailable with no endpoint"
            assert real.is_fallback is False, f"{r}: real adapter is not a fallback"
            assert "no endpoint configured" in real.reason(), f"{r}: reason must name the missing endpoint"
            chosen = select_infra(r)
            assert chosen.is_fallback is True, f"{r}: selector must fall back to local when real is unavailable"
        # 2) each real op REFUSES (raises InfraUnavailable) rather than fabricating a result.
        _assert_refuses("orchestrator", lambda: real_adapter("orchestrator").result("rid"))
        _assert_refuses("oltp", lambda: real_adapter("oltp").get("t", "k"))
        _assert_refuses("olap", lambda: real_adapter("olap").aggregate("t"))
        _assert_refuses("vector", lambda: real_adapter("vector").search([0.1, 0.2], k=1))
        _assert_refuses("stream", lambda: real_adapter("stream").consume("t", "g"))

        # 3) the LOCAL fallbacks run (the descent still works offline) — deterministic.
        orch = local_fallback("orchestrator")
        rid = orch.start_workflow("enrich", lambda p: {"out": p["x"] * 2}, {"x": 21})
        assert orch.result(rid) == {"out": 42}, "orchestrator fallback must run the workflow in-process"
        orch.signal(rid, "cancel", {"why": "test"})  # accepted, recorded
        try:
            orch.result("nope")
            raise AssertionError("orchestrator fallback must raise on an unknown run_id, not fabricate")
        except KeyError:
            pass

        db = local_fallback("oltp")
        db.put("providers", "npi-1", {"name": "Acme", "active": True})
        db.put("providers", "npi-1", {"name": "Acme", "active": False})  # upsert by key
        assert db.get("providers", "npi-1")["active"] is False, "oltp fallback must upsert by key"
        assert db.get("providers", "missing") is None, "oltp fallback miss must be None (honest), not fabricated"
        assert len(db.query("providers", lambda row: not row["active"])) == 1, "oltp fallback must filter"

        olap = local_fallback("olap")
        olap.insert("events", [{"kind": "a", "n": 2}, {"kind": "a", "n": 3}, {"kind": "b", "n": 5}])
        assert olap.aggregate("events") == {"_all": 3}, "olap fallback count(all)"
        assert olap.aggregate("events", group_by="kind") == {"a": 2, "b": 1}, "olap fallback count group-by"
        assert olap.aggregate("events", group_by="kind", measure="n", op="sum") == {"a": 5.0, "b": 5.0}, \
            "olap fallback sum group-by"

        vec = local_fallback("vector")
        vec.upsert("near", [1.0, 0.0], {"label": "near"})
        vec.upsert("far", [0.0, 1.0], {"label": "far"})
        hits = vec.search([0.9, 0.1], k=2)
        assert [h["id"] for h in hits] == ["near", "far"], "vector fallback must rank by cosine, best first"
        assert hits[0]["score"] >= hits[1]["score"] and hits[0]["payload"]["label"] == "near"

        st = local_fallback("stream")
        assert (st.produce("cdc", "k1", {"op": "insert"}), st.produce("cdc", "k2", {"op": "update"})) == (0, 1), \
            "stream fallback must assign monotonic offsets"
        first = st.consume("cdc", "indexer", max_items=1)
        assert first == [{"key": "k1", "value": {"op": "insert"}, "offset": 0}], "stream fallback consume batch"
        assert [m["key"] for m in st.consume("cdc", "indexer", max_items=10)] == ["k2"], "per-group offset advances"
        assert st.consume("cdc", "indexer") == [], "stream fallback caught up -> empty (honest)"
        # a second consumer group sees the whole log from the start (independent offset)
        assert [m["key"] for m in st.consume("cdc", "auditor", max_items=10)] == ["k1", "k2"]

        # 4) status / registry are honest + serves_truth=false.
        status = infra_status()
        assert status["serves_truth"] is False, "infra serves_truth must be False"
        assert set(status["roles"]) == set(_ROLES), "status must cover every role"
        assert all((not v["real_configured"]) and v["is_fallback"] for v in status["roles"].values()), \
            "offline: every role must report unavailable + fallback-selected"
        compact = available_infra()
        assert compact["serves_truth"] is False and set(compact["roles"]) == set(_ROLES)

        # 5) unknown role is rejected (no silent default).
        try:
            select_infra("nosuch")
            raise AssertionError("an unknown role must raise, not default silently")
        except ValueError:
            pass
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    print(f"scale_ports self-test: OK ({len(_ROLES)} infra roles · all real backends honest-unavailable "
          f"offline · local fallbacks run · serves_truth={SERVES_TRUTH})")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--status" in argv:
        import json as _json
        print(_json.dumps(infra_status(), indent=2))
        return 0
    print("usage: scale_ports --self-test | --status")
    return 0


__all__ = [
    "InfraUnavailable", "InfraPort",
    "OrchestratorPort", "OltpPort", "OlapPort", "VectorPort", "StreamPort",
    "TemporalOrchestrator", "PostgresOltp", "ClickHouseOlap", "VespaVector", "RedpandaStream",
    "LocalOrchestrator", "LocalOltp", "LocalOlap", "LocalVector", "LocalStream",
    "real_adapter", "local_fallback", "select_infra", "infra_status", "available_infra",
    "self_test", "main", "SERVES_TRUTH",
]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
