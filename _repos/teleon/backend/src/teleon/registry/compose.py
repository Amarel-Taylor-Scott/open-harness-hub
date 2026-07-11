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
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

from .port import py_const_src_teleon_registry_port__CATALOGS, py_function_src_teleon_registry_port__catalog

py_var_src_teleon_registry_compose___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
py_var_src_teleon_registry_compose___PLAYBOOKS = _resource("architecture") / "vertical_playbooks.json"
py_var_src_teleon_registry_compose___TOP = 3


def py_function_src_teleon_registry_compose___playbooks() -> dict:
    return {p["id"]: p for p in json.loads(py_var_src_teleon_registry_compose___PLAYBOOKS.read_text()).get("playbooks", [])}


def py_function_src_teleon_registry_compose___label(py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__label__rec: dict) -> str:
    for py_local_src_teleon_registry_compose__label__k in ("name", "id", "canonical", "pass", "failure_type"):
        if py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__label__rec.get(py_local_src_teleon_registry_compose__label__k):
            return str(py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__label__rec[py_local_src_teleon_registry_compose__label__k])
    return next((v for v in py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__label__rec.values() if isinstance(v, str) and v), "?")


def py_function_src_teleon_registry_compose___resolve(py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__resolve__registry_id: str, py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__resolve__query: str | None = None) -> dict:
    """Resolve a composing registry to ingredients via the menu (honest when it isn't a queryable catalog)."""
    if py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__resolve__registry_id not in py_const_src_teleon_registry_port__CATALOGS:
        return {"registry": py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__resolve__registry_id, "on_menu": False, "kind": "policy/runtime (not a queryable catalog)", "ingredients": []}
    py_local_src_teleon_registry_compose__resolve__reg = py_function_src_teleon_registry_port__catalog(py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__resolve__registry_id)
    py_local_src_teleon_registry_compose__resolve__recs = py_local_src_teleon_registry_compose__resolve__reg.search(py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__resolve__query)[:py_var_src_teleon_registry_compose___TOP] if py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__resolve__query else py_local_src_teleon_registry_compose__resolve__reg.list()[:py_var_src_teleon_registry_compose___TOP]
    return {"registry": py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__resolve__registry_id, "on_menu": True, "kind": "catalog", "ingredients": [py_function_src_teleon_registry_compose___label(r) for r in py_local_src_teleon_registry_compose__resolve__recs]}


def py_function_src_teleon_registry_compose__compile_playbook(py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_playbook__playbook_id: str) -> dict:
    """A vertical playbook -> a DAG plan: the loop stages + the composing registries resolved to candidate ingredients."""
    py_local_src_teleon_registry_compose__compile_playbook__pb = py_function_src_teleon_registry_compose___playbooks().get(py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_playbook__playbook_id)
    if not py_local_src_teleon_registry_compose__compile_playbook__pb:
        return {"playbook": py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_playbook__playbook_id, "available": False, "reason": "unknown playbook"}
    py_local_src_teleon_registry_compose__compile_playbook__composed = [py_function_src_teleon_registry_compose___resolve(rid) for rid in py_local_src_teleon_registry_compose__compile_playbook__pb.get("composes_registries", [])]
    return {
        "playbook": py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_playbook__playbook_id, "available": True, "domain": py_local_src_teleon_registry_compose__compile_playbook__pb.get("domain"),
        "loop": py_local_src_teleon_registry_compose__compile_playbook__pb.get("loop"), "stages": py_local_src_teleon_registry_compose__compile_playbook__pb.get("stages", []),
        "composes": py_local_src_teleon_registry_compose__compile_playbook__composed, "governance": py_local_src_teleon_registry_compose__compile_playbook__pb.get("governance"),
        "candidate_dag": True, "serves_truth": False,
    }


def py_function_src_teleon_registry_compose__compile_universal(py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_universal__intent: str, py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_universal__registries: list[str] | None = None) -> dict:
    """A MIXED/universal tool: an intent -> picks across chosen registries (default: a public-fact + knowledge + risk lookup)."""
    py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_universal__registries = py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_universal__registries or ["lookup_portals", "knowledge_taxonomies", "vulnerability_sources"]
    py_local_src_teleon_registry_compose__compile_universal__picks = [py_function_src_teleon_registry_compose___resolve(rid, py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_universal__intent) for rid in py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_universal__registries]
    return {"intent": py_arg_src_teleon_registry_compose__py_function_src_teleon_registry_compose__compile_universal__intent, "universal": True, "picks": py_local_src_teleon_registry_compose__compile_universal__picks, "candidate_dag": True, "serves_truth": False}
