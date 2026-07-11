#!/usr/bin/env python3
"""scripts.github_repo_report — an ADDITIVE, OFFLINE-FIRST GitHub-report ingestion slice for the Primitive
Discovery Factory. Given a LOCAL repo fixture (a directory tree, OR a JSON file describing {path: content}) it
emits `github_report` rows (schema: schemas/github_report.schema.json) across three lenses:

    repo_inventory   — files, language distribution, package manifests (pyproject.toml/package.json/…),
                       entrypoints. The "what is this repo" pass.
    primitive_mining — small PURE functions (ast), pydantic models, and openapi/postman specs (filename +
                       content heuristics) → candidate_primitives + candidate_verifiers.
    test_fixture     — pytest test files, `@pytest.mark.parametrize` case tables, fixtures (conftest / a
                       fixtures/ dir), and golden/snapshot files → candidate primitives + the
                       "N tests imply a reusable primitive" finding + golden-table verifiers.

It reuses the conventions of scripts.primitive_browser_control_harness (the capture front-end) rather than
duplicating harvesting: it does NOT crawl or harvest (that is acquisition/github_repo_harvester.py) — it
DECONSTRUCTS a fixture that is already on disk. Every emitted row is born candidate=true, serves_truth=false;
raw file bodies are NEVER stored (only path, language, digest, extracted structured units + bounded snippets);
secret-shaped strings are redacted via the harness's `redact_secrets`.

    python3 scripts/github_repo_report.py --self-test
    python3 scripts/github_repo_report.py --report ./some/repo --types repo_inventory,primitive_mining,test_fixture
    python3 scripts/github_repo_report.py --report fixture.json --types primitive_mining
    python3 scripts/github_repo_report.py --live OWNER/REPO          # behind --live; needs GH_TOKEN (else 501/skip)
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── boot: put the code roots on sys.path so `scripts.*` / `src.*` resolve, then install() (harness convention) ──
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, resource  # noqa: E402

_install()

import argparse  # noqa: E402
import ast  # noqa: E402
import datetime as _dt  # noqa: E402
import hashlib  # noqa: E402  (scripts/ MAY hash; the no-hashlib law is scoped to src/**. IDs stay canonical_id.)
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  (the ONE data-id authority)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"github_repo_report requires canonical_id; import failed: {exc}")
# REUSE (mandatory): the harness owns secret redaction — import it, never re-implement the regex.
from scripts.primitive_browser_control_harness import redact_secrets  # noqa: E402

# ── constants (single-source; NO-MAGIC-VALUES) ─────────────────────────────────────────────────────────────────
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
RECORD_TYPE = "github_report"
SCHEMA_VERSION = "2026-07-08"                      # version lives in metadata, never in an id/name
STAGED_FILENAME = "github_reports.jsonl"
_DATA_SUBDIR = "data/dev-intel/github_reports"
_SNIPPET_CAP = 400                                 # bounded, redacted snippet chars stored per unit (never the body)
_MAX_FILE_BYTES = 200_000                          # per-file read cap when loading a directory fixture
_MAX_FILES = 5000                                  # file cap when loading a directory fixture
_SMALL_FN_MAX_STMTS = 12                           # "small" pure-function ceiling (ast stmt-node count)
_SMALL_FN_MIN_STMTS = 2                            # skip empty/stub defs
_MAX_UNITS = 200                                   # cap candidates emitted per unit family (bounded rows)
_PARAMETRIZE_MIN_CASES = 2                         # >= this many cases ⇒ "tests imply a reusable primitive"

#: implemented lenses (a builder row each). The schema enum reserves ci|security|pr_issue|dependency as seams.
REPORT_TYPES_IMPLEMENTED = ("repo_inventory", "primitive_mining", "test_fixture")

# language + manifest + entrypoint lexicons (extend a row, never a parallel literal) ────────────────────────────
_EXT_LANG = {
    ".py": "Python", ".pyi": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".json": "JSON", ".toml": "TOML",
    ".yaml": "YAML", ".yml": "YAML", ".md": "Markdown", ".rst": "reStructuredText", ".txt": "Text",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".rb": "Ruby", ".php": "PHP",
    ".c": "C", ".h": "C", ".cpp": "C++", ".cc": "C++", ".hpp": "C++", ".cs": "C#", ".swift": "Swift",
    ".sh": "Shell", ".bash": "Shell", ".sql": "SQL", ".html": "HTML", ".css": "CSS", ".scss": "CSS",
    ".ipynb": "Jupyter", ".proto": "Protobuf", ".graphql": "GraphQL", ".xml": "XML", ".cfg": "Config",
    ".ini": "Config",
}
_NAME_LANG = {"Dockerfile": "Dockerfile", "Makefile": "Makefile", "Gemfile": "Ruby"}
#: manifest filename -> ecosystem
_MANIFEST_FILES = {
    "pyproject.toml": "python", "setup.py": "python", "setup.cfg": "python", "requirements.txt": "python",
    "Pipfile": "python", "package.json": "node", "package-lock.json": "node", "yarn.lock": "node",
    "pnpm-lock.yaml": "node", "Cargo.toml": "rust", "go.mod": "go", "pom.xml": "java",
    "build.gradle": "java", "Gemfile": "ruby", "composer.json": "php",
}
_ENTRYPOINT_FILES = {"__main__.py", "main.py", "app.py", "cli.py", "manage.py", "wsgi.py", "asgi.py",
                     "server.py", "index.js", "server.js", "Dockerfile", "Makefile", "Procfile"}
_MAIN_GUARD_RE = re.compile(r"""if\s+__name__\s*==\s*['"]__main__['"]""")

# purity heuristic (conservative: a false "impure" is a fine miss; a false "pure" must never happen) ─────────────
_IMPURE_ROOT_MODULES = {"os", "sys", "subprocess", "socket", "requests", "urllib", "http", "shutil",
                        "random", "time", "datetime", "logging", "sqlite3", "boto3", "aiohttp", "httpx"}
_IMPURE_CALL_NAMES = {"open", "print", "input", "exec", "eval", "compile", "system", "popen", "connect",
                      "execute", "commit", "urlopen", "sleep", "getenv", "setenv", "remove", "unlink",
                      "mkdir", "rmdir", "rename", "chmod", "kill", "fork", "spawn"}

# spec detection (openapi / postman) — filename + bounded content heuristics ────────────────────────────────────
_SPEC_FILENAME_RE = re.compile(r"(openapi|swagger)\.(json|ya?ml)$|postman_collection\.json$|asyncapi\.", re.I)
_OPENAPI_YAML_RE = re.compile(r"(?m)^\s*openapi\s*:", re.I)

# directories skipped when loading a directory fixture ─────────────────────────────────────────────────────────
_IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".mypy_cache",
                ".pytest_cache", ".ruff_cache", ".tox", ".idea", ".vscode", "target", ".next", "coverage"}
_HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options", "trace")


def _sha256(text: str) -> str:
    """Content digest for a source_hash/digest field (NOT an id). Matches the harness's helper."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


def _iso(ts: float) -> str:
    """Deterministic ISO-8601 UTC string from an epoch float (injected clock; no wall-clock under test)."""
    return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class _SecretScrubber:
    """Runs every stored string through the harness's redact_secrets and tallies the redactions, so the report
    can carry an honest `secrets_redacted` count and a risk flag. Raw bodies are never stored regardless."""

    def __init__(self) -> None:
        self.n = 0

    def clean(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return text
        cleaned, k = redact_secrets(str(text))
        self.n += k
        return cleaned

    def snippet(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return text
        return self.clean(str(text)[:_SNIPPET_CAP])


# ── the fixture: a mapping of relative path -> bounded text content (never a raw-body store downstream) ─────────
class RepoFixture:
    """A local repo rendered as {relative_path: bounded_text}. Built from a directory tree or a
    {path: content} JSON. The report stores digests + extracted units from this, never the content itself."""

    def __init__(self, files: dict[str, str], root: str = "<memory>"):
        self.files = dict(sorted(files.items()))   # deterministic iteration order
        self.root = root

    def items(self) -> list[tuple[str, str]]:
        return list(self.files.items())


def _looks_texty(path: Path) -> bool:
    return path.suffix.lower() in _EXT_LANG or path.name in _MANIFEST_FILES or path.name in _NAME_LANG


def load_repo_dir(root: Path) -> RepoFixture:
    """Walk a directory tree → RepoFixture. Skips VCS/build/vendor dirs, non-text and oversized files, and
    reads each file body-BOUNDED (never persisted; only digests + extracted units survive into a report)."""
    files: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(root).parts
        if any(part in _IGNORE_DIRS for part in rel_parts):
            continue
        if not _looks_texty(p):
            continue
        try:
            if p.stat().st_size > _MAX_FILE_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")[:_MAX_FILE_BYTES]
        except Exception:  # noqa: BLE001 — unreadable file is skipped, never fatal
            continue
        files[str(p.relative_to(root)).replace(os.sep, "/")] = text
        if len(files) >= _MAX_FILES:
            break
    return RepoFixture(files, str(root))


def load_repo_json(path: Path) -> RepoFixture:
    """Load a {path: content} JSON fixture → RepoFixture (content bounded like the directory loader)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"--report JSON must be an object of {{path: content}}: {path}")
    files = {str(k).replace("\\", "/"): str(v)[:_MAX_FILE_BYTES] for k, v in data.items()}
    return RepoFixture(files, str(path))


def load_repo(path: str | Path) -> RepoFixture:
    p = Path(path)
    if p.is_dir():
        return load_repo_dir(p)
    if p.is_file() and p.suffix == ".json":
        return load_repo_json(p)
    raise SystemExit(f"--report expects a directory tree OR a .json {{path: content}} file: {path}")


def _tree_digest(fixture: RepoFixture) -> str:
    """A deterministic content anchor over the sorted (path, file-digest) pairs — the offline stand-in for a
    git commit sha, so report_id is content-addressed and reproducible run to run."""
    body = "\n".join(f"{path}:{_sha256(text)}" for path, text in fixture.items())
    return "tree:" + _sha256(body)[7:23]           # 'tree:' + 16 hex → clearly-labelled synthetic anchor


def _language_of(path: str) -> str:
    name = os.path.basename(path)
    if name in _NAME_LANG:
        return _NAME_LANG[name]
    return _EXT_LANG.get(os.path.splitext(name)[1].lower(), "Other")


# ── ast helpers (primitive_mining + test_fixture) ──────────────────────────────────────────────────────────────
def _parse_python(text: str) -> Optional[ast.Module]:
    try:
        return ast.parse(text)
    except Exception:  # noqa: BLE001 — a syntax error is a skip, never fatal
        return None


def _call_root_attr(func: ast.AST) -> tuple[Optional[str], Optional[str]]:
    """(root_name, attr_or_name) for a Call target: os.path.join -> ('os','join'); print -> (None,'print')."""
    if isinstance(func, ast.Name):
        return None, func.id
    if isinstance(func, ast.Attribute):
        root = func.value
        while isinstance(root, ast.Attribute):
            root = root.value
        return (root.id if isinstance(root, ast.Name) else None), func.attr
    return None, None


def _is_small_pure_function(node: ast.AST) -> bool:
    """Heuristic: a module/module-level small function with a value-returning body and NO impurity signal
    (no global/nonlocal, no impure module use, no impure builtin/method call). Skips tests, dunders, and
    methods (self/cls). Conservative by design: it must never call an impure function 'pure'."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    if node.name.startswith("test_") or (node.name.startswith("__") and node.name.endswith("__")):
        return False
    first_args = node.args.posonlyargs + node.args.args
    if first_args and first_args[0].arg in ("self", "cls"):
        return False                                # a bound method is not a free pure function
    stmt_nodes = [n for n in ast.walk(node) if isinstance(n, ast.stmt)]
    if not (_SMALL_FN_MIN_STMTS <= len(stmt_nodes) <= _SMALL_FN_MAX_STMTS):
        return False
    if not any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(node)):
        return False
    for n in ast.walk(node):
        if isinstance(n, (ast.Global, ast.Nonlocal)):
            return False
        if isinstance(n, ast.Call):
            root, attr = _call_root_attr(n.func)
            if (root in _IMPURE_ROOT_MODULES) or (attr in _IMPURE_CALL_NAMES):
                return False
    return True


def _fn_signature(node: ast.AST) -> str:
    try:
        sig = f"def {node.name}({ast.unparse(node.args)})"  # includes defaults (a secret default gets redacted)
        if getattr(node, "returns", None) is not None:
            sig += f" -> {ast.unparse(node.returns)}"
        return sig
    except Exception:  # noqa: BLE001
        return f"def {getattr(node, 'name', '?')}(...)"


def _is_pydantic_model(node: ast.AST) -> bool:
    if not isinstance(node, ast.ClassDef):
        return False
    for base in node.bases:
        _, attr = _call_root_attr(base)
        if attr in ("BaseModel", "BaseSettings"):
            return True
    return False


def _pydantic_fields(node: ast.ClassDef) -> list[str]:
    out: list[str] = []
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            try:
                out.append(f"{item.target.id}: {ast.unparse(item.annotation)}")
            except Exception:  # noqa: BLE001
                out.append(item.target.id)
    return out[:30]


def _parametrize_cases(node: ast.AST) -> Optional[int]:
    """If a function carries @pytest.mark.parametrize(argnames, [case, case, ...]) return the case count."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        _, attr = _call_root_attr(dec.func)
        if attr != "parametrize":
            continue
        # the case list is the last positional arg (argnames, cases) or the first List among args
        cases = next((a for a in reversed(dec.args) if isinstance(a, (ast.List, ast.Tuple))), None)
        if cases is not None:
            return len(cases.elts)
    return None


# ── report builders (one per implemented lens; adding a lens = a new builder row) ──────────────────────────────
def _report_repo_inventory(fixture: RepoFixture, scrub: _SecretScrubber) -> dict[str, list]:
    files_meta: list[dict[str, Any]] = []
    lang_dist: dict[str, int] = {}
    manifests: list[dict[str, Any]] = []
    entrypoints: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    artifact_refs: list[dict[str, Any]] = []
    source_refs: list[dict[str, Any]] = []

    for path, text in fixture.items():
        lang = _language_of(path)
        digest = _sha256(text)
        files_meta.append({"path": path, "language": lang, "bytes": len(text), "digest": digest})
        lang_dist[lang] = lang_dist.get(lang, 0) + 1
        source_refs.append({"kind": "file", "path": path, "digest": digest})
        name = os.path.basename(path)
        if name in _MANIFEST_FILES:
            units = _extract_manifest(name, text, scrub)
            manifests.append({"path": path, "manifest_type": name, "ecosystem": _MANIFEST_FILES[name], "units": units})
            artifact_refs.append({"kind": "package_manifest", "ref": path, "ecosystem": _MANIFEST_FILES[name]})
        for ep in _entrypoints_in(path, name, text):
            entrypoints.append(ep)
            artifact_refs.append({"kind": "entrypoint", "ref": path, "signal": ep["signal"]})

    findings.append({"kind": "file_inventory", "n_files": len(files_meta), "files": files_meta[:_MAX_UNITS]})
    findings.append({"kind": "language_distribution", "distribution": dict(sorted(lang_dist.items()))})
    for m in manifests:
        findings.append({"kind": "package_manifest", **m})
    for ep in entrypoints:
        findings.append({"kind": "entrypoint", **ep})

    return {"findings": findings, "candidate_primitives": [], "candidate_verifiers": [],
            "candidate_benchmarks": [], "risk_flags": [], "artifact_refs": artifact_refs,
            "source_refs": source_refs}


def _extract_manifest(name: str, text: str, scrub: _SecretScrubber) -> dict[str, Any]:
    """Extract bounded, redacted structured units from a package manifest (no raw body)."""
    units: dict[str, Any] = {}
    try:
        if name == "package.json":
            data = json.loads(text)
            units = {"name": scrub.clean(str(data.get("name", ""))),
                     "version": str(data.get("version", "")),
                     "dependencies": sorted(list((data.get("dependencies") or {}).keys()))[:50],
                     "scripts": sorted(list((data.get("scripts") or {}).keys()))[:30]}
        elif name == "pyproject.toml":
            try:
                import tomllib  # py311 stdlib
                data = tomllib.loads(text)
                proj = data.get("project", {}) or {}
                poetry = (data.get("tool", {}) or {}).get("poetry", {}) or {}
                deps = list(proj.get("dependencies", []) or [])
                if not deps and isinstance(poetry.get("dependencies"), dict):
                    deps = sorted(poetry["dependencies"].keys())
                units = {"name": scrub.clean(str(proj.get("name") or poetry.get("name") or "")),
                         "dependencies": [scrub.clean(str(d)) for d in deps][:50],
                         "scripts": sorted(list((proj.get("scripts") or {}).keys()))[:30]}
            except Exception:  # noqa: BLE001 — fall back to a light regex
                m = re.search(r'(?m)^\s*name\s*=\s*["\']([^"\']+)', text)
                units = {"name": scrub.clean(m.group(1)) if m else "", "dependencies": [], "scripts": []}
        else:
            units = {"present": True}
    except Exception:  # noqa: BLE001
        units = {"parse_error": True}
    return units


def _entrypoints_in(path: str, name: str, text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if name in _ENTRYPOINT_FILES:
        out.append({"path": path, "signal": "entrypoint_filename"})
    if path.endswith(".py") and _MAIN_GUARD_RE.search(text):
        out.append({"path": path, "signal": "__main__ guard"})
    if name == "package.json":
        try:
            data = json.loads(text)
            if data.get("bin") or data.get("scripts"):
                out.append({"path": path, "signal": "package.json bin/scripts"})
        except Exception:  # noqa: BLE001
            pass
    if name == "pyproject.toml" and ("[project.scripts]" in text or "console_scripts" in text):
        out.append({"path": path, "signal": "pyproject console scripts"})
    return out


def _report_primitive_mining(fixture: RepoFixture, repo: str, scrub: _SecretScrubber) -> dict[str, list]:
    findings: list[dict[str, Any]] = []
    prims: list[dict[str, Any]] = []
    verifiers: list[dict[str, Any]] = []
    benchmarks: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    source_refs: list[dict[str, Any]] = []
    artifact_refs: list[dict[str, Any]] = []
    n_pure = n_models = 0

    for path, text in sorted(fixture.files.items()):
        # (a) openapi / postman specs — filename + bounded content heuristics
        spec_kind = _detect_spec(path, text)
        if spec_kind:
            source_refs.append({"kind": "spec_file", "path": path, "digest": _sha256(text)})
            artifact_refs.append({"kind": "api_spec", "ref": path, "spec_type": spec_kind})
            ops = _spec_operations(spec_kind, text)
            findings.append({"kind": "api_spec_detected", "path": path, "spec_type": spec_kind,
                             "n_operations": len(ops)})
            prims.append(_mk_primitive(repo, "primitive_mining", "api_spec", os.path.basename(path),
                                       scrub.clean(f"{spec_kind}:{path} ({len(ops)} operations)"),
                                       {"path": path, "spec_type": spec_kind}))
            for (method, route, op_id) in ops[:_MAX_UNITS]:
                prims.append(_mk_primitive(repo, "primitive_mining", "api_endpoint",
                                           op_id or f"{method} {route}",
                                           scrub.clean(f"{method} {route}"),
                                           {"path": path, "method": method, "route": route}))
            verifiers.append(_mk_verifier(repo, "primitive_mining", os.path.basename(path), "contract_test",
                                          "validate requests/responses against the spec schema"))
            continue

        # (b) python units — small pure functions + pydantic models (ast)
        if not path.endswith(".py"):
            continue
        tree = _parse_python(text)
        if tree is None:
            continue
        source_refs.append({"kind": "python_module", "path": path, "digest": _sha256(text)})
        for node in ast.walk(tree):
            if _is_small_pure_function(node):
                sig = scrub.snippet(_fn_signature(node))
                snippet = scrub.snippet(_safe_segment(text, node))
                prims.append(_mk_primitive(repo, "primitive_mining", "pure_function", node.name, sig,
                                           {"path": path, "lineno": getattr(node, "lineno", 0),
                                            "snippet": snippet}))
                verifiers.append(_mk_verifier(repo, "primitive_mining", node.name, "unit_property_test",
                                              "exercise on representative inputs; assert determinism/no side effects"))
                n_pure += 1
            elif _is_pydantic_model(node):
                fields = [scrub.clean(f) for f in _pydantic_fields(node)]
                prims.append(_mk_primitive(repo, "primitive_mining", "pydantic_model", node.name,
                                           scrub.clean("class " + node.name + "(" + ", ".join(fields) + ")"),
                                           {"path": path, "lineno": getattr(node, "lineno", 0), "fields": fields}))
                verifiers.append(_mk_verifier(repo, "primitive_mining", node.name, "schema_roundtrip_validation",
                                              "construct from valid/invalid payloads; assert validation behaviour"))
                n_models += 1

    findings.insert(0, {"kind": "pure_function_candidates", "count": n_pure})
    findings.insert(1, {"kind": "pydantic_model_candidates", "count": n_models})
    if prims:
        benchmarks.append(_mk_benchmark(repo, "primitive_mining", "reuse_vs_regenerate_tokens",
                                        {"n_candidate_primitives": len(prims),
                                         "note": "measure tokens to reuse the stored primitive vs regenerate it"}))
    if scrub.n:
        risks.append({"kind": "hardcoded_secret_default", "severity": "high",
                      "detail": "a secret-shaped literal was redacted from a mined unit's signature/snippet"})
    return {"findings": findings, "candidate_primitives": prims[:_MAX_UNITS], "candidate_verifiers": verifiers,
            "candidate_benchmarks": benchmarks, "risk_flags": risks, "artifact_refs": artifact_refs,
            "source_refs": source_refs}


def _safe_segment(text: str, node: ast.AST) -> Optional[str]:
    try:
        return ast.get_source_segment(text, node)
    except Exception:  # noqa: BLE001
        return None


def _detect_spec(path: str, text: str) -> Optional[str]:
    name = os.path.basename(path).lower()
    low = text[:4000].lower()
    if name.endswith("postman_collection.json") or ('"_postman_id"' in low):
        return "postman"
    if _SPEC_FILENAME_RE.search(name):
        return "openapi_yaml" if name.endswith((".yaml", ".yml")) else "openapi_json"
    if path.endswith(".json") and ('"openapi"' in low or '"swagger"' in low):
        return "openapi_json"
    if path.endswith((".yaml", ".yml")) and _OPENAPI_YAML_RE.search(text[:4000]):
        return "openapi_yaml"
    return None


def _spec_operations(spec_kind: str, text: str) -> list[tuple[str, str, Optional[str]]]:
    """Enumerate (METHOD, route, operationId) — best-effort, bounded. YAML specs are detected but not parsed
    (no yaml dependency); they still yield an api_spec candidate with n_operations=0."""
    ops: list[tuple[str, str, Optional[str]]] = []
    try:
        if spec_kind == "openapi_json":
            spec = json.loads(text)
            for route in sorted((spec.get("paths") or {}).keys()):
                methods = spec["paths"][route]
                if isinstance(methods, dict):
                    for m in sorted(methods.keys()):
                        if m.lower() in _HTTP_METHODS and isinstance(methods[m], dict):
                            ops.append((m.upper(), route, methods[m].get("operationId")))
        elif spec_kind == "postman":
            coll = json.loads(text)

            def _walk(items: Any) -> None:
                for it in items or []:
                    if isinstance(it, dict) and "item" in it:
                        _walk(it["item"])
                    elif isinstance(it, dict) and "request" in it:
                        req = it["request"]
                        method = (req.get("method") if isinstance(req, dict) else "") or "GET"
                        ops.append((method.upper(), str(it.get("name", "")), it.get("name")))
            _walk(coll.get("item"))
    except Exception:  # noqa: BLE001
        pass
    return ops


def _report_test_fixture(fixture: RepoFixture, repo: str, scrub: _SecretScrubber) -> dict[str, list]:
    findings: list[dict[str, Any]] = []
    prims: list[dict[str, Any]] = []
    verifiers: list[dict[str, Any]] = []
    benchmarks: list[dict[str, Any]] = []
    source_refs: list[dict[str, Any]] = []
    artifact_refs: list[dict[str, Any]] = []
    n_tests = n_param = n_fixtures = n_golden = 0

    for path, text in sorted(fixture.files.items()):
        name = os.path.basename(path)
        low_path = path.lower()

        # golden / snapshot files (data fixtures a test asserts against)
        if _is_golden_file(low_path, name):
            findings.append({"kind": "golden_snapshot_file", "path": path, "digest": _sha256(text)})
            artifact_refs.append({"kind": "golden_snapshot", "ref": path})
            n_golden += 1

        # a fixtures/ directory member (non-python data used by tests)
        if ("/fixtures/" in "/" + low_path or low_path.startswith("fixtures/")) and not path.endswith(".py"):
            findings.append({"kind": "fixture_file", "path": path, "digest": _sha256(text)})
            n_fixtures += 1

        if not path.endswith(".py"):
            continue

        is_test_file = name.startswith("test_") or name.endswith("_test.py")
        is_conftest = name == "conftest.py"
        tree = _parse_python(text)
        has_pytest = ("import pytest" in text) or ("from pytest" in text)

        if is_test_file and (has_pytest or (tree and _has_test_func(tree))):
            findings.append({"kind": "pytest_test_file", "path": path, "digest": _sha256(text)})
            source_refs.append({"kind": "pytest_test_file", "path": path, "digest": _sha256(text)})
            n_tests += 1

        if tree is None:
            continue

        # pytest fixtures (conftest.py or @pytest.fixture-decorated defs)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_pytest_fixture(node):
                findings.append({"kind": "pytest_fixture", "path": path, "name": node.name})
                n_fixtures += 1
            cases = _parametrize_cases(node)
            if cases is not None:
                n_param += 1
                target = _target_from_test_name(node.name)
                findings.append({"kind": "parametrize_cases", "path": path, "test": node.name,
                                 "n_cases": cases, "implied_target": target})
                if cases >= _PARAMETRIZE_MIN_CASES:
                    findings.append({"kind": "tests_imply_reusable_primitive", "path": path, "test": node.name,
                                     "n_cases": cases, "implied_primitive": target,
                                     "detail": f"{cases} parametrized cases over {node.name} imply a reusable "
                                               f"primitive ({target}) backed by a golden case table"})
                    prims.append(_mk_primitive(repo, "test_fixture", "test_backed_primitive", target,
                                               scrub.clean(f"{target} — {cases} golden cases from {node.name}"),
                                               {"path": path, "test": node.name, "n_cases": cases}))
                    verifiers.append(_mk_verifier(repo, "test_fixture", target, "golden_case_table",
                                                  f"replay the {cases} parametrized (input, expected) rows"))
                    benchmarks.append(_mk_benchmark(repo, "test_fixture", "golden_regression",
                                                    {"target": target, "n_cases": cases}))
        if is_conftest:
            findings.append({"kind": "conftest", "path": path})
            artifact_refs.append({"kind": "conftest", "ref": path})

    findings.insert(0, {"kind": "test_surface_summary", "n_test_files": n_tests, "n_parametrized_tests": n_param,
                        "n_fixtures": n_fixtures, "n_golden_snapshot_files": n_golden})
    return {"findings": findings, "candidate_primitives": prims[:_MAX_UNITS], "candidate_verifiers": verifiers,
            "candidate_benchmarks": benchmarks, "risk_flags": [], "artifact_refs": artifact_refs,
            "source_refs": source_refs}


def _is_golden_file(low_path: str, name: str) -> bool:
    if any(seg in low_path for seg in ("/__snapshots__/", "/snapshots/")):
        return True
    if low_path.endswith((".golden", ".snap", ".ambr")):
        return True
    return any(tok in name.lower() for tok in ("golden", "expected", "snapshot")) and not name.endswith(".py")


def _has_test_func(tree: ast.Module) -> bool:
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
               for n in ast.walk(tree))


def _is_pytest_fixture(node: ast.AST) -> bool:
    for dec in getattr(node, "decorator_list", []):
        _, attr = _call_root_attr(dec.func if isinstance(dec, ast.Call) else dec)
        if attr == "fixture":
            return True
    return False


def _target_from_test_name(test_name: str) -> str:
    return re.sub(r"^test_", "", test_name) or test_name


# ── row minting (every candidate born candidate=true, serves_truth=false; ids via canonical_id) ────────────────
def _mk_primitive(repo: str, report_type: str, kind: str, name: str, signature: Optional[str],
                  source_ref: dict[str, Any]) -> dict[str, Any]:
    pid = canonical_id("ghprim", repo, report_type, kind, name, source_ref.get("path", ""))
    return {"primitive_id": pid, "record_type": "github_report_candidate_primitive", "kind": kind,
            "name": name, "signature": signature, "source_ref": source_ref, **BOUNDARY}


def _mk_verifier(repo: str, report_type: str, target: str, kind: str, obligation: str) -> dict[str, Any]:
    vid = canonical_id("ghverify", repo, report_type, target, kind)
    return {"verifier_id": vid, "kind": kind, "target": target, "proof_obligation": obligation, **BOUNDARY}


def _mk_benchmark(repo: str, report_type: str, kind: str, detail: dict[str, Any]) -> dict[str, Any]:
    bid = canonical_id("ghbench", repo, report_type, kind)
    return {"benchmark_id": bid, "kind": kind, "detail": detail, **BOUNDARY}


_BUILDERS: dict[str, Callable[..., dict[str, list]]] = {
    "repo_inventory": lambda fx, repo, scrub: _report_repo_inventory(fx, scrub),
    "primitive_mining": lambda fx, repo, scrub: _report_primitive_mining(fx, repo, scrub),
    "test_fixture": lambda fx, repo, scrub: _report_test_fixture(fx, repo, scrub),
}


def build_report(fixture: RepoFixture, report_type: str, *, repo: str, commit_sha: str, generated_at: str) -> dict[str, Any]:
    """Build ONE github_report row for one lens. Stamps the common envelope + BOUNDARY + a canonical report_id,
    threads a secret scrubber through every stored string, and records the tree anchor as provenance."""
    if report_type not in _BUILDERS:
        raise SystemExit(f"report_type '{report_type}' not implemented; implemented: {REPORT_TYPES_IMPLEMENTED}")
    scrub = _SecretScrubber()
    parts = _BUILDERS[report_type](fixture, repo, scrub)
    source_refs = [{"kind": "tree_anchor", "path": None, "digest": commit_sha}] + parts["source_refs"]
    risk_flags = list(parts["risk_flags"])
    if scrub.n and not any(r.get("kind") == "hardcoded_secret_default" for r in risk_flags):
        risk_flags.append({"kind": "secret_redacted", "severity": "medium", "count": scrub.n})
    report = {
        "report_id": canonical_id("ghreport", repo, report_type, commit_sha),
        "record_type": RECORD_TYPE,
        "repo": repo,
        "commit_sha": commit_sha,
        "report_type": report_type,
        "schema_version": SCHEMA_VERSION,
        "source_refs": source_refs,
        "generated_at": generated_at,
        "findings": parts["findings"],
        "candidate_primitives": parts["candidate_primitives"],
        "candidate_verifiers": parts["candidate_verifiers"],
        "candidate_benchmarks": parts["candidate_benchmarks"],
        "risk_flags": risk_flags,
        "artifact_refs": parts["artifact_refs"],
        "secrets_redacted": scrub.n,
        **BOUNDARY,
    }
    return report


def build_reports(fixture: RepoFixture, *, types: list[str], repo: str, commit_sha: Optional[str],
                  clock: Callable[[], float]) -> list[dict[str, Any]]:
    """Build one report per requested lens. `clock` is INJECTED (deterministic under test); commit_sha defaults
    to the deterministic tree anchor so report_ids are reproducible offline."""
    anchor = commit_sha or _tree_digest(fixture)
    generated_at = _iso(clock())
    return [build_report(fixture, t, repo=repo, commit_sha=anchor, generated_at=generated_at) for t in types]


def write_reports(rows: list[dict[str, Any]], out_path: Optional[Path] = None) -> Path:
    out_path = out_path or (resource(_DATA_SUBDIR) / STAGED_FILENAME)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return out_path


# ── live GitHub REST (behind --live; NEVER exercised by --self-test) ───────────────────────────────────────────
def _gh_get(url: str, token: str) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "aidoneright-github-report",
                                               "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def live_repo_inventory(owner_repo: str, *, clock: Callable[[], float]) -> list[dict[str, Any]]:
    """Fetch a live repo's tree (paths only, NO bodies) → a single repo_inventory report. Needs GH_TOKEN;
    returns [] (501/skip) without one. Body-dependent lenses (mining/tests) require fetching file contents and
    are intentionally not enabled here to avoid rate-limit + secret exposure."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("501 live GitHub ingestion requires GH_TOKEN/GITHUB_TOKEN — skipping (offline is the default path).")
        return []
    try:
        meta = _gh_get(f"https://api.github.com/repos/{owner_repo}", token)
        sha_ref = meta.get("default_branch", "HEAD")
        tree = _gh_get(f"https://api.github.com/repos/{owner_repo}/git/trees/{sha_ref}?recursive=1", token)
    except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:  # noqa: BLE001
        print(f"501 live fetch failed for {owner_repo}: {type(exc).__name__}: {exc}")
        return []
    # build a paths-only fixture (empty bodies → digests are of the path list, not any content)
    files = {e["path"]: "" for e in tree.get("tree", []) if e.get("type") == "blob"}
    fixture = RepoFixture(files, owner_repo)
    scrub = _SecretScrubber()
    parts = _report_repo_inventory(fixture, scrub)
    generated_at = _iso(clock())
    commit_sha = str(meta.get("default_branch", "")) + ":tree"
    report = build_report(fixture, "repo_inventory", repo=owner_repo, commit_sha=commit_sha,
                          generated_at=generated_at)
    report["risk_flags"].append({"kind": "live_body_fetch_not_enabled", "severity": "low",
                                 "detail": "inventory built from the tree listing; file bodies not fetched"})
    return [report]


# ── self-test: OFFLINE, DETERMINISTIC (injected clock), MUTATION-GATED ─────────────────────────────────────────
_SECRET = "sk-live-SHOULDNOTLEAK0123456789"        # secret-shaped literal planted in the fixture (must be redacted)
_BODY_MARKER = "BODYMARKER_RAW_BODY_MUST_NOT_BE_STORED"

_FIXTURE_CORE = f'''"""demo module. {_BODY_MARKER}"""
from pydantic import BaseModel


def add_numbers(a: int, b: int, token: str = "{_SECRET}") -> int:
    result = a + b
    return result


class Widget(BaseModel):
    id: int
    name: str


if __name__ == "__main__":
    print(add_numbers(1, 2))
'''

_FIXTURE_TEST = '''import pytest

from mymod.core import add_numbers


@pytest.mark.parametrize("a,b,expected", [(1, 2, 3), (2, 3, 5), (10, 20, 30)])
def test_add_numbers(a, b, expected):
    assert add_numbers(a, b) == expected
'''

_FIXTURE_CONFTEST = '''import pytest


@pytest.fixture
def sample_widget():
    return {"id": 1, "name": "w"}
'''

_FIXTURE_OPENAPI = ('{"openapi": "3.0.0", "info": {"title": "Demo", "version": "1.0.0"}, '
                    '"paths": {"/widgets": {"get": {"operationId": "listWidgets"}}, '
                    '"/widgets/{id}": {"get": {"operationId": "getWidget"}}}}')

_FIXTURE_PYPROJECT = '''[project]
name = "mymod"
version = "0.1.0"
dependencies = ["pydantic>=2", "httpx"]

[project.scripts]
mymod = "mymod.core:main"
'''

_FIXTURE_FILES = {
    "pyproject.toml": _FIXTURE_PYPROJECT,
    "src/mymod/core.py": _FIXTURE_CORE,
    "openapi.json": _FIXTURE_OPENAPI,
    "tests/test_core.py": _FIXTURE_TEST,
    "tests/conftest.py": _FIXTURE_CONFTEST,
    "tests/fixtures/expected_result.json": '{"result": 3}',
    "README.md": "# mymod\\nA demo repo.\\n",
}


def _write_fixture(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def self_test() -> int:
    import tempfile

    checks: list[tuple[str, bool]] = []
    # injected clock — deterministic, no wall-clock (the verify/naming laws forbid Date.now-style seeds)
    fixed_clock: Callable[[], float] = lambda: 1_700_000_000.0  # noqa: E731  → 2023-11-14T22:13:20Z

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        _write_fixture(root, _FIXTURE_FILES)
        fixture = load_repo(root)
        reports = build_reports(fixture, types=list(REPORT_TYPES_IMPLEMENTED), repo="mymod",
                                commit_sha=None, clock=fixed_clock)
        by_type = {r["report_type"]: r for r in reports}
        blob = json.dumps(reports, sort_keys=True)

        inv = by_type["repo_inventory"]
        inv_kinds = {f["kind"] for f in inv["findings"]}
        lang_dist = next(f["distribution"] for f in inv["findings"] if f["kind"] == "language_distribution")
        checks.append(("repo_inventory: language distribution has Python + JSON",
                       lang_dist.get("Python", 0) >= 1 and lang_dist.get("JSON", 0) >= 1))
        checks.append(("repo_inventory: pyproject.toml manifest detected (name=mymod)",
                       any(f["kind"] == "package_manifest" and f.get("manifest_type") == "pyproject.toml"
                           and (f.get("units") or {}).get("name") == "mymod" for f in inv["findings"])))
        checks.append(("repo_inventory: entrypoint detected (__main__ guard or console script)",
                       "entrypoint" in inv_kinds))
        checks.append(("repo_inventory: files carry digests, raw body NOT stored",
                       _BODY_MARKER not in json.dumps(inv) and
                       all(fm.get("digest", "").startswith("sha256:")
                           for f in inv["findings"] if f["kind"] == "file_inventory" for fm in f["files"])))

        mining = by_type["primitive_mining"]
        prim_by_kind: dict[str, list] = {}
        for p in mining["candidate_primitives"]:
            prim_by_kind.setdefault(p["kind"], []).append(p)
        checks.append(("primitive_mining: small pure function add_numbers mined",
                       any(p["name"] == "add_numbers" for p in prim_by_kind.get("pure_function", []))))
        checks.append(("primitive_mining: pydantic model Widget mined",
                       any(p["name"] == "Widget" for p in prim_by_kind.get("pydantic_model", []))))
        checks.append(("primitive_mining: openapi spec detected with 2 operations + 2 endpoint primitives",
                       any(f["kind"] == "api_spec_detected" and f["n_operations"] == 2 for f in mining["findings"])
                       and len(prim_by_kind.get("api_endpoint", [])) == 2))
        checks.append(("primitive_mining: a contract_test verifier emitted for the spec",
                       any(v["kind"] == "contract_test" for v in mining["candidate_verifiers"])))
        checks.append(("primitive_mining: pure-function verifier + reuse benchmark emitted",
                       any(v["kind"] == "unit_property_test" for v in mining["candidate_verifiers"])
                       and any(b["kind"] == "reuse_vs_regenerate_tokens" for b in mining["candidate_benchmarks"])))

        tf = by_type["test_fixture"]
        tf_kinds = {f["kind"] for f in tf["findings"]}
        param = next((f for f in tf["findings"] if f["kind"] == "parametrize_cases"), None)
        checks.append(("test_fixture: pytest test file detected", "pytest_test_file" in tf_kinds))
        checks.append(("test_fixture: @pytest.mark.parametrize counted 3 cases",
                       param is not None and param["n_cases"] == 3))
        checks.append(("test_fixture: 'N tests imply a reusable primitive' finding present (target add_numbers)",
                       any(f["kind"] == "tests_imply_reusable_primitive" and f["implied_primitive"] == "add_numbers"
                           for f in tf["findings"])))
        checks.append(("test_fixture: test-backed candidate primitive + golden_case_table verifier",
                       any(p["kind"] == "test_backed_primitive" and p["name"] == "add_numbers"
                           for p in tf["candidate_primitives"])
                       and any(v["kind"] == "golden_case_table" for v in tf["candidate_verifiers"])))
        checks.append(("test_fixture: pytest fixture + fixtures/ file + golden/snapshot file detected",
                       "pytest_fixture" in tf_kinds and "fixture_file" in tf_kinds
                       and "golden_snapshot_file" in tf_kinds))

        # candidate-only boundary — report AND every nested candidate
        def _boundary_ok(rows: list[dict]) -> bool:
            return all(r.get("candidate") is True and r.get("serves_truth") is False for r in rows)
        nested = [c for r in reports for key in ("candidate_primitives", "candidate_verifiers",
                                                 "candidate_benchmarks") for c in r[key]]
        checks.append(("candidate-only: every report + every nested candidate is candidate=true, serves_truth=false",
                       _boundary_ok(reports) and _boundary_ok(nested) and len(nested) > 0))

        checks.append(("ids: report_id is canonical_id-shaped (ghreport-<16 hex>)",
                       all(re.fullmatch(r"ghreport-[0-9a-f]{16}", r["report_id"]) for r in reports)))

        # SECRET redaction — the planted secret survives NOWHERE; the mining report tallies + risk-flags it
        checks.append(("secret redaction: planted sk- secret appears in NO row; mining tallies + risk-flags it",
                       _SECRET not in blob and mining["secrets_redacted"] >= 1
                       and any(r["kind"] in ("hardcoded_secret_default", "secret_redacted")
                               for r in mining["risk_flags"])))

        # DETERMINISM — same fixture + same clock ⇒ byte-identical
        reports2 = build_reports(fixture, types=list(REPORT_TYPES_IMPLEMENTED), repo="mymod",
                                 commit_sha=None, clock=fixed_clock)
        checks.append(("determinism: two builds are byte-identical",
                       json.dumps(reports, sort_keys=True) == json.dumps(reports2, sort_keys=True)))

        # writer — append to a TEMP path (never the real data dir); every written line parses + is candidate-only
        out = write_reports(reports, Path(tmp) / STAGED_FILENAME)
        written = [json.loads(ln) for ln in out.read_text().splitlines() if ln.strip()]
        checks.append(("writer: rows append to jsonl, parse back, candidate-only",
                       len(written) == len(reports) and _boundary_ok(written)))

        # MUTATION GATE — an injected defect must flip a result: make add_numbers IMPURE (os.system) and it must
        # NO LONGER be mined as a pure_function (a detector that called everything 'pure' would fail here).
        mutated = dict(_FIXTURE_FILES)
        mutated["src/mymod/core.py"] = _FIXTURE_CORE.replace(
            "    result = a + b\n    return result",
            "    import os\n    os.system('echo side-effect')\n    return a + b")
        mroot = Path(tmp) / "mutated"
        _write_fixture(mroot, mutated)
        m_reports = build_reports(load_repo(mroot), types=["primitive_mining"], repo="mymod",
                                  commit_sha=None, clock=fixed_clock)
        m_pure = [p for p in m_reports[0]["candidate_primitives"]
                  if p["kind"] == "pure_function" and p["name"] == "add_numbers"]
        checks.append(("MUTATION GATE: an impure add_numbers is NOT mined as a pure function (detector discriminates)",
                       len(m_pure) == 0))

    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    n_prim = sum(len(r["candidate_primitives"]) for r in reports)
    print(("PASS" if ok else "FAIL") + f" - github_repo_report: offline fixture → {len(reports)} github_report "
          f"rows across {REPORT_TYPES_IMPLEMENTED}, {n_prim} candidate primitives, deterministic + "
          "secret-redacted + candidate-only (serves_truth=false); mutation gate discriminates.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Offline-first GitHub-report ingestion (candidate-only, serves_truth=false).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", metavar="DIR|FILE.json", help="local repo directory tree OR a {path:content} .json fixture")
    ap.add_argument("--types", default=",".join(REPORT_TYPES_IMPLEMENTED),
                    help=f"comma list of report types (implemented: {','.join(REPORT_TYPES_IMPLEMENTED)})")
    ap.add_argument("--repo", default=None, help="repo label to stamp (default: basename of --report)")
    ap.add_argument("--commit-sha", default=None, help="git sha to stamp (default: deterministic tree anchor)")
    ap.add_argument("--live", metavar="OWNER/REPO", help="fetch a LIVE GitHub repo tree (needs GH_TOKEN; repo_inventory only)")
    ap.add_argument("--out", default=None, help="output jsonl path (default: staged github_reports.jsonl)")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    clock: Callable[[], float] = time.time
    if args.live:
        rows = live_repo_inventory(args.live, clock=clock)
        if not rows:
            return 0
        path = write_reports(rows, Path(args.out) if args.out else None)
        print(f"live: wrote {len(rows)} repo_inventory report(s) for {args.live} → {path}")
        return 0

    if args.report:
        types = [t.strip() for t in args.types.split(",") if t.strip()]
        bad = [t for t in types if t not in REPORT_TYPES_IMPLEMENTED]
        if bad:
            raise SystemExit(f"unimplemented report type(s) {bad}; implemented: {REPORT_TYPES_IMPLEMENTED}")
        fixture = load_repo(args.report)
        repo = args.repo or Path(args.report).stem
        rows = build_reports(fixture, types=types, repo=repo, commit_sha=args.commit_sha, clock=clock)
        path = write_reports(rows, Path(args.out) if args.out else None)
        n_prim = sum(len(r["candidate_primitives"]) for r in rows)
        n_files = len(fixture.files)
        print(f"ingested {n_files} files from '{args.report}' → {len(rows)} report(s), {n_prim} candidate "
              f"primitives (candidate-only) → {path}")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
