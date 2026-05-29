"""Assembly: retrieve → orchestrate → cost → narrate → build_flow.

Stage labels / per-component labels are DERIVED from the seven primitives
(scripts/primitives/) via STAGE_ORDER / stage_for_type / label_for_type — single
source, no magic-string dicts. Only the per-stage assembly caps live here.
"""
from __future__ import annotations

import json
import re

from scripts.embeddings import describe_backend
from scripts.model_routes import resolve_route
from scripts.primitives import STAGE_ORDER, Conditional, label_for_type, stage_for_type
from scripts.showcase.index import Index

# Per-stage assembly caps (functional config, keyed by schema type).
STAGE_CAPS = {"persona": 1, "knowledge-pack": 2, "logic-pack": 1, "rule-pack": 2,
              "tool": 2, "processor": 1, "pattern": 1, "harness": 1, "adapter": 1,
              "pipeline": 1, "rubric": 1, "benchmark": 1, "dataset": 1}
RELEVANCE_FLOOR = 0.18  # below this a candidate is off-topic noise — drop it
_FLOW_CACHE: dict[str, dict] = {}  # task -> result; the two LLM calls are the slow part


def _coherent_select(candidates: list[dict]) -> list[dict]:
    """Deterministic fallback: relevance floor + per-type caps, ordered by stage."""
    kept_by_type: dict[str, list[dict]] = {}
    for c in sorted(candidates, key=lambda r: r["score"], reverse=True):
        if c["score"] < RELEVANCE_FLOOR:
            continue
        bucket = kept_by_type.setdefault(c["type"], [])
        if len(bucket) < STAGE_CAPS.get(c["type"], 1):
            bucket.append(c)
    flat = [c for t in STAGE_CAPS for c in kept_by_type.get(t, [])]
    return [{**c, "stage": stage_for_type(c["type"]), "role": label_for_type(c["type"])} for c in flat]


def _parse_keep(raw: str) -> list[str]:
    """Tolerant: extract kept ids even if a verbose/reasoning model truncated the
    JSON mid-array (the cause of the silent orchestration collapse)."""
    if not raw:
        return []
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            ids = [str(x) for x in (json.loads(m.group(0)).get("keep") or []) if isinstance(x, str)]
            if ids:
                return ids
    except Exception:
        pass
    km = re.search(r'"keep"\s*:\s*\[(.*?)(?:\]|$)', raw, re.DOTALL)
    return re.findall(r'"([a-z0-9-]+/[a-z0-9-]+)"', km.group(1) if km else raw)


def orchestrate(task: str, candidates: list[dict], route) -> tuple[list[dict], list[dict], bool]:
    """Pick the coherent, on-topic subset. An LLM prunes off-domain candidates;
    falls back to deterministic selection. Returns (kept, dropped, used_llm)."""
    floored = [c for c in candidates if c["score"] >= RELEVANCE_FLOOR]
    deterministic = _coherent_select(candidates)

    def _det_result():
        kept_ids = {c["id"] for c in deterministic}
        dropped = [{"id": c["id"], "name": c["name"], "type": c["type"]}
                   for c in candidates if c["id"] not in kept_ids][:8]
        return deterministic, dropped, False

    if not floored or not route.health():
        return _det_result()

    listing = "\n".join(f"- {c['id']} [{c['type']}] {c['name']}" for c in floored)
    system = (
        "You are the Open Harness Hub orchestrator. From the CANDIDATES, keep ONLY components "
        "genuinely relevant to the user's task and DROP off-domain ones (wrong industry, modality, "
        "or purpose). Build ONE coherent pipeline: at most one persona, one model harness, one "
        "backbone pipeline, 1-2 knowledge corpora, 1-2 if-statements, 1-2 actions, one rubric. "
        "Return ONLY compact JSON with a SINGLE key and NO explanations: "
        "{\"keep\":[\"id\",\"id\",...]}. Do not include a 'drop' list or any prose. "
        "Use only ids from the list."
    )
    keep_ids = _parse_keep(route.complete(system, f"Task: {task}\n\nCANDIDATES:\n{listing}", max_tokens=2048) or "")
    if not keep_ids:
        return _det_result()

    by_id = {c["id"]: c for c in candidates}
    chosen, counts = [], {}
    for cid in keep_ids:
        c = by_id.get(cid)
        if not c or counts.get(c["type"], 0) >= STAGE_CAPS.get(c["type"], 1):
            continue
        counts[c["type"]] = counts.get(c["type"], 0) + 1
        chosen.append({**c, "stage": stage_for_type(c["type"]), "role": label_for_type(c["type"])})
    if not chosen:
        return _det_result()
    chosen.sort(key=lambda c: STAGE_ORDER.index(c["stage"]) if c["stage"] in STAGE_ORDER else 99)
    kept_ids = {c["id"] for c in chosen}
    dropped = [{"id": c["id"], "name": c["name"], "type": c["type"]}
               for c in floored if c["id"] not in kept_ids][:8]
    return chosen, dropped, True


# --- Input/Output inference + node typing (so the diagram models the RUNTIME
# flow — the recruitment ad / pay statement it consumes — not the build query) -
_INPUT_CUES = [
    r"\btriage\s+([\w'’/+%-]+(?:\s+[\w'’/+%-]+){0,3})",
    r"\b(?:screen|classify|validate|analy[sz]e|review|parse|read|extract)\s+(?:a|an|the)?\s*([\w'’/+%-]+(?:\s+[\w'’/+%-]+){0,3})",
    r"\bin\s+(?:a|an|the)\s+([\w'’/+%-]+(?:\s+[\w'’/+%-]+){0,3})",
    r"\bfrom\s+(?:a|an|the)?\s*([\w'’/+%-]+(?:\s+[\w'’/+%-]+){0,3})",
    r"\bif\s+(?:a|an|the)\s+([\w'’/+%-]+(?:\s+[\w'’/+%-]+){0,3})",
]
_INPUT_STOP = {"and", "or", "to", "for", "with", "under", "against", "that", "which", "into", "by",
               "is", "are", "be", "then", "so", "using", "via", "on", "at", "of", "from", "in",
               "a", "an", "the", "its", "it"}
_LEAF_KEYWORDS = ("escalate", "human-review", "human_review", "review-queue", "review_queue",
                  "notify", "alert", "audit", "handoff", "page-on-call", "log-")


def infer_input(task: str) -> dict:
    """The artifact the assembled pipeline CONSUMES at runtime (the recruitment
    ad / pay statement / variant string), not the plain-language task itself."""
    low = task.lower()
    artifact = ""
    for pat in _INPUT_CUES:
        m = re.search(pat, low)
        if not m:
            continue
        s, e = m.span(1)
        out: list[str] = []
        for w in task[s:e].split():
            if w.lower().strip(".,:;") in _INPUT_STOP:
                break
            out.append(w)
        cand = " ".join(out).strip(" -.,:;")
        if len(cand) >= 3:
            artifact = cand
            break
    if not artifact:
        return {"id": "input-text", "type": "input", "name": "Input text",
                "role": "the text/document the pipeline runs on", "branch": "main", "subtype": "Input"}
    a = artifact.lower()
    itype = ("string" if "string" in a else
             "record" if any(k in a for k in ("entity", "record", "variant", "cve", "ownership")) else
             "image" if any(k in a for k in ("image", "photo", "scan", "x-ray", "xray")) else
             "document" if any(k in a for k in ("ad", "statement", "contract", "document", "report",
                                                "post", "letter", "disclosure", "circular", "form", "permit")) else
             "text")
    name = artifact if artifact[:1].isupper() else artifact[:1].upper() + artifact[1:]
    return {"id": "input-" + (re.sub(r"[^a-z0-9]+", "-", a).strip("-")[:40] or "text"),
            "type": "input", "name": name,
            "role": f"input {itype} — what the pipeline runs on at runtime",
            "branch": "main", "subtype": f"Input · {itype}"}


def _is_leaf(c: dict) -> bool:
    """Side-effect actions (escalation, review queue, notify, log) are leaves OFF
    the critical path, not inline transforms."""
    blob = (c.get("id", "") + " " + c.get("name", "")).lower()
    return any(k in blob for k in _LEAF_KEYWORDS)


def _subtype(c: dict) -> str:
    """Precise primitive subtype for the diagram (so escalation is not mislabeled
    a generic 'Transform')."""
    t, blob = c["type"], (c.get("id", "") + " " + c.get("name", "")).lower()
    if t == "persona":
        return "Add Persona"
    if t in ("rule-pack", "logic-pack"):
        return ("Classifier" if "classifier" in blob else
                "GREP / regex" if ("grep" in blob or "regex" in blob) else "Condition")
    if t in ("knowledge-pack", "dataset"):
        return "Dataset" if t == "dataset" else "Knowledge Corpus"
    if t == "pipeline":
        return "Sub-pipeline"
    if t == "pattern":
        return ("Routing" if "rout" in blob else "Parallel" if "parallel" in blob
                else "Loop" if "loop" in blob else "Flow")
    if t in ("harness", "adapter"):
        return "Model harness"
    if t == "rubric":
        return "Evaluate · rubric"
    if t == "benchmark":
        return "Evaluate · benchmark"
    if t == "processor":
        if any(k in blob for k in ("escalate", "human-review", "human_review", "handoff")):
            return "Escalate → human"
        if any(k in blob for k in ("webhook", "post", "request", "http", "api", "emit", "publish")):
            return "Execute / Webhook"
        if any(k in blob for k in ("notify", "alert", "email", "sms")):
            return "Notify"
        if any(k in blob for k in ("log", "audit")):
            return "Log / Audit"
        return "Transform"
    return label_for_type(t)


def _output_name(task: str) -> str:
    """The runtime OUTPUT, shaped by task type — a detection task answers yes/no, an
    extraction task returns fields, a grading task a score (each with cited indicators)."""
    low = task.lower()
    if any(k in low for k in ("detect", "indicator", "exploitation", "trafficking", "abuse",
                              "fraud", "violation", "is there", "whether")):
        return "Decision: yes / no + cited indicators"
    if any(k in low for k in ("flag", "screen", "risk of")):
        return "Decision: flag / clear + cited indicators"
    if "rout" in low or "hotline" in low:
        return "Routed decision + citations"
    if "classif" in low or "map it" in low or "tier" in low:
        return "Classification + citations"
    if any(k in low for k in ("extract", "line item", "read ", "parse", "into a", "csv", "fields")):
        return "Extracted fields (JSON) + citations"
    if any(k in low for k in ("grad", "score", "rubric", "rate ")):
        return "Score + rationale + citations"
    if "valid" in low or "verif" in low or "reconcile" in low:
        return "Validation result (pass / fail) + reasons"
    return "Findings (JSON) + citations"


def harness_recipe(task: str, kept: list[dict]) -> list[dict]:
    """The anatomy of ONE governed model call — the ordered THEN steps that run once the
    triage gate routes an input in. Real catalog components are SLOTTED where they exist
    (persona, regex/GREP rule-pack, RAG corpus, tools, the right-sized harness, the rubric);
    the remaining steps are deterministic built-ins (compress, injection-check, JSON
    verify/recover, retry loop). This is what makes the lift governed + cheap, not a single
    raw model call. Order mirrors the canonical detect/extract/grade harness."""
    by_type: dict[str, list[dict]] = {}
    for c in kept:
        by_type.setdefault(c["type"], []).append(c)

    def first(*types):
        for t in types:
            if by_type.get(t):
                return by_type[t][0]
        return None

    persona = first("persona")
    regex = first("rule-pack", "logic-pack")
    corpus = first("knowledge-pack", "dataset")
    tool = first("tool")
    harness = first("harness", "adapter", "pipeline")
    rubric = first("rubric", "benchmark")
    loop = first("pattern")

    def step(phase: str, tier: str, k: str, name: str, role: str, comp: dict | None = None) -> dict:
        # phase: pre | call | post ; tier: always | default | optional
        d = {"phase": phase, "tier": tier, "k": k, "name": name, "role": role, "builtin": comp is None}
        if comp:
            d["ref"] = f"{comp['type']}/{comp['id'].split('/')[-1]}"
        return d

    # Composition law (the owner's rule): an Input, a model Call, and the pre-/post-call phases
    # are ALWAYS present (even when a step is a no-op). The trigger gate, persona, regex/corpus
    # context, RAG retrieval and token reduction are DEFAULTS — on every pipeline unless there is a
    # serious reason to drop one. Real catalog components are slotted where they exist; the rest are
    # deterministic built-ins. This is what makes the lift governed + cheap, not a raw model call.
    recipe = [
        step("pre", "default", "conditional", "Trigger gate — does the input qualify?",
             "cheap check that the input meets the conditions for the full harness; else short-circuit", regex),
        step("pre", "default", "action", "Add persona / system prompt",
             "frame the model as the right domain expert", persona),
        step("pre", "default", "conditional", "Add context — regex / knowledge corpus",
             "deterministic pattern extraction + exact-match facts", regex),
        step("pre", "default", "knowledge", "Add context — RAG retrieval",
             "retrieve cited facts from the governed corpus", corpus),
    ]
    if tool:
        recipe.append(step("pre", "optional", "action", "Call tools",
                           "structured tool calls for steps the model shouldn't guess", tool))
    recipe += [
        step("pre", "optional", "action", "Check online facts / search",
             "verify volatile facts against a live source"),
        step("pre", "default", "action", "Token reduction — format · prioritize · compress",
             "salient evidence first; compress to cut tokens & cost"),
        step("pre", "default", "stop", "Prompt-injection check",
             "block if the input tries to extract or override the system prompt"),
        step("call", "always", "action", "Call the right-sized model",
             "smallest model that clears the bar, with the assembled system prompt", harness),
        step("post", "always", "conditional", "Check output",
             "validate against the expected answer shape"),
        step("post", "default", "conditional", "Verify JSON (recover if malformed)",
             "parse; if non-JSON, repair / reformat once"),
        step("post", "default", "conditional", "Re-verify",
             "second pass on the recovered output", rubric),
        step("post", "always", "loop", "If not OK → retry with changes (≤3)",
             "re-run with targeted fixes until it passes, else escalate", loop),
    ]
    return recipe


def flowchart(task: str, kept: list[dict]) -> list[dict]:
    """Ordered stages Input → … → Output, each node tagged with a precise subtype
    and main/leaf branch, and grouped Conditions joined by an explicit Logical
    Operator node (default OR) that gates the downstream action."""
    chart = [{"stage": "Input", "components": [infer_input(task)]}]
    for stage in STAGE_ORDER:
        comps = [{"id": c["id"], "type": c["type"], "name": c["name"], "role": c["role"],
                  "subtype": _subtype(c), "branch": "leaf" if _is_leaf(c) else "main"}
                 for c in kept if c.get("stage") == stage]
        if not comps:
            continue
        band: dict = {"stage": stage, "components": comps}
        if stage == Conditional.stage and sum(1 for x in comps if x["branch"] == "main") >= 2:
            # 2+ conditions are joined by an explicit Logical Operator node (a distinct
            # Conditional subtype), default OR — if ANY matches, the THEN action runs.
            band["operator"] = {"type": "operator", "op": "OR", "name": "OR",
                                "subtype": "Logical Operator", "branch": "operator",
                                "role": "if ANY condition matches, run the next action"}
        chart.append(band)
    chart.append({"stage": "Output", "components": [
        {"id": "result", "type": "output", "name": _output_name(task),
         "role": "decision (binary / number / string) + metadata + the full runtime object (replayable trace)",
         "subtype": "Output", "branch": "main"}]})
    return chart


def estimate_cost(kept: list[dict]) -> dict:
    n_model = sum(1 for s in kept if s["type"] in {"harness", "pipeline", "adapter"})
    n_rules = sum(1 for s in kept if s["type"] in {"rule-pack", "processor"})
    return {
        "cheap":    {"per_task_usd": "0.00–0.02", "how": f"local model + {n_rules} deterministic gate(s) first; model only on the residual"},
        "balanced": {"per_task_usd": "0.01–0.10", "how": f"small hosted model for {max(1, n_model)} model step(s); rules/retrieval pre-filter"},
        "quality":  {"per_task_usd": "0.10–0.60", "how": "frontier model on the final step; full retrieval + review gate"},
        "note": "Illustrative; calibrate against real runs. Rules/retrieval before the model is the main lever.",
    }


def deterministic_narrative(task: str, kept: list[dict], cost: dict) -> str:
    parts = [f"Composed a coherent flow of {len(kept)} components:"]
    for s in kept:
        parts.append(f" • [{s.get('stage', '')}] {s['type']}/{s['id'].split('/')[-1]} — {s['role']}.")
    parts.append("Deterministic rules and retrieval run before the model to cut cost; swap the "
                 f"model via the harness/adapter. Estimated ~{cost['balanced']['per_task_usd']}/task "
                 "(balanced). Refine: \"cheaper\" (local model + more rules-first) or "
                 "\"stricter\" (review gate + tighter rubric).")
    return "\n".join(parts)


def llm_narrative(task: str, kept: list[dict], cost: dict) -> tuple[str, bool]:
    route = resolve_route()
    if not route.health() or not kept:
        return deterministic_narrative(task, kept, cost), False
    comp_lines = "\n".join(f"- [{s.get('stage', '')}] {s['type']}/{s['id'].split('/')[-1]}: {s['role']}" for s in kept)
    system = ("You are the Open Harness Hub builder. In 4-6 sentences, explain the assembled "
              "pipeline of these EXISTING components for the task: the flow from input through "
              "persona, retrieval, deterministic rules, tools, the model harness, to evaluation; "
              "why rules/retrieval run before the model to cut cost; and how to swap the model. "
              "Then two one-line refinements (cheaper / stricter). Mention ONLY the listed components.")
    user = f"Task: {task}\n\nFlow (in order):\n{comp_lines}\n\nBalanced cost ~{cost['balanced']['per_task_usd']}/task."
    text = route.complete(system, user, max_tokens=2048)
    return (text.strip(), True) if text and text.strip() else (deterministic_narrative(task, kept, cost), False)


def _stratified_pool(index: Index, task: str) -> list[dict]:
    """Candidate pool that GUARANTEES per-type representation, so a flood of
    near-duplicate top scorers can't starve whole stages."""
    flat = index.search(task, k=60)
    by_type: dict[str, list[dict]] = {}
    for c in flat:
        by_type.setdefault(c["type"], []).append(c)
    pool, seen = [], set()
    for c in flat[:18]:                       # strongest overall
        if c["id"] not in seen:
            pool.append(c); seen.add(c["id"])
    for cs in by_type.values():               # + top-3 of EVERY type
        for c in cs[:3]:
            if c["id"] not in seen:
                pool.append(c); seen.add(c["id"])
    return pool


def analyze_match(kept: list[dict], pool: list[dict]) -> dict:
    """Detect UNDER-match (a needed component available but unselected) and
    OVER-match (a type exceeds its cap). Checked by TYPE so it is robust to
    stage label changes."""
    kept_types = {c["type"] for c in kept}
    pool_types = {c["type"] for c in pool}
    under = []
    if not (kept_types & {"harness", "pipeline"}) and ({"harness", "pipeline"} & pool_types):
        under.append("Model boundary — a harness/pipeline was available but not selected")
    if not (kept_types & {"rubric", "benchmark"}) and ({"rubric", "benchmark"} & pool_types):
        under.append("Evaluate — a rubric/benchmark was available but not selected")
    if "knowledge-pack" not in kept_types and "knowledge-pack" in pool_types:
        under.append("Knowledge Corpus — a corpus was available but not selected")
    counts: dict[str, int] = {}
    for c in kept:
        counts[c["type"]] = counts.get(c["type"], 0) + 1
    over = [f"{t} ×{n}" for t, n in counts.items() if n > STAGE_CAPS.get(t, 1)]
    return {"undermatched": under, "overmatched": over,
            "stage_coverage": sorted({c["stage"] for c in kept})}


def build_flow(task: str, index: Index) -> dict:
    cache_key = " ".join(task.lower().split())
    if cache_key in _FLOW_CACHE:
        return {**_FLOW_CACHE[cache_key], "cached": True}
    route = resolve_route()
    pool = _stratified_pool(index, task)
    kept, dropped, sel_llm = orchestrate(task, pool, route)
    # Back-fill a model boundary (by TYPE) if the pool had one but selection skipped it.
    if not any(c["type"] in ("harness", "pipeline") for c in kept):
        for c in pool:
            if c["type"] in ("pipeline", "harness"):
                kept.append({**c, "stage": stage_for_type(c["type"]), "role": label_for_type(c["type"])})
                break
        kept.sort(key=lambda c: STAGE_ORDER.index(c["stage"]) if c.get("stage") in STAGE_ORDER else 99)
    cost = estimate_cost(kept)
    analysis = analyze_match(kept, pool)
    narrative, narr_llm = llm_narrative(task, kept, cost)
    result = {
        "task": task,
        "flow": {"steps": kept, "stages": flowchart(task, kept), "recipe": harness_recipe(task, kept),
                 "dropped": dropped, "analysis": analysis},
        "cost": cost,
        "narrative": narrative,
        "llm_used": (sel_llm or narr_llm),
        "selection_by_model": sel_llm,
        "embedding": describe_backend(),
        "cached": False,
    }
    if len(_FLOW_CACHE) > 500:  # bounded
        _FLOW_CACHE.clear()
    _FLOW_CACHE[cache_key] = result
    return result
