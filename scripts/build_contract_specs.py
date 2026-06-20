#!/usr/bin/env python3
"""scripts.build_contract_specs — GENERATE OpenAPI + AsyncAPI specs from architecture/contract_registry.json.

This is the machine-checked projection of the contract registry — NOT a hand-edited source. The curated narrative
specs (docs/contracts/{openapi,asyncapi}.runtime.yaml) are preserved; these GENERATED docs are an additive derived
layer that must cover every registered route/channel and is regenerated, never hand-edited.

  - OpenAPI 3.1 from contract_registry.api_routes (one path+method per registered route; bodies/returns reference the
    registered envelope/artifact schemas; every operation declares an ErrorEnvelope.v1 error response; projection-only
    routes carry x-projection-only). Includes the src/teleon/inference/api_projection /api/inference/* read routes.
  - AsyncAPI 3.0 from contract_registry.command_types (CommandEnvelope), event_types (EventEnvelope / CloudEvents) and
    log_events, grouped onto registered queue channels.

Deterministic (sorted keys, no wall-clock, no RNG). `--write` emits the docs; `--check` fails on drift. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_REG = _REPO / "architecture" / "contract_registry.json"
_OUT = _REPO / "docs" / "contracts"
_OPENAPI = _OUT / "openapi.generated.json"
_ASYNCAPI = _OUT / "asyncapi.generated.json"
# $ref paths are relative to docs/contracts/ (mirrors the hand-written *.runtime.yaml convention)
_REF_PREFIX = "../../schemas/"
_ERR = "envelopes/ErrorEnvelope.v1.schema.json"
_CMD = "envelopes/CommandEnvelope.v1.schema.json"
_EVT = "envelopes/EventEnvelope.v1.schema.json"


def _registry() -> dict:
    return json.loads(_REG.read_text(encoding="utf-8"))


def _schema_index() -> dict:
    """logical name (e.g. 'ResolvedInferencePreference.v1') -> schema path relative to schemas/, for every schema on disk."""
    idx: dict[str, str] = {}
    for f in sorted((_REPO / "schemas").rglob("*.schema.json")):
        rel = f.relative_to(_REPO / "schemas").as_posix()
        idx[f.name.replace(".schema.json", "")] = rel  # 'ResolvedInferencePreference.v1'
    return idx


def _ref(rel_under_schemas: str) -> dict:
    return {"$ref": _REF_PREFIX + rel_under_schemas}


def _path_template(raw: str) -> str:
    # registry uses <id>; OpenAPI uses {id}
    return raw.replace("<", "{").replace(">", "}")


def build_openapi() -> dict:
    reg = _registry()
    idx = _schema_index()
    paths: dict = {}
    for r in sorted(reg["api_routes"], key=lambda x: x["route"]):
        method, raw = r["route"].split(" ", 1)
        path = _path_template(raw)
        returns = r.get("returns")
        ok_content = None
        if returns and returns in idx:
            ok_content = {"application/json": {"schema": _ref(idx[returns])}}
        elif returns:
            ok_content = {"application/json": {"schema": {"type": "object", "description": f"projection: {returns}"}}}
        op = {
            "summary": f"{r['route']} (owner {r.get('owner', '?')})",
            "x-owner": r.get("owner"),
            "x-projection-only": bool(r.get("projection_only")),
            "x-status": r.get("status", "active"),
            "responses": {
                "200": {"description": "OK", **({"content": ok_content} if ok_content else {})},
                "4XX": {"description": "error (ErrorEnvelope.v1)",
                        "content": {"application/json": {"schema": _ref(_ERR)}}},
            },
        }
        paths.setdefault(path, {})[method.lower()] = op
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Baltor / Teleon portfolio API (generated)",
            "version": str(reg.get("version", "1.0")),
            "description": ("GENERATED from architecture/contract_registry.json api_routes by "
                           "scripts/build_contract_specs.py — do not hand-edit. Projection-only HTTP surface; "
                           "bodies/returns are the versioned envelope/artifact schemas; errors are ErrorEnvelope.v1."),
        },
        "paths": paths,
    }


def build_asyncapi() -> dict:
    reg = _registry()
    queues = {q["name"] for q in reg.get("queue_names", [])}
    cmd_channel = "runtime.commands" if "runtime.commands" in queues else "pipeline.commands"
    channels: dict = {
        cmd_channel: {
            "description": "Durable work queue (lease/ack/nack→DLQ); payload is a CommandEnvelope.v1.",
            "messages": {c["name"]: {"name": c["name"], "x-status": c.get("status", "active"),
                                     "payload": _ref(_CMD)} for c in sorted(reg.get("command_types", []), key=lambda x: x["name"])},
        },
        "runtime.events": {
            "description": "Facts about what happened (CloudEvents 1.0 EventEnvelope.v1).",
            "messages": {e["name"]: {"name": e["name"], "x-status": e.get("status", "active"),
                                     "payload": _ref(_EVT)} for e in sorted(reg.get("event_types", []), key=lambda x: x["name"])},
        },
        "runtime.logs": {
            "description": "In-process log events (scripts.context_events); not durable facts.",
            "messages": {l["name"]: {"name": l["name"], "x-status": l.get("status", "active")}
                         for l in sorted(reg.get("log_events", []), key=lambda x: x["name"])},
        },
    }
    return {
        "asyncapi": "3.0.0",
        "info": {
            "title": "Baltor / Teleon portfolio events (generated)",
            "version": str(reg.get("version", "1.0")),
            "description": ("GENERATED from architecture/contract_registry.json (command_types / event_types / "
                           "log_events) by scripts/build_contract_specs.py — do not hand-edit. Commands are "
                           "CommandEnvelope.v1 on durable queues; events are EventEnvelope.v1 (CloudEvents 1.0)."),
        },
        "channels": channels,
    }


def _dump(doc: dict) -> str:
    return json.dumps(doc, indent=2, sort_keys=True) + "\n"


def write() -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    _OPENAPI.write_text(_dump(build_openapi()), encoding="utf-8")
    _ASYNCAPI.write_text(_dump(build_asyncapi()), encoding="utf-8")


def check_drift() -> list[str]:
    drift = []
    if not _OPENAPI.exists() or _OPENAPI.read_text(encoding="utf-8") != _dump(build_openapi()):
        drift.append(str(_OPENAPI.relative_to(_REPO)))
    if not _ASYNCAPI.exists() or _ASYNCAPI.read_text(encoding="utf-8") != _dump(build_asyncapi()):
        drift.append(str(_ASYNCAPI.relative_to(_REPO)))
    return drift


if __name__ == "__main__":
    if "--write" in sys.argv:
        write()
        print(f"wrote {_OPENAPI.relative_to(_REPO)} + {_ASYNCAPI.relative_to(_REPO)}")
    elif "--check" in sys.argv:
        d = check_drift()
        print("DRIFT: " + ", ".join(d) + " — run scripts/build_contract_specs.py --write" if d else "specs up to date")
        raise SystemExit(1 if d else 0)
    else:
        print("usage: python3 scripts/build_contract_specs.py [--write|--check]")
