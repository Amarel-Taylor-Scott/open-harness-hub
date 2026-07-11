#!/usr/bin/env python3
"""scripts.anti_primitive_store — the NEGATIVE-KNOWLEDGE / "known-bad, don't-mint" store of the primitive
supply chain (2026-07-08). The foundry already CAPTURES counterexamples per-rule (RuleCandidate.counterexamples),
per-body (primitive_security_gate quarantines), and per-card (lint_primitives hard-fail smells) — but it never
AGGREGATED them into one place the minter can consult before spending tokens re-deriving a primitive we already
know is wrong. This module is that place: a curated seed set of anti-primitives PLUS an aggregator that mints more
from the real capture streams, and a multi-axis matcher that lets the foundry STOP re-minting known-bad.

An anti-primitive is negative knowledge, not truth: it says "do NOT build a primitive that does X, because X has a
known failure mode Y, caught by verifier Z". Every row is candidate-only (serves_truth=false); the store advises the
minter, it never promotes or blocks by fiat.

Reuse-first: the counterexample/failure evidence already exists — RuleCandidate.schema.json.counterexamples,
scripts.primitive_security_gate (pass|fail|quarantine), scripts.lint_primitives (smells). This module AGGREGATES
those into anti-primitive rows and adds the matcher; it does not re-derive them. Deterministic (no timestamps in the
core rows; canonical_id for identity; sorted-key JSONL on write). candidate; serves_truth=false.

    python3 scripts/anti_primitive_store.py --self-test
    python3 scripts/anti_primitive_store.py --report            # print the seed anti-primitives
    python3 scripts/anti_primitive_store.py --build             # aggregate from the live lint/security streams + persist
    python3 scripts/anti_primitive_store.py --check some_card.json   # flag one candidate card against the store
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, resource  # noqa: E402

_install()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  DATA-plane ids: never hashlib here
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"anti_primitive_store requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
RECORD_TYPE = "anti_primitive"
ANTI_PRIMITIVE_SCHEMA_VERSION = "anti_primitive_store_v1"
STAGED_FILENAME = "anti_primitives.jsonl"
_DATA_SUBDIR = "data/dev-intel/anti_primitive_store"
_SEVERITIES: tuple[str, ...] = ("low", "med", "high")            # task-locked scale (NOT the gate's "medium")
_SEV_RANK: dict[str, int] = {"low": 0, "med": 1, "high": 2}
#: short/functional words dropped when tokenizing STRUCTURED fields (applies_to/edge/mechanism) — never the text
#: surface, which is matched by regex, not tokens.
_STOP: frozenset[str] = frozenset(
    "the and for with from into that this are was not use using when only on by in of to is as at an or if it "
    "be do no so a an the".split())


# ── tokenization (single source; used only on structured fields, never the free-text surface) ─────────────────
def _tok(s: Any) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", str(s).lower()) if len(t) >= 2 and t not in _STOP}


def _token_set(value: Any) -> set[str]:
    """Token set of a str / list / None structured value, plus the whole-value normalized form (so 'entity.merge'
    contributes {entity, merge, entity_merge})."""
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        out: set[str] = set()
        for v in value:
            out |= _token_set(v)
        return out
    out = _tok(value)
    whole = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    if whole:
        out.add(whole)
    return out


def _ordered_tokens(s: Any) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", str(s).lower()) if len(t) >= 3 and t not in _STOP]


def _slug(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


def _pattern_from_phrase(phrase: str) -> str:
    """A loose, order-preserving regex from a phrase's top significant tokens — good enough to recognize a
    candidate that would reproduce the described bad behavior (advisory match, not a proof)."""
    toks = _ordered_tokens(phrase)[:3]
    return ".{0,40}".join(re.escape(t) for t in toks) if toks else ""


# ── candidate-card feature extraction (robust to many card shapes) ────────────────────────────────────────────
_FAMILY_FIELDS = ("applies_to", "family", "families", "domain", "domains", "component_family",
                  "component_families", "tags", "category", "categories", "record_type", "kind", "stage", "layer")
_EDGE_FIELDS = ("input_edge", "output_edge", "edges", "input_edges", "output_edges", "in_edge", "out_edge",
                "input_type", "output_type")
_MECH_FIELDS = ("mechanism", "mechanisms", "method", "methods", "strategy", "approach", "lift_reason", "technique")
_TEXT_FIELDS = ("title", "name", "impl_name", "description", "blackbox", "summary", "rationale", "decision",
                "observed_decision", "must_not_decide", "notebook_step", "cell", "code", "step", "body",
                "executable_body", "goal", "intent")


def _collect(candidate: dict[str, Any], fields: tuple[str, ...]) -> set[str]:
    out: set[str] = set()
    for f in fields:
        if f in candidate:
            out |= _token_set(candidate[f])
    return out


def _family_tokens(c: dict[str, Any]) -> set[str]:
    return _collect(c, _FAMILY_FIELDS)


def _edge_tokens(c: dict[str, Any]) -> set[str]:
    return _collect(c, _EDGE_FIELDS)


def _mech_signal_tokens(c: dict[str, Any]) -> set[str]:
    """The candidate's structural 'how it works' signal — its mechanism AND its typed edges (an anti-primitive's
    forbidden edge is a mechanism-level tell)."""
    return _collect(c, _MECH_FIELDS) | _edge_tokens(c)


def _text_surface(c: dict[str, Any]) -> str:
    parts: list[str] = []
    for f in _TEXT_FIELDS:
        v = c.get(f)
        if isinstance(v, (list, tuple)):
            parts.extend(str(x) for x in v)
        elif v is not None:
            parts.append(str(v))
    for f in ("plan_steps", "steps", "cells", "notebook_steps"):
        v = c.get(f)
        if isinstance(v, (list, tuple)):
            parts.extend(json.dumps(x) if isinstance(x, dict) else str(x) for x in v)
    return " \n ".join(parts).lower()


# ── the curated SEED anti-primitives (real negative knowledge; extend a row, never a rewrite) ─────────────────
#: each: {anti_primitive_id, description, applies_to[], failure_mode, severity(low|med|high), verifier, pattern,
#: evidence_refs[]} (+ optional mechanism / bad_edges for the structural axis).
ANTI_PRIMITIVE_SEEDS: list[dict[str, Any]] = [
    {
        "anti_primitive_id": "anti.entity.person_trust_merge",
        "description": "Do NOT merge a person entity with a trust entity merely because the trust is named after "
                       "the person (shared surname / matching name). A trust is a distinct legal entity; name "
                       "similarity is not a strong shared identifier.",
        "applies_to": ["entity_resolution", "entity.merge", "canonical_entity", "dedupe_cluster",
                       "object_entity_ref"],
        "failure_mode": "false_entity_merge",
        "severity": "high",
        "verifier": "entity_merge_requires_shared_strong_identifier_not_name_similarity",
        "pattern": r"merg\w*.{0,80}person.{0,80}trust|merg\w*.{0,80}trust.{0,80}person|"
                   r"(trust|estate|foundation).{0,40}named after.{0,40}(person|individual|him|her|owner)",
        "mechanism": "name_similarity_merge",
        "bad_edges": ["Person", "Trust", "PersonEntity", "TrustEntity", "Estate"],
        "evidence_refs": [{"kind": "principle", "value": "entity-resolution: name match != identity"}],
    },
    {
        "anti_primitive_id": "anti.kaggle.target_encoding_full_train",
        "description": "Do NOT fit target/mean encoding on the full training set before cross-validation. The "
                       "encoding leaks the target into features; fit it INSIDE each CV fold on the fold's train "
                       "split only.",
        "applies_to": ["kaggle", "feature_engineering", "ml.preprocessing", "target_encoding", "notebook"],
        "failure_mode": "target_leakage",
        "severity": "high",
        "verifier": "target_encoding_fit_inside_cv_fold_only",
        "pattern": r"target[\s_]*encod\w*.{0,80}(full|entire|whole|all)[\s_]*(train|training)|"
                   r"(fit|comput\w*|appl\w*).{0,40}target[\s_]*encod\w*.{0,60}before.{0,20}"
                   r"(cv|cross[\s_-]*validation|split|fold)|"
                   r"target[\s_]*encod\w*.{0,60}(before|prior to).{0,20}(cv|cross|split|fold)",
        "mechanism": "target_encoding",
        "bad_edges": [],
        "evidence_refs": [{"kind": "principle", "value": "kaggle: encode inside the fold, never on full train"}],
    },
    {
        "anti_primitive_id": "anti.ml.leakage_test_in_train",
        "description": "Do NOT fit scalers/imputers/encoders (or any target-derived statistic) on the whole "
                       "dataset before the train/test split, and never let test rows influence training "
                       "statistics — that is train/test leakage.",
        "applies_to": ["ml.preprocessing", "data_split", "feature_engineering", "cross_validation", "pipeline"],
        "failure_mode": "train_test_leakage",
        "severity": "high",
        "verifier": "fit_transformers_on_train_split_only_after_split",
        "pattern": r"(fit|scal\w*|normali[sz]\w*|imput\w*|encod\w*|standardi[sz]\w*).{0,80}"
                   r"(whole|full|entire|all|complete).{0,20}(data|dataset|set).{0,80}"
                   r"(before|prior to|then).{0,20}(train[\s_/-]*test|split)|"
                   r"test.{0,30}(rows|data|samples).{0,40}(in|into|leak\w*|influenc\w*|during).{0,20}"
                   r"(train|training|fit)",
        "mechanism": "preprocessing_before_split",
        "bad_edges": [],
        "evidence_refs": [{"kind": "principle", "value": "split BEFORE fit; test never informs train"}],
    },
    {
        "anti_primitive_id": "anti.tool.overprivileged_shell",
        "description": "Do NOT select an unrestricted shell/subprocess tool when a scoped capability (e.g. a "
                       "file.exists() check) suffices. Least-privilege: pick the narrowest tool that answers the "
                       "question.",
        "applies_to": ["tool_selection", "agent.tool", "capability_selection", "action", "routing"],
        "failure_mode": "over_privileged_tool_choice",
        "severity": "med",
        "verifier": "least_privilege_scoped_capability_over_shell",
        "pattern": r"(unrestricted|arbitrary|overprivileged|over-privileged|general[\s-]*purpose|full)\s*shell|"
                   r"\bshell\b.{0,80}\bfile[\s._]*exists?\b|"
                   r"(subprocess|os\.system|os\.popen)\b.{0,80}(exist|\bls\b|\btest -[ef]\b)",
        "mechanism": "shell_tool_selection",
        "bad_edges": ["UnrestrictedShell", "ShellCommand"],
        "evidence_refs": [{"kind": "principle", "value": "least-privilege tool admission"}],
    },
    {
        "anti_primitive_id": "anti.security.dynamic_exec_from_input",
        "description": "Do NOT build a primitive that dynamically executes/evaluates untrusted input "
                       "(eval/exec/__import__ over request/user/payload). This is arbitrary code execution — the "
                       "security gate quarantines it.",
        "applies_to": ["security", "code_generation", "action", "tool", "untrusted_input"],
        "failure_mode": "arbitrary_code_execution",
        "severity": "high",
        "verifier": "no_dynamic_exec_of_untrusted_input",
        "pattern": r"\b(eval|exec)\s*\([^)]*(input|request|user|payload|param|arg|body|prompt|expr)|"
                   r"\b(eval|exec)\s*\(\s*(user_input|request|input|payload|prompt)|"
                   r"__import__\s*\(|compile\s*\([^)]*[\"']exec[\"']",
        "mechanism": "dynamic_exec",
        "bad_edges": [],
        "evidence_refs": [{"kind": "gate", "value": "primitive_security_gate: dynamic_exec -> quarantine"}],
    },
]


# ── row finalization + dedup ──────────────────────────────────────────────────────────────────────────────────
def _finalize_row(raw: dict[str, Any], *, origin: str) -> dict[str, Any]:
    """Stamp an anti-primitive row: sort structured fields, mint the canonical dedupe key, apply the boundary.
    Deterministic (no timestamp; canonical_id over stable parts)."""
    applies_to = sorted({str(a) for a in (raw.get("applies_to") or [])})
    pattern = raw.get("pattern") or ""
    anti_id = str(raw["anti_primitive_id"])
    severity = raw.get("severity", "med")
    if severity not in _SEVERITIES:                       # defensive clamp for minted rows; seeds are asserted
        severity = "med"
    dedupe_key = canonical_id("antikey", anti_id, pattern, "|".join(applies_to))
    return {
        "record_type": RECORD_TYPE,
        "schema_version": ANTI_PRIMITIVE_SCHEMA_VERSION,
        "anti_primitive_id": anti_id,
        "dedupe_key": dedupe_key,
        "description": raw.get("description", ""),
        "applies_to": applies_to,
        "failure_mode": raw.get("failure_mode", "unspecified"),
        "severity": severity,
        "verifier": raw.get("verifier", ""),
        "pattern": pattern,
        "mechanism": raw.get("mechanism", ""),
        "bad_edges": sorted({str(e) for e in (raw.get("bad_edges") or [])}),
        "evidence_refs": raw.get("evidence_refs", []),
        "origin": origin,
        **BOUNDARY,
    }


def _dedup(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedup by the canonical dedupe_key, preserving first-seen order (seeds precede minted, so a seed wins)."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for r in rows:
        k = r["dedupe_key"]
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def anti_primitive_seed_rows() -> list[dict[str, Any]]:
    """The finalized seed store (the curated negative knowledge)."""
    return [_finalize_row(s, origin="seed") for s in ANTI_PRIMITIVE_SEEDS]


# ── the matcher: does a candidate REPRODUCE a known anti-primitive? ────────────────────────────────────────────
def check_against_anti_primitives(candidate: dict[str, Any],
                                  store: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Multi-axis match of a candidate card against the anti-primitive store so the foundry STOPS re-minting
    known-bad. A candidate is flagged when it reproduces the anti-pattern, detected by EITHER:
      (1) pattern    — the anti-primitive's regex matches the candidate's free-text surface (strongest signal), OR
      (2) structural — the candidate is IN SCOPE (applies_to overlap) AND exhibits the anti-primitive's MECHANISM
                       or a forbidden typed EDGE (mechanism/edge overlap).
    The `edge` and `applies_to` overlaps are reported in matched_axes for explanation. Returns [] for a clean
    candidate. Pure + deterministic; hits are advisory (candidate-only), never a hard block."""
    rows = store if store is not None else anti_primitive_seed_rows()
    text = _text_surface(candidate)
    fams = _family_tokens(candidate)
    mech_sig = _mech_signal_tokens(candidate)
    edges = _edge_tokens(candidate)
    hits: list[dict[str, Any]] = []
    for anti in rows:
        pat = anti.get("pattern") or ""
        pattern_hit = bool(pat and re.search(pat, text, re.IGNORECASE | re.DOTALL))
        applies = _token_set(anti.get("applies_to"))
        applies_hit = bool(applies & fams)
        struct = _token_set(anti.get("mechanism")) | _token_set(anti.get("bad_edges"))
        mech_hit = bool(struct & mech_sig)
        edge_hit = bool((_token_set(anti.get("bad_edges")) & edges) or (applies & edges))
        flagged = pattern_hit or (applies_hit and mech_hit)
        if not flagged:
            continue
        axes = ([("pattern")] if pattern_hit else []) + (["applies_to"] if applies_hit else []) \
            + (["edge"] if edge_hit else []) + (["mechanism"] if mech_hit else [])
        hits.append({
            "anti_primitive_id": anti["anti_primitive_id"],
            "dedupe_key": anti.get("dedupe_key"),
            "severity": anti.get("severity", "med"),
            "failure_mode": anti.get("failure_mode"),
            "verifier": anti.get("verifier"),
            "origin": anti.get("origin", "seed"),
            "matched_axes": axes,
            "reason": f"{anti['anti_primitive_id']} matched via {'+'.join(axes)}: "
                      f"{str(anti.get('description', ''))[:140]}",
            **BOUNDARY,
        })
    hits.sort(key=lambda h: (-_SEV_RANK.get(h["severity"], 1), h["anti_primitive_id"]))
    return hits


# ── aggregation: mint anti-primitives from the real capture streams ───────────────────────────────────────────
_LINT_HARD_FAIL_SMELLS: frozenset[str] = frozenset({
    "no_executable_body", "body_unparseable", "missing_routing_description", "missing_io_typing",
    "undeclared_side_effect_no_permission_manifest", "token_bloat_heavy"})
_LINT_CRITICAL_SMELLS: frozenset[str] = frozenset({"no_executable_body", "body_unparseable"})
_LINT_SMELL_PATTERN: dict[str, str] = {
    "undeclared_side_effect_no_permission_manifest": r"\b(subprocess|os\.system|eval\s*\(|exec\s*\(|__import__)\b"}
#: security-gate severity (critical/high/medium/low) -> the task-locked low|med|high scale
_SEC_SEV: dict[str, str] = {"critical": "high", "high": "high", "medium": "med", "low": "low"}
_SEC_FLAG_PATTERN: dict[str, str] = {
    "dynamic_exec": r"\b(eval|exec)\s*\(",
    "unsafe_deserialize": r"\b(pickle|marshal)\.(loads?|load)\b|yaml\.load\s*\((?![^)]*SafeLoader)",
    "network": r"\b(requests|httpx|urllib|socket|http\.client)\b",
    "subprocess_or_shell": r"\b(subprocess|os\.system|os\.popen)\b",
    "environment_read": r"\bos\.environ\b|\bgetenv\b",
}


def _mint_from_rule_counterexample(rule: dict[str, Any]) -> list[dict[str, Any]]:
    """A RuleCandidate.counterexamples entry is negative knowledge: 'for these inputs the rule must NOT decide X'.
    Mint one anti-primitive per counterexample (the wrong decision a future primitive must not reproduce)."""
    rid = str(rule.get("rule_candidate_id", ""))
    rtype = str(rule.get("rule_type", "rule"))
    rclass = str(rule.get("rule_class", ""))
    scope = str(rule.get("scope", ""))
    fields = rule.get("input_fields") or []
    traces = rule.get("distilled_from_trace_ids") or []
    out: list[dict[str, Any]] = []
    for ce in (rule.get("counterexamples") or []):
        must = str(ce.get("must_not_decide", "")).strip()
        inputs = str(ce.get("inputs", "")).strip()
        exp = str(ce.get("expected_behavior", "abstain"))
        if not must:
            continue
        applies = sorted({t for t in ([_slug(rtype), _slug(rclass)] + [_slug(f) for f in fields]
                                      + list(_tok(scope))) if t})
        out.append(_finalize_row({
            "anti_primitive_id": f"anti.rule.{_slug(rtype)}.{_slug(must)[:40]}",
            "description": f"Do NOT {must} (rule '{rtype}' counterexample; expected behavior: {exp}). "
                           f"Inputs: {inputs[:160]}",
            "applies_to": applies,
            "failure_mode": "rule_counterexample_violation",
            "severity": "high" if rclass == "truth_serving" else "med",
            "verifier": f"rule_{_slug(rtype)}_must_{_slug(exp)}_on_this_input",
            "pattern": _pattern_from_phrase(must),
            "mechanism": _slug(rtype),
            "evidence_refs": [{"kind": "rule_candidate", "value": rid},
                              {"kind": "counterexample_inputs", "value": inputs[:200]},
                              *[{"kind": "trace", "value": str(t)} for t in traces[:5]]],
        }, origin="rule_counterexample"))
    return out


def _mint_from_quarantine(report: dict[str, Any]) -> list[dict[str, Any]]:
    """A primitive_security_gate report with status quarantine|fail is negative knowledge about generated code:
    'a body exhibiting this finding must not be minted'. Mint one anti-primitive per finding."""
    status = str(report.get("status", ""))
    if status not in ("quarantine", "fail"):
        return []
    handle = str(report.get("artifact_hash") or report.get("artifact_name", ""))
    pid = report.get("primitive_id")
    out: list[dict[str, Any]] = []
    for f in (report.get("findings") or []):
        rule = str(f.get("rule", ""))
        flag = rule.split(":", 1)[1] if ":" in rule else rule
        sev = _SEC_SEV.get(str(f.get("severity", "high")), "med")
        if status == "quarantine" and f.get("severity") == "critical":
            sev = "high"
        out.append(_finalize_row({
            "anti_primitive_id": f"anti.security.{_slug(flag)}",
            "description": f"Security gate {status}: a generated body exhibits '{flag}' — "
                           f"{str(f.get('detail', ''))[:160]}",
            "applies_to": ["security", "code_generation", "generated_body"],
            "failure_mode": flag,
            "severity": sev,
            "verifier": "primitive_security_gate_pass_required",
            "pattern": _SEC_FLAG_PATTERN.get(flag) or _pattern_from_phrase(flag.replace("_", " ")),
            "mechanism": _slug(flag),
            "evidence_refs": [{"kind": "security_report", "value": handle}, {"kind": "finding", "value": rule},
                              *([{"kind": "primitive_id", "value": str(pid)}] if pid else [])],
        }, origin="security_quarantine"))
    return out


def _mint_from_lint_finding(finding: dict[str, Any]) -> list[dict[str, Any]]:
    """A lint_primitives per-card finding with a HARD-FAIL smell is negative knowledge about card shape: 'a card
    carrying this smell must not be minted/served'. Mint one anti-primitive per hard-fail smell."""
    pid = finding.get("primitive_id")
    out: list[dict[str, Any]] = []
    for sm in (finding.get("smells") or []):
        if sm not in _LINT_HARD_FAIL_SMELLS:
            continue
        out.append(_finalize_row({
            "anti_primitive_id": f"anti.lint.{_slug(sm)}",
            "description": f"Lint hard-fail: a primitive card with smell '{sm}' must not be minted or served "
                           f"until the smell is resolved.",
            "applies_to": ["primitive_card", "code_generation", "card_quality"],
            "failure_mode": sm,
            "severity": "high" if sm in _LINT_CRITICAL_SMELLS else "med",
            "verifier": "lint_primitives_no_hard_fail_smell",
            "pattern": _LINT_SMELL_PATTERN.get(sm, ""),
            "mechanism": _slug(sm),
            "evidence_refs": [{"kind": "lint_finding", "value": str(pid)}, {"kind": "smell", "value": sm}],
        }, origin="lint_hard_fail"))
    return out


def aggregate_counterexamples(rule_candidates: list[dict[str, Any]] | None = None,
                              lint_findings: list[dict[str, Any]] | None = None,
                              quarantines: list[dict[str, Any]] | None = None,
                              *, include_seeds: bool = True) -> list[dict[str, Any]]:
    """Mint anti-primitive rows from the real capture streams (RuleCandidate counterexamples + security-gate
    quarantine/fail reasons + lint hard-fail smells) and combine them with the curated seeds, deduped by the
    canonical key. Deterministic given deterministic inputs; every row candidate-only."""
    minted: list[dict[str, Any]] = []
    for r in (rule_candidates or []):
        minted += _mint_from_rule_counterexample(r)
    for f in (lint_findings or []):
        minted += _mint_from_lint_finding(f)
    for q in (quarantines or []):
        minted += _mint_from_quarantine(q)
    rows = (anti_primitive_seed_rows() if include_seeds else []) + minted
    return _dedup(rows)


# ── persistence (append, candidate-only, deterministic bytes) ─────────────────────────────────────────────────
def persist_anti_primitives(rows: list[dict[str, Any]], path: Path | str | None = None) -> Path:
    out_path = Path(path) if path else (resource(_DATA_SUBDIR) / STAGED_FILENAME)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return out_path


def build_store(*, persist: bool = True, path: Path | str | None = None) -> list[dict[str, Any]]:
    """Best-effort aggregation from the LIVE streams: lint every live pack card, security-gate every live body,
    read a rule-candidate receipt if present, then aggregate + persist. Each source is optional (wrapped) so the
    build never crashes on a missing dependency."""
    lint_findings: list[dict[str, Any]] = []
    quarantines: list[dict[str, Any]] = []
    rule_candidates: list[dict[str, Any]] = []
    try:
        from scripts.lint_primitives import lint_card, load_live_cards
        from scripts.primitive_package_contract import formalize_card
        for c in load_live_cards():
            lc = lint_card(formalize_card(c))
            if any(s in _LINT_HARD_FAIL_SMELLS for s in lc.get("smells", [])):
                lint_findings.append(lc)
    except Exception:  # noqa: BLE001 — optional source
        pass
    try:
        from scripts.executable_pack_pool_sync import collect_pack_cards
        from scripts.primitive_security_gate import gate_card
        for c in collect_pack_cards():
            rep = gate_card(c)
            if rep.get("status") in ("quarantine", "fail"):
                quarantines.append(rep)
    except Exception:  # noqa: BLE001 — optional source
        pass
    rc_file = resource("data/dev-intel/source_to_primitive_foundry/real_world_loop/rule_candidates.jsonl")
    try:
        if rc_file.is_file():
            for line in rc_file.read_text().splitlines():
                if line.strip():
                    rule_candidates.append(json.loads(line))
    except Exception:  # noqa: BLE001 — optional source
        pass
    rows = aggregate_counterexamples(rule_candidates, lint_findings, quarantines)
    if persist:
        persist_anti_primitives(rows, path)
    return rows


# ── self-test (offline, deterministic, mutation-gated) ────────────────────────────────────────────────────────
def _fixture_cards() -> dict[str, dict[str, Any]]:
    """Representative candidate cards for each seed anti-pattern + a clean control + a text-free structural probe."""
    return {
        "person_trust": {
            "primitive_id": "prim:cand:pt", "title": "Merge person and eponymous trust",
            "description": "Merge a person entity with a trust entity because the trust is named after the person "
                           "and they share a surname.",
            "applies_to": ["entity_resolution", "entity.merge"],
            "input_edge": "PersonEntity", "output_edge": "MergedEntity", "mechanism": "name_similarity_merge"},
        "target_encoding": {
            "primitive_id": "prim:cand:te", "title": "Target-encode categoricals",
            "description": "Fit target encoding on the full training set, then run 5-fold cross-validation.",
            "applies_to": ["kaggle", "feature_engineering"],
            "input_edge": "TrainDataFrame", "output_edge": "EncodedFeatures", "mechanism": "target_encoding"},
        "leakage": {
            "primitive_id": "prim:cand:lk", "title": "Scale features",
            "description": "Scale and impute features using the whole dataset before the train/test split, so "
                           "test rows influence training statistics.",
            "applies_to": ["ml.preprocessing"], "mechanism": "preprocessing_before_split"},
        "overpriv": {
            "primitive_id": "prim:cand:op", "title": "Check a file",
            "description": "Select an unrestricted shell command to check whether a file exists instead of a "
                           "scoped file.exists().",
            "applies_to": ["tool_selection"], "mechanism": "shell_tool_selection"},
        "dynexec": {
            "primitive_id": "prim:cand:de", "title": "Evaluate expression",
            "description": "Evaluate the user-supplied expression to compute the result.",
            "applies_to": ["action"], "mechanism": "dynamic_eval",
            "executable_body": "def run(user_input):\n    return eval(user_input)\n"},
        "clean": {
            "primitive_id": "prim:cand:ok", "title": "Whitespace collapser",
            "description": "Collapse repeated whitespace in a raw string into single spaces and trim the ends.",
            "applies_to": ["text_normalization", "string_cleanup"],
            "input_edge": "RawString", "output_edge": "CleanString", "mechanism": "regex_whitespace_collapse",
            "executable_body": "import re\ndef collapse(s):\n    return re.sub(r'\\s+', ' ', s).strip()\n"},
        "structural": {   # no regex-triggering prose — must be caught by applies_to + mechanism/edge alone
            "primitive_id": "prim:cand:st", "title": "Combine records",
            "description": "Combine two records into one canonical record.",
            "applies_to": ["entity.merge"], "input_edge": "Person", "output_edge": "Trust",
            "mechanism": "name_similarity_merge"},
    }


def _detection_holds(matcher: Callable[..., list[dict[str, Any]]]) -> bool:
    """The core detection CONTRACT, factored out so the mutation gate can run it under BOTH the real matcher (must
    hold) and a defect-injected matcher that always returns [] (must NOT hold)."""
    store = anti_primitive_seed_rows()
    fx = _fixture_cards()
    hpt = matcher(fx["person_trust"], store)
    hte = matcher(fx["target_encoding"], store)
    hcl = matcher(fx["clean"], store)
    return (any(h["anti_primitive_id"] == "anti.entity.person_trust_merge" and h["severity"] == "high"
                for h in hpt)
            and any(h["anti_primitive_id"] == "anti.kaggle.target_encoding_full_train" and h["severity"] == "high"
                    for h in hte)
            and hcl == [])


def self_test() -> int:
    import tempfile  # noqa: PLC0415  (temp path only under test; core stays deterministic)
    checks: list[tuple[str, bool]] = []
    seeds = anti_primitive_seed_rows()
    fx = _fixture_cards()

    ids = {r["anti_primitive_id"] for r in seeds}
    required = {"anti.entity.person_trust_merge", "anti.kaggle.target_encoding_full_train",
                "anti.ml.leakage_test_in_train", "anti.tool.overprivileged_shell",
                "anti.security.dynamic_exec_from_input"}
    checks.append(("seed set includes the 5 required anti-primitives; all candidate-only + valid severity",
                   required <= ids and all(r["serves_truth"] is False and r["candidate"] is True
                                           and r["severity"] in _SEVERITIES for r in seeds)))

    # (1) the two mandated FLAG cases — right id + right severity
    hpt = check_against_anti_primitives(fx["person_trust"], seeds)
    checks.append(("person+trust merge card FLAGGED as anti.entity.person_trust_merge (severity high)",
                   any(h["anti_primitive_id"] == "anti.entity.person_trust_merge" and h["severity"] == "high"
                       for h in hpt)))
    hte = check_against_anti_primitives(fx["target_encoding"], seeds)
    checks.append(("target-encoding-before-CV step FLAGGED as anti.kaggle.target_encoding_full_train (high)",
                   any(h["anti_primitive_id"] == "anti.kaggle.target_encoding_full_train"
                       and h["severity"] == "high" for h in hte)))
    # (2) the clean control returns []
    checks.append(("clean candidate returns [] (no false positive)",
                   check_against_anti_primitives(fx["clean"], seeds) == []))
    # remaining seeds each detect their representative bad card
    checks.append(("leakage card flagged (anti.ml.leakage_test_in_train)",
                   any(h["anti_primitive_id"] == "anti.ml.leakage_test_in_train"
                       for h in check_against_anti_primitives(fx["leakage"], seeds))))
    checks.append(("overprivileged-shell card flagged (anti.tool.overprivileged_shell, med)",
                   any(h["anti_primitive_id"] == "anti.tool.overprivileged_shell" and h["severity"] == "med"
                       for h in check_against_anti_primitives(fx["overpriv"], seeds))))
    checks.append(("dynamic-exec card flagged (anti.security.dynamic_exec_from_input, high)",
                   any(h["anti_primitive_id"] == "anti.security.dynamic_exec_from_input"
                       and h["severity"] == "high" for h in check_against_anti_primitives(fx["dynexec"], seeds))))
    # multi-axis: a card with NO regex-matching prose is still caught by applies_to + mechanism/edge
    hst = check_against_anti_primitives(fx["structural"], seeds)
    checks.append(("structural match (applies_to+mechanism/edge, NO regex text) still flags known-bad",
                   any(h["anti_primitive_id"] == "anti.entity.person_trust_merge" for h in hst)
                   and hst and "pattern" not in hst[0]["matched_axes"]
                   and {"mechanism"} <= set(hst[0]["matched_axes"])))

    # (3) aggregate mints from a fake RuleCandidate counterexample
    fake_rule = {
        "schema_version": "RuleCandidate", "rule_candidate_id": "rc-abc", "rule_type": "source_authority_rule",
        "rule_class": "truth_serving", "scope": "entity merge on global_public facts",
        "input_fields": ["person_name", "trust_name"],
        "counterexamples": [{"inputs": "'John Roe' vs 'John Roe Family Trust'",
                             "must_not_decide": "merge person into trust by shared surname",
                             "expected_behavior": "abstain"}],
        "distilled_from_trace_ids": ["tr-1", "tr-2"]}
    agg = aggregate_counterexamples([fake_rule], None, None)
    minted_rule = [r for r in agg if r["origin"] == "rule_counterexample"]
    checks.append(("aggregate mints an anti-primitive from a RuleCandidate counterexample (candidate-only, "
                   "evidence-linked)",
                   len(minted_rule) == 1 and minted_rule[0]["serves_truth"] is False
                   and minted_rule[0]["severity"] == "high"
                   and any(e.get("kind") == "rule_candidate" and e.get("value") == "rc-abc"
                           for e in minted_rule[0]["evidence_refs"])))
    # the minted row is itself matchable — the foundry would now STOP re-minting that exact bad primitive
    remint = {"description": "merge person into trust by shared surname", "applies_to": ["entity_merge"],
              "mechanism": "shared_surname_merge"}
    checks.append(("minted anti-primitive round-trips: it flags a candidate that reproduces it",
                   any(h["origin"] == "rule_counterexample"
                       for h in check_against_anti_primitives(remint, agg))))

    # aggregate mints from a security quarantine + a lint hard-fail
    quarantines = [{"status": "quarantine", "artifact_name": "gen_body", "artifact_hash": "artifact-deadbeef",
                    "primitive_id": "prim:q:1",
                    "findings": [{"rule": "code_flag:dynamic_exec", "severity": "critical",
                                  "detail": "eval on request input"}]}]
    lint_findings = [{"primitive_id": "prim:l:1", "impl_name": "x", "quality_score": 10,
                      "smells": ["body_unparseable", "missing_io_typing", "missing_title"]}]
    agg2 = aggregate_counterexamples(None, lint_findings, quarantines)
    checks.append(("aggregate mints from a security quarantine (critical->high) AND a lint hard-fail",
                   any(r["origin"] == "security_quarantine" and r["severity"] == "high"
                       and r["anti_primitive_id"] == "anti.security.dynamic_exec" for r in agg2)
                   and any(r["origin"] == "lint_hard_fail" and r["failure_mode"] == "body_unparseable"
                           for r in agg2)))
    # a soft (missing_title) smell is NOT hard-fail -> not minted
    checks.append(("only HARD-FAIL lint smells mint anti-primitives (missing_title is ignored)",
                   not any(r["anti_primitive_id"] == "anti.lint.missing_title" for r in agg2)))

    # dedup by canonical key: the same counterexample twice collapses to one row
    dup = aggregate_counterexamples([fake_rule, dict(fake_rule)], None, None, include_seeds=False)
    dup_keys = [r["dedupe_key"] for r in dup]
    checks.append(("dedup by canonical key: duplicate counterexample collapses to one row",
                   len(dup) >= 1 and len(dup_keys) == len(set(dup_keys))))

    # (4) determinism: identical inputs -> byte-identical rows
    checks.append(("aggregate is deterministic (identical inputs -> identical rows twice)",
                   aggregate_counterexamples([fake_rule], lint_findings, quarantines)
                   == aggregate_counterexamples([fake_rule], lint_findings, quarantines)))

    # persistence: candidate-only + deterministic bytes on a fresh path
    with tempfile.TemporaryDirectory() as td:
        pa = Path(td) / "a.jsonl"
        pb = Path(td) / "b.jsonl"
        persist_anti_primitives(agg, pa)
        persist_anti_primitives(agg, pb)
        txt_a, txt_b = pa.read_text(), pb.read_text()
        parsed = [json.loads(ln) for ln in txt_a.splitlines() if ln.strip()]
        checks.append(("persisted JSONL is candidate-only; identical rows -> byte-identical file",
                       txt_a == txt_b and len(parsed) == len(agg)
                       and all(r["candidate"] is True and r["serves_truth"] is False
                               and r["record_type"] == RECORD_TYPE for r in parsed)))

    # MUTATION GATE: the detection contract must hold under the REAL matcher and FAIL under an injected defect
    checks.append(("real matcher satisfies the detection contract (flags both seeds, clean == [])",
                   _detection_holds(check_against_anti_primitives)))
    checks.append(("MUTATION GATE: a defect-injected matcher that always returns [] FAILS the contract "
                   "-> a real defect drives exit 1",
                   _detection_holds(check_against_anti_primitives)
                   and not _detection_holds(lambda c, store=None: [])))

    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    print(("PASS" if ok else "FAIL") + f" - anti_primitive_store: {len(ANTI_PRIMITIVE_SEEDS)} seed anti-primitives "
          f"+ aggregation from rule counterexamples / security quarantines / lint hard-fails; multi-axis matcher "
          f"(applies_to/edge/mechanism/regex) STOPS re-minting known-bad. Candidate-only, deterministic, "
          f"mutation-gated. serves_truth=false.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true", help="print the seed anti-primitives")
    ap.add_argument("--build", action="store_true", help="aggregate from the live lint/security streams + persist")
    ap.add_argument("--check", metavar="CARD_JSON", default=None,
                    help="path to a candidate card JSON; prints the anti-primitive hits (or [])")
    ap.add_argument("--out", default=None, help="override the persist path for --build")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.report:
        print(json.dumps(anti_primitive_seed_rows(), indent=2, sort_keys=True))
        return 0
    if args.build:
        rows = build_store(persist=True, path=args.out)
        origins: dict[str, int] = {}
        for r in rows:
            origins[r["origin"]] = origins.get(r["origin"], 0) + 1
        print(json.dumps({"anti_primitives": len(rows), "by_origin": origins,
                          "path": str(resource(_DATA_SUBDIR) / STAGED_FILENAME if not args.out else args.out),
                          **BOUNDARY}, indent=2, sort_keys=True))
        return 0
    if args.check:
        card = json.loads(Path(args.check).read_text())
        hits = check_against_anti_primitives(card)
        print(json.dumps(hits, indent=2, sort_keys=True))
        return 1 if hits else 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
