"""The seven pipeline primitives, all extending one generic shell.

    Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output

The folder structure mirrors the taxonomy: one file per primitive, each owning
its metadata. Labels / stages / descriptions for catalog component `type`s are
DERIVED from the primitive classes (single source) — no magic-string dicts.
"""
from __future__ import annotations

from scripts.pipeline_object import PipelineObject
from scripts.primitives.base import Primitive
from scripts.primitives.input import Input
from scripts.primitives.knowledge_corpus import KnowledgeCorpus
from scripts.primitives.if_statement import IfStatement
from scripts.primitives.action import Action
from scripts.primitives.loop import Loop
from scripts.primitives.stop_end import StopEnd
from scripts.primitives.output import Output

# Canonical order (Input seeds the run, Stop/Output terminate it).
PRIMITIVE_CLASSES = [Input, KnowledgeCorpus, IfStatement, Action, Loop, StopEnd, Output]
REGISTRY = {c.kind: c for c in PRIMITIVE_CLASSES}

# Derived from each primitive's `schema_types` — the single source of truth for
# how a catalog component type maps to a primitive.
SCHEMA_TYPE_PRIMITIVE = {t: c for c in PRIMITIVE_CLASSES for t in c.schema_types}

# Stages that hold catalog component types, in flow order.
STAGE_ORDER = [KnowledgeCorpus.stage, IfStatement.stage, Action.stage, Loop.stage]


def primitive_for_type(schema_type: str) -> type[Primitive] | None:
    return SCHEMA_TYPE_PRIMITIVE.get(schema_type)


def label_for_type(schema_type: str) -> str:
    c = SCHEMA_TYPE_PRIMITIVE.get(schema_type)
    return c.label_for(schema_type) if c else schema_type


def stage_for_type(schema_type: str) -> str:
    c = SCHEMA_TYPE_PRIMITIVE.get(schema_type)
    return c.stage if c else Action.stage


def describe_type(schema_type: str) -> str:
    c = SCHEMA_TYPE_PRIMITIVE.get(schema_type)
    return f"{c.label_for(schema_type)} — {c.description}" if c else schema_type


def run_pipeline(steps: list[Primitive], po: PipelineObject) -> PipelineObject:
    for step in steps:
        po = step.run(po)
        if po.get("__stopped__"):
            break
    return po


def _self_test() -> int:
    import json
    # every concrete primitive extends the one shell and has a unique kind
    assert all(issubclass(c, Primitive) for c in PRIMITIVE_CLASSES)
    assert len({c.kind for c in PRIMITIVE_CLASSES}) == 7
    # type->primitive derivation (no magic dict): persona is an Action, logic-pack is a IfStatement
    assert label_for_type("knowledge-pack") == "Knowledge Corpus"
    assert label_for_type("persona") == "Action: Add Persona"
    assert label_for_type("logic-pack") == "IfStatement"
    assert stage_for_type("rule-pack") == "IfStatement"
    assert "knowledge-pack" not in describe_type("knowledge-pack")  # never leak the storage name as a label

    po = PipelineObject(pipeline_id="pipeline/primitive-demo", input="text about CWE-79")
    steps = [
        Input("in", value="text about CWE-79"),
        KnowledgeCorpus("kc", out_key="facts",
                        retrieve=lambda p: ["CWE-79 = XSS"] if "CWE-79" in str(p.get("input")) else []),
        IfStatement("hasfacts", flag="has_facts", when=lambda p: bool(p.get("facts"))),
        Action("polish", "compress/polish", exec_model="code-executing",
               do=lambda p: p.set("result", "Grounded: " + "; ".join(p.get("facts", [])))),
        StopEnd("guard", when=lambda p: not p.get("has_facts"), reason="no grounding facts"),
        Output("out", from_keys=["result", "facts"]),
    ]
    po = run_pipeline(steps, po)
    assert po.outputs.get("result", "").startswith("Grounded:") and len(po.steps) == 6
    print(json.dumps({"ok": True, "primitives": list(REGISTRY),
                      "type_map": {t: label_for_type(t) for t in sorted(SCHEMA_TYPE_PRIMITIVE)},
                      "stage_order": STAGE_ORDER, "result": po.outputs["result"]}, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
