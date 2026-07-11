#!/usr/bin/env python3
"""Foundry stage_load — Stage 7: emit canonical row families for promoted components.

Turns gate-promoted candidates into the database-backed row families the platform
loads (source_record · normalized_object · object_embedding · index_record ·
label_assignment · dedupe_cluster · **knowledge_entry** · review_ticket), writes
them as JSONL staging, and computes a real embedding per object.

**Promotion-boundary honesty.** Offline, the embedder is a deterministic
hash-bag placeholder, emitted with ``is_placeholder: true`` — **staging only, never
vector-search-committed** (master-goal gate #6: no vector-search promotion without a
*real* embedding). Wire a real ``Embedder`` (sentence-transformers or a hosted route
via `scripts._config`) and the same rows become vector-ready. Dimension + model id
come from the single source (`scripts._config`), never re-typed.

The ``_entries`` a Knowledge Corpus carries become **knowledge_entry** rows — the
individually-addressable "knowledge pages" (design §15.5), each with provenance.

Run ``python -m scripts.foundry.stage_load`` for the offline self-test.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from scripts._config import DEFAULT_EMBEDDING_DIMENSIONS
from scripts.foundry.contracts import PRIMITIVE_BY_TYPE, PROMOTED, REVIEW, BaseStage, Candidate, FoundryContext
from scripts.foundry.access import classify_access
from scripts.foundry.openness import classify as classify_openness

_WORD = re.compile(r"[a-z0-9]+")
_PLACEHOLDER_MODEL = "hash-bow-v1"   # deterministic staging vector; NOT a real embedding


def _sid(text: str, n: int = 16) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:n]


@runtime_checkable
class Embedder(Protocol):
    model: str
    dim: int
    is_real: bool

    def embed(self, text: str) -> list[float]:
        ...


class PlaceholderEmbedder:
    """Deterministic hash-bag vector — STAGING ONLY (``is_real = False``).

    Lets the pipeline emit a complete ``object_embedding`` row offline without a
    model, but the row is flagged ``is_placeholder`` so it can never be treated as
    vector-search-ready. Swap for a real embedder to make objects searchable."""

    is_real = False
    model = _PLACEHOLDER_MODEL

    def __init__(self, dim: int = DEFAULT_EMBEDDING_DIMENSIONS) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _WORD.findall((text or "").lower()):
            h = int(hashlib.blake2b(tok.encode("utf-8"), digest_size=4).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [round(v / norm, 6) for v in vec]


class StageLoadStage(BaseStage):
    """Emit row families for PROMOTED candidates (+ review_ticket for REVIEW)."""

    name = "stage_load"

    def __init__(self, out_dir: str | Path | None = None, embedder: Embedder | None = None) -> None:
        self.out_dir = Path(out_dir) if out_dir else None
        self.embedder = embedder or PlaceholderEmbedder()
        self.rows: dict[str, list[dict]] = {}

    def run(self, batch: list[Candidate], ctx: FoundryContext) -> list[Candidate]:
        rows: dict[str, list[dict]] = defaultdict(list)
        seen_sources: set[str] = set()
        for c in batch:
            if c.decision == PROMOTED:
                self._emit_promoted(c, rows, seen_sources)
                # gate-passed but pending human approval ⇒ also raise a prioritized approval ticket
                if (c.lift or {}).get("approval_status") == "pending_human":
                    rows["review_ticket"].append(self._review_ticket(c, kind="approval"))
            elif c.decision == REVIEW:
                rows["review_ticket"].append(self._review_ticket(c, kind="review"))
        self.rows = dict(rows)
        if self.out_dir is not None:
            self._write(ctx)
        ctx.ledger.notes.append("stage_load row_counts: " + json.dumps(self.row_counts(), sort_keys=True))
        return batch

    # ── row builders ─────────────────────────────────────────────────────────
    def _emit_promoted(self, c: Candidate, rows: dict[str, list[dict]], seen_sources: set[str]) -> None:
        body = c.body or {}
        oid = c.component_id
        src = c.source or {}
        url = src.get("source_url", "")

        # source_record (deduped by url)
        src_id = _sid(url)
        if url and src_id not in seen_sources:
            seen_sources.add(src_id)
            rows["source_record"].append({
                "source_id": src_id, "source_url": url, "author": src.get("author", ""),
                "license": src.get("license", ""), "source_kind": src.get("source_kind", "other"),
            })

        # normalized_object
        rows["normalized_object"].append({
            "object_id": oid, "type": c.target_type, "primitive": PRIMITIVE_BY_TYPE.get(c.target_type, ""),
            "content_hash": c.content_hash, "version_hash": c.version_hash,
            "name": body.get("name", ""), "version": body.get("version", ""),
            "lifecycle": body.get("lifecycle", ""), "source_id": src_id,
        })

        # object_embedding (flagged placeholder unless a real embedder is wired)
        text = f"{body.get('name', '')}\n{body.get('description', '')}"
        rows["object_embedding"].append({
            "object_id": oid, "embedding_model": self.embedder.model, "dimensions": self.embedder.dim,
            "is_placeholder": not getattr(self.embedder, "is_real", False),
            "vector_search_ready": bool(getattr(self.embedder, "is_real", False)),
            "vector": self.embedder.embed(text),
        })

        # index_record (what a hybrid search / facet reads) + the open-core tier + delivery/billing
        lift = c.lift or {}
        openness = classify_openness(c)
        access = classify_access(c)
        rows["index_record"].append({
            "delivery": access["delivery"], "billable_events": access["billable_events"],
            "object_id": oid, "type": c.target_type, "primitive": PRIMITIVE_BY_TYPE.get(c.target_type, ""),
            "name": body.get("name", ""), "industry": body.get("industry", []),
            "capability": body.get("capability", []), "lifecycle": body.get("lifecycle", ""),
            "lift_delta": lift.get("delta"), "durability_class": lift.get("durability_class"),
            "decay_signal": lift.get("decay_signal"), "provenance_ok": bool(url and src.get("license")),
            "license": body.get("license", ""),
            "openness": openness["tier"], "openness_basis": openness["basis"],
            "openness_reason": openness["reason"],
            "approval_status": (c.lift or {}).get("approval_status", "auto"),
        })

        # dedupe_cluster (from the novelty record)
        nov = c.novelty or {}
        rows["dedupe_cluster"].append({
            "object_id": oid, "simhash": nov.get("simhash"), "nearest_id": nov.get("nearest_id"),
            "hamming": nov.get("hamming"), "source_key": nov.get("source_key"),
        })

        # label_assignment (durability/lift_reason + industry/capability facets)
        gap = c.gap or {}
        labels = []
        if gap.get("lift_reason"):
            labels.append(("lift_reason", gap["lift_reason"]))
        if lift.get("durability_class"):
            labels.append(("durability_class", lift["durability_class"]))
        for ind in body.get("industry", []) or []:
            labels.append(("industry", str(ind)))
        for cap in body.get("capability", []) or []:
            labels.append(("capability", str(cap)))
        for path, value in labels:
            rows["label_assignment"].append({"object_id": oid, "label_path": path, "value": value})

        # knowledge_entry — the individually-addressable "knowledge pages" (§15.5)
        for i, entry in enumerate(body.get("_entries", []) or []):
            anchor = entry.get("anchor") if isinstance(entry, dict) else None
            rows["knowledge_entry"].append({
                "entry_id": f"{oid}#{_sid(json.dumps(entry, sort_keys=True), 12)}",
                "corpus_id": oid, "ordinal": i, "anchor": anchor,
                "content": entry if isinstance(entry, dict) else {"text": str(entry)},
                "provenance": {"source_url": url, "author": src.get("author", ""), "license": src.get("license", "")},
            })

    def _review_ticket(self, c: Candidate, *, kind: str = "review") -> dict[str, Any]:
        """A queue item — `kind='approval'` (gate-passed, awaiting human sign-off) or
        `kind='review'` (blocked/uncertain). Prioritized so the human works the best first."""
        gap = c.gap or {}
        lift = c.lift or {}
        gate_passed = bool(lift.get("gate_passed"))
        demand = int(gap.get("demand_count") or gap.get("priority") or 0)
        priority = demand + (10 if gate_passed else 0) + (5 if gap.get("risk_tier") == "high" else 0)
        reasons = c.reasons or ([f"awaiting approval: {lift.get('approval_status')}"] if kind == "approval" else [])
        return {
            "ticket_id": _sid((c.component_id or c.target_type) + "|" + kind + "|" + ";".join(reasons)),
            "kind": kind, "object_hint": c.component_id or c.target_type, "type": c.target_type,
            "reasons": reasons, "gate_passed": gate_passed, "approval_status": lift.get("approval_status"),
            "confirmation_source": gap.get("confirmation_source"),
            "risk": "high" if gap.get("risk_tier") == "high" else "normal",
            "priority": priority, "gap_id": gap.get("id", ""),
        }

    # ── output ────────────────────────────────────────────────────────────────
    def row_counts(self) -> dict[str, int]:
        return {family: len(rs) for family, rs in sorted(self.rows.items())}

    def _write(self, ctx: FoundryContext) -> None:
        base = self.out_dir / ctx.run_id / (ctx.partition or "default")  # type: ignore[operator]
        base.mkdir(parents=True, exist_ok=True)
        for family, rs in self.rows.items():
            (base / f"{family}.jsonl").write_text(
                "".join(json.dumps(r, sort_keys=True, ensure_ascii=True) + "\n" for r in rs), encoding="utf-8"
            )


def _self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    promoted = Candidate(
        target_type="knowledge-pack", component_id="knowledge-pack/csddd-articles-abcd1234",
        content_hash="ch", version_hash="vh",
        body={"id": "knowledge-pack/csddd-articles-abcd1234", "type": "knowledge-pack", "version": "0.1.0",
              "name": "CSDDD article corpus", "description": "Grounded CSDDD article extracts.",
              "industry": ["esg", "supply_chain"], "capability": ["retrieval"], "lifecycle": "experimental",
              "license": "CC-BY-4.0",
              "_entries": [{"anchor": "Article 8", "text": "Due diligence."},
                           {"anchor": "Article 29", "text": "Civil liability."},
                           {"anchor": "Article 22", "text": "Climate plan."}]},
        gap={"id": "gap/csddd", "lift_reason": "esoteric_rule"},
        source={"source_url": "https://eur-lex.europa.eu/csddd", "author": "EU", "license": "CC-BY-4.0",
                "source_kind": "other"},
        lift={"delta": 0.41, "durability_class": "transient", "decay_signal": "watch"},
        novelty={"simhash": 123, "nearest_id": None, "hamming": None, "source_key": "eur-lex.europa.eu/csddd|knowledge-pack"},
    )
    promoted.decision = PROMOTED
    review = Candidate(target_type="tool", component_id="tool/x", reasons=["provenance incomplete — resolve in review"])
    review.decision = REVIEW

    with tempfile.TemporaryDirectory() as tmp:
        stage = StageLoadStage(out_dir=tmp)
        ctx = FoundryContext(partition="esg")
        stage.run([promoted, review], ctx)
        rc = stage.row_counts()
        check("source_record emitted", rc.get("source_record") == 1, str(rc))
        check("normalized_object emitted", rc.get("normalized_object") == 1)
        check("object_embedding emitted", rc.get("object_embedding") == 1)
        check("knowledge_entry = 3 (the knowledge pages)", rc.get("knowledge_entry") == 3, str(rc))
        check("index_record emitted", rc.get("index_record") == 1)
        check("label_assignment emitted (≥3)", rc.get("label_assignment", 0) >= 3)
        check("dedupe_cluster emitted", rc.get("dedupe_cluster") == 1)
        check("review_ticket for REVIEW candidate", rc.get("review_ticket") == 1)

        emb = stage.rows["object_embedding"][0]
        check("embedding flagged placeholder (staging only)", emb["is_placeholder"] is True)
        check("embedding NOT vector-search-ready", emb["vector_search_ready"] is False)
        check("embedding dim from _config single source", emb["dimensions"] == DEFAULT_EMBEDDING_DIMENSIONS)
        check("index_record carries measured lift", stage.rows["index_record"][0]["lift_delta"] == 0.41)
        check("index_record carries open-core tier", stage.rows["index_record"][0].get("openness") in ("open", "commercial"))
        check("EU-public non-RAG corpus ⇒ open tier", stage.rows["index_record"][0]["openness"] == "open",
              stage.rows["index_record"][0].get("openness_reason"))

        wrote = Path(tmp) / ctx.run_id / "esg" / "knowledge_entry.jsonl"
        check("JSONL written to partitioned dir", wrote.exists())
        if wrote.exists():
            check("knowledge_entry JSONL has 3 lines", len(wrote.read_text().splitlines()) == 3)

    # approval queue: a gate-passed pending_human component ⇒ a PRIORITIZED approval ticket
    pend = Candidate(target_type="knowledge-pack", component_id="knowledge-pack/pend",
                     body={"id": "knowledge-pack/pend", "type": "knowledge-pack", "version": "0.1.0",
                           "name": "P", "description": "d", "lifecycle": "experimental", "license": "MIT"},
                     gap={"id": "g", "demand_count": 3, "confirmation_source": "llm_probe"},
                     source={"source_url": "https://x/y", "author": "a", "license": "MIT"},
                     lift={"delta": 0.4, "approval_status": "pending_human", "gate_passed": True})
    pend.decision = PROMOTED
    s2 = StageLoadStage()
    s2.run([pend], FoundryContext())
    appr = [t for t in s2.rows.get("review_ticket", []) if t.get("kind") == "approval"]
    check("pending_human promotion ⇒ approval ticket", len(appr) == 1, str(appr))
    check("approval ticket prioritized (demand + gate_passed)", bool(appr) and appr[0]["priority"] >= 13, str(appr))
    check("index_record carries approval_status", s2.rows["index_record"][0]["approval_status"] == "pending_human")

    # a REAL embedder flips the staging flags
    class RealEmbedder:
        is_real = True
        model = "all-MiniLM-L6-v2"
        dim = DEFAULT_EMBEDDING_DIMENSIONS

        def embed(self, text):
            return [0.1] * self.dim

    stage2 = StageLoadStage(embedder=RealEmbedder())
    stage2.run([promoted], FoundryContext())
    emb2 = stage2.rows["object_embedding"][0]
    check("real embedder ⇒ not placeholder", emb2["is_placeholder"] is False)
    check("real embedder ⇒ vector-search-ready", emb2["vector_search_ready"] is True)

    print(f"\n{'all stage_load self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
