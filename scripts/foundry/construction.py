#!/usr/bin/env python3
"""Foundry construction — Stage 2: mine a source into typed components.

This replaces ``run_factory``'s deterministic *stub* proposer with a real
constructor: given a confirmed gap + an acquired source, an ``Author`` mines the
source's material into one-or-more **typed component drafts** (a Knowledge Corpus
of grounded entries, a Conditional/rule pack, an Action/tool wrapper, …). One rich
source expands into *many* genuine components — the affordable path to volume
(deterministic mining, no per-fact model call), as opposed to a cross-product.

The offline ``DeterministicAuthor`` mines a source ``payload`` deterministically
(facts → a schema-valid Knowledge Corpus carrying its entries). Production wires an
LLM/agent ``Author`` (a Claude sub-agent) for material that needs judgment, and
small-model polish — behind the same protocol. Constructed bodies are
schema-complete so Stage 3 (standardize) validates them against the real schemas.

A constructed candidate copies the gap + source (so the evidence travels with it,
including the gap's ``eval_tasks`` that Stage 5 measures). Run
``python -m scripts.foundry.construction`` for the offline self-test.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from scripts.foundry.contracts import BaseStage, Candidate, FoundryContext
from scripts.foundry.sources import normalize_source_kind
from scripts.foundry.standardize import slugify


@runtime_checkable
class Author(Protocol):
    def build(self, gap: dict, source: dict, ctx: FoundryContext) -> list[dict]:
        """Return a list of ``{"target_type": str, "body": dict}`` drafts (schema-complete)."""
        ...


class DeterministicAuthor:
    """Offline author: mine ``source['payload']`` into typed components, no model.

    Supported payload shapes (extend per source kind):
      - ``facts: [...]``  → a Knowledge Corpus (``knowledge-pack``) carrying the
        entries (the "knowledge pages") under ``_entries`` for Stage 7 to emit.
    """

    name = "deterministic-extractor"

    def build(self, gap: dict, source: dict, ctx: FoundryContext) -> list[dict]:
        payload: dict[str, Any] = (source or {}).get("payload") or {}
        drafts: list[dict] = []
        facts = payload.get("facts") or []
        if facts:
            drafts.append(self._knowledge_corpus(gap, source, payload, facts))
        rules = payload.get("rules") or []
        if rules:
            drafts.append(self._conditional(gap, source, payload, rules))
        # future: payload['api'] → tool (Action); payload['rubric'] → rubric (Action: Evaluate)
        return drafts

    @staticmethod
    def _knowledge_corpus(gap: dict, source: dict, payload: dict, facts: list) -> dict:
        name = str(payload.get("name") or gap.get("summary") or "Knowledge corpus")[:128]
        url = source.get("source_url", "")
        desc = payload.get("description") or (
            f"{gap.get('summary', 'Grounded reference corpus')} "
            f"Mined {len(facts)} attributable entries from {url or 'the source'} to supply facts a "
            f"bare model lacks or misremembers, with citations and per-entry provenance."
        )
        body = {
            "type": "knowledge-pack",
            "name": name,
            "description": desc,
            "industry": list(payload.get("industry") or []),
            "capability": list(payload.get("capability") or ["retrieval"]),
            "modality": list(payload.get("modality") or ["text"]),
            "content_types": list(payload.get("content_types") or ["rag_doc"]),
            "retrieval": list(payload.get("retrieval") or ["rag_vector"]),
            "freshness": payload.get("freshness", "dated"),
            "files": [{"path": f"data/foundry/{slugify(name)}.jsonl", "format": "jsonl"}],
            "provenance": {"sources": [url] if url else []},
            "attribution": {
                "source_url": url,
                "source_kind": normalize_source_kind(source.get("source_kind", "other")),
                "author": source.get("author", ""),
                "license": source.get("license", ""),
            },
            # the individual knowledge entries ("knowledge pages") — Stage 7 emits these as
            # entry rows; underscore-prefixed so it never affects the content hash or schema.
            "_entries": facts,
        }
        return {"target_type": "knowledge-pack", "body": body}

    @staticmethod
    def _conditional(gap: dict, source: dict, payload: dict, rules: list) -> dict:
        """Mine declarative IF→THEN rules into a Conditional (rule-pack)."""
        name = (str(payload.get("name") or gap.get("summary") or "Conditional") + " rules")[:128]
        url = source.get("source_url", "")
        has_pattern = any(isinstance(r, dict) and r.get("pattern") for r in rules)
        family = payload.get("rule_family") or ("grep" if has_pattern else "heuristic")
        _SEV = {"info", "low", "medium", "high", "critical"}
        built: list[dict] = []
        for i, r in enumerate(rules):
            r = r if isinstance(r, dict) else {"condition": str(r)}
            rule = {"id": str(r.get("id") or f"rule-{i + 1}")}
            # map authoring vocab (when/then) onto the schema's condition/action; keep optionals
            for src_key, dst_key in (("when", "condition"), ("condition", "condition"),
                                     ("then", "action"), ("action", "action"),
                                     ("pattern", "pattern"), ("label", "label"), ("category", "category")):
                v = r.get(src_key)
                if v is not None and dst_key not in rule:
                    rule[dst_key] = v
            if r.get("severity") in _SEV:
                rule["severity"] = r["severity"]
            built.append(rule)
        body = {
            "type": "rule-pack",
            "name": name,
            "description": (
                f"{gap.get('summary', 'Conditional rules')} "
                f"Extracted {len(built)} explainable IF→THEN rules from {url or 'the source'} so the check "
                f"runs deterministically before the model — what a bare model applies inconsistently."
            ),
            "family": family,
            "industry": list(payload.get("industry") or []),
            "capability": list(payload.get("rule_capability") or ["verification"]),
            "modality": ["text"],
            "rules": built,
            "provenance": {"sources": [url] if url else []},
            "attribution": {
                "source_url": url,
                "source_kind": normalize_source_kind(source.get("source_kind", "other")),
                "author": source.get("author", ""), "license": source.get("license", ""),
            },
        }
        return {"target_type": "rule-pack", "body": body}


class ConstructionStage(BaseStage):
    """Expand each (gap + source) candidate into typed component drafts."""

    name = "construction"

    def __init__(self, author: Author | None = None) -> None:
        self.author = author or DeterministicAuthor()

    def run(self, batch: list[Candidate], ctx: FoundryContext) -> list[Candidate]:
        out: list[Candidate] = []
        for c in batch:
            if not c.alive:
                continue
            drafts = self.author.build(c.gap or {}, c.source or {}, ctx)
            if not drafts:
                out.append(c.drop(self.name, "no component could be built from this source"))
                continue
            for d in drafts:
                child = Candidate(
                    target_type=d["target_type"],
                    body=dict(d["body"]),
                    gap=dict(c.gap or {}),       # evidence travels with the draft (incl. eval_tasks)
                    source=dict(c.source or {}),
                )
                child.mark(self.name, "built", d["target_type"])
                out.append(child)
        return out


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    gap = {"id": "gap/csddd", "summary": "Bare model misattributes CSDDD articles.",
           "lift_reason": "esoteric_rule", "model_independent_score": 0.8,
           "eval_tasks": [{"prompt": "cite art 8", "correct_answer": "Article 8 CSDDD",
                           "bare_answer": "Article 12", "pipeline_answer": "Article 8 CSDDD"}]}
    source = {"source_url": "https://eur-lex.europa.eu/csddd", "author": "EU", "license": "CC-BY-4.0",
              "source_kind": "regulation",
              "payload": {"name": "CSDDD article corpus", "industry": ["esg", "supply_chain"],
                          "facts": [{"anchor": "Article 8", "text": "Due-diligence obligation."},
                                    {"anchor": "Article 29", "text": "Civil liability."}],
                          "rule_family": "grep",
                          "rules": [{"id": "forced-labor", "when": "text matches an ILO indicator",
                                     "then": "flag for human review", "pattern": "(?i)forced labou?r",
                                     "severity": "high", "label": "ILO forced-labour indicator"}]}}
    parent = Candidate(gap=gap, source=source)
    out = ConstructionStage().run([parent], FoundryContext())
    check("two drafts built (Knowledge Corpus + Conditional)",
          len(out) == 2 and all(c.alive for c in out), str([c.short() for c in out]))
    kp = next((c for c in out if c.target_type == "knowledge-pack"), None)
    rp = next((c for c in out if c.target_type == "rule-pack"), None)
    check("Knowledge Corpus built", kp is not None)
    check("Conditional (rule-pack) built", rp is not None)
    check("content_types present (schema-required)", bool(kp) and kp.body.get("content_types") == ["rag_doc"])
    check("rule-pack has a family (schema-required)", bool(rp) and rp.body.get("family") == "grep")
    check("rule-pack carries the extracted rule", bool(rp) and len(rp.body.get("rules", [])) == 1)
    check("rule mapped when→condition / then→action",
          bool(rp) and rp.body["rules"][0].get("condition") and rp.body["rules"][0].get("action"))
    check("attribution source_kind normalized to enum", kp.body["attribution"]["source_kind"] == "other")
    check("entries carried for Stage 7", len(kp.body.get("_entries", [])) == 2)
    check("gap evidence (eval_tasks) travels with draft", kp.gap.get("eval_tasks"))
    check("source travels with draft", kp.source.get("source_url"))

    # both constructed bodies must pass the REAL schemas once standardized (no shortcut)
    from scripts.foundry.standardize import StandardizeStage
    StandardizeStage(now_s=0).run([kp, rp], FoundryContext())
    check("Knowledge Corpus standardizes + schema-validates", kp.alive and kp.component_id, str(kp.reasons))
    check("Conditional standardizes + schema-validates", rp.alive and rp.component_id, str(rp.reasons))
    check("standardized ids well-formed",
          kp.component_id.startswith("knowledge-pack/") and rp.component_id.startswith("rule-pack/"))

    # a source with no minable payload ⇒ dropped (no fabricated component)
    empty_parent = Candidate(gap={"id": "g0"}, source={"source_url": "https://x/y", "author": "a", "license": "MIT"})
    out2 = ConstructionStage().run([empty_parent], FoundryContext())
    check("unminable source ⇒ dropped", out2 and not out2[0].alive)

    print(f"\n{'all construction self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
