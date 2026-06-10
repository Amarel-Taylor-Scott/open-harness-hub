"""Optional document-intelligence adapter workers.

These workers register the full candidate tool surface now while keeping the
default local runtime lightweight. Each adapter can be enabled/disabled by
payload or environment and reports missing dependencies/configuration explicitly.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from scripts._config import CONTEXT_TOOL_ADAPTER_RUNTIME_SETTINGS, CONTEXT_TOOL_ADAPTER_SERVICE_ENDPOINTS
from scripts.context_workers.common import WORD_RE, chunk_text, compact, stable_hash
from scripts.context_workers.registry import TaskContext, TaskResult, registry
from scripts.db.runtime_settings import runtime_setting

LOCAL_DEFAULT_ADAPTERS = {
    "ftfy",
    "lingua",
    "rapidfuzz",
    "datasketch",
    "sklearn",
    "networkx",
    "rdflib",
    "pymupdf",
    "pdfplumber",
    "context-adapters-catalog",
    "node-research-catalog",
    "node-research-plan",
}

CONTEXT_TOOL_ADAPTER_RUNTIME_NAMESPACE = "baltor.context_tool_adapter.runtime"
CONTEXT_TOOL_ADAPTER_ENDPOINT_NAMESPACE = "baltor.context_tool_adapter.service_endpoint"


def _adapter_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_TOOL_ADAPTER_RUNTIME_NAMESPACE,
        definitions=CONTEXT_TOOL_ADAPTER_RUNTIME_SETTINGS,
        name=name,
    )


def _service_endpoint_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_TOOL_ADAPTER_ENDPOINT_NAMESPACE,
        definitions={
            key: {
                "env": value["env"],
                "default": "",
                "value_type": "uri",
                "setting_kind": "storage_backend",
                "description": value["description"],
            }
            for key, value in CONTEXT_TOOL_ADAPTER_SERVICE_ENDPOINTS.items()
        },
        name=name,
    )


def _adapter_env(name: str) -> str:
    return str(CONTEXT_TOOL_ADAPTER_RUNTIME_SETTINGS[name]["env"])


def _service_endpoint_env(name: str) -> str:
    return str(CONTEXT_TOOL_ADAPTER_SERVICE_ENDPOINTS[name]["env"])


def _service_endpoint_value_by_env(env_name: str) -> str:
    for endpoint_name, spec in CONTEXT_TOOL_ADAPTER_SERVICE_ENDPOINTS.items():
        if str(spec["env"]) == env_name:
            return _service_endpoint_setting(endpoint_name)
    return os.environ.get(env_name, "")


def _has_module(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _enabled(adapter: str, payload: dict[str, Any]) -> bool:
    enabled = payload.get("enabled_adapters")
    disabled = payload.get("disabled_adapters")
    if isinstance(disabled, list) and adapter in {str(item) for item in disabled}:
        return False
    if isinstance(enabled, list):
        return adapter in {str(item) for item in enabled}
    env_value = _adapter_setting("enabled_adapters").strip()
    if not env_value or env_value.lower() == "local":
        return adapter in LOCAL_DEFAULT_ADAPTERS
    if env_value.lower() == "all":
        return True
    return adapter in {part.strip() for part in env_value.split(",") if part.strip()}


def _disabled_result(adapter: str) -> TaskResult:
    return TaskResult.success(
        {"adapter": adapter, "adapter_status": "disabled", "records": []},
        warnings=[f"{adapter} disabled by configuration"],
    )


def _missing_result(adapter: str, requirement: str) -> TaskResult:
    return TaskResult.success(
        {
            "adapter": adapter,
            "adapter_status": "missing_dependency",
            "requirement": requirement,
            "records": [],
        },
        warnings=[f"{adapter} requires {requirement}"],
    )


def _not_configured_result(adapter: str, env_var: str) -> TaskResult:
    return TaskResult.success(
        {
            "adapter": adapter,
            "adapter_status": "not_configured",
            "required_env": env_var,
            "records": [],
        },
        warnings=[f"{adapter} requires {env_var}"],
    )


def _authorization_required_result(adapter: str) -> TaskResult:
    auth_env = _adapter_env("osint_authorized")
    return TaskResult.success(
        {
            "adapter": adapter,
            "adapter_status": "authorization_required",
            "records": [],
            "requirement": f"Set payload.authorized=true or {auth_env}=true for authorized security research.",
        },
        warnings=[f"{adapter} requires explicit authorized-use confirmation"],
    )


def _text_from_payload(payload: dict[str, Any]) -> str:
    if payload.get("text"):
        return str(payload.get("text") or "")
    chunks = payload.get("chunks")
    if isinstance(chunks, list):
        return "\n\n".join(str(chunk.get("text") or "") for chunk in chunks if isinstance(chunk, dict))
    return ""


def _source_path(payload: dict[str, Any]) -> Path | None:
    raw = payload.get("path") or payload.get("file_path") or payload.get("source_path")
    if raw:
        path = Path(str(raw)).expanduser()
        if path.exists() and path.is_file():
            return path
    name = payload.get("filename") or "payload.bin"
    data = payload.get("bytes")
    if isinstance(data, str):
        tmp = Path(tempfile.mkdtemp(prefix="context-adapter-")) / str(name)
        tmp.write_bytes(data.encode("utf-8"))
        return tmp
    return None


def _http_json(url: str, payload: dict[str, Any], timeout_s: int = 30) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as response:  # noqa: S310 - operator-configured local/service URL
        data = response.read().decode("utf-8", errors="replace")
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {"raw_response": data}


def _adapter_record(adapter: str, *, status: str = "ready", **extra: Any) -> dict[str, Any]:
    return {"adapter": adapter, "adapter_status": status, **extra}


@registry.register(
    "document.parse.docling",
    lane="normalize",
    description="Parse documents with Docling into structured text/Markdown/JSON for downstream RAG and graph workers.",
    emits=("parsed_document", "document_blocks", "document_assets"),
    capabilities=("document_parsing", "layout_analysis", "table_extraction", "rag_preparation"),
    task_types=("document.parse", "document.parse.docling"),
    image="baltor-worker-cpu",
    output_contract="parsed_document.v1",
)
def parse_docling(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "docling"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("docling"):
        return _missing_result(adapter, "docling")
    path = _source_path(payload)
    if not path:
        return TaskResult.failure("path or file payload required")
    try:
        from docling.document_converter import DocumentConverter  # type: ignore

        converted = DocumentConverter().convert(str(path))
        document = converted.document
        markdown = document.export_to_markdown() if hasattr(document, "export_to_markdown") else ""
        text = document.export_to_text() if hasattr(document, "export_to_text") else markdown
        document_json = document.export_to_dict() if hasattr(document, "export_to_dict") else {}
        blocks = [
            {
                "id": stable_hash("block", block, index),
                "type": "text",
                "text": block,
                "char_count": len(block),
            }
            for index, block in enumerate(re.split(r"\n{2,}", text), 1)
            if block.strip()
        ]
        return TaskResult.success({
            "parsed_document": {
                "adapter": adapter,
                "adapter_status": "ready",
                "path": str(path),
                "text": text,
                "markdown": markdown,
                "parser_json": document_json,
            },
            "document_blocks": blocks,
            "document_assets": [],
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"docling_parse_failed: {exc!r}")


@registry.register(
    "document.parse.tika",
    lane="normalize",
    description="Fallback parser using Apache Tika/tika-python for broad file type text and metadata extraction.",
    emits=("parsed_document", "document_metadata"),
    capabilities=("document_parsing", "mime_detection", "metadata_extraction", "fallback_parser"),
    task_types=("document.parse", "document.parse.tika"),
    image="baltor-worker-cpu",
    output_contract="parsed_document.v1",
)
def parse_tika(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "tika"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("tika"):
        return _missing_result(adapter, "tika")
    path = _source_path(payload)
    if not path:
        return TaskResult.failure("path or file payload required")
    try:
        from tika import parser  # type: ignore

        parsed = parser.from_file(str(path))
        text = str(parsed.get("content") or "").strip()
        return TaskResult.success({
            "parsed_document": _adapter_record(adapter, path=str(path), text=text),
            "document_metadata": parsed.get("metadata") or {},
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"tika_parse_failed: {exc!r}")


@registry.register(
    "document.parse.markitdown",
    lane="normalize",
    description="Convert common files to LLM-friendly Markdown with Microsoft MarkItDown.",
    emits=("parsed_document",),
    capabilities=("markdown_conversion", "document_parsing", "llm_preparation"),
    task_types=("document.parse", "document.parse.markitdown"),
    image="baltor-worker-cpu",
    output_contract="parsed_document.v1",
)
def parse_markitdown(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "markitdown"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("markitdown"):
        return _missing_result(adapter, "markitdown")
    path = _source_path(payload)
    if not path:
        return TaskResult.failure("path or file payload required")
    try:
        from markitdown import MarkItDown  # type: ignore

        result = MarkItDown().convert(str(path))
        markdown = str(getattr(result, "text_content", "") or "")
        return TaskResult.success({"parsed_document": _adapter_record(adapter, path=str(path), markdown=markdown, text=markdown)})
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"markitdown_parse_failed: {exc!r}")


@registry.register(
    "document.parse.unstructured",
    lane="normalize",
    description="Partition documents with Unstructured into typed elements for LLM/RAG preprocessing.",
    emits=("parsed_document", "document_blocks", "document_assets"),
    capabilities=("document_partitioning", "layout_elements", "pdf_partition", "office_partition", "llm_preparation"),
    task_types=("document.parse", "document.parse.unstructured"),
    image="baltor-worker-cpu",
    output_contract="parsed_document.v1",
)
def parse_unstructured(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "unstructured"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("unstructured"):
        return _missing_result(adapter, "unstructured[all-docs]")
    path = _source_path(payload)
    if not path:
        return TaskResult.failure("path or file payload required")
    try:
        from unstructured.partition.auto import partition  # type: ignore

        elements = partition(filename=str(path))
        blocks = []
        for index, element in enumerate(elements, 1):
            text = str(element)
            metadata = getattr(element, "metadata", None)
            blocks.append({
                "id": stable_hash("block", f"{path}:{index}:{text}", index),
                "type": getattr(element, "category", element.__class__.__name__),
                "text": text,
                "page": getattr(metadata, "page_number", None) if metadata else None,
                "metadata": metadata.to_dict() if metadata and hasattr(metadata, "to_dict") else {},
            })
        return TaskResult.success({
            "parsed_document": _adapter_record(adapter, path=str(path), text="\n\n".join(block["text"] for block in blocks)),
            "document_blocks": blocks,
            "document_assets": [],
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"unstructured_parse_failed: {exc!r}")


@registry.register(
    "document.parse.pymupdf",
    lane="normalize",
    description="Extract page text, block coordinates, metadata, and embedded image references with PyMuPDF.",
    emits=("parsed_document", "document_blocks", "document_assets"),
    capabilities=("pdf_page_extraction", "bbox_extraction", "image_extraction", "metadata_extraction"),
    task_types=("document.parse.pymupdf", "document.assets.extract"),
    image="baltor-worker-cpu",
    output_contract="pdf_blocks.v1",
)
def parse_pymupdf(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "pymupdf"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("fitz"):
        return _missing_result(adapter, "PyMuPDF")
    path = _source_path(payload)
    if not path:
        return TaskResult.failure("path or file payload required")
    try:
        import fitz  # type: ignore

        doc = fitz.open(str(path))
        blocks = []
        assets = []
        for page_index, page in enumerate(doc, 1):
            for block_index, block in enumerate(page.get_text("blocks"), 1):
                text = str(block[4] or "").strip()
                if not text:
                    continue
                blocks.append({
                    "id": stable_hash("block", f"{path}:{page_index}:{block_index}:{text}", block_index),
                    "type": "text",
                    "text": text,
                    "page": page_index,
                    "bbox": [float(block[0]), float(block[1]), float(block[2]), float(block[3])],
                })
            for image_index, image in enumerate(page.get_images(full=True), 1):
                assets.append({
                    "id": stable_hash("image", f"{path}:{page_index}:{image_index}:{image[0]}", image_index),
                    "type": "image",
                    "page": page_index,
                    "xref": image[0],
                })
        return TaskResult.success({
            "parsed_document": _adapter_record(adapter, path=str(path), page_count=doc.page_count, metadata=doc.metadata),
            "document_blocks": blocks,
            "document_assets": assets,
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"pymupdf_parse_failed: {exc!r}")


@registry.register(
    "document.parse.pdfplumber",
    lane="normalize",
    description="Extract machine-generated PDF text, tables, page dimensions, and visual-debuggable layout objects with pdfplumber.",
    emits=("parsed_document", "document_blocks", "table_records"),
    capabilities=("pdf_table_extraction", "pdf_layout_debug", "bbox_extraction"),
    task_types=("document.parse.pdfplumber", "table.extract"),
    image="baltor-worker-cpu",
    output_contract="pdfplumber_document.v1",
)
def parse_pdfplumber(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "pdfplumber"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("pdfplumber"):
        return _missing_result(adapter, "pdfplumber")
    path = _source_path(payload)
    if not path:
        return TaskResult.failure("path or file payload required")
    try:
        import pdfplumber  # type: ignore

        blocks = []
        tables = []
        with pdfplumber.open(str(path)) as pdf:
            for page_index, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                if text.strip():
                    blocks.append({
                        "id": stable_hash("page", f"{path}:{page_index}:{text[:100]}", page_index),
                        "type": "page_text",
                        "text": text,
                        "page": page_index,
                        "width": page.width,
                        "height": page.height,
                    })
                for table_index, table in enumerate(page.extract_tables() or [], 1):
                    tables.append({
                        "id": stable_hash("table", f"{path}:{page_index}:{table_index}", table_index),
                        "page": page_index,
                        "rows": table,
                    })
        return TaskResult.success({
            "parsed_document": _adapter_record(adapter, path=str(path), text="\n\n".join(block["text"] for block in blocks)),
            "document_blocks": blocks,
            "table_records": tables,
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"pdfplumber_parse_failed: {exc!r}")


def _cli_adapter_worker(adapter: str, command: list[str], output_key: str) -> Callable[[TaskContext, dict[str, Any]], TaskResult]:
    def worker(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
        if not _enabled(adapter, payload):
            return _disabled_result(adapter)
        path = _source_path(payload)
        if not path:
            return TaskResult.failure("path or file payload required")
        if not command:
            return _missing_result(adapter, f"{adapter} CLI")
        executable = command[0]
        if not any((Path(part) / executable).exists() for part in os.environ.get("PATH", "").split(os.pathsep)):
            return _missing_result(adapter, executable)
        try:
            proc = subprocess.run([*command, str(path)], capture_output=True, text=True, timeout=int(payload.get("timeout_s") or 120), check=False)
            status = "ready" if proc.returncode == 0 else "failed"
            return TaskResult.success({
                output_key: _adapter_record(
                    adapter,
                    status=status,
                    path=str(path),
                    returncode=proc.returncode,
                    stdout=proc.stdout[-20000:],
                    stderr=proc.stderr[-12000:],
                )
            }, warnings=[] if proc.returncode == 0 else [f"{adapter} CLI returned {proc.returncode}"])
        except Exception as exc:  # noqa: BLE001
            return TaskResult.failure(f"{adapter}_cli_failed: {exc!r}")

    return worker


OPENOSINT_TOOLS = {
    "email": "email",
    "username": "username",
    "breach": "breach",
    "whois": "whois",
    "ip": "ip",
    "domain": "domain",
    "dorks": "dorks",
    "paste": "paste",
    "phone": "phone",
    "shodan": "shodan",
    "virustotal": "virustotal",
    "ip2location": "ip2location",
    "censys": "censys",
    "abuseipdb": "abuseipdb",
    "github": "github",
    "dns": "dns",
}


def _osint_authorized(payload: dict[str, Any]) -> bool:
    return bool(payload.get("authorized")) or _adapter_setting("osint_authorized").lower() in {"1", "true", "yes"}


@registry.register(
    "osint.openosint.run",
    lane="research",
    description="Run an authorized OpenOSINT CLI tool and capture output for passive enrichment, verification, and security research workflows.",
    emits=("openosint_result",),
    capabilities=("osint", "passive_recon", "breach_check", "dns_intel", "domain_intel", "ip_reputation", "github_intel"),
    task_types=("osint.openosint.run", "research.osint"),
    image="baltor-worker-research",
    output_contract="openosint_result.v1",
)
def openosint_run(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "openosint"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _osint_authorized(payload):
        return _authorization_required_result(adapter)
    executable = str(payload.get("executable") or "openosint")
    path_parts = [Path(part) for part in os.environ.get("PATH", "").split(os.pathsep)]
    if not any((part / executable).exists() for part in path_parts):
        return _missing_result(adapter, "openosint")
    tool = str(payload.get("tool") or "").strip().lower()
    target = str(payload.get("target") or payload.get("query") or "").strip()
    if tool not in OPENOSINT_TOOLS:
        return TaskResult.failure(f"unsupported OpenOSINT tool: {tool or '<empty>'}", output={"supported_tools": sorted(OPENOSINT_TOOLS)})
    if not target:
        return TaskResult.failure("target required")
    if tool in {"email", "breach", "paste"} and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", target):
        return TaskResult.failure("email-like target required for this OpenOSINT tool")
    if tool == "phone" and not re.match(r"^\+?[0-9().\-\s]{7,24}$", target):
        return TaskResult.failure("phone-like target required")
    timeout_s = int(payload.get("timeout_s") or 90)
    try:
        proc = subprocess.run(
            [executable, OPENOSINT_TOOLS[tool], target],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        return TaskResult.success({
            "openosint_result": _adapter_record(
                adapter,
                status="ready" if proc.returncode == 0 else "failed",
                tool=tool,
                target_hash=stable_hash("osint-target", target, 1),
                returncode=proc.returncode,
                stdout=proc.stdout[-30000:],
                stderr=proc.stderr[-12000:],
                authorized=True,
            )
        }, warnings=[] if proc.returncode == 0 else [f"openosint returned {proc.returncode}"])
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"openosint_failed: {exc!r}")


@registry.register(
    "osint.openosint.catalog",
    lane="research",
    description="Report OpenOSINT tool readiness, required authorization, optional API keys, and supported passive research modules.",
    emits=("openosint_catalog",),
    capabilities=("osint_catalog", "preflight", "authorization_gate"),
    task_types=("osint.openosint.catalog",),
    image="baltor-worker-research",
    output_contract="openosint_catalog.v1",
)
def openosint_catalog(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "openosint"
    path_parts = [Path(part) for part in os.environ.get("PATH", "").split(os.pathsep)]
    executable = str(payload.get("executable") or "openosint")
    optional_keys = [
        "HIBP_API_KEY",
        "IPINFO_TOKEN",
        "SHODAN_API_KEY",
        "VIRUSTOTAL_API_KEY",
        "IP2LOCATION_API_KEY",
        "CENSYS_API_ID",
        "CENSYS_SECRET",
        "ABUSEIPDB_API_KEY",
        "GITHUB_TOKEN",
    ]
    return TaskResult.success({
        "openosint_catalog": {
            "adapter": adapter,
            "enabled": _enabled(adapter, payload),
            "authorized": _osint_authorized(payload),
            "available": any((part / executable).exists() for part in path_parts),
            "executable": executable,
            "supported_tools": sorted(OPENOSINT_TOOLS),
            "optional_keys": {key: bool(os.environ.get(key)) for key in optional_keys},
            "policy": "authorized passive OSINT/security research only",
        }
    })


marker_cli_extract = registry.register(
    "document.parse.marker",
    lane="normalize",
    description="Adapter for Marker PDF/Office/image conversion to Markdown, JSON, chunks, HTML, and extracted images.",
    emits=("parsed_document", "document_blocks", "document_assets"),
    capabilities=("document_parsing", "ocr", "table_extraction", "image_extraction", "markdown_conversion"),
    task_types=("document.parse.marker",),
    image="baltor-worker-cpu",
    output_contract="parsed_document.v1",
)(_cli_adapter_worker("marker", ["marker_single"], "parsed_document"))

mineru_cli_extract = registry.register(
    "document.parse.mineru",
    lane="normalize",
    description="Adapter for MinerU complex PDF/Office parsing to Markdown/JSON with images, tables, formulas, and footnotes.",
    emits=("parsed_document", "document_blocks", "document_assets"),
    capabilities=("document_parsing", "ocr", "table_extraction", "formula_extraction", "image_extraction"),
    task_types=("document.parse.mineru",),
    image="baltor-worker-cpu",
    output_contract="parsed_document.v1",
)(_cli_adapter_worker("mineru", ["mineru"], "parsed_document"))

paddleocr_cli_extract = registry.register(
    "document.ocr.paddle",
    lane="normalize",
    description="Adapter for PaddleOCR/PP-Structure OCR, layout parsing, table recognition, and formula recognition.",
    emits=("ocr_document", "document_blocks", "document_assets"),
    capabilities=("ocr", "layout_analysis", "table_extraction", "formula_extraction"),
    task_types=("document.ocr", "document.ocr.paddle"),
    image="baltor-worker-ocr",
    output_contract="ocr_document.v1",
)(_cli_adapter_worker("paddleocr", ["paddleocr"], "ocr_document"))


@registry.register(
    "document.parse.grobid",
    lane="normalize",
    description="Call GROBID for scholarly PDF metadata, references, citations, and TEI XML extraction.",
    emits=("parsed_document", "citation_records"),
    capabilities=("scientific_pdf_parsing", "citation_extraction", "tei_xml", "metadata_extraction"),
    task_types=("document.parse.grobid", "citation.extract"),
    image="baltor-worker-cpu",
    output_contract="grobid_document.v1",
)
def parse_grobid(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "grobid"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    grobid_env = _adapter_env("grobid_url")
    base_url = _adapter_setting("grobid_url").rstrip("/")
    if not base_url:
        return _not_configured_result(adapter, grobid_env)
    path = _source_path(payload)
    if not path:
        return TaskResult.failure("path or file payload required")
    boundary = "----baltor-grobid-boundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="input"; filename="{path.name}"\r\n'
        "Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/processFulltextDocument",
        data=body,
        headers={"content-type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=int(payload.get("timeout_s") or 120)) as response:  # noqa: S310
            tei = response.read().decode("utf-8", errors="replace")
        return TaskResult.success({"parsed_document": _adapter_record(adapter, path=str(path), tei_xml=tei)})
    except urllib.error.URLError as exc:
        return TaskResult.failure(f"grobid_request_failed: {exc!r}")


@registry.register(
    "nlp.spacy.extract",
    lane="analyze",
    description="Run spaCy tokenization, sentence segmentation, POS/dependency signals, NER, noun chunks, and rule matcher hooks.",
    emits=("spacy_entities", "spacy_sentences", "spacy_noun_chunks", "spacy_tokens"),
    capabilities=("tokenization", "sentence_segmentation", "pos_tagging", "dependency_parsing", "ner", "entity_ruler"),
    task_types=("nlp.spacy.extract", "entity.extract"),
    image="baltor-worker-ml",
    output_contract="spacy_extract.v1",
)
def spacy_extract(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "spacy"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("spacy"):
        return _missing_result(adapter, "spacy")
    text = _text_from_payload(payload)
    if not text.strip():
        return TaskResult.failure("text required")
    try:
        import spacy  # type: ignore
        from spacy.pipeline import EntityRuler  # noqa: F401

        model = str(payload.get("spacy_model") or _adapter_setting("spacy_model"))
        try:
            nlp = spacy.load(model)
        except Exception:
            nlp = spacy.blank("en")
            nlp.add_pipe("sentencizer")
        doc = nlp(text[: int(payload.get("max_chars") or 200000)])
        entities = [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            for ent in getattr(doc, "ents", [])
        ]
        noun_chunks = []
        try:
            noun_chunks = [{"text": chunk.text, "start": chunk.start_char, "end": chunk.end_char} for chunk in doc.noun_chunks]
        except Exception:
            noun_chunks = []
        tokens = [
            {"text": token.text, "lemma": token.lemma_, "pos": token.pos_, "dep": token.dep_, "head": token.head.i}
            for token in list(doc)[: int(payload.get("max_tokens") or 5000)]
        ]
        return TaskResult.success({
            "spacy_entities": entities,
            "spacy_sentences": [{"text": sent.text, "start": sent.start_char, "end": sent.end_char} for sent in doc.sents],
            "spacy_noun_chunks": noun_chunks,
            "spacy_tokens": tokens,
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"spacy_extract_failed: {exc!r}")


@registry.register(
    "nlp.textacy.extract",
    lane="analyze",
    description="Run textacy extractors for acronyms/definitions, quotations, noun chunks, and subject-verb-object triples.",
    emits=("textacy_triples", "textacy_terms", "textacy_quotations", "textacy_definitions"),
    capabilities=("svo_triples", "definition_extraction", "quotation_extraction", "noun_phrase_extraction"),
    task_types=("nlp.textacy.extract", "relationship.extract"),
    image="baltor-worker-ml",
    output_contract="textacy_extract.v1",
)
def textacy_extract(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "textacy"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("textacy") or not _has_module("spacy"):
        return _missing_result(adapter, "textacy spacy")
    text = _text_from_payload(payload)
    if not text.strip():
        return TaskResult.failure("text required")
    try:
        import spacy  # type: ignore
        import textacy.extract  # type: ignore

        try:
            nlp = spacy.load(str(payload.get("spacy_model") or _adapter_setting("spacy_model")))
        except Exception:
            nlp = spacy.blank("en")
            nlp.add_pipe("sentencizer")
        doc = nlp(text[: int(payload.get("max_chars") or 200000)])
        triples = []
        try:
            triples = [
                {"subject": compact(str(s)), "verb": compact(str(v)), "object": compact(str(o))}
                for s, v, o in textacy.extract.subject_verb_object_triples(doc)
            ][:500]
        except Exception:
            triples = []
        terms = [{"text": compact(str(term))} for term in textacy.extract.terms(doc, ngs=(1, 2, 3), ents=True, ncs=True)][:1000]
        return TaskResult.success({
            "textacy_triples": triples,
            "textacy_terms": terms,
            "textacy_quotations": [],
            "textacy_definitions": [],
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"textacy_extract_failed: {exc!r}")


@registry.register(
    "nlp.stanza.extract",
    lane="analyze",
    description="Run Stanford Stanza multilingual tokenization, lemmatization, POS/morphology, dependency parsing, and NER.",
    emits=("stanza_entities", "stanza_sentences", "stanza_dependencies"),
    capabilities=("multilingual_nlp", "dependency_parsing", "ner", "lemmatization"),
    task_types=("nlp.stanza.extract",),
    image="baltor-worker-ml",
    output_contract="stanza_extract.v1",
)
def stanza_extract(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "stanza"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("stanza"):
        return _missing_result(adapter, "stanza")
    text = _text_from_payload(payload)
    if not text.strip():
        return TaskResult.failure("text required")
    try:
        import stanza  # type: ignore

        lang = str(payload.get("language") or "en")
        processors = str(payload.get("processors") or "tokenize,pos,lemma,depparse,ner")
        nlp = stanza.Pipeline(lang=lang, processors=processors, download_method=None, verbose=False)
        doc = nlp(text[: int(payload.get("max_chars") or 100000)])
        entities = [{"text": ent.text, "type": ent.type} for ent in getattr(doc, "ents", [])]
        dependencies = []
        for sent_index, sentence in enumerate(doc.sentences, 1):
            for word in sentence.words:
                dependencies.append({"sentence": sent_index, "id": word.id, "text": word.text, "head": word.head, "deprel": word.deprel})
        return TaskResult.success({
            "stanza_entities": entities,
            "stanza_sentences": [{"text": sentence.text} for sentence in doc.sentences],
            "stanza_dependencies": dependencies[:5000],
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"stanza_extract_failed: {exc!r}")


@registry.register(
    "nlp.gliner.extract",
    lane="analyze",
    description="Run GLiNER for configurable zero-shot/custom entity detection before LLM graph enrichment.",
    emits=("gliner_entities",),
    capabilities=("zero_shot_ner", "custom_entity_detection", "cpu_entity_extraction"),
    task_types=("nlp.gliner.extract", "entity.extract.custom"),
    image="baltor-worker-ml",
    output_contract="gliner_entities.v1",
)
def gliner_extract(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "gliner"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("gliner"):
        return _missing_result(adapter, "gliner")
    text = _text_from_payload(payload)
    labels = payload.get("labels") if isinstance(payload.get("labels"), list) else ["person", "organization", "product", "location", "policy", "system"]
    if not text.strip():
        return TaskResult.failure("text required")
    try:
        from gliner import GLiNER  # type: ignore

        model_name = str(payload.get("model") or _adapter_setting("gliner_model"))
        model = GLiNER.from_pretrained(model_name)
        entities = model.predict_entities(text[: int(payload.get("max_chars") or 50000)], labels, threshold=float(payload.get("threshold") or 0.5))
        return TaskResult.success({"gliner_entities": entities})
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"gliner_extract_failed: {exc!r}")


@registry.register(
    "text.ftfy.repair",
    lane="normalize",
    description="Repair mojibake and Unicode text damage with ftfy before chunking and NLP.",
    emits=("repaired_text", "repair_report"),
    capabilities=("encoding_repair", "unicode_normalization", "text_hygiene"),
    task_types=("text.ftfy.repair", "text.normalize"),
    image="baltor-worker-cpu",
    output_contract="repaired_text.v1",
)
def ftfy_repair(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "ftfy"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("ftfy"):
        return _missing_result(adapter, "ftfy")
    text = _text_from_payload(payload)
    if not text:
        return TaskResult.failure("text required")
    try:
        import ftfy  # type: ignore

        repaired = ftfy.fix_text(text)
        return TaskResult.success({
            "repaired_text": repaired,
            "repair_report": {"adapter": adapter, "changed": repaired != text, "input_chars": len(text), "output_chars": len(repaired)},
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"ftfy_repair_failed: {exc!r}")


@registry.register(
    "text.language.detect",
    lane="analyze",
    description="Detect document/chunk language with lingua for routing OCR, NLP models, and LLM prompts.",
    emits=("language_detection",),
    capabilities=("language_detection", "routing_signal", "multilingual_preflight"),
    task_types=("text.language.detect",),
    image="baltor-worker-cpu",
    output_contract="language_detection.v1",
)
def language_detect(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "lingua"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("lingua"):
        return _missing_result(adapter, "lingua-language-detector")
    text = _text_from_payload(payload)
    if not text:
        return TaskResult.failure("text required")
    try:
        from lingua import LanguageDetectorBuilder  # type: ignore

        detector = LanguageDetectorBuilder.from_all_languages().with_preloaded_language_models().build()
        confidence_values = detector.compute_language_confidence_values(text[:5000])
        top = confidence_values[:5]
        return TaskResult.success({
            "language_detection": {
                "adapter": adapter,
                "top": [{"language": str(item.language), "confidence": item.value} for item in top],
            }
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"language_detect_failed: {exc!r}")


@registry.register(
    "entity.rapidfuzz.alias",
    lane="analyze",
    description="Cluster candidate entity/proper-noun aliases with RapidFuzz string similarity thresholds.",
    emits=("alias_candidates",),
    capabilities=("fuzzy_matching", "alias_detection", "entity_resolution"),
    task_types=("entity.alias.detect", "entity.rapidfuzz.alias"),
    image="baltor-worker-cpu",
    output_contract="alias_candidates.v1",
)
def rapidfuzz_alias(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "rapidfuzz"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("rapidfuzz"):
        return _missing_result(adapter, "rapidfuzz")
    try:
        from rapidfuzz import fuzz  # type: ignore

        labels = []
        for key in ("entities", "proper_nouns", "labels"):
            values = payload.get(key)
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, dict):
                        labels.append(str(item.get("label") or item.get("text") or item.get("name") or ""))
                    else:
                        labels.append(str(item))
        labels = sorted({compact(label) for label in labels if compact(label)})
        threshold = float(payload.get("threshold") or 88)
        pairs = []
        for left_index, left in enumerate(labels):
            for right in labels[left_index + 1:]:
                score = fuzz.token_sort_ratio(left, right)
                if score >= threshold:
                    pairs.append({"left": left, "right": right, "score": score})
        return TaskResult.success({"alias_candidates": pairs[:1000]})
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"rapidfuzz_alias_failed: {exc!r}")


@registry.register(
    "dedupe.datasketch.minhash",
    lane="normalize",
    description="Use datasketch MinHash/LSH-style signatures for scalable near-duplicate document and chunk detection.",
    emits=("minhash_signatures", "minhash_candidates"),
    capabilities=("minhash", "near_duplicate_detection", "lsh_ready"),
    task_types=("dedupe.minhash", "dedupe.datasketch.minhash"),
    image="baltor-worker-cpu",
    output_contract="minhash_dedupe.v1",
)
def datasketch_minhash(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "datasketch"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("datasketch"):
        return _missing_result(adapter, "datasketch")
    try:
        from datasketch import MinHash  # type: ignore

        chunks = payload.get("chunks") if isinstance(payload.get("chunks"), list) else chunk_text(_text_from_payload(payload))
        signatures = []
        seen: list[tuple[str, set[str]]] = []
        candidates = []
        for index, chunk in enumerate(chunks, 1):
            text = str(chunk.get("text") or "") if isinstance(chunk, dict) else str(chunk)
            shingles = {" ".join(words) for words in zip(*[WORD_RE.findall(text.lower())[i:] for i in range(5)])}
            if not shingles:
                shingles = set(WORD_RE.findall(text.lower()))
            mh = MinHash(num_perm=int(payload.get("num_perm") or 64))
            for shingle in shingles:
                mh.update(shingle.encode("utf-8"))
            chunk_id = str(chunk.get("id") or stable_hash("chunk", text, index)) if isinstance(chunk, dict) else stable_hash("chunk", text, index)
            for prior_id, prior_shingles in seen:
                union = shingles | prior_shingles
                if union:
                    jaccard = len(shingles & prior_shingles) / len(union)
                    if jaccard >= float(payload.get("threshold") or 0.82):
                        candidates.append({"left": prior_id, "right": chunk_id, "jaccard": round(jaccard, 4)})
            seen.append((chunk_id, shingles))
            signatures.append({"chunk_id": chunk_id, "hashvalues": [int(value) for value in mh.hashvalues[:16]], "shingle_count": len(shingles)})
        return TaskResult.success({"minhash_signatures": signatures, "minhash_candidates": candidates})
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"datasketch_minhash_failed: {exc!r}")


@registry.register(
    "privacy.presidio.detect",
    lane="verify",
    description="Use Microsoft Presidio Analyzer for broader PII detection before model routing or cloud export.",
    emits=("presidio_findings",),
    capabilities=("pii_detection", "privacy_filter", "anonymization_preflight"),
    task_types=("privacy.presidio.detect", "pii.detect"),
    image="baltor-worker-audit",
    output_contract="presidio_findings.v1",
)
def presidio_detect(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "presidio"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("presidio_analyzer"):
        return _missing_result(adapter, "presidio-analyzer")
    text = _text_from_payload(payload)
    if not text:
        return TaskResult.failure("text required")
    try:
        from presidio_analyzer import AnalyzerEngine  # type: ignore

        analyzer = AnalyzerEngine()
        results = analyzer.analyze(text=text[: int(payload.get("max_chars") or 100000)], language=str(payload.get("language") or "en"))
        findings = [
            {"entity_type": item.entity_type, "start": item.start, "end": item.end, "score": item.score}
            for item in results
        ]
        return TaskResult.success({"presidio_findings": findings})
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"presidio_detect_failed: {exc!r}")


@registry.register(
    "nlp.sklearn.features",
    lane="analyze",
    description="Create deterministic TF-IDF / hashing text feature matrices for clustering, routing, and topic experiments.",
    emits=("sklearn_features",),
    capabilities=("tfidf", "hashing_vectorizer", "topic_features", "deterministic_text_features"),
    task_types=("nlp.sklearn.features", "text.features"),
    image="baltor-worker-cpu",
    output_contract="sklearn_features.v1",
)
def sklearn_features(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "sklearn"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("sklearn"):
        return _missing_result(adapter, "scikit-learn")
    try:
        from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer  # type: ignore

        chunks = payload.get("chunks") if isinstance(payload.get("chunks"), list) else chunk_text(_text_from_payload(payload))
        documents = [str(chunk.get("text") or "") for chunk in chunks if isinstance(chunk, dict) and str(chunk.get("text") or "").strip()]
        if not documents:
            return TaskResult.failure("text or chunks required")
        mode = str(payload.get("mode") or "tfidf")
        if mode == "hashing":
            matrix = HashingVectorizer(n_features=int(payload.get("n_features") or 4096), alternate_sign=False).transform(documents)
            features = []
        else:
            vectorizer = TfidfVectorizer(max_features=int(payload.get("max_features") or 2000), ngram_range=(1, int(payload.get("max_ngram") or 2)))
            matrix = vectorizer.fit_transform(documents)
            scores = matrix.sum(axis=0).A1
            names = vectorizer.get_feature_names_out()
            features = [{"term": names[index], "score": round(float(score), 6)} for index, score in sorted(enumerate(scores), key=lambda item: -item[1])[:200]]
        return TaskResult.success({
            "sklearn_features": {
                "adapter": adapter,
                "mode": mode,
                "document_count": len(documents),
                "shape": list(matrix.shape),
                "top_terms": features,
            }
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"sklearn_features_failed: {exc!r}")


@registry.register(
    "graph.networkx.analyze",
    lane="graph",
    description="Run NetworkX graph analytics: centrality, connected components, communities, shortest paths, and rankings.",
    emits=("networkx_metrics",),
    capabilities=("graph_metrics", "centrality", "community_detection", "connected_components"),
    task_types=("graph.networkx.analyze", "graph.metrics"),
    image="baltor-worker-cpu",
    output_contract="networkx_metrics.v1",
)
def networkx_analyze(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "networkx"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("networkx"):
        return _missing_result(adapter, "networkx")
    try:
        import networkx as nx  # type: ignore

        graph = nx.Graph()
        for node in payload.get("nodes") or payload.get("document_nodes") or []:
            if isinstance(node, dict) and node.get("id"):
                graph.add_node(str(node["id"]), **{k: v for k, v in node.items() if isinstance(v, (str, int, float, bool))})
        for edge in payload.get("edges") or payload.get("document_edges") or []:
            if isinstance(edge, dict) and edge.get("from") and edge.get("to"):
                graph.add_edge(str(edge["from"]), str(edge["to"]), type=str(edge.get("type") or "related"))
        degree = nx.degree_centrality(graph) if graph.number_of_nodes() else {}
        between = nx.betweenness_centrality(graph, k=min(100, graph.number_of_nodes())) if graph.number_of_nodes() > 2 else {}
        components = [sorted(group) for group in nx.connected_components(graph)] if graph.number_of_nodes() else []
        communities = []
        try:
            communities = [sorted(group) for group in nx.community.greedy_modularity_communities(graph)] if graph.number_of_edges() else []
        except Exception:
            communities = []
        return TaskResult.success({
            "networkx_metrics": {
                "adapter": adapter,
                "adapter_status": "ready",
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "component_count": len(components),
                "component_sizes": sorted([len(group) for group in components], reverse=True),
                "top_degree": sorted(degree.items(), key=lambda item: (-item[1], item[0]))[:25],
                "top_betweenness": sorted(between.items(), key=lambda item: (-item[1], item[0]))[:25],
                "community_count": len(communities),
                "community_sizes": sorted([len(group) for group in communities], reverse=True),
            }
        })
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"networkx_analyze_failed: {exc!r}")


@registry.register(
    "graph.rdf.export",
    lane="graph",
    description="Export document/entity/relationship graph records to RDF Turtle/JSON-LD-compatible triples with RDFLib.",
    emits=("rdf_export",),
    capabilities=("rdf_export", "jsonld", "turtle", "sparql_ready", "semantic_web"),
    task_types=("graph.rdf.export", "graph.export"),
    image="baltor-worker-cpu",
    output_contract="rdf_export.v1",
)
def rdf_export(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    adapter = "rdflib"
    if not _enabled(adapter, payload):
        return _disabled_result(adapter)
    if not _has_module("rdflib"):
        return _missing_result(adapter, "rdflib")
    try:
        from rdflib import Graph, Literal, Namespace, RDF, URIRef  # type: ignore

        ns = Namespace(str(payload.get("namespace") or "https://baltor.ai/context/"))
        graph = Graph()
        for node in payload.get("nodes") or payload.get("document_nodes") or []:
            if isinstance(node, dict) and node.get("id"):
                uri = URIRef(ns[str(node["id"])])
                graph.add((uri, RDF.type, URIRef(ns[str(node.get("type") or "Node")])))
                graph.add((uri, ns.label, Literal(str(node.get("label") or node.get("id")))))
        for edge in payload.get("edges") or payload.get("document_edges") or []:
            if isinstance(edge, dict) and edge.get("from") and edge.get("to"):
                graph.add((URIRef(ns[str(edge["from"])]), URIRef(ns[str(edge.get("type") or "relatedTo")]), URIRef(ns[str(edge["to"])])))
        fmt = str(payload.get("format") or "turtle")
        data = graph.serialize(format=fmt)
        return TaskResult.success({"rdf_export": {"adapter": adapter, "adapter_status": "ready", "format": fmt, "triple_count": len(graph), "data": data}})
    except Exception as exc:  # noqa: BLE001
        return TaskResult.failure(f"rdf_export_failed: {exc!r}")


def _service_adapter(name: str, env_var: str, output_key: str, description: str, capabilities: tuple[str, ...]) -> None:
    @registry.register(
        name,
        lane="research",
        description=description,
        emits=(output_key,),
        capabilities=capabilities,
        task_types=(name,),
        image="baltor-worker-research",
        output_contract=f"{output_key}.v1",
    )
    def service_worker(ctx: TaskContext, payload: dict[str, Any], *, _name: str = name, _env_var: str = env_var, _output_key: str = output_key) -> TaskResult:
        adapter = _name.rsplit(".", 1)[-1].replace("_", "-")
        service_adapter = _name.split(".", 1)[1].replace("_", "-")
        if not _enabled(adapter, payload):
            return _disabled_result(adapter)
        if not _enabled(service_adapter, payload):
            return _disabled_result(service_adapter)
        url = _service_endpoint_value_by_env(_env_var).strip()
        if not url:
            return _not_configured_result(adapter, _env_var)
        try:
            response = _http_json(url, payload, timeout_s=int(payload.get("timeout_s") or 30))
            return TaskResult.success({_output_key: _adapter_record(adapter, response=response)})
        except Exception as exc:  # noqa: BLE001
            return TaskResult.failure(f"{adapter}_request_failed: {exc!r}")


_service_adapter(
    "semantic.opensearch.etl",
    _service_endpoint_env("open_semantic_etl"),
    "open_semantic_etl_result",
    "Call an Open Semantic ETL service for crawl/text extraction/OCR/enrichment/index handoff.",
    ("semantic_search_etl", "ocr", "ner", "entity_linking", "solr_elasticsearch_export"),
)
_service_adapter(
    "semantic.opensearch.entity_link",
    _service_endpoint_env("open_semantic_entity_api"),
    "entity_linking_result",
    "Call Open Semantic Entity Search API for entity extraction, linking, disambiguation, and reconciliation.",
    ("entity_linking", "entity_disambiguation", "skos", "rdf", "name_authority"),
)
_service_adapter(
    "index.fscrawler.submit",
    _service_endpoint_env("fscrawler"),
    "fscrawler_result",
    "Submit filesystem/binary documents to FSCrawler-style Elasticsearch indexing.",
    ("filesystem_crawl", "elasticsearch_index", "binary_document_indexing"),
)
_service_adapter(
    "index.solr_tika.submit",
    _service_endpoint_env("solr_tika"),
    "solr_tika_result",
    "Submit binary documents to Solr/Tika extraction and search indexing.",
    ("solr_index", "tika_extract", "search_indexing"),
)
_service_adapter(
    "rag.llamaindex.property_graph",
    _service_endpoint_env("llamaindex_property_graph"),
    "llamaindex_graph_result",
    "Call a LlamaIndex PropertyGraphIndex service for node/relation extraction and graph query preparation.",
    ("property_graph", "llm_ready_nodes", "graph_querying"),
)
_service_adapter(
    "rag.haystack.pipeline",
    _service_endpoint_env("haystack_pipeline"),
    "haystack_pipeline_result",
    "Call a Haystack preprocessing/retrieval pipeline service for converters, splitters, stores, and RAG routing.",
    ("document_preprocessing", "pipeline_orchestration", "retrieval"),
)
_service_adapter(
    "rag.neo4j_graphrag.build",
    _service_endpoint_env("neo4j_graphrag"),
    "neo4j_graphrag_result",
    "Call Neo4j GraphRAG builder/retriever service for persistent property graph creation and retrieval.",
    ("neo4j", "graphrag", "property_graph", "hybrid_retrieval"),
)
_service_adapter(
    "rag.microsoft_graphrag.index",
    _service_endpoint_env("microsoft_graphrag"),
    "microsoft_graphrag_result",
    "Call Microsoft GraphRAG indexing service for corpus-level graph extraction and community summaries.",
    ("graphrag", "community_detection", "community_summaries"),
)
_service_adapter(
    "rag.ragflow.ingest",
    _service_endpoint_env("ragflow"),
    "ragflow_result",
    "Call RAGFlow for deep document understanding, chunking, citations, and knowledge-graph/RAG ingestion.",
    ("rag_engine", "deep_document_understanding", "knowledge_graph", "citations"),
)
_service_adapter(
    "rag.lightrag.index",
    _service_endpoint_env("lightrag"),
    "lightrag_result",
    "Call LightRAG for graph-structured indexing, retrieval, and lightweight GraphRAG experiments.",
    ("graphrag", "lightweight_indexing", "graph_retrieval"),
)
_service_adapter(
    "graph.falkordb_graphrag.build",
    _service_endpoint_env("falkordb_graphrag"),
    "falkordb_graphrag_result",
    "Call FalkorDB GraphRAG SDK service for ontology-guided graph construction and graph retrieval.",
    ("falkordb", "graphrag", "ontology_discovery", "graph_retrieval"),
)
_service_adapter(
    "graph.docling_graph.extract",
    _service_endpoint_env("docling_graph"),
    "docling_graph_result",
    "Call Docling-Graph for schema/Pydantic-driven document extraction to NetworkX/Cypher/CSV graph outputs.",
    ("document_graph_extraction", "pydantic_schema", "cypher_export", "networkx"),
)
_service_adapter(
    "memory.cognee.ingest",
    _service_endpoint_env("cognee"),
    "cognee_result",
    "Call Cognee to ingest documents into persistent graph/vector agent memory with provenance.",
    ("agent_memory", "knowledge_graph", "vector_graph_retrieval", "provenance"),
)
_service_adapter(
    "memory.graphiti.upsert",
    _service_endpoint_env("graphiti"),
    "graphiti_result",
    "Call Graphiti/Zep temporal knowledge graph service for evolving facts, episodes, and temporal agent memory.",
    ("temporal_knowledge_graph", "agent_memory", "incremental_updates"),
)
_service_adapter(
    "pipeline.cocoindex.extract",
    _service_endpoint_env("cocoindex"),
    "cocoindex_result",
    "Call CocoIndex for incremental LLM extraction pipelines into graph/vector stores.",
    ("incremental_indexing", "llm_extraction", "graph_export", "delta_processing"),
)
_service_adapter(
    "kg.openspg_kag.build",
    _service_endpoint_env("openspg_kag"),
    "openspg_kag_result",
    "Call OpenSPG/KAG for ontology-constrained KG construction, mutual indexing, and logical-form-guided retrieval.",
    ("ontology_constrained_kg", "schema_guided_extraction", "logical_reasoning"),
)
_service_adapter(
    "llm.langchain_graph_transformer.extract",
    _service_endpoint_env("langchain_graph_transformer"),
    "langchain_graph_transformer_result",
    "Call LangChain LLMGraphTransformer for schema-constrained node/relationship/property extraction.",
    ("llm_graph_extraction", "allowed_nodes", "allowed_relationships", "property_graph"),
)
_service_adapter(
    "llm.langextract.extract",
    _service_endpoint_env("langextract"),
    "langextract_result",
    "Call Google LangExtract-style service for source-grounded structured extraction with exact spans.",
    ("llm_extraction", "source_grounding", "span_alignment", "structured_json"),
)
_service_adapter(
    "llm.ontogpt.extract",
    _service_endpoint_env("ontogpt"),
    "ontogpt_result",
    "Call OntoGPT/SPIRES for LinkML/ontology-grounded extraction to JSON/YAML/RDF/OWL.",
    ("ontology_extraction", "linkml", "rdf_export", "schema_validation"),
)
_service_adapter(
    "llm.structured_output.extract",
    _service_endpoint_env("structured_output"),
    "structured_output_result",
    "Call Instructor/BAML/PydanticAI-style structured-output service for validated node/edge/summary JSON.",
    ("structured_output", "pydantic_validation", "retry_validation", "node_edge_schema"),
)
_service_adapter(
    "llm.constrained_decode.extract",
    _service_endpoint_env("constrained_decode"),
    "constrained_decode_result",
    "Call Outlines/SGLang/Guidance-style constrained decoding service for JSON-schema/grammar-safe extraction.",
    ("constrained_decoding", "json_schema", "grammar_generation", "local_llm"),
)
_service_adapter(
    "ie.deepke.extract",
    _service_endpoint_env("deepke"),
    "deepke_result",
    "Call DeepKE/OneKE-style information extraction for entities, relations, and attributes.",
    ("information_extraction", "entity_relation_extraction", "attribute_extraction"),
)
_service_adapter(
    "ie.relik.extract",
    _service_endpoint_env("relik"),
    "relik_result",
    "Call ReLiK-style entity linking and relation extraction models before or alongside LLM graph extraction.",
    ("entity_linking", "relation_extraction", "neural_ie"),
)
_service_adapter(
    "summary.raptor.build",
    _service_endpoint_env("raptor"),
    "raptor_result",
    "Call RAPTOR-style recursive clustering and summarization for chunk/section/document/corpus summaries.",
    ("recursive_summarization", "clustering", "summary_tree", "hierarchical_retrieval"),
)
_service_adapter(
    "app.dify.workflow",
    _service_endpoint_env("dify"),
    "dify_result",
    "Call Dify workflow/app platform for RAG, agents, model routing, and productized document workflows.",
    ("llm_app_platform", "workflow_orchestration", "rag_app"),
)
_service_adapter(
    "app.flowise.workflow",
    _service_endpoint_env("flowise"),
    "flowise_result",
    "Call Flowise visual workflow builder for prototype ingestion, retrieval, and LLM extraction chains.",
    ("visual_workflow", "rag_prototype", "agent_builder"),
)
_service_adapter(
    "app.langflow.workflow",
    _service_endpoint_env("langflow"),
    "langflow_result",
    "Call Langflow visual workflow builder for LLM/RAG graph extraction prototypes.",
    ("visual_workflow", "rag_prototype", "structured_output"),
)
_service_adapter(
    "app.anythingllm.ingest",
    _service_endpoint_env("anythingllm"),
    "anythingllm_result",
    "Call AnythingLLM-style private document chat/RAG ingestion for quick internal knowledge-base experiments.",
    ("document_chat", "rag_app", "agent_workspace"),
)
_service_adapter(
    "managed.diffbot.nlp",
    _service_endpoint_env("diffbot_nlp"),
    "diffbot_nlp_result",
    "Call Diffbot-style managed NLP/entity/relationship extraction service.",
    ("managed_nlp", "entity_extraction", "relationship_extraction", "sentiment"),
)


@registry.register(
    "context.adapters.catalog",
    lane="orchestrate",
    description="Report all optional document/NLP/graph/index adapters, readiness, enablement, and configuration hints.",
    emits=("adapter_catalog",),
    capabilities=("adapter_discovery", "preflight", "configuration"),
    task_types=("context.adapters.catalog",),
    image="baltor-worker-orchestrator",
    output_contract="adapter_catalog.v1",
)
def adapter_catalog(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    modules = {
        "docling": "docling",
        "tika": "tika",
        "markitdown": "markitdown",
        "unstructured": "unstructured",
        "pymupdf": "fitz",
        "pdfplumber": "pdfplumber",
        "spacy": "spacy",
        "textacy": "textacy",
        "stanza": "stanza",
        "gliner": "gliner",
        "ftfy": "ftfy",
        "lingua": "lingua",
        "rapidfuzz": "rapidfuzz",
        "datasketch": "datasketch",
        "presidio": "presidio_analyzer",
        "sklearn": "sklearn",
        "networkx": "networkx",
        "rdflib": "rdflib",
    }
    services = {
        name.replace("_", "-"): str(spec["env"])
        for name, spec in CONTEXT_TOOL_ADAPTER_SERVICE_ENDPOINTS.items()
    }
    cli_tools = {"marker": "marker_single", "mineru": "mineru", "paddleocr": "paddleocr", "openosint": "openosint"}
    node_research_tools = {
        "spiderfoot": "SPIDERFOOT_URL",
        "osintbuddy": "OSINTBUDDY_URL",
        "aleph": "ALEPH_URL",
        "openaleph": "OPENALEPH_URL",
        "opensanctions-yente": "YENTE_URL",
        "opencorporates": "OPENCORPORATES_API_TOKEN",
        "gleif": "GLEIF_API_BASE",
        "companies-house": "COMPANIES_HOUSE_API_KEY",
        "sec-edgar": "SEC_EDGAR_USER_AGENT",
        "openownership-bods": "OPENOWNERSHIP_BODS_URL",
        "icij-offshore-leaks": "ICIJ_OFFSHORE_LEAKS_URL",
        "openalex": "OPENALEX_EMAIL",
        "crossref": "CROSSREF_MAILTO",
        "orcid": "ORCID_API_BASE",
        "ror": "ROR_API_BASE",
        "opencti": "OPENCTI_URL",
        "misp": "MISP_URL",
        "nominatim": "NOMINATIM_URL",
        "geonames": "GEONAMES_USERNAME",
        "google-fact-check": "GOOGLE_FACT_CHECK_API_KEY",
        "archivebox": "ARCHIVEBOX_URL",
        "wayback": "WAYBACK_API_BASE",
        "tavily": "TAVILY_API_KEY",
        "exa": "EXA_API_KEY",
        "firecrawl": "FIRECRAWL_URL",
        "crawl4ai": "CRAWL4AI_URL",
        "wikidata": "WIKIDATA_SPARQL_URL",
    }
    path_parts = [Path(part) for part in os.environ.get("PATH", "").split(os.pathsep)]
    return TaskResult.success({
        "adapter_catalog": {
            "modules": {
                name: {"enabled": _enabled(name, payload), "installed": _has_module(module), "module": module}
                for name, module in modules.items()
            },
            "services": {
                name: {"enabled": _enabled(name, payload), "configured": bool(_service_endpoint_value_by_env(env_var)), "env": env_var}
                for name, env_var in services.items()
            },
            "cli_tools": {
                name: {
                    "enabled": _enabled(name, payload),
                    "available": any((part / executable).exists() for part in path_parts),
                    "executable": executable,
                }
                for name, executable in cli_tools.items()
            },
            "node_research": {
                name: {"enabled": _enabled(name, payload), "configured": bool(os.environ.get(env_var)), "env": env_var}
                for name, env_var in node_research_tools.items()
            },
        }
    })


@registry.register(
    "context.pipeline.experimental_adapters",
    lane="orchestrate",
    description="Run the deterministic pipeline plus every enabled optional parser/NLP/privacy/dedupe/graph adapter for configuration comparison.",
    emits=("deterministic_output", "adapter_results", "adapter_summary"),
    capabilities=("adapter_benchmarking", "pipeline_orchestration", "configuration_comparison"),
    task_types=("context.pipeline.experimental_adapters", "context.pipeline.compare_adapters"),
    image="baltor-worker-orchestrator",
    output_contract="adapter_experiment.v1",
)
def experimental_adapters_pipeline(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    text = _text_from_payload(payload)
    path = _source_path(payload)
    if not text.strip() and path and path.suffix.lower() in {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".html"}:
        text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip() and not path:
        return TaskResult.failure("text or path required")

    results: dict[str, Any] = {}
    warnings: list[str] = []
    followups: list[dict[str, Any]] = []

    if text.strip():
        deterministic = registry.run({
            "job_id": f"{ctx.job_id}:deterministic",
            "run_id": ctx.run_id,
            "tenant_id": ctx.tenant_id,
            "pass_index": ctx.pass_index,
            "task": "context.pipeline.pass",
            "payload": {
                "text": text,
                "document_tree": payload.get("document_tree") if isinstance(payload.get("document_tree"), dict) else None,
                "source_name": payload.get("source_name"),
                "source_type": payload.get("source_type"),
                "path": payload.get("path"),
            },
        })
        results["context.pipeline.pass"] = {
            "ok": deterministic.ok,
            "error": deterministic.error,
            "warnings": deterministic.warnings,
            "output": deterministic.output,
        }
        warnings.extend(deterministic.warnings)
        followups.extend(deterministic.enqueue)
        base_payload = {**payload, **deterministic.output, "text": text}
    else:
        deterministic = None
        base_payload = dict(payload)

    file_tasks = (
        "document.parse.docling",
        "document.parse.unstructured",
        "document.parse.tika",
        "document.parse.markitdown",
        "document.parse.marker",
        "document.parse.mineru",
        "document.ocr.paddle",
        "document.parse.grobid",
        "document.parse.pymupdf",
        "document.parse.pdfplumber",
    )
    text_tasks = (
        "text.ftfy.repair",
        "text.language.detect",
        "nlp.spacy.extract",
        "nlp.textacy.extract",
        "nlp.stanza.extract",
        "nlp.gliner.extract",
        "privacy.presidio.detect",
        "nlp.sklearn.features",
        "entity.rapidfuzz.alias",
        "dedupe.datasketch.minhash",
        "graph.networkx.analyze",
        "graph.rdf.export",
        "semantic.opensearch.etl",
        "semantic.opensearch.entity_link",
        "index.fscrawler.submit",
        "index.solr_tika.submit",
        "rag.llamaindex.property_graph",
        "rag.haystack.pipeline",
        "rag.neo4j_graphrag.build",
        "rag.microsoft_graphrag.index",
        "rag.ragflow.ingest",
        "rag.lightrag.index",
        "graph.falkordb_graphrag.build",
        "graph.docling_graph.extract",
        "memory.cognee.ingest",
        "memory.graphiti.upsert",
        "pipeline.cocoindex.extract",
        "kg.openspg_kag.build",
        "llm.langchain_graph_transformer.extract",
        "llm.langextract.extract",
        "llm.ontogpt.extract",
        "llm.structured_output.extract",
        "llm.constrained_decode.extract",
        "ie.deepke.extract",
        "ie.relik.extract",
        "summary.raptor.build",
        "app.dify.workflow",
        "app.flowise.workflow",
        "app.langflow.workflow",
        "app.anythingllm.ingest",
        "managed.diffbot.nlp",
        "osint.openosint.catalog",
        "node.research.catalog",
        "node.research.plan",
        "context.adapters.catalog",
    )
    selected_tasks = list(text_tasks)
    if path:
        selected_tasks = list(file_tasks) + selected_tasks
        base_payload.setdefault("path", str(path))

    allow = payload.get("adapter_tasks")
    if isinstance(allow, list):
        allowed = {str(item) for item in allow}
        selected_tasks = [task for task in selected_tasks if task in allowed]

    max_tasks = int(payload.get("max_adapter_tasks") or len(selected_tasks))
    for task_name in selected_tasks[:max_tasks]:
        result = registry.run({
            "job_id": f"{ctx.job_id}:{task_name}",
            "run_id": ctx.run_id,
            "tenant_id": ctx.tenant_id,
            "pass_index": ctx.pass_index,
            "task": task_name,
            "payload": base_payload,
        })
        results[task_name] = {
            "ok": result.ok,
            "error": result.error,
            "warnings": result.warnings,
            "output": result.output,
        }
        warnings.extend(result.warnings)

    summary = {
        "task_count": len(results),
        "ok_count": sum(1 for item in results.values() if item["ok"]),
        "failed_count": sum(1 for item in results.values() if not item["ok"]),
        "missing_dependency_count": sum(
            1
            for item in results.values()
            if item["output"].get("adapter_status") == "missing_dependency"
            or any(isinstance(value, dict) and value.get("adapter_status") == "missing_dependency" for value in item["output"].values())
        ),
        "not_configured_count": sum(
            1
            for item in results.values()
            if item["output"].get("adapter_status") == "not_configured"
            or any(isinstance(value, dict) and value.get("adapter_status") == "not_configured" for value in item["output"].values())
        ),
    }
    return TaskResult.success({
        "deterministic_output": deterministic.output if deterministic else {},
        "adapter_results": results,
        "adapter_summary": summary,
    }, enqueue=followups, warnings=warnings)
