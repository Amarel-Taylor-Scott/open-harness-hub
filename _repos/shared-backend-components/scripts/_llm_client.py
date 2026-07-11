"""scripts._llm_client — SHARED OpenAI-compatible LLM client (used by BOTH planes; depends on neither plane's tools).

The PRODUCT runtime (_repos/teleon/backend/src/teleon/dag/real_steps) and the DEVELOPMENT tools (external_review / panel_review /
multi_model_improvement_loop) both need to call a model. Putting the client HERE (shared infra, like scripts/_jsonl_store)
means product never imports a dev tool and dev never owns product runtime. Provider lanes (Ollama Cloud default,
OpenRouter) + a reasoning-model-aware chat(). Keys are read from .env, never logged. serves_truth=false (a model call
returns a candidate, never truth). Offline-safe (no key -> error surfaced, not raised into the loop).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import fcntl
import json
import os
import datetime as dt
import sys
import time
import urllib.request
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:  # self-bootstrap so `python3 _repos/shared-backend-components/scripts/_llm_client.py --self-test` works without PYTHONPATH=.
    sys.path.insert(0, str(REPO))
from scripts._config import (  # noqa: E402
    AIDEVOBSERVER_OLLAMA_API_KEY_ENV,
    AIDEVOBSERVER_OLLAMA_CLOUD_BASE_URL,
    NVIDIA_BUILD_BASE_URL,
    NVIDIA_BUILD_DEFAULT_MODEL,
    GEMMA_MIN_CALL_INTERVAL_SECONDS,
    GEMMA_RATE_LIMIT_MAX_SLEEP_SECONDS,
    LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
    OPENWEBUI_BASE_URL_ENV,
    OPENWEBUI_CHAT_COMPLETIONS_PATH,
    OPENWEBUI_DEFAULT_BASE_URL,
    OPENWEBUI_DEFAULT_MODEL,
    OPENWEBUI_TOKEN_ENV,
    PRIMITIVE_FACTORY_GEMMA_PAUSE_FILE,
    PRIMITIVE_FACTORY_GEMMA_RATE_LIMIT_FILE,
    PRIMITIVE_FACTORY_GEMMA_SESSION_DOWN_FILE,
    PRIMITIVE_FACTORY_OLLAMA_PAUSE_FILE,
)

#: provider lanes. Ollama/OpenRouter use OpenAI-compatible /v1/chat/completions;
#: Open WebUI exposes the same request/response shape at /api/chat/completions.
PROVIDERS = {
    "ollama": {"base_url_var": "OH_LLM_BASE_URL", "base_url_default": AIDEVOBSERVER_OLLAMA_CLOUD_BASE_URL,
               "key_var": "OH_LLM_API_KEY", "key_var_alternates": [AIDEVOBSERVER_OLLAMA_API_KEY_ENV],
               "models": ["glm-5.2", "kimi-k2.7-code"], "headers": {}, "chat_path": "/chat/completions"},
    # OpenRouter — multi-key ready (key_var_alternates lets you add several keys; first non-empty wins).
    # tencent/hy3:free = Tencent Hy3 (295B MoE / 21B active, native 256K ctx, agentic-optimized) — FREE on
    # OpenRouter (cost $0, live-verified 2026-07-08). Reasons HEAVILY (default mode spends most tokens on
    # reasoning), so give it a generous max_tokens; the client already falls back to `reasoning` when content
    # is empty. Good for testing, primitive generation, and raw-material digestion/interrogation/preprocessing.
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_var": "OPENROUTER_API_KEY",
                   "key_var_alternates": ["OPENROUTER_API_KEY_2", "OPENROUTER_API_KEY_3"],
                   "models": ["tencent/hy3:free", "z-ai/glm-5.2", "moonshotai/kimi-k2.7-code"],
                   "headers": {"HTTP-Referer": "https://aidoneright.dev", "X-Title": "OpenHubForAI"},
                   "chat_path": "/chat/completions"},
    "openwebui": {"base_url_var": OPENWEBUI_BASE_URL_ENV, "base_url_default": OPENWEBUI_DEFAULT_BASE_URL,
                  "key_var": OPENWEBUI_TOKEN_ENV, "models": [OPENWEBUI_DEFAULT_MODEL],
                  "headers": {}, "chat_path": OPENWEBUI_CHAT_COMPLETIONS_PATH},
    # NVIDIA Build (integrate.api.nvidia.com) — OpenAI-compatible GLM 5.2; survives the Ollama Cloud usage
    # cap and the OpenWebUI Cloudflare wall (live-verified 2026-07-07 with real usage payloads).
    "nvidia": {"base_url": NVIDIA_BUILD_BASE_URL, "key_var": "NVIDIA_API_KEY",
               "models": [NVIDIA_BUILD_DEFAULT_MODEL], "headers": {}, "chat_path": "/chat/completions"},
    # OmniRoute (github.com/diegosouzapw/OmniRoute, MIT) — a LOCAL OpenAI-compatible gateway on :20128 that
    # auto-fails-over across 236 providers (incl. Hy3) in ~8ms, aggregating the free tiers YOU sign into (it
    # supplies no keys of its own). Model "auto" = its 9-factor router; a lane may also name a specific model.
    # x-omniroute-compression=off is DELIBERATE: its compression is LOSSY (terse-prose) and would truncate/degrade
    # primitive generation + violate the lossless-distillation law — we want the routing/fallback, never the lossy
    # squeeze. Off by default (only used when a lane selects "omniroute" AND the local gateway is running).
    "omniroute": {"base_url_var": "OMNIROUTE_BASE_URL", "base_url_default": "http://localhost:20128/v1",
                  "key_var": "OMNIROUTE_API_KEY", "key_var_alternates": [], "models": ["auto"],
                  "headers": {"x-omniroute-compression": "off"}, "chat_path": "/chat/completions"},
}
DEFAULT_PROVIDER = "ollama"

#: Ollama Cloud usage-cap circuit breaker. When the shared account hits its session usage limit the API first
#: returns 429s whose body carries these markers, then HOLDS requests instead of 429ing — so every later call
#: burns the full lane timeout (300-480s) and is recorded as a misleading TimeoutError. On a marker hit we write
#: OLLAMA_PAUSE.json (same shape as GEMMA_PAUSE.json) and short-circuit ollama calls until it expires.
OLLAMA_USAGE_LIMIT_MARKER_SESSION = "reached your session usage limit"  # definitive: the account cap is exhausted
OLLAMA_USAGE_LIMIT_MARKER_WEEKLY = "reached your weekly usage limit"  # longer account-level quota exhaustion
OLLAMA_USAGE_LIMIT_MARKER_CONCURRENT = "too many concurrent requests"  # cap symptom under load (can also be transient)
OLLAMA_USAGE_LIMIT_MARKERS = (
    OLLAMA_USAGE_LIMIT_MARKER_SESSION,
    OLLAMA_USAGE_LIMIT_MARKER_WEEKLY,
    OLLAMA_USAGE_LIMIT_MARKER_CONCURRENT,
)
OLLAMA_USAGE_PAUSE_SECONDS = 3600  # 1 hour — long enough to stop timeout burns, short enough to re-probe the cap
OLLAMA_WEEKLY_USAGE_PAUSE_SECONDS = 86400  # 24h re-probe cadence for weekly account-cap errors.
OLLAMA_CONCURRENT_PAUSE_SECONDS = 180  # 3 minutes — concurrency-cap 429s are transient load spikes, not an exhausted
#: account; a 1h pause on the first burst would strangle healthy lanes (observed 2026-07-02: fleet fan-out re-tripped
#: hour-long pauses on "too many concurrent requests" while the account still had credit).
OLLAMA_USAGE_PAUSE_ERROR_LABEL = "ollama_usage_pause_active"  # grep-able label for failed_model_outputs rows
OLLAMA_USAGE_PAUSE_REF_MARKER = "usage_limit_429"
OLLAMA_USAGE_PAUSE_REASON_MAX_CHARS = 300  # keep the recorded error snippet bounded (the 429 body repeats per call)
_OLLAMA_PAUSE_PATH_OVERRIDE: Path | None = None  # self-test only — never write the real pause file from a test

#: Gemma/Open WebUI lane breaker + severe limiter. The Open WebUI origin sits behind a Cloudflare edge on a
#: single shared GPU box. Two independent guards (both scoped to provider "openwebui", the ONLY lane that
#: reaches that GPU — non-gemma models on other providers are untouched by construction):
#: 1) SESSION-DOWN breaker — an edge 5xx means the ORIGIN is down (521/522/523/530) or degraded
#:    (502/504/520/524). We write GEMMA_SESSION_DOWN.json (never touching the operator-controlled
#:    GEMMA_PAUSE.json) so every worker fails fast with a labeled row instead of burning shards
#:    (observed 2026-07-02: 100+ shards burned against status=521 in one batch run).
#: 2) RATE LIMITER — owner 2026-07-02: "we have overloaded something on that GPU hardware". ONE gemma call
#:    at a time fleet-wide (fcntl lock held for the call duration) + minimum spacing between calls,
#:    measured from the END of the previous call (stricter; the GPU cools between generations).
GEMMA_SESSION_DOWN_ERROR_LABEL = "gemma_session_down_pause_active"  # grep-able label for failed_model_outputs rows
GEMMA_SESSION_DOWN_REF_MARKER = "cloudflare_origin_5xx"
GEMMA_ORIGIN_DOWN_STATUSES = (521, 522, 523, 530)  # edge cannot reach/complete a connection to the origin at all
GEMMA_ORIGIN_DEGRADED_STATUSES = (502, 504, 520, 524)  # origin reachable but erroring/too slow (524 = >120s proxy read window)
GEMMA_SESSION_DOWN_PAUSE_SECONDS = 600  # 10 min — an origin restart is an operator action; short enough to self-resume soon after
GEMMA_SESSION_DEGRADED_PAUSE_SECONDS = 180  # 3 min — degraded origins are often transient (mirrors OLLAMA_CONCURRENT_PAUSE_SECONDS rationale)
GEMMA_RATE_LIMITED_ERROR_LABEL = "gemma_rate_limited"  # labeled fail-fast so shard workers requeue instead of piling onto the GPU
_GEMMA_PAUSE_PATH_OVERRIDE: Path | None = None  # self-test only
_GEMMA_SESSION_DOWN_PATH_OVERRIDE: Path | None = None  # self-test only
_GEMMA_RATE_LIMIT_PATH_OVERRIDE: Path | None = None  # self-test only — never lock/write the real state file from a test


def _env(var: str) -> str:
    if os.environ.get(var):
        return os.environ[var]
    f = REPO / ".env"
    if not f.exists():
        return ""
    for ln in f.read_text(encoding="utf-8").splitlines():
        if ln.startswith(f"{var}="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _parse_utc_time(value: object) -> dt.datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _gemma_pause_error(*, model: str, provider: dict) -> str:
    if provider.get("name") != "openwebui":
        return ""
    pause_path = _GEMMA_PAUSE_PATH_OVERRIDE or (_resource(PRIMITIVE_FACTORY_GEMMA_PAUSE_FILE))
    payload = _read_json(pause_path)
    if not payload or payload.get("enabled") is False:
        return ""
    models = payload.get("models")
    paused_models = {str(item) for item in models} if isinstance(models, list) else {OPENWEBUI_DEFAULT_MODEL}
    if model not in paused_models:
        return ""
    expires_at = _parse_utc_time(payload.get("expires_at_utc") or payload.get("expires_at"))
    now = dt.datetime.now(dt.timezone.utc)
    if expires_at and now >= expires_at:
        return ""
    until = expires_at.isoformat() if expires_at else "the pause file is disabled"
    reason = str(payload.get("reason") or "gemma_calls_paused")
    return f"Gemma Open WebUI calls are paused until {until}: {reason}"


def _ollama_pause_path() -> Path:
    return _OLLAMA_PAUSE_PATH_OVERRIDE or (_resource(PRIMITIVE_FACTORY_OLLAMA_PAUSE_FILE))


def _is_ollama_cloud_provider(provider: dict) -> bool:
    """True only for the hosted Ollama lane.

    The local Ollama daemon exposes an OpenAI-compatible endpoint too
    (`http://127.0.0.1:11434/v1`). The account-level cloud quota breaker must
    not suppress local model calls.
    """
    if provider.get("name") != "ollama":
        return False
    base_url = str(provider.get("base_url") or "")
    return "ollama.com" in base_url


def _ollama_pause_error(*, model: str, provider: dict) -> str:
    """Non-empty when an unexpired Ollama usage pause is on file. The usage cap is ACCOUNT-wide, so the pause
    covers every ollama model (the payload `models` list records what tripped it — attribution, not a filter)."""
    if not _is_ollama_cloud_provider(provider):
        return ""
    payload = _read_json(_ollama_pause_path())
    if not payload or payload.get("enabled") is False:
        return ""
    expires_at = _parse_utc_time(payload.get("expires_at_utc") or payload.get("expires_at"))
    now = dt.datetime.now(dt.timezone.utc)
    if expires_at and now >= expires_at:
        return ""
    until = expires_at.isoformat() if expires_at else "the pause file is disabled"
    reason = str(payload.get("reason") or "ollama_usage_limit_pause")
    return f"{OLLAMA_USAGE_PAUSE_ERROR_LABEL}: Ollama Cloud calls are paused until {until}: {reason} (model {model})"


def _write_ollama_usage_pause(*, model: str, reason: str, pause_seconds: int = OLLAMA_USAGE_PAUSE_SECONDS) -> None:
    """Trip the breaker: record the usage-cap hit so concurrent workers fail fast until the pause expires.
    Never shortens a pause already on file (e.g. operator-requested) that expires later than ours would."""
    pause_path = _ollama_pause_path()
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    expires = now + dt.timedelta(seconds=pause_seconds)
    existing = _read_json(pause_path)
    existing_expires = _parse_utc_time(existing.get("expires_at_utc") or existing.get("expires_at"))
    if existing.get("enabled") is not False and existing_expires and existing_expires >= expires:
        return
    payload = {
        "candidate": True,
        "created_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "enabled": True,
        "expires_at_utc": expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "models": [model],
        "providers": ["ollama"],
        "reason": " ".join(str(reason).split())[:OLLAMA_USAGE_PAUSE_REASON_MAX_CHARS],
        "ref_marker": OLLAMA_USAGE_PAUSE_REF_MARKER,
        "requested_by": "circuit_breaker",
        "serves_truth": False,
    }
    try:
        pause_path.parent.mkdir(parents=True, exist_ok=True)
        pause_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        pass  # breaker is best-effort — never let pause-file IO mask the provider error we are reporting


def _ollama_error_with_usage_pause(*, model: str, provider: dict, error_text: str, timed_out: bool) -> str:
    """Classify an ollama-lane chat() failure. A usage-cap 429 body trips the breaker (writes the pause file)
    and gets the pause label; a read timeout while the pause is active (possibly written by a concurrent worker
    mid-flight) gets the label too, so failed_model_outputs rows stay attributable instead of recording a bare
    misleading TimeoutError. Every other error passes through untouched."""
    if not _is_ollama_cloud_provider(provider):
        return error_text
    lowered = error_text.lower()
    if any(marker in lowered for marker in OLLAMA_USAGE_LIMIT_MARKERS):
        # Weekly/session-cap exhaustion pauses longer; a concurrency burst is transient and pauses briefly.
        session_hit = OLLAMA_USAGE_LIMIT_MARKER_SESSION in lowered
        weekly_hit = OLLAMA_USAGE_LIMIT_MARKER_WEEKLY in lowered
        ttl = (
            OLLAMA_WEEKLY_USAGE_PAUSE_SECONDS
            if weekly_hit
            else OLLAMA_USAGE_PAUSE_SECONDS
            if session_hit
            else OLLAMA_CONCURRENT_PAUSE_SECONDS
        )
        _write_ollama_usage_pause(model=model, reason=error_text, pause_seconds=ttl)
        return f"{OLLAMA_USAGE_PAUSE_ERROR_LABEL}: {error_text}"
    if timed_out and _ollama_pause_error(model=model, provider=provider):
        return (f"{OLLAMA_USAGE_PAUSE_ERROR_LABEL} (read timed out while the Ollama usage pause is active): "
                f"{error_text}")
    return error_text


def _is_gemma_openwebui_provider(provider: dict) -> bool:
    """True for the Open WebUI lane — the only lane that reaches the shared Gemma GPU box."""
    return provider.get("name") == "openwebui"


def _gemma_session_down_path() -> Path:
    return _GEMMA_SESSION_DOWN_PATH_OVERRIDE or (_resource(PRIMITIVE_FACTORY_GEMMA_SESSION_DOWN_FILE))


def _gemma_rate_limit_path() -> Path:
    return _GEMMA_RATE_LIMIT_PATH_OVERRIDE or (_resource(PRIMITIVE_FACTORY_GEMMA_RATE_LIMIT_FILE))


def gemma_session_down_ttl_for_status(status: object) -> int:
    """Breaker TTL for an HTTP status observed on the Open WebUI lane. 0 = not a breaker status
    (auth errors, model errors, and 2xx never trip the origin breaker — pausing would mask them)."""
    try:
        code = int(status)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    if code in GEMMA_ORIGIN_DOWN_STATUSES:
        return GEMMA_SESSION_DOWN_PAUSE_SECONDS
    if code in GEMMA_ORIGIN_DEGRADED_STATUSES:
        return GEMMA_SESSION_DEGRADED_PAUSE_SECONDS
    return 0


def gemma_session_down_error(*, model: str, provider: dict) -> str:
    """Non-empty when an unexpired Gemma session-down breaker pause is on file (Open WebUI lane only)."""
    if not _is_gemma_openwebui_provider(provider):
        return ""
    payload = _read_json(_gemma_session_down_path())
    if not payload or payload.get("enabled") is False:
        return ""
    expires_at = _parse_utc_time(payload.get("expires_at_utc") or payload.get("expires_at"))
    now = dt.datetime.now(dt.timezone.utc)
    if expires_at and now >= expires_at:
        return ""
    until = expires_at.isoformat() if expires_at else "the pause file is disabled"
    reason = str(payload.get("reason") or "gemma_session_down")
    return (f"{GEMMA_SESSION_DOWN_ERROR_LABEL}: the Open WebUI origin is down/degraded; gemma calls fail fast "
            f"until {until}: {reason} (model {model})")


def record_gemma_session_down(*, model: str, status: object, reason: str, now: dt.datetime | None = None) -> str:
    """Trip the origin breaker for a Cloudflare-edge 5xx. Returns the labeled error text ("" when the status
    is not a breaker status). Never shortens a pause already on file that expires later than ours would,
    and never touches the operator-controlled GEMMA_PAUSE.json."""
    ttl = gemma_session_down_ttl_for_status(status)
    if ttl <= 0:
        return ""
    pause_path = _gemma_session_down_path()
    now = (now or dt.datetime.now(dt.timezone.utc)).replace(microsecond=0)
    expires = now + dt.timedelta(seconds=ttl)
    existing = _read_json(pause_path)
    existing_expires = _parse_utc_time(existing.get("expires_at_utc") or existing.get("expires_at"))
    reason_text = " ".join(str(reason).split())[:OLLAMA_USAGE_PAUSE_REASON_MAX_CHARS]
    if not (existing.get("enabled") is not False and existing_expires and existing_expires >= expires):
        payload = {
            "candidate": True,
            "created_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "enabled": True,
            "expires_at_utc": expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "http_status": int(status),  # type: ignore[arg-type]
            "models": [model],
            "providers": ["openwebui"],
            "reason": reason_text,
            "ref_marker": GEMMA_SESSION_DOWN_REF_MARKER,
            "requested_by": "circuit_breaker",
            "serves_truth": False,
        }
        try:
            pause_path.parent.mkdir(parents=True, exist_ok=True)
            pause_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError:
            pass  # breaker is best-effort — never let pause-file IO mask the provider error we are reporting
    return f"{GEMMA_SESSION_DOWN_ERROR_LABEL}: {reason_text}"


def _gemma_error_with_session_down(*, model: str, provider: dict, error_text: str, status: object) -> str:
    """Classify an Open WebUI lane failure: an edge-5xx trips the origin breaker and gets the session-down
    label; every other error passes through untouched."""
    if not _is_gemma_openwebui_provider(provider):
        return error_text
    labeled = record_gemma_session_down(model=model, status=status, reason=error_text)
    return f"{GEMMA_SESSION_DOWN_ERROR_LABEL}: {error_text}" if labeled else error_text


def acquire_gemma_call_slot(
    *,
    model: str,
    provider: dict,
    now: dt.datetime | None = None,
    sleep_fn=time.sleep,
    max_sleep_seconds: float | None = None,
) -> tuple[str, object]:
    """SEVERE fleet-wide gemma pacing (Open WebUI lane only). Returns (error, slot):
    - ("", None)      -> not the gemma lane, or the limiter is disabled: proceed, nothing to release.
    - ("", handle)    -> slot acquired; the fcntl lock is HELD for the call duration (fleet-wide max
                         concurrency 1). Caller MUST call release_gemma_call_slot(handle) in a finally.
    - (labeled, None) -> fail fast (another call in flight, or the next slot is too far away to sleep for).
    Spacing is measured from the END of the previous call (release rewrites last_call_utc), owner-tunable via
    min_interval_seconds in the state file without a code change."""
    if not _is_gemma_openwebui_provider(provider):
        return "", None
    path = _gemma_rate_limit_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(path, "a+", encoding="utf-8")
    except OSError:
        return "", None  # state file unavailable — the limiter is best-effort and never blocks the lane on IO errors
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return (f"{GEMMA_RATE_LIMITED_ERROR_LABEL}: another gemma call is in flight "
                f"(fleet-wide max concurrency 1; severe GPU cooling limiter; model {model})", None)
    handle.seek(0)
    try:
        state = json.loads(handle.read() or "{}")
    except (OSError, json.JSONDecodeError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    if state.get("enabled") is False:  # operator off-switch — disables spacing AND serialization
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
        return "", None
    try:
        min_interval = float(state.get("min_interval_seconds"))
    except (TypeError, ValueError):
        min_interval = float(GEMMA_MIN_CALL_INTERVAL_SECONDS)
    if min_interval < 0:
        min_interval = float(GEMMA_MIN_CALL_INTERVAL_SECONDS)
    now = now or dt.datetime.now(dt.timezone.utc)
    last = _parse_utc_time(state.get("last_call_utc"))
    wait = (min_interval - (now - last).total_seconds()) if last else 0.0
    budget = GEMMA_RATE_LIMIT_MAX_SLEEP_SECONDS if max_sleep_seconds is None else max_sleep_seconds
    if wait > budget:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
        return (f"{GEMMA_RATE_LIMITED_ERROR_LABEL}: next gemma call slot opens in {wait:.1f}s "
                f"(min spacing {min_interval:.0f}s fleet-wide; severe GPU cooling limiter; model {model})", None)
    if wait > 0:
        sleep_fn(wait)
        now = now + dt.timedelta(seconds=wait)
    _rewrite_gemma_rate_limit_state(handle, state, now=now, finished=False)
    return "", handle


def release_gemma_call_slot(slot: object, *, now: dt.datetime | None = None) -> None:
    """Release the fleet-wide gemma slot. Rewrites last_call_utc to the call END (spacing is measured from
    completion — the GPU cools between generations), then drops the lock. Never raises."""
    if slot is None:
        return
    try:
        slot.seek(0)  # type: ignore[attr-defined]
        try:
            state = json.loads(slot.read() or "{}")  # type: ignore[attr-defined]
        except (ValueError, OSError):
            state = {}
        if not isinstance(state, dict):
            state = {}
        _rewrite_gemma_rate_limit_state(slot, state, now=now or dt.datetime.now(dt.timezone.utc), finished=True)
    except Exception:  # noqa: BLE001 — releasing is best-effort; the flock always drops on close below
        pass
    finally:
        try:
            fcntl.flock(slot.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]
        except (OSError, ValueError):
            pass
        try:
            slot.close()  # type: ignore[attr-defined]
        except (OSError, ValueError):
            pass


def _rewrite_gemma_rate_limit_state(handle, state: dict, *, now: dt.datetime, finished: bool) -> None:
    """Update our fields in the locked state file, PRESERVING operator override fields
    (min_interval_seconds, enabled, anything else the owner adds)."""
    stamp = now.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    state.setdefault("record_type", "gemma_rate_limit_state")
    state.setdefault("candidate", True)
    state.setdefault("serves_truth", False)
    state["last_call_utc"] = stamp
    if finished:
        state["last_call_finished_utc"] = stamp
    state["updated_at_utc"] = stamp
    try:
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps(state, indent=2, sort_keys=True) + "\n")
        handle.flush()
    except (OSError, ValueError):
        pass  # state write is best-effort; the lock still serializes concurrency


def resolve_provider(name: str) -> dict:
    if name not in PROVIDERS:
        raise SystemExit(f"unknown provider {name!r}; have: {list(PROVIDERS)}")
    p = dict(PROVIDERS[name])
    p["base_url"] = p.get("base_url") or _env(p["base_url_var"]) or p.get("base_url_default", "")
    key_vars = [p["key_var"], *p.get("key_var_alternates", [])]
    p["key"] = next((_env(var) for var in key_vars if _env(var)), "")
    p["name"] = name
    p.setdefault("chat_path", "/chat/completions")
    return p


def chat(
    model: str,
    system: str,
    user: str,
    provider: dict,
    *,
    max_tokens: int = LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
    timeout: int = 300,
) -> dict:
    """One OpenAI-compatible chat call. Captures reasoning-model output (kimi puts text in `reasoning`, content empty).
    Returns {model, text, usage, finish_reason, error}. serves_truth=false."""
    pause_error = (_gemma_pause_error(model=model, provider=provider)
                   or gemma_session_down_error(model=model, provider=provider)
                   or _ollama_pause_error(model=model, provider=provider))
    if pause_error:
        return {"model": model, "text": "", "usage": {}, "finish_reason": "paused", "error": pause_error}
    url = provider["base_url"].rstrip("/") + provider.get("chat_path", "/chat/completions")
    body = json.dumps({"model": model, "messages": [{"role": "system", "content": system},
                                                    {"role": "user", "content": user}],
                       "temperature": 0.3, "max_tokens": max_tokens, "stream": False}).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json", **provider.get("headers", {})}
    if provider.get("key"):
        headers["Authorization"] = f"Bearer {provider['key']}"
    rate_error, gemma_slot = acquire_gemma_call_slot(model=model, provider=provider)  # pause beats rate limit (checked above)
    if rate_error:
        return {"model": model, "text": "", "usage": {}, "finish_reason": "rate_limited", "error": rate_error}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=timeout) as r:
            d = json.loads(r.read().decode())
        choice = d["choices"][0]
        msg = choice.get("message", {})
        text = msg.get("content") or msg.get("reasoning") or msg.get("reasoning_content") or ""
        return {"model": model, "text": text, "usage": d.get("usage", {}), "finish_reason": choice.get("finish_reason"), "error": None}
    except Exception as e:  # noqa: BLE001 — surface provider/network errors; callers decide
        detail = ""
        if hasattr(e, "read"):
            try:
                detail = e.read().decode()[:500]
            except Exception:
                pass
        error_text = _ollama_error_with_usage_pause(
            model=model, provider=provider, error_text=f"{type(e).__name__}: {e} {detail}",
            timed_out=isinstance(e, TimeoutError) or "timed out" in str(e).lower(),
        )
        error_text = _gemma_error_with_session_down(
            model=model, provider=provider, error_text=error_text, status=getattr(e, "code", None),
        )
        return {"model": model, "text": "", "usage": {}, "error": error_text}
    finally:
        release_gemma_call_slot(gemma_slot)


__all__ = [
    "PROVIDERS",
    "DEFAULT_PROVIDER",
    "OLLAMA_USAGE_LIMIT_MARKER_SESSION",
    "OLLAMA_USAGE_LIMIT_MARKER_CONCURRENT",
    "OLLAMA_USAGE_LIMIT_MARKERS",
    "OLLAMA_USAGE_PAUSE_ERROR_LABEL",
    "GEMMA_SESSION_DOWN_ERROR_LABEL",
    "GEMMA_RATE_LIMITED_ERROR_LABEL",
    "gemma_session_down_error",
    "gemma_session_down_ttl_for_status",
    "record_gemma_session_down",
    "acquire_gemma_call_slot",
    "release_gemma_call_slot",
    "resolve_provider",
    "chat",
]


def _self_test() -> int:
    """Offline proof of the Ollama usage-cap circuit breaker (zero network; the real pause file is never touched)."""
    import tempfile

    global _OLLAMA_PAUSE_PATH_OVERRIDE, _GEMMA_PAUSE_PATH_OVERRIDE
    global _GEMMA_SESSION_DOWN_PATH_OVERRIDE, _GEMMA_RATE_LIMIT_PATH_OVERRIDE
    provider = {"name": "ollama", "base_url": "https://ollama.com/v1", "chat_path": "/chat/completions", "headers": {}}
    local_provider = {"name": "ollama", "base_url": "http://127.0.0.1:11434/v1", "chat_path": "/chat/completions", "headers": {}}
    usage_429 = ('HTTPError: HTTP Error 429: Too Many Requests {"error":"you have reached your session usage limit, '
                 'add extra usage: https://ollama.com/settings (ref: self-test)"}')
    plain_timeout = "TimeoutError: The read operation timed out "
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as tmp:
        pause_path = Path(tmp) / "OLLAMA_PAUSE.json"
        _OLLAMA_PAUSE_PATH_OVERRIDE = pause_path
        try:
            checks.append(("non-quota errors pass through unlabeled and write no pause file",
                           _ollama_error_with_usage_pause(model="glm-5.2", provider=provider,
                                                          error_text="URLError: connection refused", timed_out=False)
                           == "URLError: connection refused" and not pause_path.exists()))
            checks.append(("a timeout WITHOUT an active pause stays unlabeled",
                           _ollama_error_with_usage_pause(model="glm-5.2", provider=provider,
                                                          error_text=plain_timeout, timed_out=True)
                           == plain_timeout and not pause_path.exists()))
            labeled = _ollama_error_with_usage_pause(model="glm-5.2", provider=provider,
                                                     error_text=usage_429, timed_out=False)
            payload = _read_json(pause_path)
            checks.append(("a usage-limit 429 body trips the breaker (pause file written, GEMMA_PAUSE shape)",
                           payload.get("enabled") is True and payload.get("candidate") is True
                           and payload.get("serves_truth") is False and payload.get("providers") == ["ollama"]
                           and payload.get("models") == ["glm-5.2"] and payload.get("requested_by") == "circuit_breaker"
                           and payload.get("ref_marker") == OLLAMA_USAGE_PAUSE_REF_MARKER
                           and "reached your session usage limit" in str(payload.get("reason"))
                           and bool(_parse_utc_time(payload.get("expires_at_utc")))))
            checks.append(("the tripping 429 error carries the pause label",
                           labeled.startswith(OLLAMA_USAGE_PAUSE_ERROR_LABEL)))
            paused = chat("kimi-k2.7-code", "s", "u", provider, max_tokens=8, timeout=1)
            checks.append(("an active pause short-circuits chat() offline for EVERY ollama model",
                           paused.get("finish_reason") == "paused"
                           and OLLAMA_USAGE_PAUSE_ERROR_LABEL in str(paused.get("error"))))
            checks.append(("a timeout WHILE the pause is active is attributed to the pause",
                           _ollama_error_with_usage_pause(model="kimi-k2.7-code", provider=provider,
                                                          error_text=plain_timeout, timed_out=True)
                           .startswith(OLLAMA_USAGE_PAUSE_ERROR_LABEL)))
            checks.append(("a fresh trip never shortens a longer pause already on file",
                           (_write_ollama_usage_pause(model="kimi-k2.7-code", reason="second trip") or True)
                           and _read_json(pause_path).get("models") == ["glm-5.2"]))
            pause_path.unlink()
            concurrent_429 = 'HTTPError: HTTP Error 429: Too Many Requests {"error":"too many concurrent requests"}'
            _ollama_error_with_usage_pause(model="glm-5.2", provider=provider,
                                           error_text=concurrent_429, timed_out=False)
            concurrent_payload = _read_json(pause_path)
            concurrent_expiry = _parse_utc_time(concurrent_payload.get("expires_at_utc"))
            concurrent_created = _parse_utc_time(concurrent_payload.get("created_at_utc"))
            checks.append(("a concurrency-only 429 trips a SHORT pause, not the hour-long usage pause",
                           bool(concurrent_expiry) and bool(concurrent_created)
                           and (concurrent_expiry - concurrent_created).total_seconds()
                           == OLLAMA_CONCURRENT_PAUSE_SECONDS))
            pause_path.unlink()
            weekly_429 = 'HTTPError: HTTP Error 429: Too Many Requests {"error":"you have reached your weekly usage limit"}'
            _ollama_error_with_usage_pause(model="glm-5.2", provider=provider,
                                           error_text=weekly_429, timed_out=False)
            weekly_payload = _read_json(pause_path)
            weekly_expiry = _parse_utc_time(weekly_payload.get("expires_at_utc"))
            weekly_created = _parse_utc_time(weekly_payload.get("created_at_utc"))
            checks.append(("a weekly usage-limit 429 trips a LONG fail-fast pause",
                           bool(weekly_expiry) and bool(weekly_created)
                           and (weekly_expiry - weekly_created).total_seconds()
                           == OLLAMA_WEEKLY_USAGE_PAUSE_SECONDS))
            expired = _read_json(pause_path) | {"expires_at_utc": "2020-01-01T00:00:00Z"}
            pause_path.write_text(json.dumps(expired), encoding="utf-8")
            checks.append(("an expired pause is ignored",
                           _ollama_pause_error(model="glm-5.2", provider=provider) == ""))
            disabled = expired | {"enabled": False, "expires_at_utc": "2099-01-01T00:00:00Z"}
            pause_path.write_text(json.dumps(disabled), encoding="utf-8")
            checks.append(("a disabled pause is ignored",
                           _ollama_pause_error(model="glm-5.2", provider=provider) == ""))
            checks.append(("non-ollama providers never see the ollama pause",
                           _ollama_pause_error(model=OPENWEBUI_DEFAULT_MODEL, provider={"name": "openwebui"}) == ""
                           and _ollama_error_with_usage_pause(model=OPENWEBUI_DEFAULT_MODEL,
                                                              provider={"name": "openwebui"},
                                                              error_text=usage_429, timed_out=False) == usage_429))
            checks.append(("local Ollama providers never see the cloud usage pause",
                           _ollama_pause_error(model="gemma4:latest", provider=local_provider) == ""
                           and _ollama_error_with_usage_pause(model="gemma4:latest",
                                                              provider=local_provider,
                                                              error_text=usage_429, timed_out=False) == usage_429))
        finally:
            _OLLAMA_PAUSE_PATH_OVERRIDE = None
    openwebui_provider = {"name": "openwebui", "base_url": OPENWEBUI_DEFAULT_BASE_URL,
                          "chat_path": OPENWEBUI_CHAT_COMPLETIONS_PATH, "headers": {}}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _GEMMA_PAUSE_PATH_OVERRIDE = tmp_path / "GEMMA_PAUSE.json"  # missing file = no operator pause (deterministic)
        _GEMMA_SESSION_DOWN_PATH_OVERRIDE = tmp_path / "GEMMA_SESSION_DOWN.json"
        _GEMMA_RATE_LIMIT_PATH_OVERRIDE = tmp_path / "GEMMA_RATE_LIMIT.json"
        try:
            # --- Gemma session-down breaker (Open WebUI origin behind the Cloudflare edge) ---
            checks.append(("gemma TTLs: origin-down 5xx pauses long, degraded pauses short, auth/model errors never",
                           gemma_session_down_ttl_for_status(521) == GEMMA_SESSION_DOWN_PAUSE_SECONDS
                           and gemma_session_down_ttl_for_status(524) == GEMMA_SESSION_DEGRADED_PAUSE_SECONDS
                           and gemma_session_down_ttl_for_status(401) == 0
                           and gemma_session_down_ttl_for_status(None) == 0))
            labeled_521 = record_gemma_session_down(model=OPENWEBUI_DEFAULT_MODEL, status=521,
                                                    reason="Open WebUI CDP fetch failed: status=521 Web server is down")
            session_payload = _read_json(_GEMMA_SESSION_DOWN_PATH_OVERRIDE)
            checks.append(("a 521 trips the session-down breaker (file written in GEMMA_PAUSE shape, labeled error)",
                           labeled_521.startswith(GEMMA_SESSION_DOWN_ERROR_LABEL)
                           and session_payload.get("enabled") is True and session_payload.get("http_status") == 521
                           and session_payload.get("providers") == ["openwebui"]
                           and session_payload.get("requested_by") == "circuit_breaker"
                           and session_payload.get("ref_marker") == GEMMA_SESSION_DOWN_REF_MARKER
                           and session_payload.get("candidate") is True
                           and session_payload.get("serves_truth") is False))
            session_paused = chat(OPENWEBUI_DEFAULT_MODEL, "s", "u", openwebui_provider, max_tokens=8, timeout=1)
            checks.append(("an active session-down pause short-circuits chat() offline with the label",
                           session_paused.get("finish_reason") == "paused"
                           and str(session_paused.get("error") or "").startswith(GEMMA_SESSION_DOWN_ERROR_LABEL)))
            checks.append(("a degraded-status trip never shortens the longer origin-down pause on file",
                           record_gemma_session_down(model=OPENWEBUI_DEFAULT_MODEL, status=524, reason="slow") != ""
                           and _read_json(_GEMMA_SESSION_DOWN_PATH_OVERRIDE).get("http_status") == 521))
            expired_session = _read_json(_GEMMA_SESSION_DOWN_PATH_OVERRIDE) | {"expires_at_utc": "2020-01-01T00:00:00Z"}
            _GEMMA_SESSION_DOWN_PATH_OVERRIDE.write_text(json.dumps(expired_session), encoding="utf-8")
            checks.append(("an expired session-down pause is ignored",
                           gemma_session_down_error(model=OPENWEBUI_DEFAULT_MODEL, provider=openwebui_provider) == ""))
            _GEMMA_SESSION_DOWN_PATH_OVERRIDE.unlink()
            checks.append(("auth errors never trip the origin breaker (pausing would mask a login problem)",
                           _gemma_error_with_session_down(model=OPENWEBUI_DEFAULT_MODEL, provider=openwebui_provider,
                                                          error_text="HTTPError: HTTP Error 401: Unauthorized",
                                                          status=401)
                           == "HTTPError: HTTP Error 401: Unauthorized"
                           and not _GEMMA_SESSION_DOWN_PATH_OVERRIDE.exists()))
            checks.append(("non-openwebui providers never see the session-down breaker",
                           _gemma_error_with_session_down(model="glm-5.2", provider=provider,
                                                          error_text="HTTPError: HTTP Error 521 edge", status=521)
                           == "HTTPError: HTTP Error 521 edge"
                           and not _GEMMA_SESSION_DOWN_PATH_OVERRIDE.exists()))
            # --- Gemma severe cross-process rate limiter (fcntl-locked shared state file) ---
            sleeps: list[float] = []
            base = dt.datetime(2026, 7, 2, 12, 0, 0, tzinfo=dt.timezone.utc)
            checks.append(("non-gemma lanes bypass the rate limiter entirely (no state file created)",
                           acquire_gemma_call_slot(model="glm-5.2", provider=provider) == ("", None)
                           and not _GEMMA_RATE_LIMIT_PATH_OVERRIDE.exists()))
            err_first, slot_first = acquire_gemma_call_slot(model=OPENWEBUI_DEFAULT_MODEL, provider=openwebui_provider,
                                                            now=base, sleep_fn=sleeps.append)
            checks.append(("a fresh state file grants the slot immediately and stamps last_call_utc",
                           err_first == "" and slot_first is not None and not sleeps
                           and _read_json(_GEMMA_RATE_LIMIT_PATH_OVERRIDE).get("last_call_utc") == "2026-07-02T12:00:00Z"))
            err_busy, slot_busy = acquire_gemma_call_slot(model=OPENWEBUI_DEFAULT_MODEL, provider=openwebui_provider,
                                                          now=base, sleep_fn=sleeps.append)
            checks.append(("a concurrent second call fails fast labeled (fleet-wide max concurrency 1)",
                           slot_busy is None and err_busy.startswith(GEMMA_RATE_LIMITED_ERROR_LABEL)
                           and "in flight" in err_busy))
            release_gemma_call_slot(slot_first, now=base + dt.timedelta(seconds=90))
            released_state = _read_json(_GEMMA_RATE_LIMIT_PATH_OVERRIDE)
            checks.append(("release stamps spacing from the call END (the GPU cools between generations)",
                           released_state.get("last_call_utc") == "2026-07-02T12:01:30Z"
                           and released_state.get("last_call_finished_utc") == "2026-07-02T12:01:30Z"
                           and released_state.get("record_type") == "gemma_rate_limit_state"))
            err_far, slot_far = acquire_gemma_call_slot(model=OPENWEBUI_DEFAULT_MODEL, provider=openwebui_provider,
                                                        now=base + dt.timedelta(seconds=95), sleep_fn=sleeps.append)
            checks.append(("a slot >20s away fails fast labeled WITHOUT sleeping (workers requeue, never pile up)",
                           slot_far is None and err_far.startswith(GEMMA_RATE_LIMITED_ERROR_LABEL)
                           and "opens in 40.0s" in err_far and not sleeps))
            err_near, slot_near = acquire_gemma_call_slot(model=OPENWEBUI_DEFAULT_MODEL, provider=openwebui_provider,
                                                          now=base + dt.timedelta(seconds=120), sleep_fn=sleeps.append)
            checks.append(("a slot <=20s away sleeps exactly the remaining spacing then proceeds",
                           err_near == "" and slot_near is not None and sleeps == [15.0]))
            release_gemma_call_slot(slot_near, now=base + dt.timedelta(seconds=200))
            tuned_state = _read_json(_GEMMA_RATE_LIMIT_PATH_OVERRIDE) | {"min_interval_seconds": 5}
            _GEMMA_RATE_LIMIT_PATH_OVERRIDE.write_text(json.dumps(tuned_state), encoding="utf-8")
            err_tuned, slot_tuned = acquire_gemma_call_slot(model=OPENWEBUI_DEFAULT_MODEL, provider=openwebui_provider,
                                                            now=base + dt.timedelta(seconds=206), sleep_fn=sleeps.append)
            preserved = _read_json(_GEMMA_RATE_LIMIT_PATH_OVERRIDE)
            checks.append(("min_interval_seconds override is honored and PRESERVED across rewrites (owner-tunable)",
                           err_tuned == "" and slot_tuned is not None and sleeps == [15.0]
                           and preserved.get("min_interval_seconds") == 5))
            release_gemma_call_slot(slot_tuned, now=base + dt.timedelta(seconds=207))
            disabled_state = _read_json(_GEMMA_RATE_LIMIT_PATH_OVERRIDE) | {"enabled": False}
            _GEMMA_RATE_LIMIT_PATH_OVERRIDE.write_text(json.dumps(disabled_state), encoding="utf-8")
            checks.append(("enabled:false in the state file disables the limiter entirely (operator off-switch)",
                           acquire_gemma_call_slot(model=OPENWEBUI_DEFAULT_MODEL, provider=openwebui_provider,
                                                   now=base + dt.timedelta(seconds=208)) == ("", None)))
            _GEMMA_RATE_LIMIT_PATH_OVERRIDE.write_text("{}", encoding="utf-8")
            _GEMMA_PAUSE_PATH_OVERRIDE.write_text(json.dumps({
                "enabled": True, "models": [OPENWEBUI_DEFAULT_MODEL],
                "expires_at_utc": "2099-01-01T00:00:00Z", "reason": "self-test operator pause"}), encoding="utf-8")
            operator_paused = chat(OPENWEBUI_DEFAULT_MODEL, "s", "u", openwebui_provider, max_tokens=8, timeout=1)
            checks.append(("the operator GEMMA_PAUSE beats the rate limiter (paused; rate state untouched)",
                           operator_paused.get("finish_reason") == "paused"
                           and "self-test operator pause" in str(operator_paused.get("error"))
                           and _read_json(_GEMMA_RATE_LIMIT_PATH_OVERRIDE) == {}))
        finally:
            _GEMMA_PAUSE_PATH_OVERRIDE = None
            _GEMMA_SESSION_DOWN_PATH_OVERRIDE = None
            _GEMMA_RATE_LIMIT_PATH_OVERRIDE = None
    failures = [name for name, ok in checks if not ok]
    print("PASS - _llm_client: Ollama usage-cap circuit breaker (429 trips the pause; labeled short-circuits; "
          "expiry/disable honored) + Gemma lane guards (session-down breaker on Cloudflare origin-5xx with "
          "never-shorten TTLs; SEVERE fcntl cross-process rate limiter: max concurrency 1, spacing from call "
          "end, sleep<=budget else labeled fail-fast, owner-tunable state file, pause beats rate limit)."
          if not failures else
          f"FAIL - _llm_client self-test: {failures}")
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true",
                        help="offline circuit-breaker proof (no network, real pause file untouched)")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
