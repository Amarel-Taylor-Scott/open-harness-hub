#!/usr/bin/env python3
"""scripts.llm_capability_router — the CORE of the provider-agnostic primitive-generation router. Hy3 is the
FIRST lane, not the only one. A JOB TYPE (ideation / spec / executor / labeling / schema-card / sensitive) is
mapped to an ORDERED list of provider LANES from the capability registry (config/llm_provider_capabilities.yaml),
and call() walks that ladder — reusing the flywheel's multi-key rotation + the shared _llm_client — under the
quota/compliance guardrail (scripts/llm_quota_manager.py).

OPERATING LAW: the LLM PROPOSES, the deterministic system DISPOSES. Routing is 0-token + deterministic; every
returned row is candidate=true, serves_truth=false; nothing here promotes or serves truth.

Policy (JOB_LANES):
  * ideation / esoteric_expansion / technology_stack_expansion / source_digest / spec_generation
        -> Hy3-first LONG-OUTPUT lane
  * executor_synthesis / adapter_generation / verifier_generation / fixture_generation / codebase_to_primitives
        -> STRONG-CODE lane (NVIDIA GLM -> Ollama Kimi -> OpenRouter qwen-coder -> Hy3)
  * labeling / triage / dedupe_judge / taxonomy                     -> CHEAP/FAST lane
  * schema_card / benchmark_task (strict schema)                    -> JSON / structured-output lane
  * sensitive / private_material (or any internal/sensitive/restricted data class)
        -> LOCAL-first (Ollama local); a cloud lane is used ONLY if it allows the data class AND a redactor passes

FALLBACK LADDER inside call(): retry-same-lane-once -> next lane (alt model / same family) -> lower-cost degraded
-> QUEUE (never silently dropped). Structured-output is requested where the lane supports it.

    python3 scripts/llm_capability_router.py --self-test        # offline, stub chat_fn, mutation-gated
    python3 scripts/llm_capability_router.py --print-routes      # show the routing table
    python3 scripts/llm_capability_router.py --call ideation --prompt "..."   # one live routed call
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

import yaml  # noqa: E402

from scripts import _llm_client as _L  # noqa: E402  REUSE: PROVIDERS + resolve_provider + chat
from scripts._config import NVIDIA_BUILD_DEFAULT_MODEL, OPENROUTER_HY3_FREE_MODEL  # noqa: E402  single-source ids
from scripts.hy3_overnight_flywheel import _THROTTLE_RE  # noqa: E402  REUSE: retryable-throttle classifier
from scripts.llm_quota_manager import (  # noqa: E402
    BOUNDARY, QuotaManager, estimate_cost, prompt_hash, schema_hash,
)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"llm_capability_router requires canonical_id; import failed: {exc}")

CONFIG_PATH = _sbc_boot / "config" / "llm_provider_capabilities.yaml"
SCHEMA_PATH = resource("schemas/llm_provider_capability.schema.json")
WEIGHTS_PATH = resource("dist") / "llm-router" / "lane_weights.json"

# ── data-class policy ──────────────────────────────────────────────────────────────────────────────────────
DATA_CLASSES: tuple[str, ...] = ("public", "synthetic", "internal", "sensitive", "restricted")
#: classes that force LOCAL-first routing (private material must not leave the box by default).
LOCAL_FIRST_CLASSES: frozenset[str] = frozenset({"internal", "sensitive", "restricted"})

# ── model ids (mirrored from _config where a canonical constant exists; the rest are drift-gated at runtime
#    against config/llm_provider_capabilities.yaml — every referenced model MUST be in its lane's models[]) ──
_HY3 = OPENROUTER_HY3_FREE_MODEL                       # "tencent/hy3:free"
_NVIDIA_GLM = NVIDIA_BUILD_DEFAULT_MODEL               # "z-ai/glm-5.2"
_OR_QWEN_CODER = "qwen/qwen3-coder:free"
_OR_QWEN_NEXT = "qwen/qwen3-next-80b-a3b-instruct:free"
_OR_GEMMA4 = "google/gemma-4-31b-it:free"
_OLLAMA_KIMI = "kimi-k2.7-code"
_OLLAMA_GLM = "glm-5.2"
_OLLAMA_LOCAL_MODEL = "gemma4"
_OMNIROUTE_AUTO = "auto"

# ── lane playlists (lane_id, model). A lane_id is a key of config/llm_provider_capabilities.yaml:providers. ──
_LONG_OUTPUT = [("openrouter", _HY3), ("omniroute", _OMNIROUTE_AUTO),
                ("nvidia", _NVIDIA_GLM), ("ollama_cloud", _OLLAMA_GLM)]
_STRONG_CODE = [("nvidia", _NVIDIA_GLM), ("ollama_cloud", _OLLAMA_KIMI),
                ("openrouter", _OR_QWEN_CODER), ("openrouter", _HY3)]
_CHEAP_FAST = [("openrouter", _OR_GEMMA4), ("openrouter", _OR_QWEN_NEXT), ("ollama_cloud", _OLLAMA_GLM)]
_JSON_STRUCTURED = [("nvidia", _NVIDIA_GLM), ("openrouter", _HY3), ("ollama_cloud", _OLLAMA_GLM)]
# NO LOCAL MODELS (owner directive 2026-07-08: local models crash this PC). Sensitive/restricted data therefore has
# NO eligible lane — it is NOT sent to a local model and NOT auto-sent to cloud (data safety); the router QUEUES it
# for human/redaction review instead of dropping it. For our public/synthetic primitive generation this never fires.
_SENSITIVE: list[tuple[str, str]] = []

#: job_type -> ordered lane playlist. Add a job type = one row (never a rewrite). Adding a lane = a YAML entry.
JOB_LANES: dict[str, list[tuple[str, str]]] = {
    "ideation": _LONG_OUTPUT, "esoteric_expansion": _LONG_OUTPUT,
    "technology_stack_expansion": _LONG_OUTPUT, "source_digest": _LONG_OUTPUT, "spec_generation": _LONG_OUTPUT,
    "executor_synthesis": _STRONG_CODE, "adapter_generation": _STRONG_CODE, "verifier_generation": _STRONG_CODE,
    "fixture_generation": _STRONG_CODE, "codebase_to_primitives": _STRONG_CODE,
    "labeling": _CHEAP_FAST, "triage": _CHEAP_FAST, "dedupe_judge": _CHEAP_FAST, "taxonomy": _CHEAP_FAST,
    "schema_card": _JSON_STRUCTURED, "benchmark_task": _JSON_STRUCTURED,
    "sensitive": _SENSITIVE, "private_material": _SENSITIVE,
}
DEFAULT_JOB_LANES = _LONG_OUTPUT

_REQUIRED_CAP_FIELDS: tuple[str, ...] = (
    "provider_id", "endpoint_type", "models", "context_window", "max_output_tokens",
    "supports_structured_output", "supports_json_mode", "supports_batch", "supports_prompt_caching",
    "rpm_limit", "tpm_limit", "concurrency_limit", "cost_input_per_million", "cost_output_per_million",
    "allowed_data_classes", "default_timeout_seconds", "status",
)
_ENDPOINT_TYPES = frozenset({"openrouter", "openai_compatible", "ollama_local", "omniroute", "custom_http", "nvidia"})
_STATUSES = frozenset({"active", "active_capped", "available_if_running", "degraded", "disabled"})

_JSON_INSTRUCTION = (
    "\n\nRespond with ONE JSON object only — no prose, no markdown fences. It must be valid, parseable JSON.")


# ── registry load + validation + drift gate ────────────────────────────────────────────────────────────────
def load_registry(path: Optional[Path] = None) -> dict[str, Any]:
    return yaml.safe_load((path or CONFIG_PATH).read_text(encoding="utf-8"))


def validate_registry(reg: dict[str, Any]) -> list[str]:
    """Deterministic structural validation (no jsonschema dependency). Returns a list of problems (empty=OK)."""
    problems: list[str] = []
    if not isinstance(reg, dict):
        return ["registry is not a mapping"]
    for key in ("registry_version", "data_classes", "providers"):
        if key not in reg:
            problems.append(f"missing top-level key: {key}")
    providers = reg.get("providers")
    if not isinstance(providers, dict) or not providers:
        problems.append("providers is not a non-empty mapping")
        return problems
    for lane_id, cap in providers.items():
        if not isinstance(cap, dict):
            problems.append(f"{lane_id}: capability is not a mapping")
            continue
        for f in _REQUIRED_CAP_FIELDS:
            if f not in cap:
                problems.append(f"{lane_id}: missing required field {f}")
        if cap.get("endpoint_type") not in _ENDPOINT_TYPES:
            problems.append(f"{lane_id}: bad endpoint_type {cap.get('endpoint_type')!r}")
        if cap.get("status") not in _STATUSES:
            problems.append(f"{lane_id}: bad status {cap.get('status')!r}")
        if not isinstance(cap.get("models"), list) or not cap.get("models"):
            problems.append(f"{lane_id}: models must be a non-empty list")
        for dc in cap.get("allowed_data_classes") or []:
            if dc not in DATA_CLASSES:
                problems.append(f"{lane_id}: unknown data class {dc!r}")
    return problems


def drift_problems(reg: dict[str, Any]) -> list[str]:
    """The runtime drift gate that keeps the YAML honest against the actual code:
    (1) every capability.provider_id is a key of _llm_client.PROVIDERS;
    (2) every model the JOB_LANES policy references exists in its lane's models[]."""
    problems: list[str] = []
    providers = reg.get("providers", {})
    for lane_id, cap in providers.items():
        if cap.get("provider_id") not in _L.PROVIDERS:
            problems.append(f"{lane_id}: provider_id {cap.get('provider_id')!r} is not a key of _llm_client.PROVIDERS")
    referenced = {(lid, m) for playlist in list(JOB_LANES.values()) + [_SENSITIVE] for lid, m in playlist}
    for lane_id, model in sorted(referenced):
        cap = providers.get(lane_id)
        if cap is None:
            problems.append(f"JOB_LANES references unknown lane_id {lane_id!r}")
        elif model not in (cap.get("models") or []):
            problems.append(f"JOB_LANES references model {model!r} not in {lane_id}.models")
    return problems


_REGISTRY_CACHE: Optional[dict[str, Any]] = None


def capabilities(reg: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """The validated providers map {lane_id: capability}. Cached for the default file."""
    global _REGISTRY_CACHE
    if reg is not None:
        return reg.get("providers", {})
    if _REGISTRY_CACHE is None:
        r = load_registry()
        problems = validate_registry(r) + drift_problems(r)
        if problems:
            raise SystemExit("llm_provider_capabilities.yaml invalid:\n  - " + "\n  - ".join(problems))
        _REGISTRY_CACHE = r
    return _REGISTRY_CACHE.get("providers", {})


# ── learned lane weights (per job-type order, from model_lane_bakeoff) — optional, self-healing ─────────────
_WEIGHTS_CACHE: Any = None


def load_weights(path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    global _WEIGHTS_CACHE
    p = path or WEIGHTS_PATH
    if path is None and _WEIGHTS_CACHE is not None:
        return _WEIGHTS_CACHE or None
    try:
        table = json.loads(p.read_text(encoding="utf-8")).get("job_lane_order")
    except (OSError, ValueError):
        table = None
    if path is None:
        _WEIGHTS_CACHE = table or False
    return table


def _job_lane_order(job_type: str, weights: Any = "auto") -> list[tuple[str, str]]:
    base = list(JOB_LANES.get(job_type, DEFAULT_JOB_LANES))
    if weights in (None, "off"):
        return base
    table = load_weights() if weights == "auto" else weights
    learned = (table or {}).get(job_type)
    if not learned:
        return base                                             # self-heal: unseen job -> policy default
    order = {lid: i for i, lid in enumerate(learned)}
    return sorted(base, key=lambda lm: order.get(lm[0], len(order) + 1))


# ── redaction rule for sensitive data leaving to a cloud lane ───────────────────────────────────────────────
def needs_redaction(lane: dict[str, Any], data_class: str) -> bool:
    """A non-local lane handling a LOCAL_FIRST data class must pass redaction first."""
    return data_class in LOCAL_FIRST_CLASSES and lane.get("endpoint_type") != "ollama_local"


def redaction_ok(lane: dict[str, Any], data_class: str, system: str, user: str,
                 redactor: Optional[Callable[[str, str], bool]]) -> bool:
    if not needs_redaction(lane, data_class):
        return True
    return bool(redactor) and bool(redactor(system, user))


def _lane_dict(lane_id: str, model: str, cap: dict[str, Any]) -> dict[str, Any]:
    return {"id": lane_id, "provider_id": cap["provider_id"], "model": model,
            "endpoint_type": cap["endpoint_type"], "base_url_override": cap.get("base_url_override"),
            "max_output_tokens": int(cap["max_output_tokens"]),
            "default_timeout_seconds": int(cap["default_timeout_seconds"]),
            "supports_json_mode": bool(cap["supports_json_mode"]),
            "supports_structured_output": bool(cap["supports_structured_output"]),
            "cost_input_per_million": float(cap["cost_input_per_million"]),
            "cost_output_per_million": float(cap["cost_output_per_million"]),
            "status": cap["status"], "allowed_data_classes": list(cap["allowed_data_classes"])}


def route(job_type: str, *, data_class: str = "public", capabilities_map: Optional[dict[str, Any]] = None,
          weights: Any = "auto") -> list[dict[str, Any]]:
    """job_type (+ data class) -> ORDERED list of runnable lane dicts. 0-token, deterministic. Sensitive/
    restricted/internal data forces LOCAL-first and filters out any lane that does not allow the class."""
    caps = capabilities_map if capabilities_map is not None else capabilities()
    playlist = _job_lane_order(job_type, weights)
    if data_class in LOCAL_FIRST_CLASSES:
        playlist = list(_SENSITIVE) + [lm for lm in playlist if lm not in _SENSITIVE]
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()                          # (lane_id, model) so alt-model-same-family survives
    for lane_id, model in playlist:
        cap = caps.get(lane_id)
        if not cap or (lane_id, model) in seen:
            continue
        if cap.get("status") == "disabled":
            continue
        if data_class not in (cap.get("allowed_data_classes") or []):
            continue                                            # cloud lanes drop out for sensitive data
        if model not in (cap.get("models") or []):
            continue                                            # drift guard (self-test proves it never fires)
        out.append(_lane_dict(lane_id, model, cap))
        seen.add((lane_id, model))
    return out


def route_table(weights: Any = "off") -> dict[str, list[str]]:
    """Inspection view: job_type -> ["lane_id:model", ...] for the public data class."""
    return {jt: [f"{ln['id']}:{ln['model']}" for ln in route(jt, weights=weights)] for jt in sorted(JOB_LANES)}


# ── the live drafting brain (reuses the flywheel's key rotation + the shared client) ────────────────────────
def _augment_json(system: str, lane: dict[str, Any]) -> str:
    if lane["supports_json_mode"] and "JSON" not in (system or "").upper():
        return (system or "") + _JSON_INSTRUCTION
    return system


def default_live_chat_fn() -> Callable[[dict[str, Any], str, str], dict[str, Any]]:
    """chat(lane, system, user) -> {text, usage, error, ...}. Cloud lanes reuse hy3_overnight_flywheel._real_chat
    (multi-key rotation + start-at-max-output + size-retry); local/override lanes call _llm_client.chat with the
    base_url override so private material stays on localhost."""
    from scripts.hy3_overnight_flywheel import _real_chat  # noqa: PLC0415 — lazy: no network at import
    cloud = _real_chat()

    def chat(lane: dict[str, Any], system: str, user: str) -> dict[str, Any]:
        override = lane.get("base_url_override")
        if override:
            prov = dict(_L.resolve_provider(lane["provider_id"]))
            prov["base_url"] = override
            return _L.chat(lane["model"], system, user, prov,
                           max_tokens=lane["max_output_tokens"], timeout=lane["default_timeout_seconds"])
        return cloud(lane["provider_id"], lane["model"], system, user)

    return chat


def _err_class(err: Any) -> str:
    s = str(err or "")
    if _THROTTLE_RE.search(s):
        return "throttled"
    head = s.split(":", 1)[0].strip()
    return (head[:40] or "error") if head else "error"


def _usage_tokens(usage: dict[str, Any], text: str, fallback_in: int) -> tuple[int, int]:
    in_tok = int(usage.get("prompt_tokens") or usage.get("input_tokens") or fallback_in)
    out_tok = int(usage.get("completion_tokens") or usage.get("output_tokens") or max(1, len(text) // 4))
    return in_tok, out_tok


def call(job_type: str, system: str, user: str, *, data_class: str = "public", campaign: str = "adhoc",
         job_id: Optional[str] = None, chat_fn: Optional[Callable[[dict, str, str], dict]] = None,
         quota: Optional[QuotaManager] = None, dry_run: bool = False, schema: Any = None,
         redactor: Optional[Callable[[str, str], bool]] = None,
         capabilities_map: Optional[dict[str, Any]] = None, weights: Any = "auto") -> dict[str, Any]:
    """Route the job then walk the fallback ladder: retry-same-lane-once -> next lane -> QUEUE (never dropped).
    Every attempt is quota-gated and ledger-recorded (redacted). serves_truth=false on every return."""
    qm = quota or QuotaManager(campaign=campaign, dry_run=dry_run)
    job_id = job_id or canonical_id("job", job_type, system, user)
    ph, sh = prompt_hash(user), schema_hash(schema)
    base = {"job_id": job_id, "job_type": job_type, "data_class": data_class, **BOUNDARY}

    if qm.kill_switch_active():
        qm.enqueue({"job_id": job_id, "job_type": job_type, "data_class": data_class, "user": user})
        return {**base, "status": "halted", "reason": "kill_switch_active", "attempts": []}

    lanes = route(job_type, data_class=data_class, capabilities_map=capabilities_map, weights=weights)
    if not lanes:
        qm.enqueue({"job_id": job_id, "job_type": job_type, "data_class": data_class, "user": user})
        return {**base, "status": "no_lane", "reason": "no_eligible_lane_for_data_class", "attempts": []}

    chat = chat_fn                                              # built lazily below so dry-run never touches network
    est_in = max(1, len(f"{system}{user}") // 4)
    attempts: list[dict[str, Any]] = []

    def _rec(lane: dict[str, Any], status: str, **extra: Any) -> None:
        qm.record(job_id=job_id, campaign=campaign, provider=lane["provider_id"], model=lane["model"],
                  lane=lane["id"], endpoint_type=lane["endpoint_type"], data_class=data_class,
                  prompt_hash=ph, schema_hash=sh, structured=lane["supports_json_mode"],
                  fallback=bool(attempts), status=status, **extra)

    for lane in lanes:
        if not redaction_ok(lane, data_class, system, user, redactor):
            attempts.append({"lane": lane["id"], "status": "skipped_redaction_required"})
            _rec(lane, "skipped_redaction_required")
            continue
        est_cost = estimate_cost(lane, est_in, lane["max_output_tokens"])
        ok, reason = qm.check(lane["provider_id"], lane["id"], estimated_cost=est_cost)
        if not ok:
            attempts.append({"lane": lane["id"], "status": f"quota_{reason}"})
            _rec(lane, f"quota_{reason}", estimated_cost=est_cost)
            continue
        if dry_run:
            _rec(lane, "dry_run", estimated_cost=est_cost, retry=0)
            return {**base, "status": "dry_run", "lane": lane["id"], "provider": lane["provider_id"],
                    "model": lane["model"], "estimated_cost": est_cost, "attempts": attempts}

        if chat is None:                                        # first real call -> build the live brain now
            chat = default_live_chat_fn()
        sys_prompt = _augment_json(system, lane)
        for retry in range(2):                                  # attempt + ONE retry on the SAME lane
            t0 = qm.clock()
            res = chat(lane, sys_prompt, user)
            latency = round(qm.clock() - t0, 3)
            res = res if isinstance(res, dict) else {"text": str(res)}
            text, err, usage = res.get("text") or "", res.get("error"), res.get("usage") or {}
            in_tok, out_tok = _usage_tokens(usage, text, est_in)
            actual_cost = (float(usage["cost"]) if usage.get("cost") is not None
                           else estimate_cost(lane, in_tok, out_tok))
            if err and _THROTTLE_RE.search(str(err)):
                _rec(lane, "throttled", error_class="throttled", retry=retry, latency_s=latency,
                     input_tokens=in_tok, output_tokens=out_tok, estimated_cost=est_cost, cost=0.0)
                if retry == 0:
                    continue                                    # retry-same-lane-once
                cooled = qm.cooldown(lane["id"])                # rest the lane, fall through to the next
                attempts.append({"lane": lane["id"], "status": "throttled_cooldown", "cooldown_s": cooled})
                break
            if err or not text.strip():
                _rec(lane, "error" if err else "empty", error_class=_err_class(err) if err else "empty_output",
                     retry=retry, latency_s=latency, estimated_cost=est_cost, cost=0.0)
                attempts.append({"lane": lane["id"], "status": "error" if err else "empty"})
                break
            qm.charge(lane["provider_id"], requests=1, tokens=out_tok, cost=actual_cost)
            qm.clear_streak(lane["id"])
            _rec(lane, "ok", retry=retry, latency_s=latency, input_tokens=in_tok, output_tokens=out_tok,
                 estimated_cost=est_cost, cost=actual_cost)
            return {**base, "status": "ok", "text": text, "lane": lane["id"], "provider": lane["provider_id"],
                    "model": lane["model"], "usage": usage, "cost": actual_cost, "latency_s": latency,
                    "retried": retry, "fell_back": bool(attempts), "attempts": attempts}

    qm.enqueue({"job_id": job_id, "job_type": job_type, "data_class": data_class, "user": user})
    return {**base, "status": "queued", "reason": "all_lanes_exhausted", "attempts": attempts}


# ── self-test (offline, deterministic, mutation-gated) ─────────────────────────────────────────────────────
def _stub_seq(*outs: dict[str, Any]) -> Callable[[dict, str, str], dict]:
    """A chat_fn that returns canned outputs in sequence (and counts calls)."""
    state = {"i": 0, "calls": []}

    def chat(lane: dict[str, Any], system: str, user: str) -> dict[str, Any]:
        state["calls"].append((lane["id"], system, user))
        out = outs[min(state["i"], len(outs) - 1)]
        state["i"] += 1
        return dict(out)

    chat.state = state  # type: ignore[attr-defined]
    return chat


def _self_test() -> int:
    import random  # noqa: PLC0415
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []

    reg = load_registry()
    caps = reg.get("providers", {})
    checks.append(("the shipped registry validates structurally + passes the drift gate",
                   validate_registry(reg) == [] and drift_problems(reg) == []))
    # MUTATION: a registry missing a required field is caught
    broken = json.loads(json.dumps(reg))
    del broken["providers"]["nvidia"]["max_output_tokens"]
    checks.append(("validation catches a missing required field (mutation gate)",
                   any("max_output_tokens" in p for p in validate_registry(broken))))
    # MUTATION: a JOB_LANES model not present in the lane's models is caught by the drift gate
    drift2 = json.loads(json.dumps(reg))
    drift2["providers"]["openrouter"]["models"] = ["something-else"]
    checks.append(("drift gate catches a JOB_LANES model missing from a lane's models",
                   any("not in openrouter.models" in p for p in drift_problems(drift2))))
    checks.append(("every capability.provider_id is a real _llm_client.PROVIDERS key",
                   all(c["provider_id"] in _L.PROVIDERS for c in caps.values())))

    # ROUTING POLICY (weights off -> pure policy, independent of any learned file)
    r_ideation = route("ideation", weights="off")
    checks.append(("ideation routes Hy3-FIRST (long-output lane)",
                   r_ideation[0]["id"] == "openrouter" and r_ideation[0]["model"] == _HY3))
    r_exec = route("executor_synthesis", weights="off")
    checks.append(("executor_synthesis routes the STRONG-CODE lane first (NVIDIA GLM, not Hy3)",
                   r_exec[0]["id"] == "nvidia" and r_exec[0]["model"] == _NVIDIA_GLM
                   and r_exec[0]["id"] != "openrouter"))
    checks.append(("alt-model-same-family survives dedup (executor keeps its openrouter qwen-coder AND hy3 tail)",
                   [(ln["id"], ln["model"]) for ln in r_exec].count(("openrouter", _HY3)) == 1
                   and ("openrouter", _OR_QWEN_CODER) in [(ln["id"], ln["model"]) for ln in r_exec]))
    r_label = route("labeling", weights="off")
    checks.append(("labeling routes the CHEAP/FAST lane first (gemma-4)",
                   r_label[0]["id"] == "openrouter" and r_label[0]["model"] == _OR_GEMMA4))
    r_schema = route("schema_card", weights="off")
    checks.append(("schema_card routes only json/structured-capable lanes",
                   len(r_schema) >= 1 and all(ln["supports_json_mode"] for ln in r_schema)))
    r_sensitive = route("spec_generation", data_class="sensitive", weights="off")
    checks.append(("NO LOCAL MODELS (owner): sensitive data has NO eligible lane (local forbidden + every cloud lane "
                   "filtered) -> empty -> the caller QUEUES it, never sends it local or unredacted-cloud",
                   r_sensitive == [] and not any(ln.get("endpoint_type") == "ollama_local"
                                                 for ln in route("labeling", data_class="sensitive", weights="off"))))
    r_unknown = route("totally_unknown_job", weights="off")
    checks.append(("an unknown job self-heals to the default (Hy3-first) lane",
                   r_unknown[0]["id"] == "openrouter" and r_unknown[0]["model"] == _HY3))

    # redaction rule (pure): a cloud lane must pass a redactor for sensitive data; local never needs one
    cloud_lane = _lane_dict("nvidia", _NVIDIA_GLM, caps["nvidia"])
    local_lane = _lane_dict("ollama_local", _OLLAMA_LOCAL_MODEL, caps["ollama_local"])
    checks.append(("redaction is required for a cloud lane on sensitive data, never for a local lane",
                   needs_redaction(cloud_lane, "sensitive") and not needs_redaction(local_lane, "sensitive")
                   and not needs_redaction(cloud_lane, "public")))
    checks.append(("redaction_ok blocks without a redactor, allows with a passing one",
                   (not redaction_ok(cloud_lane, "sensitive", "s", "u", None))
                   and redaction_ok(cloud_lane, "sensitive", "s", "u", lambda s, u: True)))

    _good = {"text": json.dumps({"name": "x", "python_body": "def x():\n    return 1"}), "usage": {"cost": 0.0}}
    _throttle = {"text": "", "error": "HTTP Error 429: Too Many Requests"}
    clk = {"t": 0.0}

    def _clock() -> float:
        clk["t"] += 1.0
        return clk["t"]

    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)

        def _qm(**kw: Any) -> QuotaManager:
            args: dict[str, Any] = {"campaign": "unit", "kill_switch_path": tp / "NO_STOP",
                                    "ledger_path": tp / "led.jsonl", "queue_path": tp / "q.jsonl",
                                    "clock": _clock, "rng": random.Random(3)}
            args.update(kw)
            return QuotaManager(**args)

        # SUCCESS on the first lane
        chat_ok = _stub_seq(_good)
        r1 = call("ideation", "sys", "please ideate PRIVATEWORD", chat_fn=chat_ok, quota=_qm())
        checks.append(("a first-lane success returns ok with the Hy3 lane, candidate-only",
                       r1["status"] == "ok" and r1["lane"] == "openrouter" and r1["fell_back"] is False
                       and r1["serves_truth"] is False))
        led = (tp / "led.jsonl").read_text()
        checks.append(("the ledger stored the prompt HASH, never the raw prompt text",
                       "PRIVATEWORD" not in led and ph_in(led)))

        # RETRY-SAME-ONCE then FALL THROUGH to the next lane
        chat_fallthrough = _stub_seq(_throttle, _throttle, _good)   # lane0 throttles twice, lane1 succeeds
        r2 = call("ideation", "sys", "u", chat_fn=chat_fallthrough, quota=_qm())
        calls = chat_fallthrough.state["calls"]  # type: ignore[attr-defined]
        checks.append(("throttle -> retry SAME lane once (2 calls) -> fall through to the next lane (success)",
                       r2["status"] == "ok" and r2["fell_back"] is True and r2["lane"] != "openrouter"
                       and [c[0] for c in calls[:2]] == ["openrouter", "openrouter"]
                       and calls[2][0] != "openrouter"))

        # ALL LANES EXHAUSTED -> QUEUED (never dropped)
        chat_dead = _stub_seq(_throttle)
        r3 = call("ideation", "sys", "u", chat_fn=chat_dead, quota=_qm())
        qtext = (tp / "q.jsonl").read_text()
        checks.append(("all lanes throttled -> job QUEUED (never silently dropped)",
                       r3["status"] == "queued" and "llm_generation_queue_row" in qtext))

        # KILL SWITCH halts before any chat call, and queues the job
        chat_guard = _stub_seq(_good)
        (tp / "STOP").write_text("halt")
        r4 = call("ideation", "sys", "u", chat_fn=chat_guard, quota=_qm(kill_switch_path=tp / "STOP"))
        checks.append(("the kill switch halts routing before any chat call",
                       r4["status"] == "halted" and chat_guard.state["i"] == 0))  # type: ignore[attr-defined]

        # DRY RUN records intent + estimated cost, calls nothing
        chat_dry = _stub_seq(_good)
        r5 = call("ideation", "sys", "u", chat_fn=chat_dry, quota=_qm(dry_run=True), dry_run=True)
        checks.append(("dry-run estimates + records without calling the model",
                       r5["status"] == "dry_run" and "estimated_cost" in r5
                       and chat_dry.state["i"] == 0))  # type: ignore[attr-defined]

        # learned weights reorder the playlist and self-heal for unseen jobs
        reordered = _job_lane_order("ideation", weights={"ideation": ["nvidia", "openrouter"]})
        checks.append(("learned weights reorder a job's lanes (nvidia lifted ahead of openrouter)",
                       reordered[0][0] == "nvidia"))

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - llm_capability_router: {len(JOB_LANES)} job types over {len(caps)} capability lanes; "
          "Hy3-first for ideation, strong-code lane for executors, cheap lane for labeling, json lane for "
          "schema cards; NO local models (owner: they crash the PC) so sensitive data has no lane -> queued; "
          "fallback ladder retries-same-once, falls "
          "through, and QUEUES (never drops); kill switch + quota + redacting ledger enforced. "
          "Offline, deterministic. serves_truth=false.")
    return 0


def ph_in(ledger_text: str) -> bool:
    return any('"prompt_hash": "prompt-' in ln for ln in ledger_text.splitlines())


def _print_routes() -> int:
    print(json.dumps({"record_type": "llm_router_route_table", "job_types": route_table(weights="off"),
                      "data_classes": list(DATA_CLASSES), **BOUNDARY}, indent=2, sort_keys=True))
    return 0


def _call_cli(job_type: str, prompt: str, data_class: str, dry_run: bool) -> int:
    system = "You mint deterministic primitives. Output only what is asked."
    res = call(job_type, system, prompt, data_class=data_class, campaign="cli", dry_run=dry_run)
    safe = {k: res.get(k) for k in ("status", "lane", "provider", "model", "cost", "estimated_cost",
                                    "latency_s", "retried", "fell_back", "reason", "job_id") if k in res}
    if res.get("status") == "ok":
        safe["text_chars"] = len(res.get("text") or "")
    print(json.dumps({**safe, "attempts": res.get("attempts")}, indent=2, sort_keys=True))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--print-routes", action="store_true", help="print the job-type -> lane routing table")
    ap.add_argument("--call", metavar="JOB_TYPE", help="make one live routed call")
    ap.add_argument("--prompt", default="", help="prompt body for --call")
    ap.add_argument("--data-class", default="public", choices=list(DATA_CLASSES))
    ap.add_argument("--dry-run", action="store_true", help="estimate + record, never call the model")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.print_routes:
        return _print_routes()
    if args.call:
        return _call_cli(args.call, args.prompt, args.data_class, args.dry_run)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
