"""src.teleon.governance.org_policy — ORG guardrail policy: the confines a capability unit (and the AI that
heals/evolves it) must stay within.

Organizations have strict devops/security rules — only certain licenses, source domains, packages, runtime
classes, or methodologies are permitted. This evaluates a candidate (a provider endpoint, or an evolution/heal
RUNNER) against an org policy and produces a deny/allow decision with reasons. Two uses, both governed:

  * forbidden_endpoints(slot, policy) -> the endpoint_ids to EXCLUDE from objective selection (so a "minimize
    cost" priority can never pick a banned-license/off-domain provider — safety beats objective).
  * bounds_runner_change(runner, policy) -> may the AI promote/fork/heal TO this runner? A self-heal or an
    evolution descent that would cross the org's confines is VETOED (escalate to human) rather than crossing them.

deny_by_default + strict_unknown_license let a regulated org refuse anything it cannot positively verify.
Composes with the egress route policy (egress/policy.py) for outbound-route decisions; this adds the
license/package/runtime/methodology bounds. Pure + deterministic; reads shared DATA only; Teleon-layer — never
imports src.baltor. A policy decision is evidence, never a fact (serves_truth False on every decision).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from dataclasses import dataclass, field
from pathlib import Path

_POLICY_PATH = _resource("architecture") / "org_guardrail_policies.json"
_DET_EPS = 1e-9
#: domains treated as internal / non-public-egress (satisfy the no_external_egress methodology).
_INTERNAL_DOMAINS = ("", "local", "localhost", "internal", "port43-whois")
_UNKNOWN_LICENSES = ("", "unknown", "none", None)


class OrgPolicyError(ValueError):
    """Raised on an unknown policy_id or a malformed policy — never a silent allow."""


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reasons: tuple
    policy_id: str
    serves_truth: bool = False

    def as_dict(self) -> dict:
        return {"allowed": self.allowed, "reasons": list(self.reasons), "policy_id": self.policy_id,
                "serves_truth": False}


@dataclass(frozen=True)
class OrgGuardrailPolicy:
    policy_id: str
    deny_by_default: bool = False
    strict_unknown_license: bool = False
    allowed_licenses: tuple = ()
    denied_licenses: tuple = ()
    allowed_source_domains: tuple = ()
    denied_source_domains: tuple = ()
    allowed_runtime_classes: tuple = ()
    denied_packages: tuple = ()
    required_methodologies: tuple = ()

    @staticmethod
    def from_dict(policy_id: str, d: dict) -> "OrgGuardrailPolicy":
        g = lambda k: tuple(d.get(k, []) or [])
        return OrgGuardrailPolicy(
            policy_id=policy_id, deny_by_default=bool(d.get("deny_by_default", False)),
            strict_unknown_license=bool(d.get("strict_unknown_license", False)),
            allowed_licenses=g("allowed_licenses"), denied_licenses=g("denied_licenses"),
            allowed_source_domains=g("allowed_source_domains"), denied_source_domains=g("denied_source_domains"),
            allowed_runtime_classes=g("allowed_runtime_classes"), denied_packages=g("denied_packages"),
            required_methodologies=g("required_methodologies"))


def _load(registry: dict | None = None) -> dict:
    return registry if registry is not None else json.loads(_POLICY_PATH.read_text(encoding="utf-8"))


def policy_ids(*, registry: dict | None = None) -> list[str]:
    return sorted(_load(registry).get("policies", {}))


def load_policy(policy_id: str, *, registry: dict | None = None) -> OrgGuardrailPolicy:
    pols = _load(registry).get("policies", {})
    if policy_id not in pols:
        raise OrgPolicyError(f"unknown org policy {policy_id!r}; known: {sorted(pols)}")
    return OrgGuardrailPolicy.from_dict(policy_id, pols[policy_id])


def _domain_matches(domain: str, pattern: str) -> bool:
    """Exact match, or a leading-wildcard suffix match (``*.gov`` matches ``api.weather.gov`` and ``weather.gov``)."""
    if pattern == domain:
        return True
    if pattern.startswith("*."):
        suffix = pattern[1:]  # ".gov"
        return domain.endswith(suffix) or domain == pattern[2:]
    return False


def evaluate(attrs: dict, policy: OrgGuardrailPolicy) -> PolicyDecision:
    """Evaluate a candidate's attributes against the org policy. ``attrs`` may carry: license, source_domain,
    runtime_class, package, determinism, llm_usage, kind. Missing attributes are simply not constrained — except
    under strict_unknown_license (an unverifiable license is denied) and deny_by_default (a candidate with no
    positively-allowed signal on a constrained dimension is denied)."""
    reasons: list[str] = []

    # ── licenses (only when the candidate carries a license dimension — a plain runner does not) ──
    if "license" in attrs:
        lic = attrs["license"]
        if lic in policy.denied_licenses:
            reasons.append(f"license {lic!r} is on the org deny-list")
        if policy.allowed_licenses and lic not in policy.allowed_licenses and lic not in _UNKNOWN_LICENSES:
            reasons.append(f"license {lic!r} is not on the org allow-list")
        if policy.strict_unknown_license and lic in _UNKNOWN_LICENSES:
            reasons.append("license is unknown/unverified and the org denies unverified licenses")

    # ── source domain / egress (only when the candidate makes an outbound call) ──
    if "source_domain" in attrs:
        dom = attrs["source_domain"]
        if dom:
            if any(_domain_matches(dom, p) for p in policy.denied_source_domains):
                reasons.append(f"source domain {dom!r} is on the org deny-list")
            if policy.allowed_source_domains and not any(_domain_matches(dom, p) for p in policy.allowed_source_domains):
                reasons.append(f"source domain {dom!r} is not on the org allow-list")
        elif policy.deny_by_default and policy.allowed_source_domains:
            reasons.append("no source domain to verify against the org allow-list (deny-by-default)")

    # ── runtime class ──
    rc = attrs.get("runtime_class")
    if rc and policy.allowed_runtime_classes and rc not in policy.allowed_runtime_classes:
        reasons.append(f"runtime class {rc!r} is not on the org allow-list")

    # ── package ──
    pkg = attrs.get("package")
    if pkg and pkg in policy.denied_packages:
        reasons.append(f"package {pkg!r} is on the org deny-list")

    # ── methodologies ──
    det, kind, llm = attrs.get("determinism"), attrs.get("kind"), attrs.get("llm_usage")
    dom, lic = attrs.get("source_domain"), attrs.get("license")
    for m in policy.required_methodologies:
        if m == "deterministic_only" and (det is None or det < 1.0 - _DET_EPS):
            reasons.append("violates deterministic_only (runner is not fully deterministic)")
        elif m == "no_llm" and (kind in ("model", "open_ended") or (llm or 0) > 0):
            reasons.append("violates no_llm (runner uses a model/agent in the hot path)")
        elif m == "no_external_egress" and dom and dom not in _INTERNAL_DOMAINS:
            reasons.append(f"violates no_external_egress (public domain {dom!r})")
        elif m == "permissive_license_only" and policy.allowed_licenses and lic is not None and lic not in policy.allowed_licenses:
            reasons.append("violates permissive_license_only (license not on the allow-list)")
        elif m == "vetted_only" and attrs.get("vetted") is not True:
            reasons.append("violates vetted_only (candidate has not passed vetting/human review)")

    return PolicyDecision(allowed=not reasons, reasons=tuple(reasons), policy_id=policy.policy_id)


def evaluate_endpoint(endpoint, policy: OrgGuardrailPolicy) -> PolicyDecision:
    """A provider endpoint is a deterministic API/library call (determinism 1.0, no LLM); check its license,
    egress domain, and any denied package (library endpoints map their provider id to a package name)."""
    pkg = endpoint.endpoint_id.replace("-lib", "") if getattr(endpoint, "kind", "") == "library" else None
    return evaluate({"license": endpoint.license, "source_domain": endpoint.egress_domain,
                     "determinism": 1.0, "kind": "api", "llm_usage": 0, "package": pkg}, policy)


def evaluate_runner(runner, policy: OrgGuardrailPolicy) -> PolicyDecision:
    """An evolution/heal RUNNER (a RunnerNode or a dict): check its determinism/kind against the methodology
    rules + runtime class. This is what BOUNDS the AI's self-heal/fork — a runner that violates the org's
    confines is not an allowed fix."""
    get = (lambda k: getattr(runner, k, None)) if not isinstance(runner, dict) else runner.get
    attrs = {"determinism": get("determinism"), "kind": get("kind"), "llm_usage": get("llm_usage")}
    rc = get("runtime_class")
    if rc is not None:
        attrs["runtime_class"] = rc
    lic = get("license")
    if lic is not None:
        attrs["license"] = lic  # a runner wrapping a third-party tool may carry a license; a plain runner does not
    return evaluate(attrs, policy)


def forbidden_endpoints(capability_slot: str, policy: OrgGuardrailPolicy, *, registry: dict | None = None) -> set:
    """The endpoint_ids the policy disallows for a capability — feed straight into
    src.teleon.endpoints.select_endpoint(forbidden=...) so objective selection can never pick a banned provider."""
    from src.teleon.endpoints import endpoints_for
    return {ep.endpoint_id for ep in endpoints_for(capability_slot, registry=registry)
            if not evaluate_endpoint(ep, policy).allowed}


def bounds_runner_change(runner, policy: OrgGuardrailPolicy) -> PolicyDecision:
    """May the AI promote / fork / heal TO this runner under the org policy? If not, the self-heal or evolution
    descent must be VETOED and escalated — never cross the org's confines to make a fix."""
    return evaluate_runner(runner, policy)
