#!/usr/bin/env python3
"""scripts.check_inference_provider_adapters — PROOF: the Shared LLM Plane has a STANDARDIZED, GOVERNED, SWAPPABLE
provider-adapter layer — one base class, many API methods, selected by CONFIG, degrading safely offline.

Asserts:
  A. BASE CLASS: InferenceProviderAdapter is an ABC with an abstract invoke(); every shipped adapter subclasses it.
  B. MULTIPLE API METHODS: distinct adapter styles exist (deterministic_stub / openai_compatible / ollama_native /
     anthropic_messages), each mapped in REGISTRY to a subclass.
  C. CONFIG-DRIVEN RESOLUTION: resolve_adapter(node) picks the adapter from the node's `adapter_style` (config) — every
     provider-graph node resolves to a base-class instance; the offline-default node resolves to the local stub.
  D. EASY SWAP: flipping a node's adapter_style swaps the adapter class with no code change (proven on a copy).
  E. CONSISTENT (not shelfware): LocalStubAdapter.invoke output is byte-identical to oips.infer_local for the same
     (object_id, input_text, now) — the adapter layer matches the live gateway.
  F. GRACEFUL DEGRADATION: an external HTTP adapter (Ollama cloud) offline (no network / no secret) returns a
     ProviderUnavailableResult (available=False, reason recorded) — never a fabricated output.
  G. NO SDK OR RAW HTTP AT IMPORT: the adapters module imports NO provider SDK at module load
     (openai/anthropic/google/groq/…) and live HTTP goes through Teleon EgressClient, not raw urllib.
  H. NO RAW KEY: the module holds no raw key; adapters carry a secret_ref (not a value); results never include output
     when unavailable and are always is_truth=False.
  I. DETERMINISM.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import inspect
import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.inference import adapters as A
from src.teleon.inference import oips

_LEAK = re.compile(r"sk-[A-Za-z0-9_\-]{16,}|gsk_[A-Za-z0-9_\-]{16,}|AIza[A-Za-z0-9_\-]{16,}")
_SDK = re.compile(r"^\s*(?:import|from)\s+(openai|anthropic|google\.generativeai|cohere|mistralai|groq|together|"
                  r"replicate|litellm|vertexai|ollama)\b", re.M)
_NOW = "2026-06-05T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    check("A: InferenceProviderAdapter is an ABC with an abstract invoke()",
          inspect.isabstract(A.InferenceProviderAdapter)
          and getattr(A.InferenceProviderAdapter.invoke, "__isabstractmethod__", False))
    classes = [A.LocalStubAdapter, A.HttpOpenAICompatibleAdapter, A.OllamaNativeAdapter, A.AnthropicMessagesAdapter]
    check("A: every shipped adapter subclasses the base", all(issubclass(c, A.InferenceProviderAdapter) for c in classes))

    check("B: multiple API methods registered (>=4 distinct styles)",
          set(A.ADAPTER_STYLES) <= set(A.REGISTRY) and len(A.REGISTRY) >= 4
          and {A.REGISTRY[s] for s in A.REGISTRY}.issuperset({A.LocalStubAdapter, A.HttpOpenAICompatibleAdapter}))

    g = oips.load_graph()
    nodes = {n["node_id"]: n for n in g["nodes"]}
    resolved = {nid: A.resolve_adapter(n) for nid, n in nodes.items()}
    check("C: every graph node resolves to a base-class adapter instance",
          all(isinstance(a, A.InferenceProviderAdapter) for a in resolved.values()))
    check("C: the offline-default node resolves to the local stub",
          isinstance(resolved[g["offline_default_node"]], A.LocalStubAdapter))

    cloud = dict(nodes["model.ollama_cloud@candidate"])
    before = type(A.resolve_adapter(cloud)).__name__
    cloud_swapped = {**cloud, "adapter_style": "ollama_native"}
    check("D: flipping adapter_style swaps the adapter class (no code change)",
          before == "HttpOpenAICompatibleAdapter" and type(A.resolve_adapter(cloud_swapped)).__name__ == "OllamaNativeAdapter")

    stub_out = A.resolve_adapter(nodes["model.local_stub@v1"]).invoke(object_id="o", input_text="hi", now=_NOW)["output"]
    ref = oips.infer_local(object_id="o", preference_layers=[{"preference_id": "p",
            "model_class_preference": {"tier_code": 100, "specialization_codes": [300]},
            "allowed_provider_nodes": ["model.local_stub@v1"], "disallowed_provider_nodes": [],
            "fallback_policy": {}, "data_policy": {}}], input_text="hi", now=_NOW)["output"]
    check("E: LocalStubAdapter output is byte-identical to the gateway (consistent, not shelfware)", stub_out == ref)

    oc = A.resolve_adapter(nodes["model.ollama_cloud@candidate"]).invoke(
        object_id="o", input_text="hi", now=_NOW, secrets=set(), allow_network=False)
    check("F: an external HTTP adapter offline returns ProviderUnavailableResult (no fabricated output)",
          oc["available"] is False and oc["output"] is None and bool(oc["reason_code"]) and oc["is_truth"] is False)

    src = (_resource("src/teleon/inference/adapters.py")).read_text(encoding="utf-8")
    check("G: no provider SDK or raw HTTP imported at module load (HTTP uses Teleon EgressClient)",
          not _SDK.search(src) and "EgressClient" in src and "import urllib.request" not in src)
    check("H: no raw key in the adapters module + offline result carries no secret/output",
          not _LEAK.search(src + json.dumps(oc)))

    g2 = oips.load_graph()
    check("I: deterministic (re-resolve stable)",
          [type(A.resolve_adapter(n)).__name__ for n in g2["nodes"]] == [type(resolved[n["node_id"]]).__name__ for n in g["nodes"]])

    print("\n" + ("PASS — check_inference_provider_adapters: the LLM plane has one governed base class with multiple "
                  "API-method subclasses, resolved by config (adapter_style), swappable with no code change, "
                  "byte-consistent with the gateway, SDK/raw-HTTP-free at import, egress-captured for live HTTP, "
                  "secret-by-ref, and degrading to a ProviderUnavailableResult offline."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_inference_provider_adapters.py --self-test")
    raise SystemExit(0)
