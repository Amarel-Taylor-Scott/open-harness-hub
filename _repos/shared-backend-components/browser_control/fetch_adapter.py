#!/usr/bin/env python3
"""browser_control.fetch_adapter — the raw HTTP-GET primitive (requests / httpx / aiohttp / urllib).

The cheapest, highest-volume lane in the zoo: a single read-only GET that returns a structured RESPONSE
record (status, safe headers, bounded+redacted body, latency, backend used) — no browser, no JS. It is the
layer BELOW the driver-neutral BrowserAdapter: HttpScrapeAdapter wraps the harness StaticBackend to expose
the full navigate/extract command surface; FetchAdapter is the lower-level fetch you compose a crawler or a
parser on top of.

REUSE-FIRST: extraction/parsing is NOT re-implemented here — pair this with ParserAdapter. Secret redaction
delegates to the harness ``redact_secrets`` (single source); robots permission delegates to
``browser_control.safety.robots_gate`` (→ the harness robots policy). The only logic added is backend
selection + a read-only, never-raising GET that produces an evidence record.

Read-only by construction: there is NO post/put/delete/form-submit method. Every optional HTTP client is
imported LAZILY inside the backend so importing this module never needs requests/httpx/aiohttp (urllib, the
stdlib fallback, is always present). Every result is candidate-only (``serves_truth=false``); an unsupported
or failed call returns a structured dict and NEVER raises.

    python3 browser_control/ingestion_self_test.py --self-test   # offline (loopback fixture), mutation-gated
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install  # noqa: E402

_install()

import importlib.util  # noqa: E402
import time  # noqa: E402
import urllib.error  # noqa: E402
import urllib.parse  # noqa: E402
import urllib.request  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import BOUNDARY, redact_secrets  # noqa: E402  single-source redactor

from browser_control import safety  # noqa: E402  single-source robots + redaction policy

#: HTTP client backends, most-preferred first. urllib (stdlib) is always available and closes the list.
HTTP_BACKENDS: tuple[str, ...] = ("requests", "httpx", "urllib")
#: response headers safe to surface — a whitelist so Set-Cookie / Authorization echoes never leak into a record
_SAFE_RESPONSE_HEADERS: tuple[str, ...] = (
    "content-type", "content-length", "content-encoding", "server", "date", "last-modified", "etag",
    "cache-control", "vary", "x-powered-by", "content-language")
_DEFAULT_UA = "AIDoneRight-PrimitiveDiscovery/1.0 (+read-only research fetch; respects robots.txt)"
_DEFAULT_TIMEOUT_S = 15.0
_DEFAULT_MAX_TEXT_CHARS = 20000        # bounded body stored per fetch (digest/handle carry the rest; no raw dumps)


def _import_ok(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:  # noqa: BLE001
        return False


class FetchAdapter:
    """A read-only HTTP-GET adapter over requests → httpx → urllib. ``get(url)`` returns a structured response
    record; it NEVER raises (network / bad-scheme / robots-block all become a structured ``ok=False`` record) and
    NEVER writes (GET only). Secrets are redacted and cookies are dropped before anything is returned."""

    name = "fetch"

    def __init__(self, *, backend: str = "auto", ua: Optional[str] = None, timeout: float = _DEFAULT_TIMEOUT_S,
                 respect_robots: bool = True, robots_fetch: Optional[Callable[[str], Optional[str]]] = None,
                 max_text_chars: int = _DEFAULT_MAX_TEXT_CHARS) -> None:
        self._backend = backend
        self._ua = ua or _DEFAULT_UA
        self._timeout = float(timeout)
        self._respect_robots = bool(respect_robots)
        self._robots_fetch = robots_fetch
        self._max_text = int(max_text_chars)

    # ── capability introspection ─────────────────────────────────────────────────────────────────────────────
    def available_backends(self) -> dict[str, bool]:
        """Which HTTP client backends are importable right now (urllib is always True)."""
        return {"requests": _import_ok("requests"), "httpx": _import_ok("httpx"),
                "aiohttp": _import_ok("aiohttp"), "urllib": True}

    def _pick_backend(self, requested: Optional[str]) -> str:
        want = requested or self._backend
        avail = self.available_backends()
        if want and want != "auto":
            return want if avail.get(want) else "urllib"
        return next((b for b in HTTP_BACKENDS if avail.get(b)), "urllib")

    def capabilities(self) -> dict[str, Any]:
        return {"adapter": self.name, "read_only": True, "methods": ["get"], "js_render": False,
                "respect_robots": self._respect_robots, "backends_available": self.available_backends(),
                "preferred_backend": self._pick_backend(None), **BOUNDARY}

    # ── the one command: a read-only GET ─────────────────────────────────────────────────────────────────────
    def get(self, url: str, *, headers: Optional[dict[str, str]] = None, timeout: Optional[float] = None,
            backend: Optional[str] = None) -> dict[str, Any]:
        """Single read-only GET → structured response record. Respects robots.txt (unless ``respect_robots=False``);
        a disallowed URL is NEVER fetched. Body is bounded + secret-redacted; cookies are dropped; never raises."""
        parts = urllib.parse.urlparse(url)
        if parts.scheme not in ("http", "https"):
            return self._record(url, ok=False, failure_mode="bad_scheme",
                                 error=f"only http/https supported, got {parts.scheme!r}")
        if self._respect_robots and not safety.robots_gate(url, fetch=self._robots_fetch, ua=self._ua):
            return self._record(url, ok=False, blocked=True, failure_mode="robots_disallow",
                                 error="robots.txt disallows this URL for our user-agent")
        chosen = self._pick_backend(backend)
        req_headers = {"User-Agent": self._ua, **(headers or {})}
        t0 = time.monotonic()
        try:
            if chosen == "requests":
                raw = self._get_requests(url, req_headers, timeout)
            elif chosen == "httpx":
                raw = self._get_httpx(url, req_headers, timeout)
            else:
                chosen, raw = "urllib", self._get_urllib(url, req_headers, timeout)
        except Exception as exc:  # noqa: BLE001 — every failure degrades to a structured record, never raises
            return self._record(url, ok=False, backend=chosen, failure_mode=type(exc).__name__,
                                 error=f"{type(exc).__name__}: {exc}"[:240],
                                 elapsed_ms=round((time.monotonic() - t0) * 1000, 1))
        elapsed_ms = round((time.monotonic() - t0) * 1000, 1)
        body = raw.get("text") or ""
        truncated = len(body) > self._max_text
        clean, n_red = redact_secrets(body[:self._max_text])
        status = int(raw.get("status") or 0)
        return self._record(
            url, ok=200 <= status < 400, backend=chosen, status=status, final_url=raw.get("final_url", url),
            content_type=raw.get("content_type", ""), bytes=raw.get("bytes", len(body.encode("utf-8", "ignore"))),
            text=clean, text_chars=len(clean), truncated=truncated, secrets_redacted=n_red,
            headers=self._safe_headers(raw.get("headers") or {}), elapsed_ms=elapsed_ms,
            failure_mode=None if 200 <= status < 400 else f"http_{status}")

    # ── backend implementations (GET only; lazy imports) ─────────────────────────────────────────────────────
    def _get_requests(self, url: str, headers: dict, timeout: Optional[float]) -> dict[str, Any]:
        import requests  # lazy
        resp = requests.get(url, headers=headers, timeout=timeout or self._timeout, allow_redirects=True)
        return {"status": resp.status_code, "final_url": resp.url, "text": resp.text,
                "content_type": resp.headers.get("Content-Type", ""), "bytes": len(resp.content),
                "headers": dict(resp.headers)}

    def _get_httpx(self, url: str, headers: dict, timeout: Optional[float]) -> dict[str, Any]:
        import httpx  # lazy
        resp = httpx.get(url, headers=headers, timeout=timeout or self._timeout, follow_redirects=True)
        return {"status": resp.status_code, "final_url": str(resp.url), "text": resp.text,
                "content_type": resp.headers.get("Content-Type", ""), "bytes": len(resp.content),
                "headers": dict(resp.headers)}

    def _get_urllib(self, url: str, headers: dict, timeout: Optional[float]) -> dict[str, Any]:
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout or self._timeout) as resp:  # noqa: S310
                data = resp.read()
                return {"status": resp.getcode(), "final_url": resp.geturl(),
                        "text": data.decode("utf-8", "ignore"),
                        "content_type": resp.headers.get("Content-Type", ""), "bytes": len(data),
                        "headers": dict(resp.headers.items())}
        except urllib.error.HTTPError as http_err:                 # a 4xx/5xx IS the answer — keep the status
            try:
                data = http_err.read()
            except Exception:  # noqa: BLE001
                data = b""
            return {"status": http_err.code, "final_url": url, "text": data.decode("utf-8", "ignore"),
                    "content_type": http_err.headers.get("Content-Type", "") if http_err.headers else "",
                    "bytes": len(data), "headers": dict(http_err.headers.items()) if http_err.headers else {}}

    # ── helpers ──────────────────────────────────────────────────────────────────────────────────────────────
    def _safe_headers(self, headers: dict) -> dict[str, str]:
        """Whitelist only non-sensitive response metadata; Set-Cookie / Authorization echoes never survive."""
        low = {str(k).lower(): str(v) for k, v in headers.items()}
        out = {k: low[k] for k in _SAFE_RESPONSE_HEADERS if k in low}
        clean, _ = safety.redact_fields(out)                        # belt-and-suspenders redaction
        return clean

    def _record(self, url: str, *, ok: bool, backend: str = "none", status: int = 0, final_url: str = "",
                content_type: str = "", bytes: int = 0, text: str = "", text_chars: int = 0,  # noqa: A002
                truncated: bool = False, secrets_redacted: int = 0, headers: Optional[dict] = None,
                elapsed_ms: float = 0.0, blocked: bool = False, failure_mode: Optional[str] = None,
                error: Optional[str] = None) -> dict[str, Any]:
        return {"supported": True, "adapter": self.name, "method": "GET", "ok": ok, "blocked": blocked,
                "backend": backend, "url": url, "final_url": final_url or url, "status": status,
                "content_type": content_type, "bytes": bytes, "text": text, "text_chars": text_chars,
                "truncated": truncated, "secrets_redacted": secrets_redacted, "headers": headers or {},
                "elapsed_ms": elapsed_ms, "failure_mode": failure_mode, "error": error, **BOUNDARY}


__all__ = ["FetchAdapter", "HTTP_BACKENDS"]
