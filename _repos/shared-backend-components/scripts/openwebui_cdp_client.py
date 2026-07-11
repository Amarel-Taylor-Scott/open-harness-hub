#!/usr/bin/env python3
"""Open WebUI browser-context client over Chrome DevTools Protocol.

This module keeps Open WebUI cookies, Cloudflare clearance, and localStorage
inside the browser profile. The local process sends a Runtime.evaluate request
to a logged-in page and receives only the normalized API response.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import base64
import datetime as dt
import json
import os
import socket
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    OPENWEBUI_BASE_URL_ENV,
    OPENWEBUI_CDP_URL_ENV,
    OPENWEBUI_CHAT_COMPLETIONS_PATH,
    OPENWEBUI_DEFAULT_BASE_URL,
    OPENWEBUI_DEFAULT_MODEL,
    OPENWEBUI_MODEL_ENV,
    PRIMITIVE_FACTORY_GEMMA_PAUSE_FILE,
    REPO_ROOT,
)
from scripts._llm_client import (  # noqa: E402 — shared Gemma lane guards (single source; no import cycle)
    GEMMA_SESSION_DOWN_ERROR_LABEL,
    acquire_gemma_call_slot,
    gemma_session_down_error,
    record_gemma_session_down,
    release_gemma_call_slot,
)

DEFAULT_CDP_URL = "http://127.0.0.1:9222"
#: minimal provider shape for the shared lane guards in scripts._llm_client (they key on provider name).
_OPENWEBUI_PROVIDER_SHAPE: dict[str, Any] = {"name": "openwebui"}
_GEMMA_PAUSE_PATH_OVERRIDE: Path | None = None  # self-test only — keeps tests deterministic while a real pause is live


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name) or default


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _parse_utc_time(value: Any) -> dt.datetime | None:
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


def gemma_pause_status(*, model: str) -> dict[str, Any]:
    pause_path = _GEMMA_PAUSE_PATH_OVERRIDE or (_resource(PRIMITIVE_FACTORY_GEMMA_PAUSE_FILE))
    payload = _read_json(pause_path)
    if not payload or payload.get("enabled") is False:
        return {"active": False, "pause_file": str(pause_path)}
    models = payload.get("models")
    paused_models = {str(item) for item in models} if isinstance(models, list) else {OPENWEBUI_DEFAULT_MODEL}
    if model not in paused_models:
        return {"active": False, "pause_file": str(pause_path)}
    expires_at = _parse_utc_time(payload.get("expires_at_utc") or payload.get("expires_at"))
    now = dt.datetime.now(dt.timezone.utc)
    if expires_at and now >= expires_at:
        return {"active": False, "expired": True, "expires_at_utc": expires_at.isoformat(), "pause_file": str(pause_path)}
    return {
        "active": True,
        "expires_at_utc": expires_at.isoformat() if expires_at else "",
        "pause_file": str(pause_path),
        "reason": str(payload.get("reason") or "gemma_calls_paused"),
    }


def _origin(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise AssertionError(f"invalid Open WebUI base URL: {base_url!r}")
    return f"{parsed.scheme}://{parsed.netloc}"


def chat_payload(
    prompt: str,
    *,
    model: str,
    system: str | None = None,
    max_tokens: int | None = None,
    stream: bool = True,
) -> dict[str, Any]:
    """Streaming is the DEFAULT: the Open WebUI origin sits behind a Cloudflare edge whose ~120s proxy-read
    window kills any non-streamed generation longer than 120s with a 524 (observed 2026-07-02 at 125s per
    call). SSE keeps bytes flowing for the whole generation, so long candidate-writer calls survive."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body: dict[str, Any] = {
        "model": model,
        "stream": bool(stream),
        "messages": messages,
    }
    if stream:
        body["stream_options"] = {"include_usage": True}  # OpenAI-compatible: final SSE chunk carries usage
    if max_tokens:
        body["max_tokens"] = max_tokens
        body["max_completion_tokens"] = max_tokens
    return body


class CDPClient:
    """Minimal stdlib WebSocket client for CDP Runtime.evaluate."""

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self._id = 0
        self._buf = b""
        host, _, rest = ws_url.split("ws://", 1)[1].partition("/")
        hostname, port = host.split(":")
        self.sock = socket.create_connection((hostname, int(port)), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        handshake = (
            f"GET /{rest} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake.encode("ascii"))
        while b"\r\n\r\n" not in self._buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise AssertionError("CDP websocket closed during upgrade")
            self._buf += chunk
        header, self._buf = self._buf.split(b"\r\n\r\n", 1)
        if b" 101 " not in header.split(b"\r\n", 1)[0]:
            raise AssertionError("CDP websocket upgrade failed")
        self.sock.settimeout(None)

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def _send(self, payload: bytes) -> None:
        mask = os.urandom(4)
        size = len(payload)
        header = bytearray([0x81])
        if size < 126:
            header.append(0x80 | size)
        elif size < 65536:
            header += bytes([0x80 | 126]) + size.to_bytes(2, "big")
        else:
            header += bytes([0x80 | 127]) + size.to_bytes(8, "big")
        self.sock.sendall(bytes(header) + mask + bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload)))

    def _recv_chunk(self, size: int, *, deadline: float | None) -> bytes:
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("CDP websocket receive deadline expired")
            self.sock.settimeout(remaining)
        else:
            self.sock.settimeout(None)
        try:
            chunk = self.sock.recv(size)
        except socket.timeout as exc:
            raise TimeoutError("CDP websocket receive timed out") from exc
        if not chunk:
            raise AssertionError("CDP websocket closed")
        return chunk

    def _recv_frame(self, *, deadline: float | None = None) -> bytes:
        def need(size: int) -> None:
            while len(self._buf) < size:
                self._buf += self._recv_chunk(65536, deadline=deadline)

        need(2)
        opcode = self._buf[0] & 0x0F
        size = self._buf[1] & 0x7F
        offset = 2
        if size == 126:
            need(4)
            size = int.from_bytes(self._buf[2:4], "big")
            offset = 4
        elif size == 127:
            need(10)
            size = int.from_bytes(self._buf[2:10], "big")
            offset = 10
        masked = bool(self._buf[1] & 0x80)
        if masked:
            need(offset + 4)
            mask = self._buf[offset:offset + 4]
            offset += 4
        else:
            mask = b""
        need(offset + size)
        data = self._buf[offset:offset + size]
        self._buf = self._buf[offset + size:]
        if masked:
            data = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
        if opcode == 0x8:
            raise AssertionError("CDP websocket closed")
        return data

    def call(self, method: str, params: dict[str, Any] | None = None, *, timeout: float = 120.0) -> dict[str, Any]:
        self._id += 1
        message_id = self._id
        self._send(json.dumps({"id": message_id, "method": method, "params": params or {}}).encode("utf-8"))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                payload = self._recv_frame(deadline=deadline)
            except TimeoutError as exc:
                raise TimeoutError(f"{method} timed out after {timeout:.1f}s") from exc
            message = json.loads(payload.decode("utf-8", "ignore"))
            if message.get("id") == message_id:
                if message.get("error"):
                    raise AssertionError(json.dumps(message["error"], sort_keys=True))
                return message.get("result", {})
        raise TimeoutError(f"{method} timed out after {timeout:.1f}s")

    def evaluate(self, expression: str, *, timeout: float = 180.0) -> Any:
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
            },
            timeout=timeout,
        )
        inner = result.get("result") or {}
        if "exceptionDetails" in result:
            raise AssertionError(json.dumps(result["exceptionDetails"], sort_keys=True))
        return inner.get("value")


def _json(url: str, *, timeout: int = 10) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def list_targets(cdp_url: str) -> list[dict[str, Any]]:
    return list(_json(cdp_url.rstrip("/") + "/json/list"))


def find_openwebui_target(cdp_url: str, base_url: str) -> dict[str, Any]:
    origin = _origin(base_url)
    targets = list_targets(cdp_url)
    pages = [target for target in targets if target.get("type") == "page" and target.get("webSocketDebuggerUrl")]
    preferred = [
        target
        for target in pages
        if str(target.get("url") or "").startswith(origin)
    ]
    if preferred:
        return preferred[0]
    if pages:
        return pages[0]
    raise AssertionError("no CDP page target with webSocketDebuggerUrl")


def _needs_app_navigation(current_url: str, origin: str) -> bool:
    """True when the CDP target is not an Open WebUI app document."""
    if not current_url.startswith(origin):
        return True
    parsed = urllib.parse.urlparse(current_url)
    return parsed.path.startswith("/api/")


def _evaluate_chat_expression(*, body: dict[str, Any], endpoint: str) -> str:
    """Page-context fetch. Streamed (SSE) responses are assembled INSIDE the page and returned in the same
    normalized shape as a non-streamed chat completion, so normalize_chat_response works for both."""
    return f"""
(async () => {{
  const token = localStorage.getItem("token");
  const headers = {{
    "Content-Type": "application/json",
    "Accept": "text/event-stream, application/json"
  }};
  if (token) {{
    headers.Authorization = `Bearer ${{token}}`;
  }}
  const response = await fetch({json.dumps(endpoint)}, {{
    method: "POST",
    headers,
    credentials: "include",
    cache: "no-store",
    body: JSON.stringify({json.dumps(body, ensure_ascii=True)})
  }});
  const contentType = response.headers.get("content-type") || "";
  if (!response.ok) {{
    const text = await response.text();
    let data = null;
    if (contentType.includes("application/json")) {{
      try {{ data = JSON.parse(text); }} catch (error) {{ data = null; }}
    }}
    return {{
      ok: false,
      status: response.status,
      content_type: contentType,
      body_text_sample: text.slice(0, 500),
      data
    }};
  }}
  if (!contentType.includes("text/event-stream") || !response.body) {{
    // Non-streamed response (server ignored stream:true): parse the plain JSON body as before.
    const text = await response.text();
    let data = null;
    try {{ data = JSON.parse(text); }} catch (error) {{ data = null; }}
    return {{
      ok: true,
      status: response.status,
      content_type: contentType,
      body_text_sample: text.slice(0, 500),
      data
    }};
  }}
  // SSE stream: bytes keep flowing while the model generates, so the Cloudflare edge's ~120s
  // proxy-read window never expires (the stream:false path 524'd every generation over 120s).
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffered = "";
  let content = "";
  let reasoning = "";
  let usage = null;
  let responseId = null;
  let responseModel = null;
  let responseObject = null;
  let finishReason = null;
  const consume = (line) => {{
    const trimmed = line.trim();
    if (!trimmed.startsWith("data:")) return;
    const payload = trimmed.slice(5).trim();
    if (!payload || payload === "[DONE]") return;
    let chunk = null;
    try {{ chunk = JSON.parse(payload); }} catch (error) {{ return; }}
    responseId = chunk.id || responseId;
    responseModel = chunk.model || responseModel;
    responseObject = chunk.object || responseObject;
    if (chunk.usage) usage = chunk.usage;
    const choice = (chunk.choices || [])[0] || {{}};
    const delta = choice.delta || choice.message || {{}};
    if (typeof delta.content === "string") content += delta.content;
    if (typeof delta.reasoning === "string") reasoning += delta.reasoning;
    else if (typeof delta.reasoning_content === "string") reasoning += delta.reasoning_content;
    if (choice.finish_reason) finishReason = choice.finish_reason;
  }};
  while (true) {{
    const {{ done, value }} = await reader.read();
    if (done) break;
    buffered += decoder.decode(value, {{ stream: true }});
    const lines = buffered.split("\\n");
    buffered = lines.pop();
    for (const line of lines) consume(line);
  }}
  buffered += decoder.decode();
  if (buffered) consume(buffered);
  const data = {{
    id: responseId,
    model: responseModel,
    object: responseObject,
    usage: usage || {{}},
    choices: [{{ finish_reason: finishReason, message: {{ content: content, reasoning: reasoning }} }}]
  }};
  return {{
    ok: true,
    status: response.status,
    content_type: contentType,
    body_text_sample: content.slice(0, 500),
    data
  }};
}})()
"""


def _evaluate_probe_expression(*, include_chat_check: bool = True, model: str | None = None) -> str:
    model_id = model or OPENWEBUI_DEFAULT_MODEL
    if include_chat_check:
        chat_js = (
            "await check(" + json.dumps(OPENWEBUI_CHAT_COMPLETIONS_PATH) + ", \"POST\", {\n"
            "      model: " + json.dumps(model_id) + ",\n"
            "      stream: false,\n"
            "      messages: [{role: \"user\", content: \"Print exactly: probe\"}],\n"
            "      max_tokens: 16\n"
            "    })"
        )
    else:
        chat_js = "{skipped: true}"  # gated off: never post a generation while paused/rate-limited
    return """
(async () => {
  const token = localStorage.getItem("token");
  async function check(path, method = "GET", body = null) {
    const headers = {"Accept": "application/json"};
    if (body) headers["Content-Type"] = "application/json";
    if (token) headers.Authorization = `Bearer ${token}`;
    try {
      const response = await fetch(path, {
        method,
        headers,
        credentials: "include",
        cache: "no-store",
        body: body ? JSON.stringify(body) : null
      });
      const contentType = response.headers.get("content-type") || "";
      const text = await response.text();
      return {
        ok: response.ok,
        status: response.status,
        content_type: contentType,
        body_text_sample: text.slice(0, 160)
      };
    } catch (error) {
      return {ok: false, status: 0, content_type: "", body_text_sample: String(error).slice(0, 160)};
    }
  }
  return {
    href: location.href,
    title: document.title,
    token_present: Boolean(token),
    config: await check("/api/config"),
    models: await check("/api/models"),
    chat: __CHAT_CHECK__
  };
})()
""".replace("__CHAT_CHECK__", chat_js)


def probe_cdp_state(
    *,
    base_url: str | None = None,
    cdp_url: str | None = None,
    timeout: int = 60,
    include_chat_check: bool | None = None,
) -> dict[str, Any]:
    """Config/models checks are cheap and always run. The chat sub-check is a REAL GPU generation, so by
    default (include_chat_check=None) it is gated behind the operator pause, the session-down breaker, and
    the fleet-wide rate limiter (no sleeping — a probe never waits for a slot). Pass True/False to force."""
    base = base_url or _env(OPENWEBUI_BASE_URL_ENV, OPENWEBUI_DEFAULT_BASE_URL)
    cdp = cdp_url or _env(OPENWEBUI_CDP_URL_ENV, DEFAULT_CDP_URL)
    model_id = _env(OPENWEBUI_MODEL_ENV, OPENWEBUI_DEFAULT_MODEL)
    chat_skip_reason = ""
    gemma_slot = None
    if include_chat_check is None:
        pause = gemma_pause_status(model=model_id)
        if pause.get("active"):
            chat_skip_reason = f"operator pause active until {pause.get('expires_at_utc') or 'disabled'}"
        else:
            chat_skip_reason = gemma_session_down_error(model=model_id, provider=_OPENWEBUI_PROVIDER_SHAPE)
        if not chat_skip_reason:
            rate_error, gemma_slot = acquire_gemma_call_slot(
                model=model_id, provider=_OPENWEBUI_PROVIDER_SHAPE, max_sleep_seconds=0,
            )
            chat_skip_reason = rate_error
        include_chat = not chat_skip_reason
    else:
        include_chat = bool(include_chat_check)
        chat_skip_reason = "" if include_chat else "chat check disabled by caller"
    try:
        target = find_openwebui_target(cdp, base)
        client = CDPClient(str(target["webSocketDebuggerUrl"]))
        try:
            client.call("Runtime.enable")
            origin = _origin(base)
            current_url = str(target.get("url") or "")
            if _needs_app_navigation(current_url, origin):
                client.call("Page.navigate", {"url": origin})
                time.sleep(2.0)
            raw = client.evaluate(
                _evaluate_probe_expression(include_chat_check=include_chat, model=model_id), timeout=timeout,
            )
        finally:
            client.close()
    finally:
        release_gemma_call_slot(gemma_slot)
    if not isinstance(raw, dict):
        raise AssertionError("CDP probe returned a non-object response")
    chat_result = raw.get("chat") or {}
    if not include_chat:
        chat_result = {"skipped": True, "skip_reason": chat_skip_reason}
    return {
        "record_type": "openwebui_cdp_probe",
        "base_url": base,
        "cdp_url": cdp,
        "href": raw.get("href"),
        "title": raw.get("title"),
        "token_present": bool(raw.get("token_present")),
        "config": raw.get("config") or {},
        "models": raw.get("models") or {},
        "chat": chat_result,
        "exports_browser_token": False,
        "exports_cookies": False,
        "exports_clearance": False,
        "candidate": True,
        "serves_truth": False,
    }


def normalize_chat_response(response: dict[str, Any], *, base_url: str, model: str, prompt: str, auth_mode: str) -> dict[str, Any]:
    data = response.get("data") or {}
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    return {
        "assistant_content": message.get("content") or message.get("reasoning") or message.get("reasoning_content") or "",
        "auth_mode": auth_mode,
        "base_url": base_url,
        "candidate_only": True,
        "endpoint": OPENWEBUI_CHAT_COMPLETIONS_PATH,
        "finish_reason": choice.get("finish_reason"),
        "http_status": response.get("status"),
        "model": data.get("model") or model,
        "object": data.get("object"),
        "prompt_sha256": __import__("hashlib").sha256(prompt.encode("utf-8")).hexdigest(),
        "provider": "open_webui",
        "response_id": data.get("id"),
        "serves_truth": False,
        "system_fingerprint": data.get("system_fingerprint"),
        "usage": data.get("usage") or {},
    }


def cdp_chat(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    cdp_url: str | None = None,
    max_tokens: int | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    base = base_url or _env(OPENWEBUI_BASE_URL_ENV, OPENWEBUI_DEFAULT_BASE_URL)
    model_id = model or _env(OPENWEBUI_MODEL_ENV, OPENWEBUI_DEFAULT_MODEL)
    pause = gemma_pause_status(model=model_id)
    if pause.get("active"):
        raise AssertionError(
            "Gemma Open WebUI calls are paused"
            f" until {pause.get('expires_at_utc') or 'the pause file is disabled'}:"
            f" {pause.get('reason')}"
        )
    session_error = gemma_session_down_error(model=model_id, provider=_OPENWEBUI_PROVIDER_SHAPE)
    if session_error:  # origin breaker: fail fast in <1s instead of burning 15-125s per shard against a dead origin
        raise AssertionError(session_error)
    rate_error, gemma_slot = acquire_gemma_call_slot(model=model_id, provider=_OPENWEBUI_PROVIDER_SHAPE)
    if rate_error:  # severe fleet-wide GPU pacing — pause beats rate limit (both checked above)
        raise AssertionError(rate_error)
    try:
        cdp = cdp_url or _env(OPENWEBUI_CDP_URL_ENV, DEFAULT_CDP_URL)
        target = find_openwebui_target(cdp, base)
        client = CDPClient(str(target["webSocketDebuggerUrl"]))
        try:
            client.call("Runtime.enable")
            current_url = str(target.get("url") or "")
            origin = _origin(base)
            if _needs_app_navigation(current_url, origin):
                client.call("Page.navigate", {"url": origin})
                time.sleep(2.0)
            body = chat_payload(prompt, model=model_id, system=system, max_tokens=max_tokens)
            raw = client.evaluate(_evaluate_chat_expression(body=body, endpoint=OPENWEBUI_CHAT_COMPLETIONS_PATH), timeout=timeout)
        finally:
            client.close()
    finally:
        release_gemma_call_slot(gemma_slot)
    if not isinstance(raw, dict):
        raise AssertionError("CDP fetch returned a non-object response")
    if not raw.get("ok"):
        status = raw.get("status")
        message = f"Open WebUI CDP fetch failed: status={status} sample={raw.get('body_text_sample')!r}"
        if record_gemma_session_down(model=model_id, status=status, reason=message):
            # Cloudflare-edge 5xx = the ORIGIN is down/degraded; the breaker file makes every
            # concurrent + subsequent worker fail fast with this grep-able label until it expires.
            raise AssertionError(f"{GEMMA_SESSION_DOWN_ERROR_LABEL}: {message}")
        raise AssertionError(message)
    return normalize_chat_response(raw, base_url=base, model=model_id, prompt=prompt, auth_mode="browser_context_token_not_exported")


def redacted_plan(*, mode: str, base_url: str | None = None, cdp_url: str | None = None) -> dict[str, Any]:
    return {
        "record_type": "openwebui_redacted_plan",
        "mode": mode,
        "base_url": base_url or _env(OPENWEBUI_BASE_URL_ENV, OPENWEBUI_DEFAULT_BASE_URL),
        "cdp_url": cdp_url or _env(OPENWEBUI_CDP_URL_ENV, DEFAULT_CDP_URL),
        "endpoint": OPENWEBUI_CHAT_COMPLETIONS_PATH,
        "model": _env(OPENWEBUI_MODEL_ENV, OPENWEBUI_DEFAULT_MODEL),
        "exports_browser_token": False,
        "exports_cookies": False,
        "exports_clearance": False,
        "candidate": True,
        "serves_truth": False,
    }


def _self_test() -> int:
    """Offline proof of the Gemma CDP lane guards (zero network/CDP; real pause/state files never touched)."""
    import tempfile

    from scripts import _llm_client as llm

    global _GEMMA_PAUSE_PATH_OVERRIDE
    checks: list[tuple[str, bool]] = []
    payload = chat_payload("p", model="m", system="s", max_tokens=7)
    checks.append(("chat payload defaults to SSE streaming with usage in the final chunk (Cloudflare 524 guard)",
                   payload["stream"] is True and payload.get("stream_options") == {"include_usage": True}
                   and payload["max_tokens"] == 7 and payload["max_completion_tokens"] == 7
                   and payload["messages"][0]["role"] == "system"))
    non_stream = chat_payload("p", model="m", stream=False)
    checks.append(("stream=False stays supported for bounded probes",
                   non_stream["stream"] is False and "stream_options" not in non_stream))
    expression = _evaluate_chat_expression(body=payload, endpoint=OPENWEBUI_CHAT_COMPLETIONS_PATH)
    checks.append(("chat expression streams SSE in the page (reader loop, [DONE] handling, plain-JSON fallback)",
                   "text/event-stream" in expression and "[DONE]" in expression and "getReader()" in expression
                   and json.dumps(OPENWEBUI_CHAT_COMPLETIONS_PATH) in expression
                   and "delta" in expression and "reasoning_content" in expression))
    probe_with = _evaluate_probe_expression(include_chat_check=True, model="m-x")
    probe_without = _evaluate_probe_expression(include_chat_check=False, model="m-x")
    checks.append(("probe chat sub-check is gated (the skipped variant never posts a generation)",
                   OPENWEBUI_CHAT_COMPLETIONS_PATH in probe_with and json.dumps("m-x") in probe_with
                   and OPENWEBUI_CHAT_COMPLETIONS_PATH not in probe_without and "skipped" in probe_without))
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _GEMMA_PAUSE_PATH_OVERRIDE = tmp_path / "GEMMA_PAUSE.json"
        llm._GEMMA_SESSION_DOWN_PATH_OVERRIDE = tmp_path / "GEMMA_SESSION_DOWN.json"
        llm._GEMMA_RATE_LIMIT_PATH_OVERRIDE = tmp_path / "GEMMA_RATE_LIMIT.json"
        unreachable_cdp = "http://127.0.0.1:1"  # every guard below must raise BEFORE any CDP/network access
        try:
            _GEMMA_PAUSE_PATH_OVERRIDE.write_text(json.dumps({
                "enabled": True, "models": [OPENWEBUI_DEFAULT_MODEL],
                "expires_at_utc": "2099-01-01T00:00:00Z", "reason": "self-test operator pause"}), encoding="utf-8")
            try:
                cdp_chat("p", model=OPENWEBUI_DEFAULT_MODEL, cdp_url=unreachable_cdp)
                pause_ok = False
            except AssertionError as exc:
                pause_ok = "paused" in str(exc) and "self-test operator pause" in str(exc)
            checks.append(("an active operator pause fails cdp_chat fast before any CDP access", pause_ok))
            _GEMMA_PAUSE_PATH_OVERRIDE.unlink()
            llm.record_gemma_session_down(model=OPENWEBUI_DEFAULT_MODEL, status=521, reason="origin down (self-test)")
            try:
                cdp_chat("p", model=OPENWEBUI_DEFAULT_MODEL, cdp_url=unreachable_cdp)
                session_ok = False
            except AssertionError as exc:
                session_ok = str(exc).startswith(GEMMA_SESSION_DOWN_ERROR_LABEL)
            checks.append(("an active session-down breaker fails cdp_chat fast with the label", session_ok))
            llm._GEMMA_SESSION_DOWN_PATH_OVERRIDE.unlink()
            hold_error, hold_slot = acquire_gemma_call_slot(model=OPENWEBUI_DEFAULT_MODEL,
                                                            provider=_OPENWEBUI_PROVIDER_SHAPE)
            try:
                cdp_chat("p", model=OPENWEBUI_DEFAULT_MODEL, cdp_url=unreachable_cdp)
                rate_ok = False
            except AssertionError as exc:
                rate_ok = str(exc).startswith(llm.GEMMA_RATE_LIMITED_ERROR_LABEL)
            finally:
                release_gemma_call_slot(hold_slot)
            checks.append(("a held fleet-wide slot fails cdp_chat fast with the rate-limited label",
                           hold_error == "" and rate_ok))
        finally:
            _GEMMA_PAUSE_PATH_OVERRIDE = None
            llm._GEMMA_SESSION_DOWN_PATH_OVERRIDE = None
            llm._GEMMA_RATE_LIMIT_PATH_OVERRIDE = None
    failures = [name for name, ok in checks if not ok]
    print("PASS - openwebui_cdp_client: SSE streaming chat payload/expression (524 guard), gated probe chat, "
          "and cdp_chat fail-fast guards (operator pause -> session-down breaker -> severe rate limiter), "
          "all raised before any CDP/network access."
          if not failures else
          f"FAIL - openwebui_cdp_client self-test: {failures}")
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="offline lane-guard + streaming-shape proof (no network, no CDP, real files untouched)")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--prompt", default="Print exactly: Open WebUI browser-context integration OK")
    parser.add_argument("--system", default="")
    parser.add_argument("--model", default=_env(OPENWEBUI_MODEL_ENV, OPENWEBUI_DEFAULT_MODEL))
    parser.add_argument("--base-url", default=_env(OPENWEBUI_BASE_URL_ENV, OPENWEBUI_DEFAULT_BASE_URL))
    parser.add_argument("--cdp-url", default=_env(OPENWEBUI_CDP_URL_ENV, DEFAULT_CDP_URL))
    parser.add_argument("--max-tokens", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.plan:
        print(json.dumps(redacted_plan(mode="cdp", base_url=args.base_url, cdp_url=args.cdp_url), indent=2, sort_keys=True))
        return 0
    if args.probe:
        try:
            print(json.dumps(
                probe_cdp_state(base_url=args.base_url, cdp_url=args.cdp_url, timeout=args.timeout),
                indent=2,
                sort_keys=True,
            ))
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        return 0
    try:
        result = cdp_chat(
            args.prompt,
            system=args.system or None,
            model=args.model,
            base_url=args.base_url,
            cdp_url=args.cdp_url,
            max_tokens=args.max_tokens or None,
            timeout=args.timeout,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
