"""Canonical pipeline runtime object — the single state container a pipeline run
threads through every component.

Standardization (per the product model): every runtime has ONE `PipelineObject`
holding the input, metadata, call info, a shared mutable variable scope, and a
step-by-step log. Each component/function receives it, reads what it needs from
`.variables` / `.input`, does its work, records a `StepLog`, and writes results
back — so at any point the object is a complete, replayable record of the run
(input → every step → output, with cost, timing, provenance, and status).

This is the durable contract for the executor (the builder *assembles* pipelines;
the executor *runs* them against this object). Stdlib-only, JSON-round-trippable.

Component-type execution model (see _repos/shared-backend-components/docs/concepts/component-taxonomy-and-stages.md):
  * static-information  → reads corpora into .variables (no side effects)
  * text-operation      → transforms .variables / .input deterministically
  * code-executing      → tools/harnesses/adapters; may set .cost + external I/O
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

INPUT_TYPES = ("text", "html", "pdf", "image", "document", "audio", "video", "combination")
STEP_STATUS = ("ok", "error", "skipped", "cached", "blocked")


@dataclass
class StepLog:
    """One component invocation in the run."""
    step_id: str
    component_id: str            # e.g. "rule-pack/grep-esg-forced-labor-red-flags"
    stage: str = ""              # canonical stage, e.g. "Knowledge"
    exec_model: str = ""         # static-information | text-operation | code-executing
    status: str = "ok"
    model_call: bool = False
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    reads: list[str] = field(default_factory=list)   # variable keys read
    writes: list[str] = field(default_factory=list)  # variable keys written
    note: str = ""
    started_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PipelineObject:
    """The full state of one pipeline run — read and modified by every step."""
    pipeline_id: str
    input: Any = None
    input_type: str = "text"
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    metadata: dict[str, Any] = field(default_factory=dict)   # tenant, caller, model route, flags…
    variables: dict[str, Any] = field(default_factory=dict)  # SHARED mutable scope across steps
    steps: list[StepLog] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0

    # --- shared variable scope (what components read/modify) ----------------
    def set(self, key: str, value: Any) -> "PipelineObject":
        self.variables[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def update(self, **kw: Any) -> "PipelineObject":
        self.variables.update(kw)
        return self

    # --- step logging + accounting ------------------------------------------
    def log(self, step: StepLog) -> StepLog:
        if not step.started_at:
            step.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if step.status not in STEP_STATUS:
            step.status = "ok"
        self.steps.append(step)
        self.cost_usd = round(self.cost_usd + step.cost_usd, 6)
        self.tokens_in += step.tokens_in
        self.tokens_out += step.tokens_out
        if step.status == "error":
            self.errors.append(f"{step.step_id}: {step.note}")
        return step

    def add_output(self, key: str, value: Any) -> "PipelineObject":
        self.outputs[key] = value
        return self

    # --- serialization (replay / audit / data+drift sharing) ----------------
    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def to_json(self, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), default=str, indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, d: dict) -> "PipelineObject":
        steps = [StepLog(**s) for s in d.get("steps", [])]
        obj = cls(**{k: v for k, v in d.items() if k != "steps"})
        obj.steps = steps
        return obj

    def summary(self) -> dict:
        return {
            "run_id": self.run_id, "pipeline_id": self.pipeline_id,
            "steps": len(self.steps), "model_calls": sum(1 for s in self.steps if s.model_call),
            "cost_usd": self.cost_usd, "tokens": self.tokens_in + self.tokens_out,
            "errors": len(self.errors), "outputs": list(self.outputs),
        }


def _self_test() -> int:
    po = PipelineObject(pipeline_id="pipeline/demo", input="<html>hi</html>", input_type="html",
                        metadata={"tenant": "t1", "model_route": "gemma4"})
    # input-formatting (text-operation): html -> markdown
    po.set("clean_text", "hi")
    po.log(StepLog("s1", "processor/html-to-markdown", stage="Input Formatting",
                   exec_model="text-operation", reads=["input"], writes=["clean_text"]))
    # knowledge (static-information): add facts
    po.set("facts", ["CWE-79 = XSS"])
    po.log(StepLog("s2", "knowledge-pack/nvd-cve-cwe-cvss-vectors", stage="Knowledge",
                   exec_model="static-information", writes=["facts"]))
    # model (code-executing): a model call with cost
    po.log(StepLog("s3", "harness/text-safety-review", stage="Model (harness)",
                   exec_model="code-executing", model_call=True, tokens_in=400, tokens_out=120,
                   cost_usd=0.0021, duration_ms=1800))
    po.add_output("verdict", "supported")

    assert po.get("clean_text") == "hi"
    assert len(po.steps) == 3 and po.summary()["model_calls"] == 1
    assert abs(po.cost_usd - 0.0021) < 1e-9 and po.tokens_in == 400
    # round-trip
    rt = PipelineObject.from_dict(json.loads(po.to_json()))
    assert rt.run_id == po.run_id and len(rt.steps) == 3 and rt.outputs["verdict"] == "supported"
    print(po.to_json(indent=2))
    print("self-test OK")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
