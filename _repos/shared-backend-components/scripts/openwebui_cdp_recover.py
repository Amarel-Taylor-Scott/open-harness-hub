#!/usr/bin/env python3
"""Recover and verify the Open WebUI CDP browser session.

The recovery keeps cookies, Cloudflare clearance, and localStorage inside the
browser profile. It captures screenshots and redacted page diagnostics, but it
never exports token values, cookie values, or clearance values.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import base64
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import OPENWEBUI_DEFAULT_BASE_URL, OPENWEBUI_DEFAULT_MODEL, REPO_ROOT  # noqa: E402
from scripts.openwebui_cdp_client import (  # noqa: E402
    CDPClient,
    cdp_chat,
    find_openwebui_target,
    probe_cdp_state,
)

DEFAULT_OUT_DIR = _resource("generated") / "openwebui_cdp_recovery"


def _now_slug() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_screenshot(client: CDPClient, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    result = client.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True}, timeout=30)
    data = result.get("data")
    if isinstance(data, str) and data:
        path.write_bytes(base64.b64decode(data))


def _redacted_page_state(client: CDPClient) -> dict[str, Any]:
    expression = """
(() => {
  const cookieNames = document.cookie
    .split(";")
    .map(part => part.trim().split("=")[0])
    .filter(Boolean);
  const bodyText = (document.body ? document.body.innerText : "").slice(0, 1200);
  const clickable = Array.from(document.querySelectorAll("button,a,input,[role=button]"))
    .slice(0, 40)
    .map((el) => ({
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || el.value || el.getAttribute("aria-label") || "").trim().slice(0, 120),
      type: el.getAttribute("type") || "",
      href: el.getAttribute("href") || "",
      visible: Boolean(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
    }));
  return {
    href: location.href,
    title: document.title,
    ready_state: document.readyState,
    token_present: Boolean(localStorage.getItem("token")),
    cookie_names: cookieNames,
    has_cf_clearance_cookie: cookieNames.includes("cf_clearance"),
    body_text_sample: bodyText,
    clickable
  };
})()
"""
    value = client.evaluate(expression, timeout=30)
    return value if isinstance(value, dict) else {"unexpected": value}


def _navigate(client: CDPClient, url: str, *, wait_seconds: float) -> None:
    client.call("Page.navigate", {"url": url}, timeout=30)
    time.sleep(wait_seconds)


def _reload(client: CDPClient, *, wait_seconds: float) -> None:
    client.call("Page.reload", {"ignoreCache": True}, timeout=30)
    time.sleep(wait_seconds)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def recover(
    *,
    base_url: str,
    cdp_url: str,
    model: str,
    out_dir: Path,
    wait_seconds: float,
    challenge_wait_seconds: float,
    smoke: bool,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = find_openwebui_target(cdp_url, base_url)
    ws_url = str(target["webSocketDebuggerUrl"])
    client = CDPClient(ws_url)
    steps: list[dict[str, Any]] = []
    try:
        client.call("Runtime.enable")
        client.call("Page.enable")
        client.call("Network.enable")

        steps.append({"step": "initial_probe", "probe": probe_cdp_state(base_url=base_url, cdp_url=cdp_url)})
        _write_screenshot(client, out_dir / "01-initial.png")
        _write_json(out_dir / "01-page-state.json", _redacted_page_state(client))

        client.call("Network.clearBrowserCache", {}, timeout=30)
        _navigate(client, base_url.rstrip("/") + "/", wait_seconds=wait_seconds)
        _reload(client, wait_seconds=challenge_wait_seconds)
        _write_screenshot(client, out_dir / "02-after-root-reload.png")
        _write_json(out_dir / "02-page-state.json", _redacted_page_state(client))
        steps.append({"step": "after_root_reload", "probe": probe_cdp_state(base_url=base_url, cdp_url=cdp_url)})

        for index, endpoint in enumerate(("/api/config", "/api/models"), start=3):
            _navigate(client, base_url.rstrip("/") + endpoint, wait_seconds=challenge_wait_seconds)
            _write_screenshot(client, out_dir / f"{index:02d}-{endpoint.strip('/').replace('/', '-')}.png")
            _write_json(out_dir / f"{index:02d}-{endpoint.strip('/').replace('/', '-')}-page-state.json", _redacted_page_state(client))
            steps.append({"step": f"after_visit_{endpoint}", "probe": probe_cdp_state(base_url=base_url, cdp_url=cdp_url)})

        _navigate(client, base_url.rstrip("/") + "/", wait_seconds=wait_seconds)
        _reload(client, wait_seconds=wait_seconds)
        _write_screenshot(client, out_dir / "05-final-root.png")
        _write_json(out_dir / "05-page-state.json", _redacted_page_state(client))
        final_probe = probe_cdp_state(base_url=base_url, cdp_url=cdp_url)
        steps.append({"step": "final_probe", "probe": final_probe})
    finally:
        client.close()

    smoke_result: dict[str, Any] = {}
    if smoke:
        try:
            normalized = cdp_chat(
                "Print exactly: Open WebUI Gemma recovery OK",
                system="Return exactly what the user asks for. No prose.",
                model=model,
                base_url=base_url,
                cdp_url=cdp_url,
                max_tokens=64,
                timeout=120,
            )
            smoke_result = {
                "ok": True,
                "assistant_content": normalized.get("assistant_content") or "",
                "usage": normalized.get("usage") or {},
                "http_status": normalized.get("http_status"),
            }
        except Exception as exc:  # noqa: BLE001
            smoke_result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    result = {
        "record_type": "openwebui_cdp_recovery_receipt",
        "base_url": base_url,
        "cdp_url": cdp_url,
        "model": model,
        "out_dir": str(out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir),
        "steps": steps,
        "smoke": smoke_result,
        "exports_browser_token": False,
        "exports_cookies": False,
        "exports_clearance": False,
        "candidate": True,
        "serves_truth": False,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    _write_json(out_dir / "recovery-receipt.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=OPENWEBUI_DEFAULT_BASE_URL)
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--model", default=OPENWEBUI_DEFAULT_MODEL)
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--wait-seconds", type=float, default=4.0)
    parser.add_argument("--challenge-wait-seconds", type=float, default=14.0)
    parser.add_argument("--no-smoke", action="store_true")
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir) if args.out_dir else DEFAULT_OUT_DIR / _now_slug()
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)
    try:
        result = recover(
            base_url=args.base_url,
            cdp_url=args.cdp_url,
            model=args.model,
            out_dir=out_dir,
            wait_seconds=args.wait_seconds,
            challenge_wait_seconds=args.challenge_wait_seconds,
            smoke=not args.no_smoke,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
