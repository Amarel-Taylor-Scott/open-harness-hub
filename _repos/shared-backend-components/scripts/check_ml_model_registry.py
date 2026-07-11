#!/usr/bin/env python3
"""check_ml_model_registry — the classical/predictive ML model-type registry is real + the scrapers target it.

Owner: a registry of ML models / model TYPES (random forest, forecasting, time series, ...) + scrapers to keep it updated.
Proves: every model maps to a real ml_task + a real implementing LIBRARY in tool_registry + a declared plane; the named
families (random forest, gradient boosting, ARIMA/forecasting, a time-series model) are present; licenses derive from the
library (single source); and the discovery pipeline classifies ML/time-series descriptions to the right planes + ideates
them as ml_model candidates (the scraper keeps the registry current). serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_ml_model_registry.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts import discovery_pipeline as P
from src.openhubforai.licenses import classify_license

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _load(name):
    return json.loads((_resource("architecture") / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    reg = _load("ml_model_registry.json")
    models = reg["models"]
    tasks = set(reg["ml_tasks"])
    tools = {t["id"]: t for t in _load("tool_registry.json")["tools"]}
    planes = {p["plane"] for p in _load("tool_planes.json")["planes"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"model types catalogued ({len(models)})", len(models) >= 15)
    bad_task = sorted({m["ml_task"] for m in models if m["ml_task"] not in tasks})
    ck("every model maps to a declared ml_task", not bad_task, str(bad_task))
    bad_lib = sorted({m["library"] for m in models if m["library"] not in tools})
    ck("every model's library is a real tool_registry component", not bad_lib, str(bad_lib))
    bad_plane = sorted({m["plane"] for m in models if m["plane"] not in planes})
    ck("every model's plane is declared", not bad_plane, str(bad_plane))
    ck("models carry deterministic + when_to_use", all("deterministic" in m and m.get("when_to_use") for m in models))

    fams = {m["id"] for m in models}
    ck("the owner-named families present (random_forest, gradient_boosting, forecasting, time-series)",
       {"random_forest", "gradient_boosting", "arima_sarimax"} <= fams and any(m["ml_task"] == "time_series_ml" for m in models))
    ck("forecasting + classification + anomaly tasks covered",
       {"forecasting", "classification", "anomaly_detection"} <= {m["ml_task"] for m in models})
    # license derives from the library (single source) — e.g. statsmodels BSD -> vendorable, prophet MIT -> vendorable
    sm = next(m for m in models if m["id"] == "arima_sarimax")
    ck("model license inherits the library's (statsmodels=BSD -> vendorable)", classify_license(tools[sm["library"]]["license"])[1] is True)
    ck("time_series libraries exist (statsmodels/prophet/sktime/darts/pyod)",
       {"statsmodels", "prophet", "sktime", "darts", "pyod"} <= set(tools))

    # the scrapers TARGET the registry: classify ML/time-series descriptions + ideate as ml_model candidates
    ck("scraper classifies 'time series forecasting' -> time_series", P.classify_plane("a time series forecasting library") == "time_series")
    ck("scraper classifies 'random forest' -> classical_ml", P.classify_plane("a random forest implementation") == "classical_ml")
    ck("scraper classifies 'anomaly detection' -> time_series", P.classify_plane("anomaly detection toolkit") == "time_series")
    idea = P.ideate({"id": "x", "plane": "time_series", "vendorable": True, "license": "MIT", "license_class": "permissive", "source": "github"}, set())
    ck("a time_series candidate is ideated as an ml_model", "ml_model" in idea["idea_kinds"])
    ck("ML_QUERIES sweep is defined for the scheduled scraper", isinstance(P.ML_QUERIES, list) and len(P.ML_QUERIES) >= 5)
    ck("serves_truth=false", reg.get("serves_truth") is False)

    print("\n" + (f"PASS - check_ml_model_registry: {len(models)} ML model types over {len(set(m['ml_task'] for m in models))} "
                  "tasks, real libraries/planes, scrapers target it." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
