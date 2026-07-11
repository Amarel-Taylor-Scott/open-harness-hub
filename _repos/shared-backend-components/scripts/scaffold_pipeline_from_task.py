#!/usr/bin/env python3
"""Search the catalog for components matching a free-text task description
and emit a draft pipeline manifest. Designed for two audiences:

1. A human developer who knows roughly what they want to build.
2. An LLM agent that is asked to assemble a pipeline from the catalog.

Ranking modes:
- lexical (default fallback): token-overlap score against name + description
  + tags + industry + capability.
- semantic (--semantic): cosine similarity against precomputed sentence-
  transformers embeddings in dist/catalog.sqlite. Falls back to lexical
  if the embeddings table is empty.
- hybrid (--hybrid): blended score = 0.55 * semantic + 0.45 * lexical,
  with an additive edge-aware boost: if a top-hit pipeline already
  references X (uses_rule_pack / uses_persona / uses_adapter / step_ref),
  X gets +0.10 so siblings frequently used together surface together.

The script does NOT call an LLM; it ranks catalog manifests for an
agent to compose from. The output is intended to be a starting draft a
human (or agent) refines.

Usage:
    python3 _repos/shared-backend-components/scripts/scaffold_pipeline_from_task.py "Review a vendor invoice for fraud signals + extract line items"
    python3 _repos/shared-backend-components/scripts/scaffold_pipeline_from_task.py --hybrid "Detect human-trafficking signals in UGC posts with Gemma 4"
    python3 _repos/shared-backend-components/scripts/scaffold_pipeline_from_task.py --json "..."          # JSON output for agent consumption
    python3 _repos/shared-backend-components/scripts/scaffold_pipeline_from_task.py "..." --draft-yaml    # YAML draft to disk

Build the embeddings sidecar (one-time, ~30s on first run):
    OH_BUILD_EMBEDDINGS=1 python3 _repos/shared-backend-components/scripts/build_catalog_db.py
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import math
import os
import re
import sqlite3
import struct
import sys
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parent.parent
CATALOG = _resource("catalog")
DB_PATH = _resource("dist") / "catalog.sqlite"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.db.catalog_row_source import iter_components_from_rows, resolve_catalog_row_dir

STOP = {"with", "from", "this", "that", "have", "been", "will", "must", "shall", "into", "than", "then", "each", "such", "their", "would", "could", "should", "above", "below", "over", "more", "less", "very", "many", "some", "what", "when", "where", "which", "while", "until", "after", "before", "every", "etc", "the", "and", "for", "are", "any", "you", "your"}


def tokenize(text: str) -> set[str]:
    toks = set()
    for raw in text.lower().split():
        t = "".join(c for c in raw if c.isalnum())
        if len(t) >= 3 and t not in STOP:
            toks.add(t)
    return toks


def _searchable_component(doc: dict, path: str) -> dict:
    searchable = " ".join([
        doc.get("name", ""),
        doc.get("description", "") if isinstance(doc.get("description"), str) else "",
        " ".join(doc.get("tags", []) if isinstance(doc.get("tags"), list) else []),
        " ".join(doc.get("industry", []) if isinstance(doc.get("industry"), list) else []),
        " ".join(doc.get("capability", []) if isinstance(doc.get("capability"), list) else []),
    ])
    return {
        "id": doc["id"],
        "type": doc["type"],
        "name": doc.get("name", ""),
        "description": (doc.get("description") or "")[:200] if isinstance(doc.get("description"), str) else "",
        "tokens": tokenize(searchable),
        "path": path,
        "_doc": doc,
    }


def load_components() -> list[dict]:
    row_dir = resolve_catalog_row_dir()
    if row_dir is not None:
        return [
            _searchable_component(component.manifest, component.source_path)
            for component in iter_components_from_rows(row_dir)
        ]

    try:
        import yaml
    except ImportError:
        sys.stderr.write("pyyaml is required for YAML fallback: pip install pyyaml\n")
        sys.exit(2)

    out = []
    for p in CATALOG.rglob("*.yaml"):
        try:
            doc = yaml.safe_load(p.read_text())
        except Exception:
            continue
        if not isinstance(doc, dict) or not doc.get("id") or not doc.get("type"):
            continue
        out.append(_searchable_component(doc, str(p.relative_to(REPO))))
    return out


def lexical_score(task_tokens: set[str], component: dict) -> float:
    if not task_tokens:
        return 0.0
    overlap = task_tokens & component["tokens"]
    return len(overlap) / max(1, len(task_tokens) ** 0.7)


def _norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v)) or 1.0


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (_norm(a) * _norm(b))


def _unpack_vector(blob: bytes, dim: int) -> list[float]:
    return list(struct.unpack(f"{dim}f", blob))


def load_embeddings() -> tuple[dict[str, list[float]], str | None]:
    """Returns ({component_id: vector}, model_name) from dist/catalog.sqlite.

    Empty dict signals 'no embeddings available' and the caller falls back to
    pure lexical scoring.
    """
    if not DB_PATH.exists():
        return {}, None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        rows = c.execute("SELECT component_id, model, dim, vector FROM embeddings").fetchall()
        conn.close()
    except sqlite3.Error:
        return {}, None
    if not rows:
        return {}, None
    out = {}
    model = rows[0][1]
    for aid, _model, dim, blob in rows:
        try:
            out[aid] = _unpack_vector(blob, int(dim))
        except Exception:
            continue
    return out, model


def embed_query(task: str, model_name: str) -> list[float] | None:
    """Encode the task with the same model used to build the sidecar.

    Returns None if sentence-transformers isn't installed. Caller falls back.
    """
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError:
        return None
    model = SentenceTransformer(model_name)
    vec = model.encode([task], normalize_embeddings=True)[0]
    return list(vec.tolist())


def load_edges() -> dict[str, list[str]]:
    """Returns {src_id: [dst_id, ...]} from the edges table."""
    if not DB_PATH.exists():
        return {}
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        rows = c.execute("SELECT src_id, dst_id FROM edges").fetchall()
        conn.close()
    except sqlite3.Error:
        return {}
    out: dict[str, list[str]] = {}
    for src, dst in rows:
        out.setdefault(src, []).append(dst)
    return out


def search(
    task: str,
    components: list[dict],
    *,
    mode: str = "lexical",
    top_k: int = 25,
) -> tuple[list[tuple[dict, float, set[str], dict[str, float]]], str]:
    """Returns (ranked, effective_mode).

    `ranked` items are (component, blended_score, matched_tokens, components)
    where `components` is the per-source breakdown {lexical, semantic, edge}.
    `effective_mode` reflects what actually ran (may downgrade if embeddings
    aren't available).
    """
    tt = tokenize(task)

    embs: dict[str, list[float]] = {}
    qvec: list[float] | None = None
    model_name: str | None = None
    effective_mode = mode

    if mode in ("semantic", "hybrid"):
        embs, model_name = load_embeddings()
        if embs and model_name:
            qvec = embed_query(task, model_name)
        if not embs or qvec is None:
            effective_mode = "lexical"

    edges = load_edges() if mode == "hybrid" else {}

    # First pass: blended score without edge boost.
    ranked_first: list[tuple[dict, float, set[str], dict[str, float]]] = []
    for art in components:
        lx = lexical_score(tt, art)
        sm = 0.0
        if effective_mode in ("semantic", "hybrid") and qvec is not None and art["id"] in embs:
            sm = _cosine(qvec, embs[art["id"]])
        if effective_mode == "semantic":
            blended = sm
        elif effective_mode == "hybrid":
            blended = 0.55 * sm + 0.45 * lx
        else:
            blended = lx
        if blended > 0:
            ranked_first.append((art, blended, tt & art["tokens"], {"lexical": lx, "semantic": sm, "edge": 0.0}))

    ranked_first.sort(key=lambda x: -x[1])

    # Edge-aware boost (hybrid only): bump anything referenced by a top-K1
    # already-ranked pipeline. Encodes "these siblings ship together."
    if effective_mode == "hybrid" and edges:
        K1 = min(8, len(ranked_first))
        top_pipeline_ids = [a["id"] for (a, _, _, _) in ranked_first[:K1] if a["type"] == "pipeline"]
        boosted: set[str] = set()
        for pid in top_pipeline_ids:
            for dst in edges.get(pid, []):
                boosted.add(dst)
        if boosted:
            ranked_second: list[tuple[dict, float, set[str], dict[str, float]]] = []
            for art, score, m, comps in ranked_first:
                bump = 0.10 if art["id"] in boosted else 0.0
                comps = {**comps, "edge": bump}
                ranked_second.append((art, score + bump, m, comps))
            ranked_second.sort(key=lambda x: -x[1])
            return ranked_second[:top_k], effective_mode

    return ranked_first[:top_k], effective_mode


def group_by_type(hits: list[tuple[dict, float, set[str], dict[str, float]]]) -> dict[str, list[tuple[dict, float, set[str], dict[str, float]]]]:
    out: dict[str, list] = {}
    for h in hits:
        out.setdefault(h[0]["type"], []).append(h)
    return out


def first_of(grouped: dict, t: str) -> dict | None:
    return grouped[t][0][0] if grouped.get(t) else None


def first_id_of_subkind(grouped: dict, t: str, family: str) -> str | None:
    for art, _s, _m, _c in grouped.get(t, []):
        doc = art.get("_doc") or {}
        if doc.get("family") == family:
            return art["id"]
    return None


def make_draft_pipeline(task: str, grouped: dict) -> dict:
    persona = first_of(grouped, "persona")
    rule_pack = first_of(grouped, "rule-pack")
    knowledge_pack = first_of(grouped, "knowledge-pack")
    rubric = first_of(grouped, "rubric")
    adapter = first_of(grouped, "adapter")

    # If a classifier-family rule pack outranks a grep-family one, prefer
    # the grep one for the early-stage triage step (cheaper, deterministic);
    # keep the classifier for the judging step.
    grep_pack_id = first_id_of_subkind(grouped, "rule-pack", "grep") or (rule_pack["id"] if rule_pack else None)
    classifier_pack_id = first_id_of_subkind(grouped, "rule-pack", "classifier")

    steps: list[dict] = []
    steps.append({"id": "structured_to_prose", "kind": "processor", "ref": "processor/structured-to-prose", "inputs": {"data": "$.inputs.input_packet"}})
    steps.append({"id": "redact_pii", "kind": "processor", "ref": "processor/redact-pii-text", "inputs": {"text": "$.steps.structured_to_prose.output.prose"}})
    if grep_pack_id:
        steps.append({"id": "grep_red_flags", "kind": "rule_pack", "ref": grep_pack_id, "inputs": {"text": "$.steps.redact_pii.output.text"}})
    if knowledge_pack:
        steps.append({"id": "rag", "kind": "rule_pack", "ref": "rule-pack/hybrid-retrieval-policy", "inputs": {"query": "$.steps.grep_red_flags.output.fired" if grep_pack_id else "$.steps.redact_pii.output.text", "corpus": knowledge_pack["id"], "top_k": 6}})
    if classifier_pack_id and classifier_pack_id != grep_pack_id:
        steps.append({"id": "stage2_judge", "kind": "rule_pack", "ref": classifier_pack_id, "inputs": {"extracted_json": "$.steps.redact_pii.output.text"}})
    if rubric:
        steps.append({"id": "grade", "kind": "processor", "ref": "processor/llm-judge", "inputs": {"candidate": "$.steps.redact_pii.output.text", "rubric_ref": rubric["id"]}})
    applied = ["persona", "pii_redact"]
    if grep_pack_id:
        applied.append("grep")
    if knowledge_pack:
        applied.append("rag")
    if classifier_pack_id and classifier_pack_id != grep_pack_id:
        applied.append("classifier")
    if rubric:
        applied.append("judge")
    steps.append({"id": "audit", "kind": "processor", "ref": "processor/audit-trace-emitter", "inputs": {"step_id": "draft-pipeline", "applied_layers": applied}})

    defaults: dict = {}
    if persona:
        defaults["persona"] = persona["id"]
    if adapter:
        defaults["model_adapter"] = adapter["id"]
    else:
        defaults["model_adapter"] = "adapter/ollama-default"
    rule_pack_refs = [r for r in [grep_pack_id, classifier_pack_id] if r]
    if rule_pack_refs:
        defaults["rule_packs"] = rule_pack_refs
    if knowledge_pack:
        defaults["knowledge_packs"] = [knowledge_pack["id"]]

    pipeline = {
        "id": "pipeline/DRAFT-rename-me",
        "type": "pipeline",
        "version": "0.1.0",
        "name": f"DRAFT: {task[:60]}",
        "description": f"Auto-scaffolded by scripts/scaffold_pipeline_from_task.py from task: {task!r}",
        "authors": [{"name": "OpenHubForAI contributors"}],
        "license": "MIT",
        "industry": ["compliance"],
        "capability": ["evaluation", "extraction"],
        "modality": ["text"],
        "lifecycle": "experimental",
        "trust_boundary": "local",
        "pipeline_kind": "review",
        "inputs": [{"name": "input_packet", "type": "string|object"}],
        "outputs": [{"name": "grade", "type": "number"}, {"name": "findings", "type": "object[]"}],
        "defaults": defaults,
        "steps": steps,
        "success_criteria": [{"rubric": rubric["id"], "threshold": 0.6}] if rubric else [],
    }
    return pipeline


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", help="Free-text task description")
    parser.add_argument("--top-k", type=int, default=25)
    parser.add_argument("--semantic", action="store_true", help="Semantic search only (cosine over embeddings sidecar)")
    parser.add_argument("--hybrid", action="store_true", help="Hybrid lexical+semantic search with edge-aware boost (recommended)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON (for LLM agent consumption)")
    parser.add_argument("--draft-yaml", action="store_true", help="Emit a draft pipeline YAML manifest")
    args = parser.parse_args()

    mode = "hybrid" if args.hybrid else ("semantic" if args.semantic else "lexical")

    components = load_components()
    hits, effective_mode = search(args.task, components, mode=mode, top_k=args.top_k)
    grouped = group_by_type(hits)

    if args.json:
        payload = {
            "task": args.task,
            "mode_requested": mode,
            "mode_effective": effective_mode,
            "hits_by_type": {
                t: [{
                    "id": a["id"],
                    "score": round(s, 3),
                    "components": {k: round(v, 3) for k, v in c.items()},
                    "matched_tokens": sorted(m),
                    "name": a["name"],
                    "description": a["description"],
                    "path": a["path"],
                } for a, s, m, c in lst[:10]]
                for t, lst in grouped.items()
            },
            "draft_pipeline": make_draft_pipeline(args.task, grouped),
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.draft_yaml:
        try:
            import yaml
        except ImportError:
            sys.stderr.write("pyyaml is required for --draft-yaml: pip install pyyaml\n")
            return 2
        draft = make_draft_pipeline(args.task, grouped)
        print(yaml.safe_dump(draft, sort_keys=False))
        return 0

    print(f"Task: {args.task!r}")
    print(f"Mode: requested={mode}  effective={effective_mode}")
    if mode != "lexical" and effective_mode == "lexical":
        print("(embeddings sidecar not found or empty; run `OH_BUILD_EMBEDDINGS=1 python3 scripts/build_catalog_db.py` to enable semantic search)")
    print()
    print(f"Found {len(hits)} relevant components across {len(grouped)} types.")
    print()
    for t in ["persona", "rule-pack", "knowledge-pack", "rubric", "tool", "processor", "pattern", "adapter", "pipeline", "dataset"]:
        if t not in grouped:
            continue
        print(f"== {t} ({len(grouped[t])} hits) ==")
        for a, s, m, c in grouped[t][:5]:
            comp_str = f"lex={c['lexical']:.2f} sem={c['semantic']:.2f}" + (f" edge=+{c['edge']:.2f}" if c["edge"] > 0 else "")
            print(f"  [{s:.2f}] {a['id']}   ({comp_str})")
            print(f"         {a['name']}")
            if m:
                print(f"         matched: {', '.join(sorted(m))}")
        print()

    print("== Draft pipeline (use --draft-yaml to emit YAML) ==")
    draft = make_draft_pipeline(args.task, grouped)
    print(f"Steps: {len(draft['steps'])}")
    for s in draft["steps"]:
        print(f"  - {s['id']:25s} {s['ref']}")
    print()
    print("To get a full YAML draft:")
    print(f"  python3 scripts/scaffold_pipeline_from_task.py {args.task!r} --draft-yaml > /tmp/draft.yaml")
    print("To get JSON for agent consumption:")
    print(f"  python3 scripts/scaffold_pipeline_from_task.py {args.task!r} --json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
