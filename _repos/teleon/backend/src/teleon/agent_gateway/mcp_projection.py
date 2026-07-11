"""src.teleon.agent_gateway.mcp_projection — a LOCAL MCP PROJECTION of the Teleon Agent Capability Gateway.

An agent that speaks MCP should see a SMALL, STABLE tool surface — five tools, not three hundred — and call
them instead of burning tokens re-deriving answers. This module is the thin projection that gives it exactly
that: it wraps an :class:`~src.teleon.agent_gateway.gateway.AgentCapabilityGateway` and exposes precisely FIVE
MCP-style tool descriptors plus a single ``call_tool`` dispatch. Nothing more is reachable through it.

THE LAW (unchanged from the gateway — this layer only *projects* it):
  * **agents ASK, Teleon EXECUTES, Baltor governs truth** — the projection NEVER executes anything itself; it
    delegates every run to ``gateway.run(...)`` and passes the gateway's plain-dict result back. There is no
    second gateway, no second registry, no truth here.
  * **deterministic-first / offline** — ``now`` is injected on every dispatch (no wall-clock, no RNG); the
    local capabilities resolve at the ``deterministic`` rung; no live model, no network, no MCP install.
  * **compact, receipt-backed** — listing returns COMPACT capability cards (id / purpose / input + output
    contract / expected cost / policy notes) and a run returns a COMPACT result carrying its ``receipt_id``.
    The projection deliberately DROPS the card's internal runtime knobs (``deterministic_first`` /
    ``llm_fallback_allowed`` / ``receipt_required`` / ``freshness_policy`` / ``expected_latency``) and the
    receipt's backend internals from the surfaced view — an agent sees the contract, not the machinery.
  * **output ≠ truth** — every run result carries ``serves_truth=False`` (passed straight through from the
    gateway); a capability output is EVIDENCE the agent receives, not a CanonicalFact it can re-sell.
  * **no self-expanded boundary** — ``teleon_request_boundary_expansion`` returns the gateway's
    ``pending_human_approval`` / ``auto_applied=False`` request unchanged; the projection can NEVER grant it.
  * **no arbitrary execution / no secret leak** — ``call_tool`` dispatches ONLY the five named tools through a
    fixed table of bound methods; an unknown name returns a STRUCTURED error dict (it never raises, never
    execs, never reflects a caller string into a method). No secret VALUE, backend internal, or raw key is
    ever surfaced — refs stay ``env://`` / ``ref://`` strings inside the gateway.

Teleon-owned: stdlib only; imports only the sibling gateway. It NEVER imports ``src.baltor``. Deterministic
when ``now`` is injected; offline.
"""
from __future__ import annotations

from typing import Any, Callable

from src.teleon.agent_gateway.gateway import (
    py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH,
    py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway,
    py_class_src_teleon_agent_gateway_gateway__AgentConsumer,
    py_const_src_teleon_agent_gateway_gateway__RUN_STATUS_UNAVAILABLE,
)

#: the EXACT five tool names this projection exposes — the single source of the surfaced tool set. An agent
#: sees these five, never the internal capability handlers, the receipt store, or the runtime selector.
py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES = "teleon_list_capabilities"
py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY = "teleon_describe_capability"
py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY = "teleon_run_capability"
py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT = "teleon_get_receipt"
py_const_src_teleon_agent_gateway_mcp_projection__TOOL_REQUEST_BOUNDARY_EXPANSION = "teleon_request_boundary_expansion"

#: the five names, in stable order. ``tool_descriptors()`` and the dispatch table both read THIS — there is no
#: parallel list to drift, and the projection asserts it is exactly length 5.
py_const_src_teleon_agent_gateway_mcp_projection__TOOL_NAMES: tuple[str, ...] = (
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT,
    py_const_src_teleon_agent_gateway_mcp_projection__TOOL_REQUEST_BOUNDARY_EXPANSION,
)
#: the count an agent should see — five, not three hundred (a named constant the proof asserts).
py_const_src_teleon_agent_gateway_mcp_projection__EXPOSED_TOOL_COUNT = 5

#: the ONLY card fields the projection surfaces (a COMPACT contract view). Internal runtime knobs
#: (deterministic_first / llm_fallback_allowed / receipt_required / freshness_policy / expected_latency) are
#: deliberately omitted — an agent sees what it must satisfy + what it costs, not the machinery.
py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_CARD_FIELDS: tuple[str, ...] = (
    "capability_id",
    "purpose",
    "input_contract",
    "output_contract",
    "expected_cost",
    "policy_notes",
)
#: the ONLY result fields the projection surfaces (a COMPACT, receipt-backed result). The receipt itself is
#: fetched separately via ``teleon_get_receipt`` — the run result just carries its ``receipt_id``.
py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_RESULT_FIELDS: tuple[str, ...] = (
    "request_id",
    "capability_id",
    "status",
    "output",
    "source_handles",
    "held_out",
    "receipt_id",
    "fallback_used",
    "tokens_saved_estimate",
    "serves_truth",
    "allowed_use",
)

#: substrings a surfaced view must NEVER contain (defense in depth — the gateway already keeps these out, but
#: the projection refuses to pass a key carrying one through). Lower-cased comparison.
py_var_src_teleon_agent_gateway_mcp_projection___FORBIDDEN_KEY_SUBSTRINGS: tuple[str, ...] = (
    "secret",
    "backend_internal",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "token_value",
    "password",
    "credential",
)

#: the structured-error shape ``call_tool`` returns for a bad request — NEVER an exception, NEVER an exec.
py_const_src_teleon_agent_gateway_mcp_projection__ERROR_UNKNOWN_TOOL = "unknown_tool"
py_const_src_teleon_agent_gateway_mcp_projection__ERROR_BAD_INPUT = "bad_input"


def py_function_src_teleon_agent_gateway_mcp_projection___is_forbidden_key(py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__is_forbidden_key__key: str) -> bool:
    """True if ``key`` looks like it could carry a secret / backend internal. A belt-and-braces guard: the
    gateway never emits such keys on its public surface, and the projection drops any that somehow appear."""
    py_local_src_teleon_agent_gateway_mcp_projection__is_forbidden_key__low = str(py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__is_forbidden_key__key).lower()
    return any(bad in py_local_src_teleon_agent_gateway_mcp_projection__is_forbidden_key__low for bad in py_var_src_teleon_agent_gateway_mcp_projection___FORBIDDEN_KEY_SUBSTRINGS)


def py_function_src_teleon_agent_gateway_mcp_projection___scrub(py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__scrub__value: Any) -> Any:
    """Recursively drop any dict key whose name looks secret/backend-internal. The gateway's public dicts do
    not contain such keys, so on the happy path this is a no-op; it exists so the projection can NEVER become a
    path that leaks a secret value even if an upstream shape changes. Lists/tuples are walked; scalars pass."""
    if isinstance(py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__scrub__value, dict):
        return {k: py_function_src_teleon_agent_gateway_mcp_projection___scrub(v) for k, v in py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__scrub__value.items() if not py_function_src_teleon_agent_gateway_mcp_projection___is_forbidden_key(k)}
    if isinstance(py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__scrub__value, (list, tuple)):
        return [py_function_src_teleon_agent_gateway_mcp_projection___scrub(v) for v in py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__scrub__value]
    return py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__scrub__value


def py_function_src_teleon_agent_gateway_mcp_projection___project(py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__project__source: dict, py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__project__fields: tuple[str, ...]) -> dict:
    """Return a COMPACT projection of ``source`` containing only ``fields`` that are present, each scrubbed of
    secret/backend-internal keys. Missing fields are simply absent (honest); nothing is invented."""
    return {f: py_function_src_teleon_agent_gateway_mcp_projection___scrub(py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__project__source[f]) for f in py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__project__fields if f in py_arg_src_teleon_agent_gateway_mcp_projection__py_function_src_teleon_agent_gateway_mcp_projection__project__source}


class py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection:
    """A LOCAL MCP projection over an :class:`AgentCapabilityGateway`.

    It exposes EXACTLY five MCP-style tools (``tool_descriptors()``) and one dispatch entry point
    (``call_tool(name, input, *, now)``). It is a thin READ/DISPATCH layer: every tool delegates to a gateway
    method and returns the gateway's plain dict (compacted for the run/list views). It holds NO state of its
    own beyond the wrapped gateway — no second gateway, no second registry, no truth.

    Projection-only invariants (asserted by ``_repos/shared-backend-components/scripts/check_teleon_agent_gateway_mcp_projection.py``):
    exactly five descriptors with the five fixed names; compact cards (no runtime/secret/backend fields); a
    run returns a compact result + ``receipt_id`` that ``teleon_get_receipt`` resolves; a boundary request is
    always ``pending_human_approval`` / ``auto_applied=False``; an unknown tool name → a structured error
    (never a crash/exec); ``serves_truth`` is False; it never imports ``src.baltor``.
    """

    def __init__(self, gateway: py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway | None = None) -> None:
        #: the wrapped gateway — the ONE place execution, the receipt store, and the catalog live. The
        #: projection never creates a second one of any of those.
        self.gateway: py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway = gateway or py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway()
        # the fixed dispatch table: tool name -> bound handler. ``call_tool`` only ever indexes THIS — it never
        # reflects a caller-supplied string into an attribute, so no arbitrary method can be reached/executed.
        self._dispatch: dict[str, Callable[[dict, str], dict]] = {
            py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES: self._tool_list_capabilities,
            py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY: self._tool_describe_capability,
            py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY: self._tool_run_capability,
            py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT: self._tool_get_receipt,
            py_const_src_teleon_agent_gateway_mcp_projection__TOOL_REQUEST_BOUNDARY_EXPANSION: self._tool_request_boundary_expansion,
        }
        # the surfaced set is EXACTLY the five names — keep the descriptor list and the dispatch table in lock.
        assert tuple(self._dispatch) == py_const_src_teleon_agent_gateway_mcp_projection__TOOL_NAMES, "dispatch table must be exactly the five tool names"

    # -- the MCP tool surface ------------------------------------------------------------------------------- #
    def tool_descriptors(self) -> list[dict]:
        """Return the FIVE MCP-style tool descriptors (``{name, description, input_schema}``), in stable order.

        ``input_schema`` is a JSON-Schema-ish dict (``type='object'`` + ``properties`` + ``required``) — enough
        for an MCP host to render/validate the tool, with no Teleon-internal field exposed. This is the COMPLETE
        tool surface: an agent sees these five and nothing else."""
        return [
            {
                "name": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES,
                "description": (
                    "List the small, stable catalog of Teleon capabilities you can call instead of reasoning "
                    "from scratch. Returns COMPACT capability cards (id, purpose, input/output contract, "
                    "expected cost, policy notes). Optionally filter by domain / data_class / allowed_actions."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string",
                                   "description": "optional: only cards whose id is under this dotted domain "
                                                  "prefix (e.g. 'cfpb', 'tariff')."},
                        "data_class": {"type": "string",
                                       "description": "optional, advisory: the data sensitivity class the agent "
                                                      "intends to handle (recorded as a filter hint, not a gate)."},
                        "allowed_actions": {"type": "array", "items": {"type": "string"},
                                            "description": "optional: only cards whose allowed_use intersects "
                                                           "these action labels."},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
            {
                "name": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY,
                "description": (
                    "Return the single COMPACT card for one capability id (purpose, input/output contract, "
                    "expected cost, policy notes). Use it before running to learn the input contract."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "capability_id": {"type": "string", "description": "the capability id to describe."},
                    },
                    "required": ["capability_id"],
                    "additionalProperties": False,
                },
            },
            {
                "name": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY,
                "description": (
                    "Run a capability on Teleon's deterministic-first runtime and get a COMPACT, receipt-backed "
                    "result (status, output as EVIDENCE, source handles, held-out contradictions, and a "
                    "receipt_id). Teleon executes; Baltor governs truth — the output is evidence, never a fact "
                    "you can re-sell (serves_truth is always false)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "capability_id": {"type": "string", "description": "the capability id to run."},
                        "payload": {"type": "object",
                                    "description": "the capability input, per its input_contract."},
                        "consumer_id": {"type": "string",
                                        "description": "the calling agent's stable identity (recorded on the "
                                                       "receipt)."},
                        "allowed_use": {"type": "array", "items": {"type": "string"},
                                        "description": "optional: the agent's declared intended use (annotation)."},
                        "max_cost": {"type": "number",
                                     "description": "optional: refuse if the capability's expected USD cost "
                                                    "exceeds this ceiling (pre-flight gate)."},
                        "freshness_requirement": {"type": "string",
                                                  "description": "optional, advisory: the freshness the agent "
                                                                 "needs (recorded as an annotation)."},
                    },
                    "required": ["capability_id", "payload", "consumer_id"],
                    "additionalProperties": False,
                },
            },
            {
                "name": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT,
                "description": (
                    "Fetch the provenance receipt for a prior run by its receipt_id (runtime path taken, input/"
                    "output content hashes, timing window, and the policy checks Teleon enforced)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "receipt_id": {"type": "string",
                                       "description": "the receipt_id returned by teleon_run_capability."},
                    },
                    "required": ["receipt_id"],
                    "additionalProperties": False,
                },
            },
            {
                "name": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_REQUEST_BOUNDARY_EXPANSION,
                "description": (
                    "REQUEST (never grant) an expansion of your boundary — a new capability, tool, domain, or "
                    "raised cost ceiling. The request is queued as pending_human_approval with auto_applied "
                    "false; a human must approve it out-of-band. An agent can NEVER self-expand its boundary."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "consumer_id": {"type": "string", "description": "the requesting agent's identity."},
                        "capability_id": {"type": "string",
                                          "description": "the capability the requested change concerns."},
                        "requested_change": {"type": "object",
                                             "description": "the boundary change being requested "
                                                            "(e.g. {'add_capability': '<id>'}); described, never "
                                                            "applied."},
                        "justification": {"type": "string",
                                          "description": "the agent's stated reason, for the human reviewer."},
                    },
                    "required": ["consumer_id", "capability_id", "requested_change", "justification"],
                    "additionalProperties": False,
                },
            },
        ]

    def call_tool(self, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__name: str, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__input: dict | None = None, *, now: str) -> dict:
        """Dispatch ONE of the five tools by ``name`` and return its dict. ``now`` is injected (determinism).

        Robust by construction: ``name`` is looked up in a FIXED table of bound methods — an unknown name
        returns a STRUCTURED error (``{error: 'unknown_tool', ...}``), never raises, never execs, never
        reflects ``name`` into an attribute. A non-dict ``input`` is rejected with a structured ``bad_input``
        error. This is the only entry point through which the gateway is reachable from MCP."""
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__handler = self._dispatch.get(str(py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__name))
        if py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__handler is None:
            return {
                "error": py_const_src_teleon_agent_gateway_mcp_projection__ERROR_UNKNOWN_TOOL,
                "message": f"unknown tool {py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__name!r}; this projection exposes exactly {py_const_src_teleon_agent_gateway_mcp_projection__EXPOSED_TOOL_COUNT} tools",
                "available_tools": list(py_const_src_teleon_agent_gateway_mcp_projection__TOOL_NAMES),
                "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH,
            }
        if py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__input is None:
            py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__input = {}
        if not isinstance(py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__input, dict):
            return {
                "error": py_const_src_teleon_agent_gateway_mcp_projection__ERROR_BAD_INPUT,
                "message": f"tool {py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__name!r} expects an object input, got {type(py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__input).__name__}",
                "tool": str(py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__name),
                "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH,
            }
        return py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__handler(py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection_call_tool__input, now)

    # -- tool implementations (each delegates to the gateway; nothing executes here) ------------------------ #
    def _tool_list_capabilities(self, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__input: dict, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__now: str) -> dict:
        """``teleon_list_capabilities`` — COMPACT cards, optionally filtered. Delegates to
        ``gateway.list_capabilities()`` then projects each card to ``COMPACT_CARD_FIELDS`` (dropping runtime/
        secret/backend fields). Filters are over PUBLIC card fields only."""
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__domain = py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__input.get("domain")
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__allowed_actions = py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__input.get("allowed_actions")
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__actions = {str(a) for a in py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__allowed_actions} if isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__allowed_actions, (list, tuple, set)) else None

        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__cards = self.gateway.list_capabilities()
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__out: list[dict] = []
        for py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__card in py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__cards:
            py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__cid = str(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__card.get("capability_id", ""))
            if py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__domain and not (py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__cid == str(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__domain) or py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__cid.startswith(f"{py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__domain}.")):
                continue
            if py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__actions is not None and not (set(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__card.get("allowed_use", [])) & py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__actions):
                continue
            py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__out.append(py_function_src_teleon_agent_gateway_mcp_projection___project(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__card, py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_CARD_FIELDS))
        return {
            "tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES,
            "capabilities": py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__out,
            "count": len(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__out),
            "total_available": len(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_list_capabilities__cards),
            "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH,
        }

    def _tool_describe_capability(self, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__input: dict, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__now: str) -> dict:
        """``teleon_describe_capability`` — one COMPACT card. Delegates to ``gateway.describe(capability_id)``;
        an unknown id returns a structured ``not_found`` (honest, never invented)."""
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__capability_id = py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__input.get("capability_id")
        if not isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__capability_id, str) or not py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__capability_id:
            return {"error": py_const_src_teleon_agent_gateway_mcp_projection__ERROR_BAD_INPUT, "message": "capability_id (string) is required",
                    "tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY, "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH}
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__card = self.gateway.describe(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__capability_id)
        if py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__card is None:
            return {"tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY, "found": False, "capability_id": py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__capability_id,
                    "capability": None, "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH}
        return {"tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY, "found": True, "capability_id": py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__capability_id,
                "capability": py_function_src_teleon_agent_gateway_mcp_projection___project(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_describe_capability__card, py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_CARD_FIELDS), "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH}

    def _tool_run_capability(self, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__input: dict, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__now: str) -> dict:
        """``teleon_run_capability`` — run a capability end-to-end and return a COMPACT result + ``receipt_id``.

        Builds a minimal :class:`AgentConsumer` whose allow-list is EXACTLY the requested capability (so the
        gateway's allow-list gate passes for this one call, and nothing else), maps the flat MCP ``payload`` /
        ``consumer_id`` onto the gateway's ``run`` request, then delegates to ``gateway.run(...)``. The agent's
        ``allowed_use`` / ``freshness_requirement`` are recorded as request annotations (never used to weaken a
        check). ``max_cost`` is a pre-flight ceiling: if the card's expected USD cost exceeds it we refuse
        BEFORE running (no receipt — nothing ran). The gateway's result dict is projected to
        ``COMPACT_RESULT_FIELDS`` and passed through with ``serves_truth`` intact (always False).

        The projection NEVER sets ``allow_live_llm`` — an LLM rung is unreachable through MCP; and it never
        permits an LLM fallback on the synthesized consumer."""
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__capability_id = py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__input.get("capability_id")
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__payload = py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__input.get("payload", {})
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__consumer_id = py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__input.get("consumer_id")
        if not isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__capability_id, str) or not py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__capability_id:
            return {"error": py_const_src_teleon_agent_gateway_mcp_projection__ERROR_BAD_INPUT, "message": "capability_id (string) is required",
                    "tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY, "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH}
        if not isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__consumer_id, str) or not py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__consumer_id:
            return {"error": py_const_src_teleon_agent_gateway_mcp_projection__ERROR_BAD_INPUT, "message": "consumer_id (string) is required",
                    "tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY, "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH}
        if not isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__payload, dict):
            py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__payload = {"payload": py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__payload}

        # pre-flight cost ceiling (optional). Use the gateway's own quote so the projection never re-derives
        # cost. A refusal here is a compact unavailable-style result with no receipt (nothing ran).
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__max_cost = py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__input.get("max_cost")
        if isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__max_cost, (int, float)) and not isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__max_cost, bool):
            py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__quote = self.gateway.quote(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__capability_id)
            py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__expected = py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__quote.get("expected_cost") if isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__quote, dict) else None
            py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__usd = py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__expected.get("usd") if isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__expected, dict) else None
            if isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__usd, (int, float)) and not isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__usd, bool) and py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__usd > py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__max_cost:
                return {
                    "tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY,
                    "capability_id": py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__capability_id,
                    "status": py_const_src_teleon_agent_gateway_gateway__RUN_STATUS_UNAVAILABLE,
                    "output": {"refused": True,
                               "reason": f"expected cost {py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__usd} exceeds max_cost {py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__max_cost}"},
                    "source_handles": [],
                    "held_out": [],
                    "receipt_id": None,
                    "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH,
                }

        # the bounded consumer for THIS call: allow exactly this capability, never permit an LLM fallback.
        consumer = py_class_src_teleon_agent_gateway_gateway__AgentConsumer(
            consumer_id=py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__consumer_id,
            allowed_capabilities=frozenset({py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__capability_id}),
            forbidden_tools=frozenset(),
            llm_fallback_permitted=False,
        )
        # record the agent's advisory annotations on the request (kept, never used to weaken a check).
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__annotations: dict[str, Any] = {}
        if isinstance(py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__input.get("allowed_use"), (list, tuple)):
            py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__annotations["requested_use"] = [str(a) for a in py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__input["allowed_use"]]
        if isinstance(py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__input.get("freshness_requirement"), str):
            py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__annotations["freshness_requirement"] = py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__input["freshness_requirement"]

        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__request = {"capability_id": py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__capability_id, "payload": py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__payload}
        if py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__annotations:
            py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__request["annotations"] = py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__annotations

        # DELEGATE — the projection executes nothing; the gateway runs the deterministic handler + writes the
        # receipt. allow_live_llm is intentionally NOT passed (defaults False): no live model via MCP, ever.
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__result = self.gateway.run(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__request, now=py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__now, consumer=consumer)
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__compact = py_function_src_teleon_agent_gateway_mcp_projection___project(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__result, py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_RESULT_FIELDS)
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__compact["tool"] = py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY
        # serves_truth is pinned by the gateway; reassert it on the surfaced view so it can never be absent.
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__compact["serves_truth"] = bool(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__result.get("serves_truth", py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH))
        return py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_run_capability__compact

    def _tool_get_receipt(self, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__input: dict, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__now: str) -> dict:
        """``teleon_get_receipt`` — fetch a stored receipt by id. Delegates to ``gateway.get_receipt(...)`` and
        scrubs the (already-public) view; an unknown id returns a structured ``not_found`` (never invented)."""
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__receipt_id = py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__input.get("receipt_id")
        if not isinstance(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__receipt_id, str) or not py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__receipt_id:
            return {"error": py_const_src_teleon_agent_gateway_mcp_projection__ERROR_BAD_INPUT, "message": "receipt_id (string) is required",
                    "tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT, "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH}
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__receipt = self.gateway.get_receipt(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__receipt_id)
        if py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__receipt is None:
            return {"tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT, "found": False, "receipt_id": py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__receipt_id,
                    "receipt": None, "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH}
        return {"tool": py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT, "found": True, "receipt_id": py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__receipt_id,
                "receipt": py_function_src_teleon_agent_gateway_mcp_projection___scrub(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_get_receipt__receipt), "serves_truth": py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH}

    def _tool_request_boundary_expansion(self, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__input: dict, py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__now: str) -> dict:
        """``teleon_request_boundary_expansion`` — queue a boundary-expansion REQUEST (never grant it).

        Maps the MCP input (``consumer_id`` / ``capability_id`` / ``requested_change`` / ``justification``)
        straight onto ``gateway.request_boundary_expansion(req, now=now)`` and passes the gateway's dict
        through UNCHANGED — it is always ``status='pending_human_approval'`` with ``auto_applied=False``. The
        projection forces nothing and can never grant an expansion."""
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__req = {
            "consumer_id": py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__input.get("consumer_id", ""),
            "capability_id": py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__input.get("capability_id", ""),
            "requested_change": py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__input.get("requested_change", {}),
            "justification": py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__input.get("justification", ""),
        }
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__result = self.gateway.request_boundary_expansion(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__req, now=py_arg_src_teleon_agent_gateway_mcp_projection__py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__now)
        # pass the gateway's queued request through (scrubbed); annotate the tool name for the MCP host.
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__out = py_function_src_teleon_agent_gateway_mcp_projection___scrub(py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__result)
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__out["tool"] = py_const_src_teleon_agent_gateway_mcp_projection__TOOL_REQUEST_BOUNDARY_EXPANSION
        py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__out["serves_truth"] = py_const_src_teleon_agent_gateway_gateway__AGENT_GATEWAY_SERVES_TRUTH
        return py_local_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection__tool_request_boundary_expansion__out


__all__ = [
    "py_class_src_teleon_agent_gateway_mcp_projection__TeleonMcpProjection",
    "py_const_src_teleon_agent_gateway_mcp_projection__TOOL_NAMES",
    "py_const_src_teleon_agent_gateway_mcp_projection__EXPOSED_TOOL_COUNT",
    "py_const_src_teleon_agent_gateway_mcp_projection__TOOL_LIST_CAPABILITIES",
    "py_const_src_teleon_agent_gateway_mcp_projection__TOOL_DESCRIBE_CAPABILITY",
    "py_const_src_teleon_agent_gateway_mcp_projection__TOOL_RUN_CAPABILITY",
    "py_const_src_teleon_agent_gateway_mcp_projection__TOOL_GET_RECEIPT",
    "py_const_src_teleon_agent_gateway_mcp_projection__TOOL_REQUEST_BOUNDARY_EXPANSION",
    "py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_CARD_FIELDS",
    "py_const_src_teleon_agent_gateway_mcp_projection__COMPACT_RESULT_FIELDS",
]
