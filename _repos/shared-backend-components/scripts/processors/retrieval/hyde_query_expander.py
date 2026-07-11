#!/usr/bin/env python3
"""Backs `processor/hyde-query-expander` (process_kind ``query.hyde``).

HyDE (Hypothetical Document Embeddings, taxonomy step R0): generate a
hypothetical ANSWER document with the model and retrieve with THAT text —
bridging the short-query↔long-document vocabulary gap for dense retrieval.

The model is the whole point of HyDE, so it is REQUIRED: the ``complete``
callable is injected (model-route idiom) and calling without one RAISES —
there is no deterministic stand-in for "imagine the answer", and faking one
would poison retrieval silently. The hypothetical text is retrieval BAIT,
never an answer: the envelope pins ``is_hypothetical: True`` /
``serves_truth: False`` and carries the original query untouched.

Contract: side_effects=external_call; on_error=raise.

Inputs query → output expanded_query.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/retrieval/hyde_query_expander.py
"""
from __future__ import annotations

import json
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: System prompt: a SHORT plausible answer passage — style over facts; the
#: text is an embedding probe, its claims are never served.
HYDE_SYSTEM = ("Write one short passage (3-5 sentences) that PLAUSIBLY answers the "
               "question, in the style of the target corpus. The passage is used only "
               "as a retrieval probe — do not hedge, do not say 'it depends'.")

#: Hypothetical passages longer than this are truncated for embedding economy
#: (HyDE's lift comes from vocabulary, not length).
MAX_HYPOTHETICAL_CHARS = 1200


def run(*, query: str, complete: Callable[[str, str], str] | None = None) -> dict[str, Any]:
    """Generate the hypothetical answer-document for ``query`` via the injected model."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty str")
    if complete is None:
        raise RuntimeError(
            "HyDE requires a model route — pass complete=(prompt, system) -> str "
            "(scripts.foundry.model_route). There is no deterministic stand-in for "
            "a hypothetical answer; refusing to fake one.")
    text = str(complete(f"Question: {query}", HYDE_SYSTEM)).strip()
    if not text:
        raise ValueError("the model returned an empty hypothetical — cannot expand")
    truncated = len(text) > MAX_HYPOTHETICAL_CHARS
    if truncated:
        text = text[:MAX_HYPOTHETICAL_CHARS]
    return {"expanded_query": {
        "original_query": query,
        "hypothetical_document": text,
        "retrieve_with": text,           # what the dense leg should embed
        "truncated": truncated,
        "is_hypothetical": True,
        "serves_truth": False,
    }}


def _selftest() -> None:
    def scripted(prompt: str, system: str) -> str:
        assert system == HYDE_SYSTEM and prompt.startswith("Question: ")
        return ("Under Regulation E, a bank generally must provide provisional credit "
                "within ten business days of receiving an error notice. The consumer "
                "keeps use of the funds during the investigation.")

    out = run(query="how fast is provisional credit?", complete=scripted)["expanded_query"]
    # The expansion is the model's passage, flagged hypothetical, original intact.
    assert out["retrieve_with"] == out["hypothetical_document"]
    assert "ten business days" in out["retrieve_with"]
    assert out["original_query"] == "how fast is provisional credit?"
    assert out["is_hypothetical"] is True and out["serves_truth"] is False
    # No model → honest refusal (RuntimeError), never a fake expansion.
    raised = False
    try:
        run(query="anything")
    except RuntimeError as e:
        raised = "refusing to fake" in str(e)
    assert raised
    # Oversize hypotheticals truncate and say so.
    big = run(query="q", complete=lambda p, s: "x" * (MAX_HYPOTHETICAL_CHARS + 50))["expanded_query"]
    assert big["truncated"] is True and len(big["retrieve_with"]) == MAX_HYPOTHETICAL_CHARS
    # Empty model output raises; empty query raises.
    raised = False
    try:
        run(query="q", complete=lambda p, s: "   ")
    except ValueError:
        raised = True
    assert raised
    raised = False
    try:
        run(query="  ", complete=scripted)
    except ValueError:
        raised = True
    assert raised
    # Deterministic given the same scripted route.
    assert json.dumps(run(query="q2", complete=scripted), sort_keys=True) == \
           json.dumps(run(query="q2", complete=scripted), sort_keys=True)
    print("PASS — hyde_query_expander: injected-model hypothetical passage as the dense "
          "probe (is_hypothetical pinned, serves_truth False), honest no-model refusal, "
          "truncation reported verified")


if __name__ == "__main__":
    _selftest()
