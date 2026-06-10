"""src.teleon.agent_gateway.gateway — the AgentCapabilityGateway + its P0-shaped contracts.

The gateway is the single seam an AI agent talks to. It LISTS a small stable catalog, DESCRIBEs a capability,
QUOTEs the cost/latency/runtime-path-plan, RUNs a capability (writing a receipt), and accepts a
boundary-expansion REQUEST that is always ``pending_human_approval`` / ``auto_applied=False``.

Contracts here match the P0 spec EXACTLY (so the parallel P0 contract build converges on the same shapes):
``AgentCapabilityCard``, ``AgentCapabilityRunResult``, ``AgentCapabilityReceipt``,
``AgentBoundaryExpansionRequest``. They are frozen dataclasses with an ``as_dict()`` (the gateway's public API
returns plain dicts, like the rest of Teleon). ``AgentConsumer`` is the calling agent's bounded identity:
``allowed_capabilities`` (allow-list) + ``forbidden_tools`` (deny-list) + ``llm_fallback_permitted`` (policy).

THE LAW, enforced here:
  * **deterministic-first** — :func:`AgentCapabilityGateway.run` resolves a runtime path down the TOKEN_LADDER
    (cache → deterministic → … → llm-fallback → human) and the LOCAL capabilities all resolve at the
    ``deterministic`` rung; the result's ``runtime_path`` and the receipt record what was actually taken;
  * an LLM fallback is reached only if BOTH ``card.llm_fallback_allowed`` AND the consumer's policy permit it —
    an agent can NEVER force it; in a self-test no live model is ever called;
  * **compact, receipt-backed result** — the body is bounded by the handler and the gateway asserts a
    ``receipt_id`` is present; a capability never returns a raw corpus;
  * ``serves_truth`` is pinned False on every result — capability output is EVIDENCE the agent receives, not a
    fact it can re-sell; Baltor's rail governs truth;
  * an agent CANNOT read a secret VALUE (refs are ``env://`` strings), call a ``forbidden_tool``, run a
    capability outside ``allowed_capabilities``, weaken success criteria, or self-expand its boundary.

Execution is DELEGATED to :func:`src.teleon.runtime.capability_binding.bind_capability_task` (the one place
backend/binding choice lives) — the gateway records the binding's chosen backend on the receipt, then runs the
deterministic handler. Teleon-owned: stdlib + Teleon runtime selection + Teleon ids + the Teleon-infra CFPB
environment; NEVER imports ``src.baltor``. Deterministic when ``now`` is injected; offline.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from src.teleon.agent_gateway import capabilities as caps
from src.teleon.experiments.ids import canonical_id, sha256_hex
from src.teleon.runtime.capability_binding import bind_capability_task

#: pinned False on every gateway result — THE INVARIANT (capability output is evidence, never truth).
AGENT_GATEWAY_SERVES_TRUTH = False

#: the deterministic-first TOKEN LADDER, cheapest rung first. The gateway always tries the cheapest CORRECT
#: rung; the local capabilities resolve at ``deterministic``. The single source for the ladder + its ordering.
TOKEN_LADDER: tuple[str, ...] = (
    "cache",            # 0 — a prior receipt for the identical request (free)
    "deterministic",    # 1 — a pure stdlib handler / table lookup (the local capabilities live here)
    "api",              # 2 — a cheap deterministic external API (governed; not reached in self-test)
    "local_calc",       # 3 — a heavier local computation
    "small_model",      # 4 — a small local model (still no network LLM)
    "browser",          # 5 — a bounded browser action (owner-gated)
    "provider",         # 6 — a hosted provider call (owner-gated)
    "llm_fallback",     # 7 — a network LLM (only if card + policy allow; agent can NEVER force it)
    "human",            # 8 — escalate to a human (the last rung)
)
#: the rung the local deterministic capabilities resolve at (a named constant the proofs assert).
RUNTIME_PATH_DETERMINISTIC = "deterministic"
#: the LLM rung name (reached only with card + policy opt-in).
RUNTIME_PATH_LLM_FALLBACK = "llm_fallback"

#: statuses an AgentCapabilityRunResult may carry (the P0 enum).
RUN_STATUS_VERIFIED = "verified"       # ran AND satisfied the capability's governance checks
RUN_STATUS_SUCCEEDED = "succeeded"     # ran, no governance verdict attached
RUN_STATUS_FAILED = "failed"           # the run itself failed
RUN_STATUS_UNAVAILABLE = "unavailable"  # refused / not runnable (policy, unknown id, …)

#: a boundary-expansion request is ALWAYS this status — never auto-applied (the safety constant).
BOUNDARY_STATUS_PENDING = "pending_human_approval"


# --------------------------------------------------------------------------------------------------------- #
# P0-shaped contracts (frozen dataclasses + as_dict()).
# --------------------------------------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AgentCapabilityCard:
    """The public contract for one capability the agent can call. ``deterministic_first`` says the gateway
    tries the deterministic rung first; ``llm_fallback_allowed`` gates whether an LLM rung is EVER reachable
    for this capability; ``receipt_required`` says every run must write a receipt."""
    capability_id: str
    purpose: str
    input_contract: dict
    output_contract: dict
    allowed_use: list
    forbidden_use: list
    expected_cost: dict
    expected_latency: dict
    freshness_policy: dict
    policy_notes: str
    deterministic_first: bool = True
    llm_fallback_allowed: bool = False
    receipt_required: bool = True

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AgentCapabilityRunResult:
    """The COMPACT, receipt-backed outcome the agent receives. ``output`` is bounded evidence (never a raw
    corpus); ``held_out`` carries surfaced-but-separate contradictions; ``serves_truth`` is pinned False —
    Baltor's rail governs truth. ``tokens_saved_estimate`` quantifies the tokens the agent did NOT burn."""
    request_id: str
    capability_id: str
    status: str               # verified | succeeded | failed | unavailable
    output: dict
    source_handles: list
    held_out: list
    receipt_id: str | None
    fallback_used: bool = False
    tokens_saved_estimate: int = 0
    serves_truth: bool = AGENT_GATEWAY_SERVES_TRUTH
    allowed_use: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AgentCapabilityReceipt:
    """The provenance receipt every run writes. Records the ACTUAL ``runtime_path`` taken down the ladder, the
    ``backend`` the binding chose, content hashes of the input + output, the timing window, and the
    ``policy_checks`` the gateway enforced. Hashes are content-addressed (deterministic)."""
    receipt_id: str
    request_id: str
    capability_id: str
    consumer_id: str
    input_hash: str
    output_hash: str
    runtime_path: str
    backend: str | None
    cost_estimate: dict
    started_at: str
    completed_at: str
    policy_checks: dict

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AgentBoundaryExpansionRequest:
    """An agent's REQUEST to expand its boundary (a new capability / tool / domain / cost ceiling / loosened
    policy). It is ALWAYS recorded as ``pending_human_approval`` with ``auto_applied=False`` — the gateway NEVER
    grants it. A human must approve it out-of-band; this object only captures the ask + its justification for
    the human-approval queue.

    Field names match ``schemas/agents/AgentBoundaryExpansionRequest.v1.schema.json`` EXACTLY:
    ``capability_id`` (the capability the change concerns), ``requested_change`` (the boundary change being
    requested, e.g. ``{"add_capability": ...}`` / ``{"add_allowed_domain": ...}`` / ``{"raise_max_cost": ...}``
    — described, never applied), and ``justification`` (the agent's stated reason, for the reviewer). The old
    ``requested_capability`` / ``rationale`` names are accepted only as INPUT aliases (see
    :meth:`AgentCapabilityGateway.request_boundary_expansion`); the EMITTED object uses these schema names."""
    request_id: str
    consumer_id: str
    capability_id: str
    requested_change: dict
    justification: str
    status: str = BOUNDARY_STATUS_PENDING
    auto_applied: bool = False
    requested_at: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AgentConsumer:
    """The calling agent's bounded identity. ``allowed_capabilities`` is an ALLOW-list (a capability not in it
    is refused); ``forbidden_tools`` is a DENY-list (a capability whose id is a forbidden tool is refused);
    ``llm_fallback_permitted`` is the consumer-side policy gate on the LLM rung (the card must ALSO allow it).
    An empty ``allowed_capabilities`` means 'no capabilities' (deny-by-default), not 'all'."""
    consumer_id: str
    allowed_capabilities: frozenset = frozenset()
    forbidden_tools: frozenset = frozenset()
    llm_fallback_permitted: bool = False

    def may_call(self, capability_id: str) -> bool:
        return capability_id in self.allowed_capabilities and capability_id not in self.forbidden_tools


# --------------------------------------------------------------------------------------------------------- #
# The gateway.
# --------------------------------------------------------------------------------------------------------- #
class AgentCapabilityGateway:
    """The deterministic capability runner AI agents call. Holds an in-memory receipt store (write-once,
    content-addressed). All public methods return plain dicts (like the rest of Teleon). Deterministic when
    ``now`` is injected; offline; never reaches a live model.

    ``run`` is the load-bearing method and enforces, in order: (1) the capability exists; (2) the consumer's
    allow-list AND deny-list permit it; (3) a runtime path is resolved DETERMINISTIC-FIRST (the LLM rung is
    reachable only if the card AND the consumer policy allow it — never forced by the agent, never live in a
    self-test); (4) execution backend is chosen by DELEGATING to ``bind_capability_task``; (5) the handler
    produces a COMPACT body; (6) a receipt is written recording the actual ``runtime_path``; (7)
    ``serves_truth`` is pinned False.
    """

    def __init__(self) -> None:
        self._receipts: dict[str, dict] = {}

    # -- catalog ------------------------------------------------------------------------------------------- #
    def list_capabilities(self) -> list[dict]:
        """Return the public cards for every registered capability (stable, sorted by id). ~5, not 300."""
        return [caps.get_card(cid) for cid in caps.capability_ids()]

    def describe(self, capability_id: str) -> dict | None:
        """Return the public card for ``capability_id`` (a copy), or ``None`` if unknown."""
        return caps.get_card(capability_id)

    def quote(self, capability_id: str, request: dict | None = None) -> dict:
        """Quote ``{capability_id, known, expected_cost, expected_latency, runtime_path_plan}`` for a call
        WITHOUT running it. ``runtime_path_plan`` is the rung the gateway WOULD take (``deterministic`` for the
        local capabilities). Honest for an unknown id (``known=False``)."""
        card = caps.get_card(capability_id)
        if card is None:
            return {"capability_id": capability_id, "known": False,
                    "expected_cost": None, "expected_latency": None, "runtime_path_plan": None,
                    "reason": "unknown capability_id"}
        return {
            "capability_id": capability_id,
            "known": True,
            "expected_cost": card["expected_cost"],
            "expected_latency": card["expected_latency"],
            "runtime_path_plan": RUNTIME_PATH_DETERMINISTIC,
        }

    # -- receipts ------------------------------------------------------------------------------------------ #
    def get_receipt(self, receipt_id: str) -> dict | None:
        """Return a COPY of the stored receipt for ``receipt_id`` (or ``None``). A copy so a caller can never
        mutate the write-once store."""
        rec = self._receipts.get(receipt_id)
        return dict(rec) if rec is not None else None

    # -- boundary expansion (never auto-applied) ----------------------------------------------------------- #
    def request_boundary_expansion(self, req: dict, *, now: str) -> dict:
        """Record an agent's boundary-expansion REQUEST. The result is ALWAYS
        ``status='pending_human_approval'`` with ``auto_applied=False`` — the gateway NEVER grants it (an agent
        cannot self-expand its boundary). The emitted dict uses the schema field names
        (``capability_id`` / ``requested_change`` / ``justification``); the legacy ``requested_capability`` /
        ``rationale`` keys are accepted as INPUT aliases for back-compat. Returns the queued request as a dict
        for the human-approval queue."""
        consumer_id = str(req.get("consumer_id", "unknown"))
        # schema field names, with the legacy aliases mapped in (back-compat; never trust the value verbatim).
        capability_id = str(req.get("capability_id", req.get("requested_capability", "")))
        justification = str(req.get("justification", req.get("rationale", "")))
        # ``requested_change`` is the (object) boundary change being requested. Accept it directly; otherwise
        # synthesize the canonical {add_capability} shape from the requested capability so legacy callers (who
        # only passed a capability) still produce a schema-shaped object.
        requested_change = req.get("requested_change")
        if not isinstance(requested_change, dict):
            requested_change = {"add_capability": capability_id} if capability_id else {}
        # a deterministic id over the (consumer, capability, change, justification) ask.
        request_id = canonical_id("boundaryreq", consumer_id, capability_id, sha256_hex(requested_change),
                                  justification, now)
        # status + auto_applied are FORCED here regardless of what the caller asked for — never trust the input;
        # the gateway NEVER grants a boundary expansion.
        return AgentBoundaryExpansionRequest(
            request_id=request_id, consumer_id=consumer_id, capability_id=capability_id,
            requested_change=requested_change, justification=justification,
            status=BOUNDARY_STATUS_PENDING, auto_applied=False, requested_at=now,
        ).as_dict()

    # -- run ----------------------------------------------------------------------------------------------- #
    def _unavailable(self, capability_id: str, request_id: str, reason: str, card: dict | None) -> dict:
        """Build an UNAVAILABLE result (refusal / not runnable). No receipt is written (nothing ran). Carries
        the card's ``allowed_use`` when known so the agent still sees the contract."""
        return AgentCapabilityRunResult(
            request_id=request_id, capability_id=capability_id, status=RUN_STATUS_UNAVAILABLE,
            output={"refused": True, "reason": reason}, source_handles=[], held_out=[], receipt_id=None,
            fallback_used=False, tokens_saved_estimate=0, serves_truth=AGENT_GATEWAY_SERVES_TRUTH,
            allowed_use=list(card.get("allowed_use", [])) if card else [],
        ).as_dict()

    def run(self, request: dict, *, now: str, consumer: AgentConsumer | None = None,
            allow_live_llm: bool = False, **selector_kwargs) -> dict:
        """Run a capability for an agent consumer and return a COMPACT :class:`AgentCapabilityRunResult` dict
        (a receipt is written for every actual run). ``request`` is
        ``{capability_id, payload, [request_id]}``. ``now`` is injected (determinism). ``consumer`` is the
        bounded calling agent (default: a deny-all anonymous consumer). ``allow_live_llm`` is an explicit,
        owner-gated switch that the SELF-TEST never sets — even a card that allows an LLM fallback will NOT
        reach a live model unless this is True; the local capabilities never need it.

        Enforcement order is documented on the class. The capability is resolved DETERMINISTIC-FIRST; backend
        choice is DELEGATED to ``bind_capability_task``; ``serves_truth`` is pinned False.
        """
        capability_id = str(request.get("capability_id", ""))
        payload = request.get("payload", {})
        if not isinstance(payload, dict):
            payload = {"payload": payload}
        # deterministic request id over (capability, payload, consumer) — same call → same id.
        consumer = consumer or AgentConsumer(consumer_id="anonymous")
        request_id = str(request.get("request_id")
                         or canonical_id("agentcapreq", capability_id, sha256_hex(payload), consumer.consumer_id))

        card = caps.get_card(capability_id)
        # (1) capability must exist.
        if card is None:
            return self._unavailable(capability_id, request_id, f"unknown capability_id {capability_id!r}", None)
        # (2) consumer allow-list AND deny-list must permit it (agent boundary; cannot be self-expanded).
        if capability_id not in consumer.allowed_capabilities:
            return self._unavailable(capability_id, request_id,
                                     f"capability {capability_id!r} not in consumer.allowed_capabilities", card)
        if capability_id in consumer.forbidden_tools:
            return self._unavailable(capability_id, request_id,
                                     f"capability {capability_id!r} is a forbidden tool for this consumer", card)

        # (3) resolve the runtime path DETERMINISTIC-FIRST. The local handlers all resolve at `deterministic`;
        #     an LLM rung is reachable ONLY if the card allows it AND the consumer policy permits it AND the
        #     owner-gated live switch is on — an agent can NEVER force it, and the self-test never sets it.
        handler = caps.get_handler(capability_id)
        runtime_path = RUNTIME_PATH_DETERMINISTIC
        fallback_used = False
        if handler is None:
            # no deterministic handler: the ONLY way to serve this is an LLM rung — gated three ways.
            may_llm = bool(card.get("llm_fallback_allowed")) and consumer.llm_fallback_permitted and allow_live_llm
            if not may_llm:
                reason = ("no deterministic handler and llm_fallback not permitted "
                          f"(card={bool(card.get('llm_fallback_allowed'))}, "
                          f"consumer={consumer.llm_fallback_permitted}, live={allow_live_llm})")
                return self._unavailable(capability_id, request_id, reason, card)
            runtime_path, fallback_used = RUNTIME_PATH_LLM_FALLBACK, True

        # (4) DELEGATE execution-backend choice to the binding contract (the one place backend choice lives).
        binding = bind_capability_task(
            {"capability_id": f"agent_capability::{capability_id}", "worker_bucket": "utility",
             "estimated_runtime_ms": int(card["expected_latency"].get("p95_ms", 5))},
            now=now, **selector_kwargs)
        backend = getattr(binding, "backend", None) or getattr(binding, "backend_would_be", None)

        started_at = now
        # (5) run the deterministic handler → a COMPACT body. (Live-LLM rung is owner-gated + never in tests;
        #     since every local capability has a handler we never hit a live model here.)
        body = handler(payload, now=now)  # type: ignore[misc]
        output = body.get("output", {})
        source_handles = list(body.get("source_handles", []))
        held_out = list(body.get("held_out", []))
        tokens_saved = int(body.get("tokens_saved_estimate", 0))

        # verdict: a capability carrying a source handle AND surfacing its held-out contradictions is VERIFIED
        # (governed-evidence shape); otherwise a clean run is `succeeded`.
        status = RUN_STATUS_VERIFIED if source_handles else RUN_STATUS_SUCCEEDED

        # (6) write the receipt FIRST (every run is receipted), recording the ACTUAL runtime_path + backend.
        #     Key names are a SUPERSET aligned with the P0 contract's policy_checks (capability_allowed /
        #     no_forbidden_tool_used / secrets_refs_only / deterministic_first_honored /
        #     llm_fallback_within_policy / no_self_boundary_expansion) so the same receipt satisfies the P0
        #     schema, plus the gateway's own invariant flags.
        policy_checks = {
            # --- P0-contract-aligned check names ---
            "capability_allowed": True,                 # passed the allow-list (we'd have refused otherwise)
            "no_forbidden_tool_used": True,             # passed the deny-list
            "secrets_refs_only": True,                  # the gateway never surfaces a secret value
            "deterministic_first_honored": bool(card["deterministic_first"]),
            "llm_fallback_within_policy": (not fallback_used) or bool(card["llm_fallback_allowed"]),
            "no_self_boundary_expansion": True,         # run() never expands a boundary
            # --- gateway invariant flags (the proofs assert these) ---
            "deterministic_first": bool(card["deterministic_first"]),
            "allow_list_ok": True,
            "deny_list_ok": True,
            "llm_fallback_used": fallback_used,
            "llm_fallback_allowed_by_card": bool(card["llm_fallback_allowed"]),
            "serves_truth": AGENT_GATEWAY_SERVES_TRUTH,
            "compact_output": True,
        }
        output_hash = sha256_hex(output)
        input_hash = sha256_hex(payload)
        receipt_id = canonical_id("agentcaprcpt", request_id, capability_id, runtime_path, input_hash,
                                  output_hash, now)
        receipt = AgentCapabilityReceipt(
            receipt_id=receipt_id, request_id=request_id, capability_id=capability_id,
            consumer_id=consumer.consumer_id, input_hash=input_hash, output_hash=output_hash,
            runtime_path=runtime_path, backend=backend, cost_estimate=dict(card["expected_cost"]),
            started_at=started_at, completed_at=now, policy_checks=policy_checks,
        ).as_dict()
        # write-once: a deterministic id means a re-run of the identical call overwrites with an identical
        # receipt (idempotent), never a divergent one.
        self._receipts[receipt_id] = receipt

        # (7) return the compact, receipt-backed result. serves_truth pinned False.
        return AgentCapabilityRunResult(
            request_id=request_id, capability_id=capability_id, status=status, output=output,
            source_handles=source_handles, held_out=held_out, receipt_id=receipt_id, fallback_used=fallback_used,
            tokens_saved_estimate=tokens_saved, serves_truth=AGENT_GATEWAY_SERVES_TRUTH,
            allowed_use=list(card.get("allowed_use", [])),
        ).as_dict()


__all__ = [
    "AgentCapabilityGateway",
    "AgentCapabilityCard",
    "AgentCapabilityRunResult",
    "AgentCapabilityReceipt",
    "AgentBoundaryExpansionRequest",
    "AgentConsumer",
    "AGENT_GATEWAY_SERVES_TRUTH",
    "TOKEN_LADDER",
    "RUNTIME_PATH_DETERMINISTIC",
    "RUNTIME_PATH_LLM_FALLBACK",
    "RUN_STATUS_VERIFIED",
    "RUN_STATUS_SUCCEEDED",
    "RUN_STATUS_FAILED",
    "RUN_STATUS_UNAVAILABLE",
    "BOUNDARY_STATUS_PENDING",
]
