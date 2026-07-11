#!/usr/bin/env python3
"""scripts.ml_team_role_primitive_minter — mint governed primitives for the 23-role production-ML TEAM: every
role (Product Manager, Tech Lead, Domain Expert, Data Steward, Data Engineer, Analytics Engineer, Data Analyst,
Data Scientist, Labeling Specialist, ML Engineer, MLOps Engineer, Backend Engineer, Frontend Engineer, DevOps,
SRE, QA Engineer, Security Engineer, Privacy/Legal, Responsible-AI Lead, UX Designer, Technical Writer,
Support/Human-Review, Engineering Manager) crossed with its concrete ACTIONS and the TOOLS/technologies it uses.

Each primitive names WHO (role) does WHAT (action) with WHICH tool — e.g. "Data Engineer: build deduplication
logic in Airflow", "SRE: define SLOs with Prometheus", "ML Engineer: register model versions in MLflow". The
role-action-tool taxonomy is inherently concrete, so these are high-quality non-placeholder leads. Deterministic
coprime-strided walk to ``--target``; canonical ids; candidate/serves_truth=false; write refuses verified
corpus; usefulness gate = NON-DESTRUCTIVE routing.

    python3 scripts/ml_team_role_primitive_minter.py --self-test
    python3 scripts/ml_team_role_primitive_minter.py --mint --target 50000
    python3 scripts/ml_team_role_primitive_minter.py --grid-size
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Iterator, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"ml_team_role_primitive_minter requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ROLE_ID_PREFIX = "prim-mlrole"
ROLE_RECORD_TYPE = "ml_team_role_primitive_candidate"
STAGED_FILENAME = "ml_team_role_primitive_candidates.jsonl"
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_COPRIME_STRIDE = 2147483647

# ── the 23 roles: (role, category, (concrete actions...)). Single source. ────────────────────────────────────
_ROLES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("product manager", "product", ("define the business objective", "convert business needs to ML use cases", "define success metrics", "define a rollout strategy", "own the go no-go launch decision", "monitor business impact")),
    ("technical lead", "architecture", ("choose the high-level architecture", "design data flow source to inference", "define service boundaries", "define non-functional requirements", "write architecture decision records", "design rollback and disaster recovery")),
    ("domain expert", "domain", ("define what the target label means", "create labeling guidelines", "catalog edge cases", "build a gold-standard test set", "review false positives and negatives", "define escalation paths")),
    ("data steward", "governance", ("identify approved data sources", "classify sensitive data", "define retention rules", "document data lineage", "define access controls", "enforce data contracts")),
    ("data engineer", "data", ("build ingestion pipelines", "implement schema validation", "build deduplication logic", "handle late-arriving data", "create backfills", "build feature computation pipelines", "make pipelines idempotent", "publish to a feature store")),
    ("analytics engineer", "analytics", ("build curated analytics tables", "define business metrics", "build model performance dashboards", "add SQL tests to models", "maintain the semantic layer")),
    ("data analyst", "analytics", ("explore historical data", "estimate the business opportunity", "measure baseline performance", "run post-launch analysis", "investigate metric regressions")),
    ("data scientist", "modeling", ("define the ML task", "engineer features", "train candidate models", "tune hyperparameters", "run cross-validation", "run error analysis", "check for leakage", "test fairness and robustness", "create explainability reports")),
    ("labeling specialist", "data", ("label examples to guidelines", "review model-suggested labels", "resolve annotation disagreements", "measure inter-annotator agreement", "audit label quality")),
    ("ml engineer", "engineering", ("convert notebooks to production training code", "build reproducible training pipelines", "integrate with a feature store", "optimize model inference", "register model versions", "build batch scoring jobs", "build online inference services", "add input output validation", "implement retraining pipelines")),
    ("mlops engineer", "platform", ("build reusable pipeline templates", "maintain the model registry", "build CI/CD for ML", "implement dev staging prod promotion", "build automated retraining", "enforce model governance gates", "standardize experiment tracking")),
    ("backend engineer", "engineering", ("build inference APIs", "validate incoming requests", "fetch real-time features", "build rate limiting", "build caching", "handle timeouts and retries", "build fallback behavior", "log prediction requests", "write contract tests")),
    ("frontend engineer", "engineering", ("design UI for model outputs", "capture user feedback", "display confidence and explanations", "integrate feature flags", "support A/B test variants", "handle model errors gracefully")),
    ("devops engineer", "infrastructure", ("provision cloud infrastructure", "build CI/CD pipelines", "manage kubernetes clusters", "manage secrets and keys", "configure autoscaling", "support deployment rollback", "manage cost controls")),
    ("site reliability engineer", "reliability", ("define SLIs and SLOs", "create dashboards and alerts", "write runbooks", "handle production incidents", "run load testing", "perform capacity planning", "test failure scenarios", "coordinate rollbacks")),
    ("qa engineer", "quality", ("test data pipeline outputs", "test model input output schemas", "test API behavior", "perform regression testing across model versions", "run load and performance testing", "test rollback procedures", "validate staging before release")),
    ("security engineer", "security", ("perform threat modeling", "review cloud IAM", "add dependency scanning", "add container image scanning", "secure model endpoints", "review prompt injection risks", "add audit logging")),
    ("privacy legal compliance", "compliance", ("review whether data can be used for ML", "review user consent", "review data retention", "run a data protection impact assessment", "review model use in regulated decisions", "create audit documentation")),
    ("responsible ai lead", "risk", ("test model performance by segment", "measure fairness metrics", "perform red teaming", "test robustness", "review safety filters", "evaluate hallucination and toxicity", "create model cards")),
    ("ux designer", "design", ("map user workflows", "design confidence indicators", "design human override flows", "design feedback capture", "test user trust and understanding", "design fallback states")),
    ("technical writer", "docs", ("write model documentation", "write API documentation", "write runbooks", "maintain model and data cards", "document rollback procedures", "write release notes")),
    ("support human review", "operations", ("review uncertain or high-risk outputs", "investigate false positives and negatives", "label production examples", "escalate safety issues", "track manual review workload")),
    ("engineering manager", "delivery", ("plan milestones", "track dependencies", "manage delivery risks", "coordinate production readiness reviews", "coordinate launch approvals", "track post-launch issues")),
)

# tools/technologies axis (union of the role stacks — concrete)
_TOOLS: tuple[str, ...] = (
    "Airflow", "dbt", "Great Expectations", "Feast", "MLflow", "Weights & Biases", "Docker", "Kubernetes",
    "Terraform", "GitHub Actions", "Prometheus", "Grafana", "OpenTelemetry", "Evidently", "Arize", "FastAPI",
    "KServe", "BentoML", "Triton", "Spark", "Kafka", "Snowflake", "BigQuery", "dbt tests", "pytest",
    "Label Studio", "SHAP", "Fairlearn", "Vault", "Argo CD", "Datadog", "PagerDuty", "scikit-learn",
    "PyTorch", "SageMaker", "Vertex AI", "Redis", "Postgres", "Looker", "LaunchDarkly",
)

_STOP = frozenset("a an the for of to in on with and or via using into from as is are be that this it one".split())
_FRAMES: tuple[str, ...] = (
    "A production-ML team primitive: a {role} ({category}) will {action}, using {tool}. Typed input and "
    "output; a reusable, owned step in the ML operating system.",
    "As a {role}, you {action} with {tool} ({category} responsibility). A composable, typed primitive.",
    "{action} — the '{role}' team primitive ({category}), implemented with {tool}. Typed edges.",
    "For the {category} layer, a {role} {action} via {tool}. Reusable and owned; typed input/output.",
)

#: flattened (role, category, action) spine
_ROLE_SPINE: tuple[tuple[str, str, str], ...] = tuple(
    (role, cat, action) for role, cat, actions in _ROLES for action in actions)


def axis_sizes() -> dict[str, int]:
    return {"roles": len(_ROLES), "role_actions_total": len(_ROLE_SPINE), "tools": len(_TOOLS)}


def grid_size() -> int:
    return len(_ROLE_SPINE) * len(_TOOLS)


def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    return ("".join(p[:1].upper() + p[1:] for p in parts if p) or "X")[:60]


def _card(idx: tuple[int, int]) -> dict[str, Any]:
    ai, ti = idx
    role, category, action = _ROLE_SPINE[ai]
    tool = _TOOLS[ti]
    title = f"{role}: {action} with {tool}"
    frame = _FRAMES[(ai * 3 + ti) % len(_FRAMES)]
    blackbox = frame.format(role=role, category=category, action=action, tool=tool)
    tokens = [w.lower() for w in re.findall(r"[a-z]+", (action + " " + role).lower()) if w.lower() not in _STOP][:8]
    input_edge = _camel(role.split()[0], action.split()[0], "input")
    output_edge = _camel(action.split()[0], _camel(tool), "result")
    pid = canonical_id(ROLE_ID_PREFIX, title, blackbox)
    return {
        "record_type": ROLE_RECORD_TYPE, "schema_version": 1, "kind": "route.primitive",
        "primitive_id": pid, "title": title[:180], "blackbox": blackbox[:1200],
        "input_edge": input_edge, "output_edge": output_edge, "blocking_keys": tokens,
        "role": {"name": role, "category": category, "action": action, "tool": tool},
        "capability_tags": [f"role:{role.replace(' ', '_')}", f"category:{category}",
                            f"action:{action.replace(' ', '_')}", f"tool:{_camel(tool).lower()}"],
        "contract": {"input": f"the {role}'s work context ({category})",
                     "output": f"a typed result of '{action}' via {tool}"},
        "provenance": {"minter": "scripts.ml_team_role_primitive_minter", "grid_size": grid_size()},
        "promotion_blockers": ["source_evidence", "correctness_proof", "usefulness_or_enrichment"],
        "readiness": "ml_team_role_candidate_unproven", **BOUNDARY,
    }


def _strided_indices(target: int) -> Iterator[tuple[int, int]]:
    total = grid_size()
    sizes = [len(_ROLE_SPINE), len(_TOOLS)]
    for i in range(min(target, total)):
        flat = (i * _COPRIME_STRIDE) % total
        rem = flat
        idx = []
        for sz in reversed(sizes):
            idx.append(rem % sz)
            rem //= sz
        yield tuple(reversed(idx))  # type: ignore[misc]


def mint(target: int) -> list[dict[str, Any]]:
    if target < 1:
        raise ValueError("target must be >= 1")
    cards: list[dict[str, Any]] = []
    seen: set = set()
    for idx in _strided_indices(target):
        c = _card(idx)
        if c["primitive_id"] in seen:
            raise ValueError(f"duplicate mint for {c['title']!r}")
        seen.add(c["primitive_id"])
        cards.append(c)
    return cards


def validate_card(card: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if card.get("primitive_id") != canonical_id(ROLE_ID_PREFIX, card.get("title", ""), card.get("blackbox", "")):
        problems.append("primitive_id does not recompute")
    for ef in ("input_edge", "output_edge"):
        if not _CAMEL_EDGE_RE.match(str(card.get(ef) or "")):
            problems.append(f"{ef} not CamelCase")
    if card.get("serves_truth") is not False or card.get("candidate") is not True:
        problems.append("candidate boundary not stamped")
    text = f"{card.get('title','')} {card.get('blackbox','')}".lower()
    if not all(t in text for t in card.get("blocking_keys", [])[:2]):
        problems.append("blackbox does not carry its leading tokens")
    return problems


def staged_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / STAGED_FILENAME


def write_staged(cards: list[dict[str, Any]], target_path: Optional[Path] = None) -> dict[str, Any]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = target_path or staged_path()
    if p.name != STAGED_FILENAME:
        raise ValueError(f"refusing to write to {p.name!r} — only {STAGED_FILENAME!r} allowed")
    if p.is_symlink() or (p.exists() and p.resolve().name in _VERIFIED_CORPUS_FILENAMES):
        raise ValueError("refused: symlink or verified-corpus target")
    for c in cards:
        probs = validate_card(c)
        if probs:
            raise ValueError(f"card {c.get('primitive_id')} failed validation: {probs}")
    existing = {str(r.get("primitive_id")) for r in (read_jsonl_tolerant(p) if p.exists() else [])}
    appended = 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for c in cards:
            if str(c["primitive_id"]) in existing:
                continue
            existing.add(str(c["primitive_id"]))
            fh.write(json.dumps(c, sort_keys=True) + "\n")
            appended += 1
    return {"appended": appended, "on_file": len(existing), "path": str(p), **BOUNDARY}


def quality_report(cards: list[dict[str, Any]]) -> dict[str, Any]:
    from scripts.primitive_usefulness_gate import measure_pool  # noqa: PLC0415
    m = measure_pool(cards, "ml_team_role_mint")
    return {k: m[k] for k in ("n_cards_scored", "placeholder_rate", "weak_rate", "verdict_counts", "stamped_clusters")}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("all 23 roles are encoded", len(_ROLES) == 23))
    s = axis_sizes()
    checks.append(("role-actions + grid size computed",
                   s["role_actions_total"] >= 130 and grid_size() == s["role_actions_total"] * s["tools"]
                   and grid_size() > 5000))
    cards = mint(1000)
    checks.append(("mints deterministically + byte-identical",
                   len(cards) == 1000 and json.dumps(cards, sort_keys=True) == json.dumps(mint(1000), sort_keys=True)))
    checks.append(("every card validates", all(not validate_card(c) for c in cards)))
    checks.append(("ids unique", len({c["primitive_id"] for c in cards}) == len(cards)))
    checks.append(("the stride covers many roles + tools + categories",
                   len({c["role"]["name"] for c in cards}) >= 18
                   and len({c["role"]["tool"] for c in cards}) >= 20
                   and len({c["role"]["category"] for c in cards}) >= 10))
    import tempfile  # noqa: PLC0415
    refused = False
    try:
        write_staged(cards[:1], target_path=Path(tempfile.gettempdir()) / "verified_factory_primitive_cards.jsonl")
    except ValueError:
        refused = True
    checks.append(("write_staged refuses a verified corpus filename", refused))
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / STAGED_FILENAME
        a = write_staged(cards[:50], target_path=tp)
        b = write_staged(cards[:50], target_path=tp)
        checks.append(("append-dedupe", a["appended"] == 50 and b["appended"] == 0))
    qr = quality_report(cards)
    checks.append(("usefulness gate scores the mint", set(qr["verdict_counts"]) == {"pass", "weak", "placeholder"}))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - ml_team_role_primitive_minter: primitives for all 23 production-ML team roles "
          f"({s['role_actions_total']} role-actions x {s['tools']} tools = a {grid_size():,}-point grid); "
          f"role x action x tool; deterministic strided mint; canonical ids; typed edges; NON-DESTRUCTIVE "
          f"gate. serves_truth=false.")
    return 0


def _mint(target: int) -> int:
    cards = mint(target)
    qr = quality_report(cards)
    wrote = write_staged(cards)
    rec = {"record_type": "ml_team_role_mint_receipt", "target": target, "minted": len(cards),
           "appended": wrote["appended"], "on_file": wrote["on_file"], "grid_size": grid_size(),
           "axis_sizes": axis_sizes(), "distinct_roles": len({c["role"]["name"] for c in cards}),
           "quality_gate": qr, "routing": "placeholder/weak route to enrichment; NONE discarded", **BOUNDARY}
    out = resource("data") / "dev-intel" / "session_emulation" / "ml_team_role_mint_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("target", "minted", "appended", "grid_size", "distinct_roles",
                                          "quality_gate")}, indent=2, sort_keys=True))
    print(f"\nstaged: {wrote['path']}\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mint", action="store_true")
    ap.add_argument("--target", type=int, default=50_000)
    ap.add_argument("--grid-size", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.grid_size:
        print(json.dumps({"grid_size": grid_size(), "axis_sizes": axis_sizes()}, indent=2))
        return 0
    if args.mint:
        return _mint(args.target)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
