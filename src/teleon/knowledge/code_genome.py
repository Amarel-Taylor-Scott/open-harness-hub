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
PRIMITIVES: dict[str, list[str]] = {
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
_PRIMITIVE_ORDER = list(PRIMITIVES)


def decompose(text: str) -> list[str]:
    """Which architectural primitives are present in this code/description (deterministic signal scan)."""
    low = (text or "").lower()
    return [name for name, tells in PRIMITIVES.items() if any(re.search(re.escape(t), low) for t in tells)]


def fingerprint(text: str) -> list[float]:
    """A genome fingerprint: a vector over the canonical primitive list (1.0 where the primitive is present)."""
    present = set(decompose(text))
    return [1.0 if name in present else 0.0 for name in _PRIMITIVE_ORDER]


def genome_similarity(fp_a: list[float], fp_b: list[float]) -> float:
    """Cosine similarity between two genome fingerprints (software similarity %)."""
    if not fp_a or not fp_b or len(fp_a) != len(fp_b):
        return 0.0
    dot = sum(x * y for x, y in zip(fp_a, fp_b))
    na = math.sqrt(sum(x * x for x in fp_a))
    nb = math.sqrt(sum(y * y for y in fp_b))
    return dot / (na * nb) if na and nb else 0.0


def decompose_ast(source: str) -> list[str]:
    """Higher-fidelity decomposition: parse Python source and read only REAL symbols (imports, call names, def/class
    names) — so a primitive merely mentioned in a comment/string does NOT count (the precision win over the prose
    scan). Falls back to the signal scan on a syntax error (partial snippets). tree-sitter is the multi-language fork."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return decompose(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                names.add(f.id)
            elif isinstance(f, ast.Attribute):
                names.add(f.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    hay = " ".join(n.lower() for n in names if n)
    return [name for name, tells in PRIMITIVES.items()
            if any(re.search(rf"\b{re.escape(t.split()[0])}", hay) for t in tells)]


def ast_fingerprint(source: str) -> list[float]:
    """A genome fingerprint from the AST decomposition (symbol-level, comment/string-immune)."""
    present = set(decompose_ast(source))
    return [1.0 if name in present else 0.0 for name in _PRIMITIVE_ORDER]


def nearest_genomes(text: str, corpus: list[dict], *, limit: int = 5) -> dict:
    """Rank corpus repos by genome similarity to `text`. corpus = [{id, text|fingerprint}]. Governed candidate."""
    q = fingerprint(text)
    ranked = []
    for r in corpus:
        fp = r.get("fingerprint") or fingerprint(r.get("text", ""))
        ranked.append({"id": r["id"], "similarity": round(genome_similarity(q, fp), 4)})
    ranked.sort(key=lambda x: x["similarity"], reverse=True)
    return {
        "primitives": decompose(text),
        "nearest": ranked[:limit],
        "verdict": "this architecture is genome-similar to existing repos — likely reinvention" if (
            ranked and ranked[0]["similarity"] >= 0.8) else "no close genome match",
        "serves_truth": False, "candidate": True,
    }


def _self_test() -> list[str]:
    fails = []

    def ck(name, ok):
        if not ok:
            fails.append(f"code_genome: {name}")
            print(f"  [XX] code_genome: {name}")

    auth_text = "build a login system with oauth and jwt and a session token, plus a connection pool to the database"
    prims = decompose(auth_text)
    ck("decompose finds authentication", "authentication" in prims)
    ck("decompose finds db_connection", "db_connection" in prims)
    ck("fingerprint length == primitive count", len(fingerprint(auth_text)) == len(PRIMITIVES))

    # two auth-heavy repos are similar; an auth repo vs a pure-cache repo are less similar
    a = fingerprint("oauth login jwt password session token, database orm connection pool")
    b = fingerprint("auth login jwt with database connection pool and orm")
    c = fingerprint("a redis cache with lru_cache memoize, nothing else")
    ck("two auth+db repos are highly similar", genome_similarity(a, b) >= 0.8)
    ck("auth repo vs cache repo less similar than auth vs auth", genome_similarity(a, c) < genome_similarity(a, b))
    ck("identical genomes -> 1.0", abs(genome_similarity(a, a) - 1.0) < 1e-9)

    corpus = [{"id": "repo_auth_1", "text": "oauth jwt login database orm"},
              {"id": "repo_cache_1", "text": "redis cache memoize lru_cache"}]
    res = nearest_genomes(auth_text, corpus)
    ck("nearest_genomes ranks the auth repo first", res["nearest"][0]["id"] == "repo_auth_1")
    ck("verdict is a governed candidate", res["serves_truth"] is False and res["candidate"])

    # AST fork: reads real symbols, ignores a primitive that only appears in a comment/string (precision win)
    src = ("import jwt\nimport sqlalchemy\n\n"
           "def login(user):\n    # this is not really a cache layer\n    return jwt.encode(user)\n")
    ast_prims = decompose_ast(src)
    ck("AST finds authentication from real imports/defs (jwt, login)", "authentication" in ast_prims)
    ck("AST finds db_connection from a real import (sqlalchemy)", "db_connection" in ast_prims)
    ck("AST IGNORES 'cache' that is only in a comment (precision win)", "cache" not in ast_prims)
    ck("prose scan WOULD wrongly catch the comment 'cache'", "cache" in decompose(src))
    ck("AST falls back to the signal scan on a syntax error", "retry" in decompose_ast("def f( retry backoff"))
    ck("ast_fingerprint length == primitive count", len(ast_fingerprint(src)) == len(PRIMITIVES))
    return fails
