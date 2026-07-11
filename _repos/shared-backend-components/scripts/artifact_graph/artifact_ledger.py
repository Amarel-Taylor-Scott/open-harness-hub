#!/usr/bin/env python3
"""scripts.artifact_graph.artifact_ledger — ONE durable ledger for all decomposed CFPB artifacts.

The page is NOT the source of truth — this ledger is. Five SQLite tables (stdlib sqlite3, WAL, thread-safe
— same pattern as DurableStore, compatible with the same .db file): ``artifacts`` (one row for every
decomposed object: source_record … atomic_fact … conclusion … context_pack … receipt — versioned,
content-hashed, lineaged, with source handles + governance), ``artifact_edges`` (deterministic | llm |
human | imported), ``artifact_vectors`` (provider/model/version/dimensions), ``conflicts``, and
``reconciliations``. Determinism: ``created_at`` is INJECTED (never a clock read) so artifacts/edges are
byte-stable across runs.

CLI: imported by the C32 builder, demo orchestrator, proofs, and the read-only API projection.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

EPOCH = "1970-01-01T00:00:00Z"  # deterministic default stamp (no wall-clock in the compared bytes)


def chash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:24]


@dataclass
class Artifact:
    artifact_id: str
    tenant_id: str
    source_id: str
    source_version: str
    artifact_type: str
    schema_version: str
    text: str
    payload_json: dict
    content_hash: str
    parent_artifact_id: str | None
    source_handles_json: list
    pipeline_id: str
    pipeline_version: str
    processor_id: str
    processor_version: str
    run_id: str
    claim_status: str
    promotion_eligible: bool = False
    model_dependent: bool = False
    created_at: str = EPOCH
    superseded_by: str | None = None


@dataclass
class Edge:
    edge_id: str
    tenant_id: str
    from_artifact_id: str
    to_artifact_id: str
    edge_type: str
    edge_source: str  # deterministic | llm | human | imported
    confidence: float
    evidence_json: dict
    pipeline_id: str
    processor_id: str
    run_id: str
    created_at: str = EPOCH


@dataclass
class Vector:
    vector_id: str
    tenant_id: str
    artifact_id: str
    vector_provider: str
    vector_model: str
    vector_version: str
    dimensions: int
    vector_json: list
    content_hash: str
    created_at: str = EPOCH


@dataclass
class Conflict:
    conflict_id: str
    tenant_id: str
    artifact_a_id: str
    artifact_b_id: str
    conflict_type: str
    detector: str
    severity: str
    evidence_json: dict
    status: str  # open | reconciled | false_positive | needs_human
    reconciliation_id: str | None = None
    created_at: str = EPOCH


@dataclass
class Reconciliation:
    reconciliation_id: str
    tenant_id: str
    conflict_ids_json: list
    decision: str
    winning_artifact_id: str | None
    rationale: str
    resolver_type: str  # deterministic | llm_suggested | human_signed
    receipt_json: dict
    created_at: str = EPOCH


class ArtifactGraphLedger:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._init()

    def _init(self) -> None:
        with self._lock:
            c = self.conn
            c.execute("""CREATE TABLE IF NOT EXISTS artifacts(
                artifact_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, source_id TEXT NOT NULL,
                source_version TEXT NOT NULL, artifact_type TEXT NOT NULL, schema_version TEXT NOT NULL,
                text TEXT, payload_json TEXT NOT NULL, content_hash TEXT NOT NULL, parent_artifact_id TEXT,
                source_handles_json TEXT NOT NULL, pipeline_id TEXT NOT NULL, pipeline_version TEXT NOT NULL,
                processor_id TEXT NOT NULL, processor_version TEXT NOT NULL, run_id TEXT NOT NULL,
                claim_status TEXT NOT NULL, promotion_eligible INTEGER NOT NULL DEFAULT 0,
                model_dependent INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, superseded_by TEXT)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_art_t ON artifacts(tenant_id, artifact_type)")
            c.execute("""CREATE TABLE IF NOT EXISTS artifact_edges(
                edge_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, from_artifact_id TEXT NOT NULL,
                to_artifact_id TEXT NOT NULL, edge_type TEXT NOT NULL, edge_source TEXT NOT NULL,
                confidence REAL, evidence_json TEXT NOT NULL, pipeline_id TEXT NOT NULL,
                processor_id TEXT NOT NULL, run_id TEXT NOT NULL, created_at TEXT NOT NULL)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_edge_t ON artifact_edges(tenant_id, edge_type)")
            c.execute("""CREATE TABLE IF NOT EXISTS artifact_vectors(
                vector_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, artifact_id TEXT NOT NULL,
                vector_provider TEXT NOT NULL, vector_model TEXT NOT NULL, vector_version TEXT NOT NULL,
                dimensions INTEGER NOT NULL, vector_json TEXT NOT NULL, content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_vec_t ON artifact_vectors(tenant_id, artifact_id)")
            c.execute("""CREATE TABLE IF NOT EXISTS conflicts(
                conflict_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, artifact_a_id TEXT NOT NULL,
                artifact_b_id TEXT NOT NULL, conflict_type TEXT NOT NULL, detector TEXT NOT NULL,
                severity TEXT NOT NULL, evidence_json TEXT NOT NULL, status TEXT NOT NULL,
                reconciliation_id TEXT, created_at TEXT NOT NULL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS reconciliations(
                reconciliation_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, conflict_ids_json TEXT NOT NULL,
                decision TEXT NOT NULL, winning_artifact_id TEXT, rationale TEXT NOT NULL,
                resolver_type TEXT NOT NULL, receipt_json TEXT NOT NULL, created_at TEXT NOT NULL)""")

    # ── writes ──
    def put_artifact(self, a: Artifact) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO artifacts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (a.artifact_id, a.tenant_id, a.source_id, a.source_version, a.artifact_type, a.schema_version,
                 a.text, json.dumps(a.payload_json, sort_keys=True), a.content_hash, a.parent_artifact_id,
                 json.dumps(a.source_handles_json), a.pipeline_id, a.pipeline_version, a.processor_id,
                 a.processor_version, a.run_id, a.claim_status, int(a.promotion_eligible),
                 int(a.model_dependent), a.created_at, a.superseded_by))

    def put_edge(self, e: Edge) -> None:
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO artifact_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                              (e.edge_id, e.tenant_id, e.from_artifact_id, e.to_artifact_id, e.edge_type,
                               e.edge_source, e.confidence, json.dumps(e.evidence_json, sort_keys=True),
                               e.pipeline_id, e.processor_id, e.run_id, e.created_at))

    def put_vector(self, v: Vector) -> None:
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO artifact_vectors VALUES(?,?,?,?,?,?,?,?,?,?)",
                              (v.vector_id, v.tenant_id, v.artifact_id, v.vector_provider, v.vector_model,
                               v.vector_version, v.dimensions, json.dumps(v.vector_json), v.content_hash, v.created_at))

    def put_conflict(self, c: Conflict) -> None:
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO conflicts VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                              (c.conflict_id, c.tenant_id, c.artifact_a_id, c.artifact_b_id, c.conflict_type,
                               c.detector, c.severity, json.dumps(c.evidence_json, sort_keys=True), c.status,
                               c.reconciliation_id, c.created_at))

    def put_reconciliation(self, r: Reconciliation) -> None:
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO reconciliations VALUES(?,?,?,?,?,?,?,?,?)",
                              (r.reconciliation_id, r.tenant_id, json.dumps(r.conflict_ids_json), r.decision,
                               r.winning_artifact_id, r.rationale, r.resolver_type,
                               json.dumps(r.receipt_json, sort_keys=True), r.created_at))

    def link_conflict(self, conflict_id: str, reconciliation_id: str, status: str) -> None:
        with self._lock:
            self.conn.execute("UPDATE conflicts SET reconciliation_id=?, status=? WHERE conflict_id=?",
                              (reconciliation_id, status, conflict_id))

    def supersede(self, artifact_id: str, by: str) -> None:
        with self._lock:
            self.conn.execute("UPDATE artifacts SET superseded_by=? WHERE artifact_id=?", (by, artifact_id))

    # ── reads (projections; the ledger is the truth) ──
    def get_artifact(self, artifact_id: str) -> dict | None:
        with self._lock:
            row = self.conn.execute("SELECT * FROM artifacts WHERE artifact_id=?", (artifact_id,)).fetchone()
            cols = [d[0] for d in self.conn.execute("SELECT * FROM artifacts LIMIT 0").description]
        if not row:
            return None
        d = dict(zip(cols, row))
        d["payload_json"] = json.loads(d["payload_json"]); d["source_handles_json"] = json.loads(d["source_handles_json"])
        d["promotion_eligible"] = bool(d["promotion_eligible"]); d["model_dependent"] = bool(d["model_dependent"])
        return d

    def artifacts(self, tenant_id: str, artifact_type: str | None = None) -> list[dict]:
        q = "SELECT artifact_id,artifact_type,claim_status,promotion_eligible,run_id,superseded_by FROM artifacts WHERE tenant_id=?"
        args: list[Any] = [tenant_id]
        if artifact_type:
            q += " AND artifact_type=?"; args.append(artifact_type)
        cols = ("artifact_id", "artifact_type", "claim_status", "promotion_eligible", "run_id", "superseded_by")
        with self._lock:
            return [dict(zip(cols, r)) for r in self.conn.execute(q, args).fetchall()]

    def counts_by_type(self, tenant_id: str) -> dict[str, int]:
        with self._lock:
            return {t: n for t, n in self.conn.execute(
                "SELECT artifact_type,COUNT(*) FROM artifacts WHERE tenant_id=? GROUP BY artifact_type", (tenant_id,)).fetchall()}

    def edge_counts(self, tenant_id: str) -> dict[str, int]:
        with self._lock:
            return {t: n for t, n in self.conn.execute(
                "SELECT edge_type,COUNT(*) FROM artifact_edges WHERE tenant_id=? GROUP BY edge_type", (tenant_id,)).fetchall()}

    def edges(self, tenant_id: str) -> list[dict]:
        cols = ("edge_id", "from_artifact_id", "to_artifact_id", "edge_type", "edge_source", "confidence", "evidence_json")
        with self._lock:
            rows = self.conn.execute(
                "SELECT edge_id,from_artifact_id,to_artifact_id,edge_type,edge_source,confidence,evidence_json "
                "FROM artifact_edges WHERE tenant_id=? ORDER BY edge_id", (tenant_id,)).fetchall()
        out = [dict(zip(cols, r)) for r in rows]
        for e in out:
            e["evidence_json"] = json.loads(e["evidence_json"])
        return out

    def neighbors(self, tenant_id: str, artifact_id: str) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT edge_type,from_artifact_id,to_artifact_id FROM artifact_edges "
                "WHERE tenant_id=? AND (from_artifact_id=? OR to_artifact_id=?) ORDER BY edge_id",
                (tenant_id, artifact_id, artifact_id)).fetchall()
        return [{"edge_type": r[0], "from": r[1], "to": r[2]} for r in rows]

    def vectors(self, tenant_id: str, artifact_id: str | None = None) -> list[dict]:
        q = "SELECT vector_id,artifact_id,vector_provider,vector_model,vector_version,dimensions,vector_json FROM artifact_vectors WHERE tenant_id=?"
        args: list[Any] = [tenant_id]
        if artifact_id:
            q += " AND artifact_id=?"; args.append(artifact_id)
        cols = ("vector_id", "artifact_id", "vector_provider", "vector_model", "vector_version", "dimensions", "vector_json")
        with self._lock:
            out = [dict(zip(cols, r)) for r in self.conn.execute(q, args).fetchall()]
        for v in out:
            v["vector_json"] = json.loads(v["vector_json"])
        return out

    def list_conflicts(self, tenant_id: str) -> list[dict]:
        cols = ("conflict_id", "artifact_a_id", "artifact_b_id", "conflict_type", "detector", "severity", "status", "reconciliation_id")
        with self._lock:
            rows = self.conn.execute(
                "SELECT conflict_id,artifact_a_id,artifact_b_id,conflict_type,detector,severity,status,reconciliation_id "
                "FROM conflicts WHERE tenant_id=? ORDER BY conflict_id", (tenant_id,)).fetchall()
        return [dict(zip(cols, r)) for r in rows]

    def list_reconciliations(self, tenant_id: str) -> list[dict]:
        cols = ("reconciliation_id", "decision", "winning_artifact_id", "rationale", "resolver_type", "receipt_json")
        with self._lock:
            rows = self.conn.execute(
                "SELECT reconciliation_id,decision,winning_artifact_id,rationale,resolver_type,receipt_json "
                "FROM reconciliations WHERE tenant_id=? ORDER BY reconciliation_id", (tenant_id,)).fetchall()
        out = [dict(zip(cols, r)) for r in rows]
        for r in out:
            r["receipt_json"] = json.loads(r["receipt_json"])
        return out

    def counts(self, tenant_id: str) -> dict[str, int]:
        with self._lock:
            c = self.conn
            return {
                "artifacts": c.execute("SELECT COUNT(*) FROM artifacts WHERE tenant_id=?", (tenant_id,)).fetchone()[0],
                "edges": c.execute("SELECT COUNT(*) FROM artifact_edges WHERE tenant_id=?", (tenant_id,)).fetchone()[0],
                "vectors": c.execute("SELECT COUNT(*) FROM artifact_vectors WHERE tenant_id=?", (tenant_id,)).fetchone()[0],
                "conflicts": c.execute("SELECT COUNT(*) FROM conflicts WHERE tenant_id=?", (tenant_id,)).fetchone()[0],
                "reconciliations": c.execute("SELECT COUNT(*) FROM reconciliations WHERE tenant_id=?", (tenant_id,)).fetchone()[0],
            }

    def close(self) -> None:
        with self._lock:
            self.conn.close()
