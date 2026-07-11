"""Cross-cutting telemetry — the ONE contract every service imports (see
docs/architecture/backend-services-and-platform.md). Three signals, one import:

  • structured JSON logs   — built on scripts/showcase/jsonlog.py (the existing standard)
  • Prometheus metrics     — counters / histograms, scraped at /metrics
  • OpenTelemetry traces    — spans that follow a job enqueue → worker → store

Dependency-light by design: `prometheus_client` and `opentelemetry` are OPTIONAL. If they're not
installed (the core image stays minimal — see requirements-platform.txt for the scale extras), every
call degrades to a no-op and structured logging still works. So a service can `from
services.platform._shared import telemetry` unconditionally.

    telemetry.configure("foundry", metrics_port=9101)
    telemetry.log("partition.start", partition=p, gaps=len(gaps))
    with telemetry.span("run_partition", partition=p):
        telemetry.counter("candidates_total", "candidates produced").inc(n)
"""
from __future__ import annotations

import contextlib
import os
from typing import Any

try:                                            # the existing structured-log standard
    from scripts.showcase.jsonlog import emit as _emit
except Exception:                               # pragma: no cover - keep telemetry import-safe anywhere
    def _emit(event: str, level: str = "info", **fields: Any) -> None:
        print({"event": event, "level": level, **fields})

# --- optional Prometheus -------------------------------------------------------------------------
try:
    from prometheus_client import Counter, Histogram, start_http_server  # type: ignore
    _PROM = True
except Exception:                               # pragma: no cover
    _PROM = False

# --- optional OpenTelemetry ----------------------------------------------------------------------
try:
    from opentelemetry import trace as _ot_trace  # type: ignore
    _OTEL = True
except Exception:                               # pragma: no cover
    _OTEL = False

_SERVICE = "unset"
_metrics: dict[str, Any] = {}
_tracer = None


def configure(service: str, metrics_port: int | None = None) -> None:
    """Name this process's service and (optionally) start the Prometheus /metrics endpoint."""
    global _SERVICE, _tracer
    _SERVICE = service
    if _OTEL:
        _tracer = _ot_trace.get_tracer(service)
    if _PROM and metrics_port:
        with contextlib.suppress(Exception):
            start_http_server(metrics_port)
    _emit("service.configure", service=service, prometheus=_PROM, otel=_OTEL, metrics_port=metrics_port)


def log(event: str, level: str = "info", **fields: Any) -> None:
    """Structured JSON log, always tagged with the service name."""
    _emit(event, level=level, service=_SERVICE, **fields)


class _NoOpMetric:
    def inc(self, *_a: Any, **_k: Any) -> None: ...
    def observe(self, *_a: Any, **_k: Any) -> None: ...
    def labels(self, *_a: Any, **_k: Any) -> "_NoOpMetric": return self


def counter(name: str, description: str = "", labelnames: tuple[str, ...] = ()) -> Any:
    key = "c:" + name
    if key not in _metrics:
        _metrics[key] = Counter(name, description, labelnames) if _PROM else _NoOpMetric()
    return _metrics[key]


def histogram(name: str, description: str = "", labelnames: tuple[str, ...] = ()) -> Any:
    key = "h:" + name
    if key not in _metrics:
        _metrics[key] = Histogram(name, description, labelnames) if _PROM else _NoOpMetric()
    return _metrics[key]


@contextlib.contextmanager
def span(name: str, **attrs: Any):
    """Trace span across a unit of work (OTel when present; always emits start/done logs)."""
    log(name + ".start", **attrs)
    if _OTEL and _tracer is not None:
        with _tracer.start_as_current_span(name) as sp:  # pragma: no cover - needs otel installed
            for k, v in attrs.items():
                with contextlib.suppress(Exception):
                    sp.set_attribute(k, v)
            try:
                yield sp
            finally:
                log(name + ".done", **attrs)
    else:
        try:
            yield None
        finally:
            log(name + ".done", **attrs)


def self_test() -> int:
    configure("telemetry-selftest")
    log("hello", n=1)
    counter("ohh_selftest_total", "self-test counter").inc()
    with span("selftest.unit", step=1):
        pass
    print(f"telemetry ok (service={_SERVICE} prometheus={_PROM} otel={_OTEL})")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
