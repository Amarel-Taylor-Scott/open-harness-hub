"""tools.web_fetch — a basic, GOVERNED HTTP fetch primitive (the 'basic browser/automation' floor).

stdlib urllib GET with a timeout + size cap + HONEST failure (never raises into a pipeline). GOVERNED:
declares a real User-Agent, no auth/PII, candidate-only output, caller is responsible for ToS/robots. A full
browser (research/browser_port) is the next rung for JS / anti-bot. serves_truth=false (fetched bytes are a
candidate signal, not truth). Deterministic on the failure path; network only on the success path.
"""
from __future__ import annotations

import urllib.error
import urllib.request

_TIMEOUT_S = 15
_MAX_BYTES = 2_000_000
_UA = "Teleon-dogfood/0.1 (governed registry population; respects ToS/robots)"


def fetch(url: str, *, timeout: int = _TIMEOUT_S, max_bytes: int = _MAX_BYTES) -> dict:
    """GET `url` -> {url, status, text, bytes, error}. On any failure returns error set, text empty (no raise)."""
    if not isinstance(url, str) or not url.lower().startswith(("http://", "https://")):
        return {"url": url, "status": None, "text": "", "bytes": 0, "error": "ValueError: url must be http(s)"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (scheme guarded above)
            data = r.read(max_bytes)
        return {"url": url, "status": getattr(r, "status", 200), "text": data.decode("utf-8", "replace"),
                "bytes": len(data), "error": None}
    except Exception as e:  # noqa: BLE001 — honest-fail: a fetch error must not crash the pipeline
        return {"url": url, "status": None, "text": "", "bytes": 0, "error": f"{type(e).__name__}: {str(e)[:120]}"}
