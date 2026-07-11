"""src.teleon.dag.example_pipelines — extraction + enrichment expressed as flexible DAGs over the step library.

These show the point: extraction/enrichment are NOT "OCR -> cheapest model". They route (If), filter, chunk (Loop),
extract per-chunk, merge (fan-in), retrieve/rerank, synthesize, and verify — and the DESCENT picks the cheapest viable
alternative per choice-point that clears the requirement floor. Step fns are deterministic offline stand-ins (a real
deployment swaps in OCR/search/model adapters); the WIRING + the choice economics are the demonstration.
serves_truth=false. Teleon-layer.
"""
from __future__ import annotations

from src.teleon.dag.pipeline_dag import DAG, Node

# ── shared deterministic step fns (offline stand-ins) ────────────────────────────────────────────
def _acquire(bus):           return f"text<<{bus['source'].get('id', 'doc')}>>"
def _normalize(bus):         return bus["text"].lower()
def _chunk(bus):             return [f"chunk{i}:{bus['text']}" for i in range(3)]          # fan-out: 3 passages
def _relevance(bus):         return [p for p in bus["passages"] if "chunk" in p]            # filter (keeps all here)
def _extract_item(bus):      return {f"field_{bus['_item'][:6]}": bus["_item"]}             # per-chunk extract (map)
def _merge_chunks(bus):      return {k: v for d in bus["chunk_fields"] for k, v in d.items()}
def _validate(bus):          return {**bus["fields"], "_validated": True}
def _emit_schema(bus):       return {"schema": bus["schema"], "ok": True}


def build_extraction_dag() -> DAG:
    """document -> defined-schema, as a DAG: route/acquire(choice) -> normalize -> chunk(choice/Loop) -> filter ->
    per-chunk extract(choice) -> merge(fan-in) -> validate -> emit."""
    return DAG((
        # acquire choice-point — cheapest viable wins (text-layer < OCR < enhanced < vision-LLM)
        Node("pdf_text_extract", "text", _acquire, ("source",), 0.002, "Action",
             alt_group="acquire", viable=lambda i: i.get("has_text_layer"), score=0.95),
        Node("ocr", "text", _acquire, ("source",), 0.020, "Action",
             alt_group="acquire", viable=lambda i: i.get("scanned"), score=0.95),
        Node("vision_llm", "text", _acquire, ("source",), 0.300, "Action",
             alt_group="acquire", viable=lambda i: "LLM_API_KEY" in i.get("keys", ()), score=0.99),
        Node("clean_normalize", "text2", _normalize, ("text",), 0.001, "Action"),
        # chunk choice (Loop / fan-out)
        Node("fixed_chunk", "passages", lambda b: _chunk({"text": b["text2"]}), ("text2",), 0.001, "Loop",
             alt_group="chunk", score=0.8),
        Node("semantic_chunk", "passages", lambda b: _chunk({"text": b["text2"]}), ("text2",), 0.010, "Loop",
             alt_group="chunk", score=0.95),
        Node("relevance_filter", "passages2", _relevance, ("passages",), 0.002, "If"),
        # per-chunk extract choice (map_over the passages) — the floor moves the tier
        Node("regex_keyword", "chunk_fields", _extract_item, ("passages2",), 0.001, "Action",
             alt_group="extract", map_over="passages2", score=0.5),
        Node("deterministic_nlp", "chunk_fields", _extract_item, ("passages2",), 0.005, "Action",
             alt_group="extract", map_over="passages2", score=0.7),
        Node("cheap_llm_extract", "chunk_fields", _extract_item, ("passages2",), 0.030, "Action",
             alt_group="extract", map_over="passages2", viable=lambda i: "LLM_API_KEY" in i.get("keys", ()), score=0.85),
        Node("frontier_llm_extract", "chunk_fields", _extract_item, ("passages2",), 0.300, "Action",
             alt_group="extract", map_over="passages2", viable=lambda i: "LLM_API_KEY" in i.get("keys", ()), score=1.0),
        Node("merge_chunks", "fields", _merge_chunks, ("chunk_fields",), 0.001, "Action"),
        Node("schema_validate", "schema", _validate, ("fields",), 0.001, "Action"),
        Node("emit_schema", "output", _emit_schema, ("schema",), 0.0, "Output"),
    ))


# ── enrichment ───────────────────────────────────────────────────────────────────────────────────
def _search(bus):            return [{"url": f"https://src/{i}", "snip": f"fact {i} about {bus['query'][:12]}"} for i in range(4)]
def _dedupe(bus):            return list({s["url"]: s for s in bus["sources"]}.values())
def _rerank(bus):            return sorted(bus["sources2"], key=lambda s: s["url"])[:3]
def _synthesize(bus):        return {"answer": "; ".join(s["snip"] for s in bus["topk"]), "sources": [s["url"] for s in bus["topk"]]}
def _attribute(bus):
    a = bus["answer"]
    grounded = bool(a.get("sources"))
    return {**a, "grounded": grounded, "status": "served" if grounded else "held_out", "serves_truth": False}


def build_enrichment_dag() -> DAG:
    """enrich via search+LLM, as a DAG: search(choice) -> dedupe -> rerank -> synthesize(choice) -> attribute(If)."""
    return DAG((
        Node("web_search_cheap", "sources", _search, ("query",), 0.005, "Knowledge Corpus",
             alt_group="search", score=0.8),
        Node("grounded_search_premium", "sources", _search, ("query",), 0.035, "Knowledge Corpus",
             alt_group="search", score=0.95),
        Node("dedupe_passages", "sources2", _dedupe, ("sources",), 0.002, "Action"),
        Node("rerank", "topk", _rerank, ("sources2",), 0.005, "Action"),
        Node("cheap_synthesize", "answer", _synthesize, ("topk",), 0.001, "Action",
             alt_group="synthesize", viable=lambda i: "LLM_API_KEY" in i.get("keys", ()), score=0.8),
        Node("grounded_synthesize", "answer", _synthesize, ("topk",), 0.030, "Action",
             alt_group="synthesize", score=0.95),
        Node("source_attribution", "final", _attribute, ("answer",), 0.001, "Action"),
        Node("emit_answer", "output", lambda b: b["final"], ("final",), 0.0, "Output"),
    ))


def extraction_inputs(*, has_text_layer=True, scanned=False, keys=("LLM_API_KEY",)) -> dict:
    return {"source": {"id": "agency-licence-001"}, "has_text_layer": has_text_layer, "scanned": scanned, "keys": keys}


def enrichment_inputs(query="What is the registered address of Acme Robotics Inc?", *, keys=("LLM_API_KEY",)) -> dict:
    return {"query": query, "keys": keys}
