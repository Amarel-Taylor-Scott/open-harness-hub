#!/usr/bin/env python3
"""browser_control.adapters.cdp_adapter — the ZERO-PIP live adapter (system Chrome over CDP).

Wraps the harness CdpBackend (which launches the installed Chrome headless and drives it via the shipped
stdlib CDP transport, scripts.browser_capture.CDP) + TabControlAPI. It backs the FULL command surface —
real tab control (CDP Target.*), navigation, DOM, and a REAL screenshot (bytes hashed, never stored).

LIVE-ONLY + LAZY: no browser is launched until start_session(); if Chrome is absent or fails to launch,
start_session returns a structured ``{"supported": False, "reason": ...}`` result (it NEVER raises), so the
offline test suite never needs a browser. Use it for real logged-in/attached sessions, tabs/popups, and
downloads where a genuine browser is required.
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[2])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install  # noqa: E402

_install()

from typing import Any, Callable, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import BackendPort, CdpBackend, _sha256  # noqa: E402

from browser_control.adapter import CAPABILITY_KEYS, _BackendAdapter, _wall_clock  # noqa: E402


class CdpAdapter(_BackendAdapter):
    """Live adapter over the installed Chrome via the harness CdpBackend + TabControlAPI. Full capabilities."""

    name = "cdp"
    JS_RENDER = True
    CAPABILITIES = {k: True for k in CAPABILITY_KEYS}

    def __init__(self, *, port: int = 9377, chrome: Optional[str] = None,
                 clock: Optional[Callable[[], float]] = None, allow_side_effects: bool = False) -> None:
        super().__init__(clock=clock or _wall_clock(), allow_side_effects=allow_side_effects)
        self._port = port
        self._chrome = chrome

    def _make_backend(self) -> BackendPort:
        # lazy: launches a real Chrome; start_session() catches any failure and degrades to unsupported.
        return CdpBackend(port=self._port, chrome=self._chrome)

    def capture_screenshot(self, *, tab_id: Optional[str] = None) -> dict[str, Any]:
        """Capture a REAL screenshot by reusing the harness's already-connected CDP transport (no CDP re-impl);
        the base64 image bytes are hashed into a digest — the image itself is never stored (no raw bodies)."""
        g = self._require("screenshot", "capture_screenshot")
        if g:
            return g
        cdp = getattr(self._backend, "_cdp", None)
        if cdp is None:
            return super().capture_screenshot(tab_id=tab_id)      # fall back to the cached page-bundle flag
        try:
            data = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data")
        except Exception as exc:  # noqa: BLE001 — never raise; record the reason
            return self._unsupported("capture_screenshot", f"live CDP screenshot failed: {exc}")
        if not data:
            return self._unsupported("capture_screenshot", "CDP returned no screenshot data")
        digest = _sha256(data)
        tid = tab_id or self._active_tab()
        rec = self._emit("capture_screenshot", {"tab_id": tid}, verifier_result="captured", artifact_refs=[digest])
        return {"supported": True, "backend": self.name, "screenshot_hash": digest, "receipt": rec,
                "candidate": True, "serves_truth": False}


__all__ = ["CdpAdapter"]
