"""Append-only local egress ledger.

The graph is a projection. This ledger is the local source of record for egress
intents, route decisions, attempts, and payload references.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.teleon.egress.traffic_graph import DEFAULT_DB_PATH, EGRESS_SERVES_TRUTH
from src.teleon.experiments.ids import sha256_hex

LEDGER_SCHEMA_VERSION = "TeleonEgressLedger"
DEFAULT_LEDGER_DB_PATH = DEFAULT_DB_PATH.replace("egress_graph", "egress_ledger")


class EgressLedgerRejected(ValueError):
    """Raised when an append would violate the egress ledger contract."""


def _content_hash(record: dict[str, Any]) -> str:
    return "sha256:" + sha256_hex(record)


class LocalEgressLedger:
    """SQLite append-only egress ledger.

    Tables are deliberately separate so production can replay each record family
    into a durable store or analytics system without deriving truth from graph
    nodes.
    """

    provider_id = "egress_ledger.local_sqlite@v1"

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or DEFAULT_LEDGER_DB_PATH
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS intents (
                intent_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                route_policy_id TEXT NOT NULL,
                body TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS decisions (
                decision_id TEXT PRIMARY KEY,
                intent_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                route_policy_id TEXT NOT NULL,
                action TEXT NOT NULL,
                body TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attempts (
                attempt_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                intent_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                status TEXT NOT NULL,
                response_hash TEXT NOT NULL,
                body TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS payload_refs (
                payload_ref_id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                retention_policy TEXT NOT NULL,
                body TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _seq (name TEXT PRIMARY KEY, value INTEGER NOT NULL);
            """
        )
        self._conn.commit()

    def _next_seq(self) -> int:
        cur = self._conn.cursor()
        cur.execute("INSERT INTO _seq(name, value) VALUES('egress_ledger', 1) "
                    "ON CONFLICT(name) DO UPDATE SET value = value + 1")
        cur.execute("SELECT value FROM _seq WHERE name='egress_ledger'")
        return int(cur.fetchone()[0])

    def describe(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "schema_version": LEDGER_SCHEMA_VERSION,
            "append_only": True,
            "record_families": ["intents", "decisions", "attempts", "payload_refs"],
            "serves_truth": EGRESS_SERVES_TRUTH,
        }

    def _append(self, table: str, key_field: str, record: dict[str, Any], columns: dict[str, Any]) -> dict[str, Any]:
        if record.get("serves_truth") is not False:
            raise EgressLedgerRejected("egress ledger records must never serve truth")
        key = str(record.get(key_field) or "")
        if not key:
            raise EgressLedgerRejected(f"{key_field} missing")
        body = json.dumps(record, sort_keys=True, separators=(",", ":"))
        content_hash = _content_hash(record)
        cur = self._conn.cursor()
        existing = cur.execute(f"SELECT content_hash, body FROM {table} WHERE {key_field}=?", (key,)).fetchone()
        if existing:
            if existing["content_hash"] != content_hash:
                raise EgressLedgerRejected(f"append-only violation: {table}.{key_field} already exists")
            return json.loads(existing["body"])
        column_names = [key_field, *columns, "body", "content_hash", "seq"]
        values = [key, *columns.values(), body, content_hash, self._next_seq()]
        placeholders = ",".join("?" for _ in column_names)
        cur.execute(
            f"INSERT INTO {table}({','.join(column_names)}) VALUES({placeholders})",
            values,
        )
        self._conn.commit()
        return record

    def append_intent(self, intent: dict[str, Any]) -> dict[str, Any]:
        return self._append("intents", "intent_id", intent, {
            "tenant_id": intent["tenant_id"],
            "run_id": intent["run_id"],
            "worker_id": intent["worker_id"],
            "route_policy_id": intent["route_policy_id"],
        })

    def append_decision(self, decision: dict[str, Any]) -> dict[str, Any]:
        return self._append("decisions", "decision_id", decision, {
            "intent_id": decision["intent_id"],
            "tenant_id": decision["tenant_id"],
            "route_policy_id": decision["route_policy_id"],
            "action": decision["action"],
        })

    def append_attempt(self, attempt: dict[str, Any]) -> dict[str, Any]:
        return self._append("attempts", "attempt_id", attempt, {
            "decision_id": attempt["decision_id"],
            "intent_id": attempt["intent_id"],
            "tenant_id": attempt["tenant_id"],
            "status": attempt["status"],
            "response_hash": attempt["response_hash"],
        })

    def append_payload_ref(self, payload_ref: dict[str, Any]) -> dict[str, Any]:
        return self._append("payload_refs", "payload_ref_id", payload_ref, {
            "attempt_id": payload_ref["attempt_id"],
            "tenant_id": payload_ref["tenant_id"],
            "payload_hash": payload_ref["payload_hash"],
            "retention_policy": payload_ref["retention_policy"],
        })

    def records(self, table: str, *, tenant_id: str = "") -> list[dict[str, Any]]:
        if table not in {"intents", "decisions", "attempts", "payload_refs"}:
            raise EgressLedgerRejected(f"unknown ledger table {table!r}")
        if tenant_id:
            rows = self._conn.execute(f"SELECT body FROM {table} WHERE tenant_id=? ORDER BY seq", (tenant_id,)).fetchall()
        else:
            rows = self._conn.execute(f"SELECT body FROM {table} ORDER BY seq").fetchall()
        return [json.loads(row["body"]) for row in rows]


__all__ = [
    "DEFAULT_LEDGER_DB_PATH",
    "EgressLedgerRejected",
    "LEDGER_SCHEMA_VERSION",
    "LocalEgressLedger",
]
