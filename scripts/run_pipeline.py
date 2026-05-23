#!/usr/bin/env python3
"""Minimal pipeline runner — load a pipeline manifest, walk its steps,
call a model adapter for harness steps, and emit a sample-run JSON.

This is the runtime that the playground (hf-space/app.py) uses. It is
intentionally small: each step kind has one handler, and unknown step
kinds become a stub with `simulated: true`.

Usage:
  python scripts/run_pipeline.py pipeline/research-entity --inputs inputs.json
  python scripts/run_pipeline.py pipeline/brand-safe-product-photo --simulate
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml is required: pip install pyyaml\n")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"


def load_catalog() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts or any(p == "data" for p in path.parts):
            continue
        try:
            data = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and "id" in data:
            out[data["id"]] = data
    return out


PATH_RE = re.compile(r"\$\.([A-Za-z_]+)(?:\.([A-Za-z0-9_\.]+))?")


def resolve(value: Any, ctx: dict) -> Any:
    """Resolve `$.steps.<id>.output...`-style references against ctx."""
    if not isinstance(value, str):
        return value
    match = PATH_RE.fullmatch(value)
    if not match:
        return value
    head, tail = match.group(1), match.group(2) or ""
    obj: Any = ctx.get(head)
    if tail:
        for part in tail.split("."):
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return None
    return obj


# ------------------------------------------------------------------
# Processor implementations — small, deterministic, no external calls.
# Open vocabulary: add new ones by id.
# ------------------------------------------------------------------

_PII_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "EMAIL"),
    # Phone: avoid eating digit-runs embedded in hyphenated tokens
    # (Slack/Datadog/AWS API IDs etc.). Require either intl prefix,
    # parenthesised area code, OR an actual phone formatting that
    # wouldn't appear inside an alphanumeric-hyphen identifier.
    (re.compile(r"(?<![\w-])(?:\+\d{1,3}[ -]?)?(?:\(\d{2,4}\)\s?\d{3,4}[ -]?\d{4}|\d{3}[ -]\d{3}[ -]\d{4})(?![\w-])"), "PHONE"),
    (re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"), "US_SSN"),
    (re.compile(r"(?<![\w-])[A-Z]{2}\d{2}[A-Z0-9]{12,30}(?![\w-])"), "IBAN"),
    (re.compile(r"(?<!\d)(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13})(?!\d)"), "CREDIT_CARD"),
]

def _redact_pii(text: str) -> tuple[str, list[dict]]:
    found: list[dict] = []
    for pat, kind in _PII_PATTERNS:
        for m in pat.finditer(text):
            found.append({"type": kind, "start": m.start(), "end": m.end(), "value": m.group()[:32]})
        text = pat.sub(f"[REDACTED:{kind}]", text)
    return text, found


def _structured_to_prose(data, prefix: str = "") -> list[str]:
    out: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            label = k.replace("_", " ")
            if isinstance(v, (str, int, float, bool)) and v not in (None, "", 0):
                out.append(f"{label}: {v}")
            else:
                out.extend(_structured_to_prose(v, label))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                if item.strip():
                    out.append(f"{prefix}: {item}" if prefix else item)
            elif isinstance(item, dict):
                out.extend(_structured_to_prose(item, prefix))
    elif isinstance(data, str) and data.strip():
        out.append(f"{prefix}: {data}" if prefix else data)
    return out


def _run_processor(ref_id: str, inputs: dict, artifact: dict | None) -> dict:
    """Dispatch on processor id. Falls back to structured echo if unknown."""
    if ref_id == "processor/structured-to-prose":
        lines = _structured_to_prose(inputs.get("data", {}))
        return {"prose": "\n".join(lines), "lines": lines, "line_count": len(lines)}

    if ref_id == "processor/redact-pii-text":
        text = inputs.get("text", "")
        if not isinstance(text, str):
            text = json.dumps(text) if text else ""
        redacted, found = _redact_pii(text)
        counts: dict[str, int] = {}
        for f in found:
            counts[f["type"]] = counts.get(f["type"], 0) + 1
        return {"text": redacted, "detected_entities": found, "entity_counts_by_type": counts}

    if ref_id == "processor/audit-trace-emitter":
        return {
            "step_id":        inputs.get("step_id", "unknown"),
            "applied_layers": inputs.get("applied_layers", []),
            "trace_ts":       time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    if ref_id == "processor/llm-judge":
        return _llm_judge(inputs)

    if ref_id == "processor/checklist-evaluator":
        return _checklist_evaluator(inputs)

    return {"_simulated": True, "echo": inputs, "processor": ref_id}


def _checklist_evaluator(inputs: dict) -> dict:
    """Apply named procedural checklist as deterministic GO/NO-GO gate."""
    candidate = inputs.get("candidate", "")
    if not isinstance(candidate, str):
        candidate = json.dumps(candidate) if candidate else ""
    candidate_lc = candidate.lower()
    checklist_id = inputs.get("checklist_id", "")

    checklists_path = Path(__file__).resolve().parent.parent / "data" / "technician-checklists" / "checklists.jsonl"
    checklist = None
    if checklists_path.exists():
        for line in checklists_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("id") == checklist_id:
                checklist = rec
                break
    if not checklist:
        return {"verdict": "nogo", "items": [], "nogo_triggers": [f"checklist_not_found:{checklist_id}"], "checklist_version": "n/a"}

    def _kw_tokens(text: str) -> list[str]:
        toks = []
        stop = {"with", "from", "this", "that", "have", "been", "will", "must", "shall", "into", "than", "then", "each", "such", "their", "would", "could", "should", "above", "below", "over", "more", "less", "very", "many", "some", "what", "when", "where", "which", "while", "until", "after", "before", "every", "etc"}
        for raw in text.lower().split():
            t = "".join(c for c in raw if c.isalnum())
            if len(t) >= 4 and t not in stop:
                toks.append(t)
        return toks

    def _bigrams(tokens: list[str]) -> list[str]:
        return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]

    items = []
    for step_text in checklist.get("steps", []):
        toks = _kw_tokens(step_text)
        if not toks:
            items.append({"step": step_text, "status": "unverified", "evidence": ""})
            continue
        matched = sum(1 for t in toks if t in candidate_lc)
        ratio = matched / max(1, len(toks))
        status = "verified" if ratio >= 0.35 else "unverified"
        items.append({"step": step_text, "status": status, "matched_tokens": matched, "total_tokens": len(toks)})

    NEGATION_WORDS = {"not", "no", "missing", "fail", "failed", "failure", "exceed", "exceeds", "exceeded", "exceedance", "overdue", "past", "unable", "absent", "loss", "lost", "unverified", "uncorrected", "open", "below", "exposed", "expired", "violation", "violated", "wrong", "incorrect", "delayed", "unreported", "unresolved", "incomplete", "noncompliant", "noncompliance", "unauthorized", "danger", "dangered", "hazardous", "discrepancy", "lapsed", "leak", "leakage", "outage", "abort", "stop", "halt", "withdraw", "trip", "block", "omitted", "illuminated", "without"}

    cand_tokens = _kw_tokens(candidate)
    cand_text_lc = candidate_lc

    COMPLIANCE_PHRASES = ["within limits", "within limit", "within window", "within tolerance", "within spec", "within range", "within plan", "within 3", "within ±", "within +/-", "well above", "well below", "all closed", "no split", "no findings", "no defect", "no defects", "no exceedance", "no violation", "no violations", "no breach", "no breaches", "no tolerance violation", "all completed", "all verified", "all current", "fully compliant", "verified compliant", "compliant per", "no concerns", "no issues", "no anomaly", "no anomalies", "compliant", "fully resolved", "all resolved", "unchanged", "tolerances applied", "delivered ≥", "received before", "screening clear", "no changed circumstance", "meets the 3 business", "verified within"]

    WINDOW_SIZE = 28

    nogo_triggers: list[str] = []
    for trigger in checklist.get("go_nogo", []):
        trig_content = [t for t in _kw_tokens(trigger) if t not in NEGATION_WORDS]
        if len(trig_content) < 2:
            continue
        trig_content_set = set(trig_content)
        # Require ≥70% of distinct content tokens to appear within a single sliding window
        required = max(2, int(round(0.70 * len(trig_content_set))))

        best_idx = -1
        best_hit = 0
        for i in range(len(cand_tokens)):
            window = cand_tokens[i:i + WINDOW_SIZE]
            hit = len(trig_content_set & set(window))
            if hit > best_hit:
                best_hit = hit
                best_idx = i
                if best_hit == len(trig_content_set):
                    break
        if best_hit < required:
            continue

        window_tokens = cand_tokens[best_idx:best_idx + WINDOW_SIZE]
        first_tok = window_tokens[0]
        last_tok = window_tokens[-1] if window_tokens else first_tok
        first_pos = candidate_lc.find(first_tok)
        last_pos = candidate_lc.rfind(last_tok, first_pos)
        if first_pos < 0:
            continue
        lo_pos = max(0, first_pos - 60)
        hi_pos = (last_pos + len(last_tok) + 120) if last_pos >= 0 else min(len(candidate_lc), first_pos + 400)
        local_context = candidate_lc[lo_pos:hi_pos]

        compliance_assert = any(p in local_context for p in COMPLIANCE_PHRASES)
        if compliance_assert:
            continue

        import re as _re_local
        def _word_in(text: str, word: str) -> bool:
            return bool(_re_local.search(r"\b" + _re_local.escape(word) + r"\b", text))

        trigger_lc = trigger.lower()
        trig_negation_anchors = [
            "".join(c for c in w if c.isalpha())
            for w in trigger_lc.replace("/", " ").split()
            if "".join(c for c in w if c.isalpha()) in NEGATION_WORDS
        ]
        if trig_negation_anchors:
            has_specific_neg = any(_word_in(local_context, w) for w in trig_negation_anchors)
            generic_neg_present = any(_word_in(local_context, w) for w in NEGATION_WORDS)
            if not (has_specific_neg or generic_neg_present):
                continue
        nogo_triggers.append(trigger)

    unverified_count = sum(1 for it in items if it["status"] == "unverified")
    total = max(1, len(items))
    verdict = "nogo" if (nogo_triggers or unverified_count >= (total + 1) // 2) else "go"
    return {
        "verdict":              verdict,
        "items":                items,
        "nogo_triggers":        nogo_triggers,
        "checklist_id":         checklist_id,
        "checklist_artifact":   checklist.get("artifact", ""),
        "checklist_source":     checklist.get("source", ""),
        "unverified_count":     unverified_count,
        "step_count":           total,
    }


# ------------------------------------------------------------------
# LLM judge — three execution paths, picked in order:
#   1. Real adapter call (Ollama if reachable; Anthropic / OpenAI if
#      env keys present and OH_JUDGE_ARM names one)
#   2. Deterministic rubric-based score from prior-step GREP hits +
#      severity weighting (always works, no network)
#   3. The bare stub (only if catalog has no rubric)
# ------------------------------------------------------------------
_SEVERITY_WEIGHT = {"critical": 1.0, "high": 0.6, "medium": 0.3, "low": 0.1}


def _deterministic_grade(rubric: dict | None, ctx_steps: dict) -> dict:
    """Reduce rubric pass/fail to a number using prior GREP findings."""
    if not rubric:
        return {"score": None, "method": "no_rubric"}

    severity_counts = {k: 0 for k in _SEVERITY_WEIGHT}
    for step in ctx_steps.values():
        if step.get("kind") == "rule_pack":
            for h in (step.get("output") or {}).get("fired", []) or []:
                sev = (h.get("severity") or "low").lower()
                if sev in severity_counts:
                    severity_counts[sev] += 1

    # Severity-weighted penalty: each finding reduces score by its
    # weight × 0.05, capped at 1.0 penalty.
    penalty = sum(severity_counts[s] * _SEVERITY_WEIGHT[s] * 0.05 for s in severity_counts)
    score = max(0.0, 1.0 - min(penalty, 1.0))

    return {
        "score":          round(score, 3),
        "rubric":         rubric.get("id"),
        "rubric_version": rubric.get("version"),
        "method":         "deterministic_severity_weighted",
        "severity_counts": severity_counts,
        "penalty":         round(penalty, 3),
    }


def _llm_judge(inputs: dict) -> dict:
    """LLM judge — try adapter, fall back to deterministic."""
    rubric_id = inputs.get("rubric_ref")
    candidate = inputs.get("candidate", "")
    rubric_artifact = _load_artifact(rubric_id) if rubric_id else None
    ctx_steps = _CURRENT_CTX.get("steps", {}) if _CURRENT_CTX else {}

    arm = os.environ.get("OH_JUDGE_ARM", "deterministic")
    adapter_result: dict | None = None

    if arm == "ollama" and _ollama_available():
        adapter_result = _judge_via_ollama(candidate, rubric_artifact)
    elif arm == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
        adapter_result = _judge_via_anthropic(candidate, rubric_artifact)
    elif arm == "openai" and os.environ.get("OPENAI_API_KEY"):
        adapter_result = _judge_via_openai(candidate, rubric_artifact)

    deterministic = _deterministic_grade(rubric_artifact, ctx_steps)

    if adapter_result is not None:
        return {
            "score":         adapter_result.get("score", deterministic.get("score")),
            "rationale":     adapter_result.get("rationale", ""),
            "rubric":        rubric_id,
            "method":        f"llm_judge:{arm}",
            "deterministic_baseline": deterministic,
        }
    return {**deterministic, "method_label": "deterministic (no model arm configured / available)"}


def _load_artifact(art_id: str | None) -> dict | None:
    if not art_id:
        return None
    catalog = _CURRENT_CATALOG
    if catalog is None:
        return None
    return catalog.get(art_id)


def _ollama_available() -> bool:
    try:
        import urllib.request
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        with urllib.request.urlopen(f"{host}/api/tags", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def _judge_via_ollama(candidate: str, rubric: dict | None) -> dict | None:
    try:
        import urllib.request
        host  = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        prompt = _build_judge_prompt(candidate, rubric)
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.0, "num_predict": int(os.environ.get("OH_OLLAMA_MAX_TOKENS", "512"))}}).encode()
        req = urllib.request.Request(f"{host}/api/generate", data=payload, headers={"Content-Type": "application/json"})
        timeout = int(os.environ.get("OH_OLLAMA_TIMEOUT", "300"))
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        return _parse_judge_response(data.get("response", ""))
    except Exception as e:
        return {"score": None, "rationale": f"ollama_error: {e}"}


def _judge_via_anthropic(candidate: str, rubric: dict | None) -> dict | None:
    try:
        import urllib.request
        api_key = os.environ["ANTHROPIC_API_KEY"]
        model   = os.environ.get("OH_ANTHROPIC_MODEL", "claude-sonnet-4-6")
        prompt = _build_judge_prompt(candidate, rubric)
        payload = json.dumps({"model": model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        text = "".join(b.get("text", "") for b in data.get("content", []))
        return _parse_judge_response(text)
    except Exception as e:
        return {"score": None, "rationale": f"anthropic_error: {e}"}


def _judge_via_openai(candidate: str, rubric: dict | None) -> dict | None:
    try:
        import urllib.request
        api_key = os.environ["OPENAI_API_KEY"]
        model   = os.environ.get("OH_OPENAI_MODEL", "gpt-5")
        endpoint = os.environ.get("OH_OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions")
        prompt = _build_judge_prompt(candidate, rubric)
        payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}).encode()
        req = urllib.request.Request(endpoint, data=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        text = data["choices"][0]["message"]["content"]
        return _parse_judge_response(text)
    except Exception as e:
        return {"score": None, "rationale": f"openai_error: {e}"}


def _build_judge_prompt(candidate: str, rubric: dict | None) -> str:
    rubric_block = ""
    if rubric and "dimensions" in rubric:
        lines = []
        for d in rubric["dimensions"]:
            lines.append(f"  - {d['id']} ({d.get('weight', 0):.2f}): {d.get('label', '')}\n    evidence required: {d.get('evidence_required', '')}")
        rubric_block = "\n".join(lines)
    return (
        f"You are a grading judge. Grade the following candidate text against the rubric.\n"
        f"Return ONLY this JSON: {{\"score\": 0.0-1.0, \"per_dimension\": {{...}}, \"rationale\": \"...\"}}\n"
        f"\nRUBRIC ({rubric.get('id') if rubric else 'unknown'}):\n{rubric_block}\n"
        f"\nCANDIDATE:\n{candidate[:8000]}\n"
        f"\nJSON:"
    )


def _parse_judge_response(text: str) -> dict:
    try:
        start = text.index("{")
        end   = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"score": None, "rationale": text[:1000]}


# Tiny module-level state so processors can see catalog + context.
_CURRENT_CATALOG: dict[str, dict] | None = None
_CURRENT_CTX:     dict | None = None


# ------------------------------------------------------------------
# Composable success-criteria evaluator.
# ------------------------------------------------------------------
def _resolve_path(path: str, ctx: dict) -> Any:
    """Resolve $.steps.X.output.field or $.inputs.field against ctx."""
    if not isinstance(path, str) or not path.startswith("$."):
        return path
    parts = path[2:].split(".")
    obj: Any = ctx
    for p in parts:
        if isinstance(obj, dict):
            obj = obj.get(p)
        else:
            return None
        if obj is None:
            return None
    return obj


def _evaluate_criterion(criterion: dict, ctx: dict) -> dict:
    """Evaluate one success criterion. Returns {pass, kind, label, details}."""
    kind = criterion.get("kind", "rubric")  # legacy default
    label = criterion.get("label") or kind
    severity = criterion.get("severity", "medium")

    try:
        if kind == "rubric":
            target = _find_judge_score_in_trace(ctx)
            threshold = criterion.get("threshold", 0.7)
            passed = target is not None and target >= threshold
            return {"pass": passed, "kind": kind, "label": label, "severity": severity, "actual": target, "threshold": threshold}

        if kind == "regex":
            text = _resolve_path(criterion.get("target", ""), ctx) or ""
            if not isinstance(text, str):
                text = json.dumps(text)
            flags = re.IGNORECASE if criterion.get("case_insensitive", True) else 0
            matches = re.findall(criterion["pattern"], text, flags)
            must = criterion.get("must_match", True)
            passed = bool(matches) if must else not matches
            return {"pass": passed, "kind": kind, "label": label, "severity": severity, "match_count": len(matches), "must_match": must, "first_match": (str(matches[0])[:80] if matches else None)}

        if kind == "semantic":
            text = _resolve_path(criterion.get("target", ""), ctx) or ""
            topics = criterion.get("must_cover", [])
            threshold = criterion.get("similarity_threshold", 0.6)
            sims = _semantic_similarities(text, topics)
            min_sim = min(sims.values()) if sims else 0.0
            return {"pass": min_sim >= threshold, "kind": kind, "label": label, "severity": severity, "per_topic_similarity": sims, "min_similarity": round(min_sim, 3), "threshold": threshold}

        if kind == "llm_judge":
            text = _resolve_path(criterion.get("target", ""), ctx) or ""
            rubric = _load_artifact(criterion.get("rubric"))
            res = _llm_judge({"candidate": text, "rubric_ref": criterion.get("rubric")})
            score = res.get("score")
            threshold = criterion.get("threshold", 0.7)
            passed = score is not None and score >= threshold
            return {"pass": passed, "kind": kind, "label": label, "severity": severity, "score": score, "threshold": threshold, "method": res.get("method"), "rationale": (res.get("rationale") or "")[:300]}

        if kind == "deterministic":
            actual = _resolve_path(criterion.get("target", ""), ctx)
            op = criterion.get("op")
            value = criterion.get("value")
            passed = _apply_op(actual, op, value)
            return {"pass": passed, "kind": kind, "label": label, "severity": severity, "actual": actual, "op": op, "expected": value}

        if kind == "tool_validate":
            target = _resolve_path(criterion.get("target", ""), ctx) if criterion.get("target") else None
            tool_id = criterion.get("tool")
            params = criterion.get("params", {})
            tool_result = _invoke_tool(tool_id, target, params)
            return {"pass": bool(tool_result.get("pass")), "kind": kind, "label": label, "severity": severity, "tool": tool_id, "tool_result": tool_result}

        if kind == "composite":
            op = criterion.get("op", "AND")
            children = criterion.get("children", [])
            child_results = [_evaluate_criterion(c, ctx) for c in children]
            child_pass = [r["pass"] for r in child_results]
            if op == "AND":
                passed = all(child_pass)
            elif op == "OR":
                passed = any(child_pass)
            elif op == "NOT":
                passed = not (child_pass[0] if child_pass else False)
            else:
                passed = False
            return {"pass": passed, "kind": kind, "label": label, "op": op, "child_results": child_results}

        return {"pass": False, "kind": kind, "label": label, "error": f"unknown criterion kind: {kind}"}
    except Exception as e:
        return {"pass": False, "kind": kind, "label": label, "error": f"evaluator_error: {e}"}


def _find_judge_score_in_trace(ctx: dict) -> float | None:
    for step in (ctx.get("steps") or {}).values():
        if step.get("ref") == "processor/llm-judge":
            out = step.get("output") or {}
            s = out.get("score")
            if s is not None:
                return s
    return None


def _apply_op(actual, op, expected):
    try:
        if op == ">":          return actual > expected
        if op == ">=":         return actual >= expected
        if op == "<":          return actual < expected
        if op == "<=":         return actual <= expected
        if op == "==":         return actual == expected
        if op == "!=":         return actual != expected
        if op == "in":         return actual in expected
        if op == "not_in":     return actual not in expected
        if op == "is_truthy":  return bool(actual)
        if op == "is_falsy":   return not bool(actual)
    except Exception:
        return False
    return False


def _semantic_similarities(text: str, topics: list[str]) -> dict[str, float]:
    """Fallback semantic: word-set Jaccard if no embedder available."""
    if not text or not topics:
        return {t: 0.0 for t in topics}
    text_words = set(re.findall(r"[a-z]{3,}", text.lower()))
    out = {}
    for t in topics:
        t_words = set(re.findall(r"[a-z]{3,}", t.lower()))
        if not t_words:
            out[t] = 0.0
            continue
        overlap = len(text_words & t_words)
        out[t] = round(overlap / len(t_words), 3)
    return out


def _invoke_tool(tool_id: str, target: Any, params: dict) -> dict:
    """Minimal tool dispatch. Currently supports json-schema-validator."""
    if tool_id == "tool/json-schema-validator":
        try:
            import jsonschema  # type: ignore[import]
        except ImportError:
            return {"pass": False, "error": "jsonschema not installed; pip install jsonschema"}
        schema_path = params.get("schema_path")
        if not schema_path:
            return {"pass": False, "error": "schema_path required"}
        try:
            schema = json.loads((ROOT / schema_path).read_text())
            jsonschema.Draft202012Validator(schema).validate(target)
            return {"pass": True}
        except jsonschema.ValidationError as e:
            return {"pass": False, "error": str(e)[:300]}
        except Exception as e:
            return {"pass": False, "error": f"tool_error: {e}"}
    return {"pass": False, "error": f"unknown tool: {tool_id}"}


# Re-rooted ROOT for tool calls
ROOT = Path(__file__).resolve().parent.parent


def run_step(step: dict, catalog: dict[str, dict], ctx: dict, *, simulate: bool) -> dict:
    """Run one pipeline step. Returns a step-result record."""
    started = time.monotonic()
    ref_id = step["ref"]
    artifact = catalog.get(ref_id) if not ref_id.startswith("$.") else catalog.get(resolve(ref_id, ctx))
    inputs = {k: resolve(v, ctx) for k, v in (step.get("inputs") or {}).items()}

    output: dict = {}
    simulated = simulate or artifact is None

    if simulated:
        # Stub: echo a structured response so the trace is meaningful.
        output = {
            "_simulated": True,
            "echo": inputs,
            "note": f"simulated run of step {step['id']!r} → {ref_id!r}",
        }
    elif step["kind"] == "rule_pack":
        # Deterministic: report which rules would fire over the input text.
        text = inputs.get("text", "")
        if isinstance(text, (dict, list)):
            text = json.dumps(text)
        elif not isinstance(text, str):
            text = str(text)
        fired = []
        for rule in artifact.get("rules", []) or []:
            pattern = rule.get("pattern")
            if pattern:
                try:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        fired.append({
                            "rule_id":     rule["id"],
                            "category":    rule.get("category"),
                            "severity":    rule.get("severity"),
                            "match_count": len(matches),
                            "first_match": str(matches[0])[:120] if matches else None,
                        })
                except re.error:
                    pass
        output = {"fired": fired, "pack": ref_id, "hit_count": len(fired)}
    elif step["kind"] == "processor":
        output = _run_processor(ref_id, inputs, artifact)
    elif step["kind"] == "pipeline":
        # Nested pipeline: run it with the resolved inputs and return its
        # output + a per-step trace summary.
        if artifact is None or artifact.get("type") != "pipeline":
            output = {"_error": f"step references {ref_id} which is not a pipeline"}
        else:
            sub_result = run_pipeline(artifact, inputs, simulate=False)
            output = {
                "sub_pipeline":      ref_id,
                "sub_output":        sub_result.get("output"),
                "sub_aggregate":     sub_result.get("success_aggregate"),
                "sub_criteria":      sub_result.get("success_criteria"),
                "sub_step_count":    len(sub_result.get("trace") or []),
                "sub_findings_total":sum(
                    len((s.get("output") or {}).get("fired") or [])
                    for s in (sub_result.get("trace") or [])
                ),
            }
    elif step["kind"] == "harness":
        # Deferred to the playground app; here we stub.
        output = {"_simulated": True, "echo": inputs, "harness": ref_id}
    elif step["kind"] == "tool":
        output = {"_simulated": True, "echo": inputs, "tool": ref_id}
    elif step["kind"] == "knowledge_pack":
        output = {"_simulated": True, "echo": inputs, "pack": ref_id}

    return {
        "step_id":   step["id"],
        "kind":      step["kind"],
        "ref":       ref_id,
        "input":     inputs,
        "output":    output,
        "ms":        round((time.monotonic() - started) * 1000, 2),
        "simulated": simulated,
    }


def run_pipeline(pipeline: dict, inputs: dict, *, simulate: bool) -> dict:
    global _CURRENT_CATALOG, _CURRENT_CTX
    catalog = load_catalog()
    ctx: dict[str, Any] = {"inputs": inputs, "steps": {}}
    _CURRENT_CATALOG = catalog
    _CURRENT_CTX     = ctx
    trace: list[dict] = []
    for step in pipeline.get("steps", []) or []:
        if "when" in step:
            cond = resolve(step["when"], ctx)
            if not cond:
                continue
        result = run_step(step, catalog, ctx, simulate=simulate)
        trace.append(result)
        ctx["steps"][step["id"]] = result

    last_output = trace[-1]["output"] if trace else {}

    # Evaluate composable success criteria.
    criteria = pipeline.get("success_criteria") or []
    criterion_results = [_evaluate_criterion(c, ctx) for c in criteria]
    aggregate_pass = all(r.get("pass") for r in criterion_results) if criterion_results else True

    return {
        "pipeline":           pipeline["id"],
        "inputs":             inputs,
        "trace":              trace,
        "output":             last_output,
        "success_criteria":   criterion_results,
        "success_aggregate":  aggregate_pass,
        "model":              os.environ.get("OH_MODEL", "simulated"),
        "frozen_at":          time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a pipeline manifest from the catalog.")
    ap.add_argument("pipeline_id", help="e.g. pipeline/research-entity")
    ap.add_argument("--inputs", default=None, help="Path to a JSON file with inputs.")
    ap.add_argument("--simulate", action="store_true", help="Force all steps to simulate.")
    args = ap.parse_args()

    catalog = load_catalog()
    pipeline = catalog.get(args.pipeline_id)
    if pipeline is None:
        sys.stderr.write(f"unknown pipeline {args.pipeline_id!r}\n")
        return 1
    if pipeline.get("type") != "pipeline":
        sys.stderr.write(f"{args.pipeline_id!r} is not a pipeline\n")
        return 1

    inputs = json.loads(Path(args.inputs).read_text()) if args.inputs else {}
    result = run_pipeline(pipeline, inputs, simulate=args.simulate)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
