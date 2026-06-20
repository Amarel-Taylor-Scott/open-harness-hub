#!/usr/bin/env python3
"""scripts.pattern_miner — scan the repo for REPEATED SHAPES and grade them against the pattern registry.

This is a META layer over existing code: it does NOT add a runtime, bus, worker framework, ledger, gateway,
optimizer, parser, or consumption service. It only READS the tree (scripts/, src/baltor/, architecture/,
schemas/, web/baltor/, docs/) and reports where the same shape recurs, where a one-off should become a
standard, what is unstandardized, what anti-patterns exist, and which pattern_registry entries each detected
shape maps to.

Output: a JSON report at ``.agent/pattern_miner_report.json`` with seven keys ::

    detected_patterns          shapes seen >= MIN_REPEAT times, each with real example paths + registry map
    unstandardized_repetitions repeated shapes whose registry entry is still "candidate" (built twice, not std)
    one_offs                   shapes seen exactly once (watch list — a second occurrence makes a pattern)
    candidate_templates        detected patterns with no template yet (template_ids == [])
    anti_patterns              real violations: raw provider/sqlite imports outside their allowed home, vague names
    recommended_standards      next promotions: candidate registry patterns that now have >= MIN_REPEAT examples
    waivers_needed             enforced-or-standard patterns whose detected examples fall short of done_when

Every path emitted is REAL (it exists on disk at scan time). The miner is deterministic and offline:
no network, no wall-clock in content, sorted output, content-addressed nowhere needed (it reports, not writes ids).

CLI:
    python3 scripts/pattern_miner.py --scan              # scan the real repo, write the report
    python3 scripts/pattern_miner.py --scan --root DIR   # scan an arbitrary fixture tree (used by the proof)
    python3 scripts/pattern_miner.py --self-test         # tiny deterministic fixture, assert 7 keys + detections
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
from typing import Any

_THIS = Path(__file__).resolve()
_REPO = _THIS.parents[1]

# --- single source of truth: where the report + registry live (no parallel literals) ---
REPORT_REL = ".agent/pattern_miner_report.json"
REPORT_MD_REL = "docs/status/pattern-miner-report.md"
REGISTRY_REL = "architecture/pattern_registry.json"

# Directories the miner is allowed to read (the lane's scan surface).
SCAN_DIRS = ("scripts", "src/baltor", "architecture", "schemas", "web/baltor", "docs")

# A shape must recur at least this many times to be a "pattern" rather than a "one-off".
MIN_REPEAT = 2  # "build it twice -> it is a pattern" (see docs/standards/pattern-system.md)

# The seven report keys this miner contracts to emit (single source for the proof to assert against).
REPORT_KEYS = (
    "detected_patterns",
    "unstandardized_repetitions",
    "one_offs",
    "candidate_templates",
    "anti_patterns",
    "recommended_standards",
    "waivers_needed",
)

# Provider SDKs that must only be imported inside an adapter / gateway home (raw import elsewhere = anti-pattern).
_PROVIDER_IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+(openai|anthropic|google\.generativeai|cohere)\b", re.M)
# requests/httpx raw network in domain code (allowed only in adapters/ingest/gateway).
_NETWORK_IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+(requests|httpx|urllib3)\b", re.M)
# raw sqlite in a processor (processors must go through the ledger/store, not open their own db).
_SQLITE_RE = re.compile(r"\bsqlite3\b")
# vague filenames that hide intent (a one-off that should be named for its shape).
_VAGUE_NAME_RE = re.compile(r"^(util|utils|helper|helpers|misc|tmp|temp|stuff|new|test2|copy|foo|bar)\.py$", re.I)

# Folders where a provider/network import is legitimate (the adapter/gateway/ingest seam).
_PROVIDER_ALLOWED = ("src/baltor/adapters", "src/baltor/llm_gateway", "scripts/llm_gateway", "scripts/ingest")
# Folders where sqlite is legitimate (durable store / db tooling / proofs that assert sqlite is absent).
_SQLITE_ALLOWED = ("scripts/db", "scripts/durable_store.py", "scripts/check_", "scripts/build_", "scripts/scaffold_")

# Map of a detected shape -> the canonical pattern_id it satisfies (single source; the registry must contain each).
SHAPE_TO_PATTERN = {
    "check_proof": "proof_script_pattern",
    "self_test": "proof_script_pattern",
    "api_route": "api_projection_route_pattern",
    "web_fetch": "ui_projection_page_pattern",
    "source_adapter": "source_adapter_pattern",
    "source_artifact": "source_artifact_pattern",
    "parser_provider": "parser_provider_pattern",
    "ingestion_feed": "ingestion_sync_pattern",
    "durable_command": "durable_command_pattern",
    "worker_claim": "worker_claim_loop_pattern",
    "processor_harness": "processor_harness_pattern",
    "artifact_contract": "artifact_envelope_pattern",
    "provider_adapter": "provider_adapter_pattern",
    "schema_file": "contract_schema_pattern",
    "docs_page": "documentation_page_pattern",
    "json_registry": "section_maturity_entry_pattern",
    "capability_catalog": "capability_catalog_entry_pattern",
    "optimization_candidate": "optimization_candidate_pattern",
    "reconciliation": "reconciliation_decision_pattern",
    "held_out_warning": "held_out_warning_pattern",
    "watchtower_task": "watchtower_verification_task_pattern",
    "tenant_isolation": "tenant_isolation_pattern",
    "structured_logging": "structured_logging_pattern",
    "review_pack": "review_pack_pattern",
    "dependency_emulator": "dependency_emulator_pattern",
    "multi_source_fixture": "multi_source_fixture_pattern",
}


def _rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def _iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for d in SCAN_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".py", ".json", ".html", ".js", ".md"):
                out.append(p)
    return out


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _starts_with_any(rel: str, prefixes: tuple[str, ...]) -> bool:
    return any(rel == pre or rel.startswith(pre.rstrip("/") + "/") or Path(rel).name.startswith(pre.split("/")[-1])
              for pre in prefixes)


def scan(root: Path) -> dict[str, Any]:
    """Scan ``root`` and return a structured report. Pure read; no writes, no network, no wall-clock."""
    root = root.resolve()
    registry = _load_registry(root)
    files = _iter_files(root)

    # shape_id -> sorted list of real relative example paths
    hits: dict[str, list[str]] = {k: [] for k in SHAPE_TO_PATTERN}
    anti: list[dict[str, str]] = []

    for p in files:
        rel = _rel(p, root)
        name = p.name
        txt = _read(p)

        # --- proof scripts / self-test ---
        if name.startswith("check_") and name.endswith(".py"):
            hits["check_proof"].append(rel)
        if "--self-test" in txt and name.endswith(".py"):
            hits["self_test"].append(rel)

        # --- API route handlers (string literals "/api/..." in a server module) ---
        if name.endswith(".py") and re.search(r'["\']/api/[a-z0-9_./-]+', txt):
            hits["api_route"].append(rel)

        # --- web pages calling /api/ ---
        if p.suffix in (".html", ".js") and "/api/" in txt:
            hits["web_fetch"].append(rel)

        # --- source adapters (implement/declare the SourceAdapter seam) ---
        if ("adapters/source" in rel or "ingest/source_adapters" in rel) and name.endswith(".py") and name != "__init__.py":
            hits["source_adapter"].append(rel)
        if "SourceAdapterPort" in txt or ("class" in txt and "SourceAdapter" in txt and "Protocol" in txt):
            hits["source_adapter"].append(rel)

        # --- source artifacts (the governed object an adapter emits: content-hashed, scoped, lineage) ---
        if name.endswith(".py") and re.search(r'SourceArtifact|source_artifact|artifact_ledger|content_hash', txt) \
                and ("artifact" in rel or "ledger" in rel or "source_artifact" in rel):
            hits["source_artifact"].append(rel)

        # --- parser provider ---
        if "parser_provider" in name or ("parser" in rel and "provider" in txt and name.endswith(".py")):
            hits["parser_provider"].append(rel)

        # --- ingestion feeds ---
        if rel.startswith("scripts/ingest/") and name.endswith("_feed.py"):
            hits["ingestion_feed"].append(rel)

        # --- durable command handlers ---
        if "durable" in name and name.endswith(".py"):
            hits["durable_command"].append(rel)
        if re.search(r'command_type|command\.run_step|run_step|CommandEnvelope', txt) and name.endswith(".py") \
                and ("command" in rel or "durable" in rel):
            hits["durable_command"].append(rel)

        # --- worker claim loops ---
        if "worker" in name and name.endswith(".py"):
            hits["worker_claim"].append(rel)
        if re.search(r'\bclaim\b.*\b(loop|next|task)\b|baltor\.claim|worker_claim', txt) and "worker" in rel:
            hits["worker_claim"].append(rel)

        # --- processor harness ---
        if rel.startswith("src/baltor/processors/") and name not in ("__init__.py", "README.md"):
            hits["processor_harness"].append(rel)
        if "pipeline_runtime/processors.py" in rel:
            hits["processor_harness"].append(rel)
        # the working runtime harness home: scripts/runtime/processor*.py + builtin_processors.py
        if re.fullmatch(r"scripts/runtime/(processor|processor_harness|processor_registry|builtin_processors)\.py", rel):
            hits["processor_harness"].append(rel)

        # --- artifact contracts / envelopes ---
        if rel.startswith("src/baltor/contracts/artifacts/") and name.endswith(".py") and name != "__init__.py":
            hits["artifact_contract"].append(rel)
        if "pipeline_runtime/envelope.py" in rel or "pipeline_runtime/artifact_types.py" in rel:
            hits["artifact_contract"].append(rel)

        # --- provider adapters (gateway providers / object/graph stores) bound to a capability slot ---
        if rel.startswith("src/baltor/llm_gateway/providers/") and name.endswith(".py") and name != "__init__.py":
            hits["provider_adapter"].append(rel)
        if rel.startswith("src/baltor/adapters/") and name.endswith(".py") and name not in ("__init__.py",) \
                and "adapters/source" not in rel:
            hits["provider_adapter"].append(rel)
        # the capability registry that routes domain code to slots is part of the provider-adapter shape
        if "registry/capability_registry.py" in rel or ("capability_slot" in txt and name.endswith(".py") and "registry" in rel):
            hits["provider_adapter"].append(rel)

        # --- schema files ---
        if rel.startswith("schemas/") and name.endswith(".schema.json"):
            hits["schema_file"].append(rel)

        # --- docs pages ---
        if rel.startswith("docs/") and name.endswith(".md"):
            hits["docs_page"].append(rel)

        # --- JSON registries (architecture/*.json with version+note, the matrix/registry shape) ---
        if rel.startswith("architecture/") and name.endswith(".json"):
            try:
                obj = json.loads(txt)
                if isinstance(obj, dict) and "version" in obj:
                    hits["json_registry"].append(rel)
                    if "capability_slots" in obj:
                        hits["capability_catalog"].append(rel)
            except json.JSONDecodeError:
                pass
        # the capability registry module + catalog proofs are part of the capability-catalog shape
        if "registry/capability_registry.py" in rel or "check_external_capability_catalog" in name:
            hits["capability_catalog"].append(rel)

        # --- optimization candidate (measured serve/assembly change carrying lift+cost) ---
        if name.endswith(".py") and re.search(r'optimization_candidate|OptimizationCandidate|measured.*lift|lift.*cost', txt) \
                and ("optimization" in rel or "consumption" in rel or "optimization" in name):
            hits["optimization_candidate"].append(rel)

        # --- reconciliation decision (deterministic winner/loser/conflict record) ---
        if name.endswith(".py") and re.search(r'reconcil', txt, re.I) \
                and ("reconcil" in rel or "conflict" in rel or "artifact_graph" in rel):
            hits["reconciliation"].append(rel)

        # --- held-out warning (uncorroborated/held-out output carries an explicit warning) ---
        if name.endswith(".py") and re.search(r'held[ _-]?out', txt, re.I):
            hits["held_out_warning"].append(rel)

        # --- watchtower verification task (continuous re-verification of fact freshness) ---
        if name.endswith(".py") and re.search(r'VerificationTask|verification_task|WatchPolicy|watch_policy|refresh_planner', txt) \
                and ("contracts/artifacts" in rel or "facts" in rel or "watchtower" in rel or "watchtower" in name):
            hits["watchtower_task"].append(rel)

        # --- tenant isolation (tenant_private cannot promote to global_public; no cross-tenant read) ---
        if name.endswith(".py") and re.search(r'tenant_private|global_public|cross.tenant|tenant.*isolation', txt) \
                and ("isolation" in rel or "isolation" in name):
            hits["tenant_isolation"].append(rel)

        # --- structured runtime logging (JSON log record with canonical correlation fields) ---
        if name.endswith(".py") and re.search(r'correlation_id', txt) \
                and re.search(r'tenant_id', txt) and ("log" in rel or "log" in name):
            hits["structured_logging"].append(rel)

        # --- review pack (assembled object+sources+conflicts+proposed decision for human sign-off) ---
        if re.search(r'review[_-]?pack|review[_-]?ticket|review[_-]?queue', name + " " + txt, re.I) \
                and ("review" in rel or "review" in name):
            hits["review_pack"].append(rel)

        # --- dependency emulator (deterministic offline stub satisfying a real port) ---
        if name.endswith(".py") and re.search(r'@v1|deterministic.*stub|\bstub\b.*deterministic|offline.*stub|synthetic.*fixture', txt) \
                and (rel.startswith("scripts/ingest/") or "adapters/object_store" in rel or "stub" in name):
            hits["dependency_emulator"].append(rel)

        # --- multi-source fixture (same pipeline driven from several sources) ---
        if re.search(r'multi[_-]?source', name + " " + rel, re.I):
            hits["multi_source_fixture"].append(rel)

        # ---- anti-patterns ----
        if name.endswith(".py"):
            m = _PROVIDER_IMPORT_RE.search(txt)
            if m and not _rel_in(rel, _PROVIDER_ALLOWED) and not name.startswith("check_"):
                anti.append({"kind": "raw_provider_import", "path": rel, "detail": f"imports {m.group(1)} outside an adapter/gateway home"})
            mn = _NETWORK_IMPORT_RE.search(txt)
            if mn and not _rel_in(rel, _PROVIDER_ALLOWED) and not name.startswith("check_") and not rel.startswith("docs/"):
                anti.append({"kind": "raw_network_import", "path": rel, "detail": f"imports {mn.group(1)} outside an adapter/ingest home"})
            if rel.startswith("src/baltor/processors/") and _SQLITE_RE.search(txt):
                anti.append({"kind": "raw_sqlite_in_processor", "path": rel, "detail": "processor opens sqlite directly instead of going through the ledger/store"})
            if _VAGUE_NAME_RE.match(name):
                anti.append({"kind": "vague_filename", "path": rel, "detail": f"vague filename '{name}' hides intent"})

    # de-dup + sort every hit list
    for k in hits:
        hits[k] = sorted(set(hits[k]))
    anti = sorted({(a["kind"], a["path"], a["detail"]) for a in anti})
    anti = [{"kind": k, "path": p, "detail": d} for (k, p, d) in anti]

    return _assemble(hits, anti, registry)


def _rel_in(rel: str, prefixes: tuple[str, ...]) -> bool:
    for pre in prefixes:
        if pre.endswith(".py"):
            if rel == pre:
                return True
        elif rel.startswith(pre.rstrip("/") + "/") or rel == pre.rstrip("/"):
            return True
        elif Path(rel).name.startswith(pre.split("/")[-1]) and "/" not in pre:
            return True
    # name-prefix allow (check_/build_/scaffold_)
    nm = Path(rel).name
    for pre in prefixes:
        base = pre.split("/")[-1]
        if base.endswith("_") and nm.startswith(base):
            return True
    return False


def _load_registry(root: Path) -> dict[str, Any]:
    reg_path = root / REGISTRY_REL
    if not reg_path.exists():
        # fall back to the canonical repo registry so a fixture scan can still map shapes
        reg_path = _REPO / REGISTRY_REL
    if not reg_path.exists():
        return {"patterns": []}
    try:
        return json.loads(reg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"patterns": []}


def _pattern_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p.get("pattern_id"): p for p in registry.get("patterns", []) if p.get("pattern_id")}


def _assemble(hits: dict[str, list[str]], anti: list[dict[str, str]], registry: dict[str, Any]) -> dict[str, Any]:
    pidx = _pattern_index(registry)

    detected_patterns: list[dict[str, Any]] = []
    one_offs: list[dict[str, Any]] = []
    unstandardized: list[dict[str, Any]] = []
    candidate_templates: list[dict[str, Any]] = []
    recommended: list[dict[str, Any]] = []
    waivers: list[dict[str, Any]] = []

    # collapse shapes onto their canonical pattern_id (proof_script: check_proof + self_test together)
    by_pattern: dict[str, list[str]] = {}
    for shape, examples in hits.items():
        pid = SHAPE_TO_PATTERN[shape]
        by_pattern.setdefault(pid, [])
        by_pattern[pid].extend(examples)
    for pid in by_pattern:
        by_pattern[pid] = sorted(set(by_pattern[pid]))

    for pid in sorted(by_pattern):
        examples = by_pattern[pid]
        reg = pidx.get(pid, {})
        maturity = reg.get("maturity", "unknown")
        templates = reg.get("template_ids", [])
        entry = {
            "pattern_id": pid,
            "examples_count": len(examples),
            "examples": examples[:12],  # cap for report readability; count is exact above
            "registry_maturity": maturity,
            "in_registry": pid in pidx,
        }
        if len(examples) >= MIN_REPEAT:
            detected_patterns.append(entry)
            if maturity == "candidate":
                unstandardized.append({"pattern_id": pid, "examples_count": len(examples),
                                       "note": "built >= twice but registry maturity is still 'candidate' — promote to 'standard'"})
                recommended.append({"pattern_id": pid, "from": "candidate", "to": "standard",
                                    "evidence_count": len(examples)})
            if not templates:
                candidate_templates.append({"pattern_id": pid, "examples_count": len(examples),
                                            "note": "repeated shape with no template_ids — a template would let new instances start standard"})
        elif len(examples) == 1:
            one_offs.append({"pattern_id": pid, "example": examples[0],
                             "note": "seen once — a second occurrence makes it a pattern"})

    # waivers_needed: a registry pattern claimed standard/enforced but the scan found fewer than MIN_REPEAT examples
    for pid, reg in pidx.items():
        maturity = reg.get("maturity")
        if maturity in ("standard", "enforced"):
            found = by_pattern.get(pid, [])
            if len(found) < MIN_REPEAT and not reg.get("waiver_allowed", False):
                waivers.append({"pattern_id": pid, "maturity": maturity, "examples_found": len(found),
                                "note": "registry claims standard/enforced but scan found < 2 examples — confirm detector or file a waiver"})

    return {
        "detected_patterns": detected_patterns,
        "unstandardized_repetitions": unstandardized,
        "one_offs": one_offs,
        "candidate_templates": candidate_templates,
        "anti_patterns": anti,
        "recommended_standards": recommended,
        "waivers_needed": waivers,
    }


def _summary_line(report: dict[str, Any]) -> str:
    return (f"detected_patterns={len(report['detected_patterns'])} "
            f"unstandardized={len(report['unstandardized_repetitions'])} "
            f"one_offs={len(report['one_offs'])} "
            f"candidate_templates={len(report['candidate_templates'])} "
            f"anti_patterns={len(report['anti_patterns'])} "
            f"recommended_standards={len(report['recommended_standards'])} "
            f"waivers_needed={len(report['waivers_needed'])}")


def _write_report(report: dict[str, Any], root: Path) -> Path:
    out = root / REPORT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def render_markdown(report: dict[str, Any]) -> str:
    """Render the report JSON to a deterministic Markdown status page (no wall-clock, sorted)."""
    L: list[str] = []
    L.append("# Pattern Miner Report")
    L.append("")
    L.append("> Generated by `scripts/pattern_miner.py --scan`. Do not hand-edit; re-run the miner. "
             "Every path below is real (it existed on disk at scan time).")
    L.append("")
    L.append(f"**Roll-up:** {_summary_line(report)}")
    L.append("")

    def section(title: str, key: str, fmt) -> None:
        items = report[key]
        L.append(f"## {title} ({len(items)})")
        L.append("")
        if not items:
            L.append("_none_")
            L.append("")
            return
        for it in items:
            L.append(f"- {fmt(it)}")
        L.append("")

    section("Detected patterns", "detected_patterns",
            lambda it: f"`{it['pattern_id']}` — {it['examples_count']} examples, registry maturity `{it['registry_maturity']}`"
                       + (f" — e.g. `{it['examples'][0]}`" if it.get("examples") else ""))
    section("Unstandardized repetitions", "unstandardized_repetitions",
            lambda it: f"`{it['pattern_id']}` — {it['examples_count']} examples — {it['note']}")
    section("Candidate templates", "candidate_templates",
            lambda it: f"`{it['pattern_id']}` — {it['examples_count']} examples — {it['note']}")
    section("Recommended standard promotions", "recommended_standards",
            lambda it: f"`{it['pattern_id']}` — {it['from']} -> {it['to']} ({it['evidence_count']} examples)")
    section("Anti-patterns", "anti_patterns",
            lambda it: f"`{it['kind']}` at `{it['path']}` — {it['detail']}")
    section("One-offs (watch list)", "one_offs",
            lambda it: f"`{it['pattern_id']}` — `{it['example']}` — {it['note']}")
    section("Waivers needed", "waivers_needed",
            lambda it: f"`{it['pattern_id']}` — maturity `{it['maturity']}`, found {it['examples_found']} — {it['note']}")

    return "\n".join(L) + "\n"


def _write_markdown(report: dict[str, Any], root: Path) -> Path:
    out = root / REPORT_MD_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_markdown(report), encoding="utf-8")
    return out


# ------------------------------------------------------------------------------------------------------
# self-test: a tiny deterministic fixture tree (offline, temp dir, cleaned up).
# ------------------------------------------------------------------------------------------------------
def _build_fixture(root: Path) -> None:
    """Create a minimal but realistic tree exercising the detectors. Deterministic content only."""
    (root / "scripts").mkdir(parents=True)
    (root / "src/baltor/adapters/source").mkdir(parents=True)
    (root / "src/baltor/processors/decompose").mkdir(parents=True)
    (root / "architecture").mkdir(parents=True)
    (root / "schemas").mkdir(parents=True)
    (root / "web/baltor").mkdir(parents=True)
    (root / "docs/concepts").mkdir(parents=True)
    (root / ".agent").mkdir(parents=True)

    # two proof scripts (-> proof_script_pattern, count >= MIN_REPEAT)
    (root / "scripts/check_alpha.py").write_text(
        "import argparse\n# CLI: --self-test\nif '--self-test':\n    print('PASS')\n", encoding="utf-8")
    (root / "scripts/check_beta.py").write_text(
        "import argparse\n# --self-test supported\nprint('PASS')\n", encoding="utf-8")
    # an api server with two routes (-> api_projection_route_pattern)
    (root / "scripts/baltor_demo_server_fixture.py").write_text(
        'ROUTES = ["/api/health", "/api/events"]\n', encoding="utf-8")
    (root / "scripts/another_server_fixture.py").write_text(
        'HANDLER = "/api/status"\n', encoding="utf-8")
    # two web pages calling /api/ (-> ui_projection_page_pattern)
    (root / "web/baltor/page_one.html").write_text(
        '<script>fetch("/api/health")</script>\n', encoding="utf-8")
    (root / "web/baltor/page_two.html").write_text(
        '<script>fetch("/api/events")</script>\n', encoding="utf-8")
    # two source adapters (-> source_adapter_pattern)
    (root / "src/baltor/adapters/source/alpha_source.py").write_text(
        "class AlphaSource:\n    adapter_id = 'alpha@v1'\n", encoding="utf-8")
    (root / "src/baltor/adapters/source/beta_source.py").write_text(
        "class BetaSource:\n    adapter_id = 'beta@v1'\n", encoding="utf-8")
    # two docs pages (-> documentation_page_pattern)
    (root / "docs/concepts/one.md").write_text("# One\n", encoding="utf-8")
    (root / "docs/concepts/two.md").write_text("# Two\n", encoding="utf-8")
    # two schema files (-> contract_schema_pattern)
    (root / "schemas/alpha.schema.json").write_text('{"$id":"alpha"}\n', encoding="utf-8")
    (root / "schemas/beta.schema.json").write_text('{"$id":"beta"}\n', encoding="utf-8")
    # a json registry with version (-> section_maturity_entry_pattern) + capability catalog
    (root / "architecture/some_matrix.json").write_text('{"version":"1.0","sections":[]}\n', encoding="utf-8")
    (root / "architecture/capability_catalog.json").write_text(
        '{"version":"1.0","capability_slots":[]}\n', encoding="utf-8")
    # ANTI-PATTERN: raw provider import in a processor + raw sqlite in a processor + vague filename
    (root / "src/baltor/processors/decompose/bad_processor.py").write_text(
        "import openai\nimport sqlite3\nconn = sqlite3.connect('x.db')\n", encoding="utf-8")
    (root / "scripts/utils.py").write_text("# vague\n", encoding="utf-8")
    # a minimal local registry so shape->pattern maps resolve even offline (uses canonical ids)
    (root / REGISTRY_REL).parent.mkdir(parents=True, exist_ok=True)
    (root / REGISTRY_REL).write_text(json.dumps({
        "version": "fixture",
        "patterns": [
            {"pattern_id": "proof_script_pattern", "maturity": "candidate", "template_ids": []},
            {"pattern_id": "api_projection_route_pattern", "maturity": "standard", "template_ids": ["t1"]},
            {"pattern_id": "ui_projection_page_pattern", "maturity": "candidate", "template_ids": []},
            {"pattern_id": "source_adapter_pattern", "maturity": "standard", "template_ids": ["t2"]},
            {"pattern_id": "documentation_page_pattern", "maturity": "standard", "template_ids": ["t3"]},
            {"pattern_id": "contract_schema_pattern", "maturity": "standard", "template_ids": ["t4"]},
            {"pattern_id": "section_maturity_entry_pattern", "maturity": "standard", "template_ids": ["t5"]},
            {"pattern_id": "capability_catalog_entry_pattern", "maturity": "standard", "template_ids": ["t6"]},
        ],
    }) + "\n", encoding="utf-8")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = Path(tempfile.mkdtemp(prefix="pattern_miner_selftest_"))
    try:
        _build_fixture(tmp)
        report = scan(tmp)

        check("report has all seven keys", set(REPORT_KEYS) <= set(report), str(sorted(set(REPORT_KEYS) - set(report))))

        detected_ids = {d["pattern_id"] for d in report["detected_patterns"]}
        check("detected the check_* proof pattern", "proof_script_pattern" in detected_ids, str(sorted(detected_ids)))
        check("detected the API route pattern", "api_projection_route_pattern" in detected_ids, str(sorted(detected_ids)))
        check("detected the docs page pattern", "documentation_page_pattern" in detected_ids, str(sorted(detected_ids)))
        check("detected the web page (/api/) pattern", "ui_projection_page_pattern" in detected_ids, str(sorted(detected_ids)))
        check("detected the source adapter pattern", "source_adapter_pattern" in detected_ids, str(sorted(detected_ids)))

        # determinism: scanning twice yields identical JSON
        report2 = scan(tmp)
        check("scan is deterministic (same input -> same output)",
              json.dumps(report, sort_keys=True) == json.dumps(report2, sort_keys=True))

        # report references pattern_registry entries
        check("detected patterns carry registry maturity (report references the registry)",
              all("registry_maturity" in d and d.get("in_registry") for d in report["detected_patterns"]),
              str([d["pattern_id"] for d in report["detected_patterns"] if not d.get("in_registry")]))

        # anti-patterns: the bad processor + vague file are caught, all referencing REAL fixture files
        anti_kinds = {a["kind"] for a in report["anti_patterns"]}
        check("anti-pattern: raw provider import in processor caught", "raw_provider_import" in anti_kinds, str(sorted(anti_kinds)))
        check("anti-pattern: raw sqlite in processor caught", "raw_sqlite_in_processor" in anti_kinds, str(sorted(anti_kinds)))
        check("anti-pattern: vague filename caught", "vague_filename" in anti_kinds, str(sorted(anti_kinds)))
        check("every anti-pattern path is a real file in the fixture",
              all((tmp / a["path"]).exists() for a in report["anti_patterns"]),
              str([a["path"] for a in report["anti_patterns"] if not (tmp / a["path"]).exists()]))

        # unstandardized: proof_script_pattern is 'candidate' with >=2 examples -> flagged
        check("unstandardized repetition flagged for candidate-maturity repeated shape",
              any(u["pattern_id"] == "proof_script_pattern" for u in report["unstandardized_repetitions"]),
              str(report["unstandardized_repetitions"]))

        # markdown renders without error and contains the roll-up
        md = render_markdown(report)
        check("markdown renders and contains roll-up", "Pattern Miner Report" in md and "Roll-up" in md)
    finally:
        # clean up the temp tree
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'PASS — pattern_miner: 7 report keys; detects proof/api/docs/web/source shapes; flags real anti-patterns; deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pattern miner — scan the repo for repeated shapes and grade them.")
    p.add_argument("--scan", action="store_true", help="scan the repo (or --root) and write the JSON + MD report")
    p.add_argument("--root", default=None, help="root dir to scan (default: repo root)")
    p.add_argument("--self-test", action="store_true", help="run the deterministic fixture self-test")
    a = p.parse_args(argv)

    if a.self_test:
        return _self_test()
    if a.scan:
        root = Path(a.root).resolve() if a.root else _REPO
        report = scan(root)
        rj = _write_report(report, root)
        rm = _write_markdown(report, root)
        print(_summary_line(report))
        print(f"wrote {_rel(rj, root)}")
        print(f"wrote {_rel(rm, root)}")
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
