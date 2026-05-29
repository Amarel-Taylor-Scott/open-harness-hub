#!/usr/bin/env python3
"""Foundry interactions — collect user interactions → the experience DB → new components.

Logs every user interaction (search · build · run · improve · view · feedback · adopt ·
export) to a durable, privacy-redacted store, then mines it for **demand** — the
strongest, most *model-independent* gap signal there is: a real user asking for
something the registry can't satisfy. This is the direct answer to "the LLM doesn't
know what it doesn't know" — the **user** does, and a zero-result query proves it.

The loop (the experience-database moat + demand capture):

    interaction → redact + consent-gate → Sink (JSONL now; Postgres via the same load
    path) → DemandMiner → unmet-need **capability-requests** + **research-queue areas**
    → the foundry builds them (the gaps stage already trusts model-independent signals).

Each retrieval interaction also records the **`embedding_model`** used, so an
embedding-model change is auditable and A/B-comparable on real queries — the payoff of
keeping the embedder swappable (`scripts/_config`, `model_route.RouteEmbedder`).

Privacy by construction: PII/secrets redacted, user/tenant ids hashed, logging
consent-gated. stdlib-only. Run `python -m scripts.foundry.interactions` for the test.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable

from scripts.foundry.standardize import slugify

INTERACTION_KINDS = ("search", "build", "run", "improve", "view", "feedback", "adopt", "export", "capability_request")

# --- privacy: redact PII / secrets before anything is stored --------------------
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"\b\+?\d[\d\s().-]{7,}\d\b")
_LONGNUM = re.compile(r"\b\d{9,}\b")              # SSNs, account numbers, …
_SECRET = re.compile(r"\b(?:sk|pk|key|token|bearer|api[_-]?key)[-_:=\s]*[A-Za-z0-9._-]{12,}\b", re.IGNORECASE)


def redact(text: str) -> str:
    if not text:
        return text
    out = _SECRET.sub("[redacted-secret]", text)
    out = _EMAIL.sub("[redacted-email]", out)
    out = _PHONE.sub("[redacted-phone]", out)
    out = _LONGNUM.sub("[redacted-number]", out)
    return out


def _hash_id(value: str) -> str:
    return "anon-" + hashlib.sha256((value or "").encode("utf-8")).hexdigest()[:16] if value else ""


def _redact_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: _redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_obj(v) for v in obj]
    return obj


@dataclass
class Interaction:
    """One user interaction. ``redacted()`` returns the privacy-safe form that is stored."""

    kind: str
    query: str = ""
    ts: str = ""                                    # ISO 8601; pass it in (no hidden clock)
    user: str = ""                                  # raw id — hashed on redaction
    tenant: str = ""                                # raw id — hashed on redaction
    context: dict = field(default_factory=dict)     # {industry, capability, filters, retrieval_mode, embedding_model}
    result: dict = field(default_factory=dict)      # {n_results, zero_result, top_component_ids, retrieval_mode}
    outcome: dict = field(default_factory=dict)     # {adopted, exported, components_used, lift_seen, cost, satisfied}
    consent: bool = True
    interaction_id: str = ""

    def redacted(self) -> "Interaction":
        q = redact(self.query)
        tenant_h, user_h = _hash_id(self.tenant), _hash_id(self.user)
        iid = self.interaction_id or "ix-" + hashlib.sha256(
            f"{self.kind}|{q}|{tenant_h}|{self.ts}".encode("utf-8")).hexdigest()[:16]
        return Interaction(
            kind=self.kind, query=q, ts=self.ts, user=user_h, tenant=tenant_h,
            context=_redact_obj(self.context), result=_redact_obj(self.result),
            outcome=_redact_obj(self.outcome), consent=self.consent, interaction_id=iid,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --- sink: where redacted interactions land (swappable) -------------------------
@runtime_checkable
class Sink(Protocol):
    def write(self, record: dict) -> None: ...


class JsonlSink:
    """Append-only local store. Production swaps a Postgres adapter (same row contract)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(ln) for ln in self.path.read_text(encoding="utf-8").splitlines() if ln.strip()]


class StoreSink:
    """Persist interactions to the foundry Store (DB) — the production sink. Same `Store`
    that holds the row families, so interactions live in the experience DB, not a file."""

    def __init__(self, store: Any, *, table: str = "interaction_record") -> None:
        self.store = store
        self.table = table

    def write(self, record: dict) -> None:
        self.store.write(self.table, [record])

    def read(self) -> list[dict]:
        return self.store.read(self.table, limit=100000)


def sink_from_env() -> Sink:
    """Pick the interaction sink: the Store (DB) when configured, else a local JSONL file —
    the same local→cloud switch as everything else (env only)."""
    if os.environ.get("DATABASE_URL") or os.environ.get("OH_STORE"):
        from scripts.foundry.store import from_env as store_from_env
        return StoreSink(store_from_env())
    return JsonlSink(os.environ.get("OH_INTERACTIONS_PATH", "dist/interactions.jsonl"))


class InteractionLog:
    """Redact + consent-gate + persist. The web tier calls ``log()`` on every interaction."""

    def __init__(self, sink: Sink, *, require_consent: bool = True) -> None:
        self.sink = sink
        self.require_consent = require_consent

    def log(self, interaction: Interaction) -> Interaction | None:
        if self.require_consent and not interaction.consent:
            return None
        safe = interaction.redacted()
        self.sink.write(safe.to_dict())
        return safe


# --- mining: user demand → unmet needs → capability-requests + research areas ----
def _norm_query(q: str) -> str:
    return re.sub(r"\s+", " ", (q or "").strip().lower())


class DemandMiner:
    """Aggregate logged interactions into demand; turn unmet demand into build fuel.

    Unmet = repeated demand with high zero-result rate OR low adoption — i.e. the
    registry isn't answering it. Each becomes a capability-request (build-on-demand)
    and a research-queue area, tagged ``user_demand`` (model-independent)."""

    def __init__(self, *, min_demand: int = 2, zero_result_unmet: float = 0.5,
                 low_adopt_unmet: float = 0.34) -> None:
        self.min_demand = min_demand
        self.zero_result_unmet = zero_result_unmet
        self.low_adopt_unmet = low_adopt_unmet

    @staticmethod
    def _records(interactions: Iterable[Any]) -> list[dict]:
        out = []
        for it in interactions:
            out.append(it.to_dict() if isinstance(it, Interaction) else dict(it))
        return out

    def mine(self, interactions: Iterable[Any]) -> dict[str, Any]:
        recs = self._records(interactions)
        counts: Counter = Counter()
        zero: dict[str, int] = defaultdict(int)
        adopt: dict[str, int] = defaultdict(int)
        examples: dict[str, list[str]] = defaultdict(list)
        embed_models: set[str] = set()
        for r in recs:
            q = _norm_query(r.get("query", ""))
            if not q:
                continue
            counts[q] += 1
            res, outc, ctx = r.get("result") or {}, r.get("outcome") or {}, r.get("context") or {}
            if res.get("zero_result") or res.get("n_results") == 0:
                zero[q] += 1
            if outc.get("adopted"):
                adopt[q] += 1
            if r.get("interaction_id"):
                examples[q].append(r["interaction_id"])
            if ctx.get("embedding_model"):
                embed_models.add(ctx["embedding_model"])

        demand = []
        for q, c in counts.most_common():
            demand.append({
                "query": q, "demand_count": c,
                "zero_result_rate": round(zero[q] / c, 3),
                "adopt_rate": round(adopt[q] / c, 3),
                "examples": examples[q][:5],
            })
        unmet = [d for d in demand if d["demand_count"] >= self.min_demand
                 and (d["zero_result_rate"] >= self.zero_result_unmet or d["adopt_rate"] < self.low_adopt_unmet)]
        return {
            "demand": demand,
            "unmet": unmet,
            "capability_requests": [self._to_capreq(d) for d in unmet],
            "research_queue": [self._to_area(d) for d in unmet],
            "embedding_models_seen": sorted(embed_models),   # auditability of embedding changes
        }

    @staticmethod
    def _to_capreq(d: dict) -> dict:
        return {
            "id": f"capability-request/{slugify(d['query'])}",
            "title": d["query"], "target_type": None, "maturity": "abstract", "status": "requested",
            "demand_count": d["demand_count"], "signal": "user_demand (model-independent)",
            "evidence": {"zero_result_rate": d["zero_result_rate"], "adopt_rate": d["adopt_rate"],
                         "example_interactions": d["examples"]},
        }

    @staticmethod
    def _to_area(d: dict) -> dict:
        # research-queue (areas.jsonl) shape — demand is the model-independent signal;
        # model-self-report fields (confident_hallucination) are intentionally absent.
        return {
            "area": d["query"], "use_case": "", "status": "queued", "source": "user_interactions",
            "model_independent_signal": "user_demand", "demand_count": d["demand_count"],
            "query_misses": int(round(d["zero_result_rate"] * d["demand_count"])),
            "current_coverage": round(d["adopt_rate"], 3),
            "why": f"user demand: {d['demand_count']} queries, {int(d['zero_result_rate']*100)}% zero-result",
        }


# --- self-test (offline) --------------------------------------------------------
def _self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # redaction + hashing
    it = Interaction(kind="search", query="screen jane@acme.com phone 415-555-1234 key sk-ABCDEF1234567890",
                     user="user-42", tenant="acme", ts="2026-05-28T00:00:00Z")
    r = it.redacted()
    check("email redacted", "[redacted-email]" in r.query and "jane@acme.com" not in r.query, r.query)
    check("phone redacted", "[redacted-phone]" in r.query)
    check("secret redacted", "[redacted-secret]" in r.query and "sk-ABCDEF" not in r.query, r.query)
    check("user id hashed", r.user.startswith("anon-") and "user-42" not in r.user)
    check("interaction_id assigned", r.interaction_id.startswith("ix-"))

    # consent gate + sink
    with tempfile.TemporaryDirectory() as tmp:
        sink = JsonlSink(Path(tmp) / "ix.jsonl")
        log = InteractionLog(sink)
        check("consent=False ⇒ not logged", log.log(Interaction(kind="search", query="x", consent=False)) is None)
        log.log(Interaction(kind="search", query="hello", ts="t", consent=True))
        check("consented interaction stored (redacted)", len(sink.read()) == 1 and sink.read()[0]["query"] == "hello")

        # StoreSink → the DB, and DemandMiner reads demand back out of it (no file placeholder)
        from scripts.foundry.store import SqliteStore
        st = SqliteStore(Path(tmp) / "ix.sqlite")
        slog = InteractionLog(StoreSink(st))
        for i in range(3):
            slog.log(Interaction(kind="search", query="EUDR polygon validator", ts=f"t{i}",
                                 result={"zero_result": True}, consent=True))
        check("StoreSink persists interactions to the DB", st.count("interaction_record") == 3)
        mined = DemandMiner().mine(StoreSink(st).read())
        check("demand mined from the DB store", any(u["query"] == "eudr polygon validator" for u in mined["unmet"]), str(mined["unmet"]))

    # demand mining: an unmet, repeated, zero-result query ⇒ capability-request + area
    ixs = []
    for i in range(3):
        ixs.append(Interaction(kind="search", query="EUDR geolocation polygon validator", ts=f"t{i}",
                               context={"embedding_model": "nomic-embed-text"},
                               result={"n_results": 0, "zero_result": True}).redacted())
    # a satisfied query (adopted) ⇒ NOT unmet
    for i in range(3):
        ixs.append(Interaction(kind="search", query="redact pii from a pdf", ts=f"s{i}",
                               result={"n_results": 5}, outcome={"adopted": True}).redacted())
    mined = DemandMiner().mine(ixs)
    unmet_q = [u["query"] for u in mined["unmet"]]
    check("repeated zero-result query is unmet", "eudr geolocation polygon validator" in unmet_q, str(unmet_q))
    check("satisfied/adopted query is NOT unmet", "redact pii from a pdf" not in unmet_q, str(unmet_q))
    creq = mined["capability_requests"][0]
    check("unmet ⇒ capability-request (abstract, requested)",
          creq["maturity"] == "abstract" and creq["status"] == "requested" and creq["demand_count"] == 3, str(creq))
    check("capability-request signal is model-independent user demand", "user_demand" in creq["signal"])
    area = mined["research_queue"][0]
    check("unmet ⇒ research-queue area tagged user_demand", area["source"] == "user_interactions"
          and area["model_independent_signal"] == "user_demand", str(area))
    check("embedding model recorded for A/B auditability", "nomic-embed-text" in mined["embedding_models_seen"])

    print(f"\n{'all interactions self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Foundry interactions — log + mine user demand.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--mine", nargs="?", const="store", default=None,
                   help="mine demand: `--mine` reads the DB store; `--mine PATH` reads a JSONL sink")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.mine is not None:
        if args.mine == "store":
            from scripts.foundry.store import from_env as store_from_env
            recs = store_from_env().read("interaction_record", limit=100000)
        else:
            recs = JsonlSink(args.mine).read()
        out = DemandMiner().mine(recs)
        print(json.dumps({"unmet": len(out["unmet"]),
                          "capability_requests": out["capability_requests"],
                          "research_queue": out["research_queue"],
                          "embedding_models_seen": out["embedding_models_seen"]}, indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
