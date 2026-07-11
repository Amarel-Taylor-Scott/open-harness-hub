"""Local registry connector for AIDevObserver.

This is the first private-alpha registry connector slice. It turns an explicit
repo root into candidate-only source-ref records for the things AI coding
agents often recreate or over-read:

* Python functions, classes, methods, and constants.
* README/docs snippets and Claude-style project instruction surfaces.
* package.json and pyproject command entries.

The connector never claims truth, never stores transcript text, and never emits
absolute local paths. It produces repo-relative source refs that the observer
review layer, benchmark fixtures, or future Teleon route mode can use as
candidate evidence.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .settings import LOCAL_REGISTRY_SETTINGS

LOCAL_REGISTRY_ID = "local_repo"
CONNECTOR_VERSION = "0.1.0"
LOCAL_PRIMITIVE_CANDIDATE_SCHEMA = "local_repo_primitive_v0.2"
MAX_INDEXED_FILES = LOCAL_REGISTRY_SETTINGS.max_indexed_files
MAX_DOC_CHARS = LOCAL_REGISTRY_SETTINGS.max_doc_chars
MAX_SNIPPET_CHARS = LOCAL_REGISTRY_SETTINGS.max_snippet_chars
MAX_SEARCH_RESULTS = LOCAL_REGISTRY_SETTINGS.max_search_results
MAX_PRIMITIVE_CANDIDATES = LOCAL_REGISTRY_SETTINGS.max_primitive_candidates
MIN_SEARCH_SCORE = LOCAL_REGISTRY_SETTINGS.min_search_score
PYTHON_SUFFIX = ".py"
DOC_SUFFIXES = {".md", ".txt", ".rst"}
DOC_NAME_PREFIXES = ("readme", "contributing", "architecture", "runbook", "guide")
CLAUDE_ROOT_DOC_KINDS = {
    "claude.md": "claude_project_context",
    "hooks.md": "claude_hooks_overview",
    "session-log.md": "session_memory_doc",
    "session_log.md": "session_memory_doc",
}
CLAUDE_DOC_DIR_KINDS = {
    "commands": "claude_command",
    "hooks": "claude_hook_doc",
    "mcp": "mcp_connector_doc",
}
CLAUDE_PROJECT_KINDS = frozenset({
    "claude_project_context",
    "claude_hooks_overview",
    "session_memory_doc",
    "claude_skill",
    "claude_command",
    "claude_hook_doc",
    "mcp_connector_doc",
})
SCRIPT_FILENAMES = {"package.json", "pyproject.toml"}
PRIMITIVE_SKIP_DIRS = {"tests", "__tests__"}
KIND_PRIORITY = {
    "python_function": 0,
    "python_method": 1,
    "python_class": 2,
    "python_constant": 3,
    "python_entrypoint": 4,
    "package_script": 5,
    "claude_command": 6,
    "claude_skill": 7,
    "mcp_connector_doc": 8,
    "claude_hook_doc": 9,
    "claude_hooks_overview": 10,
    "claude_project_context": 11,
    "session_memory_doc": 12,
    "doc_snippet": 19,
}
SKIP_DIRS = {
    ".agent",
    ".agents",
    ".claude",
    ".codex",
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "_reference",
    "archive",
    "dist",
    "node_modules",
    "repo_reference",
    "site",
}
TOKEN_RE = re.compile(r"[a-z0-9]+")
PYPROJECT_SCRIPT_SECTION_RE = re.compile(r"^\[(project\.scripts|tool\.poetry\.scripts)\]\s*$")
SAFE_REL_PATH_RE = re.compile(r"^[A-Za-z0-9._/@+-]+$")
STOPWORDS = {
    "a",
    "add",
    "agent",
    "all",
    "also",
    "an",
    "and",
    "as",
    "be",
    "build",
    "by",
    "code",
    "create",
    "creating",
    "do",
    "find",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "me",
    "model",
    "of",
    "or",
    "scan",
    "scanning",
    "session",
    "that",
    "the",
    "this",
    "to",
    "where",
    "with",
    "write",
    "writing",
}
QUERY_SYNONYMS = {
    "csv": {"csv", "delimiter", "header", "rows", "read", "reader", "import"},
    "parser": {"parse", "parser", "read", "reader", "rows"},
    "parse": {"parse", "parser", "read", "reader"},
    "import": {"import", "ingest", "load", "read", "rows"},
    "retry": {"retry", "backoff", "tenacity", "attempts"},
    "backoff": {"retry", "backoff", "tenacity", "attempts"},
    "constant": {"constant", "config", "setting", "settings"},
    "defined": {"constant", "definition", "symbol", "where"},
    "max": {"limit", "maximum", "max"},
    "script": {"command", "script", "cli", "run"},
    "command": {"command", "script", "cli", "run"},
}

SELF_PARAM_NAMES = {"self", "cls"}
MUTATION_SCALAR_TO_SEQUENCE = "scalar_to_sequence"
MUTATION_OUTPUT_FIELD_WRAPPER = "output_field_wrapper"
MUTATION_FIELD_RENAME_ADAPTER = "field_rename_adapter"
MUTATION_RETRY_CACHE_RATE_LIMIT_ADAPTER = "retry_cache_rate_limit_adapter"
FIT_EXACT_MATCH = "exact_match"
FIT_DETERMINISTIC_EDIT_MATCH = "deterministic_edit_match"
FIT_INCOMPATIBLE = "incompatible"
_INDEX_CACHE_LOCK = threading.Lock()
_INDEX_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def clear_local_repo_index_cache() -> None:
    """Clear the in-process local repo index cache.

    Tests and long-running development sessions can call this when they need a
    hard refresh. Production search can also disable caching by setting
    ``OH_OBSERVER_LOCAL_INDEX_CACHE_TTL_SECONDS=0``.
    """

    with _INDEX_CACHE_LOCK:
        _INDEX_CACHE.clear()


@dataclass(frozen=True, slots=True)
class LocalRegistryRecord:
    """Candidate source-ref row from an explicit local repo root."""

    record_id: str
    kind: str
    name: str
    path: str
    summary: str
    source_ref: dict[str, Any]
    search_terms: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    candidate: bool = True
    serves_truth: bool = False
    trust: str = "candidate"
    connector_version: str = CONNECTOR_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.record_id,
            "registry": LOCAL_REGISTRY_ID,
            "kind": self.kind,
            "name": self.name,
            "path": self.path,
            "summary": self.summary,
            "source_ref": self.source_ref,
            "search_terms": list(self.search_terms),
            "metadata": self.metadata,
            "candidate": self.candidate,
            "serves_truth": self.serves_truth,
            "trust": self.trust,
            "connector_version": self.connector_version,
        }


def _repo_root(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _is_doc_file(path: Path) -> bool:
    lower_name = path.name.lower()
    if _project_doc_kind(path):
        return True
    return path.suffix.lower() in DOC_SUFFIXES and (
        path.parent.name == "docs" or lower_name.startswith(DOC_NAME_PREFIXES) or "docs" in path.parts
    )


def _file_index_priority(rel: Path) -> int | None:
    if _project_doc_kind(rel):
        return -1
    if rel.suffix == PYTHON_SUFFIX:
        return 0
    if rel.name in SCRIPT_FILENAMES:
        return 1
    if _is_doc_file(rel):
        return 8
    return None


def _project_doc_kind(rel: Path) -> str | None:
    """Return a structured kind for Claude-style project docs."""
    if rel.suffix.lower() not in DOC_SUFFIXES:
        return None
    lower_name = rel.name.lower()
    parts = tuple(part.lower() for part in rel.parts)
    if len(parts) == 1:
        return CLAUDE_ROOT_DOC_KINDS.get(lower_name)
    top = parts[0]
    if top == "skills" and lower_name == "skill.md" and len(parts) >= 3:
        return "claude_skill"
    return CLAUDE_DOC_DIR_KINDS.get(top)


def _project_doc_name(rel: Path, kind: str) -> str:
    if kind == "claude_project_context":
        return "claude_project_context"
    if kind == "claude_hooks_overview":
        return "claude_hooks_overview"
    if kind == "session_memory_doc":
        return "session_memory"
    if kind == "claude_skill" and len(rel.parts) >= 2:
        return Path(rel.parts[-2]).name
    return rel.stem.replace("-", "_").replace(" ", "_")


def _iter_files(root: Path) -> Iterable[Path]:
    candidates: list[tuple[int, str, Path]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if _is_skipped(rel):
            continue
        priority = _file_index_priority(rel)
        if priority is None:
            continue
        candidates.append((priority, rel.as_posix(), path))
    for _, _, path in sorted(candidates)[:MAX_INDEXED_FILES]:
        yield path


def _safe_rel(root: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(root).as_posix()
    except ValueError:
        # post-_repos-migration a discovered file may live under a SIBLING repo (_repos/<other>/...) while
        # root is one repo's dir — relativize against the monorepo root (the .aidoneright-root sentinel
        # ancestor) so the ref stays repo-relative; anything outside the monorepo still raises below
        monorepo = next((a for a in Path(root).resolve().parents if (a / ".aidoneright-root").exists()), None)
        if monorepo is None:
            raise
        rel = resolved.relative_to(monorepo).as_posix()
    if rel.startswith("../") or rel.startswith("/") or not SAFE_REL_PATH_RE.match(rel):
        raise ValueError(f"unsafe relative path: {rel!r}")
    return rel


def _tokens(text: str) -> set[str]:
    out = {token for token in TOKEN_RE.findall(text.lower()) if len(token) >= 2 and token not in STOPWORDS}
    for token in list(out):
        out.update(QUERY_SYNONYMS.get(token, set()))
    return out


def _record_id(kind: str, path: str, name: str) -> str:
    body = f"{kind}:{path}:{name}".lower()
    safe = re.sub(r"[^a-z0-9]+", "-", body).strip("-")
    return f"local:{safe[:LOCAL_REGISTRY_SETTINGS.record_id_slug_chars]}"


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.strip().split())[:MAX_SNIPPET_CHARS]


def _sha(text: str, *, n: int = LOCAL_REGISTRY_SETTINGS.hash_digest_chars) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _annotation_name(node: ast.AST | None) -> str:
    if node is None:
        return "Any"
    try:
        out = ast.unparse(node)
    except Exception:
        return "Any"
    return re.sub(r"\s+", "", out.replace("typing.", ""))[:LOCAL_REGISTRY_SETTINGS.annotation_chars] or "Any"


def _ast_digest(node: ast.AST) -> str:
    return f"sha256:{_sha(ast.dump(node, include_attributes=False), n=24)}"


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    names = [arg.arg for arg in node.args.posonlyargs + node.args.args]
    if node.args.vararg:
        names.append("*" + node.args.vararg.arg)
    names.extend(arg.arg for arg in node.args.kwonlyargs)
    if node.args.kwarg:
        names.append("**" + node.args.kwarg.arg)
    return f"{node.name}({', '.join(names)})"


def _signature_with_annotations(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args: list[str] = []
    for arg in node.args.posonlyargs + node.args.args:
        label = arg.arg
        if arg.annotation is not None:
            label = f"{label}: {_annotation_name(arg.annotation)}"
        args.append(label)
    if node.args.vararg:
        label = "*" + node.args.vararg.arg
        if node.args.vararg.annotation is not None:
            label = f"{label}: {_annotation_name(node.args.vararg.annotation)}"
        args.append(label)
    for arg in node.args.kwonlyargs:
        label = arg.arg
        if arg.annotation is not None:
            label = f"{label}: {_annotation_name(arg.annotation)}"
        args.append(label)
    if node.args.kwarg:
        label = "**" + node.args.kwarg.arg
        if node.args.kwarg.annotation is not None:
            label = f"{label}: {_annotation_name(node.args.kwarg.annotation)}"
        args.append(label)
    ret = _annotation_name(node.returns)
    return f"{node.name}({', '.join(args)}) -> {ret}"


def _function_contract(node: ast.FunctionDef | ast.AsyncFunctionDef, *, is_method: bool) -> dict[str, str]:
    args = list(node.args.posonlyargs + node.args.args)
    if is_method and args and args[0].arg in SELF_PARAM_NAMES:
        args = args[1:]
    args.extend(node.args.kwonlyargs)
    parts = [f"{arg.arg}:{_annotation_name(arg.annotation)}" for arg in args]
    if node.args.vararg:
        parts.append(f"*{node.args.vararg.arg}:{_annotation_name(node.args.vararg.annotation)}")
    if node.args.kwarg:
        parts.append(f"**{node.args.kwarg.arg}:{_annotation_name(node.args.kwarg.annotation)}")
    if not parts:
        input_contract = "None"
    elif len(parts) == 1:
        input_contract = parts[0].split(":", 1)[1]
    else:
        input_contract = f"Args[{','.join(parts)}]"
    return {
        "input": input_contract,
        "output": _annotation_name(node.returns),
    }


def _make_record(
    *,
    kind: str,
    name: str,
    path: str,
    summary: str,
    line: int | None = None,
    metadata: dict[str, Any] | None = None,
    search_terms: Iterable[str] = (),
) -> LocalRegistryRecord:
    source_ref = {
        "registry": LOCAL_REGISTRY_ID,
        "kind": kind,
        "name": name,
        "path": path,
    }
    if line is not None:
        source_ref["line"] = line
    terms = tuple(sorted(_tokens(" ".join([name, path, summary, " ".join(search_terms)]))))
    return LocalRegistryRecord(
        record_id=_record_id(kind, path, name),
        kind=kind,
        name=name,
        path=path,
        summary=summary,
        source_ref=source_ref,
        search_terms=terms,
        metadata=metadata or {},
    )


def _index_python_file(root: Path, path: Path) -> list[LocalRegistryRecord]:
    rel = _safe_rel(root, path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []

    records: list[LocalRegistryRecord] = []
    parent_stack: list[str] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.ClassDef):
            name = ".".join(parent_stack + [node.name])
            records.append(_make_record(
                kind="python_class",
                name=name,
                path=rel,
                line=node.lineno,
                summary=_first_line(ast.get_docstring(node)) or f"Class {name}",
                metadata={
                    "source_digest": _ast_digest(node),
                    "base_classes": [_annotation_name(base) for base in node.bases],
                },
                search_terms=("class", "object", *[base.id for base in node.bases if isinstance(base, ast.Name)]),
            ))
            parent_stack.append(node.name)
            for child in node.body:
                visit(child)
            parent_stack.pop()
            return

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = ".".join(parent_stack + [node.name])
            kind = "python_method" if parent_stack else "python_function"
            contract = _function_contract(node, is_method=bool(parent_stack))
            records.append(_make_record(
                kind=kind,
                name=name,
                path=rel,
                line=node.lineno,
                summary=_first_line(ast.get_docstring(node)) or _signature_with_annotations(node),
                metadata={
                    "signature": _signature(node),
                    "typed_signature": _signature_with_annotations(node),
                    "contract": contract,
                    "contract_digest": f"sha256:{_sha(_canonical_json(contract), n=24)}",
                    "source_digest": _ast_digest(node),
                },
                search_terms=("function", "method", "callable", node.name.replace("_", " ")),
            ))
            return

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            else:
                targets = [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    annotation = _annotation_name(node.annotation) if isinstance(node, ast.AnnAssign) else "ConfigValue"
                    records.append(_make_record(
                        kind="python_constant",
                        name=target.id,
                        path=rel,
                        line=node.lineno,
                        summary=f"Constant {target.id}",
                        metadata={
                            "contract": {"input": "None", "output": annotation},
                            "contract_digest": f"sha256:{_sha(_canonical_json({'input': 'None', 'output': annotation}), n=24)}",
                            "source_digest": _ast_digest(node),
                        },
                        search_terms=("constant", "config", "setting", target.id.replace("_", " ")),
                    ))

        for child in ast.iter_child_nodes(node):
            visit(child)

    for child in tree.body:
        visit(child)
    return records


def _index_doc_file(root: Path, path: Path) -> list[LocalRegistryRecord]:
    rel = _safe_rel(root, path)
    rel_path = Path(rel)
    try:
        text = path.read_text(encoding="utf-8")[:MAX_DOC_CHARS]
    except (UnicodeDecodeError, OSError):
        return []
    compact = " ".join(text.split())
    if not compact:
        return []
    kind = _project_doc_kind(rel_path) or "doc_snippet"
    title = _project_doc_name(rel_path, kind) if kind != "doc_snippet" else path.stem.replace("-", " ").replace("_", " ").strip() or path.name
    project_terms = {
        "claude_project_context": ("claude", "instructions", "project", "context", "policy"),
        "claude_hooks_overview": ("claude", "hooks", "policy", "integration"),
        "session_memory_doc": ("session", "memory", "summary", "log"),
        "claude_skill": ("claude", "skill", "capability", "procedure"),
        "claude_command": ("claude", "command", "slash", "workflow", "template"),
        "claude_hook_doc": ("claude", "hook", "pretooluse", "posttooluse", "integration"),
        "mcp_connector_doc": ("mcp", "tool", "server", "connector", "integration"),
    }.get(kind, ())
    return [_make_record(
        kind=kind,
        name=title,
        path=rel,
        summary=compact[:MAX_SNIPPET_CHARS],
        search_terms=("doc", "readme", "guide", title, *project_terms),
    )]


def _index_package_scripts(root: Path, path: Path) -> list[LocalRegistryRecord]:
    rel = _safe_rel(root, path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return []
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return []
    records = []
    for name, command in sorted(scripts.items()):
        if not isinstance(name, str) or not isinstance(command, str):
            continue
        records.append(_make_record(
            kind="package_script",
            name=name,
            path=rel,
            summary=command[:MAX_SNIPPET_CHARS],
            search_terms=("script", "command", "npm", name, command),
        ))
    return records


def _index_pyproject_scripts(root: Path, path: Path) -> list[LocalRegistryRecord]:
    rel = _safe_rel(root, path)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return []
    records = []
    in_scripts = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_scripts = bool(PYPROJECT_SCRIPT_SECTION_RE.match(stripped))
            continue
        if not in_scripts or "=" not in stripped or stripped.startswith("#"):
            continue
        name, command = stripped.split("=", 1)
        name = name.strip().strip('"').strip("'")
        command = command.strip().strip('"').strip("'")
        if name:
            records.append(_make_record(
                kind="python_entrypoint",
                name=name,
                path=rel,
                summary=command[:MAX_SNIPPET_CHARS],
                search_terms=("script", "command", "cli", "entrypoint", name, command),
            ))
    return records


def index_local_repo(root: str | Path) -> list[dict[str, Any]]:
    """Index repo-local symbols/docs/scripts into candidate source-ref rows."""
    repo = _repo_root(root)
    if not repo.is_dir():
        raise NotADirectoryError(str(root))

    records: list[LocalRegistryRecord] = []
    for path in _iter_files(repo):
        if path.suffix == PYTHON_SUFFIX:
            records.extend(_index_python_file(repo, path))
        elif _is_doc_file(path.relative_to(repo)):
            records.extend(_index_doc_file(repo, path))
        elif path.name == "package.json":
            records.extend(_index_package_scripts(repo, path))
        elif path.name == "pyproject.toml":
            records.extend(_index_pyproject_scripts(repo, path))

    deduped: dict[str, dict[str, Any]] = {}
    for record in records:
        deduped.setdefault(record.record_id, record.to_dict())
    return list(deduped.values())


def cached_index_local_repo(root: str | Path, *, ttl_seconds: int | None = None) -> list[dict[str, Any]]:
    """Return local repo index rows using a bounded in-process cache.

    The cache is deliberately process-local and TTL-based. It avoids indexing
    the same repo once per finding during a review, while still letting local
    changes refresh quickly. Set TTL to 0 to force uncached behavior.
    """

    ttl = LOCAL_REGISTRY_SETTINGS.index_cache_ttl_seconds if ttl_seconds is None else int(ttl_seconds)
    if ttl <= 0:
        return index_local_repo(root)

    repo = _repo_root(root)
    if not repo.is_dir():
        raise NotADirectoryError(str(root))
    key = str(repo)
    now = time.monotonic()

    with _INDEX_CACHE_LOCK:
        cached = _INDEX_CACHE.get(key)
        if cached and now - cached[0] <= ttl:
            return list(cached[1])

    records = index_local_repo(repo)

    with _INDEX_CACHE_LOCK:
        _INDEX_CACHE[key] = (now, records)
        max_roots = max(1, LOCAL_REGISTRY_SETTINGS.index_cache_max_roots)
        if len(_INDEX_CACHE) > max_roots:
            for old_key, _ in sorted(_INDEX_CACHE.items(), key=lambda item: item[1][0])[:len(_INDEX_CACHE) - max_roots]:
                _INDEX_CACHE.pop(old_key, None)
    return list(records)


def _record_text(record: dict[str, Any]) -> str:
    return " ".join([
        str(record.get("kind") or ""),
        str(record.get("name") or ""),
        str(record.get("path") or ""),
        str(record.get("summary") or ""),
        " ".join(str(term) for term in record.get("search_terms") or []),
    ])


def search_local_records(
    query: str,
    records: list[dict[str, Any]],
    *,
    limit: int = MAX_SEARCH_RESULTS,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
) -> list[dict[str, Any]]:
    """Rank candidate local records for a query using deterministic lexical overlap."""
    query_tokens = _tokens(query)
    scored: list[tuple[int, dict[str, Any]]] = []
    for record in records:
        record_tokens = _tokens(_record_text(record))
        overlap = query_tokens & record_tokens
        edge_fit = _edge_fit(
            record,
            requested_input=requested_input,
            requested_output=requested_output,
            query_tokens=query_tokens,
        )
        edge_score = 0
        if edge_fit["fit_class"] == FIT_EXACT_MATCH:
            edge_score += LOCAL_REGISTRY_SETTINGS.edge_exact_score_boost
        elif edge_fit["fit_class"] == FIT_DETERMINISTIC_EDIT_MATCH:
            edge_score += LOCAL_REGISTRY_SETTINGS.edge_mutation_score_boost
        if edge_fit.get("query_mutation_hints"):
            edge_score += LOCAL_REGISTRY_SETTINGS.edge_query_mutation_score_boost
        if not overlap and edge_score <= 0:
            continue
        score = len(overlap)
        name = str(record.get("name") or "").lower()
        path = str(record.get("path") or "").lower()
        kind = str(record.get("kind") or "")
        if any(token in name for token in query_tokens):
            score += LOCAL_REGISTRY_SETTINGS.exact_name_score_boost
        if any(token in path for token in query_tokens):
            score += LOCAL_REGISTRY_SETTINGS.path_score_boost
        if kind in {"python_function", "python_method"} and query_tokens & {"parse", "parser", "read", "reader"}:
            score += LOCAL_REGISTRY_SETTINGS.callable_parse_score_boost
        if kind == "python_constant" and query_tokens & {"constant", "defined", "definition", "where", "max"}:
            score += LOCAL_REGISTRY_SETTINGS.constant_score_boost
        if kind in {"package_script", "python_entrypoint"} and query_tokens & {"script", "command", "run", "cli"}:
            score += LOCAL_REGISTRY_SETTINGS.command_score_boost
        score += edge_score
        if score >= MIN_SEARCH_SCORE:
            hit = dict(record)
            hit["score"] = score
            hit["matched_terms"] = sorted(overlap)
            hit["edge_fit"] = edge_fit
            scored.append((score, hit))

    fit_priority = {FIT_EXACT_MATCH: 0, FIT_DETERMINISTIC_EDIT_MATCH: 1, "query_only": 2, FIT_INCOMPATIBLE: 9}
    scored.sort(key=lambda item: (
        fit_priority.get(str((item[1].get("edge_fit") or {}).get("fit_class")), 8),
        -item[0],
        str(item[1].get("kind")),
        str(item[1].get("path")),
        str(item[1].get("name")),
    ))
    return [hit for _, hit in scored[:limit]]


def search_local_repo(
    query: str,
    root: str | Path,
    *,
    limit: int = MAX_SEARCH_RESULTS,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
) -> list[dict[str, Any]]:
    """Index and search an explicit repo root in one call."""
    return search_local_records(
        query,
        cached_index_local_repo(root),
        limit=limit,
        requested_input=requested_input,
        requested_output=requested_output,
    )


def _primitive_slug(record: dict[str, Any]) -> str:
    path_slug = re.sub(r"[^a-z0-9]+", ".", str(record.get("path") or "").lower()).strip(".")
    name_slug = re.sub(r"[^a-z0-9]+", "_", str(record.get("name") or "").lower()).strip("_")
    return ".".join(part for part in (path_slug, name_slug) if part)[:LOCAL_REGISTRY_SETTINGS.record_id_slug_chars] or "local.record"


def _contract_for_local_record(record: dict[str, Any]) -> dict[str, str]:
    kind = str(record.get("kind") or "")
    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        contract = metadata.get("contract")
        if (
            isinstance(contract, dict)
            and isinstance(contract.get("input"), str)
            and isinstance(contract.get("output"), str)
        ):
            return {"input": contract["input"], "output": contract["output"]}
    if kind in {"python_function", "python_method"}:
        return {"input": "PythonCallArgs", "output": "PythonReturnValue"}
    if kind == "python_class":
        return {"input": "PythonConstructorArgs", "output": "PythonObject"}
    if kind == "python_constant":
        return {"input": "None", "output": "ConfigValue"}
    if kind in {"package_script", "python_entrypoint"}:
        return {"input": "CommandInvocation", "output": "CommandReceipt"}
    if kind == "claude_project_context":
        return {"input": "ProjectContextQuery", "output": "ProjectInstructionPackRef"}
    if kind == "claude_skill":
        return {"input": "CapabilityIntent", "output": "SkillProcedureRef"}
    if kind == "claude_command":
        return {"input": "CommandIntent", "output": "WorkflowTemplateRef"}
    if kind in {"claude_hook_doc", "claude_hooks_overview"}:
        return {"input": "HookEvent", "output": "HookPolicyRef"}
    if kind == "mcp_connector_doc":
        return {"input": "MCPConnectionIntent", "output": "MCPConnectorProfileRef"}
    if kind == "session_memory_doc":
        return {"input": "SessionQuery", "output": "SessionMemoryRef"}
    if kind == "doc_snippet":
        return {"input": "ContextQuery", "output": "ContextSnippetRef"}
    return {"input": "LocalRepoEvidence", "output": "PrimitiveRecordDraft"}


def _contract_tokens(text: str) -> set[str]:
    return _tokens(str(text).replace("[", " ").replace("]", " ").replace(",", " ").replace(":", " "))


def _contract_fields(text: str) -> list[str]:
    raw = str(text or "")
    fields: list[str] = []
    if raw.startswith("Args[") and raw.endswith("]"):
        body = raw[5:-1]
        for part in body.split(","):
            name = part.split(":", 1)[0].strip().lstrip("*")
            if name:
                fields.append(name)
    elif ":" in raw and not raw.startswith(("list[", "dict[", "tuple[", "set[")):
        fields.append(raw.split(":", 1)[0].strip().lstrip("*"))
    return sorted(set(field for field in fields if field))


def _contract_shape(text: str) -> str:
    raw = str(text or "Unknown").strip()
    low = raw.lower().replace("typing.", "")
    if low in {"", "any", "unknown"}:
        return "unknown"
    if low == "none":
        return "none"
    if low.startswith(("list[", "sequence[", "tuple[", "set[")) or low in {"list", "sequence", "array"}:
        return "sequence"
    if low.startswith(("dict[", "mapping[", "record[", "args[")) or low in {"dict", "mapping", "object", "record"}:
        return "object"
    if low.endswith("ref") or "artifact" in low:
        return "reference"
    return "scalar"


def _edge_descriptor(edge_kind: str, contract_text: str) -> dict[str, Any]:
    """Small black-box edge descriptor for LLMs and deterministic matching."""

    shape = _contract_shape(contract_text)
    fields = _contract_fields(contract_text)
    return {
        "edge": edge_kind,
        "contract": str(contract_text or "Unknown"),
        "shape": shape,
        "fields": fields,
        "tokens": sorted(_contract_tokens(contract_text)),
    }


def _mutation_option(
    mutation_id: str,
    *,
    from_edge: str,
    to_edge: str,
    proof_obligations: list[str],
    preconditions: list[str] | None = None,
    deterministic: bool = True,
) -> dict[str, Any]:
    return {
        "id": mutation_id,
        "from_edge": from_edge,
        "to_edge": to_edge,
        "deterministic": deterministic,
        "preconditions": preconditions or [],
        "proof_obligations": proof_obligations,
        "serves_truth": False,
    }


def _edge_mutation_options(input_edge: dict[str, Any], output_edge: dict[str, Any], effects: list[str]) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    if input_edge["shape"] in {"scalar", "object", "reference"} and output_edge["shape"] != "none":
        options.append(_mutation_option(
            MUTATION_SCALAR_TO_SEQUENCE,
            from_edge=f"{input_edge['contract']}->{output_edge['contract']}",
            to_edge=f"list[{input_edge['contract']}]->list[{output_edge['contract']}]",
            proof_obligations=["singleton_equivalence", "order_preserved", "error_mapping_preserved"],
            preconditions=["base primitive does not perform non-idempotent writes"],
        ))
    if output_edge["shape"] not in {"object", "unknown", "none"}:
        options.append(_mutation_option(
            MUTATION_OUTPUT_FIELD_WRAPPER,
            from_edge=output_edge["contract"],
            to_edge=f"{{value:{output_edge['contract']}}}",
            proof_obligations=["payload_preserved", "wrapper_schema_matches"],
            preconditions=["target output has exactly one requested field or explicit field name is supplied"],
        ))
    if output_edge["shape"] == "object":
        options.append(_mutation_option(
            MUTATION_FIELD_RENAME_ADAPTER,
            from_edge=output_edge["contract"],
            to_edge="object_with_renamed_fields",
            proof_obligations=["explicit_field_map_present", "schema_after_rename_matches"],
            preconditions=["field map is explicit; no name guessing"],
        ))
    if effects:
        options.append(_mutation_option(
            MUTATION_RETRY_CACHE_RATE_LIMIT_ADAPTER,
            from_edge=f"{input_edge['contract']}->{output_edge['contract']}",
            to_edge=f"{input_edge['contract']}->{output_edge['contract']}",
            proof_obligations=["retry_bounds_logged", "cache_key_safe", "rate_limit_policy_logged"],
            preconditions=["operation is idempotent or caller provides idempotency key"],
        ))
    return options


def _requested_edge(value: str | dict | None, edge_kind: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        contract = str(value.get("contract") or value.get("type") or value.get("shape") or "Unknown")
        edge = _edge_descriptor(edge_kind, contract)
        if value.get("shape"):
            edge["shape"] = str(value["shape"]).lower()
        raw_fields = value.get("fields")
        if isinstance(raw_fields, list):
            edge["fields"] = sorted(str(field).lower() for field in raw_fields)
        return edge
    text = str(value).strip()
    if not text:
        return None
    return _edge_descriptor(edge_kind, text)


def _edge_direct_compatible(candidate: dict[str, Any], requested: dict[str, Any] | None) -> bool:
    if requested is None:
        return True
    candidate_shape = candidate.get("shape")
    requested_shape = requested.get("shape")
    if requested_shape in {"unknown", "any"} or candidate_shape in {"unknown", "any"}:
        return True
    if candidate_shape == requested_shape:
        requested_fields = set(requested.get("fields") or [])
        candidate_fields = set(candidate.get("fields") or [])
        return not requested_fields or not candidate_fields or requested_fields <= candidate_fields
    if candidate_shape == "reference" and requested_shape in {"scalar", "object"}:
        return False
    return False


def _edge_fit(
    record: dict[str, Any],
    *,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
    query_tokens: set[str] | None = None,
) -> dict[str, Any]:
    contract = _contract_for_local_record(record)
    input_edge = _edge_descriptor("input", contract["input"])
    output_edge = _edge_descriptor("output", contract["output"])
    req_input = _requested_edge(requested_input, "input")
    req_output = _requested_edge(requested_output, "output")
    input_direct = _edge_direct_compatible(input_edge, req_input)
    output_direct = _edge_direct_compatible(output_edge, req_output)
    required_mutations: list[str] = []

    if req_input and req_input["shape"] == "sequence" and input_edge["shape"] in {"scalar", "object", "reference"}:
        required_mutations.append(MUTATION_SCALAR_TO_SEQUENCE)
        input_direct = True
    if req_output and req_output["shape"] == "sequence" and output_edge["shape"] != "sequence" and MUTATION_SCALAR_TO_SEQUENCE in required_mutations:
        output_direct = True
    if req_output and req_output["shape"] == "object" and not output_direct:
        req_fields = set(req_output.get("fields") or [])
        if output_edge["shape"] not in {"object", "unknown", "none"} and len(req_fields) <= 1:
            required_mutations.append(MUTATION_OUTPUT_FIELD_WRAPPER)
            output_direct = True
        elif output_edge["shape"] == "object" and req_fields and set(output_edge.get("fields") or []) and len(req_fields) == len(set(output_edge.get("fields") or [])):
            required_mutations.append(MUTATION_FIELD_RENAME_ADAPTER)
            output_direct = True

    qt = query_tokens or set()
    query_mutation_hints: list[str] = []
    if qt & {"batch", "many", "multiple", "list", "files", "rows", "items"} and input_edge["shape"] in {"scalar", "object", "reference"}:
        query_mutation_hints.append(MUTATION_SCALAR_TO_SEQUENCE)
    if qt & {"json", "object", "wrapped", "provenance", "provenanced", "packet"} and output_edge["shape"] not in {"object", "unknown", "none"}:
        query_mutation_hints.append(MUTATION_OUTPUT_FIELD_WRAPPER)

    if req_input is None and req_output is None:
        fit_class = "query_only"
    elif input_direct and output_direct and not required_mutations:
        fit_class = FIT_EXACT_MATCH
    elif input_direct and output_direct:
        fit_class = FIT_DETERMINISTIC_EDIT_MATCH
    else:
        fit_class = FIT_INCOMPATIBLE

    return {
        "fit_class": fit_class,
        "input_direct": input_direct,
        "output_direct": output_direct,
        "required_mutations": sorted(set(required_mutations)),
        "query_mutation_hints": sorted(set(query_mutation_hints)),
        "input_edge": input_edge,
        "output_edge": output_edge,
        "requested_input_edge": req_input,
        "requested_output_edge": req_output,
        "serves_truth": False,
    }


def _effects_for_local_record(record: dict[str, Any]) -> list[str]:
    kind = str(record.get("kind") or "")
    if kind in {"package_script", "python_entrypoint"}:
        return ["subprocess"]
    return []


def _fingerprints_for_local_record(record: dict[str, Any], contract: dict[str, str]) -> dict[str, str | None]:
    metadata = record.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    contract_digest = str(metadata.get("contract_digest") or f"sha256:{_sha(_canonical_json(contract), n=24)}")
    source_digest = metadata.get("source_digest")
    return {
        "source": str(source_digest) if source_digest else None,
        "contract": contract_digest,
    }


def _callable_surface_for_local_record(record: dict[str, Any]) -> dict[str, Any] | None:
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        return None
    signature = metadata.get("typed_signature") or metadata.get("signature")
    if not signature:
        return None
    return {
        "kind": record.get("kind"),
        "path": record.get("path"),
        "name": record.get("name"),
        "line": (record.get("source_ref") or {}).get("line") if isinstance(record.get("source_ref"), dict) else None,
        "signature": signature,
    }


def primitive_candidate_from_local_record(record: dict[str, Any]) -> dict[str, Any]:
    """Convert one local registry row into a source-backed primitive draft.

    The source is explicit first-party repo evidence, so this can be a
    ``primitive_draft`` candidate instead of a synthetic-only opportunity. It
    still never serves truth without later proof/promotion.
    """

    record_id = str(record.get("id") or _record_id(str(record.get("kind") or "record"), str(record.get("path") or ""), str(record.get("name") or "")))
    source_ref = dict(record.get("source_ref") or {})
    slug = _primitive_slug(record)
    contract = _contract_for_local_record(record)
    effects = _effects_for_local_record(record)
    input_edge = _edge_descriptor("input", contract["input"])
    output_edge = _edge_descriptor("output", contract["output"])
    mutation_options = _edge_mutation_options(input_edge, output_edge, effects)
    fingerprints = _fingerprints_for_local_record(record, contract)
    candidate = {
        "record_type": "primitive_draft",
        "candidate_schema": LOCAL_PRIMITIVE_CANDIDATE_SCHEMA,
        "candidate_stage": "primitive_draft",
        "primitive_id": f"prim:candidate:local-repo:{record_id.removeprefix('local:')}",
        "slug": slug,
        "source_candidate": f"source:local-repo:{record_id}",
        "source_surface_id": "local-repo",
        "source_kind": "first_party_repo_record",
        "source_evidence_status": "source_backed",
        "source_ref": source_ref,
        "source_fingerprints": fingerprints,
        "title": f"Local repo {record.get('kind')} {record.get('name')} primitive candidate",
        "contract": contract,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "blackbox": {
            "does": str(record.get("summary") or f"Reuse local repo {record.get('kind')} {record.get('name')}."),
            "input_edge": input_edge,
            "output_edge": output_edge,
            "side_effects": effects,
            "failure_modes": ["unknown_until_proven"],
            "mutation_options": mutation_options,
            "serves_truth": False,
        },
        "edge_mutation_options": mutation_options,
        "effects": effects,
        "memory": "artifact" if "Ref" in contract["output"] else "inline",
        "cache": "content_hash",
        "trust": "candidate",
        "readiness": "R3_contract_known",
        "license_status": "first_party_reviewed",
        "redaction_status": "reviewed_safe",
        "proof_requirements": [
            "source_ref_exists",
            "source_fingerprint_review",
            "contract_review",
            "unit_or_usage_proof",
            "privacy_boundary_review",
            "promotion_review",
        ],
        "remix_tools": sorted({option["id"] for option in mutation_options} | {"map_sequence", "output_wrapper"}),
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
    }
    surface = _callable_surface_for_local_record(record)
    if surface:
        candidate["callable_surface"] = surface
    candidate["source_fingerprints"]["primitive_record"] = f"sha256:{_sha(_canonical_json(candidate), n=24)}"
    return candidate


def _eligible_primitive_record(record: dict[str, Any]) -> bool:
    path = str(record.get("path") or "")
    parts = {part for part in path.split("/") if part}
    if parts & PRIMITIVE_SKIP_DIRS:
        return False
    name = str(record.get("name") or "")
    if name.startswith("test_") or ".test_" in name:
        return False
    return True


def primitive_candidates_from_local_repo(root: str | Path, *, limit: int = MAX_PRIMITIVE_CANDIDATES) -> list[dict[str, Any]]:
    """Create source-backed primitive draft candidates from an explicit repo root."""

    candidates = [
        primitive_candidate_from_local_record(record)
        for record in index_local_repo(root)
        if _eligible_primitive_record(record)
    ]
    def sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
        return (
            KIND_PRIORITY.get(str(row.get("source_ref", {}).get("kind") or ""), LOCAL_REGISTRY_SETTINGS.default_kind_priority),
            str(row.get("source_ref", {}).get("path") or ""),
            str(row.get("slug") or ""),
        )

    project_setup = [
        row for row in candidates
        if str(row.get("source_ref", {}).get("kind") or "") in CLAUDE_PROJECT_KINDS
    ]
    ordinary = [
        row for row in candidates
        if str(row.get("source_ref", {}).get("kind") or "") not in CLAUDE_PROJECT_KINDS
    ]
    project_setup.sort(key=sort_key)
    ordinary.sort(key=sort_key)
    selected = project_setup + ordinary
    if limit <= 0:
        return selected
    return selected[:max(0, min(limit, MAX_PRIMITIVE_CANDIDATES))]


__all__ = [
    "cached_index_local_repo",
    "clear_local_repo_index_cache",
    "CONNECTOR_VERSION",
    "LOCAL_PRIMITIVE_CANDIDATE_SCHEMA",
    "LOCAL_REGISTRY_ID",
    "index_local_repo",
    "primitive_candidate_from_local_record",
    "primitive_candidates_from_local_repo",
    "search_local_records",
    "search_local_repo",
]
