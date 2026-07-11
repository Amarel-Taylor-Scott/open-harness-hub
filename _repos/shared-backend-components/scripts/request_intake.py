#!/usr/bin/env python3
"""scripts.request_intake — the STRUCTURED INTAKE layer: turn a raw user/agent prompt into a canonical REQUEST
BRIEF before retrieval, by answering a fixed set of questions — *what are you trying to do, what's the input,
what's the output, what must it integrate with, what platform, what technologies, what constraints* — so an
underspecified prompt becomes a standard, machine-usable shape — gaps INFERRED from context/defaults, not asked.

The brief is one schema; each field is filled by a ZOO of extractors, deterministic-first with model escalation:
  * det_facet    — operation/datatype facets (primitive_descriptor) for goal + data shapes.
  * det_lexicon  — curated seed lexicons (platform / technology / integration), word-boundary + phrase match.
  * det_pattern  — light regex for input/output direction ("from X" / "writes X to Y").
  * det_constraint — trailing constraint clauses (query_decomposer) → constraints, out of the capability text.
  * embed_nearest — (custom embedding) nearest canonical field value when the lexicon misses, via the real
                    local embedder — the hook where a custom embedding / fine-tuned model sharpens a fuzzy field.
  * llm          — a seam (None by default) for a small model / custom LoRA to fill the fields determinism can't;
                   it runs ONLY on the low-confidence gaps, and its output is re-typed by the same schema.

``intake(prompt, context=None, llm=None)`` fills each field deterministic-first, then ASSUMES the gaps from the
session/agent context (history + priors) and local-first defaults — it does NOT stop to ask. Clarifying questions
are a rare, advisory, NON-BLOCKING last resort for an essential unknowable field (an agent proceeds on the
brief). Returns the brief + per-field confidence + a NORMALIZED QUERY the agent acts on. serves_truth=false — an
intake is a candidate understanding of the request, never truth.

    PYTHONPATH=. python3 scripts/request_intake.py --self-test
    PYTHONPATH=. python3 scripts/request_intake.py --intake "dedupe customer records from Postgres on AWS in Python"
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import primitive_descriptor as _desc  # noqa: E402  REUSE: operation/datatype facets
from scripts import query_decomposer as _decomp  # noqa: E402  REUSE: constraint stripping

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_CONF_FILLED = 0.5   # a field with confidence >= this is "filled"; below → a clarifying question is asked
_EMBED_FLOOR = 0.30  # cosine above which an embed-nearest canonical value is accepted (single-source)

#: SEED lexicons (extensible — promote to vocabularies/ as they grow). canonical -> surface variants.
_PLATFORM_LEXICON: dict[str, tuple[str, ...]] = {
    "aws": ("aws", "amazon web services", "ec2", "ecs", "fargate", "lambda"), "gcp": ("gcp", "google cloud",
    "cloud run", "gke"), "azure": ("azure",), "kubernetes": ("kubernetes", "k8s"), "docker": ("docker",
    "container", "containerized"), "serverless": ("serverless", "cloud function", "edge function"),
    "local": ("local", "localhost", "on-prem", "on premise", "offline", "desktop"), "cloud": ("cloud", "hosted"),
    "browser": ("browser", "client-side", "web app"), "mobile": ("mobile", "ios", "android"),
    "render": ("render.com",), "fly": ("fly.io", "flyio"), "vercel": ("vercel",),
}
_TECH_LEXICON: dict[str, tuple[str, ...]] = {
    "python": ("python", "py"), "javascript": ("javascript", "js"), "typescript": ("typescript", "ts"),
    "react": ("react",), "node": ("node", "nodejs"), "fastapi": ("fastapi",), "flask": ("flask",),
    "django": ("django",), "pandas": ("pandas",), "pytorch": ("pytorch", "torch"), "tensorflow": ("tensorflow",),
    "go": ("golang",), "rust": ("rust",), "java": ("java",), "sql": ("sql",), "spark": ("spark",),
}
_INTEGRATION_LEXICON: dict[str, tuple[str, ...]] = {
    "postgres": ("postgres", "postgresql", "pgvector"), "mysql": ("mysql",), "redis": ("redis",),
    "s3": ("s3", "object storage"), "kafka": ("kafka",), "stripe": ("stripe",), "slack": ("slack",),
    "salesforce": ("salesforce",), "twilio": ("twilio",), "github": ("github",), "bigquery": ("bigquery",),
    "snowflake": ("snowflake",), "elasticsearch": ("elasticsearch", "opensearch"), "mongodb": ("mongodb", "mongo"),
    "openai": ("openai",), "anthropic": ("anthropic", "claude"), "ollama": ("ollama",),
}

#: the canonical REQUEST BRIEF — ordered fields, each with how it is filled, an optional local-first DEFAULT to
#: ASSUME when unknown, and ``ask_if_missing`` (only the essential fields ever produce an advisory question; the
#: rest are inferred or left blank, never asked — asking stops agents, so it is the last resort not the default).
REQUEST_FIELDS: tuple[dict[str, Any], ...] = (
    {"name": "goal", "question": "What are you trying to do (the main action/capability)?", "fill": "facet_op",
     "ask_if_missing": True},
    {"name": "input", "question": "What is the input to this?", "fill": "io_input"},
    {"name": "output", "question": "What should the output be?", "fill": "io_output"},
    {"name": "integrations", "question": "What systems or services must it integrate with?",
     "fill": "lexicon", "lexicon": _INTEGRATION_LEXICON},
    {"name": "platform", "question": "What platform should it run on (local, cloud, which provider)?",
     "fill": "lexicon", "lexicon": _PLATFORM_LEXICON, "embed_canonical": True, "default": ["local"]},
    {"name": "technologies", "question": "What languages / frameworks / technologies?",
     "fill": "lexicon", "lexicon": _TECH_LEXICON},
    {"name": "constraints", "question": "Any constraints (keep API stable, deterministic, budget)?",
     "fill": "constraints"},
)


def _lexicon_hits(text_lower: str, lexicon: dict[str, tuple[str, ...]]) -> list[str]:
    """Canonical keys whose surface variants appear in the prompt (word-boundary for tokens, substring phrases)."""
    hits: list[str] = []
    for canon, variants in lexicon.items():
        for v in variants:
            if (" " in v or "." in v) and v in text_lower:
                hits.append(canon); break
            if re.search(rf"\b{re.escape(v)}\b", text_lower):
                hits.append(canon); break
    return sorted(set(hits))


def _io_span(text: str, side: str) -> list[str]:
    """Light direction patterns: 'from X' → input; 'to/into/writes/returns X' → output. A weak deterministic
    signal (low confidence); precise input/output is a clarifying-question / model job."""
    pats = ({"from", "read", "ingest", "given", "takes"} if side == "input"
            else {"to", "into", "writes", "write", "return", "returns", "produce", "produces", "store", "stores",
                  "output", "outputs", "generate", "generates"})
    found: list[str] = []
    for m in re.finditer(r"\b(" + "|".join(sorted(pats)) + r")\s+(?:an?|the)?\s*([a-z][a-z0-9 ]{2,28}?)"
                         r"(?=\s+(?:and|then|,|\.|to|into|from|on|in|using|database|file|api|records?|rows?|"
                         r"table|data|back)\b|$)", text.lower()):
        span = m.group(2).strip()
        if span and span not in pats:
            found.append(span)
    return sorted(set(found))[:3]


def _embed_nearest(text: str, canon_labels: list[str]) -> Optional[str]:
    """Custom-embedding fallback: the canonical label nearest the prompt by the REAL local embedder (the hook a
    fine-tuned model / LoRA sharpens). None if nothing is close enough."""
    try:
        from scripts import capability_embedding as _emb  # noqa: PLC0415
        path = _emb.real_text_path()
        q = _emb.embed_text(text, path=path)
        best, best_s = None, _EMBED_FLOOR
        for label in canon_labels:
            s = _emb.cosine(q, _emb.embed_text(label, path=path))
            if s > best_s:
                best, best_s = label, s
        return best
    except Exception:  # noqa: BLE001 — no embedder → no fallback, never a crash
        return None


def _fill_field(spec: dict[str, Any], prompt: str, *, use_embed: bool) -> dict[str, Any]:
    """Fill ONE field by its extractor(s); return {value, confidence, source}."""
    name, kind = spec["name"], spec["fill"]
    qc = {"title": prompt, "blackbox": prompt, "input_edge": "", "output_edge": ""}
    if kind == "facet_op":
        val = sorted(_decomp._robust_operations(prompt))  # fuzzy: 'dedupes'->'dedup' the exact lexicon misses
        return {"value": val, "confidence": 0.9 if val else 0.0, "source": "det_facet"}
    if kind in ("io_input", "io_output"):
        span = _io_span(prompt, "input" if kind == "io_input" else "output")
        dts = sorted(_desc.datatypes(qc))
        val = span or dts
        return {"value": val, "confidence": 0.6 if span else (0.4 if dts else 0.0),
                "source": "det_pattern" if span else ("det_facet" if dts else "none")}
    if kind == "lexicon":
        val = _lexicon_hits(prompt.lower(), spec["lexicon"])
        if val:
            return {"value": val, "confidence": 0.9, "source": "det_lexicon"}
        if use_embed and spec.get("embed_canonical"):
            near = _embed_nearest(prompt, sorted(spec["lexicon"]))
            if near:
                return {"value": [near], "confidence": 0.5, "source": "embed_nearest"}
        return {"value": [], "confidence": 0.0, "source": "none"}
    if kind == "constraints":
        _cap, constraints = _decomp.strip_constraints(prompt)
        return {"value": constraints, "confidence": 0.8 if constraints else 0.0,
                "source": "det_constraint" if constraints else "none"}
    return {"value": [], "confidence": 0.0, "source": "none"}


def _infer_from_context(spec: dict[str, Any], context: dict[str, Any]) -> Optional[list[str]]:
    """Fill a field from the SESSION/AGENT context instead of asking: a direct prior value (context[field],
    context['environment'][field], or context['prior_brief'][field]) wins; otherwise re-run the field's own
    extractor over the history text so a platform/tech/integration mentioned earlier in the session carries
    forward. None only when the context is genuinely silent on this field."""
    name = spec["name"]
    for source in (context, context.get("environment") or {}, context.get("prior_brief") or {}):
        direct = source.get(name)
        if direct:
            return direct if isinstance(direct, list) else [direct]
    hist = context.get("history")
    if hist:
        text = hist if isinstance(hist, str) else " ".join(str(h) for h in hist)
        cell = _fill_field(spec, text, use_embed=False)
        if cell["confidence"] >= _CONF_FILLED and cell["value"]:
            return cell["value"] if isinstance(cell["value"], list) else [cell["value"]]
    return None


def intake(prompt: str, *, context: Optional[dict[str, Any]] = None,
           llm: Optional[Callable[[str], str]] = None, use_embed: bool = False) -> dict[str, Any]:
    """Normalize a raw prompt into a canonical REQUEST BRIEF, INFER-FIRST: fill each field deterministically,
    then ASSUME the gaps from ``context`` (session/agent history + priors) and local-first defaults, then an
    optional ``llm`` (small model / LoRA) seam. Clarifying questions are a rare last resort — only for essential
    fields still unknowable — and are ADVISORY: the agent proceeds on the brief, it is never stopped. 0-token
    unless ``llm`` runs."""
    context = context or {}
    brief: dict[str, Any] = {spec["name"]: _fill_field(spec, prompt, use_embed=use_embed)
                             for spec in REQUEST_FIELDS}

    # 1) ASSUME low-confidence gaps from the session/agent context — carry forward, do not ask
    for spec in REQUEST_FIELDS:
        if brief[spec["name"]]["confidence"] < _CONF_FILLED:
            inferred = _infer_from_context(spec, context)
            if inferred:
                brief[spec["name"]] = {"value": inferred, "confidence": 0.55, "source": "context"}

    # 2) a small model / LoRA seam fills whatever is still a gap (only when supplied), re-typed into the schema
    llm_calls = 0
    gaps = [s["name"] for s in REQUEST_FIELDS if brief[s["name"]]["confidence"] < _CONF_FILLED]
    if llm is not None and gaps:
        try:
            parsed = llm(f"Fill these request fields as a JSON object (string or list values); fields: {gaps}. "
                         f"Request: {prompt!r}")
            parsed = json.loads(parsed) if isinstance(parsed, str) else (parsed or {})
            llm_calls = 1
            for name in gaps:
                v = parsed.get(name)
                if v:
                    brief[name] = {"value": v if isinstance(v, list) else [v], "confidence": 0.7, "source": "llm"}
        except Exception:  # noqa: BLE001 — a bad answer never breaks intake
            pass

    # 3) local-first DEFAULT priors for anything still empty — still an assumption, still not a question
    for spec in REQUEST_FIELDS:
        if brief[spec["name"]]["confidence"] < _CONF_FILLED and spec.get("default") is not None:
            brief[spec["name"]] = {"value": spec["default"], "confidence": 0.4, "source": "default"}

    # 4) advisory questions ONLY for essential (ask_if_missing) fields still empty — rare, never blocking
    unresolved = [s for s in REQUEST_FIELDS if not brief[s["name"]]["value"]]
    questions = [{"field": s["name"], "question": s["question"]} for s in unresolved if s.get("ask_if_missing")]
    _det = {"det_facet", "det_lexicon", "det_pattern", "det_constraint"}
    return {"record_type": "request_brief", "prompt": prompt, "brief": brief,
            "determined_fields": [s["name"] for s in REQUEST_FIELDS if brief[s["name"]]["source"] in _det],
            "assumed_fields": [s["name"] for s in REQUEST_FIELDS
                               if brief[s["name"]]["source"] in ("context", "default", "embed_nearest", "llm")],
            "resolved_fields": [s["name"] for s in REQUEST_FIELDS if brief[s["name"]]["value"]],
            "clarifying_questions": questions, "blocking": False,
            "ready": bool(brief["goal"]["value"]),  # an agent can proceed once the goal is known or assumed
            "llm_calls": llm_calls, "normalized_query": to_normalized_query(brief),
            "note": "INFER-FIRST: gaps are assumed from session/agent context + local-first defaults, not asked. "
                    "clarifying_questions are advisory + non-blocking (essential unresolvable fields only) — the "
                    "agent proceeds on the brief. serves_truth=false.", **BOUNDARY}


def to_normalized_query(brief: dict[str, Any]) -> str:
    """The canonical string form — every field that has a value (determined OR assumed), so the agent gets a
    full normalized request to act on without waiting on questions."""
    parts = []
    for spec in REQUEST_FIELDS:
        val = brief.get(spec["name"], {}).get("value")
        if val:
            parts.append(f"{spec['name'].upper()}: {', '.join(val) if isinstance(val, list) else val}")
    return " | ".join(parts)


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    rich = ("Build a Python service that dedupes customer records from a Postgres database and writes the clean "
            "rows back, deployed on AWS, keeping the existing public API unchanged")
    b = intake(rich)
    brief = b["brief"]
    checks.append(("goal is extracted from the operation facet", "dedup" in brief["goal"]["value"]))
    checks.append(("the integration (Postgres) is extracted by lexicon", "postgres" in brief["integrations"]["value"]))
    checks.append(("the platform (AWS) is extracted by lexicon", "aws" in brief["platform"]["value"]))
    checks.append(("the technology (Python) is extracted by lexicon", "python" in brief["technologies"]["value"]))
    checks.append(("the constraint is stripped out of the capability text",
                   any("public api" in c.lower() for c in brief["constraints"]["value"])))
    checks.append(("a normalized query string is produced from the filled fields",
                   "GOAL:" in b["normalized_query"] and "PLATFORM:" in b["normalized_query"]))

    # a fully-specified prompt asks NOTHING and is ready to proceed (the common case must not stop an agent)
    checks.append(("a clear prompt produces ZERO questions, is ready, non-blocking",
                   b["clarifying_questions"] == [] and b["ready"] is True and b["blocking"] is False))

    # INFER-FIRST: an unstated field is ASSUMED from the session CONTEXT (carried forward), never asked
    ctx = intake("dedupe the rows", context={"platform": ["aws"], "technologies": ["python"]})
    checks.append(("an unstated field is assumed from session context, not asked",
                   "aws" in ctx["brief"]["platform"]["value"] and ctx["brief"]["platform"]["source"] == "context"
                   and not any(q["field"] == "platform" for q in ctx["clarifying_questions"])))
    # ...and from the session HISTORY text too
    hist = intake("now also validate them", context={"history": "build a python service on gcp with bigquery"})
    checks.append(("fields carry forward from session HISTORY text (assumed, not asked)",
                   "gcp" in hist["brief"]["platform"]["value"] and "python" in hist["brief"]["technologies"]["value"]
                   and hist["clarifying_questions"] == []))

    # local-first DEFAULT: no platform stated and no context -> ASSUME local, do NOT ask
    d = intake("dedupe the rows")
    checks.append(("an unknown platform defaults to local (assumed), never a question",
                   d["brief"]["platform"]["value"] == ["local"] and d["brief"]["platform"]["source"] == "default"
                   and not any(q["field"] == "platform" for q in d["clarifying_questions"])))

    # questions are RARE + advisory: even a thin prompt asks at most the ONE essential field (goal), non-blocking
    thin = intake("help me with the thing")
    checks.append(("questions are rare + advisory (<=1, essential only, non-blocking)",
                   len(thin["clarifying_questions"]) <= 1 and thin["blocking"] is False
                   and all(q["field"] == "goal" for q in thin["clarifying_questions"])))

    # a lexicon VARIANT resolves to the canonical value
    checks.append(("a lexicon VARIANT resolves to the canonical value (postgresql->postgres)",
                   "postgres" in intake("store it in postgresql")["brief"]["integrations"]["value"]))

    # the LLM/LoRA seam fills a gap ONLY when present; deterministic default is 0-token
    checks.append(("deterministic intake spends 0 tokens", b["llm_calls"] == 0))
    stub = intake("zzz the qqq", llm=lambda p: json.dumps({"goal": "build a thing"}))
    checks.append(("the llm seam fills an essential gap and is counted",
                   stub["llm_calls"] == 1 and stub["brief"]["goal"]["source"] == "llm" and stub["ready"] is True))

    # determinism + governance
    checks.append(("intake is deterministic (byte-identical twice)",
                   json.dumps(intake(rich), sort_keys=True) == json.dumps(intake(rich), sort_keys=True)))
    checks.append(("the brief is candidate/serves_truth=false", b["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - request_intake: normalize a raw prompt into a canonical REQUEST BRIEF ({len(REQUEST_FIELDS)} "
          f"fields — goal/input/output/integrations/platform/technologies/constraints), each filled by a zoo of "
          f"extractors (facet / lexicon / pattern / constraint-strip / embed-nearest / llm-seam), INFER-FIRST "
          f"and 0-token; gaps are ASSUMED from session/agent context + local-first defaults (not asked), and "
          f"clarifying questions are a rare, advisory, non-blocking last resort — the agent proceeds on the "
          f"normalized brief. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--intake", metavar="PROMPT", default=None, help="normalize one prompt into a brief")
    ap.add_argument("--embed", action="store_true", help="enable the embed-nearest canonical fallback")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.intake:
        print(json.dumps(intake(args.intake, use_embed=args.embed), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
