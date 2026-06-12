#!/usr/bin/env python3
"""Backs `processor/system-prompt-builder` (process_kind ``assemble.prompt_template``).

Assemble the INSTRUCTION CONTRACT — task, hard constraints, the grounding/
citation requirement, and an explicit abstention policy ("if the corpus
doesn't support it, say so") — kept SEPARATE from any persona text. The
cite-or-abstain contract is what converts retrieval into governed output;
this builder makes it impossible to emit a system prompt that lacks it.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs task, constraints, schema → output system_prompt.

CLI / self-test: python3 scripts/processors/retrieval/system_prompt_builder.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: The non-negotiable grounding/citation clause — present in EVERY built
#: prompt; a builder that can omit it defeats its purpose.
GROUNDING_CLAUSE = ("Ground every claim in the provided evidence and cite the "
                    "evidence id for each claim.")

#: The non-negotiable abstention clause.
ABSTENTION_CLAUSE = ("If the provided evidence does not support an answer, say "
                     "\"the corpus does not support an answer to this\" — do not guess.")

#: Section headers, in emission order (single definition; tests read them).
SECTION_TASK = "# Task"
SECTION_CONSTRAINTS = "# Hard constraints"
SECTION_GROUNDING = "# Grounding and citation"
SECTION_OUTPUT = "# Output schema"
SECTION_ABSTENTION = "# Abstention policy"


def run(*, task: str, constraints: list[str] | None = None,
        schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the instruction-contract system prompt (persona-free by design)."""
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task must be a non-empty str")
    if constraints is not None and not isinstance(constraints, list):
        raise TypeError("constraints must be a list of strings or None")
    if schema is not None and not isinstance(schema, dict):
        raise TypeError("schema must be a dict or None")
    cons = [str(c).strip() for c in (constraints or []) if str(c).strip()]

    parts: list[str] = [SECTION_TASK, task.strip(), ""]
    if cons:
        parts += [SECTION_CONSTRAINTS, *[f"- {c}" for c in cons], ""]
    parts += [SECTION_GROUNDING, GROUNDING_CLAUSE, ""]
    if schema is not None:
        parts += [SECTION_OUTPUT,
                  "Reply with JSON matching exactly:",
                  "```json",
                  json.dumps(schema, indent=2, sort_keys=True),
                  "```", ""]
    parts += [SECTION_ABSTENTION, ABSTENTION_CLAUSE]
    prompt = "\n".join(parts)
    return {"system_prompt": {
        "prompt": prompt,
        "sections": [s for s in (SECTION_TASK,
                                 SECTION_CONSTRAINTS if cons else None,
                                 SECTION_GROUNDING,
                                 SECTION_OUTPUT if schema is not None else None,
                                 SECTION_ABSTENTION) if s],
        "persona_free": True,
        "cite_or_abstain": True,
    }}


def _selftest() -> None:
    out = run(task="Answer questions about state usury caps.",
              constraints=["Use only the provided evidence blocks.",
                           "Never compute interest for a specific loan."],
              schema={"type": "object", "required": ["answer", "citations"]})["system_prompt"]
    p = out["prompt"]
    # The contract is complete and ordered: task → constraints → grounding →
    # schema → abstention.
    idx = [p.index(s) for s in (SECTION_TASK, SECTION_CONSTRAINTS, SECTION_GROUNDING,
                                SECTION_OUTPUT, SECTION_ABSTENTION)]
    assert idx == sorted(idx)
    # The two non-negotiable clauses are ALWAYS present…
    assert GROUNDING_CLAUSE in p and ABSTENTION_CLAUSE in p
    # …even in the minimal call.
    minimal = run(task="Summarize the corpus.")["system_prompt"]
    assert GROUNDING_CLAUSE in minimal["prompt"] and ABSTENTION_CLAUSE in minimal["prompt"]
    assert SECTION_CONSTRAINTS not in minimal["prompt"]  # empty sections are omitted
    # Constraints render as list items; the schema embeds verbatim.
    assert "- Never compute interest for a specific loan." in p
    assert '"required"' in p
    # Persona-free flag is structural (the builder offers no persona slot).
    assert out["persona_free"] is True and out["cite_or_abstain"] is True
    # Deterministic; on_error=raise.
    assert json.dumps(run(task="t"), sort_keys=True) == json.dumps(run(task="t"), sort_keys=True)
    raised = False
    try:
        run(task="   ")
    except ValueError:
        raised = True
    assert raised
    print("PASS — system_prompt_builder: task→constraints→grounding→schema→abstention "
          "contract with non-omittable cite-or-abstain clauses, persona-free, "
          "deterministic verified")


if __name__ == "__main__":
    _selftest()
