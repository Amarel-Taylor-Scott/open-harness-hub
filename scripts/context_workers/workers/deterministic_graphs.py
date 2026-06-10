"""Deterministic graph and NLP workers.

These workers intentionally avoid model calls. They produce explainable graph
structures from text, normalized document trees, regexes, and source code so
later model workers can operate over stable records instead of raw blobs.
"""
from __future__ import annotations

import ast
import re
from collections import Counter
from typing import Any

from scripts.context_workers.common import WORD_RE, chunk_text, compact, sentences, stable_hash
from scripts.context_workers.registry import TaskContext, TaskResult, registry

PROPER_NOUN_RE = re.compile(
    r"\b(?:[A-Z][a-z]+|[A-Z]{2,})(?:[\s&./-]+(?:[A-Z][a-z]+|[A-Z]{2,})){0,5}\b"
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
URL_RE = re.compile(r"\bhttps?://[^\s<>)\"']+", re.I)
MONEY_RE = re.compile(r"(?<!\w)(?:USD\s*)?\$\s?\d[\d,]*(?:\.\d{2})?|\b\d[\d,]*(?:\.\d{2})?\s?(?:USD|dollars)\b", re.I)
DATE_RE = re.compile(r"\b(?:20\d{2}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d{2}|20\d{2})\b", re.I)
PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|percent)\b", re.I)
SECTION_RE = re.compile(r"^(#{1,6})\s+(.+)$|^\s*(?:section|article|chapter)\s+([A-Z0-9_.-]+)\b[:.\s-]*(.*)$", re.I | re.M)
CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb", ".php", ".cs", ".cpp", ".c", ".h"}


def _chunk_id_for_text(text: str, index: int) -> str:
    return stable_hash("chunk", text, index)


def _source_chunks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    chunks = payload.get("chunks")
    if isinstance(chunks, list) and chunks:
        return chunks
    return chunk_text(str(payload.get("text") or ""))


def _proper_noun_candidates(text: str) -> list[str]:
    ignored = {
        "The", "This", "That", "These", "Those", "Current", "Latest", "According", "As", "No", "Yes",
        "Note", "Figure", "Table", "Page", "Section",
    }
    found = []
    for match in PROPER_NOUN_RE.finditer(text):
        label = compact(match.group(0).strip(" .,:;()[]{}"))
        if not label or label in ignored or label.lower().startswith(("http", "www")):
            continue
        if len(label) < 3:
            continue
        found.append(label)
    return found


@registry.register(
    "context.proper_noun.extract",
    lane="analyze",
    description="Extract proper-noun candidates and mention edges with deterministic casing rules.",
    emits=("proper_nouns", "proper_noun_edges"),
    capabilities=("proper_noun_detection", "local_rules", "entity_extraction"),
    task_types=("proper_noun.extract", "entity.proper_noun.detect"),
    image="baltor-worker-cpu",
    output_contract="proper_nouns.v1",
)
def proper_noun_extract(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    chunks = _source_chunks(payload)
    counts: Counter[str] = Counter()
    for chunk in chunks:
        counts.update(_proper_noun_candidates(str(chunk.get("text") or "")))
    labels = [label for label, _count in counts.most_common(120)]
    nodes = [
        {
            "id": stable_hash("proper", label, index),
            "label": label,
            "type": "proper_noun",
            "mention_count": counts[label],
            "confidence": round(min(0.95, 0.45 + 0.1 * counts[label] + 0.05 * len(label.split())), 3),
        }
        for index, label in enumerate(labels, 1)
    ]
    by_label = {node["label"]: node["id"] for node in nodes}
    edges = []
    for chunk in chunks:
        chunk_text_value = str(chunk.get("text") or "")
        for label in labels:
            if label in chunk_text_value:
                edges.append({"from": by_label[label], "to": chunk.get("id") or _chunk_id_for_text(chunk_text_value, 1), "type": "mentioned_in"})
    return TaskResult.success({"proper_nouns": nodes, "proper_noun_edges": edges})


@registry.register(
    "context.regex.extract",
    lane="analyze",
    description="Extract deterministic regex-backed facts such as dates, money, URLs, emails, percentages, and sections.",
    emits=("regex_facts", "regex_edges"),
    capabilities=("regex_extraction", "fact_signals", "local_rules"),
    task_types=("regex.extract", "fact.regex.detect"),
    image="baltor-worker-cpu",
    output_contract="regex_facts.v1",
)
def regex_extract(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    chunks = _source_chunks(payload)
    patterns = [
        ("email", EMAIL_RE),
        ("url", URL_RE),
        ("money", MONEY_RE),
        ("date", DATE_RE),
        ("percent", PERCENT_RE),
    ]
    facts = []
    edges = []
    seen: set[tuple[str, str, str]] = set()
    for chunk in chunks:
        chunk_id = str(chunk.get("id") or _chunk_id_for_text(str(chunk.get("text") or ""), 1))
        text = str(chunk.get("text") or "")
        for kind, pattern in patterns:
            for match in pattern.finditer(text):
                value = match.group(0).strip(" .,;)")
                key = (kind, value.lower(), chunk_id)
                if key in seen:
                    continue
                seen.add(key)
                item = {
                    "id": stable_hash("regex", f"{kind}:{value}:{chunk_id}", len(facts) + 1),
                    "type": kind,
                    "value": value,
                    "source_chunk": chunk_id,
                    "start": match.start(),
                    "end": match.end(),
                    "evidence": text[max(0, match.start() - 80):match.end() + 80],
                }
                facts.append(item)
                edges.append({"from": item["id"], "to": chunk_id, "type": "found_in"})
    return TaskResult.success({"regex_facts": facts, "regex_edges": edges, "regex_fact_count": len(facts)})


@registry.register(
    "context.nlp.signals",
    lane="analyze",
    description="Produce deterministic NLP signals: sentence counts, lexical density, headings, and action verbs.",
    emits=("nlp_signals",),
    capabilities=("nlp_signals", "local_rules", "text_statistics"),
    task_types=("nlp.signals", "text.statistics"),
    image="baltor-worker-cpu",
    output_contract="nlp_signals.v1",
)
def nlp_signals(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    chunks = _source_chunks(payload)
    signals = []
    action_re = re.compile(r"\b(must|shall|should|required|requires|review|approve|verify|submit|retain|delete|archive|escalate)\b", re.I)
    for index, chunk in enumerate(chunks, 1):
        text = str(chunk.get("text") or "")
        words = WORD_RE.findall(text)
        sentence_list = sentences(text)
        headings = [compact((m.group(2) or m.group(3) or "") + (" " + m.group(4) if m.group(4) else "")) for m in SECTION_RE.finditer(text)]
        action_terms = sorted({m.group(0).lower() for m in action_re.finditer(text)})
        signals.append({
            "id": stable_hash("nlp", chunk.get("id") or text, index),
            "chunk_id": chunk.get("id") or _chunk_id_for_text(text, index),
            "char_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentence_list),
            "avg_sentence_words": round(len(words) / max(1, len(sentence_list)), 2),
            "unique_word_ratio": round(len({w.lower() for w in words}) / max(1, len(words)), 3),
            "heading_count": len([h for h in headings if h]),
            "headings": [h for h in headings if h][:20],
            "action_terms": action_terms,
        })
    return TaskResult.success({"nlp_signals": signals})


def _document_tree_files(payload: dict[str, Any]) -> list[dict[str, Any]]:
    tree = payload.get("document_tree") if isinstance(payload.get("document_tree"), dict) else {}
    files = tree.get("files") if isinstance(tree.get("files"), list) else []
    if files:
        return files
    source_name = str(payload.get("source_name") or "inline.txt")
    text = str(payload.get("text") or "")
    return [{"path": source_name, "folder": "/", "name": source_name, "extension": "." + source_name.rsplit(".", 1)[-1] if "." in source_name else "none", "pages": [], "char_count": len(text), "readable_text": bool(text)}]


@registry.register(
    "context.document_graph.build",
    lane="graph",
    description="Build deterministic source/folder/file/page/component graph from normalized document tree metadata.",
    emits=("document_nodes", "document_edges"),
    capabilities=("document_graph", "lineage_edges", "local_rules"),
    task_types=("document_graph.build", "source_tree.graph"),
    image="baltor-worker-cpu",
    output_contract="document_graph.v1",
)
def document_graph_build(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    files = _document_tree_files(payload)
    nodes = [{"id": f"run:{ctx.run_id}", "label": ctx.run_id, "type": "run"}]
    edges = []
    folder_ids: dict[str, str] = {}
    for file_index, file_record in enumerate(files, 1):
        folder = str(file_record.get("folder") or "/")
        parts = [part for part in folder.strip("/").split("/") if part]
        parent_id = f"run:{ctx.run_id}"
        folder_path = ""
        if not parts:
            folder_ids.setdefault("/", "folder:/")
            if not any(node.get("id") == "folder:/" for node in nodes):
                nodes.append({"id": "folder:/", "label": "/", "type": "folder", "depth": 0})
                edges.append({"from": "folder:/", "to": parent_id, "type": "child_of"})
            parent_id = "folder:/"
        for depth, part in enumerate(parts, 1):
            folder_path = f"{folder_path}/{part}" if folder_path else part
            folder_id = "folder:" + folder_path
            if folder_id not in folder_ids:
                folder_ids[folder_path] = folder_id
                nodes.append({"id": folder_id, "label": part, "path": folder_path, "type": "folder", "depth": depth})
                edges.append({"from": folder_id, "to": parent_id, "type": "child_of"})
            parent_id = folder_id
        file_path = str(file_record.get("path") or file_record.get("name") or f"file-{file_index}")
        file_id = stable_hash("file", file_path, file_index)
        nodes.append({
            "id": file_id,
            "label": file_record.get("name") or file_path.rsplit("/", 1)[-1],
            "path": file_path,
            "type": "file",
            "extension": file_record.get("extension", "none"),
            "byte_size": file_record.get("byte_size", 0),
            "char_count": file_record.get("char_count", 0),
            "readable_text": bool(file_record.get("readable_text")),
        })
        edges.append({"from": file_id, "to": parent_id, "type": "child_of"})
        for page in file_record.get("pages") or []:
            page_no = int(page.get("page_number") or 0)
            page_id = stable_hash("page", f"{file_path}:{page_no}", page_no or 1)
            nodes.append({"id": page_id, "label": f"page {page_no}", "type": "page", "page_number": page_no, "char_count": page.get("char_count", 0)})
            edges.append({"from": page_id, "to": file_id, "type": "page_of"})
            for component in page.get("components") or []:
                component_id = stable_hash("component", f"{file_path}:{page_no}:{component.get('id')}", len(nodes))
                nodes.append({
                    "id": component_id,
                    "label": component.get("id"),
                    "type": "component",
                    "component_type": component.get("type"),
                    "char_count": component.get("char_count", 0),
                    "text_preview": component.get("text_preview", ""),
                })
                edges.append({"from": component_id, "to": page_id, "type": "component_of"})
    return TaskResult.success({"document_nodes": nodes, "document_edges": edges, "document_node_count": len(nodes), "document_edge_count": len(edges)})


def _code_text_records(payload: dict[str, Any]) -> list[dict[str, str]]:
    records = payload.get("files") if isinstance(payload.get("files"), list) else []
    out = []
    for index, record in enumerate(records, 1):
        path = str(record.get("path") or record.get("name") or f"file-{index}.txt")
        text = str(record.get("text") or record.get("content") or "")
        if text:
            out.append({"path": path, "text": text})
    if out:
        return out
    source_name = str(payload.get("source_name") or "inline.py")
    return [{"path": source_name, "text": str(payload.get("text") or "")}]


class _PythonGraphVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []
        self.scope_stack: list[str] = []

    def _add_node(self, node_id: str, label: str, kind: str, lineno: int = 0) -> None:
        self.nodes.append({"id": node_id, "label": label, "type": kind, "path": self.path, "lineno": lineno})

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        node_id = stable_hash("code", f"{self.path}:class:{node.name}:{node.lineno}", len(self.nodes) + 1)
        self._add_node(node_id, node.name, "class", node.lineno)
        if self.scope_stack:
            self.edges.append({"from": node_id, "to": self.scope_stack[-1], "type": "defined_in"})
        parent = self.scope_stack[-1] if self.scope_stack else None
        self.scope_stack.append(node_id)
        self.generic_visit(node)
        self.scope_stack.pop()
        if parent:
            self.scope_stack.append(parent)
            self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self._visit_function(node, "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self._visit_function(node, "async_function")

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, kind: str) -> None:
        node_id = stable_hash("code", f"{self.path}:{kind}:{node.name}:{node.lineno}", len(self.nodes) + 1)
        self._add_node(node_id, node.name, kind, node.lineno)
        if self.scope_stack:
            self.edges.append({"from": node_id, "to": self.scope_stack[-1], "type": "defined_in"})
        self.scope_stack.append(node_id)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Call(self, node: ast.Call) -> Any:
        if not self.scope_stack:
            self.generic_visit(node)
            return
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        if name:
            call_id = stable_hash("call", f"{self.path}:{name}:{node.lineno}:{node.col_offset}", len(self.nodes) + 1)
            self._add_node(call_id, name, "call", node.lineno)
            self.edges.append({"from": self.scope_stack[-1], "to": call_id, "type": "calls"})
        self.generic_visit(node)


@registry.register(
    "context.code_graph.build",
    lane="graph",
    description="Build deterministic code symbol/call/import graph, with Python AST support and regex fallback.",
    emits=("code_nodes", "code_edges"),
    capabilities=("code_graph", "ast_parse", "regex_extraction", "local_rules"),
    task_types=("code_graph.build", "code.symbols.extract"),
    image="baltor-worker-cpu",
    output_contract="code_graph.v1",
)
def code_graph_build(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    records = _code_text_records(payload)
    nodes = []
    edges = []
    for file_index, record in enumerate(records, 1):
        path = record["path"]
        text = record["text"]
        file_id = stable_hash("codefile", path, file_index)
        nodes.append({"id": file_id, "label": path.rsplit("/", 1)[-1], "path": path, "type": "code_file"})
        suffix = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if suffix == ".py":
            try:
                tree = ast.parse(text)
                visitor = _PythonGraphVisitor(path)
                visitor.scope_stack.append(file_id)
                visitor.visit(tree)
                visitor.scope_stack.pop()
                nodes.extend(visitor.nodes)
                edges.extend(visitor.edges)
                for item in tree.body:
                    if isinstance(item, (ast.Import, ast.ImportFrom)):
                        module = ".".join(alias.name for alias in item.names) if isinstance(item, ast.Import) else str(item.module or "")
                        import_id = stable_hash("import", f"{path}:{module}:{getattr(item, 'lineno', 0)}", len(nodes) + 1)
                        nodes.append({"id": import_id, "label": module, "type": "import", "path": path, "lineno": getattr(item, "lineno", 0)})
                        edges.append({"from": file_id, "to": import_id, "type": "imports"})
                continue
            except SyntaxError:
                pass
        for match in re.finditer(r"^\s*(?:function|def|class|const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.M):
            symbol_id = stable_hash("symbol", f"{path}:{match.group(1)}:{match.start()}", len(nodes) + 1)
            nodes.append({"id": symbol_id, "label": match.group(1), "type": "symbol", "path": path})
            edges.append({"from": symbol_id, "to": file_id, "type": "defined_in"})
    return TaskResult.success({"code_nodes": nodes, "code_edges": edges, "code_node_count": len(nodes), "code_edge_count": len(edges)})
