"""check_teleon_agent_gateway_mcp_projection — proof for _repos/teleon/backend/src/teleon/agent_gateway/mcp_projection.py.

A DETERMINISTIC, OFFLINE, stdlib-only self-test that the LOCAL MCP PROJECTION of the Teleon Agent Capability
Gateway holds its projection-only invariants. It runs the projection end-to-end against a real
``AgentCapabilityGateway`` (no network, no MCP install, no live model) and asserts:

  * the projection exposes EXACTLY five tool descriptors, with exactly the five fixed names; each descriptor
    carries ``name`` + ``description`` + an object ``input_schema``;
  * ``teleon_list_capabilities`` returns COMPACT cards — only the public contract fields, and NO internal
    runtime field (deterministic_first / llm_fallback_allowed / receipt_required / freshness_policy /
    expected_latency) and NO secret/backend/raw-key field anywhere in the surfaced payload;
  * ``teleon_describe_capability`` returns one compact card for a known id;
  * ``teleon_run_capability`` runs a DETERMINISTIC capability end-to-end and returns a COMPACT result carrying
    a ``receipt_id``; ``teleon_get_receipt`` then RESOLVES that receipt; the result is reproducible (same now
    → same receipt_id) and ``serves_truth`` is False;
  * the CFPB capability runs as governed EVIDENCE (authoritative answer + a source handle + the held-out
    contradiction surfaced separately) — and ``serves_truth`` is still False;
  * ``teleon_request_boundary_expansion`` returns ``status='pending_human_approval'`` with
    ``auto_applied=False`` — never granted (an agent cannot self-expand its boundary);
  * an UNKNOWN tool name → a STRUCTURED error dict (never a crash, never an exec); a non-dict input → a
    structured ``bad_input`` error;
  * ``max_cost`` is enforced as a pre-flight ceiling (a too-low ceiling refuses with no receipt);
  * the projection module's source does NOT import ``src.baltor`` and contains no raw key literal.

Run: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_teleon_agent_gateway_mcp_projection.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import re
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.agent_gateway.gateway import py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway  # noqa: E402
from src.teleon.agent_gateway.mcp_projection import (  # noqa: E402
    py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_CARD_FIELDS,
    py_const_src_teleon_agent_gateway_mcp_projection__EXPOSED_TOOL_COUNT,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_NAMES,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_REQUEST_BOUNDARY_EXPANSION,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY,
    py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection,
)

#: a fixed injected clock — the projection/gateway are deterministic when ``now`` is supplied.
_NOW = "2026-06-08T00:00:00Z"

#: internal runtime knobs that a COMPACT card must NOT surface (the projection drops these on purpose).
_FORBIDDEN_CARD_FIELDS = (
    "deterministic_first", "llm_fallback_allowed", "receipt_required", "freshness_policy", "expected_latency",
)
#: any surfaced dict key containing one of these substrings is a leak (secret / backend internal / raw key).
_FORBIDDEN_KEY_SUBSTRINGS = (
    "secret", "backend_internal", "api_key", "apikey", "access_key", "private_key", "token_value",
    "password", "credential",
)
#: raw-key shapes that must never appear as a literal in the projection source.
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9]{8,})")


def _walk_keys(obj) -> list[str]:
    """Every dict key appearing anywhere in a nested structure (for leak scanning)."""
    found: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.append(str(k))
            found.extend(_walk_keys(v))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            found.extend(_walk_keys(v))
    return found


def _has_forbidden_key(obj) -> str | None:
    """Return the first surfaced key that looks secret/backend-internal, or None if the payload is clean."""
    for key in _walk_keys(obj):
        low = key.lower()
        if any(bad in low for bad in _FORBIDDEN_KEY_SUBSTRINGS):
            return key
    return None


def main() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")

    gw = py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway()
    proj = py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection(gw)

    # ---- (1) exactly five descriptors, with the five fixed names + required keys --------------------------- #
    descriptors = proj.tool_descriptors()
    check("five_descriptors", len(descriptors) == py_const_src_teleon_agent_gateway_mcp_projection__EXPOSED_TOOL_COUNT == 5,
          f"got {len(descriptors)} (EXPOSED_TOOL_COUNT={py_const_src_teleon_agent_gateway_mcp_projection__EXPOSED_TOOL_COUNT})")
    names = [d.get("name") for d in descriptors]
    check("descriptor_names_exact", names == list(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_NAMES), f"names={names}")
    expected_names = {
        py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES, py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY, py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY,
        py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT, py_const_src_teleon_agent_gateway_mcp_projection__TOOL_REQUEST_BOUNDARY_EXPANSION,
    }
    check("descriptor_names_are_the_five", set(names) == expected_names, f"names={set(names)}")
    for d in descriptors:
        nm = d.get("name", "?")
        check(f"descriptor_has_name[{nm}]", isinstance(d.get("name"), str) and bool(d.get("name")))
        check(f"descriptor_has_description[{nm}]",
              isinstance(d.get("description"), str) and bool(d.get("description")))
        schema = d.get("input_schema")
        check(f"descriptor_has_input_schema[{nm}]",
              isinstance(schema, dict) and schema.get("type") == "object" and "properties" in schema)

    # the projection exposes ONLY these five — there is no descriptor for an internal handler / receipt store.
    check("no_internal_tool_exposed",
          all(not str(n).startswith("_") for n in names)
          and "teleon_run_handler" not in names and "teleon_get_capabilities_registry" not in names)

    # ---- (2) teleon_list_capabilities → COMPACT cards, no runtime/secret/backend leak ---------------------- #
    listed = proj.call_tool(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES, {}, now=_NOW)
    check("list_has_capabilities", isinstance(listed.get("capabilities"), list) and listed["capabilities"],
          f"keys={sorted(listed)}")
    check("list_serves_truth_false", listed.get("serves_truth") is False)
    for card in listed.get("capabilities", []):
        cid = card.get("capability_id", "?")
        # compact: only the allowed public fields are present.
        extra = set(card) - set(py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_CARD_FIELDS)
        check(f"card_compact[{cid}]", not extra, f"unexpected fields {sorted(extra)}")
        # explicitly assert each forbidden runtime field is ABSENT.
        leaked_runtime = [f for f in _FORBIDDEN_CARD_FIELDS if f in card]
        check(f"card_no_runtime_internals[{cid}]", not leaked_runtime, f"leaked {leaked_runtime}")
    # no secret/backend/raw-key-shaped key anywhere in the listing payload.
    bad = _has_forbidden_key(listed)
    check("list_no_secret_or_backend_key", bad is None, f"leaked key {bad!r}")

    # domain filter narrows the set (the cfpb domain has exactly the one cfpb.* card).
    cfpb_only = proj.call_tool(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES, {"domain": "cfpb"}, now=_NOW)
    cfpb_ids = {c.get("capability_id") for c in cfpb_only.get("capabilities", [])}
    check("list_domain_filter", cfpb_ids == {"cfpb.deadline.verify"}, f"cfpb_ids={cfpb_ids}")

    # ---- (3) describe → one compact card; unknown id → honest not_found --------------------------------- #
    described = proj.call_tool(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY, {"capability_id": "utility.hash"}, now=_NOW)
    check("describe_found", described.get("found") is True and isinstance(described.get("capability"), dict))
    card = described.get("capability") or {}
    check("describe_compact", set(card) <= set(py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_CARD_FIELDS) and "capability_id" in card,
          f"keys={sorted(card)}")
    check("describe_no_runtime_internals", not any(f in card for f in _FORBIDDEN_CARD_FIELDS))
    missing = proj.call_tool(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY, {"capability_id": "does.not.exist"}, now=_NOW)
    check("describe_unknown_not_found", missing.get("found") is False and missing.get("capability") is None)

    # ---- (4) run a DETERMINISTIC capability end-to-end → compact result + receipt_id --------------------- #
    run = proj.call_tool(
        py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY,
        {"capability_id": "utility.hash", "payload": {"payload": {"a": 1, "b": [2, 3]}},
         "consumer_id": "agent-proof"},
        now=_NOW,
    )
    check("run_has_receipt_id", isinstance(run.get("receipt_id"), str) and bool(run.get("receipt_id")),
          f"receipt_id={run.get('receipt_id')!r}")
    check("run_status_ok", run.get("status") in ("verified", "succeeded"), f"status={run.get('status')}")
    check("run_serves_truth_false", run.get("serves_truth") is False)
    check("run_has_output", isinstance(run.get("output"), dict) and run["output"].get("algorithm") == "sha256")
    # compact: no receipt internals / no secret key leaked through the run view.
    check("run_no_receipt_internals_inline",
          "policy_checks" not in run and "input_hash" not in run and "backend" not in run,
          f"keys={sorted(run)}")
    check("run_no_secret_or_backend_key", _has_forbidden_key(run) is None)

    # teleon_get_receipt RESOLVES the receipt_id from the run.
    receipt_id = run.get("receipt_id")
    got = proj.call_tool(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT, {"receipt_id": receipt_id}, now=_NOW)
    check("get_receipt_found", got.get("found") is True and isinstance(got.get("receipt"), dict))
    rec = got.get("receipt") or {}
    check("receipt_matches_run", rec.get("receipt_id") == receipt_id and rec.get("capability_id") == "utility.hash")
    check("receipt_runtime_path_deterministic", rec.get("runtime_path") == "deterministic",
          f"runtime_path={rec.get('runtime_path')}")
    check("get_receipt_no_secret_key", _has_forbidden_key(got) is None)
    check("get_receipt_serves_truth_false", got.get("serves_truth") is False)

    # determinism: same call + same now → same receipt_id (content-addressed; idempotent).
    run2 = proj.call_tool(
        py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY,
        {"capability_id": "utility.hash", "payload": {"payload": {"a": 1, "b": [2, 3]}},
         "consumer_id": "agent-proof"},
        now=_NOW,
    )
    check("run_deterministic_receipt", run2.get("receipt_id") == receipt_id,
          f"{run2.get('receipt_id')} != {receipt_id}")

    # unknown receipt id → honest not_found (never invented).
    miss_rcpt = proj.call_tool(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT, {"receipt_id": "agentcaprcpt-deadbeef"}, now=_NOW)
    check("get_receipt_unknown_not_found", miss_rcpt.get("found") is False and miss_rcpt.get("receipt") is None)

    # ---- (5) the CFPB capability runs as governed EVIDENCE (answer + source handle + held-out) ----------- #
    cfpb = proj.call_tool(
        py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY,
        {"capability_id": "cfpb.deadline.verify", "payload": {}, "consumer_id": "agent-proof"},
        now=_NOW,
    )
    check("cfpb_verified", cfpb.get("status") == "verified", f"status={cfpb.get('status')}")
    check("cfpb_has_source_handle", isinstance(cfpb.get("source_handles"), list) and cfpb["source_handles"])
    check("cfpb_held_out_surfaced", isinstance(cfpb.get("held_out"), list) and len(cfpb["held_out"]) >= 1)
    check("cfpb_serves_truth_false", cfpb.get("serves_truth") is False)
    check("cfpb_has_receipt", isinstance(cfpb.get("receipt_id"), str) and bool(cfpb.get("receipt_id")))
    # the authoritative answer is surfaced and the held-out '30 days' is NOT the answer.
    ans = (cfpb.get("output") or {}).get("answer", "")
    check("cfpb_authoritative_answer", "business day" in str(ans).lower(), f"answer={ans!r}")
    held_values = [str(h.get("value", "")) for h in cfpb.get("held_out", []) if isinstance(h, dict)]
    check("cfpb_held_out_not_in_answer", all(hv not in str(ans) for hv in held_values if hv),
          f"answer={ans!r} held={held_values}")

    # ---- (6) boundary expansion → pending_human_approval / auto_applied False (never granted) ------------ #
    boundary = proj.call_tool(
        py_const_src_teleon_agent_gateway_mcp_projection__TOOL_REQUEST_BOUNDARY_EXPANSION,
        {"consumer_id": "agent-proof", "capability_id": "some.new.capability",
         "requested_change": {"add_capability": "some.new.capability"},
         "justification": "need it for a new task"},
        now=_NOW,
    )
    check("boundary_pending", boundary.get("status") == "pending_human_approval", f"status={boundary.get('status')}")
    check("boundary_not_auto_applied", boundary.get("auto_applied") is False,
          f"auto_applied={boundary.get('auto_applied')}")
    check("boundary_serves_truth_false", boundary.get("serves_truth") is False)
    # it is a REQUEST queued, not a grant: there is no 'granted'/'applied' truthy flag.
    check("boundary_no_grant_flag",
          not boundary.get("granted") and not boundary.get("approved") and not boundary.get("applied"))

    # ---- (7) unknown tool name → STRUCTURED error (never a crash / exec); bad input → bad_input ---------- #
    try:
        unknown = proj.call_tool("teleon_do_anything_arbitrary", {"x": 1}, now=_NOW)
        crashed = False
    except Exception as exc:  # pragma: no cover - must NOT happen
        unknown, crashed = {}, True
        check("unknown_tool_no_crash", False, f"raised {exc!r}")
    if not crashed:
        check("unknown_tool_no_crash", True)
        check("unknown_tool_structured_error", unknown.get("error") == "unknown_tool",
              f"got {unknown!r}")
        check("unknown_tool_lists_five", unknown.get("available_tools") == list(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_NAMES))
        check("unknown_tool_serves_truth_false", unknown.get("serves_truth") is False)

    # a non-dict input is rejected with a structured error, not a crash.
    bad_input = proj.call_tool(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY, ["not", "a", "dict"], now=_NOW)  # type: ignore[arg-type]
    check("bad_input_structured_error", bad_input.get("error") == "bad_input", f"got {bad_input!r}")

    # ---- (8) max_cost pre-flight ceiling refuses with no receipt ----------------------------------------- #
    refused = proj.call_tool(
        py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY,
        {"capability_id": "utility.hash", "payload": {"payload": 1}, "consumer_id": "agent-proof",
         "max_cost": -1.0},  # impossible ceiling → must refuse before running
        now=_NOW,
    )
    check("max_cost_refuses", refused.get("status") == "unavailable" and refused.get("receipt_id") is None,
          f"status={refused.get('status')} receipt={refused.get('receipt_id')}")

    # ---- (9) source hygiene: no src.baltor import, no raw-key literal ------------------------------------ #
    src_path = _resource("src/teleon/agent_gateway/mcp_projection.py")
    src = src_path.read_text()
    check("no_baltor_import", "import src.baltor" not in src and "from src.baltor" not in src)
    check("no_raw_key_literal", _KEY_RE.search(src) is None)

    # ------------------------------------------------------------------------------------------------------- #
    if fails:
        print("check_teleon_agent_gateway_mcp_projection: FAILURES")
        for f in fails[:40]:
            print("  -", f)
        return 1

    print(
        f"PASS — check_teleon_agent_gateway_mcp_projection: projection exposes exactly {py_const_src_teleon_agent_gateway_mcp_projection__EXPOSED_TOOL_COUNT} "
        f"MCP tools {list(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_NAMES)}; cards are compact (no runtime/secret/backend fields); "
        f"teleon_run_capability ran utility.hash + cfpb.deadline.verify deterministically and "
        f"teleon_get_receipt resolved receipt {receipt_id!r} (runtime_path=deterministic); CFPB returned "
        f"governed evidence (answer + source handle + held-out, serves_truth False); boundary request stayed "
        f"pending_human_approval/auto_applied=False; unknown tool → structured error (no crash/exec); "
        f"max_cost ceiling refused with no receipt; module imports no src.baltor and carries no raw key."
    )
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    raise SystemExit(main())
