"""src.teleon.egress.traffic_graph — Teleon outbound traffic evidence graph.

Every Teleon worker can touch the outside world: web searches, HTTP fetches,
API calls, MCP/tool invocations, registry lookups. This module records those
egress events as append-only evidence and projects them into a searchable graph:

    Query -> EgressEvent -> Destination
      ^        |              ^
      |        v              |
    Worker   Tool          ResponseDigest

The layer is inspired by graph-augmented agent tools such as pi-gitnexus, but it
records runtime egress rather than code-call context. It is intentionally
truth-free: an egress event says "this worker queried/fetched this thing and got
this receipt-shaped response," never "the returned fact is true." Baltor's
separate governance rail decides what becomes served context.

Pure stdlib + Teleon helpers. Deterministic when timestamps are injected.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.teleon.experiments.ids import canonical_id, sha256_hex
from src.teleon.io.event_io import redact_secrets

_REPO = Path(__file__).resolve().parents[3]

SCHEMA_VERSION = "TeleonEgressObservation"
GRAPH_SCHEMA_VERSION = "TeleonEgressGraph"
LOCAL_EGRESS_GRAPH_PROVIDER_ID = "egress_graph.local_sqlite@v1"
DEFAULT_DB_PATH = str(_REPO / ".agent" / "teleon.egress_graph.local.db")
EGRESS_SERVES_TRUTH = False
HASH_PREFIX = "sha256:"
_REDACTED = "[REDACTED]"

_SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "client_secret",
    "code",
    "key",
    "password",
    "secret",
    "sig",
    "signature",
    "token",
}
_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
_KEY_PREFIXES = ("sk-", "gsk_", "hf_", "AIza", "nvapi-")
_DSN_RE = re.compile(r"(postgres|postgresql|mysql|mongodb|redis|amqp)://[^ \"']+:[^ \"']+@", re.I)


class TeleonEgressGraphRejected(ValueError):
    """Raised when an egress observation would violate the evidence graph contract."""


def _content_hash(value: Any) -> str:
    return f"{HASH_PREFIX}{sha256_hex(value)}"


def _looks_secret(value: str) -> bool:
    if any(re.search(re.escape(prefix) + r"[A-Za-z0-9_\-]{16,}", value) for prefix in _KEY_PREFIXES):
        return True
    return bool(_DSN_RE.search(value))


def _redact_url(url: str) -> str:
    """Redact credentials and sensitive query parameters while preserving the evidence endpoint."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return _REDACTED if _looks_secret(url) else url
    if not parts.scheme or not parts.netloc:
        return _REDACTED if _looks_secret(url) else url

    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        query.append((key, _REDACTED if key.lower() in _SENSITIVE_QUERY_KEYS or _looks_secret(value) else value))
    return urlunsplit((parts.scheme.lower(), host.lower(), parts.path, urlencode(query, doseq=True), ""))


def _redact_string(value: str) -> str:
    if _looks_secret(value):
        return _REDACTED
    return _URL_RE.sub(lambda m: _redact_url(m.group(0)), value)


def _deep_redact(value: Any) -> Any:
    """Redact secrets in nested request/response metadata and URL-looking strings."""
    value = redact_secrets(value)
    if isinstance(value, str):
        return _redact_string(value)
    if isinstance(value, list):
        return [_deep_redact(v) for v in value]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in _SENSITIVE_QUERY_KEYS or str(key).lower() in {"authorization", "cookie", "set-cookie"}:
                out[key] = _REDACTED
            else:
                out[key] = _deep_redact(item)
        return out
    return value


def _destination_parts(destination_url: str) -> dict[str, str]:
    redacted = _redact_url(destination_url)
    parts = urlsplit(redacted)
    host = (parts.hostname or "").lower()
    path = parts.path or "/"
    destination_key = urlunsplit((parts.scheme.lower(), host, path, "", ""))
    return {"destination_url": redacted, "destination_host": host, "destination_key": destination_key}


def _search_blob(observation: dict) -> str:
    pieces = [
        observation.get("tenant_id"),
        observation.get("run_id"),
        observation.get("query_id"),
        observation.get("query_text_redacted"),
        observation.get("worker_id"),
        observation.get("worker_kind"),
        observation.get("tool_name"),
        observation.get("operation"),
        observation.get("destination", {}).get("destination_host"),
        observation.get("destination", {}).get("destination_key"),
        observation.get("status"),
        json.dumps(observation.get("request") or {}, sort_keys=True),
        json.dumps(observation.get("response") or {}, sort_keys=True),
    ]
    return " ".join(str(p).lower() for p in pieces if p not in (None, ""))


def _contains_raw_secret(observation: dict) -> bool:
    return _looks_secret(json.dumps(observation, sort_keys=True))


def make_egress_observation(
    *,
    tenant_id: str,
    run_id: str,
    worker_id: str,
    worker_kind: str,
    query_text: str,
    operation: str,
    destination_url: str,
    started_at: str,
    completed_at: str,
    query_id: str | None = None,
    tool_name: str = "",
    request: dict | None = None,
    response: dict | None = None,
    status: str = "ok",
    trace_id: str = "",
    parent_event_id: str = "",
) -> dict:
    """Mint a governed outbound-traffic observation.

    ``request`` and ``response`` should be summaries, not raw payload dumps. This
    function still redacts common secret shapes and URL credentials before the
    record is returned.
    """
    required = {
        "tenant_id": tenant_id,
        "run_id": run_id,
        "worker_id": worker_id,
        "worker_kind": worker_kind,
        "query_text": query_text,
        "operation": operation,
        "destination_url": destination_url,
        "started_at": started_at,
        "completed_at": completed_at,
    }
    missing = [k for k, v in required.items() if not str(v or "").strip()]
    if missing:
        raise TeleonEgressGraphRejected(f"missing required egress fields: {missing}")

    query_text_redacted = _redact_string(query_text)
    query_id = query_id or canonical_id("egq", tenant_id, run_id, query_text_redacted)
    request_redacted = _deep_redact(request or {})
    response_redacted = _deep_redact(response or {})
    destination = _destination_parts(destination_url)
    request_hash = _content_hash(request_redacted)
    response_hash = _content_hash(response_redacted)
    event_id = canonical_id(
        "ego",
        tenant_id,
        run_id,
        query_id,
        worker_id,
        operation,
        destination["destination_key"],
        started_at,
        request_hash,
        response_hash,
        status,
    )
    observation = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id,
        "tenant_id": tenant_id,
        "run_id": run_id,
        "query_id": query_id,
        "query_text_redacted": query_text_redacted,
        "query_hash": _content_hash(query_text_redacted),
        "worker_id": worker_id,
        "worker_kind": worker_kind,
        "tool_name": tool_name,
        "operation": operation,
        "destination": destination,
        "request": request_redacted,
        "request_hash": request_hash,
        "response": response_redacted,
        "response_hash": response_hash,
        "status": status,
        "started_at": started_at,
        "completed_at": completed_at,
        "trace_id": trace_id,
        "parent_event_id": parent_event_id,
        "serves_truth": EGRESS_SERVES_TRUTH,
    }
    if _contains_raw_secret(observation):
        raise TeleonEgressGraphRejected("egress observation still contains a raw secret after redaction")
    return observation


def _validate_observation(observation: Any) -> list[str]:
    problems: list[str] = []
    if not isinstance(observation, dict):
        return [f"observation must be a dict, got {type(observation).__name__}"]
    for key in (
        "schema_version",
        "event_id",
        "tenant_id",
        "run_id",
        "query_id",
        "query_hash",
        "worker_id",
        "operation",
        "destination",
        "started_at",
        "completed_at",
    ):
        if key not in observation or observation.get(key) in (None, ""):
            problems.append(f"{key} missing")
    if observation.get("schema_version") != SCHEMA_VERSION:
        problems.append("schema_version mismatch")
    if observation.get("serves_truth") is not False:
        problems.append("egress observations must never serve truth")
    dest = observation.get("destination")
    if not isinstance(dest, dict) or not dest.get("destination_host") or not dest.get("destination_key"):
        problems.append("destination must include destination_host and destination_key")
    if _contains_raw_secret(observation):
        problems.append("raw secret detected")
    return problems


def _graph_projection(observation: dict) -> tuple[list[dict], list[dict]]:
    query_node = {
        "node_id": f"query:{observation['query_id']}",
        "node_type": "query",
        "label": observation["query_text_redacted"],
        "body": {
            "query_id": observation["query_id"],
            "query_hash": observation["query_hash"],
            "tenant_id": observation["tenant_id"],
            "run_id": observation["run_id"],
        },
    }
    event_node = {
        "node_id": f"egress:{observation['event_id']}",
        "node_type": "egress_event",
        "label": f"{observation['operation']} {observation['destination']['destination_host']}",
        "body": {
            "event_id": observation["event_id"],
            "status": observation["status"],
            "started_at": observation["started_at"],
            "completed_at": observation["completed_at"],
            "serves_truth": False,
        },
    }
    worker_node = {
        "node_id": f"worker:{observation['worker_id']}",
        "node_type": "worker",
        "label": observation["worker_id"],
        "body": {"worker_id": observation["worker_id"], "worker_kind": observation["worker_kind"]},
    }
    dest = observation["destination"]
    destination_node = {
        "node_id": f"destination:{dest['destination_key']}",
        "node_type": "destination",
        "label": dest["destination_host"],
        "body": dest,
    }
    response_node = {
        "node_id": f"response:{observation['response_hash']}",
        "node_type": "response_digest",
        "label": observation["response_hash"],
        "body": {
            "response_hash": observation["response_hash"],
            "status": observation.get("response", {}).get("status_code"),
            "content_type": observation.get("response", {}).get("content_type"),
            "bytes": observation.get("response", {}).get("bytes"),
        },
    }
    nodes = [query_node, event_node, worker_node, destination_node, response_node]
    if observation.get("tool_name"):
        nodes.append({
            "node_id": f"tool:{observation['tool_name']}",
            "node_type": "tool",
            "label": observation["tool_name"],
            "body": {"tool_name": observation["tool_name"]},
        })

    def edge(edge_type: str, src: str, dst: str) -> dict:
        edge_id = canonical_id("ege", observation["event_id"], edge_type, src, dst)
        return {"edge_id": edge_id, "edge_type": edge_type, "src": src, "dst": dst, "event_id": observation["event_id"]}

    event_id = event_node["node_id"]
    edges = [
        edge("for_query", event_id, query_node["node_id"]),
        edge("performed_by", event_id, worker_node["node_id"]),
        edge("to_destination", event_id, destination_node["node_id"]),
        edge("returned_digest", event_id, response_node["node_id"]),
    ]
    if observation.get("tool_name"):
        edges.append(edge("used_tool", event_id, f"tool:{observation['tool_name']}"))
    if observation.get("parent_event_id"):
        edges.append(edge("caused_by", event_id, f"egress:{observation['parent_event_id']}"))
    return nodes, edges


class LocalEgressGraph:
    """Append-only local SQLite egress graph.

    The schema is intentionally simple: observations are the source of record;
    nodes/edges are deterministic projections for graph lookup. Use an external
    graph database later by replaying the same observation stream.
    """

    provider_id = LOCAL_EGRESS_GRAPH_PROVIDER_ID

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS observations (
                event_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                query_id TEXT NOT NULL,
                query_hash TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                destination_host TEXT NOT NULL,
                destination_key TEXT NOT NULL,
                operation TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                body TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                search_blob TEXT NOT NULL,
                seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                label TEXT NOT NULL,
                body TEXT NOT NULL,
                seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS edges (
                edge_id TEXT PRIMARY KEY,
                edge_type TEXT NOT NULL,
                src TEXT NOT NULL,
                dst TEXT NOT NULL,
                event_id TEXT NOT NULL,
                seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _seq (name TEXT PRIMARY KEY, value INTEGER NOT NULL);
            """
        )
        self._conn.commit()

    def _next_seq(self) -> int:
        cur = self._conn.cursor()
        cur.execute("INSERT INTO _seq(name, value) VALUES('egress', 1) "
                    "ON CONFLICT(name) DO UPDATE SET value = value + 1")
        cur.execute("SELECT value FROM _seq WHERE name='egress'")
        return int(cur.fetchone()[0])

    def describe(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "schema_version": GRAPH_SCHEMA_VERSION,
            "append_only": True,
            "searchable": True,
            "requires_network": False,
            "serves_truth": EGRESS_SERVES_TRUTH,
            "projection": "observations -> nodes/edges",
        }

    def append(self, observation: dict) -> dict:
        problems = _validate_observation(observation)
        if problems:
            raise TeleonEgressGraphRejected("; ".join(problems))
        body = json.dumps(observation, sort_keys=True, separators=(",", ":"))
        content_hash = _content_hash(observation)
        cur = self._conn.cursor()
        existing = cur.execute("SELECT content_hash FROM observations WHERE event_id=?",
                               (observation["event_id"],)).fetchone()
        if existing:
            if existing["content_hash"] != content_hash:
                raise TeleonEgressGraphRejected("append-only violation: event_id already exists with different content")
            return self.get_event(observation["event_id"]) or observation

        seq = self._next_seq()
        dest = observation["destination"]
        cur.execute(
            "INSERT INTO observations(event_id, tenant_id, run_id, query_id, query_hash, worker_id, "
            "destination_host, destination_key, operation, status, started_at, completed_at, body, "
            "content_hash, search_blob, seq) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                observation["event_id"],
                observation["tenant_id"],
                observation["run_id"],
                observation["query_id"],
                observation["query_hash"],
                observation["worker_id"],
                dest["destination_host"],
                dest["destination_key"],
                observation["operation"],
                observation["status"],
                observation["started_at"],
                observation["completed_at"],
                body,
                content_hash,
                _search_blob(observation),
                seq,
            ),
        )
        nodes, edges = _graph_projection(observation)
        for node in nodes:
            cur.execute(
                "INSERT OR IGNORE INTO nodes(node_id, node_type, label, body, seq) VALUES(?,?,?,?,?)",
                (node["node_id"], node["node_type"], node["label"],
                 json.dumps(node["body"], sort_keys=True), self._next_seq()),
            )
        for e in edges:
            cur.execute(
                "INSERT OR IGNORE INTO edges(edge_id, edge_type, src, dst, event_id, seq) VALUES(?,?,?,?,?,?)",
                (e["edge_id"], e["edge_type"], e["src"], e["dst"], e["event_id"], self._next_seq()),
            )
        self._conn.commit()
        return self.get_event(observation["event_id"]) or observation

    def get_event(self, event_id: str) -> dict | None:
        row = self._conn.execute("SELECT body FROM observations WHERE event_id=?", (event_id,)).fetchone()
        return json.loads(row["body"]) if row else None

    def search_events(
        self,
        *,
        tenant_id: str,
        text: str = "",
        query_id: str = "",
        worker_id: str = "",
        destination_host: str = "",
        limit: int = 20,
    ) -> list[dict]:
        """Search redacted egress observations for one tenant."""
        clauses = ["tenant_id=?"]
        params: list[Any] = [tenant_id]
        if text:
            clauses.append("search_blob LIKE ?")
            params.append(f"%{text.lower()}%")
        if query_id:
            clauses.append("query_id=?")
            params.append(query_id)
        if worker_id:
            clauses.append("worker_id=?")
            params.append(worker_id)
        if destination_host:
            clauses.append("destination_host=?")
            params.append(destination_host.lower())
        params.append(max(1, int(limit)))
        rows = self._conn.execute(
            "SELECT body FROM observations WHERE " + " AND ".join(clauses) + " ORDER BY seq, event_id LIMIT ?",
            params,
        ).fetchall()
        return [json.loads(r["body"]) for r in rows]

    def graph_for_query(self, *, tenant_id: str, query_id: str = "", text: str = "") -> dict:
        """Return the nodes/edges induced by a tenant-scoped query search."""
        events = self.search_events(tenant_id=tenant_id, query_id=query_id, text=text, limit=500)
        event_ids = {event["event_id"] for event in events}
        if not event_ids:
            return {"schema_version": GRAPH_SCHEMA_VERSION, "tenant_id": tenant_id,
                    "query_id": query_id, "events": [], "nodes": [], "edges": [], "serves_truth": False}
        placeholders = ",".join("?" for _ in event_ids)
        edge_rows = self._conn.execute(
            f"SELECT edge_id, edge_type, src, dst, event_id FROM edges WHERE event_id IN ({placeholders}) "
            "ORDER BY seq, edge_id",
            tuple(sorted(event_ids)),
        ).fetchall()
        node_ids = {r["src"] for r in edge_rows} | {r["dst"] for r in edge_rows}
        node_placeholders = ",".join("?" for _ in node_ids)
        node_rows = self._conn.execute(
            f"SELECT node_id, node_type, label, body FROM nodes WHERE node_id IN ({node_placeholders}) "
            "ORDER BY seq, node_id",
            tuple(sorted(node_ids)),
        ).fetchall()
        return {
            "schema_version": GRAPH_SCHEMA_VERSION,
            "tenant_id": tenant_id,
            "query_id": query_id,
            "events": events,
            "nodes": [
                {"node_id": r["node_id"], "node_type": r["node_type"], "label": r["label"], "body": json.loads(r["body"])}
                for r in node_rows
            ],
            "edges": [dict(r) for r in edge_rows],
            "serves_truth": False,
        }


__all__ = [
    "DEFAULT_DB_PATH",
    "EGRESS_SERVES_TRUTH",
    "GRAPH_SCHEMA_VERSION",
    "LOCAL_EGRESS_GRAPH_PROVIDER_ID",
    "LocalEgressGraph",
    "SCHEMA_VERSION",
    "TeleonEgressGraphRejected",
    "make_egress_observation",
]
