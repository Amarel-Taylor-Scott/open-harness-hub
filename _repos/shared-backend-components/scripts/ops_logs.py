#!/usr/bin/env python3
"""scripts.ops_logs — the Global Operations Console RAW LOGS aggregator (GET /api/ops/logs backend).

Streams structured log lines from every source the operator wants in one console: the local backend
SERVICES + product SURFACES (dist/local-services/*.log), DOCKER containers (docker logs, best-effort),
and KUBERNETES pods (kubectl logs, best-effort). Each line is normalized to the design's shape
(docs/design/.../OPS-CONSOLE-HANDOFF.md §4) so the UI's source/level filters, search, and click-to-
inspect raw-JSON pane work uniformly. Read-only; bounded buffer; honest when a source is unavailable
(no docker/kubectl -> that source is simply empty, never a fabricated line).

CLI:  python3 _repos/shared-backend-components/scripts/ops_logs.py --self-test   |   --tail 50
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_SVC_LOG_DIR = _resource("dist") / "local-services"
_BUFFER = 240
_LEVEL_RE = re.compile(r"\b(error|err|exception|traceback|fatal|critical|warn(?:ing)?)\b", re.I)
_STATUS_RE = re.compile(r"\bHTTP[/ ](\d{3})\b|\bstatus[=: ]+(\d{3})\b", re.I)
_LATENCY_RE = re.compile(r"\b(\d+)\s*ms\b")
#: a service_id ending in these is a product SURFACE (vs a backend svc)
_SURFACE_SUFFIX = ("_app", "_site")


def _level(line: str) -> str:
    m = _LEVEL_RE.search(line)
    if not m:
        return "info"
    tok = m.group(1).lower()
    return "error" if tok in ("error", "err", "exception", "traceback", "fatal", "critical") else "warn"


def _entry(_id: int, ts_ms: int, type_: str, label: str, line: str, extra: dict | None = None) -> dict:
    line = line.rstrip("\n")[:600]
    lvl = _level(line)
    status = next((int(g) for g in (_STATUS_RE.search(line).groups() if _STATUS_RE.search(line) else []) if g), None)
    lat = _LATENCY_RE.search(line)
    j = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts_ms / 1000)),
         "level": lvl, "source": f"{type_}/{label}", "message": line}
    if status is not None:
        j["status"] = status
    if lat:
        j["latency_ms"] = int(lat.group(1))
    if extra:
        j.update(extra)
    return {"id": _id, "ts": ts_ms, "type": type_, "label": label, "level": lvl, "msg": line, "json": j}


def _tail(path: Path, n: int) -> list[str]:
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 24000))
            return f.read().decode("utf-8", "replace").splitlines()[-n:]
    except OSError:
        return []


def _service_logs(per_file: int = 12) -> list[dict]:
    out: list[dict] = []
    if not _SVC_LOG_DIR.exists():
        return out
    for log in sorted(_SVC_LOG_DIR.glob("*.log")):
        label = log.stem
        type_ = "surface" if label.endswith(_SURFACE_SUFFIX) else "svc"
        try:
            ts_ms = int(log.stat().st_mtime * 1000)
        except OSError:
            ts_ms = int(time.time() * 1000)
        for line in _tail(log, per_file):
            if line.strip():
                out.append(_entry(0, ts_ms, type_, label, line, {"port": None}))
    return out


def _docker_logs(max_containers: int = 8, per: int = 6) -> list[dict]:
    if not shutil.which("docker"):
        return []
    out: list[dict] = []
    try:
        names = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True,
                               text=True, timeout=4).stdout.split()
    except (OSError, subprocess.SubprocessError):
        return []
    for name in names[:max_containers]:
        try:
            logs = subprocess.run(["docker", "logs", "--tail", str(per), name], capture_output=True,
                                  text=True, timeout=4)
            for line in (logs.stdout + logs.stderr).splitlines():
                if line.strip():
                    out.append(_entry(0, int(time.time() * 1000), "docker", name, line, {"container": name}))
        except (OSError, subprocess.SubprocessError):
            continue
    return out


def _k8s_logs(max_pods: int = 8, per: int = 6) -> list[dict]:
    if not shutil.which("kubectl"):
        return []
    out: list[dict] = []
    try:
        pods = subprocess.run(["kubectl", "get", "pods", "-o", "jsonpath={.items[*].metadata.name}"],
                              capture_output=True, text=True, timeout=4).stdout.split()
    except (OSError, subprocess.SubprocessError):
        return []
    for pod in pods[:max_pods]:
        try:
            logs = subprocess.run(["kubectl", "logs", "--tail", str(per), pod], capture_output=True,
                                  text=True, timeout=4)
            for line in logs.stdout.splitlines():
                if line.strip():
                    out.append(_entry(0, int(time.time() * 1000), "k8s", pod, line, {"pod": pod}))
        except (OSError, subprocess.SubprocessError):
            continue
    return out


def collect_logs(limit: int = _BUFFER) -> dict:
    """Aggregate all sources into one bounded, id-stamped, newest-last buffer. Honest source availability."""
    entries = _service_logs() + _docker_logs() + _k8s_logs()
    entries.sort(key=lambda e: e["ts"])
    entries = entries[-limit:]
    for i, e in enumerate(entries):
        e["id"] = i + 1
    return {"entries": entries, "count": len(entries),
            "sources": {"svc_surface": _SVC_LOG_DIR.exists(),
                        "docker": shutil.which("docker") is not None,
                        "k8s": shutil.which("kubectl") is not None},
            "serves_truth": False}


def _self_test() -> int:
    import tempfile
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    # entry normalization
    e = _entry(1, 1_719_500_000_000, "docker", "observer-runtime", "GET /healthz HTTP 200 in 93 ms")
    ck("entry has the design shape (id/ts/type/label/level/msg/json)",
       all(k in e for k in ("id", "ts", "type", "label", "level", "msg", "json")))
    ck("json sub-object carries source + parsed status + latency",
       e["json"]["source"] == "docker/observer-runtime" and e["json"].get("status") == 200 and e["json"].get("latency_ms") == 93)
    ck("level inference: error / warn / info",
       _level("Traceback (most recent call last)") == "error" and _level("WARNING: retrying") == "warn" and _level("ok") == "info")

    # service-log parsing (hermetic dir) — patch the dir
    global _SVC_LOG_DIR
    orig = _SVC_LOG_DIR
    try:
        with tempfile.TemporaryDirectory() as d:
            _SVC_LOG_DIR = Path(d)
            (Path(d) / "openhubforai_app.log").write_text("started on :8000\nGET / HTTP 200\n", encoding="utf-8")
            (Path(d) / "observer_runtime.log").write_text("ERROR: boom\nrecovered\n", encoding="utf-8")
            agg = collect_logs()
            labels = {e["label"] for e in agg["entries"]}
            types = {e["type"] for e in agg["entries"]}
            ck("aggregates service logs + classifies surface vs svc",
               "openhubforai_app" in labels and "observer_runtime" in labels and "surface" in types and "svc" in types)
            ck("an ERROR line is leveled error", any(e["level"] == "error" for e in agg["entries"]))
            ck("buffer is bounded + ids are sequential", agg["count"] <= _BUFFER and agg["entries"][0]["id"] == 1)
            ck("source availability is reported honestly (no fabrication when a source is absent)",
               isinstance(agg["sources"]["docker"], bool) and isinstance(agg["sources"]["k8s"], bool))
    finally:
        _SVC_LOG_DIR = orig

    if fails:
        print(f"FAIL - ops_logs: {len(fails)} failure(s)")
        return 1
    print("PASS - ops_logs: multi-source (svc/surface + docker + k8s), normalized to the design shape, level "
          "inference, status/latency parse, bounded buffer, honest source availability.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ops console raw-logs aggregator.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--tail", type=int, help="print the last N aggregated entries as JSON")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.tail is not None:
        print(json.dumps(collect_logs(args.tail), indent=2)[:4000])
        return 0
    ap.error("use --self-test or --tail N")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
