"""Deterministic document-tree normalization workers.

This module handles the first local step after upload/connect: turn a file set,
ZIP manifest, or inline text payload into stable document, page, component, and
hierarchy records. It intentionally uses only the Python standard library so it
can run before heavier parser/OCR/NLP images are available.
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Any

from scripts.context_workers.common import compact, stable_hash
from scripts.context_workers.registry import TaskContext, TaskResult, registry

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".xml", ".html", ".log", ".py", ".js", ".ts"}
MAX_ZIP_FILES = 200
MAX_ZIP_MEMBER_BYTES = 1_500_000
PAGE_CHARS = 2800


def _path_tags(path: str) -> list[str]:
    parts = [part for part in path.replace("\\", "/").split("/") if part]
    tags: list[str] = []
    for index, _part in enumerate(parts[:-1], 1):
        tags.append(f"folder:{'/'.join(parts[:index])}")
        tags.append(f"depth:{index}")
    if parts:
        suffix = "." + parts[-1].rsplit(".", 1)[-1].lower() if "." in parts[-1] else "none"
        tags.append(f"filename:{parts[-1]}")
        tags.append(f"extension:{suffix}")
    return tags


def _component_type(text: str) -> str:
    if re.match(r"^\s*[-*]\s+", text) or "\n-" in text:
        return "list"
    if re.search(r"\|.+\|", text) or ("," in text and text.count("\n") >= 2):
        return "table_like"
    if re.search(r"[{};=<>]{3,}", text):
        return "code_like"
    if len(text) <= 120 and re.search(r"^(#{1,6}\s+|[A-Z0-9][A-Z0-9 .:/_-]{4,})$", text.strip()):
        return "heading"
    return "paragraph"


def _page_components(text: str) -> list[dict[str, Any]]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    return [
        {
            "component_id": stable_hash("component", block, index),
            "ordinal": index,
            "type": _component_type(block),
            "text_preview": compact(block)[:360],
            "char_count": len(block),
        }
        for index, block in enumerate(blocks[:250], 1)
    ]


def _text_pages(text: str) -> list[dict[str, Any]]:
    if "\f" in text:
        page_texts = [part.strip() for part in text.split("\f") if part.strip()]
    else:
        page_texts = [text[index:index + PAGE_CHARS].strip() for index in range(0, len(text), PAGE_CHARS) if text[index:index + PAGE_CHARS].strip()]
    return [
        {
            "page_id": stable_hash("page-text", page_text, index),
            "page_number": index,
            "char_count": len(page_text),
            "components": _page_components(page_text),
        }
        for index, page_text in enumerate(page_texts or [text], 1)
    ]


def _file_record(path: str, raw: bytes, text: str, *, source: str) -> dict[str, Any]:
    clean_path = path.replace("\\", "/").strip("/") or "source.txt"
    name = clean_path.rsplit("/", 1)[-1]
    folder = clean_path.rsplit("/", 1)[0] if "/" in clean_path else "/"
    suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else "none"
    readable = bool(text.strip())
    return {
        "file_id": stable_hash("file", clean_path, len(raw) + len(text)),
        "path": clean_path,
        "folder": folder or "/",
        "name": name,
        "extension": suffix,
        "source": source,
        "byte_size": len(raw),
        "char_count": len(text),
        "readable_text": readable,
        "tags": _path_tags(clean_path),
        "pages": _text_pages(text) if readable else [],
    }


def _tree_from_zip(path: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    folders: set[str] = set()
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist()[:MAX_ZIP_FILES]:
            clean_name = info.filename.replace("\\", "/").strip("/")
            if not clean_name:
                continue
            parent_parts = clean_name.split("/")[:-1] if not info.is_dir() else clean_name.split("/")
            for index in range(1, len(parent_parts) + 1):
                folders.add("/".join(parent_parts[:index]))
            if info.is_dir():
                continue
            suffix = "." + clean_name.rsplit(".", 1)[-1].lower() if "." in clean_name else "none"
            if info.file_size > MAX_ZIP_MEMBER_BYTES:
                records.append(_file_record(clean_name, b"", "", source="zip-skipped-too-large"))
                continue
            if suffix not in TEXT_EXTENSIONS:
                records.append(_file_record(clean_name, b"", "", source="zip-binary-or-unsupported"))
                continue
            raw = zf.read(info)
            text = raw.decode("utf-8", errors="ignore")
            records.append(_file_record(clean_name, raw, text, source="zip"))
    return _tree_summary({"kind": "zip", "archive_name": path.name, "upload_path": str(path), "folders": sorted(folders), "files": records})


def _tree_summary(tree: dict[str, Any]) -> dict[str, Any]:
    files = [record for record in tree.get("files", []) if isinstance(record, dict)]
    folders = {str(folder) for folder in tree.get("folders", [])}
    for record in files:
        folder = str(record.get("folder") or "")
        if folder and folder != "/":
            parts = [part for part in folder.split("/") if part]
            for index in range(1, len(parts) + 1):
                folders.add("/".join(parts[:index]))
    tree["folders"] = sorted(folders)
    tree["summary"] = {
        "folders": len(folders),
        "files": len(files),
        "readable_files": sum(1 for record in files if record.get("readable_text")),
        "pages": sum(len(record.get("pages") or []) for record in files),
        "components": sum(len(page.get("components") or []) for record in files for page in record.get("pages") or []),
    }
    return tree


def _tree_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    tree = payload.get("document_tree") if isinstance(payload.get("document_tree"), dict) else None
    if tree and isinstance(tree.get("files"), list):
        return _tree_summary(dict(tree))
    raw_path = payload.get("path") or payload.get("file_path") or payload.get("source_path")
    if raw_path:
        path = Path(str(raw_path)).expanduser()
        if path.exists() and path.is_file():
            if path.suffix.lower() == ".zip":
                return _tree_from_zip(path)
            raw = path.read_bytes()
            text = raw.decode("utf-8", errors="ignore") if path.suffix.lower() in TEXT_EXTENSIONS else ""
            return _tree_summary({"kind": "single_file", "archive_name": "", "upload_path": str(path), "folders": [], "files": [_file_record(path.name, raw, text, source="path")]})
    text = str(payload.get("text") or "")
    source_name = str(payload.get("source_name") or "inline-context.txt")
    raw = text.encode("utf-8", errors="ignore")
    return _tree_summary({"kind": "inline_text", "archive_name": "", "folders": [], "files": [_file_record(source_name, raw, text, source=str(payload.get("source_type") or "inline"))]})


@registry.register(
    "context.document_tree.normalize",
    lane="normalize",
    description="Normalize uploaded file sets, ZIPs, and connector envelopes into stable file/page/component hierarchy records.",
    emits=("normalized_document_tree", "normalized_documents", "page_components", "source_hierarchy_edges"),
    capabilities=("file_set_normalization", "zip_manifest", "page_component_split", "hierarchy_tagging", "local_rules"),
    task_types=("document_tree.normalize", "file_set.normalize", "zip.normalize"),
    image="baltor-worker-cpu",
    output_contract="document_tree",
)
def document_tree_normalize(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    tree = _tree_from_payload(payload)
    documents: list[dict[str, Any]] = []
    components: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for file_index, record in enumerate(tree.get("files") or [], 1):
        if not isinstance(record, dict):
            continue
        file_id = str(record.get("file_id") or stable_hash("file", record.get("path") or file_index, file_index))
        documents.append({
            "file_id": file_id,
            "path": record.get("path"),
            "folder": record.get("folder"),
            "name": record.get("name"),
            "extension": record.get("extension"),
            "source": record.get("source"),
            "readable_text": bool(record.get("readable_text")),
            "tags": record.get("tags") or [],
            "page_count": len(record.get("pages") or []),
            "component_count": sum(len(page.get("components") or []) for page in record.get("pages") or []),
        })
        for page in record.get("pages") or []:
            page_id = str(page.get("page_id") or stable_hash("page", f"{file_id}:{page.get('page_number')}", len(components) + 1))
            edges.append({"from": page_id, "to": file_id, "type": "page_of"})
            for component in page.get("components") or []:
                component_id = str(component.get("component_id") or stable_hash("component", f"{page_id}:{component.get('ordinal')}", len(components) + 1))
                components.append({
                    "component_id": component_id,
                    "file_id": file_id,
                    "page_id": page_id,
                    "path": record.get("path"),
                    "page_number": page.get("page_number"),
                    "ordinal": component.get("ordinal"),
                    "type": component.get("type"),
                    "char_count": component.get("char_count", 0),
                    "text_preview": component.get("text_preview", ""),
                })
                edges.append({"from": component_id, "to": page_id, "type": "component_of"})
    return TaskResult.success({
        "normalized_document_tree": tree,
        "normalized_documents": documents,
        "page_components": components,
        "source_hierarchy_edges": edges,
        "document_tree_summary": tree.get("summary", {}),
    })
