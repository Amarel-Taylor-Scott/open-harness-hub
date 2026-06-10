"""Policy-aware model route selection for Baltor and Open Harness Hub.

Workers should ask for a capability, not a concrete provider. This module picks
the first compliant local, hosted, or frontier route from deployment config and
returns a model-route decision record suitable for ledgers and audit packets.

Stdlib-only by design. The actual chat call still goes through
``scripts.model_routes`` or an OpenAI-compatible gateway.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from scripts.model_routes import DEFAULT_BASE_URL, DEFAULT_MODEL

LANE_ORDER = {
    "deterministic": 0,
    "local_efficient": 1,
    "open_weight_medium": 2,
    "open_weight_large": 3,
    "frontier_controlled": 4,
    "hermes_discovery": 5,
    "openclaw_audit": 5,
}

TRUST_ORDER = {"local": 0, "tenant": 1, "hosted": 2, "frontier": 3}
PRIVATE_SCOPES = {"private", "user", "tenant", "org"}
NON_COMMERCIAL_DEMO_ENVIRONMENTS = {"demo_noncommercial", "local_demo"}
NON_COMMERCIAL_USES = {"non_commercial", "demo", "research", "personal"}
LOW_TRUST_PROVIDER_TIERS = {"free_best_effort", "non_commercial_demo", "experimental_untrusted"}
SENSITIVE_CAPABILITIES = {
    "verification",
    "oracle.verify",
    "oracle.challenge",
    "claim.verify",
    "policy",
    "policy.decision",
    "audit_review",
    "context.receipt",
    "context_receipt",
    "private_summary",
    "source_handle.expand",
}


@dataclass(frozen=True)
class ModelRouteCandidate:
    adapter: str
    lane: str
    backend: str = "http-openai"
    model: str = DEFAULT_MODEL
    base_url: str | None = DEFAULT_BASE_URL
    provider: str = "local"
    provider_tier: str = "local"
    trust_boundary: str = "local"
    quality_tier: str = "local"
    capabilities: tuple[str, ...] = ("*",)
    modalities: tuple[str, ...] = ("text",)
    blocked_capabilities: tuple[str, ...] = ()
    allowed_environments: tuple[str, ...] = ()
    commercial_use: str = "unrestricted"
    api_key_env: str | None = None
    data_retention: str = "local"
    free_credit: bool = False
    enabled: bool = True
    estimated_cost_usd: float = 0.0
    latency_ms: int | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ModelRouteCandidate":
        return cls(
            adapter=str(raw.get("adapter") or raw.get("name") or raw.get("selected_adapter") or "unnamed"),
            lane=str(raw.get("lane") or "local_efficient"),
            backend=str(raw.get("backend") or "http-openai"),
            model=str(raw.get("model") or raw.get("model_id") or DEFAULT_MODEL),
            base_url=raw.get("base_url"),
            provider=str(raw.get("provider") or "configured"),
            provider_tier=str(raw.get("provider_tier") or raw.get("tier") or raw.get("trust_level") or "configured"),
            trust_boundary=str(raw.get("trust_boundary") or "hosted"),
            quality_tier=str(raw.get("quality_tier") or raw.get("lane") or "configured"),
            capabilities=tuple(str(v) for v in raw.get("capabilities", ["*"])),
            modalities=tuple(str(v) for v in raw.get("modalities", ["text"])),
            blocked_capabilities=tuple(str(v) for v in raw.get("blocked_capabilities", [])),
            allowed_environments=tuple(str(v) for v in raw.get("allowed_environments", [])),
            commercial_use=str(raw.get("commercial_use") or "unrestricted"),
            api_key_env=raw.get("api_key_env"),
            data_retention=str(raw.get("data_retention") or "unknown"),
            free_credit=bool(raw.get("free_credit", False)),
            enabled=bool(raw.get("enabled", True)),
            estimated_cost_usd=float(raw.get("estimated_cost_usd") or 0.0),
            latency_ms=int(raw["latency_ms"]) if raw.get("latency_ms") is not None else None,
        )

    def asdict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "lane": self.lane,
            "backend": self.backend,
            "model": self.model,
            "base_url": self.base_url,
            "provider": self.provider,
            "provider_tier": self.provider_tier,
            "trust_boundary": self.trust_boundary,
            "quality_tier": self.quality_tier,
            "capabilities": list(self.capabilities),
            "modalities": list(self.modalities),
            "blocked_capabilities": list(self.blocked_capabilities),
            "allowed_environments": list(self.allowed_environments),
            "commercial_use": self.commercial_use,
            "api_key_env": self.api_key_env,
            "data_retention": self.data_retention,
            "free_credit": self.free_credit,
            "enabled": self.enabled,
            "estimated_cost_usd": self.estimated_cost_usd,
            "latency_ms": self.latency_ms,
        }


@dataclass(frozen=True)
class ModelRouteRequest:
    task_type: str
    capability: str = "*"
    modality: tuple[str, ...] = ("text",)
    preferred_lane: str | None = None
    privacy_scope: str = "tenant"
    allow_cloud: bool = False
    allow_frontier: bool = False
    allow_free_credit: bool = True
    require_zero_data_retention: bool = False
    deployment_environment: str = "production"
    commercial_use: str = "commercial"
    max_cost_usd: float | None = None
    latency_budget_ms: int | None = None
    tenant_allowed_providers: tuple[str, ...] = ()

    @classmethod
    def from_task(cls, task: dict[str, Any]) -> "ModelRouteRequest":
        payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
        policy = task.get("model_policy")
        if not isinstance(policy, dict):
            policy = payload.get("model_policy") if isinstance(payload.get("model_policy"), dict) else {}
        data_policy = task.get("data_policy")
        if not isinstance(data_policy, dict):
            data_policy = payload.get("data_policy") if isinstance(payload.get("data_policy"), dict) else {}
        budget_policy = task.get("budget_policy")
        if not isinstance(budget_policy, dict):
            budget_policy = payload.get("budget_policy") if isinstance(payload.get("budget_policy"), dict) else {}
        modality = policy.get("modality") or policy.get("modalities") or task.get("modality") or ["text"]
        if isinstance(modality, str):
            modality = [modality]
        allowed = policy.get("tenant_allowed_providers") or data_policy.get("tenant_allowed_providers") or []
        return cls(
            task_type=str(task.get("task_type") or task.get("task") or ""),
            capability=str(policy.get("capability") or task.get("capability") or task.get("task_type") or task.get("task") or "*"),
            modality=tuple(str(v) for v in modality),
            preferred_lane=policy.get("lane") or task.get("model_lane"),
            privacy_scope=str(data_policy.get("privacy_scope") or policy.get("privacy_scope") or "tenant"),
            allow_cloud=bool(policy.get("allow_cloud") or data_policy.get("allow_cloud")),
            allow_frontier=bool(policy.get("allow_frontier")),
            allow_free_credit=bool(policy.get("allow_free_credit", True)),
            require_zero_data_retention=bool(data_policy.get("require_zero_data_retention") or policy.get("require_zero_data_retention")),
            deployment_environment=str(
                policy.get("deployment_environment")
                or data_policy.get("deployment_environment")
                or os.environ.get("BALTOR_DEPLOYMENT_ENV")
                or os.environ.get("OH_DEPLOYMENT_ENV")
                or "production"
            ),
            commercial_use=str(policy.get("commercial_use") or data_policy.get("commercial_use") or "commercial"),
            max_cost_usd=float(budget_policy["max_model_cost_usd"]) if budget_policy.get("max_model_cost_usd") is not None else None,
            latency_budget_ms=int(policy["latency_budget_ms"]) if policy.get("latency_budget_ms") is not None else None,
            tenant_allowed_providers=tuple(str(v) for v in allowed),
        )


@dataclass(frozen=True)
class CandidateReview:
    adapter: str
    accepted: bool
    reason_codes: tuple[str, ...] = field(default_factory=tuple)

    def asdict(self) -> dict[str, Any]:
        return {"adapter": self.adapter, "accepted": self.accepted, "reason_codes": list(self.reason_codes)}


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def default_candidates_from_env() -> list[ModelRouteCandidate]:
    """Return route candidates from env, with a local default for dev.

    ``OH_LLM_ROUTES`` may be a JSON array of candidate objects. If absent, the
    legacy ``OH_LLM_*`` variables become a single local route. Optional hosted
    fallback vars let local dev add one cloud route without a config file:
    ``OH_LLM_HOSTED_BASE_URL``, ``OH_LLM_HOSTED_MODEL``, ``OH_LLM_HOSTED_API_KEY_ENV``.
    """
    raw_routes = os.environ.get("OH_LLM_ROUTES")
    if raw_routes:
        data = json.loads(raw_routes)
        if not isinstance(data, list):
            raise ValueError("OH_LLM_ROUTES must be a JSON array")
        return [ModelRouteCandidate.from_dict(item) for item in data if isinstance(item, dict)]

    routes = [
        ModelRouteCandidate(
            adapter=os.environ.get("OH_LLM_ADAPTER") or "local-ollama",
            lane=os.environ.get("OH_LLM_LANE") or "local_efficient",
            backend=os.environ.get("OH_LLM_BACKEND") or "http-openai",
            model=os.environ.get("OH_LLM_MODEL") or DEFAULT_MODEL,
            base_url=os.environ.get("OH_LLM_BASE_URL") or DEFAULT_BASE_URL,
            provider=os.environ.get("OH_LLM_PROVIDER") or "ollama",
            provider_tier=os.environ.get("OH_LLM_PROVIDER_TIER") or "local",
            trust_boundary=os.environ.get("OH_LLM_TRUST_BOUNDARY") or "local",
            quality_tier=os.environ.get("OH_LLM_QUALITY_TIER") or "local_efficient",
            capabilities=_split_csv(os.environ.get("OH_LLM_CAPABILITIES")) or ("*",),
            modalities=_split_csv(os.environ.get("OH_LLM_MODALITIES")) or ("text",),
            blocked_capabilities=_split_csv(os.environ.get("OH_LLM_BLOCKED_CAPABILITIES")),
            allowed_environments=_split_csv(os.environ.get("OH_LLM_ALLOWED_ENVIRONMENTS")),
            commercial_use=os.environ.get("OH_LLM_COMMERCIAL_USE") or "unrestricted",
            api_key_env="OH_LLM_API_KEY" if os.environ.get("OH_LLM_API_KEY") else None,
            data_retention=os.environ.get("OH_LLM_DATA_RETENTION") or "local",
            free_credit=bool(os.environ.get("OH_LLM_FREE_CREDIT")),
            estimated_cost_usd=float(os.environ.get("OH_LLM_ESTIMATED_COST_USD") or 0.0),
        )
    ]
    if os.environ.get("OH_LLM_HOSTED_BASE_URL"):
        routes.append(
            ModelRouteCandidate(
                adapter=os.environ.get("OH_LLM_HOSTED_ADAPTER") or "hosted-openai-compatible",
                lane=os.environ.get("OH_LLM_HOSTED_LANE") or "open_weight_medium",
                backend="http-openai",
                model=os.environ.get("OH_LLM_HOSTED_MODEL") or os.environ.get("OH_LLM_MODEL") or DEFAULT_MODEL,
                base_url=os.environ.get("OH_LLM_HOSTED_BASE_URL"),
                provider=os.environ.get("OH_LLM_HOSTED_PROVIDER") or "hosted",
                provider_tier=os.environ.get("OH_LLM_HOSTED_PROVIDER_TIER") or "hosted",
                trust_boundary=os.environ.get("OH_LLM_HOSTED_TRUST_BOUNDARY") or "hosted",
                quality_tier=os.environ.get("OH_LLM_HOSTED_QUALITY_TIER") or "open_weight_medium",
                capabilities=_split_csv(os.environ.get("OH_LLM_HOSTED_CAPABILITIES")) or ("*",),
                modalities=_split_csv(os.environ.get("OH_LLM_HOSTED_MODALITIES")) or ("text",),
                blocked_capabilities=_split_csv(os.environ.get("OH_LLM_HOSTED_BLOCKED_CAPABILITIES")),
                allowed_environments=_split_csv(os.environ.get("OH_LLM_HOSTED_ALLOWED_ENVIRONMENTS")),
                commercial_use=os.environ.get("OH_LLM_HOSTED_COMMERCIAL_USE") or "unrestricted",
                api_key_env=os.environ.get("OH_LLM_HOSTED_API_KEY_ENV") or "OH_LLM_HOSTED_API_KEY",
                data_retention=os.environ.get("OH_LLM_HOSTED_DATA_RETENTION") or "unknown",
                free_credit=bool(os.environ.get("OH_LLM_HOSTED_FREE_CREDIT")),
                estimated_cost_usd=float(os.environ.get("OH_LLM_HOSTED_ESTIMATED_COST_USD") or 0.0),
            )
        )
    chatanywhere_key_env = os.environ.get("OH_LLM_CHATANYWHERE_API_KEY_ENV")
    if not chatanywhere_key_env:
        chatanywhere_key_env = "OH_LLM_CHATANYWHERE_API_KEY" if os.environ.get("OH_LLM_CHATANYWHERE_API_KEY") else "CHATANYWHERE_API_KEY"
    if os.environ.get(chatanywhere_key_env) or os.environ.get("OH_LLM_ENABLE_CHATANYWHERE_DEMO"):
        routes.append(
            ModelRouteCandidate(
                adapter=os.environ.get("OH_LLM_CHATANYWHERE_ADAPTER") or "chatanywhere-noncommercial-demo",
                lane=os.environ.get("OH_LLM_CHATANYWHERE_LANE") or "open_weight_medium",
                backend="http-openai",
                model=os.environ.get("OH_LLM_CHATANYWHERE_MODEL") or "gpt-3.5-turbo",
                base_url=os.environ.get("OH_LLM_CHATANYWHERE_BASE_URL") or "https://api.chatanywhere.tech/v1",
                provider="chatanywhere",
                provider_tier="non_commercial_demo",
                trust_boundary="hosted",
                quality_tier="demo_best_effort",
                capabilities=_split_csv(os.environ.get("OH_LLM_CHATANYWHERE_CAPABILITIES")) or (
                    "draft_enhancement",
                    "background_summary",
                    "public_summary",
                    "demo_chat",
                    "summary",
                ),
                modalities=("text",),
                blocked_capabilities=_split_csv(os.environ.get("OH_LLM_CHATANYWHERE_BLOCKED_CAPABILITIES")) or (
                    "verification",
                    "policy",
                    "audit_review",
                    "claim.verify",
                    "context.receipt",
                    "private_summary",
                ),
                allowed_environments=_split_csv(os.environ.get("OH_LLM_CHATANYWHERE_ALLOWED_ENVIRONMENTS")) or tuple(sorted(NON_COMMERCIAL_DEMO_ENVIRONMENTS)),
                commercial_use="non_commercial_only",
                api_key_env=chatanywhere_key_env,
                data_retention=os.environ.get("OH_LLM_CHATANYWHERE_DATA_RETENTION") or "unknown",
                free_credit=True,
                estimated_cost_usd=0.0,
            )
        )
    return routes


def _supports(candidate_values: tuple[str, ...], requested: tuple[str, ...] | str) -> bool:
    if "*" in candidate_values:
        return True
    values = (requested,) if isinstance(requested, str) else requested
    return all(value in candidate_values for value in values)


def _review_candidate(candidate: ModelRouteCandidate, request: ModelRouteRequest) -> CandidateReview:
    reasons: list[str] = []
    if not candidate.enabled:
        reasons.append("candidate_disabled")
    if candidate.api_key_env and not os.environ.get(candidate.api_key_env):
        reasons.append("api_key_missing")
    if not _supports(candidate.modalities, request.modality):
        reasons.append("modality_not_supported")
    if not _supports(candidate.capabilities, request.capability):
        reasons.append("capability_not_supported")
    if _supports(candidate.blocked_capabilities, request.capability):
        reasons.append("capability_blocked_by_provider_policy")
    if request.preferred_lane and candidate.lane != request.preferred_lane:
        reasons.append("preferred_lane_mismatch")
    if request.privacy_scope in PRIVATE_SCOPES and candidate.trust_boundary not in {"local", "tenant"} and not request.allow_cloud:
        reasons.append("cloud_not_allowed_for_private_scope")
    if candidate.trust_boundary == "frontier" and not request.allow_frontier:
        reasons.append("frontier_not_allowed")
    if request.require_zero_data_retention and candidate.data_retention not in {"zero", "local"}:
        reasons.append("zero_data_retention_required")
    if request.max_cost_usd is not None and candidate.estimated_cost_usd > request.max_cost_usd:
        reasons.append("cost_ceiling_exceeded")
    if request.latency_budget_ms is not None and candidate.latency_ms is not None and candidate.latency_ms > request.latency_budget_ms:
        reasons.append("latency_budget_exceeded")
    if request.tenant_allowed_providers and candidate.provider not in request.tenant_allowed_providers:
        reasons.append("provider_not_tenant_allowed")
    if candidate.free_credit and not request.allow_free_credit:
        reasons.append("free_credit_route_not_allowed")
    if candidate.allowed_environments and request.deployment_environment not in candidate.allowed_environments:
        reasons.append("deployment_environment_not_allowed")
    if candidate.provider_tier in LOW_TRUST_PROVIDER_TIERS:
        if request.privacy_scope in PRIVATE_SCOPES:
            reasons.append("low_trust_route_not_allowed_for_private_scope")
        if request.capability in SENSITIVE_CAPABILITIES:
            reasons.append("low_trust_route_not_allowed_for_sensitive_capability")
    if candidate.commercial_use == "non_commercial_only":
        if request.deployment_environment not in NON_COMMERCIAL_DEMO_ENVIRONMENTS:
            reasons.append("non_commercial_route_requires_demo_environment")
        if request.commercial_use not in NON_COMMERCIAL_USES:
            reasons.append("non_commercial_route_not_allowed_for_commercial_use")
    return CandidateReview(candidate.adapter, not reasons, tuple(reasons))


def _rank(candidate: ModelRouteCandidate, request: ModelRouteRequest) -> tuple[int, int, int, float, int, str]:
    lane_distance = abs(LANE_ORDER.get(candidate.lane, 99) - LANE_ORDER.get(request.preferred_lane or candidate.lane, LANE_ORDER.get(candidate.lane, 99)))
    trust = TRUST_ORDER.get(candidate.trust_boundary, 9)
    free_credit = 0 if candidate.free_credit and request.allow_free_credit else 1
    latency = candidate.latency_ms if candidate.latency_ms is not None else 999999
    return (lane_distance, trust, free_credit, candidate.estimated_cost_usd, latency, candidate.adapter)


def resolve_model_route(
    task: dict[str, Any],
    *,
    candidates: list[ModelRouteCandidate] | None = None,
    now: int | None = None,
) -> dict[str, Any]:
    """Resolve a compliant model route for a task envelope.

    The returned object matches ``schemas/model-route-record.schema.json`` and
    includes extra audit metadata for policy debugging.
    """
    request = ModelRouteRequest.from_task(task)
    route_candidates = candidates if candidates is not None else default_candidates_from_env()
    reviews = [_review_candidate(candidate, request) for candidate in route_candidates]
    accepted = [candidate for candidate, review in zip(route_candidates, reviews) if review.accepted]
    selected = sorted(accepted, key=lambda item: _rank(item, request))[0] if accepted else None
    route_seed = {
        "task_type": request.task_type,
        "capability": request.capability,
        "selected_adapter": selected.adapter if selected else "none",
        "time": now or int(time.time()),
    }
    route_id = "mr-" + sha256(json.dumps(route_seed, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return {
        "model_route_id": route_id,
        "task_type": request.task_type,
        "modality": list(request.modality),
        "selected_adapter": selected.adapter if selected else "none",
        "selected_model": selected.model if selected else "none",
        "candidate_adapters": [candidate.adapter for candidate in route_candidates],
        "trust_boundary": selected.trust_boundary if selected else "none",
        "provider_tier": selected.provider_tier if selected else "none",
        "commercial_use": selected.commercial_use if selected else "none",
        "cost_estimate": {"estimated_cost_usd": selected.estimated_cost_usd if selected else None},
        "latency_budget_ms": request.latency_budget_ms,
        "quality_tier": selected.quality_tier if selected else "none",
        "route_reason": "selected_first_compliant_policy_route" if selected else "no_compliant_model_route",
        "fallbacks": [review.asdict() for review in reviews],
        "policy": {
            "capability": request.capability,
            "preferred_lane": request.preferred_lane,
            "privacy_scope": request.privacy_scope,
            "allow_cloud": request.allow_cloud,
            "allow_frontier": request.allow_frontier,
            "allow_free_credit": request.allow_free_credit,
            "require_zero_data_retention": request.require_zero_data_retention,
            "deployment_environment": request.deployment_environment,
            "commercial_use": request.commercial_use,
            "max_cost_usd": request.max_cost_usd,
            "tenant_allowed_providers": list(request.tenant_allowed_providers),
        },
        "selected_route": selected.asdict() if selected else None,
    }


def _self_test() -> int:
    local = ModelRouteCandidate(
        adapter="local-gemma",
        lane="local_efficient",
        provider="ollama",
        trust_boundary="local",
        capabilities=("summary", "claim.extract"),
        modalities=("text", "image"),
    )
    hosted = ModelRouteCandidate(
        adapter="hosted-qwen",
        lane="open_weight_medium",
        provider="openrouter",
        trust_boundary="hosted",
        capabilities=("summary", "claim.extract"),
        modalities=("text",),
        free_credit=True,
        data_retention="zero",
        estimated_cost_usd=0.01,
    )
    frontier = ModelRouteCandidate(
        adapter="frontier-review",
        lane="frontier_controlled",
        provider="openai",
        trust_boundary="frontier",
        capabilities=("adjudicate",),
        modalities=("text",),
        estimated_cost_usd=1.25,
    )
    demo = ModelRouteCandidate(
        adapter="chatanywhere-noncommercial-demo",
        lane="open_weight_medium",
        provider="chatanywhere",
        provider_tier="non_commercial_demo",
        trust_boundary="hosted",
        capabilities=("draft_enhancement", "summary"),
        blocked_capabilities=("verification", "context.receipt", "private_summary"),
        allowed_environments=("demo_noncommercial", "local_demo"),
        commercial_use="non_commercial_only",
        modalities=("text",),
        free_credit=True,
    )
    private_task = {
        "task": "context.chunk.summary",
        "model_policy": {"capability": "summary", "lane": "local_efficient"},
        "data_policy": {"privacy_scope": "tenant"},
    }
    private_record = resolve_model_route(private_task, candidates=[hosted, local], now=1)
    assert private_record["selected_adapter"] == "local-gemma"
    cloud_task = {
        "task": "context.claim.extract",
        "model_policy": {"capability": "claim.extract", "allow_cloud": True, "lane": "open_weight_medium"},
        "data_policy": {"privacy_scope": "public", "require_zero_data_retention": True},
        "budget_policy": {"max_model_cost_usd": 0.02},
    }
    cloud_record = resolve_model_route(cloud_task, candidates=[hosted, local], now=1)
    assert cloud_record["selected_adapter"] == "hosted-qwen"
    blocked_record = resolve_model_route(cloud_task, candidates=[frontier], now=1)
    assert blocked_record["selected_adapter"] == "none"
    assert "frontier_not_allowed" in blocked_record["fallbacks"][0]["reason_codes"]
    demo_task = {
        "task": "context.demo.draft_enhancement",
        "model_policy": {
            "capability": "draft_enhancement",
            "allow_cloud": True,
            "deployment_environment": "demo_noncommercial",
            "commercial_use": "non_commercial",
        },
        "data_policy": {"privacy_scope": "public"},
    }
    demo_record = resolve_model_route(demo_task, candidates=[demo], now=1)
    assert demo_record["selected_adapter"] == "chatanywhere-noncommercial-demo"
    production_record = resolve_model_route(
        {
            "task": "context.demo.draft_enhancement",
            "model_policy": {"capability": "draft_enhancement", "allow_cloud": True},
            "data_policy": {"privacy_scope": "public"},
        },
        candidates=[demo],
        now=1,
    )
    assert production_record["selected_adapter"] == "none"
    assert "non_commercial_route_requires_demo_environment" in production_record["fallbacks"][0]["reason_codes"]
    private_demo_record = resolve_model_route(
        {
            "task": "context.demo.draft_enhancement",
            "model_policy": {
                "capability": "draft_enhancement",
                "allow_cloud": True,
                "deployment_environment": "demo_noncommercial",
                "commercial_use": "non_commercial",
            },
            "data_policy": {"privacy_scope": "tenant"},
        },
        candidates=[demo],
        now=1,
    )
    assert private_demo_record["selected_adapter"] == "none"
    assert "low_trust_route_not_allowed_for_private_scope" in private_demo_record["fallbacks"][0]["reason_codes"]
    print(
        json.dumps(
            {
                "ok": True,
                "private": private_record,
                "cloud": cloud_record,
                "blocked": blocked_record,
                "demo": demo_record,
                "production_demo_blocked": production_record,
                "private_demo_blocked": private_demo_record,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
