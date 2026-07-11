"""knowledge.code_genome — the Code Genome (the owner's §9).

Every codebase decomposes into recurring architectural PRIMITIVES (auth, db_connection, api_wrapper, retry, cache,
pagination, queue_worker, logging_middleware, rate_limiter, schema_validator, file_uploader, ...). Each repo becomes
'DNA' — a fingerprint over which primitives it contains — and we measure software similarity ('Repo A is 81% similar
to Repo C') and, crucially, 'your new module is genome-identical to 3,700 existing repos.'

Deterministic decomposition (signal patterns per primitive; a tree-sitter/semgrep AST pass is the higher-fidelity
fork for real source). The fingerprint is a presence/weight vector over the canonical primitive list (single-sourced
here, no magic). serves_truth=false; similarity is a governed signal, not an assertion.
"""
from __future__ import annotations

import ast
import math
import re

#: canonical architectural primitives (the 'genes'). Single source — fingerprints index THIS order.
py_const_src_teleon_knowledge_code_genome__PRIMITIVES: dict[str, list[str]] = {
    "authentication": ["auth", "login", "oauth", "jwt", "password", "session token"],
    "db_connection": ["database", "db connection", "connection pool", "sqlalchemy", "psycopg", "orm"],
    "api_wrapper": ["api client", "http client", "requests.", "httpx", "fetch(", "rest client"],
    "retry": ["retry", "backoff", "tenacity", "max attempts"],
    "cache": ["cache", "memoize", "lru_cache", "redis"],
    "pagination": ["paginate", "pagination", "page size", "offset", "cursor page"],
    "queue_worker": ["queue", "worker", "celery", "task queue", "consumer"],
    "logging_middleware": ["logging", "logger", "log middleware", "structlog"],
    "rate_limiter": ["rate limit", "throttle", "token bucket", "leaky bucket"],
    "schema_validator": ["schema", "validate", "pydantic", "jsonschema", "marshmallow"],
    "file_uploader": ["upload", "multipart", "presigned", "file storage", "s3 put"],
    "scheduler": ["schedule", "cron", "interval", "periodic task"],
}
py_var_src_teleon_knowledge_code_genome___PRIMITIVE_ORDER = list(py_const_src_teleon_knowledge_code_genome__PRIMITIVES)


def py_function_src_teleon_knowledge_code_genome__decompose(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__decompose__text: str) -> list[str]:
    """Which architectural primitives are present in this code/description (deterministic signal scan)."""
    py_local_src_teleon_knowledge_code_genome__decompose__low = (py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__decompose__text or "").lower()
    return [name for name, tells in py_const_src_teleon_knowledge_code_genome__PRIMITIVES.items() if any(re.search(re.escape(t), py_local_src_teleon_knowledge_code_genome__decompose__low) for t in tells)]


def py_function_src_teleon_knowledge_code_genome__fingerprint(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__fingerprint__text: str) -> list[float]:
    """A genome fingerprint: a vector over the canonical primitive list (1.0 where the primitive is present)."""
    py_local_src_teleon_knowledge_code_genome__fingerprint__present = set(py_function_src_teleon_knowledge_code_genome__decompose(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__fingerprint__text))
    return [1.0 if name in py_local_src_teleon_knowledge_code_genome__fingerprint__present else 0.0 for name in py_var_src_teleon_knowledge_code_genome___PRIMITIVE_ORDER]


def py_function_src_teleon_knowledge_code_genome__genome_similarity(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_a: list[float], py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_b: list[float]) -> float:
    """Cosine similarity between two genome fingerprints (software similarity %)."""
    if not py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_a or not py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_b or len(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_a) != len(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_b):
        return 0.0
    py_local_src_teleon_knowledge_code_genome__genome_similarity__dot = sum(x * y for x, y in zip(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_a, py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_b))
    py_local_src_teleon_knowledge_code_genome__genome_similarity__na = math.sqrt(sum(x * x for x in py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_a))
    py_local_src_teleon_knowledge_code_genome__genome_similarity__nb = math.sqrt(sum(y * y for y in py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__genome_similarity__fp_b))
    return py_local_src_teleon_knowledge_code_genome__genome_similarity__dot / (py_local_src_teleon_knowledge_code_genome__genome_similarity__na * py_local_src_teleon_knowledge_code_genome__genome_similarity__nb) if py_local_src_teleon_knowledge_code_genome__genome_similarity__na and py_local_src_teleon_knowledge_code_genome__genome_similarity__nb else 0.0


def py_function_src_teleon_knowledge_code_genome__decompose_ast(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__decompose_ast__source: str) -> list[str]:
    """Higher-fidelity decomposition: parse Python source and read only REAL symbols (imports, call names, def/class
    names) — so a primitive merely mentioned in a comment/string does NOT count (the precision win over the prose
    scan). Falls back to the signal scan on a syntax error (partial snippets). tree-sitter is the multi-language fork."""
    try:
        py_local_src_teleon_knowledge_code_genome__decompose_ast__tree = ast.parse(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__decompose_ast__source)
    except SyntaxError:
        return py_function_src_teleon_knowledge_code_genome__decompose(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__decompose_ast__source)
    py_local_src_teleon_knowledge_code_genome__decompose_ast__names: set[str] = set()
    for py_local_src_teleon_knowledge_code_genome__decompose_ast__node in ast.walk(py_local_src_teleon_knowledge_code_genome__decompose_ast__tree):
        if isinstance(py_local_src_teleon_knowledge_code_genome__decompose_ast__node, ast.Import):
            py_local_src_teleon_knowledge_code_genome__decompose_ast__names.update(a.name.split(".")[0] for a in py_local_src_teleon_knowledge_code_genome__decompose_ast__node.names)
        elif isinstance(py_local_src_teleon_knowledge_code_genome__decompose_ast__node, ast.ImportFrom):
            py_local_src_teleon_knowledge_code_genome__decompose_ast__names.add((py_local_src_teleon_knowledge_code_genome__decompose_ast__node.module or "").split(".")[0])
        elif isinstance(py_local_src_teleon_knowledge_code_genome__decompose_ast__node, ast.Call):
            py_local_src_teleon_knowledge_code_genome__decompose_ast__f = py_local_src_teleon_knowledge_code_genome__decompose_ast__node.func
            if isinstance(py_local_src_teleon_knowledge_code_genome__decompose_ast__f, ast.Name):
                py_local_src_teleon_knowledge_code_genome__decompose_ast__names.add(py_local_src_teleon_knowledge_code_genome__decompose_ast__f.id)
            elif isinstance(py_local_src_teleon_knowledge_code_genome__decompose_ast__f, ast.Attribute):
                py_local_src_teleon_knowledge_code_genome__decompose_ast__names.add(py_local_src_teleon_knowledge_code_genome__decompose_ast__f.attr)
        elif isinstance(py_local_src_teleon_knowledge_code_genome__decompose_ast__node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            py_local_src_teleon_knowledge_code_genome__decompose_ast__names.add(py_local_src_teleon_knowledge_code_genome__decompose_ast__node.name)
    py_local_src_teleon_knowledge_code_genome__decompose_ast__hay = " ".join(n.lower() for n in py_local_src_teleon_knowledge_code_genome__decompose_ast__names if n)
    return [name for name, tells in py_const_src_teleon_knowledge_code_genome__PRIMITIVES.items()
            if any(re.search(rf"\b{re.escape(t.split()[0])}", py_local_src_teleon_knowledge_code_genome__decompose_ast__hay) for t in tells)]


def py_function_src_teleon_knowledge_code_genome__ast_fingerprint(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__ast_fingerprint__source: str) -> list[float]:
    """A genome fingerprint from the AST decomposition (symbol-level, comment/string-immune)."""
    py_local_src_teleon_knowledge_code_genome__ast_fingerprint__present = set(py_function_src_teleon_knowledge_code_genome__decompose_ast(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__ast_fingerprint__source))
    return [1.0 if name in py_local_src_teleon_knowledge_code_genome__ast_fingerprint__present else 0.0 for name in py_var_src_teleon_knowledge_code_genome___PRIMITIVE_ORDER]


def py_function_src_teleon_knowledge_code_genome__nearest_genomes(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__nearest_genomes__text: str, py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__nearest_genomes__corpus: list[dict], *, py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__nearest_genomes__limit: int = 5) -> dict:
    """Rank corpus repos by genome similarity to `text`. corpus = [{id, text|fingerprint}]. Governed candidate."""
    py_local_src_teleon_knowledge_code_genome__nearest_genomes__q = py_function_src_teleon_knowledge_code_genome__fingerprint(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__nearest_genomes__text)
    py_local_src_teleon_knowledge_code_genome__nearest_genomes__ranked = []
    for py_local_src_teleon_knowledge_code_genome__nearest_genomes__r in py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__nearest_genomes__corpus:
        py_local_src_teleon_knowledge_code_genome__nearest_genomes__fp = py_local_src_teleon_knowledge_code_genome__nearest_genomes__r.get("fingerprint") or py_function_src_teleon_knowledge_code_genome__fingerprint(py_local_src_teleon_knowledge_code_genome__nearest_genomes__r.get("text", ""))
        py_local_src_teleon_knowledge_code_genome__nearest_genomes__ranked.append({"id": py_local_src_teleon_knowledge_code_genome__nearest_genomes__r["id"], "similarity": round(py_function_src_teleon_knowledge_code_genome__genome_similarity(py_local_src_teleon_knowledge_code_genome__nearest_genomes__q, py_local_src_teleon_knowledge_code_genome__nearest_genomes__fp), 4)})
    py_local_src_teleon_knowledge_code_genome__nearest_genomes__ranked.sort(key=lambda py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__nearest_genomes__x: py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__nearest_genomes__x["similarity"], reverse=True)
    return {
        "primitives": py_function_src_teleon_knowledge_code_genome__decompose(py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__nearest_genomes__text),
        "nearest": py_local_src_teleon_knowledge_code_genome__nearest_genomes__ranked[:py_arg_src_teleon_knowledge_code_genome__py_function_src_teleon_knowledge_code_genome__nearest_genomes__limit],
        "verdict": "this architecture is genome-similar to existing repos — likely reinvention" if (
            py_local_src_teleon_knowledge_code_genome__nearest_genomes__ranked and py_local_src_teleon_knowledge_code_genome__nearest_genomes__ranked[0]["similarity"] >= 0.8) else "no close genome match",
        "serves_truth": False, "candidate": True,
    }


def _self_test() -> list[str]:
    py_local_src_teleon_knowledge_code_genome__self_test__fails = []

    def ck(py_arg_src_teleon_knowledge_code_genome__self_test_ck__name, py_arg_src_teleon_knowledge_code_genome__self_test_ck__ok):
        if not py_arg_src_teleon_knowledge_code_genome__self_test_ck__ok:
            py_local_src_teleon_knowledge_code_genome__self_test__fails.append(f"code_genome: {py_arg_src_teleon_knowledge_code_genome__self_test_ck__name}")
            print(f"  [XX] code_genome: {py_arg_src_teleon_knowledge_code_genome__self_test_ck__name}")

    py_local_src_teleon_knowledge_code_genome__self_test__auth_text = "build a login system with oauth and jwt and a session token, plus a connection pool to the database"
    py_local_src_teleon_knowledge_code_genome__self_test__prims = py_function_src_teleon_knowledge_code_genome__decompose(py_local_src_teleon_knowledge_code_genome__self_test__auth_text)
    ck("decompose finds authentication", "authentication" in py_local_src_teleon_knowledge_code_genome__self_test__prims)
    ck("decompose finds db_connection", "db_connection" in py_local_src_teleon_knowledge_code_genome__self_test__prims)
    ck("fingerprint length == primitive count", len(py_function_src_teleon_knowledge_code_genome__fingerprint(py_local_src_teleon_knowledge_code_genome__self_test__auth_text)) == len(py_const_src_teleon_knowledge_code_genome__PRIMITIVES))

    # two auth-heavy repos are similar; an auth repo vs a pure-cache repo are less similar
    py_local_src_teleon_knowledge_code_genome__self_test__a = py_function_src_teleon_knowledge_code_genome__fingerprint("oauth login jwt password session token, database orm connection pool")
    py_local_src_teleon_knowledge_code_genome__self_test__b = py_function_src_teleon_knowledge_code_genome__fingerprint("auth login jwt with database connection pool and orm")
    py_local_src_teleon_knowledge_code_genome__self_test__c = py_function_src_teleon_knowledge_code_genome__fingerprint("a redis cache with lru_cache memoize, nothing else")
    ck("two auth+db repos are highly similar", py_function_src_teleon_knowledge_code_genome__genome_similarity(py_local_src_teleon_knowledge_code_genome__self_test__a, py_local_src_teleon_knowledge_code_genome__self_test__b) >= 0.8)
    ck("auth repo vs cache repo less similar than auth vs auth", py_function_src_teleon_knowledge_code_genome__genome_similarity(py_local_src_teleon_knowledge_code_genome__self_test__a, py_local_src_teleon_knowledge_code_genome__self_test__c) < py_function_src_teleon_knowledge_code_genome__genome_similarity(py_local_src_teleon_knowledge_code_genome__self_test__a, py_local_src_teleon_knowledge_code_genome__self_test__b))
    ck("identical genomes -> 1.0", abs(py_function_src_teleon_knowledge_code_genome__genome_similarity(py_local_src_teleon_knowledge_code_genome__self_test__a, py_local_src_teleon_knowledge_code_genome__self_test__a) - 1.0) < 1e-9)

    py_local_src_teleon_knowledge_code_genome__self_test__corpus = [{"id": "repo_auth_1", "text": "oauth jwt login database orm"},
              {"id": "repo_cache_1", "text": "redis cache memoize lru_cache"}]
    py_local_src_teleon_knowledge_code_genome__self_test__res = py_function_src_teleon_knowledge_code_genome__nearest_genomes(py_local_src_teleon_knowledge_code_genome__self_test__auth_text, py_local_src_teleon_knowledge_code_genome__self_test__corpus)
    ck("nearest_genomes ranks the auth repo first", py_local_src_teleon_knowledge_code_genome__self_test__res["nearest"][0]["id"] == "repo_auth_1")
    ck("verdict is a governed candidate", py_local_src_teleon_knowledge_code_genome__self_test__res["serves_truth"] is False and py_local_src_teleon_knowledge_code_genome__self_test__res["candidate"])

    # AST fork: reads real symbols, ignores a primitive that only appears in a comment/string (precision win)
    py_local_src_teleon_knowledge_code_genome__self_test__src = ("import jwt\nimport sqlalchemy\n\n"
           "def login(user):\n    # this is not really a cache layer\n    return jwt.encode(user)\n")
    py_local_src_teleon_knowledge_code_genome__self_test__ast_prims = py_function_src_teleon_knowledge_code_genome__decompose_ast(py_local_src_teleon_knowledge_code_genome__self_test__src)
    ck("AST finds authentication from real imports/defs (jwt, login)", "authentication" in py_local_src_teleon_knowledge_code_genome__self_test__ast_prims)
    ck("AST finds db_connection from a real import (sqlalchemy)", "db_connection" in py_local_src_teleon_knowledge_code_genome__self_test__ast_prims)
    ck("AST IGNORES 'cache' that is only in a comment (precision win)", "cache" not in py_local_src_teleon_knowledge_code_genome__self_test__ast_prims)
    ck("prose scan WOULD wrongly catch the comment 'cache'", "cache" in py_function_src_teleon_knowledge_code_genome__decompose(py_local_src_teleon_knowledge_code_genome__self_test__src))
    ck("AST falls back to the signal scan on a syntax error", "retry" in py_function_src_teleon_knowledge_code_genome__decompose_ast("def f( retry backoff"))
    ck("ast_fingerprint length == primitive count", len(py_function_src_teleon_knowledge_code_genome__ast_fingerprint(py_local_src_teleon_knowledge_code_genome__self_test__src)) == len(py_const_src_teleon_knowledge_code_genome__PRIMITIVES))
    return py_local_src_teleon_knowledge_code_genome__self_test__fails
