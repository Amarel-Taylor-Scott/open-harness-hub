"""registry.compose — compile a vertical PLAYBOOK (or a universal intent) into a DAG plan FROM the registries.

Answers the load-bearing question 'how do registries become a TOOL?'. A vertical management tool (dental clinic)
or a universal tool (research-a-topic) is a DAG the federation ASSEMBLES: each stage PICKS components from the
registries via the RegistryPort menu. This is the consumption_model made concrete + runnable:

    compile_playbook('dental_clinic')   -> a DAG plan: stages -> composing registries -> candidate ingredients
    compile_universal('weather')        -> a mixed tool: intent -> picks across registries

serves_truth=false. The result is a CANDIDATE DAG plan — verify_buildable_dag + the governance gates run before
anything executes (an invasive/regulated stage routes through human_approval / redaction first).
"""
from __future__ import annotations

import json
from pathlib import Path

from .port import CATALOGS, catalog

_REPO = Path(__file__).resolve().parents[3]
_PLAYBOOKS = _REPO / "architecture" / "vertical_playbooks.json"
_TOP = 3


def _playbooks() -> dict:
    return {p["id"]: p for p in json.loads(_PLAYBOOKS.read_text()).get("playbooks", [])}


def _label(rec: dict) -> str:
    for k in ("name", "id", "canonical", "pass", "failure_type"):
        if rec.get(k):
            return str(rec[k])
    return next((v for v in rec.values() if isinstance(v, str) and v), "?")


def _resolve(registry_id: str, query: str | None = None) -> dict:
    """Resolve a composing registry to ingredients via the menu (honest when it isn't a queryable catalog)."""
    if registry_id not in CATALOGS:
        return {"registry": registry_id, "on_menu": False, "kind": "policy/runtime (not a queryable catalog)", "ingredients": []}
    reg = catalog(registry_id)
    recs = reg.search(query)[:_TOP] if query else reg.list()[:_TOP]
    return {"registry": registry_id, "on_menu": True, "kind": "catalog", "ingredients": [_label(r) for r in recs]}


def compile_playbook(playbook_id: str) -> dict:
    """A vertical playbook -> a DAG plan: the loop stages + the composing registries resolved to candidate ingredients."""
    pb = _playbooks().get(playbook_id)
    if not pb:
        return {"playbook": playbook_id, "available": False, "reason": "unknown playbook"}
    composed = [_resolve(rid) for rid in pb.get("composes_registries", [])]
    return {
        "playbook": playbook_id, "available": True, "domain": pb.get("domain"),
        "loop": pb.get("loop"), "stages": pb.get("stages", []),
        "composes": composed, "governance": pb.get("governance"),
        "candidate_dag": True, "serves_truth": False,
    }


def compile_universal(intent: str, registries: list[str] | None = None) -> dict:
    """A MIXED/universal tool: an intent -> picks across chosen registries (default: a public-fact + knowledge + risk lookup)."""
    registries = registries or ["lookup_portals", "knowledge_taxonomies", "vulnerability_sources"]
    picks = [_resolve(rid, intent) for rid in registries]
    return {"intent": intent, "universal": True, "picks": picks, "candidate_dag": True, "serves_truth": False}
