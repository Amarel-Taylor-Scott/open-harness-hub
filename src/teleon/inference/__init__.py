"""src.teleon.inference — the shared INFERENCE GATEWAY + Open Inference Preference Spec (OIPS).

The portfolio's ONE model-routing plane: every object declares a portable InferencePreference (desired tier +
specialization, allowed/disallowed provider NODES, data/budget/latency/fallback policy); the gateway resolves
it (inheritance), selects a provider via the NUMERIC model graph, handles governed fallback, executes (offline:
the local deterministic stub), and writes a ModelInvocationReceipt recording the ACTUAL model used + the
fallback trail + the allowed downstream use. Raw API keys live only behind secret_refs. LLM output is
candidate/advisory — never served truth (Baltor governs serving).

ARCHITECTURAL LAW: this lives in Teleon (model routing is a runtime concern). Baltor + the open hubs CONSUME it
via the allowed Baltor->Teleon direction; it must never import src.baltor. It is the OIPS layer ABOVE the
existing LLM gateway (scripts/llm_gateway / scripts/model_gateway.py), which becomes the primary provider
adapter during the runtime extraction (not reinvented).
"""
from .oips import (resolve_preference, select_provider, build_receipt, infer_local, load_graph,
                   OFFLINE_DEFAULT_NODE, ALLOWED_USE_ORDER)
from .free_endpoint_intel import (classify, score_risk, due_diligence, assess_gateway_repo,
                                  to_opentools_metadata, run_registry, run_watchlist)

__all__ = ["resolve_preference", "select_provider", "build_receipt", "infer_local", "load_graph",
           "OFFLINE_DEFAULT_NODE", "ALLOWED_USE_ORDER",
           "classify", "score_risk", "due_diligence", "assess_gateway_repo", "to_opentools_metadata",
           "run_registry", "run_watchlist"]
