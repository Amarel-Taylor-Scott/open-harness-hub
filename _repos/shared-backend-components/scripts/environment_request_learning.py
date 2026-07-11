#!/usr/bin/env python3
"""environment_request_learning — the MCP tool's LEARNING layer: environment + requests + the usage database.

Owner (2026-07-10): "the MCP tool can be more flexible and learn from the environment and requests, and database,
because it could involve any technology actions." This module is that flexibility, kept OUT of the hardened MCP
transport so the server change is a few-line opt-in hook:

- ENVIRONMENT — `fingerprint_environment(root)` detects the caller's technologies from manifests + file extensions
  (ANY technology: python/node/rust/go/java/dotnet/terraform/docker/… — a data-driven marker table, one row per
  technology, never a hardcoded language assumption). Profiles persist per root digest (derived cache, recomputable).
- REQUESTS — every adapted search is recorded twice: a hash-chained `primitive_usage_ledger` "searched" event (the
  signal the adaptive-vectorization WATERFALL promotes on) and an append-only request ledger row carrying the
  environment digest + technologies (bounded previews, no raw prompt bodies).
- DATABASE — `learned_technology_bias()` derives ranking weights from what the ledgers already know: primitives that
  were downloaded/successfully implemented, and which technologies co-occurred with them. The bias is applied by a
  NON-DESTRUCTIVE rerank (`rerank_hits_with_learned_bias`): hits are only reordered, never dropped — the learned
  lane is a router, not a gate, so a wrong lesson can demote but never hide a result.

The single entry point for a serving surface is `adapt_search_response(query, response, surface=…)`:
OFF (default — `OH_MCP_ADAPTIVE_LEARNING` unset) it returns the response object UNCHANGED, bit-for-bit; ON it
fingerprints + records + reranks and annotates the response with an `adaptive` receipt. Any internal error fails
OPEN (original response + a bounded error note) — learning must never break retrieval. serves_truth=false: learned
weights are candidate routing advice, never served truth.

    PYTHONPATH=. python3 scripts/environment_request_learning.py --self-test
    PYTHONPATH=. python3 scripts/environment_request_learning.py --profile [--root PATH]
    PYTHONPATH=. python3 scripts/environment_request_learning.py --status
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: The opt-in flag a serving surface checks before calling `adapt_search_response`. MIRRORED as a literal in
#: `capability_retrieval_mcp_server._ADAPTIVE_LEARNING_ENV` (a stdio server must not import this module at startup);
#: the self-test drift-checks that mirror so the two names can never diverge silently.
ADAPTIVE_LEARNING_ENVIRONMENT_VARIABLE = "OH_MCP_ADAPTIVE_LEARNING"
#: Redirects ALL learning state (profiles + request ledger + the usage-ledger lane) into one sandbox dir —
#: test isolation and per-tenant sandboxes use this; unset -> the canonical data/dev-intel locations.
LEARNING_DATA_DIR_ENVIRONMENT_VARIABLE = "OH_LEARNING_DATA_DIR"
#: The workspace an MCP client is working in (a stdio server's cwd is arbitrary); unset -> os.getcwd().
WORKSPACE_ROOT_ENVIRONMENT_VARIABLE = "OH_MCP_WORKSPACE_ROOT"

_DEFAULT_DATA_DIR = _REPO / "data" / "dev-intel" / "environment_request_learning"

#: TECHNOLOGY MARKER TABLE (data-driven — "it could involve ANY technology"): manifest filename -> technologies.
#: Extending coverage = add a row, never code. Filenames are matched case-sensitively except Dockerfile variants.
TECHNOLOGY_MARKERS: dict[str, list[str]] = {
    "package.json": ["javascript", "node"],
    "tsconfig.json": ["typescript"],
    "pyproject.toml": ["python"],
    "requirements.txt": ["python"],
    "setup.py": ["python"],
    "Pipfile": ["python"],
    "Cargo.toml": ["rust"],
    "go.mod": ["go"],
    "pom.xml": ["java", "maven"],
    "build.gradle": ["java", "gradle"],
    "build.gradle.kts": ["kotlin", "gradle"],
    "Gemfile": ["ruby"],
    "composer.json": ["php"],
    "mix.exs": ["elixir"],
    "pubspec.yaml": ["dart", "flutter"],
    "Dockerfile": ["docker"],
    "docker-compose.yml": ["docker", "docker-compose"],
    "docker-compose.yaml": ["docker", "docker-compose"],
    "Chart.yaml": ["helm", "kubernetes"],
    "kustomization.yaml": ["kubernetes"],
    "serverless.yml": ["serverless-framework"],
    "Makefile": ["make"],
    "CMakeLists.txt": ["cmake", "cpp"],
    "dbt_project.yml": ["dbt", "sql"],
    "dvc.yaml": ["dvc", "ml-pipeline"],
    "MLproject": ["mlflow", "ml-pipeline"],
    ".terraform.lock.hcl": ["terraform"],
}
#: extension -> language (the second, weaker signal; counts weight the profile's language histogram).
EXTENSION_LANGUAGES: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript",
    ".rs": "rust", ".go": "go", ".java": "java", ".kt": "kotlin", ".rb": "ruby", ".php": "php",
    ".cs": "csharp", ".cpp": "cpp", ".cc": "cpp", ".c": "c", ".swift": "swift", ".scala": "scala",
    ".sql": "sql", ".sh": "shell", ".tf": "terraform", ".proto": "protobuf", ".ipynb": "jupyter",
    ".html": "html", ".css": "css", ".r": "r", ".jl": "julia", ".ex": "elixir", ".dart": "dart",
}
#: directories never scanned (dependency/VCS/build output — huge and not the caller's own technology choices).
_SKIP_DIRECTORY_NAMES = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next",
                         "target", ".codegraph", ".mypy_cache", ".pytest_cache", ".tox", "site-packages"}
_MAX_SCANNED_ENTRIES = 4_000   # fingerprint walk bound: a monorepo costs the same as a small repo
_MAX_MANIFESTS_KEPT = 40       # bounded manifest list persisted on a profile
_MAX_TECHNOLOGIES_KEPT = 24    # bounded technologies persisted on a profile / request row
_QUERY_PREVIEW_CHARS = 120     # bounded query snippet on a request row (digest carries identity)
_MAX_TOP_IDS_KEPT = 8          # bounded hit ids on a request row
_MAX_EVENTS_READ = 5_000       # bias derivation reads at most this many most-recent events per ledger

#: ranking-bias weights — a successful implementation is worth far more than a download; technology co-occurrence
#: is a mild tie-breaker on top. Reordering only (non-destructive), so mis-weighting can never hide a hit.
_BIAS_WEIGHT_IMPLEMENT_SUCCESS = 3.0
_BIAS_WEIGHT_DOWNLOAD = 1.0
_BIAS_WEIGHT_TECHNOLOGY_MATCH = 0.5

_PROFILE_CACHE: dict[str, dict[str, Any]] = {}  # in-process per-root cache so serving never rescans per request


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _digest16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def learning_data_dir() -> Path:
    override = os.environ.get(LEARNING_DATA_DIR_ENVIRONMENT_VARIABLE)
    return Path(override) if override else _DEFAULT_DATA_DIR


def request_ledger_path() -> Path:
    return learning_data_dir() / "requests.jsonl"


def _usage_ledger_path_override() -> Optional[Path]:
    """Sandboxed usage-ledger lane iff the learning dir is redirected; None -> the canonical hash-chained ledger."""
    if os.environ.get(LEARNING_DATA_DIR_ENVIRONMENT_VARIABLE):
        return learning_data_dir() / "usage_events.jsonl"
    return None


# ================================================================================================================
# ENVIRONMENT — fingerprint any technology from manifests + extensions
# ================================================================================================================
def fingerprint_environment(root: str | Path, *, max_entries: int = _MAX_SCANNED_ENTRIES,
                            persist: bool = True) -> dict[str, Any]:
    """Detect the technologies in a workspace: bounded, deterministic (sorted walk), any-technology (table-driven)."""
    root_path = Path(root).resolve()
    languages: Counter[str] = Counter()
    technologies: set[str] = set()
    manifests: list[str] = []
    scanned = 0
    for current_dir, dir_names, file_names in os.walk(root_path):
        dir_names[:] = sorted(d for d in dir_names if d not in _SKIP_DIRECTORY_NAMES and not d.startswith(".cache"))
        for file_name in sorted(file_names):
            scanned += 1
            if scanned > max_entries:
                break
            marked = TECHNOLOGY_MARKERS.get(file_name)
            if marked:
                technologies.update(marked)
                if len(manifests) < _MAX_MANIFESTS_KEPT:
                    manifests.append(str(Path(current_dir, file_name).relative_to(root_path)))
            language = EXTENSION_LANGUAGES.get(Path(file_name).suffix.lower())
            if language:
                languages[language] += 1
        if scanned > max_entries:
            break
    technologies.update(lang for lang, _count in languages.most_common(8))
    profile = {
        "schema_version": "environment-profile/v1",
        "root_digest": _digest16(str(root_path)),
        "scanned_entries": min(scanned, max_entries),
        "scan_truncated": scanned > max_entries,
        "languages": dict(languages.most_common(12)),
        "technologies": sorted(technologies)[:_MAX_TECHNOLOGIES_KEPT],
        "manifests": manifests,
        "candidate": True,
        "serves_truth": False,
    }
    if persist:
        profile_dir = learning_data_dir() / "profiles"
        profile_dir.mkdir(parents=True, exist_ok=True)
        (profile_dir / f"{profile['root_digest']}.json").write_text(json.dumps(profile, indent=2, sort_keys=True))
    return profile


def _cached_profile(root: str | Path) -> dict[str, Any]:
    key = str(Path(root).resolve())
    if key not in _PROFILE_CACHE:
        _PROFILE_CACHE[key] = fingerprint_environment(key)
    return _PROFILE_CACHE[key]


# ================================================================================================================
# REQUESTS — the append-only request ledger (environment digest + technologies per request)
# ================================================================================================================
def log_request(*, surface: str, action: str, query_text: str, environment_profile: dict[str, Any],
                result_count: int, top_primitive_ids: list[str], ts: str = "",
                ledger_path: Optional[Path] = None) -> dict[str, Any]:
    path = Path(ledger_path or request_ledger_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": ts or _now_iso(),
        "surface": surface,
        "action": action,
        "query_digest": _digest16(query_text),
        "query_preview": query_text[:_QUERY_PREVIEW_CHARS],
        "environment_digest": environment_profile.get("root_digest", ""),
        "technologies": list(environment_profile.get("technologies", []))[:_MAX_TECHNOLOGIES_KEPT],
        "result_count": result_count,
        "top_primitive_ids": list(top_primitive_ids)[:_MAX_TOP_IDS_KEPT],
        "candidate": True,
        "serves_truth": False,
    }
    with path.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def load_requests(ledger_path: Optional[Path] = None) -> list[dict[str, Any]]:
    path = Path(ledger_path or request_ledger_path())
    if not path.exists():
        return []
    lines = path.read_text().splitlines()[-_MAX_EVENTS_READ:]
    return [json.loads(line) for line in lines if line.strip()]


# ================================================================================================================
# DATABASE — learned bias from the usage ledger + request ledger; NON-DESTRUCTIVE rerank
# ================================================================================================================
def learned_technology_bias(usage_events: Optional[list[dict[str, Any]]] = None,
                            request_events: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    """Ranking weights the ledgers already justify: outcome-weighted per-primitive scores + technology co-occurrence."""
    if usage_events is None:
        from scripts import primitive_usage_ledger as _usage_ledger  # noqa: PLC0415
        usage_events = _usage_ledger.load_events(_usage_ledger_path_override())[-_MAX_EVENTS_READ:]
    if request_events is None:
        request_events = load_requests()
    global_weight: dict[str, float] = defaultdict(float)
    for event in usage_events:
        event_type = event.get("event_type")
        for primitive_id in event.get("primitive_ids", []):
            if event_type == "downloaded":
                global_weight[primitive_id] += _BIAS_WEIGHT_DOWNLOAD
            elif event_type == "implemented" and event.get("outcome") == "success":
                global_weight[primitive_id] += _BIAS_WEIGHT_IMPLEMENT_SUCCESS
    by_technology: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for request in request_events:
        for technology in request.get("technologies", []):
            for primitive_id in request.get("top_primitive_ids", []):
                by_technology[technology][primitive_id] += 1.0
    return {
        "global": dict(global_weight),
        "by_technology": {technology: dict(weights) for technology, weights in by_technology.items()},
        "n_usage_events": len(usage_events),
        "n_request_events": len(request_events),
        "candidate": True,
        "serves_truth": False,
    }


def rerank_hits_with_learned_bias(hits: list[dict[str, Any]], technologies: list[str],
                                  bias: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Stable, NON-DESTRUCTIVE reorder: every hit survives; boosted hits carry an `adaptive_boost` annotation."""
    def _boost(hit: dict[str, Any]) -> float:
        primitive_id = str(hit.get("primitive_id") or "")
        score = float(bias.get("global", {}).get(primitive_id, 0.0))
        for technology in technologies:
            score += _BIAS_WEIGHT_TECHNOLOGY_MATCH * bias.get("by_technology", {}).get(technology, {}).get(primitive_id, 0.0)
        return score

    scored = [(_boost(hit), index, hit) for index, hit in enumerate(hits)]
    reordered = sorted(scored, key=lambda row: (-row[0], row[1]))  # stable: base order breaks ties
    out: list[dict[str, Any]] = []
    boosted = 0
    for score, _index, hit in reordered:
        if score > 0:
            boosted += 1
            hit = {**hit, "adaptive_boost": round(score, 4)}
        out.append(hit)
    moved = [h.get("primitive_id") for h in out] != [h.get("primitive_id") for h in hits]
    return out, {"reordered": moved, "boosted": boosted}


# ================================================================================================================
# THE HOOK a serving surface calls — off = identity; on = record + learn + annotate; errors fail OPEN
# ================================================================================================================
def adapt_search_response(query: str, response: dict[str, Any], *, surface: str,
                          workspace_root: Optional[str] = None, enabled: Optional[bool] = None,
                          ts: str = "") -> dict[str, Any]:
    if enabled is None:
        enabled = os.environ.get(ADAPTIVE_LEARNING_ENVIRONMENT_VARIABLE) == "1"
    if not enabled:
        return response
    try:
        root = workspace_root or os.environ.get(WORKSPACE_ROOT_ENVIRONMENT_VARIABLE) or os.getcwd()
        profile = _cached_profile(root)
        hits = response.get("results") if isinstance(response.get("results"), list) else []
        hit_ids = [str(h.get("primitive_id") or "") for h in hits if isinstance(h, dict)]

        from scripts import primitive_usage_ledger as _usage_ledger  # noqa: PLC0415
        usage_record = _usage_ledger.log_search(query, [h for h in hits if isinstance(h, dict)],
                                                agent=surface, ts=ts or _now_iso(),
                                                ledger_path=_usage_ledger_path_override())
        log_request(surface=surface, action="primitive_search", query_text=query, environment_profile=profile,
                    result_count=len(hits), top_primitive_ids=hit_ids, ts=ts)

        bias = learned_technology_bias()
        reranked, rerank_meta = rerank_hits_with_learned_bias(
            [h for h in hits if isinstance(h, dict)], profile.get("technologies", []), bias)
        if rerank_meta["reordered"] or rerank_meta["boosted"]:
            response["results"] = reranked
        response["adaptive"] = {
            "enabled": True,
            "surface": surface,
            "environment_digest": profile.get("root_digest"),
            "technologies": profile.get("technologies", []),
            **rerank_meta,
            "learned_from": {"usage_events": bias["n_usage_events"], "request_events": bias["n_request_events"]},
            "request_logged": bool(usage_record.get("hash")),
            "candidate": True,
            "serves_truth": False,
        }
        return response
    except Exception as error:  # noqa: BLE001  fail OPEN — learning must never break retrieval
        response["adaptive"] = {"enabled": True, "error": str(error)[:200], "candidate": True, "serves_truth": False}
        return response


def learning_status() -> dict[str, Any]:
    """Bounded summary of what the learning layer currently knows (for the agent tool / operators)."""
    bias = learned_technology_bias()
    top_global = sorted(bias["global"].items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    profile_dir = learning_data_dir() / "profiles"
    return {
        "data_dir": str(learning_data_dir()),
        "n_usage_events": bias["n_usage_events"],
        "n_request_events": bias["n_request_events"],
        "n_environment_profiles": len(list(profile_dir.glob("*.json"))) if profile_dir.exists() else 0,
        "top_boosted_primitives": [{"primitive_id": pid, "weight": weight} for pid, weight in top_global],
        "technologies_seen": sorted(bias["by_technology"])[:_MAX_TECHNOLOGIES_KEPT],
        "candidate": True,
        "serves_truth": False,
    }


# ================================================================================================================
def _self_test() -> int:
    import tempfile
    checks: list[tuple[str, bool, str]] = []
    saved_environment = {name: os.environ.get(name) for name in
                         (ADAPTIVE_LEARNING_ENVIRONMENT_VARIABLE, LEARNING_DATA_DIR_ENVIRONMENT_VARIABLE,
                          WORKSPACE_ROOT_ENVIRONMENT_VARIABLE)}
    try:
        with tempfile.TemporaryDirectory() as sandbox:
            os.environ[LEARNING_DATA_DIR_ENVIRONMENT_VARIABLE] = str(Path(sandbox) / "learning")
            workspace = Path(sandbox) / "workspace"
            workspace.mkdir()
            (workspace / "package.json").write_text("{}")
            (workspace / "pyproject.toml").write_text("[project]\nname='x'")
            (workspace / "main.tf").write_text("resource {}")
            (workspace / "app.py").write_text("print('hello')")

            # (1) ENVIRONMENT: any-technology fingerprint from manifests + extensions (table-driven).
            profile = fingerprint_environment(workspace)
            found = set(profile["technologies"])
            checks.append((f"fingerprint detects cross-technology stack ({sorted(found)})",
                           {"javascript", "python", "terraform"} <= found, json.dumps(profile)))
            checks.append(("profile persisted per root digest",
                           (Path(sandbox) / "learning" / "profiles" / f"{profile['root_digest']}.json").exists(), ""))

            # (2) OFF -> identity: the same response OBJECT, no annotation, nothing written.
            os.environ.pop(ADAPTIVE_LEARNING_ENVIRONMENT_VARIABLE, None)
            original = {"results": [{"primitive_id": "p:a"}, {"primitive_id": "p:b"}]}
            untouched = adapt_search_response("query", original, surface="test")
            checks.append(("flag OFF -> response returned unchanged (same object, no adaptive key)",
                           untouched is original and "adaptive" not in original
                           and not request_ledger_path().exists(), ""))

            # (3) ON -> records to BOTH ledgers, annotates, and never drops a hit.
            os.environ[ADAPTIVE_LEARNING_ENVIRONMENT_VARIABLE] = "1"
            os.environ[WORKSPACE_ROOT_ENVIRONMENT_VARIABLE] = str(workspace)
            response = {"results": [{"primitive_id": "p:cold"}, {"primitive_id": "p:hot"}]}
            adapted = adapt_search_response("build a sanctions screen", response, surface="test", ts="t0")
            adaptive = adapted.get("adaptive", {})
            hit_ids = {h["primitive_id"] for h in adapted["results"]}
            checks.append(("flag ON -> adaptive receipt + request logged + hit set preserved",
                           adaptive.get("enabled") is True and adaptive.get("request_logged") is True
                           and hit_ids == {"p:cold", "p:hot"} and len(load_requests()) == 1,
                           json.dumps(adaptive)))

            # (4) DATABASE: an implemented-success primitive learns a boost and rises (reorder, never drop).
            from scripts import primitive_usage_ledger as _usage_ledger
            _usage_ledger.log_implement("p:hot", success=True, query_text="sanctions", ts="t1",
                                        ledger_path=_usage_ledger_path_override())
            again = adapt_search_response("build a sanctions screen",
                                          {"results": [{"primitive_id": "p:cold"}, {"primitive_id": "p:hot"}]},
                                          surface="test", ts="t2")
            checks.append(("learned success bias reorders p:hot to the top, p:cold survives",
                           [h["primitive_id"] for h in again["results"]] == ["p:hot", "p:cold"]
                           and again["results"][0].get("adaptive_boost", 0) > 0, json.dumps(again["results"])))

            # (5) technology co-occurrence bias exists and rerank stays non-destructive under it.
            bias = learned_technology_bias()
            reranked, meta = rerank_hits_with_learned_bias(
                [{"primitive_id": "p:x"}, {"primitive_id": "p:hot"}], ["python"], bias)
            checks.append(("bias derives from both ledgers; rerank preserves every hit",
                           bias["n_usage_events"] >= 1 and bias["n_request_events"] >= 2
                           and {h["primitive_id"] for h in reranked} == {"p:x", "p:hot"}, json.dumps(meta)))

            # (6) fail OPEN: a broken workspace path still returns the response with a bounded error note.
            _PROFILE_CACHE.clear()
            broken = adapt_search_response("q", {"results": []}, surface="test", workspace_root="\x00invalid")
            checks.append(("internal error fails OPEN (response survives with bounded adaptive.error)",
                           "error" in broken.get("adaptive", {}) and broken["adaptive"].get("enabled") is True,
                           json.dumps(broken.get("adaptive"))))

            # (7) determinism: same workspace fingerprints identically (sorted walk, no wall-clock in the body).
            checks.append(("fingerprint deterministic",
                           fingerprint_environment(workspace, persist=False)
                           == fingerprint_environment(workspace, persist=False), ""))

            # (8) no-magic-values drift check: the MCP server mirrors the flag name as a literal — verify it.
            server_source = (_REPO / "scripts" / "capability_retrieval_mcp_server.py").read_text()
            checks.append((f"MCP server mirrors the {ADAPTIVE_LEARNING_ENVIRONMENT_VARIABLE} flag literal",
                           ADAPTIVE_LEARNING_ENVIRONMENT_VARIABLE in server_source, ""))

            # (9) status summary is bounded and stamped candidate-only.
            status = learning_status()
            checks.append(("learning_status reports events/profiles, serves_truth=false",
                           status["n_usage_events"] >= 1 and status["n_environment_profiles"] >= 1
                           and status["serves_truth"] is False, json.dumps(status)))
    finally:
        for name, value in saved_environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        _PROFILE_CACHE.clear()

    ok = all(passed for _name, passed, _detail in checks)
    print(f"{'PASS' if ok else 'FAIL'} - environment_request_learning: any-technology environment fingerprint + "
          f"request ledger + database-derived NON-DESTRUCTIVE rerank; OFF=bit-for-bit identity, errors fail open. "
          f"serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:300]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="The MCP learning layer: environment + requests + usage database.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--profile", action="store_true", help="fingerprint a workspace (default: cwd)")
    parser.add_argument("--root", default=".", help="workspace root for --profile")
    parser.add_argument("--status", action="store_true", help="what the learning layer currently knows")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.profile:
        print(json.dumps(fingerprint_environment(args.root), indent=2, sort_keys=True))
        return 0
    if args.status:
        print(json.dumps(learning_status(), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
