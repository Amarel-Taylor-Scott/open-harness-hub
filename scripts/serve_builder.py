#!/usr/bin/env python3
"""Local showcase site for the paste-to-flow conversational builder.

Zero-dependency (stdlib ``http.server``). It demonstrates the headline product
interaction from ``docs/codex/master-goal.md``:

    paste a task  ->  hybrid-retrieve components  ->  assemble a flow
                  ->  estimate cost  ->  explain (optional local model)

Retrieval is **hybrid** (keyword + label + vector), so it returns sensible
results offline on the placeholder hash vectors, and gets sharper the moment a
real embedding backend is configured (``OH_EMBED_*``; see scripts/embeddings.py).
The "explain" narrative uses a local model (Gemma via Ollama) when one is
reachable (``OH_LLM_*``; see scripts/model_routes.py) and falls back to a
deterministic explanation otherwise — local now, cloud later, by env var only.

Run:
    python3 -m scripts.serve_builder            # http://127.0.0.1:8000
    python3 -m scripts.serve_builder --port 9000 --self-test
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts.db import build_vector_store as vs
from scripts.embeddings import describe_backend, resolve_backend
from scripts.model_routes import resolve_route

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.+-]{1,40}")
# Order in which an assembled flow is presented (rough pre-LLM -> model -> post).
# Stage-ordered flow (input → … → output). Each component type maps to a stage.
# Canonical stages — see docs/concepts/component-taxonomy-and-stages.md
STAGE_ORDER = ["Input Formatting", "Persona", "Knowledge", "Rules", "Tools",
               "Model (harness)", "Backbone pipeline", "Post-process", "Evaluate"]
TYPE_STAGE = {
    "persona": "Persona",
    "knowledge-pack": "Knowledge", "logic-pack": "Knowledge",
    "rule-pack": "Rules",
    "tool": "Tools",
    "processor": "Input Formatting", "pattern": "Post-process",
    "harness": "Model (harness)", "adapter": "Model (harness)",
    "pipeline": "Backbone pipeline",
    "rubric": "Evaluate", "benchmark": "Evaluate", "dataset": "Evaluate",
}
# Caps for a COHERENT flow — one persona, one model harness, one backbone, etc.
STAGE_CAPS = {"persona": 1, "knowledge-pack": 2, "logic-pack": 1, "rule-pack": 2,
              "tool": 2, "processor": 1, "pattern": 1, "harness": 1, "adapter": 1,
              "pipeline": 1, "rubric": 1, "benchmark": 1, "dataset": 1}
ROLE_BLURB = {
    "persona": "frames the role/voice the model adopts (no facts)",
    "knowledge-pack": "adds facts via a trigger (RAG / exact-id / regex / keyword)",
    "rule-pack": "deterministic text rules applied before the model",
    "tool": "takes an action (API / code / fetch / extract) or advanced preprocessing",
    "processor": "deterministic transform, no model call (formatting)",
    "harness": "runs the model behind a trust boundary",
    "adapter": "provider-neutral model transport — swap local↔hosted",
    "logic-pack": "prompts / schemas / response policy",
    "pattern": "reusable workflow shape",
    "pipeline": "an end-to-end backbone you can deploy",
    "rubric": "scores the output (the evaluation contract)",
    "benchmark": "proves the capability lift vs a bare model",
    "dataset": "labeled inputs/outputs for evaluation",
}
# Stopwords: matching on these ("and/for/the/risk") produced nonsense selections.
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "you", "are",
    "use", "using", "get", "via", "per", "out", "all", "any", "can", "has", "have",
    "of", "to", "in", "on", "is", "it", "as", "by", "or", "be", "at", "we", "an", "a",
    "task", "build", "make", "create", "run", "then", "when", "each", "its", "their",
    "based", "given", "following", "appropriate", "most", "more", "less",
}
RELEVANCE_FLOOR = 0.18  # below this a candidate is off-topic noise — drop it


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if len(t) >= 3 and t not in STOPWORDS}


class Index:
    """In-memory hybrid index loaded once from the vector store."""

    def __init__(self) -> None:
        self.backend = resolve_backend()
        store = vs.DEFAULT_STORE
        if not store.exists():
            vs.build(store=store, model=self.backend.model_id)
        con = sqlite3.connect(store)
        rows = con.execute(
            "SELECT subject_id, subject_type, text, embedding FROM object_embedding WHERE embedding_model=?",
            (self.backend.model_id,),
        ).fetchall()
        if not rows:  # store built with a different model — (re)build for this one
            con.close()
            vs.build(store=store, model=self.backend.model_id)
            con = sqlite3.connect(store)
            rows = con.execute(
                "SELECT subject_id, subject_type, text, embedding FROM object_embedding WHERE embedding_model=?",
                (self.backend.model_id,),
            ).fetchall()
        self.labels: dict[str, list[str]] = {}
        for sid, label in con.execute("SELECT subject_id, label FROM label_assignment"):
            self.labels.setdefault(sid, []).append(label)
        con.close()
        self.items = []
        for sid, stype, text, emb in rows:
            name, desc = (text.split(" · ", 2) + ["", ""])[:2]
            self.items.append({
                "id": sid, "type": stype, "name": name.strip() or sid,
                "desc": desc.strip(), "text": text, "tokens": _tokens(text),
                "vec": json.loads(emb), "labels": self.labels.get(sid, []),
            })

    def search(self, task: str, k: int = 24) -> list[dict]:
        qtok = _tokens(task)
        qvec = self.backend.embed_one(task)
        semantic = self.backend.promotable  # real embeddings → trust the vector
        out = []
        for it in self.items:
            lex = len(qtok & it["tokens"]) / (len(qtok) + 1)         # stopword-filtered overlap
            vec = max(0.0, sum(a * b for a, b in zip(qvec, it["vec"])))  # cosine (both L2)
            lab = 0.04 * len(set(it["labels"]) & qtok)               # label boost
            # With real embeddings the vector leads; offline (hash) lean on keywords.
            score = (0.72 * vec + 0.24 * lex + lab) if semantic else (0.30 * vec + 0.65 * lex + lab)
            shared = sorted(qtok & it["tokens"])[:6]
            out.append({**{x: it[x] for x in ("id", "type", "name", "desc", "labels")},
                        "score": round(score, 4), "vec": round(vec, 4), "matched": shared})
        out.sort(key=lambda r: r["score"], reverse=True)
        return out[:k]


def _coherent_select(candidates: list[dict]) -> list[dict]:
    """Deterministic fallback: relevance floor + per-type caps, ordered by stage."""
    kept_by_type: dict[str, list[dict]] = {}
    for c in sorted(candidates, key=lambda r: r["score"], reverse=True):
        if c["score"] < RELEVANCE_FLOOR:
            continue
        bucket = kept_by_type.setdefault(c["type"], [])
        if len(bucket) < STAGE_CAPS.get(c["type"], 1):
            bucket.append(c)
    flat = [c for t in TYPE_STAGE for c in kept_by_type.get(t, [])]
    return [{**c, "stage": TYPE_STAGE.get(c["type"], "Processors"),
             "role": ROLE_BLURB.get(c["type"], "")} for c in flat]


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
    # Fallback: pull the "keep" array body even if the object never closed,
    # then harvest component-id-shaped strings.
    km = re.search(r'"keep"\s*:\s*\[(.*?)(?:\]|$)', raw, re.DOTALL)
    return re.findall(r'"([a-z0-9-]+/[a-z0-9-]+)"', km.group(1) if km else raw)


def orchestrate(task: str, candidates: list[dict], route) -> tuple[list[dict], list[dict], bool]:
    """Pick the coherent, on-topic subset. An LLM prunes off-domain candidates
    (e.g. a drug-interaction pack for an ESG task) and one-of-each-stage; falls
    back to deterministic selection. Returns (kept, dropped, used_llm)."""
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
        "backbone pipeline, 1-2 knowledge packs, 1-2 rule packs, 1-2 tools, one rubric. "
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
        chosen.append({**c, "stage": TYPE_STAGE.get(c["type"], "Processors"),
                       "role": ROLE_BLURB.get(c["type"], "")})
    if not chosen:
        return _det_result()
    chosen.sort(key=lambda c: STAGE_ORDER.index(c["stage"]) if c["stage"] in STAGE_ORDER else 99)
    kept_ids = {c["id"] for c in chosen}
    dropped = [{"id": c["id"], "name": c["name"], "type": c["type"]}
               for c in floored if c["id"] not in kept_ids][:8]
    return chosen, dropped, True


def flowchart(kept: list[dict]) -> list[dict]:
    """Group kept components into ordered stages: Input → … → Output."""
    chart = [{"stage": "Input", "components": [
        {"id": "user task", "type": "input", "name": "User task", "role": "plain-language description"}]}]
    for stage in STAGE_ORDER:
        comps = [{"id": c["id"], "type": c["type"], "name": c["name"], "role": c["role"]}
                 for c in kept if c.get("stage") == stage]
        if comps:
            chart.append({"stage": stage, "components": comps})
    chart.append({"stage": "Output", "components": [
        {"id": "result", "type": "output", "name": "Costed, deployable flow", "role": "validated result + trace"}]})
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


def _stratified_pool(index: "Index", task: str) -> list[dict]:
    """Candidate pool that GUARANTEES per-type representation, so a flood of
    near-duplicate top scorers can't starve whole stages (the cause of a RAG
    task getting an ESG backbone, or a missing model/trust boundary)."""
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
    """Detect UNDER-match (a needed stage was available but unselected) and
    OVER-match (a stage exceeds its cap / redundant components)."""
    present = {c["stage"] for c in kept}
    pool_types = {c["type"] for c in pool}
    under = []
    if not (present & {"Model (harness)", "Backbone pipeline"}) and ({"harness", "pipeline"} & pool_types):
        under.append("Model boundary — a harness/pipeline was available but not selected")
    if "Evaluate" not in present and "rubric" in pool_types:
        under.append("Evaluate — a rubric was available but not selected")
    if "Knowledge / RAG" not in present and ("knowledge-pack" in pool_types):
        under.append("Knowledge — a knowledge/RAG pack was available but not selected")
    counts: dict[str, int] = {}
    for c in kept:
        counts[c["type"]] = counts.get(c["type"], 0) + 1
    over = [f"{t} ×{n}" for t, n in counts.items() if n > STAGE_CAPS.get(t, 1)]
    return {"undermatched": under, "overmatched": over, "stage_coverage": sorted(present)}


_FLOW_CACHE: dict[str, dict] = {}  # task -> result; the two LLM calls are the slow part


def build_flow(task: str, index: Index) -> dict:
    cache_key = " ".join(task.lower().split())
    if cache_key in _FLOW_CACHE:
        return {**_FLOW_CACHE[cache_key], "cached": True}
    route = resolve_route()
    pool = _stratified_pool(index, task)
    kept, dropped, sel_llm = orchestrate(task, pool, route)
    # Back-fill a model boundary if the pool had one but selection skipped it.
    if not any(c.get("stage") in ("Model (harness)", "Backbone pipeline") for c in kept):
        for c in pool:
            if c["type"] in ("pipeline", "harness"):
                kept.append({**c, "stage": TYPE_STAGE[c["type"]], "role": ROLE_BLURB.get(c["type"], "")})
                break
        kept.sort(key=lambda c: STAGE_ORDER.index(c["stage"]) if c.get("stage") in STAGE_ORDER else 99)
    cost = estimate_cost(kept)
    analysis = analyze_match(kept, pool)
    narrative, narr_llm = llm_narrative(task, kept, cost)
    result = {
        "task": task,
        "flow": {"steps": kept, "stages": flowchart(kept), "dropped": dropped, "analysis": analysis},
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


# --------------------------------------------------------------------------- #
# Export / standardize: assembled flow -> portable OHH pipeline component
# --------------------------------------------------------------------------- #
_STEP_KIND = {
    "knowledge-pack": "knowledge_pack", "logic-pack": "knowledge_pack",
    "rule-pack": "rule_pack", "tool": "tool", "processor": "processor",
    "harness": "harness", "adapter": "adapter", "pipeline": "pipeline",
}


def _slugify(text: str) -> str:
    return (re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48].strip("-")) or "assembled-flow"


def export_flow(result: dict) -> dict:
    """Standardize the assembled flow as a portable Open Harness Hub *pipeline*
    component — the catalog's canonical format — so a builder output round-trips
    back into the registry as a reusable, schema-validatable component. Per-
    component exports (MCP, Croissant, HF card, SPDX, …) live in scripts/emit/."""
    task = result["task"]
    steps, defaults, success = [], {}, []
    for c in result["flow"]["steps"]:
        t = c["type"]
        if t == "persona":
            defaults["persona"] = c["id"]
        elif t == "rubric":
            success.append({"rubric": c["id"], "threshold": 0.7})
        elif t in _STEP_KIND:
            steps.append({"id": c["id"].split("/")[-1], "kind": _STEP_KIND[t], "ref": c["id"]})
    spec = {
        "id": f"pipeline/{_slugify(task)}",
        "type": "pipeline",
        "version": "0.1.0",
        "name": f"Assembled flow: {task[:56]}",
        "description": f"Auto-assembled by the Open Harness Hub builder for: {task}",
        "authors": [{"name": "Open Harness Hub builder"}],
        "license": "MIT",
        "industry": ["cross_industry"],
        "capability": ["reasoning", "retrieval"],
        "modality": ["text"],
        "lifecycle": "experimental",
        "trust_boundary": "local",
        "freshness": "volatile",
        "tags": ["assembled", "builder-export"],
        "created": time.strftime("%Y-%m-%d"),
        "updated": time.strftime("%Y-%m-%d"),
        "task": task,
        "pipeline_kind": "assembled",
        "steps": steps or [{"id": "review", "kind": "harness", "ref": "harness/text-safety-review"}],
    }
    if defaults:
        spec["defaults"] = defaults
    if success:
        spec["success_criteria"] = success
    return spec


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
HTML = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Open Harness Hub — paste a task, get a flow</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#fb7714;--good:#3fb950}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:28px 22px 10px;max-width:980px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);font-size:14px}
main{max-width:980px;margin:0 auto;padding:12px 22px 60px}
textarea{width:100%;min-height:96px;background:var(--panel);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:12px;font:inherit;resize:vertical}
.row{display:flex;gap:10px;align-items:center;margin:10px 0}
button{background:var(--acc);color:#1a1300;border:0;border-radius:9px;padding:11px 18px;font-weight:650;cursor:pointer}
button:disabled{opacity:.5;cursor:wait}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin:6px 0 2px}
.chip{font-size:12.5px;color:var(--mut);border:1px solid var(--line);border-radius:20px;padding:4px 11px;cursor:pointer;background:var(--panel)}
.banner{font-size:13px;border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:8px;padding:9px 12px;color:var(--mut);margin:12px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:14px 16px;margin:14px 0}
.step{display:flex;gap:11px;padding:9px 0;border-bottom:1px solid var(--line)}.step:last-child{border:0}
.badge{font-size:11px;font-weight:700;letter-spacing:.3px;text-transform:uppercase;color:var(--acc);min-width:118px}
.sid{font-weight:600}.role{color:var(--mut);font-size:13.5px}
.matched{color:var(--good);font-size:12px}
.fc{display:flex;flex-direction:column}
.stage{border:1px solid var(--line);border-radius:9px;padding:8px 12px;background:#11161d}
.stage>.lbl{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--acc);margin-bottom:5px}
.stage .comp{font-size:13.5px;padding:3px 0}.stage .comp .cn{font-weight:600}.stage .comp .ci{color:var(--mut);font-size:12px}
.arrow{align-self:center;color:var(--mut);font-size:15px;margin:3px 0}
.dropped{color:var(--mut);font-size:12.5px;margin-top:10px;border-top:1px dashed var(--line);padding-top:8px}
.costs{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.cost{border:1px solid var(--line);border-radius:9px;padding:10px}.cost b{color:var(--acc)}
pre.narr{white-space:pre-wrap;background:transparent;color:var(--fg);margin:0;font:inherit}
.muted{color:var(--mut);font-size:12.5px}h3{margin:0 0 8px;font-size:15px}
a{color:var(--acc)}
</style></head><body>
<header><h1>Open Harness Hub <span style="color:var(--acc)">·</span> paste a task, get a flow</h1>
<div style="margin:6px 0 2px;font-size:13.5px"><a href="/" style="color:var(--acc);font-weight:600;margin-right:14px;text-decoration:none">Build a flow</a><a href="/browse" style="color:var(--acc);font-weight:600;text-decoration:none">Browse components →</a></div>
<div class=sub>Describe a task in plain language. The builder hybrid-searches the component registry and assembles a costed, deployable pipeline of existing components.</div></header>
<main>
<textarea id=task placeholder="e.g. Screen supplier disclosures for forced-labor risk, cite the relevant regulations, and route high-risk cases to human review."></textarea>
<div class=chips id=examples></div>
<div class=row><button id=go>Build pipeline</button><span class=muted id=status></span></div>
<div id=banner></div>
<div id=out></div>
</main>
<script>
const EX=["Detect human-trafficking indicators in a recruitment ad and route to the right hotline with citations",
"Screen a labor-recruitment contract for modern-slavery and debt-bondage red flags against ILO indicators",
"Flag predatory overcharging and illegal recruitment fees in a migrant worker's pay statement",
"Aggregate beneficial ownership under the OFAC 50% Rule to decide if an unlisted entity is blocked",
"Classify a CVE: derive its CVSS v3.1 vector and map it to the correct CWE",
"Triage acute malnutrition from MUAC and bilateral oedema under the CMAM protocol",
"Validate an HGVS variant string and map it to current ClinVar clinical significance"];
const exDiv=document.getElementById('examples');
EX.forEach(t=>{const c=document.createElement('span');c.className='chip';c.textContent=t;c.onclick=()=>{task.value=t;build()};exDiv.appendChild(c)});
const task=document.getElementById('task'),go=document.getElementById('go'),out=document.getElementById('out'),status=document.getElementById('status'),banner=document.getElementById('banner');
async function health(){try{const h=await (await fetch('/api/health')).json();
 banner.innerHTML='<div class=banner>'+(h.embedding.promotable?'✓ semantic embeddings active ('+h.embedding.embedding_model+')':'⚠ offline <b>placeholder</b> embeddings ('+h.embedding.embedding_model+') — hybrid keyword+label search is doing the work; set OH_EMBED_* for semantic ranking.')+' · '+h.components+' components · model polish: '+(h.llm_reachable?('on ('+h.llm.model+')'):'off (deterministic)')+'</div>';}catch(e){}}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function build(){const t=task.value.trim();if(!t)return;go.disabled=true;status.textContent='retrieving + assembling…';out.innerHTML='';
 try{const resp=await fetch('/api/build?task='+encodeURIComponent(t));
   if(!resp.ok)throw new Error('server returned HTTP '+resp.status);
   const ct=resp.headers.get('content-type')||'';
   if(ct.indexOf('application/json')<0)throw new Error('stale tab — this tunnel URL is no longer served; reload the current URL');
   render(await resp.json());
 }catch(e){out.innerHTML='<div class=card>Error: '+esc(''+e)+'<div class=muted style=margin-top:6px>If this says "stale", your browser tab is pointing at an old (ephemeral) tunnel URL — reload the current one.</div></div>'}
 go.disabled=false;status.textContent='';}
function render(r){let h='';
 h+='<div class=card><h3>Pipeline flow '+(r.selection_by_model?'<span class=muted>(orchestrated by local model)</span>':'<span class=muted>(deterministic)</span>')+'</h3><div class=fc>';
 r.flow.stages.forEach((st,i)=>{
   h+='<div class=stage><div class=lbl>'+esc(st.stage)+'</div>';
   st.components.forEach(c=>{h+='<div class=comp><span class=cn>'+esc(c.name)+'</span> <span class=ci>'+esc(c.id)+'</span><div class=role>'+esc(c.role||'')+'</div></div>'});
   h+='</div>';
   if(i<r.flow.stages.length-1)h+='<div class=arrow>↓</div>';
 });
 h+='</div>';
 if(r.flow.dropped&&r.flow.dropped.length){h+='<div class=dropped>Pruned as off-topic: '+r.flow.dropped.map(d=>esc(d.id||d)).join(', ')+'</div>';}
 h+='</div>';
 var et=encodeURIComponent(r.task);
 h+='<div class=card><h3>Export &amp; standardize</h3><a href="/api/export?format=yaml&task='+et+'">⬇ Open Harness Hub pipeline (YAML)</a> · <a href="/api/export?format=json&task='+et+'">JSON</a><div class=muted style=margin-top:6px>Standard catalog format — round-trips into the registry as a reusable component. Per-component exports (MCP · Croissant · HF card · SPDX · lm-eval · …) via scripts/emit/.</div></div>';
 h+='<div class=card><h3>Cost profile (per task)</h3><div class=costs>';
 ['cheap','balanced','quality'].forEach(k=>{h+='<div class=cost><b>'+k+'</b><br>$'+esc(r.cost[k].per_task_usd)+'<br><span class=muted>'+esc(r.cost[k].how)+'</span></div>'});
 h+='</div><div class=muted style=margin-top:8px>'+esc(r.cost.note)+'</div></div>';
 h+='<div class=card><h3>Why this flow '+(r.llm_used?'<span class=muted>(local model)</span>':'<span class=muted>(deterministic)</span>')+'</h3><pre class=narr>'+esc(r.narrative)+'</pre></div>';
 out.innerHTML=h;}
go.onclick=build;health();
</script></body></html>"""


BROWSE_HTML = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Open Harness Hub — browse components</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#fb7714;--good:#3fb950}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:24px 22px 8px;max-width:1000px;margin:0 auto}h1{font-size:21px;margin:0 0 4px}
.nav{margin:6px 0 2px;font-size:13.5px}.nav a{color:var(--acc);text-decoration:none;font-weight:600;margin-right:14px}
.sub{color:var(--mut);font-size:13.5px}
main{max-width:1000px;margin:0 auto;padding:10px 22px 60px}
input{width:100%;background:var(--panel);color:var(--fg);border:1px solid var(--line);border-radius:9px;padding:10px 12px;font:inherit}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}
.chip{font-size:12px;color:var(--mut);border:1px solid var(--line);border-radius:18px;padding:3px 10px;cursor:pointer;background:var(--panel)}
.chip.on{color:#1a1300;background:var(--acc);border-color:var(--acc);font-weight:650}
.muted{color:var(--mut);font-size:12.5px;margin:8px 0}
.item{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:9px 12px;margin:7px 0}
.badge{display:inline-block;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;color:var(--acc);border:1px solid var(--line);border-radius:5px;padding:1px 6px;margin-right:8px}
.nm{font-weight:600}.cid{color:var(--mut);font-size:12px}.ds{color:var(--mut);font-size:13px;margin-top:3px}
</style></head><body>
<header><h1>Open Harness Hub <span style="color:var(--acc)">·</span> browse components</h1>
<div class=nav><a href="/">← Build a flow</a><a href="/browse">Browse</a></div>
<div class=sub id=count>loading…</div></header>
<main>
<input id=q placeholder="Search components by name, id, or description…">
<div class=chips id=types></div>
<div class=muted id=status></div>
<div id=list></div>
</main>
<script>
let TYPE='';
const q=document.getElementById('q'),types=document.getElementById('types'),list=document.getElementById('list'),status=document.getElementById('status'),count=document.getElementById('count');
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
let T=null;
async function load(){
 const url='/api/components?limit=300'+(TYPE?('&type='+encodeURIComponent(TYPE)):'')+(q.value.trim()?('&q='+encodeURIComponent(q.value.trim())):'');
 const r=await (await fetch(url)).json();
 if(!T){T=r.by_type;count.textContent=r.total+' components across '+Object.keys(T).length+' types';renderChips()}
 status.textContent=r.matched+' match'+(r.matched===1?'':'es')+(r.matched>r.results.length?(' (showing '+r.results.length+')'):'');
 list.innerHTML=r.results.map(c=>'<div class=item><div><span class=badge>'+esc(c.type)+'</span><span class=nm>'+esc(c.name)+'</span> <span class=cid>'+esc(c.id)+'</span></div>'+(c.desc?'<div class=ds>'+esc(c.desc)+'</div>':'')+'</div>').join('');
}
function renderChips(){
 let h='<span class="chip'+(TYPE===''?' on':'')+'" data-t="">all</span>';
 Object.keys(T).sort().forEach(t=>{h+='<span class="chip'+(TYPE===t?' on':'')+'" data-t="'+t+'">'+esc(t)+' '+T[t]+'</span>'});
 types.innerHTML=h;
 [...types.querySelectorAll('.chip')].forEach(c=>c.onclick=()=>{TYPE=c.dataset.t;renderChips();load()});
}
let deb;q.oninput=()=>{clearTimeout(deb);deb=setTimeout(load,180)};
load();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    index: Index = None  # type: ignore

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif parsed.path == "/api/health":
            route = resolve_route()
            payload = {"embedding": self.index.backend.provenance(),
                       "components": len(self.index.items),
                       "llm": route.summary(), "llm_reachable": route.health()}
            self._send(200, json.dumps(payload).encode(), "application/json")
        elif parsed.path == "/api/build":
            task = (parse_qs(parsed.query).get("task") or [""])[0]
            if not task.strip():
                self._send(400, b'{"error":"task required"}', "application/json")
                return
            result = build_flow(task, self.index)
            self._send(200, json.dumps(result).encode(), "application/json")
        elif parsed.path == "/api/export":
            qs = parse_qs(parsed.query)
            task = (qs.get("task") or [""])[0]
            fmt = (qs.get("format") or ["yaml"])[0]
            if not task.strip():
                self._send(400, b'{"error":"task required"}', "application/json")
                return
            spec = export_flow(build_flow(task, self.index))
            slug = spec["id"].split("/")[-1]
            if fmt == "json":
                self._send(200, json.dumps(spec, indent=2).encode(), "application/json")
            else:
                import yaml as _yaml
                body = _yaml.safe_dump(spec, sort_keys=False, allow_unicode=True).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/yaml; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{slug}.yaml"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        elif parsed.path == "/browse":
            self._send(200, BROWSE_HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif parsed.path == "/api/components":
            from collections import Counter
            qs = parse_qs(parsed.query)
            q = (qs.get("q") or [""])[0].lower()
            typ = (qs.get("type") or [""])[0]
            limit = int((qs.get("limit") or ["300"])[0])
            items = self.index.items
            res = [{"id": it["id"], "type": it["type"], "name": it["name"], "desc": it["desc"][:160]}
                   for it in items
                   if (not typ or it["type"] == typ)
                   and (not q or q in it["name"].lower() or q in it["id"].lower() or q in it["desc"].lower())]
            payload = {"total": len(items), "by_type": dict(sorted(Counter(i["type"] for i in items).items())),
                       "matched": len(res), "results": res[:limit]}
            self._send(200, json.dumps(payload).encode(), "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *args) -> None:  # quiet
        pass


def serve(port: int = 8000) -> None:
    Handler.index = Index()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Open Harness Hub showcase → http://127.0.0.1:{port}  "
          f"({len(Handler.index.items)} components, embeddings={Handler.index.backend.name}, "
          f"promotable={Handler.index.backend.promotable})")
    httpd.serve_forever()


def _self_test() -> int:
    idx = Index()
    assert idx.items, "no components loaded"
    res = build_flow("screen supplier disclosures for forced labor and cite regulations", idx)
    assert res["flow"]["steps"], "empty flow"
    assert res["cost"]["balanced"]["per_task_usd"]
    print(json.dumps({
        "ok": True, "components": len(idx.items),
        "embedding_backend": idx.backend.name, "promotable": idx.backend.promotable,
        "selection_by_model": res["selection_by_model"], "llm_used": res["llm_used"],
        "stages": [s["stage"] for s in res["flow"]["stages"]],
        "kept": [f"{s['type']}/{s['id'].split('/')[-1]}" for s in res["flow"]["steps"]],
        "dropped": [d["id"] for d in res["flow"]["dropped"]],
    }, indent=2))
    spec = export_flow(res)
    assert spec["type"] == "pipeline" and spec["steps"], "export produced no pipeline"
    print("export OK → pipeline/" + spec["id"].split("/")[-1] + " with " + str(len(spec["steps"])) + " steps")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Local paste-to-flow showcase site.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    serve(args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
