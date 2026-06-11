#!/usr/bin/env python3
"""Foundry CPU-batch inference lane — an OPTIONAL, degrade-safe local model server.

This is **lane 2** of `docs/architecture/flexible-inference-lanes.md`: for long-running
NON-realtime foundry work (overnight enrichment, CDC re-verification, candidate
generation) where tokens/sec doesn't matter but $/token and data-locality do, the worker
can stand up a *local* OpenAI-compatible server (a quantized Gemma on CPU) for the
duration of a batch, route its model calls at `127.0.0.1`, then shut it down so the
machine can scale to zero. Full lifecycle + cost math: `docs/architecture/cpu-batch-inference-lane.md`.

Design laws (this module obeys all four):
  - **Optional / no-op:** when ``OH_BATCH_LLM`` is unset the lane is INACTIVE — the manager
    is a no-op and the cloud route is byte-for-byte unchanged.
  - **Honest degradation:** if ``OH_BATCH_LLM=local`` but NO supported backend binary
    (``llama-server`` or ``ollama``) is resolvable, the lane reports ``available=False``
    with a reason and the caller falls back to the existing cloud route. It NEVER fabricates
    a model answer and NEVER crashes the worker.
  - **No magic values:** every endpoint / binary / model / timeout is a named constant with a
    rationale, overridable by env. No hardcoded paths or model tags in logic.
  - **Lossless / honest provenance:** the lane does not rewrite outputs; the worker records
    WHICH lane served each batch (``cloud`` | ``local-batch``) so the funnel ledger never
    lies about where a measurement came from.

The lane is transport-compatible with ``scripts.foundry.model_route.from_env()``: it speaks
the OpenAI ``/v1/chat/completions`` shape (same as ``model_routes.ChatRoute`` and the OIPS
``openai_compatible`` adapter), so activating it is purely a base_url switch — no new caller.

Pure stdlib + subprocess. Run ``python3 -m scripts.foundry.batch_inference --self-test``
(offline; uses a FAKE local server — proves the lifecycle with no real model installed).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

# --------------------------------------------------------------------------- #
# Environment contract (every value named + overridable — NO magic literals)
# --------------------------------------------------------------------------- #
#: master switch. The lane is ACTIVE only when this equals LANE_LOCAL ("local").
#: Any other value (or unset) ⇒ INACTIVE ⇒ no-op ⇒ cloud route unchanged.
ENV_BATCH_LLM = "OH_BATCH_LLM"
#: the one value of ENV_BATCH_LLM that turns the lane on (a self-host CPU batch server).
LANE_LOCAL = "local"
#: provenance tags the worker stamps onto each batch result (single source — never retyped).
LANE_TAG_CLOUD = "cloud"            # the existing model_route.from_env() cloud/remote lane
LANE_TAG_LOCAL_BATCH = "local-batch"  # this module's local CPU-batch server

#: model tag to serve. Default = a SMALL gemma so it runs on a CPU-only worker. Override per
#: deployment (e.g. a pulled `gemma4` Ollama tag or a baked llama.cpp GGUF alias).
ENV_BATCH_MODEL = "OH_BATCH_LLM_MODEL"
DEFAULT_BATCH_MODEL = "gemma4"      # rationale: smallest Gemma-4 class tag that runs Q4 on CPU

#: loopback host/port the local server binds to. Loopback so the receipt/base_host is honest
#: and no port is exposed off-box; port is env-overridable to avoid collisions on a busy worker.
ENV_BATCH_HOST = "OH_BATCH_LLM_HOST"
DEFAULT_BATCH_HOST = "127.0.0.1"    # rationale: loopback only — lane 2 is on-box, never public
ENV_BATCH_PORT = "OH_BATCH_LLM_PORT"
DEFAULT_BATCH_PORT = 11533          # rationale: high port unlikely to clash with ollama(11434)/vLLM(8000)

#: which backend to use. "auto" probes llama.cpp first, then ollama. Force one for determinism.
ENV_BATCH_BACKEND = "OH_BATCH_LLM_BACKEND"
BACKEND_AUTO = "auto"
BACKEND_LLAMACPP = "llamacpp"
BACKEND_OLLAMA = "ollama"
#: binary names (resolved on PATH via shutil.which) — overridable for non-standard installs.
ENV_LLAMACPP_BIN = "OH_BATCH_LLM_LLAMACPP_BIN"
DEFAULT_LLAMACPP_BIN = "llama-server"   # the llama.cpp OpenAI-compatible server entrypoint
ENV_OLLAMA_BIN = "OH_BATCH_LLM_OLLAMA_BIN"
DEFAULT_OLLAMA_BIN = "ollama"
#: a llama.cpp server needs a model FILE; ollama needs only a pulled tag. No default path on
#: purpose — a wrong baked path must DEGRADE, never guess. (llama.cpp lane stays unavailable
#: until this is set, so we never start a server that can't answer.)
ENV_LLAMACPP_MODEL_PATH = "OH_BATCH_LLM_LLAMACPP_MODEL_PATH"

#: lifecycle timing (seconds). CPU model load is slow → a generous-but-bounded health wait.
ENV_HEALTH_TIMEOUT_S = "OH_BATCH_LLM_HEALTH_TIMEOUT_S"
DEFAULT_HEALTH_TIMEOUT_S = 120      # rationale: cold CPU load of a Q4 gemma can take ~1 min
HEALTH_POLL_INTERVAL_S = 0.5        # rationale: cheap loopback GET; tight enough to feel instant in tests
#: graceful-stop grace before SIGKILL — long enough for a clean exit, short enough to not hang a drain.
SHUTDOWN_GRACE_S = 10

#: the local server speaks OpenAI-compat. We probe /v1/models for readiness and the route then
#: talks /v1/chat/completions — the exact shape model_route.from_env() already uses.
HEALTH_PATH = "/v1/models"
OPENAI_V1_SUFFIX = "/v1"

#: env keys we hand to model_route.from_env() so the EXISTING cloud route transparently points
#: at the local server (it reads OPENAI_BASE_URL/OPENAI_API_KEY/OH_CHAT_MODEL). Single source so
#: the worker wiring and this manager can't drift on which vars carry the override.
ROUTE_BASE_URL_ENV = "OPENAI_BASE_URL"
ROUTE_API_KEY_ENV = "OPENAI_API_KEY"
ROUTE_MODEL_ENV = "OH_CHAT_MODEL"
#: from_env() prefers these keys OVER OPENAI_* — they must be cleared while the local lane is the
#: route, or a cloud provider would shadow the on-box server. (We restore them on exit.)
ROUTE_HIGHER_PRIORITY_KEYS = ("OLLAMA_API_KEY", "ANTHROPIC_API_KEY")
#: a non-empty placeholder key: local servers ignore auth, but from_env() only takes the
#: OPENAI_* branch when OPENAI_API_KEY is truthy. NOT a credential.
LOCAL_PLACEHOLDER_KEY = "local-batch-no-auth"


def lane_active() -> bool:
    """True only when ENV_BATCH_LLM == LANE_LOCAL. Unset/other ⇒ INACTIVE (cloud unchanged)."""
    return os.environ.get(ENV_BATCH_LLM, "").strip().lower() == LANE_LOCAL


def job_wants_batch(job: dict | None) -> bool:
    """Lane eligibility for a job: active AND not latency-bound. A job tagged
    ``latency_class: "interactive"`` must use the cloud lane (lane 1) even when the batch lane
    is up — interactive callers can't wait on CPU tokens/sec. Anything else (``batch`` / unset)
    is batch-eligible."""
    if not lane_active():
        return False
    latency = str((job or {}).get("latency_class", "") or "").strip().lower()
    return latency != "interactive"


# --------------------------------------------------------------------------- #
# Backend detection (honest: returns what's actually runnable, else a reason)
# --------------------------------------------------------------------------- #
@dataclass
class BackendPlan:
    """A resolved, runnable backend, or an honest 'unavailable' with a reason."""
    available: bool
    backend: str | None = None        # BACKEND_LLAMACPP | BACKEND_OLLAMA
    binary: str | None = None         # absolute path to the resolved server binary
    reason: str = ""                  # human-readable WHY when not available (logged, never silent)


def _which(env_key: str, default_bin: str) -> str | None:
    return shutil.which(os.environ.get(env_key, default_bin))


def _llamacpp_plan() -> BackendPlan:
    """llama.cpp is runnable only if BOTH the binary AND a model FILE are present — a server with
    no GGUF can't answer, so we DEGRADE rather than start a broken endpoint."""
    binary = _which(ENV_LLAMACPP_BIN, DEFAULT_LLAMACPP_BIN)
    if not binary:
        return BackendPlan(False, reason=f"{DEFAULT_LLAMACPP_BIN} not on PATH")
    model_path = os.environ.get(ENV_LLAMACPP_MODEL_PATH, "")
    if not model_path or not os.path.exists(model_path):
        return BackendPlan(False, reason=f"{ENV_LLAMACPP_MODEL_PATH} unset or missing (need a GGUF file)")
    return BackendPlan(True, backend=BACKEND_LLAMACPP, binary=binary)


def _ollama_plan() -> BackendPlan:
    binary = _which(ENV_OLLAMA_BIN, DEFAULT_OLLAMA_BIN)
    if not binary:
        return BackendPlan(False, reason=f"{DEFAULT_OLLAMA_BIN} not on PATH")
    return BackendPlan(True, backend=BACKEND_OLLAMA, binary=binary)


def detect_backend() -> BackendPlan:
    """Resolve the backend honoring ENV_BATCH_BACKEND (auto|llamacpp|ollama). On auto, prefer
    llama.cpp (lower overhead per-batch) then ollama. Always returns a BackendPlan — never raises;
    an unrunnable environment yields ``available=False`` + a reason the caller logs before falling
    back to cloud."""
    choice = os.environ.get(ENV_BATCH_BACKEND, BACKEND_AUTO).strip().lower() or BACKEND_AUTO
    if choice == BACKEND_LLAMACPP:
        return _llamacpp_plan()
    if choice == BACKEND_OLLAMA:
        return _ollama_plan()
    # auto: try llama.cpp, then ollama; report the most useful reason if neither works.
    llama = _llamacpp_plan()
    if llama.available:
        return llama
    ollama = _ollama_plan()
    if ollama.available:
        return ollama
    return BackendPlan(False, reason=f"no batch backend: [{llama.reason}]; [{ollama.reason}]")


def _server_argv(plan: BackendPlan, host: str, port: int, model: str) -> list[str]:
    """The subprocess argv to launch the chosen backend as an OpenAI-compatible server on host:port."""
    if plan.backend == BACKEND_LLAMACPP:
        # llama.cpp `llama-server` exposes /v1/chat/completions + /v1/models natively.
        return [str(plan.binary), "--host", host, "--port", str(port),
                "-m", os.environ[ENV_LLAMACPP_MODEL_PATH]]
    if plan.backend == BACKEND_OLLAMA:
        # `ollama serve` binds OLLAMA_HOST and serves /v1/* (OpenAI-compat). Host/port via env.
        return [str(plan.binary), "serve"]
    raise ValueError(f"no argv for backend {plan.backend!r}")  # unreachable: callers gate on available


def _server_env(plan: BackendPlan, host: str, port: int) -> dict[str, str]:
    """Subprocess env: ollama reads OLLAMA_HOST for its bind address; llama.cpp takes flags."""
    env = dict(os.environ)
    if plan.backend == BACKEND_OLLAMA:
        env["OLLAMA_HOST"] = f"{host}:{port}"
    return env


def _http_ok(url: str, timeout: float) -> bool:
    """True iff a GET returns HTTP 200. Never raises — a connection refused is just 'not ready yet'."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 - loopback only
            return getattr(resp, "status", resp.getcode()) == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


# --------------------------------------------------------------------------- #
# The lane manager (start → health → yield base_url → drain → stop)
# --------------------------------------------------------------------------- #
@dataclass
class BatchLane:
    """A handle to an ACTIVE local batch server (or an honest 'unavailable' lane).

    ``available=False`` means: degrade to cloud (the worker reads ``base_url is None`` and leaves
    the cloud route in place). ``available=True`` carries the loopback ``base_url`` (…/v1) callers
    route through and the ``model``/``lane_tag`` to record for provenance."""
    available: bool
    base_url: str | None = None
    model: str | None = None
    backend: str | None = None
    lane_tag: str = LANE_TAG_CLOUD
    reason: str = ""


def _log(msg: str) -> None:
    """Honest, visible degradation/lifecycle logging (stderr, never silent)."""
    print(f"[batch_inference] {msg}", file=sys.stderr)


@contextmanager
def inactive_lane(reason: str = "batch lane not eligible") -> Iterator[BatchLane]:
    """A zero-side-effect context: yields an UNAVAILABLE lane, starts nothing, touches no env.

    Callers use this for the cloud-only / interactive / inactive case so the with-block shape is
    identical to the active case (one code path) while remaining a true no-op — paired with
    ``route_env_override`` (also a no-op on an unavailable lane), the cloud route is byte-for-byte
    unchanged."""
    yield BatchLane(available=False, reason=reason)


@contextmanager
def batch_server(*, model: str | None = None, host: str | None = None, port: int | None = None,
                 health_timeout_s: float | None = None,
                 _spawn=subprocess.Popen) -> Iterator[BatchLane]:
    """Context manager for the CPU-batch lane. On enter:

      1. if the lane is INACTIVE (env unset) → yield an unavailable lane (no-op, cloud unchanged);
      2. else detect a backend → if none, LOG honestly and yield an unavailable lane (→ cloud);
      3. else start the server subprocess, poll HEALTH_PATH until 200 (bounded by the timeout) →
         on timeout, stop the process and yield unavailable (→ cloud);
      4. on success, yield an ACTIVE lane with a loopback ``base_url`` (…/v1).

    On exit it ALWAYS terminates the subprocess cleanly (terminate → wait → kill), so a drained
    batch lets the machine scale to zero. ``_spawn`` is injectable so the self-test can drive a
    fake server with no real backend.
    """
    if not lane_active():
        # No-op path: the lane is off. Yield an unavailable handle; nothing is started or changed.
        yield BatchLane(available=False, reason=f"{ENV_BATCH_LLM} != {LANE_LOCAL} (lane inactive)")
        return

    plan = detect_backend()
    if not plan.available:
        _log(f"lane requested but unavailable — {plan.reason}; falling back to cloud route.")
        yield BatchLane(available=False, reason=plan.reason)
        return

    host = host or os.environ.get(ENV_BATCH_HOST, DEFAULT_BATCH_HOST)
    port = int(port or os.environ.get(ENV_BATCH_PORT, DEFAULT_BATCH_PORT))
    model = model or os.environ.get(ENV_BATCH_MODEL, DEFAULT_BATCH_MODEL)
    timeout = float(health_timeout_s if health_timeout_s is not None
                    else os.environ.get(ENV_HEALTH_TIMEOUT_S, DEFAULT_HEALTH_TIMEOUT_S))
    base = f"http://{host}:{port}"
    health_url = base + HEALTH_PATH

    proc = None
    try:
        try:
            proc = _spawn(_server_argv(plan, host, port, model),
                          env=_server_env(plan, host, port),
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, ValueError) as exc:
            _log(f"failed to start {plan.backend} server ({exc}); falling back to cloud route.")
            yield BatchLane(available=False, reason=f"spawn failed: {exc}")
            return

        deadline = time.monotonic() + timeout
        ready = False
        while time.monotonic() < deadline:
            if proc.poll() is not None:   # server died during boot → degrade
                _log(f"{plan.backend} server exited (code={proc.returncode}) before health; "
                     "falling back to cloud route.")
                yield BatchLane(available=False, reason=f"server exited code={proc.returncode}")
                return
            if _http_ok(health_url, timeout=HEALTH_POLL_INTERVAL_S):
                ready = True
                break
            time.sleep(HEALTH_POLL_INTERVAL_S)

        if not ready:
            _log(f"{plan.backend} server not healthy within {timeout}s; falling back to cloud route.")
            yield BatchLane(available=False, reason=f"health timeout after {timeout}s")
            return

        _log(f"lane UP — {plan.backend} serving {model} at {base}{OPENAI_V1_SUFFIX} (local CPU batch).")
        yield BatchLane(available=True, base_url=base + OPENAI_V1_SUFFIX, model=model,
                        backend=plan.backend, lane_tag=LANE_TAG_LOCAL_BATCH)
    finally:
        if proc is not None:
            _shutdown(proc)


def _shutdown(proc) -> None:
    """Clean drain-stop: terminate, wait up to the grace, then kill. Never raises."""
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=SHUTDOWN_GRACE_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=SHUTDOWN_GRACE_S)
    except Exception as exc:  # noqa: BLE001 - shutdown must never break a drain
        _log(f"server shutdown raised (ignored): {exc}")


@contextmanager
def route_env_override(lane: BatchLane) -> Iterator[bool]:
    """While an ACTIVE lane is in scope, point ``model_route.from_env()`` at the local server by
    setting OPENAI_BASE_URL/OPENAI_API_KEY/OH_CHAT_MODEL (and clearing the higher-priority
    OLLAMA_/ANTHROPIC_ keys so a cloud provider can't shadow the on-box server). Restores the
    PRIOR environment exactly on exit (lossless — no env leaks across jobs). For an unavailable
    lane this is a no-op and yields False, so the cloud route is untouched.

    Yields True iff the override is in effect (i.e. calls will hit the local batch server)."""
    if not lane.available or not lane.base_url:
        yield False
        return
    keys = (ROUTE_BASE_URL_ENV, ROUTE_API_KEY_ENV, ROUTE_MODEL_ENV, *ROUTE_HIGHER_PRIORITY_KEYS)
    saved = {k: os.environ.get(k) for k in keys}
    try:
        os.environ[ROUTE_BASE_URL_ENV] = lane.base_url
        os.environ[ROUTE_API_KEY_ENV] = LOCAL_PLACEHOLDER_KEY
        if lane.model:
            os.environ[ROUTE_MODEL_ENV] = lane.model
        for k in ROUTE_HIGHER_PRIORITY_KEYS:   # ensure OPENAI_* branch wins in from_env()
            os.environ.pop(k, None)
        yield True
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# --------------------------------------------------------------------------- #
# self-test — a FAKE local server proves the full lifecycle with NO real model
# --------------------------------------------------------------------------- #
def _fake_server_script(*, sentinel: str) -> str:
    """A tiny stdlib http.server that speaks just enough OpenAI-compat to prove the lane:
    GET /v1/models → 200 (health), POST /v1/chat/completions → a fixed completion carrying a
    ``sentinel`` so the test can prove the call was actually served LOCALLY (not by cloud)."""
    return (
        "import json,sys\n"
        "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
        f"SENTINEL={sentinel!r}\n"
        "class H(BaseHTTPRequestHandler):\n"
        "    def log_message(self,*a):\n        pass\n"
        "    def do_GET(self):\n"
        "        if self.path.rstrip('/').endswith('/v1/models'):\n"
        "            b=json.dumps({'object':'list','data':[{'id':'fake'}]}).encode()\n"
        "            self.send_response(200); self.send_header('content-type','application/json')\n"
        "            self.send_header('content-length',str(len(b))); self.end_headers(); self.wfile.write(b)\n"
        "        else:\n            self.send_response(404); self.end_headers()\n"
        "    def do_POST(self):\n"
        "        n=int(self.headers.get('content-length',0)); self.rfile.read(n)\n"
        "        b=json.dumps({'choices':[{'message':{'role':'assistant','content':SENTINEL}}]}).encode()\n"
        "        self.send_response(200); self.send_header('content-type','application/json')\n"
        "        self.send_header('content-length',str(len(b))); self.end_headers(); self.wfile.write(b)\n"
        "host=sys.argv[1]; port=int(sys.argv[2])\n"
        "HTTPServer((host,port),H).serve_forever()\n"
    )


def _free_port() -> int:
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _self_test() -> int:  # noqa: C901 - one linear scenario script; readability over decomposition
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    saved_env = {k: os.environ.get(k) for k in (
        ENV_BATCH_LLM, ENV_BATCH_BACKEND, ENV_BATCH_PORT, ENV_BATCH_HOST, ENV_BATCH_MODEL,
        ENV_LLAMACPP_BIN, ENV_OLLAMA_BIN, ENV_LLAMACPP_MODEL_PATH, ENV_HEALTH_TIMEOUT_S,
        ROUTE_BASE_URL_ENV, ROUTE_API_KEY_ENV, ROUTE_MODEL_ENV, *ROUTE_HIGHER_PRIORITY_KEYS)}

    def restore_env() -> None:
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    try:
        # ---- 1) NO-OP PATH: lane unset ⇒ inactive, nothing started, base_url None ----
        os.environ.pop(ENV_BATCH_LLM, None)
        check("lane_active() False when unset", lane_active() is False)
        check("job_wants_batch False when inactive", job_wants_batch({"latency_class": "batch"}) is False)
        with batch_server() as lane:
            check("no-op: lane unavailable when unset", lane.available is False and lane.base_url is None)
        with batch_server() as lane:
            with route_env_override(lane) as active:
                check("no-op: route override is a no-op (cloud unchanged)", active is False)
                check("no-op: OPENAI_BASE_URL untouched", ROUTE_BASE_URL_ENV not in os.environ
                      or os.environ.get(ROUTE_BASE_URL_ENV) == saved_env.get(ROUTE_BASE_URL_ENV))

        # ---- 2) DEGRADATION: lane on but configured binary missing ⇒ unavailable, no crash ----
        os.environ[ENV_BATCH_LLM] = LANE_LOCAL
        check("lane_active() True when =local", lane_active() is True)
        os.environ[ENV_BATCH_BACKEND] = BACKEND_LLAMACPP
        os.environ[ENV_LLAMACPP_BIN] = "definitely-not-a-real-binary-xyz"
        plan = detect_backend()
        check("detect_backend unavailable for missing llama bin", plan.available is False and bool(plan.reason))
        with batch_server() as lane:
            check("degrade: missing-binary lane unavailable (→ cloud)", lane.available is False)
            check("degrade: reason is reported (honest)", bool(lane.reason))

        # forced-ollama path resolves a binary IF present, else still degrades cleanly (no crash)
        os.environ[ENV_BATCH_BACKEND] = BACKEND_OLLAMA
        os.environ[ENV_OLLAMA_BIN] = "definitely-not-a-real-binary-xyz"
        with batch_server() as lane:
            check("degrade: forced-ollama missing bin → unavailable, no crash", lane.available is False)

        # ---- 3) LIFECYCLE on a FAKE server: start → health → route a call → shutdown ----
        # We bypass real backends by injecting a _spawn that launches the fake OpenAI server and
        # forcing BACKEND_OLLAMA detection to succeed (ollama IS on PATH in many envs; if not, we
        # still prove the lifecycle because the fake spawn is what actually serves).
        import tempfile
        sentinel = "LOCAL-BATCH-SERVED-OK"
        script = _fake_server_script(sentinel=sentinel)
        with tempfile.TemporaryDirectory() as td:
            script_path = os.path.join(td, "fake_server.py")
            with open(script_path, "w", encoding="utf-8") as fh:
                fh.write(script)

            def fake_spawn(argv, env=None, stdout=None, stderr=None):
                # ignore the backend argv; launch our fake OpenAI server on the lane's host:port
                host = env.get("OLLAMA_HOST", f"{DEFAULT_BATCH_HOST}:{port}").split(":")
                h, p = host[0], host[1] if len(host) > 1 else str(port)
                return subprocess.Popen([sys.executable, script_path, h, p],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            port = _free_port()
            os.environ[ENV_BATCH_BACKEND] = BACKEND_OLLAMA
            os.environ[ENV_OLLAMA_BIN] = sys.executable   # any real binary so detect() succeeds
            os.environ[ENV_BATCH_PORT] = str(port)
            os.environ[ENV_BATCH_MODEL] = "fake-gemma"

            with batch_server(health_timeout_s=15, _spawn=fake_spawn) as lane:
                check("lifecycle: lane is UP (available)", lane.available is True, lane.reason)
                check("lifecycle: base_url is loopback …/v1",
                      lane.base_url == f"http://{DEFAULT_BATCH_HOST}:{port}{OPENAI_V1_SUFFIX}", str(lane.base_url))
                check("lifecycle: lane_tag is local-batch (provenance)", lane.lane_tag == LANE_TAG_LOCAL_BATCH)
                # health really passed (server answers /v1/models)
                check("lifecycle: health endpoint returns 200", _http_ok(lane.base_url + "/models", 2))
                # route a real call THROUGH model_route.from_env() pointed at the local server
                with route_env_override(lane) as active:
                    check("lifecycle: route override active", active is True)
                    check("lifecycle: OPENAI_BASE_URL points at local lane",
                          os.environ.get(ROUTE_BASE_URL_ENV) == lane.base_url)
                    check("lifecycle: higher-priority keys cleared",
                          all(k not in os.environ for k in ROUTE_HIGHER_PRIORITY_KEYS))
                    from scripts.foundry.model_route import from_env as route_from_env
                    route = route_from_env()
                    check("lifecycle: from_env built a route to the local server", route is not None)
                    answer = route.complete("ping") if route else ""
                    check("lifecycle: local server served the completion (sentinel)",
                          sentinel in (answer or ""), repr(answer))
                # override restored after the with-block
                check("lifecycle: route override restored on exit",
                      os.environ.get(ROUTE_BASE_URL_ENV) == saved_env.get(ROUTE_BASE_URL_ENV))
                grabbed_base = lane.base_url

            # ---- 4) SHUTDOWN: after the context exits the server is gone (port no longer healthy) ----
            time.sleep(0.3)
            check("shutdown: server stopped after drain (health now fails)",
                  _http_ok(grabbed_base + "/models", 1) is False)

        # ---- 5) FALLBACK-WHEN-ABSENT proven by job gating ----
        os.environ[ENV_BATCH_LLM] = LANE_LOCAL
        check("job gating: interactive job NEVER uses batch lane",
              job_wants_batch({"latency_class": "interactive"}) is False)
        check("job gating: batch job is eligible when active",
              job_wants_batch({"latency_class": "batch"}) is True)
        check("job gating: untagged job is eligible when active", job_wants_batch({}) is True)
    finally:
        restore_env()

    print(f"\n{'all batch_inference self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _status() -> int:
    """Print the resolved lane decision for the current env (operability check, no server start)."""
    plan = detect_backend() if lane_active() else BackendPlan(False, reason="lane inactive")
    print(json.dumps({
        "active": lane_active(), "backend_available": plan.available, "backend": plan.backend,
        "reason": plan.reason or None, "model": os.environ.get(ENV_BATCH_MODEL, DEFAULT_BATCH_MODEL),
        "host": os.environ.get(ENV_BATCH_HOST, DEFAULT_BATCH_HOST),
        "port": int(os.environ.get(ENV_BATCH_PORT, DEFAULT_BATCH_PORT)),
    }, indent=2))
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Foundry CPU-batch inference lane (optional, degrade-safe).")
    p.add_argument("--self-test", action="store_true", help="offline lifecycle proof via a fake local server")
    p.add_argument("--status", action="store_true", help="print the resolved lane decision for the current env")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.status:
        return _status()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
