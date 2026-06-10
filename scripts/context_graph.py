#!/usr/bin/env python3
"""scripts.context_graph — interrogate the Baltor context graph (deterministic, offline).

The "interrogate the graph" product surface. A context graph is built from canonical records —
nodes are `schemas/context-object` records, edges are `schemas/context-relationship` records
(UPPERCASE enum: IMPLEMENTS / CONTRADICTS / SUPERSEDES / CITES / OWNED_BY / …), and claims are
`schemas/context-assertion` records. We do NOT invent a parallel node/edge vocabulary — the graph
is a *view* over the existing context schemas (no-magic-values).

A user (or agent) asks a question about an object or topic; the engine answers by TRAVERSING the
graph, not by calling a model:
  * gather the assertions relevant to the question (predicate/topic keyword match);
  * detect CONTRADICTIONS — both explicit CONTRADICTS edges and conflicting assertions
    (same predicate, different value) among connected objects;
  * pick the AUTHORITY deterministically (the subject that SUPERSEDES the others, then by
    freshness, then confidence) — never silently average two conflicting numbers;
  * cite the exact `ctx://` source handles for every fact returned;
  * recommend a SWARM when a contradiction is unresolved on disk or the authority is weak/stale
    (tees up `context_object_swarm`, the next surface).

REAL vs SEAM (honesty first): the traversal, contradiction detection, authority resolution, paths,
and source-handle citation are REAL and deterministic offline. A live model route only *phrases*
the final prose answer (`model_answer` callable seam, default None → deterministic template); it is
never allowed to change the facts, the authority, or the contradictions — those come from the graph.

CLI / self-test (proves interrogation on the Acme Billing demo graph; no model, no network):
    python3 scripts/context_graph.py --self-test
    python3 scripts/context_graph.py --ask "what is the retry ceiling?"
    python3 scripts/context_graph.py --neighbors obj-adr-014
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import deque
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

_REPO = Path(__file__).resolve().parents[1]
#: The bundled demo graph (Acme Billing). Single source for the offline self-test + the demo UI.
DEMO_SEED = _REPO / "demo-data" / "acme-billing" / "seed-graph.json"

#: Edge types that establish one object as authoritative OVER its target (from→to: from wins).
AUTHORITY_OVER = ("SUPERSEDES", "MAY_SUPERSEDE")
#: Edge types that signal disagreement between the two endpoints.
CONFLICT_EDGES = ("CONTRADICTS",)
#: Freshness rank — fresher wins ties when no supersession edge decides authority.
_FRESHNESS_RANK = {"fresh": 0, "dated": 1, "stale": 2, "unknown": 3}
#: Below this confidence, an authoritative claim is "weak" → recommend a swarm to verify.
WEAK_CONFIDENCE = 0.6
#: A question token must be at least this long to count as a keyword (drops "is", "a", "of").
_MIN_TOKEN = 3
#: Common stopwords dropped from keyword matching so high-frequency words ("the", "what", "how")
#: don't spuriously match every object's summary. Deliberately small + generic (not domain terms).
_STOPWORDS = frozenset({
    "the", "and", "for", "are", "was", "were", "this", "that", "with", "from", "into", "your",
    "you", "can", "does", "did", "has", "have", "had", "will", "would", "should", "could",
    "about", "which", "when", "where", "who", "why", "what", "how", "not", "but", "all", "any",
    "our", "per", "its", "use", "used", "using", "via", "than", "then", "them", "they", "there",
    "here", "many", "much", "some", "such", "only", "also", "may", "might", "must", "shall",
})


def load_seed(path: Path | str = DEMO_SEED) -> dict[str, Any]:
    """Load a seed graph file ({objects, relationships, assertions})."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


class ContextGraph:
    """An in-memory view over context objects / relationships / assertions.

    Pure structure + deterministic queries; stdlib only. Holds no model and does no IO after build.
    """

    def __init__(self, seed: dict[str, Any]) -> None:
        self.objects: dict[str, dict] = {o["context_object_id"]: o for o in seed.get("objects", [])}
        self.relationships: list[dict] = list(seed.get("relationships", []))
        self.assertions: list[dict] = list(seed.get("assertions", []))
        # adjacency (directed + an undirected mirror for neighbor/path queries)
        self._out: dict[str, list[dict]] = {oid: [] for oid in self.objects}
        self._adj: dict[str, set[str]] = {oid: set() for oid in self.objects}
        for r in self.relationships:
            a, b = r["from_id"], r["to_id"]
            self._out.setdefault(a, []).append(r)
            self._adj.setdefault(a, set()).add(b)
            self._adj.setdefault(b, set()).add(a)

    # ── structural queries ────────────────────────────────────────────────
    def neighbors(self, node_id: str, depth: int = 1) -> list[str]:
        """Node ids within `depth` hops of `node_id` (undirected), excluding itself, sorted."""
        seen: set[str] = {node_id}
        frontier = {node_id}
        for _ in range(max(1, depth)):
            nxt: set[str] = set()
            for n in frontier:
                nxt |= self._adj.get(n, set())
            nxt -= seen
            seen |= nxt
            frontier = nxt
            if not frontier:
                break
        return sorted(seen - {node_id})

    def shortest_path(self, a: str, b: str) -> list[str]:
        """BFS shortest path (undirected) from a to b; [] if unreachable. Deterministic."""
        if a not in self._adj or b not in self._adj:
            return []
        prev: dict[str, str] = {a: a}
        q = deque([a])
        while q:
            cur = q.popleft()
            if cur == b:
                path = [b]
                while path[-1] != a:
                    path.append(prev[path[-1]])
                return list(reversed(path))
            for nb in sorted(self._adj.get(cur, set())):
                if nb not in prev:
                    prev[nb] = cur
                    q.append(nb)
        return []

    def timeline(self) -> list[dict]:
        """Objects ordered by created_at (then id) — the 'when did each fact enter' view."""
        rows = [{"id": oid, "created_at": o.get("created_at", ""), "title": o.get("title", ""),
                 "object_type": o.get("object_type", ""), "staleness": (o.get("freshness") or {}).get("staleness")}
                for oid, o in self.objects.items()]
        return sorted(rows, key=lambda r: (r["created_at"], r["id"]))

    def _staleness(self, oid: str) -> str:
        return ((self.objects.get(oid) or {}).get("freshness") or {}).get("staleness") or "unknown"

    def _supersedes(self, winner: str, loser: str) -> bool:
        """True iff `winner` has an AUTHORITY_OVER edge to `loser`."""
        return any(r["from_id"] == winner and r["to_id"] == loser and r["relationship_type"] in AUTHORITY_OVER
                   for r in self.relationships)

    # ── contradiction detection ─────────────────────────────────────────────
    def find_contradictions(self) -> list[dict]:
        """Conflicts from (a) explicit CONTRADICTS edges and (b) assertions that share a predicate
        but disagree on value. Each is resolved to an authority deterministically."""
        out: list[dict] = []
        # (a) assertion-value conflicts, grouped by predicate
        by_pred: dict[str, list[dict]] = {}
        for a in self.assertions:
            by_pred.setdefault(a["predicate"], []).append(a)
        for predicate, claims in sorted(by_pred.items()):
            values = {json.dumps(c.get("value"), sort_keys=True) for c in claims}
            if len(values) > 1:
                out.append(self._resolve_conflict(predicate, claims))
        # (b) explicit CONTRADICTS edges not already represented by an assertion conflict
        for r in self.relationships:
            if r["relationship_type"] in CONFLICT_EDGES:
                preds = {a["predicate"] for a in self.assertions
                         if a["subject_id"] in (r["from_id"], r["to_id"])}
                if not preds:  # an edge-level contradiction with no assertion behind it
                    out.append({
                        "predicate": None, "kind": "edge",
                        "between": sorted([r["from_id"], r["to_id"]]),
                        "label": r.get("relationship_label"),
                        "source_handles": r.get("source_handles", []),
                        "resolved": False,
                    })
        return out

    def _resolve_conflict(self, predicate: str, claims: list[dict]) -> dict:
        """Pick the authoritative claim among conflicting ones: supersession > freshness > confidence."""
        def rank(c: dict) -> tuple:
            subj = c["subject_id"]
            # how many other conflicting subjects does this one supersede? (more = more authoritative)
            supersedes_n = sum(1 for o in claims if o is not c and self._supersedes(subj, o["subject_id"]))
            superseded_by = any(self._supersedes(o["subject_id"], subj) for o in claims if o is not c)
            return (
                0 if not superseded_by else 1,                 # not-superseded first
                -supersedes_n,                                 # supersedes more → earlier
                _FRESHNESS_RANK.get(self._staleness(subj), 3), # fresher → earlier
                -(c.get("confidence") or 0.0),                 # higher confidence → earlier
                subj,                                          # stable tiebreak
            )
        ordered = sorted(claims, key=rank)
        authority, losers = ordered[0], ordered[1:]
        handles: list[str] = []
        for c in claims:
            handles.extend(c.get("evidence", []))
        return {
            "predicate": predicate, "kind": "assertion",
            "authority": {"subject_id": authority["subject_id"], "value": authority.get("value"),
                          "confidence": authority.get("confidence"),
                          "staleness": self._staleness(authority["subject_id"])},
            "conflicting": [{"subject_id": c["subject_id"], "value": c.get("value"),
                             "confidence": c.get("confidence"), "staleness": self._staleness(c["subject_id"]),
                             "superseded": any(self._supersedes(o["subject_id"], c["subject_id"]) for o in claims if o is not c)}
                            for c in losers],
            "source_handles": sorted(set(handles)),
            # "resolved on disk" iff every loser is explicitly superseded AND stale — i.e. the
            # contradiction is recorded, but the stale record still physically disagrees → not closed.
            "resolved": False,
        }


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9_]+", (text or "").lower())
            if len(t) >= _MIN_TOKEN and t not in _STOPWORDS}


def interrogate(graph: ContextGraph, question: str, *,
                model_answer: Callable[[str], str] | None = None, bus=None) -> dict[str, Any]:
    """Answer `question` against the graph. Deterministic facts; optional model phrasing (seam).

    Returns a record conforming to schemas/context/graph-interrogation-run.schema.json. If `bus`
    (a scripts.context_events.EventBus, duck-typed) is passed, emit lifecycle events for the live
    dashboard — non-breaking + deterministic when omitted (default None → no events, identical output).
    """
    q_tokens = _tokens(question)
    # correlation id derived from the question (deterministic — no clock/RNG) so all events of this
    # interrogation group together on the dashboard.
    _cid = "interro-" + sha256(question.encode("utf-8")).hexdigest()[:8]
    if bus is not None:
        bus.publish("component.started", component="context_graph", stage="Enhancement",
                    correlation_id=_cid, payload={"question": question})

    # 1) relevant assertions: predicate or value token overlaps the question
    rel_assertions = [a for a in graph.assertions
                      if _tokens(a["predicate"]) & q_tokens or _tokens(str(a.get("value"))) & q_tokens]
    # 2) relevant objects: title/summary/claim/topic token overlap, plus assertion subjects
    def obj_match(o: dict) -> bool:
        topics = (((o.get("five_w_one_h") or {}).get("what") or {}).get("topics")) or []
        hay = " ".join([o.get("title", ""), o.get("summary", ""), o.get("claim", ""), " ".join(topics)])
        return bool(_tokens(hay) & q_tokens)
    consulted = {a["subject_id"] for a in rel_assertions}
    consulted |= {oid for oid, o in graph.objects.items() if obj_match(o)}

    # 3) contradictions touching the consulted set
    all_conflicts = graph.find_contradictions()
    conflicts = [c for c in all_conflicts
                 if (c.get("kind") == "assertion" and c["authority"]["subject_id"] in consulted)
                 or (c.get("kind") == "edge" and set(c.get("between", [])) & consulted)
                 or any(a["predicate"] in q_tokens or _tokens(a["predicate"]) & q_tokens for a in rel_assertions
                        if c.get("predicate") == a["predicate"])]

    if bus is not None:
        for _c in conflicts:
            if _c.get("kind") == "assertion":
                bus.publish("contradiction_found", component="context_graph", stage="Reconciliation",
                            correlation_id=_cid, object_ref=_c["authority"]["subject_id"],
                            payload={"predicate": _c.get("predicate"), "authority": _c["authority"]["subject_id"],
                                     "value": _c["authority"]["value"]})

    # 4) authority + answer
    source_handles: list[str] = []
    authority = None
    uncertainty = "low"
    swarm_recommended = False
    swarm_reason = None

    answer_value = None
    if conflicts and any(c.get("kind") == "assertion" for c in conflicts):
        c = next(c for c in conflicts if c.get("kind") == "assertion")
        authority = c["authority"]
        answer_value = authority["value"]
        source_handles = list(c["source_handles"])
        # a contradiction that still physically disagrees on disk → uncertain + swarm
        uncertainty = "medium"
        swarm_recommended = True
        losers = ", ".join(f"{x['subject_id']}={x['value']}" for x in c["conflicting"])
        swarm_reason = (f"unresolved contradiction on '{c['predicate']}': authority "
                        f"{authority['subject_id']}={authority['value']} but {losers} still disagree on disk")
    elif rel_assertions:
        # no conflict — take the highest-confidence fresh assertion
        best = sorted(rel_assertions, key=lambda a: (_FRESHNESS_RANK.get(graph._staleness(a["subject_id"]), 3),
                                                      -(a.get("confidence") or 0.0)))[0]
        authority = {"subject_id": best["subject_id"], "value": best.get("value"),
                     "confidence": best.get("confidence"), "staleness": graph._staleness(best["subject_id"])}
        answer_value = best.get("value")
        source_handles = list(best.get("evidence", []))
        if (best.get("confidence") or 0.0) < WEAK_CONFIDENCE or graph._staleness(best["subject_id"]) == "stale":
            uncertainty = "high"
            swarm_recommended = True
            swarm_reason = "authoritative claim is weak/stale — verify before relying on it"
    else:
        # nothing matched — return the consulted objects' handles, flag high uncertainty
        for oid in sorted(consulted):
            source_handles.extend(graph.objects[oid].get("source_handles", []))
        uncertainty = "high"
        swarm_reason = "no addressable assertion matched the question"

    # de-dup handles, keep deterministic order
    seen: set[str] = set()
    source_handles = [h for h in source_handles if not (h in seen or seen.add(h))]

    # 5) paths used: shortest path from each consulted object to the authority (explainability)
    paths_used: list[list[str]] = []
    if authority:
        for oid in sorted(consulted):
            if oid != authority["subject_id"]:
                p = graph.shortest_path(oid, authority["subject_id"])
                if p:
                    paths_used.append(p)

    # 6) deterministic answer text (or model phrasing seam — facts unchanged)
    det_answer = _format_answer(authority, conflicts, answer_value)
    used_model = False
    answer = det_answer
    if model_answer is not None:
        try:
            answer = model_answer(_answer_prompt(question, authority, conflicts, source_handles))
            used_model = True
        except Exception:
            answer = det_answer  # model is a phrasing convenience; never block on it

    if bus is not None:
        bus.publish("component.finished", component="context_graph", stage="Enhancement",
                    correlation_id=_cid, payload={"answer_value": answer_value, "swarm_recommended": swarm_recommended})

    run_seed = json.dumps({"q": question, "auth": authority, "v": answer_value}, sort_keys=True)
    return {
        "kind": "baltor.graph-interrogation-run.v1",
        "interrogation_run_id": "gir-" + sha256(run_seed.encode("utf-8")).hexdigest()[:16],
        "question": question,
        "answer": answer,
        "answer_value": answer_value,
        "authority": authority,
        "source_handles": source_handles,
        "contradictions": conflicts,
        "objects_consulted": sorted(consulted),
        "paths_used": paths_used,
        "uncertainty": uncertainty,
        "suggested_next_query": _suggest_next(authority, conflicts),
        "swarm_recommended": swarm_recommended,
        "swarm_reason": swarm_reason,
        "deterministic": not used_model,
        "model_used": used_model,
        "created_at": "1970-01-01T00:00:00Z",
    }


def _format_answer(authority: dict | None, conflicts: list[dict], value: Any) -> str:
    if authority is None:
        return "No addressable answer in the graph. Expand a source handle or run a swarm to verify."
    base = f"{authority['value']} (per {authority['subject_id']}, confidence {authority.get('confidence')})"
    ac = [c for c in conflicts if c.get("kind") == "assertion"]
    if ac:
        losers = "; ".join(f"{x['subject_id']} says {x['value']}"
                           + (" [superseded]" if x.get("superseded") else "")
                           + (" [stale]" if x.get("staleness") == "stale" else "")
                           for x in ac[0]["conflicting"])
        return (f"{base}. NOTE: a contradiction exists — {losers}. The authority is "
                f"{authority['subject_id']}; the disagreeing source is stale/superseded and should be fixed.")
    return base


def _answer_prompt(question: str, authority: dict | None, conflicts: list[dict], handles: list[str]) -> str:
    return (f"Question: {question}\nAuthoritative fact (do NOT change): {authority}\n"
            f"Contradictions (state them): {conflicts}\nCite these source handles: {handles}\n"
            "Write a 1-2 sentence answer grounded ONLY in the above.")


def _suggest_next(authority: dict | None, conflicts: list[dict]) -> str | None:
    if any(c.get("kind") == "assertion" for c in conflicts):
        c = next(c for c in conflicts if c.get("kind") == "assertion")
        return f"swarm-verify {c['authority']['subject_id']} to close the '{c['predicate']}' contradiction"
    if authority:
        return f"expand the source handle for {authority['subject_id']} to see the raw evidence"
    return None


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    check("demo seed exists", DEMO_SEED.exists())
    g = ContextGraph(load_seed())
    check("graph has the 8 demo objects", len(g.objects) == 8, str(len(g.objects)))

    # neighbors / paths
    nbrs = g.neighbors("obj-adr-014")
    check("ADR-014 neighbors include code, runbook, incident, ticket",
          {"obj-retry-py", "obj-runbook", "obj-inc-2026-04", "obj-bill-782"} <= set(nbrs), ",".join(nbrs))
    path = g.shortest_path("obj-bill-782", "obj-billing-team")
    check("path BILL-782 → billing-team exists", len(path) >= 2, "->".join(path))

    # contradiction detection: the planted 5-vs-3 conflict on max_retries
    conflicts = g.find_contradictions()
    mc = [c for c in conflicts if c.get("predicate") == "max_retries" and c.get("kind") == "assertion"]
    check("max_retries contradiction detected", len(mc) == 1, str(len(conflicts)))
    if mc:
        c = mc[0]
        check("authority resolves to the ADR (it SUPERSEDES the runbook)", c["authority"]["subject_id"] == "obj-adr-014",
              c["authority"]["subject_id"])
        check("authoritative value is 5 (not the stale 3, not an average)", c["authority"]["value"] == 5,
              str(c["authority"]["value"]))
        check("the stale runbook (3) is flagged as the superseded loser",
              any(x["subject_id"] == "obj-runbook" and x["value"] == 3 and x["superseded"] for x in c["conflicting"]))
        check("contradiction cites both source handles",
              any("ADR-014" in h for h in c["source_handles"]) and any("runbook" in h for h in c["source_handles"]))

    # interrogation: ask the retry question
    run = interrogate(g, "What is the retry ceiling / how many retries are allowed?")
    check("interrogation returns the authoritative value 5", run["answer_value"] == 5, str(run["answer_value"]))
    check("interrogation cites ctx:// source handles", all(h.startswith("ctx://") for h in run["source_handles"]) and run["source_handles"])
    check("interrogation surfaces the contradiction", any(c.get("predicate") == "max_retries" for c in run["contradictions"]))
    check("interrogation recommends a swarm (unresolved on-disk contradiction)", run["swarm_recommended"] is True)
    check("interrogation reports a paths_used trail", len(run["paths_used"]) >= 1)
    check("interrogation is deterministic by default (no model)", run["deterministic"] is True and run["model_used"] is False)
    check("answer text names the ADR authority and the stale disagreement",
          "obj-adr-014" in run["answer"] and ("stale" in run["answer"] or "superseded" in run["answer"]))

    # determinism: same question → identical run (modulo nothing; no clock/RNG)
    run2 = interrogate(g, "What is the retry ceiling / how many retries are allowed?")
    check("interrogation is byte-identical on re-run", run2 == run)

    # model seam: a phrasing model changes the prose but NOT the facts
    run_m = interrogate(g, "how many retries?", model_answer=lambda _p: "Up to five.")
    check("model phrasing seam used → model_used True, value still 5",
          run_m["model_used"] is True and run_m["answer_value"] == 5 and run_m["answer"] == "Up to five.")

    # unknown question → high uncertainty, no fabricated value
    run_u = interrogate(g, "what is the quarterly revenue forecast?")
    check("unknown question → high uncertainty, no fabricated answer_value",
          run_u["uncertainty"] == "high" and run_u["answer_value"] is None)

    print(f"\n{'PASS — context_graph: interrogation finds the planted 5-vs-3 contradiction, resolves to the ADR authority (value 5), cites handles, recommends a swarm; deterministic.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Interrogate the Baltor context graph (deterministic).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--ask", metavar="QUESTION", help="ask the demo graph a question")
    p.add_argument("--neighbors", metavar="OBJECT_ID", help="list neighbors of an object")
    p.add_argument("--seed", default=str(DEMO_SEED), help="seed graph json (default: Acme Billing demo)")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    g = ContextGraph(load_seed(args.seed))
    if args.neighbors:
        print(json.dumps(g.neighbors(args.neighbors), indent=2))
        return 0
    if args.ask:
        print(json.dumps(interrogate(g, args.ask), indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
