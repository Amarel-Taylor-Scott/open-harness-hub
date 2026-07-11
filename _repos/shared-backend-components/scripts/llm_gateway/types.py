#!/usr/bin/env python3
"""scripts.llm_gateway.types — LLM Gateway contracts (request/response/provider/validation/trace).

The rest of Baltor never calls OpenAI/Anthropic/Gemini/Ollama/vLLM directly — it builds an LLMRequest and
calls ``gateway.complete(request, policy)``. Every model interaction is governed (tenant policy, data
classification, cost/latency SLO), validated (schema/grounding/policy/cost), and traced (provider, model,
prompt_hash, model_config_hash, attempt). Secrets are referenced (``env://OPENAI_API_KEY``), never inlined.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


def _sha(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:24]


@dataclass
class RoutingPolicy:
    preferred_providers: list[str] = field(default_factory=list)
    fallback_providers: list[str] = field(default_factory=list)
    max_attempts: int = 3
    max_cost_usd: float = 0.25
    latency_slo_ms: int = 10000


@dataclass
class LLMRequest:
    request_id: str
    tenant_id: str
    task_type: str                         # e.g. conflict_explanation, relation_extraction
    prompt_id: str
    prompt_version: str
    schema_id: str                         # declared output JSON schema id
    data_classification: str = "internal"  # public | internal | customer_confidential | restricted
    required_output_mode: str = "json_schema"
    input_artifact_ids: list[str] = field(default_factory=list)
    prompt_text: str = ""
    input_payload: dict = field(default_factory=dict)
    routing_policy: RoutingPolicy = field(default_factory=RoutingPolicy)
    idempotency_key: str = ""

    def prompt_hash(self) -> str:
        return _sha({"prompt_id": self.prompt_id, "prompt_version": self.prompt_version, "text": self.prompt_text})

    def input_hash(self) -> str:
        return _sha({"artifacts": sorted(self.input_artifact_ids), "payload": self.input_payload})

    def cache_key(self, model_config_hash: str) -> str:
        return _sha({"in": self.input_hash(), "prompt": self.prompt_hash(), "model": model_config_hash,
                     "schema": self.schema_id})


@dataclass
class ValidationResult:
    transport_valid: bool = False
    schema_valid: bool = False
    grounding_valid: bool = False
    policy_valid: bool = False
    quality_valid: bool = False
    cost_valid: bool = False
    no_unknown_artifact_ids: bool = False
    no_promoted_claim_without_source: bool = False
    reasons: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all([self.transport_valid, self.schema_valid, self.grounding_valid, self.policy_valid,
                    self.cost_valid, self.no_unknown_artifact_ids, self.no_promoted_claim_without_source])

    def as_dict(self) -> dict:
        return {**{k: v for k, v in self.__dict__.items()}, "ok": self.ok}


@dataclass
class RetryDecision:
    retryable: bool
    reason: str


@dataclass
class LLMResponse:
    request_id: str
    provider: str
    model: str
    endpoint: str
    status: str                            # ok | invalid | unavailable | needs_human | policy_blocked
    output_json: dict = field(default_factory=dict)
    raw_response_ref: str = ""             # object-store ref (raw responses never inlined on dashboards)
    usage: dict = field(default_factory=dict)
    validation: dict = field(default_factory=dict)
    trace: dict = field(default_factory=dict)


@dataclass
class LLMTrace:
    request_id: str
    attempts: list = field(default_factory=list)

    def record(self, *, provider: str, model: str, prompt_hash: str, model_config_hash: str,
               attempt: int, status: str, validation: dict | None = None, reason: str = "") -> None:
        self.attempts.append({"provider": provider, "model": model, "prompt_hash": prompt_hash,
                              "model_config_hash": model_config_hash, "attempt": attempt, "status": status,
                              "validation": validation or {}, "reason": reason})
