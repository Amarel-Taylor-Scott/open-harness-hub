#!/usr/bin/env python3
"""local_emulators.model_emulator — a deterministic, OpenAI-compatible LOCAL model server for local dev
(Docker / Tilt). Closes the go-live "live LLM inference" seam locally without a GPU, a key, or a network call.

  POST /v1/chat/completions  {model, messages:[{role,content}]}
    -> {choices:[{message:{role:'assistant', content:<deterministic>}}], usage:{prompt_tokens, completion_tokens}}

The completion is a DETERMINISTIC hash of the prompt (same prompt -> same output), so local runs are reproducible
and the usage block reports real token counts (-> tokens_in/tokens_out telemetry). It stands in for Ollama/Codex
locally; LLM output is NEVER truth (a candidate). Importable (in-process) + runnable (stdlib http.server only).
"""
from __future__ import annotations

import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

_MODEL_ID = "local-emulator-deterministic@v1"


def _est_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)  # ~4 chars/token, matching token_reduction.estimate_tokens


class ModelEmulator:
    """In-process deterministic 'model'. ``complete`` returns a stable response + token usage for a prompt."""

    model_id = _MODEL_ID
    serves_truth = False  # LLM output is never truth — a candidate proposal

    def complete(self, prompt: str) -> dict:
        digest = hashlib.sha256((prompt or "").encode("utf-8")).hexdigest()[:12]
        content = f"[local-emulated deterministic completion {digest}]"
        return {"model": self.model_id, "content": content, "serves_truth": False,
                "tokens_in": _est_tokens(prompt), "tokens_out": _est_tokens(content)}


def _prompt_of(messages: list) -> str:
    return "\n".join(str(m.get("content", "")) for m in (messages or []))


def _make_handler(emu: ModelEmulator):
    class _H(BaseHTTPRequestHandler):
        def _send(self, code: int, body: dict) -> None:
            data = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802
            if self.path.rstrip("/") in ("", "/health", "/healthz", "/v1/models"):
                self._send(200, {"ok": True, "model": emu.model_id, "serves_truth": False})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            if self.path.rstrip("/") != "/v1/chat/completions":
                self._send(404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
            r = emu.complete(_prompt_of(body.get("messages", [])))
            self._send(200, {
                "model": r["model"], "is_truth": False,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": r["content"]},
                             "finish_reason": "stop"}],
                "usage": {"prompt_tokens": r["tokens_in"], "completion_tokens": r["tokens_out"],
                          "total_tokens": r["tokens_in"] + r["tokens_out"]},
            })

        def log_message(self, *_args):  # quiet
            return
    return _H


def serve(emu: ModelEmulator | None = None, *, host: str = "0.0.0.0", port: int = 8080) -> None:  # pragma: no cover
    emu = emu or ModelEmulator()
    HTTPServer((host, port), _make_handler(emu)).serve_forever()


if __name__ == "__main__":  # pragma: no cover
    serve(host=os.environ.get("EMU_HOST", "0.0.0.0"), port=int(os.environ.get("EMU_MODEL_PORT", "8080")))
