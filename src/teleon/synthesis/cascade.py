"""cascade — the LLM cascade's escalate-or-stop judge (the descent's stop logic, made explicit). FrugalGPT frames a
cascade as three parts — a ROUTER (which model first; that's our routing_engine), a SCORER (is this answer good enough),
and a STOP-JUDGER (return or escalate). The training-free variant (agreement-based cascading) bases the escalate decision
on AGREEMENT among an ensemble of cheap-model responses: high agreement → trust the cheap answer and STOP; low agreement →
ESCALATE to a stronger (costlier) model. No labelled data, no trained scorer. serves_truth=false.
"""
from __future__ import annotations

from collections import Counter


def agreement_score(responses: list) -> dict:
    """The fraction of the ensemble that gives the MAJORITY answer (the training-free confidence signal). Returns
    {majority, agreement, n}. Empty → agreement 0."""
    clean = [r for r in responses if r is not None]
    if not clean:
        return {"majority": None, "agreement": 0.0, "n": 0}
    counts = Counter(clean)
    majority, top = counts.most_common(1)[0]
    return {"majority": majority, "agreement": round(top / len(clean), 4), "n": len(clean)}


def should_escalate(responses: list, *, threshold: float = 0.7) -> dict:
    """Decide STOP vs ESCALATE from ensemble agreement (no trained scorer). agreement ≥ threshold → STOP with the
    majority answer; else ESCALATE to a stronger model. Returns {decision, answer, agreement, confidence, n, threshold}."""
    sc = agreement_score(responses)
    stop = sc["n"] > 0 and sc["agreement"] >= threshold
    return {"decision": "stop" if stop else "escalate", "answer": sc["majority"] if stop else None,
            "agreement": sc["agreement"], "confidence": sc["agreement"], "n": sc["n"], "threshold": threshold,
            "serves_truth": False}


def run_cascade(stages: list, *, threshold: float = 0.7) -> dict:
    """Walk a cost-ordered cascade of stages until one is confident enough to STOP. stages: [{name, responses}] from
    cheapest to most capable (each `responses` is that stage's ensemble of answers). Returns the first stage that clears
    the agreement threshold (or the last stage as the honest final fallback) + the trace of decisions."""
    trace, escalations = [], 0
    for st in stages:
        d = should_escalate(st.get("responses", []), threshold=threshold)
        trace.append({"stage": st.get("name"), **{k: d[k] for k in ("decision", "agreement", "n")}})
        if d["decision"] == "stop":
            return {"answer": d["answer"], "stopped_at": st.get("name"), "escalations": escalations,
                    "agreement": d["agreement"], "trace": trace, "serves_truth": False}
        escalations += 1
    # nothing cleared the bar — return the most-capable (last) stage's majority as the honest final answer
    last = agreement_score(stages[-1].get("responses", [])) if stages else {"majority": None, "agreement": 0.0}
    return {"answer": last["majority"], "stopped_at": (stages[-1].get("name") if stages else None),
            "escalations": max(0, escalations - 1), "agreement": last["agreement"], "trace": trace,
            "exhausted": True, "serves_truth": False}
