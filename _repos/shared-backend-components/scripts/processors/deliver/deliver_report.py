#!/usr/bin/env python3
"""Backs `processor/deliver-report` (process_kind ``report.pdf``).

Render the validated result into a shareable report — Markdown natively, PDF
via an injected renderer — with a CITATIONS section built from the result's
source handles. The RENDER is deterministic (same result → byte-identical
Markdown); DELIVERY goes through an injected ``sink(filename, content) ->
uri``. Without a sink the call returns an honest ``delivered: False``
preview carrying the full rendered document (preview ≠ faked URI); PDF
without a renderer is refused, never approximated.

Contract: render deterministic; side_effects=external_call (sink);
on_error=raise. Inputs result, format → output document_uri.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/deliver/deliver_report.py
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

FORMAT_MARKDOWN = "markdown"
FORMAT_PDF = "pdf"
SUPPORTED_FORMATS = (FORMAT_MARKDOWN, FORMAT_PDF)

HASH_ALGORITHM = "sha256"
REPORT_ID_PREFIX = "rpt:"
REPORT_ID_HEX_LEN = 16

#: Section headers (single definition; tests read them).
H_ANSWER = "## Answer"
H_DETAILS = "## Details"
H_CITATIONS = "## Citations"


def render_markdown(result: dict[str, Any]) -> str:
    """Deterministic Markdown: title, answer, details, citations (always present)."""
    if not isinstance(result, dict):
        raise TypeError(f"result must be a dict, got {type(result).__name__}")
    title = str(result.get("title", "Result report"))
    lines = [f"# {title}", ""]
    if "answer" in result:
        lines += [H_ANSWER, str(result["answer"]), ""]
    details = result.get("details")
    if isinstance(details, dict) and details:
        lines += [H_DETAILS]
        lines += [f"- **{k}**: {details[k]}" for k in sorted(details)]
        lines += [""]
    citations = result.get("citations") or []
    lines += [H_CITATIONS]
    lines += [f"- {c}" for c in citations] if citations else ["- (none provided)"]
    return "\n".join(lines) + "\n"


def run(*, result: dict[str, Any], format: str = FORMAT_MARKDOWN,  # noqa: A002 — manifest input name
        sink: Callable[[str, bytes], str] | None = None,
        pdf_renderer: Callable[[str], bytes] | None = None) -> dict[str, Any]:
    """Render the report and deliver it via ``sink`` (or preview honestly)."""
    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"format must be one of {SUPPORTED_FORMATS}, got {format!r}")
    md = render_markdown(result)
    rid = REPORT_ID_PREFIX + hashlib.new(HASH_ALGORITHM, md.encode("utf-8")).hexdigest()[:REPORT_ID_HEX_LEN]
    if format == FORMAT_PDF:
        if pdf_renderer is None:
            raise RuntimeError("pdf output needs an injected pdf_renderer(markdown) -> bytes; "
                               "a PDF is never approximated from Markdown silently")
        payload = pdf_renderer(md)
        filename = f"{rid.replace(':', '-')}.pdf"
    else:
        payload = md.encode("utf-8")
        filename = f"{rid.replace(':', '-')}.md"
    if sink is None:
        return {"document_uri": {"uri": None, "delivered": False, "report_id": rid,
                                 "format": format, "rendered_markdown": md,
                                 "note": "no sink injected — honest preview, not a fake URI"}}
    uri = str(sink(filename, payload))
    return {"document_uri": {"uri": uri, "delivered": True, "report_id": rid,
                             "format": format, "rendered_markdown": md}}


def _selftest() -> None:
    result = {"title": "Reg E timing", "answer": "10 business days",
              "details": {"rule": "12 CFR 1005.11", "scope": "consumer EFT"},
              "citations": ["12 CFR 1005.11", "CFPB FAQ (held out: '30 days')"]}
    # Preview lane: full render, honest non-delivery.
    pv = run(result=result)["document_uri"]
    assert pv["delivered"] is False and pv["uri"] is None
    assert pv["rendered_markdown"].startswith("# Reg E timing")
    assert H_CITATIONS in pv["rendered_markdown"] and "12 CFR 1005.11" in pv["rendered_markdown"]
    # Determinism: byte-identical render + stable report id.
    assert run(result=result)["document_uri"]["rendered_markdown"] == pv["rendered_markdown"]
    assert run(result=result)["document_uri"]["report_id"] == pv["report_id"]
    # Sink lane: delivered with the sink's URI.
    store: dict[str, bytes] = {}
    def sink(filename: str, content: bytes) -> str:
        store[filename] = content
        return f"file:///reports/{filename}"
    dv = run(result=result, sink=sink)["document_uri"]
    assert dv["delivered"] is True and dv["uri"].endswith(".md")
    assert store[dv["uri"].split("/")[-1]] == pv["rendered_markdown"].encode()
    # Citations section always exists (even empty — honest).
    bare = run(result={"answer": "x"})["document_uri"]["rendered_markdown"]
    assert "- (none provided)" in bare
    # PDF: refused without a renderer; rendered via injected one.
    raised = False
    try:
        run(result=result, format=FORMAT_PDF, sink=sink)
    except RuntimeError:
        raised = True
    assert raised
    pdf = run(result=result, format=FORMAT_PDF, sink=sink,
              pdf_renderer=lambda md: b"%PDF-1.4 " + md.encode())["document_uri"]
    assert pdf["uri"].endswith(".pdf") and store[pdf["uri"].split("/")[-1]].startswith(b"%PDF")
    # Unknown format raises.
    raised = False
    try:
        run(result=result, format="docx")
    except ValueError:
        raised = True
    assert raised
    print("PASS — deliver_report: deterministic Markdown render (answer/details/citations "
          "always sectioned), content-addressed report ids, honest no-sink preview, "
          "PDF refused without a real renderer verified")


if __name__ == "__main__":
    _selftest()
