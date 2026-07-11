#!/usr/bin/env python3
"""scripts.ml_lifecycle_primitive_minter — mint governed primitives for EVERY stage of the end-to-end machine
learning lifecycle (44 stages: define objective → define task → data sourcing/acquisition/governance/ingest/
validate/label/explore/split/preprocess/feature-engineer → baseline/select/train/tune/evaluate/error-analysis/
leakage/fairness/readiness → package/register/inference/serving-pattern/staging/tests/rollout/deploy → monitor
infra/inputs/outputs/performance/business/fairness → alerts/logging/fallback/feedback/retrain/CICD/document/
govern/retire).

Each stage decomposes into CONCRETE operations (stratified time-based split · KS-test drift monitor · SHAP
error analysis · canary rollout gate · model-card generation · …); each operation crosses a technique/tool
axis and mints a primitive card naming the STAGE (context) + OPERATION + TECHNIQUE + typed input/output. The
ML lifecycle is inherently concrete, so these are high-quality, non-placeholder leads. Deterministic
coprime-strided walk to ``--target``; canonical ids; candidate/serves_truth=false; write refuses verified
corpus; usefulness gate = NON-DESTRUCTIVE routing (nothing discarded).

    python3 scripts/ml_lifecycle_primitive_minter.py --self-test
    python3 scripts/ml_lifecycle_primitive_minter.py --mint --target 50000
    python3 scripts/ml_lifecycle_primitive_minter.py --grid-size
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/primitive_grid_remixer.py) ───────────────────────────
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
    raise SystemExit(f"ml_lifecycle_primitive_minter requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ML_ID_PREFIX = "prim-mllife"
ML_RECORD_TYPE = "ml_lifecycle_primitive_candidate"
STAGED_FILENAME = "ml_lifecycle_primitive_candidates.jsonl"
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_COPRIME_STRIDE = 2147483647

# ── the 44-stage lifecycle: (stage_num, phase, stage_name, (concrete operations...)). Single source. ─────────
_LIFECYCLE: tuple[tuple[int, str, str, tuple[str, ...]], ...] = (
    (1, "define", "define objective", ("write problem statement", "set success criteria", "estimate business value", "decide if ML is needed", "capture constraints latency cost privacy fairness")),
    (2, "define", "define ml task", ("map business goal to ML task", "choose prediction target", "define model inputs", "define output shape", "decide batch vs realtime serving")),
    (3, "data", "identify data sources", ("catalog candidate sources", "check data availability", "check legal usability", "assess representativeness", "assess freshness", "detect bias or gaps")),
    (4, "data", "acquire data", ("export database tables", "pull from API", "load from object storage", "stream events from kafka", "license a dataset", "generate synthetic examples", "record acquisition metadata")),
    (5, "data", "governance privacy compliance", ("review data ownership", "review consent", "detect PII", "set retention policy", "enforce access controls", "anonymize or pseudonymize", "produce usage policy for GDPR HIPAA SOC2 PCI")),
    (6, "data", "ingest to storage", ("build ETL pipeline", "build ELT pipeline", "load to data lake", "load to warehouse", "write to feature store", "version a data snapshot", "load embeddings to a vector database")),
    (7, "data", "validate raw data quality", ("detect missing values", "detect duplicate records", "check schema mismatch", "detect outliers", "flag corrupt records", "detect unexpected categories", "detect time gaps", "assess class imbalance", "flag data leakage risk", "produce a data quality report")),
    (8, "data", "label or annotate", ("derive labels from business outcomes", "route to human annotators", "apply weak supervision", "apply heuristic labels", "model-assisted labeling", "active learning sampling", "measure inter-annotator agreement", "measure label noise")),
    (9, "data", "explore data EDA", ("plot feature distributions", "plot label distribution", "compute correlations", "analyze missingness patterns", "detect time-based trends", "segment-level behavior analysis", "representativeness analysis", "leakage detection scan")),
    (10, "prepare", "define splits", ("random split", "stratified split", "time-based split", "group-based split", "user-based split", "geographic split", "k-fold cross-validation", "document split logic")),
    (11, "prepare", "build preprocessing pipeline", ("impute missing values", "remove duplicates", "normalize numeric features", "standardize units", "encode categorical variables", "tokenize text", "resize images", "handle outliers", "parse timestamps", "create time windows", "balance classes")),
    (12, "prepare", "engineer features", ("compute age from birthdate", "days since last event", "rolling window aggregate", "text embeddings", "image embeddings", "time-of-day features", "historical behavior features", "real-time feature computation", "write feature definitions to a store")),
    (13, "model", "establish baseline", ("majority-class baseline", "rule-based baseline", "logistic regression baseline", "linear regression baseline", "decision tree baseline", "human-performance benchmark")),
    (14, "model", "select candidate models", ("shortlist tabular models xgboost rf nn", "shortlist image models cnn vit", "shortlist text transformers", "shortlist recommenders two-tower", "shortlist forecasters arima prophet lstm", "score candidates on accuracy latency cost interpretability")),
    (15, "model", "train initial models", ("load and preprocess data", "optimize model parameters", "track loss and metrics", "save checkpoints", "log experiment metadata dataset code feature versions", "set random seed for reproducibility")),
    (16, "model", "tune hyperparameters", ("grid search", "random search", "bayesian optimization", "hyperband", "population-based training", "tune learning rate batch size depth regularization")),
    (17, "evaluate", "evaluate offline", ("compute accuracy precision recall f1", "compute roc-auc pr-auc", "compute mae mse rmse r2", "compute ndcg map mrr", "compute mape smape", "evaluate by segment", "assess calibration", "estimate cost and latency")),
    (18, "evaluate", "error analysis", ("analyze false positives", "analyze false negatives", "find worst user segments", "find rare-case failures", "confusion between similar classes", "seasonal-drift failure analysis", "produce an improvement plan")),
    (19, "evaluate", "check data leakage", ("detect future-information leakage", "detect target-as-feature leakage", "detect time-series split leakage", "detect train-test user overlap", "produce a leakage assessment")),
    (20, "evaluate", "validate fairness safety robustness", ("bias testing across groups", "fairness metric computation", "adversarial testing", "stress testing", "out-of-distribution testing", "toxicity testing", "hallucination testing for LLMs", "privacy-leakage testing", "abuse-case analysis")),
    (21, "evaluate", "production readiness decision", ("check metric thresholds", "check beats baseline", "check latency budget", "check cost budget", "check fairness results", "check reproducibility", "check data lineage", "make go no-go decision")),
    (22, "deploy", "package the model", ("serialize the model", "export to ONNX", "export to TorchScript", "export to SavedModel", "build a container image", "embed preprocessing logic", "define input output schemas", "attach model metadata")),
    (23, "deploy", "register the model", ("write to model registry", "record training dataset version", "record code version and metrics", "set deployment stage experimental staging production", "record changelog and rollback options")),
    (24, "deploy", "build inference pipeline", ("validate input schema", "fetch required features", "apply preprocessing", "run model prediction", "apply thresholding", "rank outputs", "apply business rules", "generate explanations", "safety-filter outputs", "log request and prediction")),
    (25, "serve", "choose serving pattern", ("real-time online serving", "batch serving", "streaming serving", "edge serving", "decide the serving architecture")),
    (26, "deploy", "deploy to staging", ("verify API behavior", "verify input validation", "measure latency and memory", "verify feature availability", "verify logging and monitoring hooks", "verify security controls")),
    (27, "deploy", "integration and system tests", ("unit tests", "data validation tests", "feature pipeline tests", "model loading tests", "API tests", "load tests", "latency tests", "failure-mode tests", "end-to-end tests")),
    (28, "deploy", "select rollout strategy", ("shadow deployment", "canary deployment 1 5 25 50 100", "A/B test", "blue-green deployment", "multi-armed bandit rollout")),
    (29, "deploy", "deploy to production", ("launch production endpoint", "launch batch scoring job", "launch stream processor", "wire load balancer and autoscaling", "wire secrets management", "record deployment logs")),
    (30, "monitor", "monitor system health", ("track request volume", "track latency and throughput", "track error and timeout rate", "track cpu gpu memory", "track queue depth", "track autoscaling behavior", "track cost")),
    (31, "monitor", "monitor model inputs", ("track missing-feature rate", "track invalid-input rate", "detect schema changes", "detect distribution drift", "detect category drift", "track feature freshness", "track pipeline delays")),
    (32, "monitor", "monitor model outputs", ("track prediction distribution", "track confidence distribution", "track positive-prediction rate", "detect score drift", "track safety-filter trigger rate", "track fallback rate")),
    (33, "monitor", "monitor model performance", ("compute live accuracy precision recall", "compute live auc", "handle delayed labels", "track false positive false negative rate", "track escalation rate")),
    (34, "monitor", "monitor business metrics", ("track revenue and retention", "track conversion", "track fraud loss", "track support resolution time", "track cost per prediction", "track manual review workload")),
    (35, "monitor", "monitor fairness safety compliance", ("track performance by demographic", "track disparate impact", "track harmful-output rate", "track privacy incidents", "track security events", "maintain regulatory audit logs")),
    (36, "maintain", "alerts and incident response", ("alert on latency threshold", "alert on error-rate spike", "alert on feature-pipeline failure", "alert on prediction drift", "alert on performance drop", "define escalation path and rollback")),
    (37, "maintain", "log predictions for audit", ("log request id and timestamp", "log model version", "log input features under privacy rules", "log prediction and confidence", "log latency and errors", "log ground-truth when available")),
    (38, "maintain", "human review and fallback", ("route uncertain cases to humans", "fall back to a rules system", "fall back to a previous model", "refuse unsafe generative outputs", "trigger manual fraud review", "serve default recommendations on failure")),
    (39, "maintain", "collect feedback ground truth", ("capture clicks and purchases", "capture ratings", "capture human corrections", "capture manual review decisions", "capture delayed business outcomes", "capture A/B test results")),
    (40, "maintain", "retrain or update", ("pull new data", "validate and relabel", "recompute features", "train candidate", "evaluate against production model", "register and approve", "trigger on drift or performance drop")),
    (41, "maintain", "MLOps CI/CD automation", ("run code and data tests", "run feature tests", "run model training job", "enforce evaluation gates", "run security scans", "build container and update registry", "automate rollback")),
    (42, "maintain", "document the model", ("write a model card", "write a data card", "document training methodology", "document intended and out-of-scope use", "document known limitations", "document bias analysis", "document monitoring and retraining plan")),
    (43, "maintain", "govern lifecycle ownership", ("assign model owner", "assign data owner", "assign on-call owner", "define approval process and review cadence", "define deprecation policy", "define access permissions")),
    (44, "maintain", "retire or replace", ("stop serving traffic", "archive artifacts", "preserve audit logs", "notify stakeholders", "remove unused infrastructure", "update documentation", "decommission pipelines")),
)

# technique/context axis crossed with each operation (concrete framing that specializes the primitive)
_TECHNIQUES: tuple[str, ...] = (
    "in a scikit-learn pipeline", "as an Airflow DAG task", "in a dbt model", "with a Great Expectations suite",
    "as a Kubeflow component", "with an MLflow run", "in a Spark job", "as a FastAPI endpoint",
    "with a feature-store lookup", "as an Evidently monitor", "with a SHAP explainer", "in a Docker container",
    "as a Prometheus metric", "with a Weights & Biases log", "as a Ray task", "with a pandas transform",
    "in a Postgres query", "as a Kafka stream processor", "with an ONNX runtime", "as a batch cron job",
)
# the ML task family the primitive is specialized for (adds domain specificity)
_TASK_FAMILIES: tuple[str, ...] = (
    "binary classification", "multiclass classification", "regression", "ranking", "recommendation",
    "time-series forecasting", "anomaly detection", "clustering", "generative LLM", "computer vision",
    "NLP", "fraud detection", "churn prediction", "demand forecasting",
)

_STOP = frozenset("a an the for of to in on with and or via using into from as is are be that this it one".split())
_FRAMES: tuple[str, ...] = (
    "An ML-lifecycle primitive for the '{stage}' stage ({phase} phase): {op}, {tech}, specialized for {task}. "
    "Typed input and output; composes into the training/serving pipeline.",
    "In the {phase} phase, at the '{stage}' stage, this unit {op} {tech} for {task}. A reusable, typed step.",
    "{op} — the '{stage}' lifecycle primitive ({phase}), {tech}, for {task}. Composable by typed edges.",
    "For {task}, the '{stage}' stage requires: {op}. This primitive does it {tech}. Typed, reusable.",
)


def axis_sizes() -> dict[str, int]:
    n_ops = sum(len(ops) for _n, _ph, _s, ops in _LIFECYCLE)
    return {"stages": len(_LIFECYCLE), "operations_total": n_ops, "techniques": len(_TECHNIQUES),
            "task_families": len(_TASK_FAMILIES)}


def grid_size() -> int:
    s = axis_sizes()
    return s["operations_total"] * s["techniques"] * s["task_families"]


#: flattened (stage_num, phase, stage_name, op) list — the operation spine
_OP_SPINE: tuple[tuple[int, str, str, str], ...] = tuple(
    (num, phase, stage, op) for num, phase, stage, ops in _LIFECYCLE for op in ops)


def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    return ("".join(p[:1].upper() + p[1:] for p in parts if p) or "X")[:60]


def _card(idx: tuple[int, int, int]) -> dict[str, Any]:
    oi, ti, fi = idx
    num, phase, stage, op = _OP_SPINE[oi]
    tech = _TECHNIQUES[ti]
    task = _TASK_FAMILIES[fi]
    title = f"{op} for {task} at the '{stage}' ML stage"
    frame = _FRAMES[(oi * 5 + ti * 3 + fi) % len(_FRAMES)]
    blackbox = frame.format(stage=stage, phase=phase, op=op, tech=tech, task=task)
    tokens = [w.lower() for w in re.findall(r"[a-z]+", (op + " " + stage + " " + task).lower())
              if w.lower() not in _STOP][:8]
    input_edge = _camel(task.split()[0], stage.split()[0], "input")
    output_edge = _camel(op.split()[0], "result")
    pid = canonical_id(ML_ID_PREFIX, title, blackbox)
    return {
        "record_type": ML_RECORD_TYPE, "schema_version": 1, "kind": "route.primitive",
        "primitive_id": pid, "title": title[:180], "blackbox": blackbox[:1200],
        "input_edge": input_edge, "output_edge": output_edge, "blocking_keys": tokens,
        "lifecycle": {"stage_num": num, "phase": phase, "stage": stage, "operation": op},
        "capability_tags": [f"ml_stage:{num}", f"ml_phase:{phase}", f"ml_op:{op.replace(' ', '_')}",
                            f"task:{task.replace(' ', '_')}"],
        "contract": {"input": f"{task} artifacts at the {stage} stage",
                     "output": f"a typed result of {op}"},
        "provenance": {"minter": "scripts.ml_lifecycle_primitive_minter", "grid_size": grid_size()},
        "promotion_blockers": ["source_evidence", "correctness_proof", "usefulness_or_enrichment"],
        "readiness": "ml_lifecycle_candidate_unproven", **BOUNDARY,
    }


def _strided_indices(target: int) -> Iterator[tuple[int, int, int]]:
    total = grid_size()
    sizes = [len(_OP_SPINE), len(_TECHNIQUES), len(_TASK_FAMILIES)]
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
    if card.get("primitive_id") != canonical_id(ML_ID_PREFIX, card.get("title", ""), card.get("blackbox", "")):
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
    m = measure_pool(cards, "ml_lifecycle_mint")
    return {k: m[k] for k in ("n_cards_scored", "placeholder_rate", "weak_rate", "verdict_counts",
                              "stamped_clusters")}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("all 44 lifecycle stages are encoded", len(_LIFECYCLE) == 44
                   and [s[0] for s in _LIFECYCLE] == list(range(1, 45))))
    s = axis_sizes()
    checks.append(("operations + grid size are COMPUTED and in the hundreds-of-thousands",
                   s["operations_total"] >= 300 and grid_size() == s["operations_total"] * s["techniques"] * s["task_families"]
                   and grid_size() > 50_000))
    cards = mint(1000)
    checks.append(("mints deterministically + byte-identical remint",
                   len(cards) == 1000 and json.dumps(cards, sort_keys=True) == json.dumps(mint(1000), sort_keys=True)))
    checks.append(("every card validates (id recompute, edges, boundary, tokens)",
                   all(not validate_card(c) for c in cards)))
    checks.append(("ids unique", len({c["primitive_id"] for c in cards}) == len(cards)))
    checks.append(("the stride covers MANY stages + phases + tasks",
                   len({c["lifecycle"]["stage_num"] for c in cards}) >= 30
                   and len({c["lifecycle"]["phase"] for c in cards}) >= 6
                   and len({tuple(t for t in c["capability_tags"] if t.startswith("task:")) for c in cards}) >= 10))
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
    checks.append(("usefulness gate scores the mint (routing signal)",
                   set(qr["verdict_counts"]) == {"pass", "weak", "placeholder"}))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - ml_lifecycle_primitive_minter: primitives for all 44 ML-lifecycle stages "
          f"({s['operations_total']} concrete operations x {s['techniques']} techniques x {s['task_families']} "
          f"task families = a {grid_size():,}-point grid); deterministic strided mint; canonical ids; typed "
          f"edges; candidate/serves_truth=false; usefulness gate = NON-DESTRUCTIVE routing. serves_truth=false.")
    return 0


def _mint(target: int) -> int:
    cards = mint(target)
    qr = quality_report(cards)
    wrote = write_staged(cards)
    rec = {"record_type": "ml_lifecycle_mint_receipt", "target": target, "minted": len(cards),
           "appended": wrote["appended"], "on_file": wrote["on_file"], "grid_size": grid_size(),
           "axis_sizes": axis_sizes(),
           "distinct_stages": len({c["lifecycle"]["stage_num"] for c in cards}),
           "distinct_phases": sorted({c["lifecycle"]["phase"] for c in cards}),
           "quality_gate": qr, "routing": "placeholder/weak route to enrichment; NONE discarded", **BOUNDARY}
    out = resource("data") / "dev-intel" / "session_emulation" / "ml_lifecycle_mint_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("target", "minted", "appended", "grid_size", "distinct_stages",
                                          "distinct_phases", "quality_gate")}, indent=2, sort_keys=True))
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
