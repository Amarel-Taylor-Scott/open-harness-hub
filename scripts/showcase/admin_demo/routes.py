"""HTTP route helpers for the Baltor admin demo."""
from __future__ import annotations

import json

from scripts.showcase.admin_demo.analysis import analyze_admin_context
from scripts.showcase.admin_demo.exports import build_export
from scripts.showcase.admin_demo.readiness import admin_demo_readiness
from scripts.showcase.admin_demo.runs import (
    MAX_ADMIN_DEMO_BYTES,
    admin_run_payload,
    start_admin_demo_run,
)
from scripts.showcase.admin_demo.source_sync import source_statuses


def handle_admin_demo_get(handler, parsed) -> bool:
    """Serve admin-demo API routes. Returns True when the path was handled."""
    if parsed.path == "/api/admin-demo/readiness":
        handler._send(200, json.dumps(admin_demo_readiness()).encode("utf-8"), "application/json")
        return True

    if parsed.path.startswith("/api/admin-demo/runs/") and "/exports/" in parsed.path:
        parts = parsed.path.strip("/").split("/")
        if len(parts) != 6:
            handler._send(404, b'{"error":"export not found"}', "application/json")
            return True
        run_id, kind = parts[3], parts[5]
        export = build_export(run_id, kind)
        if export is None:
            handler._send(404, b'{"error":"export not ready"}', "application/json")
            return True
        body, ctype, filename = export
        handler.send_response(200)
        handler.send_header("Content-Type", ctype)
        handler.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        handler.send_header("Content-Length", str(len(body)))
        handler.send_header("Cache-Control", "no-store, must-revalidate")
        handler.end_headers()
        handler.wfile.write(body)
        return True

    if parsed.path.startswith("/api/admin-demo/runs/"):
        run_id = parsed.path.rsplit("/", 1)[-1]
        payload = admin_run_payload(run_id)
        if payload is None:
            handler._send(404, b'{"error":"run not found"}', "application/json")
            return True
        handler._send(200, json.dumps(payload).encode("utf-8"), "application/json")
        return True

    return False


def handle_admin_demo_post(handler, parsed) -> bool:
    """Serve admin-demo mutation routes. Returns True when the path was handled."""
    if parsed.path not in ("/api/admin-demo/analyze", "/api/admin-demo/runs"):
        return False
    if not handler._authed(parsed):
        handler._send(401, b'{"error":"token required"}', "application/json")
        return True
    try:
        length = int(handler.headers.get("Content-Length") or "0")
    except ValueError:
        handler._send(400, b'{"error":"invalid content length"}', "application/json")
        return True
    if length <= 0:
        handler._send(400, b'{"error":"request body required"}', "application/json")
        return True
    if length > MAX_ADMIN_DEMO_BYTES:
        handler._send(413, b'{"error":"context is too large for the local demo"}', "application/json")
        return True
    try:
        payload = json.loads(handler.rfile.read(length).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        handler._send(400, b'{"error":"valid JSON required"}', "application/json")
        return True

    text = str(payload.get("text") or "")
    filename = str(payload.get("filename") or "")
    raw_sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    sources = [source for source in raw_sources if isinstance(source, dict)][:40]

    if parsed.path == "/api/admin-demo/runs":
        result = start_admin_demo_run(text, filename, sources)
        handler._send(202, json.dumps(result).encode("utf-8"), "application/json")
        return True

    result = analyze_admin_context(text, filename)
    result["sources"] = source_statuses(sources, text)
    code = 400 if "error" in result else 200
    handler._send(code, json.dumps(result).encode("utf-8"), "application/json")
    return True


__all__ = ["handle_admin_demo_get", "handle_admin_demo_post"]
