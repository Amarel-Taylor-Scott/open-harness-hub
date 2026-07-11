#!/usr/bin/env python3
"""scripts.runtime.catalog_runtime_adapter — register catalog processors INTO the runtime.

`catalog_processor_bridge` discovers and dispatches the 97 governed processor callables;
this module wraps each as a runtime `Processor` (the `handle(command, ctx)` contract) and
registers them into the existing `ProcessorRegistry`, so the consumption runner can dispatch
the REAL component families alongside (or instead of) the hand-wired CFPB builtins. This is
the load-bearing half of "the product uses the components that already exist."

The contract: a command carries the processor's `run()` inputs at
``command.payload['inputs']``; the adapter calls `run(**inputs)` and emits ONE
``processor_output`` artifact whose payload carries the run() output. The output is a
CANDIDATE — ``claim_status='candidate'``, ``promotion_eligible=False`` — because a catalog
processor's output is never truth (most pin `serves_truth=False`); the verification gate, not
this adapter, promotes. A `run()` that raises becomes a clean `make_fail`, never a crash.

CLI / self-test:
    python3 _repos/shared-backend-components/scripts/runtime/catalog_runtime_adapter.py
    python3 -m scripts.runtime.catalog_runtime_adapter --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2]))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.runtime import catalog_processor_bridge as bridge
from scripts.runtime.envelopes import ArtifactEnvelope, ProcessorResult, content_hash
from scripts.runtime.processor import Processor, ProcessorSpec

#: Catalog outputs are candidates — the verification gate promotes, not the adapter.
_CANDIDATE_CLAIM = "candidate"
_OUTPUT_ARTIFACT_TYPE = "processor_output"
_OUTPUT_SCHEMA = "ProcessorOutput"
_ADAPTER_VERSION = "v1"
_DEMO_SECURITY = {"classification": "demo_public", "kms_key_ref": "local://demo", "retention_policy_id": "demo"}

#: side_effects values from the manifest that mean the processor reads/writes beyond its args
#: (the runtime can route these differently); 'none'/'read' are pure-ish.
_NETWORK_SIDE_EFFECTS = frozenset({"external_call"})
_WRITE_SIDE_EFFECTS = frozenset({"write", "external_call"})


class CatalogProcessorAdapter(Processor):
    """Wrap one catalog processor (`run(**inputs) -> dict`) as a runtime Processor."""

    def __init__(self, spec: bridge.ProcessorSpec) -> None:
        self._catalog = spec
        self._run = spec.load()
        self.spec = ProcessorSpec(
            processor_id=spec.component_id, processor_version=_ADAPTER_VERSION,
            output_artifact_types=[_OUTPUT_ARTIFACT_TYPE],
            deterministic=spec.deterministic,
            side_effects=spec.side_effects in _WRITE_SIDE_EFFECTS,
            network_access=spec.side_effects in _NETWORK_SIDE_EFFECTS)

    def handle(self, command, ctx) -> ProcessorResult:  # noqa: D401
        inputs = dict(command.payload.get("inputs", {}))
        try:
            output = self._run(**inputs)
        except Exception as e:  # noqa: BLE001 — a processor error is a clean fail, not a crash
            return ProcessorResult.make_fail(
                run_id=command.run_id, step_id=command.step_id,
                processor_id=self.processor_id, processor_version=self.processor_version,
                errors=[{"code": "processor_run_error", "message": f"{type(e).__name__}: {e}",
                         "component_id": self._catalog.component_id}])
        key = self._catalog.component_id.split("/")[-1]
        artifact = ArtifactEnvelope(
            artifact_id=f"{command.run_id}:{_OUTPUT_ARTIFACT_TYPE}:{key}",
            tenant_id=command.tenant_id, artifact_type=_OUTPUT_ARTIFACT_TYPE,
            artifact_schema_version=_OUTPUT_SCHEMA,
            content_hash=content_hash({"c": self._catalog.component_id, "o": output}),
            payload={"component_id": self._catalog.component_id,
                     "process_kind": self._catalog.process_kind, "output": output},
            lineage={"run_id": command.run_id, "processor_id": self.processor_id,
                     "processor_version": self.processor_version},
            governance={"claim_status": _CANDIDATE_CLAIM, "promotion_eligible": False,
                        "model_dependent": not self._catalog.deterministic,
                        "requires_human_review": False},
            security=dict(_DEMO_SECURITY))
        return ProcessorResult.make_ok(
            run_id=command.run_id, step_id=command.step_id,
            processor_id=self.processor_id, processor_version=self.processor_version,
            artifacts=[artifact],
            metrics={"output_keys": len(output) if isinstance(output, dict) else 0,
                     "deterministic": int(self._catalog.deterministic)})


def register_catalog_processors(registry, *, only: list[str] | None = None) -> int:
    """Register catalog processors into ``registry`` (the runtime ProcessorRegistry).

    ``only`` limits to specific component ids; default registers the whole fleet. Returns
    the count registered. Idempotent per ref (the registry is a dict by ref)."""
    specs = bridge.all_specs()
    if only is not None:
        wanted = set(only)
        specs = [s for s in specs if s.component_id in wanted]
    count = 0
    for spec in specs:
        registry.register(CatalogProcessorAdapter(spec))
        count += 1
    return count


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    from scripts.runtime.context import build_context
    from scripts.runtime.envelopes import CommandEnvelope
    from scripts.runtime.processor_registry import ProcessorRegistry

    ctx = build_context(tenant_id="demo", run_id="run-1")

    def _cmd(component_id: str, inputs: dict) -> CommandEnvelope:
        return CommandEnvelope(command_type="process", tenant_id="demo", run_id="run-1",
                               queue="default", step_id="s1", processor_id=component_id,
                               processor_version=_ADAPTER_VERSION, payload={"inputs": inputs})

    # A deterministic processor (bm25) runs through the adapter and emits its output as a
    # CANDIDATE artifact.
    bm25 = CatalogProcessorAdapter(bridge.resolve("processor/bm25-keyword-retrieve"))
    res = bm25.handle(_cmd("processor/bm25-keyword-retrieve",
                           {"query": "provisional credit", "top_k": 3,
                            "corpus": [{"id": "d1", "text": "provisional credit within ten days"},
                                       {"id": "d2", "text": "unrelated note"}]}), ctx)
    check("adapter handle returns ok", res.ok)
    art = res.artifacts[0]
    check("emits a processor_output artifact", art.artifact_type == _OUTPUT_ARTIFACT_TYPE)
    check("artifact carries the run() output", art.payload["output"]["candidates"][0]["id"] == "d1")
    # Catalog output is a CANDIDATE — the gate promotes, not the adapter.
    check("output is candidate, not promotable",
          art.governance["claim_status"] == _CANDIDATE_CLAIM and art.governance["promotion_eligible"] is False)
    check("spec carries determinism", bm25.spec.deterministic is True)

    # A run() error is a clean fail, never a crash (bm25 needs corpus → omit it).
    bad = bm25.handle(_cmd("processor/bm25-keyword-retrieve", {"query": "x"}), ctx)
    check("processor error -> make_fail (no crash)", not bad.ok and bad.errors[0]["code"] == "processor_run_error")

    # Registration into the SAME runtime registry the runner uses.
    reg = ProcessorRegistry()
    n = register_catalog_processors(reg)
    check("registers the whole fleet (>= 90)", n >= 90, str(n))
    ref = "processor/cache-exact@v1"
    check("a catalog processor is resolvable by ref", reg.has(ref))
    # And it actually runs from the registry.
    cache_proc = reg.resolve(ref)
    out = cache_proc.handle(_cmd("processor/cache-exact",
                                 {"key": {"task": "t", "components": [], "inputs": {"x": 1}}}), ctx)
    check("registered processor runs from the registry", out.ok and out.artifacts[0].payload["output"]["hit"]["hit"] is False)

    # only= filter.
    reg2 = ProcessorRegistry()
    n2 = register_catalog_processors(reg2, only=["processor/cache-exact", "processor/rrf-fusion"])
    check("only= registers the subset", n2 == 2 and reg2.has("processor/rrf-fusion@v1"))

    ok = not fails
    print("\n" + (f"PASS — catalog_runtime_adapter: wraps catalog run() callables as runtime "
                  f"Processors, emits candidate processor_output artifacts (gate promotes), "
                  f"registers the fleet ({n}) into the ProcessorRegistry, errors fail cleanly."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Register catalog processors into the runtime.")
    p.add_argument("--self-test", action="store_true")
    p.parse_args(argv)
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
