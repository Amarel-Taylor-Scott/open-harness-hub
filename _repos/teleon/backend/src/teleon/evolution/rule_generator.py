"""src.teleon.evolution.rule_generator — GENERATE a deterministic rule from LLM decisions, validate it LOSSLESSLY.

Closes the "real distillation" seam: today a fork is a governed SPEC; this uses a LIVE model to GENERATE the actual rule
the fork represents, then PROVES it on held-out examples before accepting (the lossless-distillation + lift law — a
distilled rule replaces the LLM ONLY if it matches on held-out; else it's rejected and the LLM stays, with lineage to the
rejected candidate). The rule is STRUCTURED JSON ({rules:[{if:[{field,op,value}], then}], default}) executed by a SAFE
deterministic interpreter — never eval'd code. serves_truth=false; Teleon layer.
"""
from __future__ import annotations

import json

_OPS = {
    "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
    "<": lambda a, b: _num(a) < _num(b), "<=": lambda a, b: _num(a) <= _num(b),
    ">": lambda a, b: _num(a) > _num(b), ">=": lambda a, b: _num(a) >= _num(b),
    "contains": lambda a, b: str(b).lower() in str(a).lower(),
    "startswith": lambda a, b: str(a).lower().startswith(str(b).lower()),
}


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def apply_rule(rule: dict, row: dict):
    """SAFE deterministic interpreter (no eval): first matching rule's `then`, else `default`."""
    for r in rule.get("rules", []):
        conds = r.get("if", [])
        if conds and all(c.get("field") in row and _OPS.get(c.get("op"), lambda a, b: False)(row[c["field"]], c.get("value")) for c in conds):
            return r.get("then")
    return rule.get("default")


def _prompt(train: list) -> str:
    fields = sorted({k for x, _ in train for k in x})
    return ("Given these (input -> label) examples, output ONLY a JSON deterministic rule of the form "
            '{"rules":[{"if":[{"field":F,"op":O,"value":V}],"then":LABEL}],"default":LABEL} where O is one of '
            f'==,!=,<,<=,>,>=,contains,startswith and F is one of {fields}. Examples:\n'
            + "\n".join(f"  {json.dumps(x)} -> {y}" for x, y in train))


def _parse_rule(text: str) -> dict | None:
    try:
        s = text[text.index("{"):text.rindex("}") + 1]
        rule = json.loads(s)
        return rule if isinstance(rule.get("rules"), list) else None
    except Exception:  # noqa: BLE001
        return None


def generate_rule(examples: list, *, llm, holdout_frac: float = 0.34, accept_at: float = 0.9) -> dict:
    """examples = [(input_dict, label), ...]. Split train/holdout; LLM proposes a structured rule from train; apply it
    DETERMINISTICALLY to holdout; accept ONLY if holdout accuracy >= accept_at (lossless lift gate). llm(prompt)->str."""
    n_hold = max(1, int(len(examples) * holdout_frac))
    holdout, train = examples[:n_hold], examples[n_hold:]
    if not train:
        return {"accepted": False, "reason": "too few examples to split", "serves_truth": False}
    raw = llm(_prompt(train))
    rule = _parse_rule(raw if isinstance(raw, str) else raw.get("text", ""))
    if rule is None:
        return {"accepted": False, "reason": "model did not produce a parseable structured rule", "candidate": None,
                "lineage": {"examples": len(examples)}, "serves_truth": False}
    correct = sum(1 for x, y in holdout if apply_rule(rule, x) == y)
    acc = round(correct / len(holdout), 3)
    accepted = acc >= accept_at
    return {"accepted": accepted, "holdout_accuracy": acc, "n_train": len(train), "n_holdout": len(holdout),
            "rule": rule if accepted else None, "rejected_candidate": None if accepted else rule,
            "reason": ("distilled rule matches the LLM on held-out (replaces the model)" if accepted
                       else f"held-out accuracy {acc} < {accept_at}: keep the LLM (rule rejected, lineage kept)"),
            "lineage": {"examples": len(examples), "model_output_kept": True}, "serves_truth": False}


def real_llm_caller():
    """A live LLM caller (the held lane) -> a string. Network-gated; raises offline so the caller falls back/injects."""
    from src.teleon.dag.real_steps import llm_available, real_llm
    if not llm_available():
        raise RuntimeError("LLM lane not available (offline / no key) — inject an llm for the generator")
    return lambda prompt: real_llm(prompt, system="You output ONLY compact JSON. No prose.", max_tokens=400, timeout=60).get("text", "")
