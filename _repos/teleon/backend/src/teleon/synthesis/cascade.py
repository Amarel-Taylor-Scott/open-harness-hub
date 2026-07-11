"""cascade — the LLM cascade's escalate-or-stop judge (the descent's stop logic, made explicit). FrugalGPT frames a
cascade as three parts — a ROUTER (which model first; that's our routing_engine), a SCORER (is this answer good enough),
and a STOP-JUDGER (return or escalate). The training-free variant (agreement-based cascading) bases the escalate decision
on AGREEMENT among an ensemble of cheap-model responses: high agreement → trust the cheap answer and STOP; low agreement →
ESCALATE to a stronger (costlier) model. No labelled data, no trained scorer. serves_truth=false.
"""
from __future__ import annotations

from collections import Counter


def py_function_src_teleon_synthesis_cascade__agreement_score(py_arg_src_teleon_synthesis_cascade__agreement_score__responses: list) -> dict:
    """The fraction of the ensemble that gives the MAJORITY answer (the training-free confidence signal). Returns
    {majority, agreement, n}. Empty → agreement 0."""
    py_local_src_teleon_synthesis_cascade__agreement_score__clean = [r for r in py_arg_src_teleon_synthesis_cascade__agreement_score__responses if r is not None]
    if not py_local_src_teleon_synthesis_cascade__agreement_score__clean:
        return {"majority": None, "agreement": 0.0, "n": 0}
    counts = Counter(py_local_src_teleon_synthesis_cascade__agreement_score__clean)
    py_local_src_teleon_synthesis_cascade__agreement_score__majority, py_local_src_teleon_synthesis_cascade__agreement_score__top = counts.most_common(1)[0]
    return {"majority": py_local_src_teleon_synthesis_cascade__agreement_score__majority, "agreement": round(py_local_src_teleon_synthesis_cascade__agreement_score__top / len(py_local_src_teleon_synthesis_cascade__agreement_score__clean), 4), "n": len(py_local_src_teleon_synthesis_cascade__agreement_score__clean)}


def py_function_src_teleon_synthesis_cascade__should_escalate(py_arg_src_teleon_synthesis_cascade__should_escalate__responses: list, *, threshold: float = 0.7) -> dict:
    """Decide STOP vs ESCALATE from ensemble agreement (no trained scorer). agreement ≥ threshold → STOP with the
    majority answer; else ESCALATE to a stronger model. Returns {decision, answer, agreement, confidence, n, threshold}."""
    py_local_src_teleon_synthesis_cascade__should_escalate__sc = py_function_src_teleon_synthesis_cascade__agreement_score(py_arg_src_teleon_synthesis_cascade__should_escalate__responses)
    py_local_src_teleon_synthesis_cascade__should_escalate__stop = py_local_src_teleon_synthesis_cascade__should_escalate__sc["n"] > 0 and py_local_src_teleon_synthesis_cascade__should_escalate__sc["agreement"] >= threshold
    return {"decision": "stop" if py_local_src_teleon_synthesis_cascade__should_escalate__stop else "escalate", "answer": py_local_src_teleon_synthesis_cascade__should_escalate__sc["majority"] if py_local_src_teleon_synthesis_cascade__should_escalate__stop else None,
            "agreement": py_local_src_teleon_synthesis_cascade__should_escalate__sc["agreement"], "confidence": py_local_src_teleon_synthesis_cascade__should_escalate__sc["agreement"], "n": py_local_src_teleon_synthesis_cascade__should_escalate__sc["n"], "threshold": threshold,
            "serves_truth": False}


def py_function_src_teleon_synthesis_cascade__run_cascade(py_arg_src_teleon_synthesis_cascade__run_cascade__stages: list, *, threshold: float = 0.7) -> dict:
    """Walk a cost-ordered cascade of stages until one is confident enough to STOP. stages: [{name, responses}] from
    cheapest to most capable (each `responses` is that stage's ensemble of answers). Returns the first stage that clears
    the agreement threshold (or the last stage as the honest final fallback) + the trace of decisions."""
    py_local_src_teleon_synthesis_cascade__run_cascade__trace, py_local_src_teleon_synthesis_cascade__run_cascade__escalations = [], 0
    for py_local_src_teleon_synthesis_cascade__run_cascade__st in py_arg_src_teleon_synthesis_cascade__run_cascade__stages:
        py_local_src_teleon_synthesis_cascade__run_cascade__d = py_function_src_teleon_synthesis_cascade__should_escalate(py_local_src_teleon_synthesis_cascade__run_cascade__st.get("responses", []), threshold=threshold)
        py_local_src_teleon_synthesis_cascade__run_cascade__trace.append({"stage": py_local_src_teleon_synthesis_cascade__run_cascade__st.get("name"), **{k: py_local_src_teleon_synthesis_cascade__run_cascade__d[k] for k in ("decision", "agreement", "n")}})
        if py_local_src_teleon_synthesis_cascade__run_cascade__d["decision"] == "stop":
            return {"answer": py_local_src_teleon_synthesis_cascade__run_cascade__d["answer"], "stopped_at": py_local_src_teleon_synthesis_cascade__run_cascade__st.get("name"), "escalations": py_local_src_teleon_synthesis_cascade__run_cascade__escalations,
                    "agreement": py_local_src_teleon_synthesis_cascade__run_cascade__d["agreement"], "trace": py_local_src_teleon_synthesis_cascade__run_cascade__trace, "serves_truth": False}
        py_local_src_teleon_synthesis_cascade__run_cascade__escalations += 1
    # nothing cleared the bar — return the most-capable (last) stage's majority as the honest final answer
    py_local_src_teleon_synthesis_cascade__run_cascade__last = py_function_src_teleon_synthesis_cascade__agreement_score(py_arg_src_teleon_synthesis_cascade__run_cascade__stages[-1].get("responses", [])) if py_arg_src_teleon_synthesis_cascade__run_cascade__stages else {"majority": None, "agreement": 0.0}
    return {"answer": py_local_src_teleon_synthesis_cascade__run_cascade__last["majority"], "stopped_at": (py_arg_src_teleon_synthesis_cascade__run_cascade__stages[-1].get("name") if py_arg_src_teleon_synthesis_cascade__run_cascade__stages else None),
            "escalations": max(0, py_local_src_teleon_synthesis_cascade__run_cascade__escalations - 1), "agreement": py_local_src_teleon_synthesis_cascade__run_cascade__last["agreement"], "trace": py_local_src_teleon_synthesis_cascade__run_cascade__trace,
            "exhausted": True, "serves_truth": False}
