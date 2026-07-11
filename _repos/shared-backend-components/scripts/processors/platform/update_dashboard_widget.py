#!/usr/bin/env python3
"""Backs ``processor/update-dashboard-widget``. Canonical wiring: the manifest
``_repos/shared-backend-components/catalog/processors/platform/update-dashboard-widget.yaml`` (process_kind
``platform.dashboard_widget``). This planner derives a deterministic widget id
and binds one metric to a data store; it updates no live dashboard (the manifest
is the contract).
"""
from __future__ import annotations

from typing import Any

from scripts.processors.platform._platform_base import (
    content_address,
    content_hash,
    plan_row,
    require,
    selftest_run,
)

PROCESS_KIND = "platform.dashboard_widget"


def run(metric: Any, store: Any) -> dict[str, Any]:
    """Plan a dashboard-widget update for ``metric`` bound to ``store``. Returns ``{widget_id}``."""
    require(metric, "metric")
    require(store, "store")
    metric_name = metric.get("name") if isinstance(metric, dict) else str(metric)
    store_id = store.get("store_id") if isinstance(store, dict) else str(store)
    require(metric_name, "metric.name")
    require(store_id, "store.store_id")
    widget_id_value = content_address("dashboard-widget", {"metric": metric_name, "store": store_id})
    plan = plan_row(
        action=PROCESS_KIND,
        target=str(store_id),
        payload=metric,
        extra={
            "widget_id": widget_id_value,
            "metric_name": str(metric_name),
            "store_id": str(store_id),
            "metric_hash": content_hash(metric),
        },
    )
    return {"widget_id": plan}


def _self_test() -> int:
    result = run(metric={"name": "cost"}, store={"store_id": "data-store/abc"})
    assert result["widget_id"]["metric_name"] == "cost", result
    assert result["widget_id"]["store_id"] == "data-store/abc", result
    assert result["widget_id"]["widget_id"].startswith("dashboard-widget/"), result
    return selftest_run(
        run, {"metric": {"name": "cost"}, "store": {"store_id": "data-store/abc"}}, ("widget_id",)
    )


if __name__ == "__main__":
    raise SystemExit(_self_test())
