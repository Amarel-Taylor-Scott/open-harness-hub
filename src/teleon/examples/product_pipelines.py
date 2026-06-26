"""examples.product_pipelines — example use-cases as runnable, functional PIPELINES, one+ per product surface.

Each product (Teleon, Baltor, OpenHubForAI, AIDevObserver) gets 1-2 example use-cases expressed as a PIPELINE: a
named sequence of REAL existing Teleon functions wired so the output of one step feeds the next. Every pipeline
runs DETERMINISTICALLY + OFFLINE (the DAG descent picks deterministic rungs when no model key is present), or
returns an HONEST needs-key result where a step genuinely needs an LLM/network (never a fabricated answer).
serves_truth=false throughout — a pipeline output is a candidate the verification rail dispositions.

  Teleon        — the runtime/compiler: descend a DAG to the cheapest viable plan (extraction, search-enrichment).
  Baltor        — governs truth: the provider-directory freshness vertical; verified-source answer (needs a key).
  OpenHubForAI  — the open registry ecosystem: compose a capability from the federation; grow + enrich a record.
  AIDevObserver — post-session review of an AI coding transcript (reinvention + waste, human-triaged candidates).

These reuse existing modules (src.teleon.dag / registry / verticals / observer / demos); nothing here is a new
engine. Teleon layer — never imports src.baltor.

  python3 src/teleon/examples/product_pipelines.py --self-test
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[3]   # src/teleon/examples/ -> repo root
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

#: the four product surfaces — the single source of the product list (counts are computed, never typed).
PRODUCTS: tuple[str, ...] = ("Teleon", "Baltor", "OpenHubForAI", "AIDevObserver")


# --- the tiny pipeline model (a linear sequence of real-function steps over a shared state) --------------------------
@dataclass(frozen=True)
class Step:
    """One pipeline step: ``fn(state) -> dict`` returns the artifacts it adds to the shared state. ``calls`` records
    WHICH real existing function it invokes (provenance, so a reader can trace the wiring back to the source)."""
    name: str
    calls: str
    fn: Callable


@dataclass(frozen=True)
class Pipeline:
    """An example use-case: a named, ordered sequence of real-function Steps belonging to one product. ``run`` threads
    a shared state through the steps (each merges its output in) and returns a receipt + the final ``output``."""
    name: str
    product: str
    use_case: str
    steps: tuple
    make_inputs: Callable

    def step_names(self) -> list[str]:
        return [s.name for s in self.steps]

    def run(self, inputs: dict | None = None) -> dict:
        """Execute the steps in order over a shared state (offline + deterministic, or honest-unavailable). Returns a
        receipt: the step path, what each step produced, whether the run was available, and the final output."""
        state = dict(self.make_inputs() if inputs is None else inputs)
        trace: list[dict] = []
        for step in self.steps:
            update = step.fn(state) or {}
            state.update(update)
            trace.append({"step": step.name, "calls": step.calls, "produced": sorted(update)})
        return {
            "pipeline": self.name, "product": self.product, "use_case": self.use_case,
            "steps": self.step_names(), "trace": trace,
            "available": bool(state.get("available", True)),
            "output": state.get("output"), "serves_truth": False,
        }


# ====================================================================================================================
# Teleon — the runtime/compiler: descend a DAG to the cheapest viable plan.
# ====================================================================================================================
def teleon_extract_pipeline() -> Pipeline:
    """Teleon use-case: turn a born-digital document into a defined schema for the cheapest viable cost. With no model
    key the make-it-work->make-it-cheap DESCENT stays on deterministic rungs (text-layer, fixed-chunk, regex extract)."""
    from src.teleon.dag.example_pipelines import build_extraction_dag, extraction_inputs

    def s_build(state):
        return {"dag": build_extraction_dag()}

    def s_inputs(state):
        # born-digital, NO LLM key -> the descent cannot pick a model rung; it must stay deterministic.
        return {"dag_inputs": extraction_inputs(has_text_layer=True, scanned=False, keys=())}

    def s_descend(state):
        result = state["dag"].run(state["dag_inputs"])
        return {"output": {
            "path": result["path"],
            "chosen_alternatives": result["chosen_alternatives"],
            "total_cost": result["total_cost"],
            "schema": result["bus"].get("output"),
            "serves_truth": result["serves_truth"],
        }}

    return Pipeline(
        name="extract-document-to-schema", product="Teleon",
        use_case="Compile a document->schema extraction and descend to the cheapest viable plan; with no model key "
                 "the descent proves the work runs on deterministic rungs alone.",
        steps=(
            Step("build_extraction_dag", "dag.example_pipelines.build_extraction_dag", s_build),
            Step("prepare_inputs", "dag.example_pipelines.extraction_inputs(keys=())", s_inputs),
            Step("descend_and_run", "dag.pipeline_dag.DAG.run", s_descend),
        ),
        make_inputs=lambda: {"profile": "born-digital pdf, no model key"},
    )


def teleon_enrich_pipeline() -> Pipeline:
    """Teleon use-case: answer-by-enrichment (search -> dedupe -> rerank -> synthesize -> attribute) as a DAG descent.
    With no model key the descent picks cheap search + the keyless grounded-synthesize rung. Output is grounded + cited."""
    from src.teleon.dag.example_pipelines import build_enrichment_dag, enrichment_inputs

    def s_build(state):
        return {"dag": build_enrichment_dag()}

    def s_inputs(state):
        return {"dag_inputs": enrichment_inputs(state["query"], keys=())}

    def s_descend(state):
        result = state["dag"].run(state["dag_inputs"])
        return {"output": {
            "path": result["path"],
            "chosen_alternatives": result["chosen_alternatives"],
            "total_cost": result["total_cost"],
            "answer": result["bus"].get("output"),
            "serves_truth": result["serves_truth"],
        }}

    return Pipeline(
        name="enrich-answer-from-search", product="Teleon",
        use_case="Compile a grounded-answer enrichment (search+synthesize) and descend to the cheapest viable plan; "
                 "the answer carries its sources and an honest grounded/held-out status.",
        steps=(
            Step("build_enrichment_dag", "dag.example_pipelines.build_enrichment_dag", s_build),
            Step("prepare_inputs", "dag.example_pipelines.enrichment_inputs(keys=())", s_inputs),
            Step("descend_and_run", "dag.pipeline_dag.DAG.run", s_descend),
        ),
        make_inputs=lambda: {"query": "What is the registered address of Acme Robotics Inc?"},
    )


# ====================================================================================================================
# Baltor — governs truth: the provider-directory freshness vertical (healthcare-admin, NOT insurance).
# ====================================================================================================================
def baltor_provider_directory_pipeline() -> Pipeline:
    """Baltor use-case: keep a provider directory FRESH cheaply + safely. Deterministic rungs resolve the bulk at ~$0
    (NPI Luhn check, field normalization, cross-source agreement), an LLM would touch only the ambiguous residual, and
    every proposed change is a governed candidate routed to auto_update / human_review by confidence. serves_truth=false."""
    from src.teleon.verticals.provider_directory import validate_npi, resolve_record, cost_per_1000

    def s_validate(state):
        return {"npi_valid": validate_npi(state["record"]["npi"])}

    def s_resolve(state):
        return {"resolution": resolve_record(state["record"], state["source_observations"])}

    def s_cost(state):
        res = state["resolution"]
        # the descent's cost depends on how much escalates to a human (auto_update needs none).
        manual_fraction = 0.0 if res["recommended_action"] == "auto_update" else 1.0
        return {"output": {
            "npi_valid": state["npi_valid"],
            "recommended_action": res["recommended_action"],
            "reason": res["reason"],
            "changes": res["changes"],
            "overall_confidence": res["overall_confidence"],
            "cost_per_1000": cost_per_1000(manual_fraction=manual_fraction),
            "serves_truth": res["serves_truth"],
        }}

    def _inputs():
        base9 = "123456789"   # a deterministic, VALID synthetic NPI (the Luhn check digit is searched, not hard-typed).
        npi = next(base9 + str(d) for d in range(10) if validate_npi(base9 + str(d)))
        return {
            "record": {
                "provider_id": "P-1001", "npi": npi, "provider_name": "Dr. Jane Smith",
                "specialty": "Cardiology", "practice_name": "Bay Cardiology Group",
                "address": "100 Market Street Suite 200", "phone": "415-555-0001",
                "website": "https://baycardio.example", "status": "active",
            },
            # two authoritative sources agree on a NEW phone (in different formats that normalize to one value).
            "source_observations": {
                "NPI Registry": {"phone": "(415) 555-9999", "specialty": "Cardiology"},
                "State Medical Board": {"phone": "415.555.9999", "specialty": "Cardiology"},
            },
        }

    return Pipeline(
        name="provider-directory-freshness", product="Baltor",
        use_case="Refresh a provider directory record against cross-source observations: validate the NPI, resolve the "
                 "winning value by weighted agreement, route the change by confidence, and price the descent vs naive.",
        steps=(
            Step("validate_npi", "verticals.provider_directory.validate_npi", s_validate),
            Step("resolve_record", "verticals.provider_directory.resolve_record", s_resolve),
            Step("cost_model", "verticals.provider_directory.cost_per_1000", s_cost),
        ),
        make_inputs=_inputs,
    )


def baltor_verified_source_answer_pipeline() -> Pipeline:
    """Baltor use-case (HONEST-UNAVAILABLE): answer ONLY from a verified source (cite it, or say MISSING). This genuinely
    needs the user's model key, so offline it returns an honest needs-key result through the BYO-key demo plane — never a
    fabricated answer. This is the correct 'honest-unavailable' shape required of a step that needs an LLM."""
    from src.teleon.demos.byo_key_demo import run_byo_demo

    def s_demo(state):
        res = run_byo_demo("baltor", byo_key=None, inputs=state.get("inputs"))   # no key -> honest needs_key
        return {"output": res, "available": bool(res.get("ok"))}

    return Pipeline(
        name="answer-only-from-verified-source", product="Baltor",
        use_case="Answer a question strictly from a provided source (cite or MISSING). Needs the user's model key — "
                 "returns an honest needs-key result offline instead of fabricating.",
        steps=(Step("run_byo_demo(baltor)", "demos.byo_key_demo.run_byo_demo", s_demo),),
        make_inputs=lambda: {"inputs": {}},
    )


# ====================================================================================================================
# OpenHubForAI — the open registry ecosystem: compose a capability from the federation; grow + enrich a record.
# ====================================================================================================================
def openhubs_compose_pipeline() -> Pipeline:
    """OpenHubForAI use-case: turn an intent into a candidate tool. Federated-search EVERY open registry for the intent,
    then compile the hits into a candidate DAG plan across the registries. This is how the open component ecosystem
    becomes a runnable tool. The result is a CANDIDATE plan (the verify gate runs before anything executes)."""
    from src.teleon.registry.search import build_capability
    from src.teleon.registry.compose import compile_universal

    def s_search(state):
        return {"ingredients": build_capability(state["intent"])}

    def s_compose(state):
        ing = state["ingredients"]["ingredients_by_registry"]
        plan = compile_universal(state["intent"])
        return {"output": {
            "registries_hit": len(ing),
            "ingredients_by_registry": {k: ing[k] for k in sorted(ing)[:5]},   # a readable head of the federated hits
            "candidate_dag": plan,
            "serves_truth": plan["serves_truth"],
        }}

    return Pipeline(
        name="compose-capability-from-registries", product="OpenHubForAI",
        use_case="Federated-search the open registries for an intent and compile the hits into a candidate DAG plan — "
                 "how the open component ecosystem becomes a runnable tool.",
        steps=(
            Step("federated_search", "registry.search.build_capability", s_search),
            Step("compile_candidate_dag", "registry.compose.compile_universal", s_compose),
        ),
        make_inputs=lambda: {"intent": "extract address and phone from a scanned document"},
    )


def openhubs_populate_enrich_pipeline() -> Pipeline:
    """OpenHubForAI use-case: grow the registry. Turn a discovered repo slug into a governed candidate component RECORD,
    then ENRICH it (deterministic embedding + keywords + labels + use-cases) so it is searchable on the buffet. Offline +
    deterministic; discovery != trust (the record is a candidate, license-checked before adoption). serves_truth=false."""
    from src.teleon.registry.populate import repo_to_record
    from src.teleon.registry.enrich import enrich_record

    def s_record(state):
        return {"record": repo_to_record(state["slug"], source="examples", desc=state["desc"])}

    def s_enrich(state):
        enriched = enrich_record(state["record"])
        enr = enriched["_enrichment"]
        return {"output": {
            "id": enriched["id"],
            "candidate": enriched["candidate"],
            "description": enr["description"],
            "keywords": enr["keywords"],
            "labels": enr["labels"],
            "embedding_dim": enr["embedding_dim"],
            "use_cases": enr["use_cases"],
            "serves_truth": enriched["serves_truth"],
        }}

    return Pipeline(
        name="populate-and-enrich-component", product="OpenHubForAI",
        use_case="Turn a discovered repo slug into a governed, enriched candidate registry record (embedding, keywords, "
                 "labels, use-cases) — how a registry grows records offline.",
        steps=(
            Step("repo_to_record", "registry.populate.repo_to_record", s_record),
            Step("enrich_record", "registry.enrich.enrich_record", s_enrich),
        ),
        make_inputs=lambda: {"slug": "open-source/ocr-toolkit", "desc": "OCR and document text extraction toolkit"},
    )


# ====================================================================================================================
# AIDevObserver — post-session review of an AI coding transcript (reinvention + waste, human-triaged candidates).
# ====================================================================================================================
def observer_session_review_pipeline() -> Pipeline:
    """AIDevObserver use-case: review a finished AI coding session. Run the full typed-module taxonomy over the
    transcript (reinvention grounded in the federation + waste signals) and surface the highest-confidence finding.
    Zero live interruptions; every finding is a governed candidate a human triages (discovery != trust)."""
    from src.teleon.observer.review import review_session

    def s_review(state):
        return {"report": review_session(state["messages"])}

    def s_top(state):
        rep = state["report"]
        # review_session already ranks the report by confidence (desc); the top finding is the head.
        top = rep["report"][0] if rep["report"] else None
        return {"output": {
            "messages_reviewed": rep["summary"]["messages_reviewed"],
            "findings": rep["summary"]["findings"],
            "reinventions": rep["summary"]["reinventions"],
            "waste_signals": rep["summary"]["waste_signals"],
            "by_type": rep["summary"]["by_type"],
            "top_finding": None if top is None else {
                "type": top["type"], "confidence": top["confidence"], "suggestion": top["suggestion"],
            },
            "serves_truth": rep["serves_truth"],
        }}

    sample = [
        {"role": "user", "content": "let me write a pdf parser from scratch"},          # reinvention (grounded)
        {"role": "user", "content": "I'll implement my own address validation"},          # reinvention (grounded)
        {"role": "assistant", "content": "ok, genuinely novel research with no solved domain"},  # stays quiet
    ]
    return Pipeline(
        name="review-ai-coding-session", product="AIDevObserver",
        use_case="Review a finished AI coding transcript for reinvention + waste and surface the top human-triaged "
                 "candidate finding, with zero live interruptions.",
        steps=(
            Step("review_session", "observer.review.review_session", s_review),
            Step("select_top_finding", "report[0] (review_session pre-ranks by confidence)", s_top),
        ),
        make_inputs=lambda: {"messages": [dict(m) for m in sample]},
    )


# --- registry of all example pipelines ------------------------------------------------------------------------------
def all_pipelines() -> list:
    """Every example pipeline (1-2 per product). The single source of the example set."""
    return [
        teleon_extract_pipeline(),
        teleon_enrich_pipeline(),
        baltor_provider_directory_pipeline(),
        baltor_verified_source_answer_pipeline(),
        openhubs_compose_pipeline(),
        openhubs_populate_enrich_pipeline(),
        observer_session_review_pipeline(),
    ]


def pipelines_for(product: str) -> list:
    """The example pipelines belonging to one product surface."""
    return [p for p in all_pipelines() if p.product == product]


def run_all() -> dict:
    """Run every example pipeline -> {pipeline_name: receipt}. Deterministic + offline."""
    return {p.name: p.run() for p in all_pipelines()}


# --- proof ----------------------------------------------------------------------------------------------------------
def self_test() -> int:
    pipes = all_pipelines()
    by_product: dict[str, list] = {}
    for p in pipes:
        by_product.setdefault(p.product, []).append(p)

    # 1) every product surface has at least one example pipeline.
    for prod in PRODUCTS:
        assert by_product.get(prod), f"product {prod!r} has no example pipeline"

    # 2) every pipeline runs, produces output, is serves_truth=false, and is DETERMINISTIC (same input -> same result).
    first = {p.name: p.run() for p in pipes}
    second = {p.name: p.run() for p in pipes}
    for p in pipes:
        r = first[p.name]
        assert r["serves_truth"] is False, f"{p.name} must be serves_truth=false"
        assert r["output"] is not None, f"{p.name} produced no output"
        assert r["steps"] and len(r["trace"]) == len(r["steps"]), f"{p.name} step/trace mismatch"
        assert second[p.name] == r, f"{p.name} is not deterministic"

    # 3) REQUIRED: every product has >=1 RUNNABLE example pipeline that produces output (available + non-empty output).
    for prod in PRODUCTS:
        ok = any(first[p.name]["available"] and first[p.name]["output"] for p in by_product[prod])
        assert ok, f"product {prod!r} has no runnable example pipeline that produces output"

    # 4) spot-check the load-bearing output of each product's deterministic flagship.
    tex = first["extract-document-to-schema"]["output"]
    assert tex["schema"] and tex["total_cost"] >= 0.0, "Teleon extraction must yield a schema + a cost"
    assert "llm" not in str(tex["chosen_alternatives"]).lower(), "no-key descent must stay on deterministic rungs"

    ten = first["enrich-answer-from-search"]["output"]
    assert ten["answer"] and ten["answer"].get("sources"), "Teleon enrichment must yield a grounded answer with sources"

    bd = first["provider-directory-freshness"]["output"]
    assert bd["npi_valid"] is True, "Baltor freshness must validate the synthetic NPI"
    assert bd["recommended_action"] in {"auto_update", "human_review", "no_change"}, bd["recommended_action"]
    assert bd["cost_per_1000"]["serves_truth"] is False

    oh = first["compose-capability-from-registries"]["output"]
    assert oh["registries_hit"] >= 1 and oh["candidate_dag"]["serves_truth"] is False, oh

    oe = first["populate-and-enrich-component"]["output"]
    assert oe["candidate"] is True and oe["keywords"] and oe["embedding_dim"] >= 1, oe

    ob = first["review-ai-coding-session"]["output"]
    assert ob["findings"] >= 1 and ob["reinventions"] >= 1 and ob["top_finding"], ob

    # 5) the HONEST-UNAVAILABLE Baltor pipeline returns an honest needs-key result, NOT a fabricated answer.
    bu = first["answer-only-from-verified-source"]
    assert bu["available"] is False and bu["output"]["status"] == "needs_key", bu["output"]

    print(f"product_pipelines self-test: OK ({len(pipes)} runnable example pipelines across {len(PRODUCTS)} products "
          f"[{', '.join(PRODUCTS)}]; deterministic + offline; honest-unavailable where an LLM/key is needed; "
          f"serves_truth=false)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    for p in all_pipelines():
        r = p.run()
        status = "ok" if r["available"] else "honest-unavailable"
        print(f"[{p.product}] {p.name}: {status} — {' -> '.join(r['steps'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
