#!/usr/bin/env python3
"""Local object-factory workers.

These workers are intentionally stdlib-only. They provide a deterministic
baseline for page-to-Markdown conversion, candidate extraction, sensitive-data
screening, and schema-polish/verification before the hosted SaaS has queues,
object storage, or model endpoints wired in.

CLI:
    python3 -m scripts.factory.object_factory_workers --self-test
    python3 -m scripts.factory.object_factory_workers page-to-markdown --input page.html
    python3 -m scripts.factory.object_factory_workers extract --input page.md
    python3 -m scripts.factory.object_factory_workers screen --input candidates.json
    python3 -m scripts.factory.object_factory_workers polish --input candidates.json
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])


class _MarkdownHTMLParser(HTMLParser):
    """Small HTML-to-Markdown converter for source pages.

    It is not a full browser renderer. The point is to preserve useful source
    structure cheaply: headings, paragraphs, bullets, links, and table cells.
    Container workers can replace this for JS-heavy pages and PDFs.
    """

    BLOCK_TAGS = {"p", "div", "section", "article", "tr", "table", "blockquote"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []
        self._href_stack: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        attr = {k.lower(): v for k, v in attrs if v is not None}
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            self._emit("\n" + ("#" * level) + " ")
        elif tag in {"p", "div", "section", "article", "tr", "table", "blockquote"}:
            self._emit("\n")
        elif tag in {"li"}:
            self._emit("\n- ")
        elif tag == "br":
            self._emit("\n")
        elif tag == "a":
            href = attr.get("href", "")
            self._href_stack.append(href)
            if href:
                self.links.append(href)
        elif tag in {"th", "td"}:
            self._emit(" | ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "a" and self._href_stack:
            href = self._href_stack.pop()
            if href:
                self._emit(f" ({href})")
        elif tag in self.BLOCK_TAGS or tag in {"li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._emit("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = re.sub(r"\s+", " ", html.unescape(data)).strip()
        if text:
            self._emit(text + " ")

    def _emit(self, text: str) -> None:
        self.parts.append(text)

    def markdown(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip() + "\n"


@dataclass
class SourceSpan:
    id: str
    heading: str
    start_offset: int
    end_offset: int


SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[REDACTED_EMAIL]"),
    ("us_ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    ("phone", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[REDACTED_PRIVATE_KEY]"),
    ("api_key", re.compile(r"\b(?:sk|pk|api|token|secret)(?:[-_][A-Za-z0-9]+)*[-_][A-Za-z0-9]{12,}\b", re.I), "[REDACTED_SECRET]"),
]


def _read_pointer(pointer: str | None, fallback_text: str | None = None) -> str:
    if fallback_text is not None:
        return fallback_text
    if not pointer:
        return ""
    if pointer.startswith("file://"):
        pointer = pointer[7:]
    if pointer.startswith(("s3://", "gs://", "r2://", "http://", "https://")):
        raise ValueError(f"local worker cannot read remote pointer: {pointer}")
    return Path(pointer).read_text(encoding="utf-8", errors="replace")


def _write_optional(text: str, output_path: str | None) -> str:
    if not output_path:
        return ""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


def _source_spans(markdown: str) -> list[dict[str, Any]]:
    spans: list[SourceSpan] = []
    headings: list[tuple[str, int]] = []
    for match in re.finditer(r"(?m)^(#{1,6})\s+(.+)$", markdown):
        headings.append((match.group(2).strip(), match.start()))
    if not headings:
        return [{"id": "span-001", "heading": "Document", "start_offset": 0, "end_offset": len(markdown)}]
    for i, (heading, start) in enumerate(headings):
        end = headings[i + 1][1] if i + 1 < len(headings) else len(markdown)
        spans.append(SourceSpan(f"span-{i + 1:03d}", heading, start, end))
    return [span.__dict__ for span in spans]


def convert_page_to_markdown(
    *,
    source_record: dict[str, Any] | None = None,
    snapshot_pointer: str | None = None,
    mime_type: str | None = None,
    conversion_policy: dict[str, Any] | None = None,
    output_path: str | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    """Convert local text/HTML into Markdown with source spans."""
    raw = _read_pointer(snapshot_pointer, text)
    mime = (mime_type or "").lower()
    warnings: list[str] = []
    if "<html" in raw[:1000].lower() or mime in {"text/html", "application/xhtml+xml"}:
        parser = _MarkdownHTMLParser()
        parser.feed(raw)
        markdown = parser.markdown()
        links = sorted(set(parser.links))
    else:
        markdown = raw.strip() + "\n"
        links = re.findall(r"https?://[^\s)>\"]+", raw)
        if mime and mime not in {"text/plain", "text/markdown", "text/x-markdown"}:
            warnings.append(f"treated unsupported mime_type as text: {mime}")
    if conversion_policy and conversion_policy.get("prepend_source_url") and source_record:
        url = source_record.get("url") or source_record.get("source_url")
        if url:
            markdown = f"Source: {url}\n\n{markdown}"
    markdown_pointer = _write_optional(markdown, output_path)
    return {
        "markdown": markdown if not output_path else "",
        "markdown_pointer": markdown_pointer,
        "source_spans": _source_spans(markdown),
        "links": sorted(set(links)),
        "warnings": warnings,
    }


def extract_normalized_objects(
    *,
    source_record: dict[str, Any] | None = None,
    source_content: dict[str, Any] | None = None,
    extraction_targets: list[str] | None = None,
    extraction_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract simple candidate objects from Markdown headings and bullets."""
    source_content = source_content or {}
    markdown = source_content.get("markdown") or _read_pointer(source_content.get("markdown_pointer"))
    spans = source_content.get("source_spans") or _source_spans(markdown)
    span_by_range = [(s["id"], s.get("start_offset", 0), s.get("end_offset", len(markdown))) for s in spans]
    targets = set(extraction_targets or ["task", "fact", "question", "checklist_item", "decision_gate"])
    candidates: list[dict[str, Any]] = []
    warnings: list[str] = []
    for match in re.finditer(r"(?m)^(?:[-*]\s+|\d+[.)]\s+)(.+)$", markdown):
        text = match.group(1).strip()
        if len(text) < 12:
            continue
        object_type = "question" if text.endswith("?") else "checklist_item"
        if any(word in text.lower() for word in ("must", "required", "shall", "approve", "reject", "if ")):
            object_type = "decision_gate"
        if object_type not in targets and "checklist_item" in targets:
            object_type = "checklist_item"
        evidence_span_ids = [sid for sid, start, end in span_by_range if start <= match.start() <= end] or ["span-001"]
        candidates.append({
            "object_type": object_type,
            "text": text,
            "source_record_id": (source_record or {}).get("id", ""),
            "evidence_span_ids": evidence_span_ids,
            "confidence": 0.72,
        })
    if not candidates:
        paragraph = re.sub(r"\s+", " ", markdown).strip()[:600]
        if paragraph:
            object_type = "fact" if "fact" in targets else "task"
            candidates.append({
                "object_type": object_type,
                "text": paragraph,
                "source_record_id": (source_record or {}).get("id", ""),
                "evidence_span_ids": ["span-001"],
                "confidence": 0.45,
            })
            warnings.append("no bullets found; emitted one low-confidence summary candidate")
    return {"normalized_objects": candidates, "evidence_spans": spans, "extraction_warnings": warnings}


def screen_sensitive_data(
    *,
    source_record: dict[str, Any] | None = None,
    markdown_pointer: str | None = None,
    candidate_objects: list[dict[str, Any]] | None = None,
    tenant_policy: dict[str, Any] | None = None,
    publication_policy: dict[str, Any] | None = None,
    output_path: str | None = None,
    markdown: str | None = None,
) -> dict[str, Any]:
    """Redact sensitive spans from Markdown and candidate object text."""
    raw_markdown = _read_pointer(markdown_pointer, markdown) if (markdown_pointer or markdown is not None) else ""
    findings: list[dict[str, Any]] = []

    def redact_text(text: str, field: str) -> str:
        redacted = text
        for kind, pattern, repl in SENSITIVE_PATTERNS:
            for match in list(pattern.finditer(redacted)):
                findings.append({"kind": kind, "field": field, "start": match.start(), "end": match.end()})
            redacted = pattern.sub(repl, redacted)
        return redacted

    redacted_markdown = redact_text(raw_markdown, "markdown") if raw_markdown else ""
    redacted_objects: list[dict[str, Any]] = []
    for obj in candidate_objects or []:
        clone = dict(obj)
        if isinstance(clone.get("text"), str):
            clone["text"] = redact_text(clone["text"], "candidate.text")
        redacted_objects.append(clone)

    redacted_markdown_pointer = _write_optional(redacted_markdown, output_path) if redacted_markdown else ""
    has_secrets = any(f["kind"] in {"private_key", "api_key"} for f in findings)
    allowed_external = not has_secrets
    if tenant_policy and tenant_policy.get("local_only"):
        allowed_external = False
    allowed_publication = not findings or not (publication_policy or {}).get("public_catalog", False)
    review_tickets = []
    if findings:
        review_tickets.append({
            "reason": "sensitive_data_detected",
            "finding_count": len(findings),
            "requires_review": True,
        })
    return {
        "allowed_for_external_model": allowed_external,
        "allowed_for_publication": allowed_publication,
        "redacted_markdown_pointer": redacted_markdown_pointer,
        "redacted_markdown": "" if output_path else redacted_markdown,
        "redacted_objects": redacted_objects,
        "findings": findings,
        "review_tickets": review_tickets,
    }


def polish_and_verify(
    *,
    candidate_objects: list[dict[str, Any]],
    target_schema: dict[str, Any] | None = None,
    source_spans: list[dict[str, Any]] | None = None,
    model_route: dict[str, Any] | None = None,
    polish_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deterministically normalize candidates and verify basic evidence links."""
    span_ids = {s.get("id") for s in source_spans or [] if isinstance(s, dict)}
    polished: list[dict[str, Any]] = []
    review_tickets: list[dict[str, Any]] = []
    uncited = 0
    for i, obj in enumerate(candidate_objects):
        text = re.sub(r"\s+", " ", str(obj.get("text", ""))).strip()
        evidence = [sid for sid in obj.get("evidence_span_ids", []) if sid in span_ids] if span_ids else obj.get("evidence_span_ids", [])
        if not text:
            review_tickets.append({"reason": "empty_candidate_text", "candidate_index": i})
            continue
        if not evidence:
            uncited += 1
            if (polish_policy or {}).get("forbid_uncited_facts"):
                review_tickets.append({"reason": "missing_valid_evidence_span", "candidate_index": i})
                continue
        polished.append({
            **obj,
            "text": text,
            "evidence_span_ids": evidence,
            "polish_status": "deterministic_normalized",
            "verified": bool(evidence),
            "updated": time.strftime("%Y-%m-%d", time.gmtime()),
        })
    return {
        "polished_objects": polished,
        "verification_report": {
            "checked": len(candidate_objects),
            "accepted": len(polished),
            "uncited_facts": uncited,
            "target_schema_ref": (target_schema or {}).get("schema_ref", ""),
        },
        "model_route_record": model_route or {"selected_adapter": "none", "route_reason": "deterministic local baseline"},
        "review_tickets": review_tickets,
    }


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _self_test() -> int:
    html_doc = """
    <html><body><h1>Review workflow</h1>
    <p>Contact reviewer@example.com before external publication.</p>
    <ul><li>Confirm the source citation is present.</li>
    <li>If the object contains a secret token sk_test_1234567890abcdef reject it.</li></ul>
    </body></html>
    """
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "page.html"
        md = Path(tmp) / "page.md"
        src.write_text(html_doc, encoding="utf-8")
        converted = convert_page_to_markdown(snapshot_pointer=str(src), mime_type="text/html", output_path=str(md))
        extracted = extract_normalized_objects(source_content={
            "markdown_pointer": str(md),
            "source_spans": converted["source_spans"],
        }, extraction_targets=["checklist_item", "decision_gate", "question"])
        screened = screen_sensitive_data(
            markdown_pointer=str(md),
            candidate_objects=extracted["normalized_objects"],
            publication_policy={"public_catalog": True},
        )
        polished = polish_and_verify(
            candidate_objects=screened["redacted_objects"],
            source_spans=converted["source_spans"],
            polish_policy={"forbid_uncited_facts": True},
        )
    assert converted["source_spans"], "source spans should be emitted"
    assert extracted["normalized_objects"], "candidate objects should be extracted"
    assert len(screened["findings"]) >= 2, "email and secret findings should be detected"
    assert polished["polished_objects"], "polished objects should be emitted"
    _print_json({
        "ok": True,
        "converted_spans": len(converted["source_spans"]),
        "extracted_objects": len(extracted["normalized_objects"]),
        "sensitive_findings": len(screened["findings"]),
        "polished_objects": len(polished["polished_objects"]),
    })
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run local object-factory workers.")
    p.add_argument("--self-test", action="store_true", help="Run an end-to-end local worker self-test")
    sub = p.add_subparsers(dest="cmd")

    page = sub.add_parser("page-to-markdown")
    page.add_argument("--input", required=True)
    page.add_argument("--mime-type", default="")
    page.add_argument("--output")

    extract = sub.add_parser("extract")
    extract.add_argument("--input", required=True, help="Markdown file")

    screen = sub.add_parser("screen")
    screen.add_argument("--input", required=True, help="JSON list of candidate objects")
    screen.add_argument("--markdown")
    screen.add_argument("--output-markdown")

    polish = sub.add_parser("polish")
    polish.add_argument("--input", required=True, help="JSON list of candidate objects")
    polish.add_argument("--spans", help="JSON list of source spans")

    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cmd == "page-to-markdown":
        _print_json(convert_page_to_markdown(snapshot_pointer=args.input, mime_type=args.mime_type, output_path=args.output))
        return 0
    if args.cmd == "extract":
        markdown = Path(args.input).read_text(encoding="utf-8")
        _print_json(extract_normalized_objects(source_content={"markdown": markdown}))
        return 0
    if args.cmd == "screen":
        _print_json(screen_sensitive_data(
            markdown_pointer=args.markdown,
            candidate_objects=_load_json(args.input),
            publication_policy={"public_catalog": True},
            output_path=args.output_markdown,
        ))
        return 0
    if args.cmd == "polish":
        spans = _load_json(args.spans) if args.spans else []
        _print_json(polish_and_verify(candidate_objects=_load_json(args.input), source_spans=spans))
        return 0
    p.error("--self-test or a subcommand is required")
    return 2


if __name__ == "__main__":
    sys.exit(_main())
