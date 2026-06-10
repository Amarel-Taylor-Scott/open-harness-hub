#!/usr/bin/env python3
"""scripts.validate_compose — guard the existing docker-compose files (don't pin → don't drift).

The repo already has the local stack (infra/docker-compose*.yml, infra/postgres/*.pgvector.yml,
etc.). This guards them rather than adding a duplicate: STATEFUL services (Postgres/Redis/Qdrant/
MinIO/…) must NOT use `:latest` or an implicit (untagged) image — that is a reproducibility +
data-safety hazard (docs/standards/table-shape-guidelines.md: canonical state is durable). Self-test
runs over the real compose files (they pass — images are pinned) + a negative inline case.

CLI:
    python3 scripts/validate_compose.py --self-test
    python3 scripts/validate_compose.py            # scan repo compose files; exit 1 on violations
"""
from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

#: service-name hints that imply a stateful/data service (also any svc declaring volumes).
STATEFUL_HINTS = {"postgres", "redis", "qdrant", "weaviate", "minio", "neo4j", "elasticsearch",
                  "opensearch", "mysql", "mongo", "mongodb", "clickhouse", "kafka", "zookeeper", "graphiti"}


def _compose_files() -> list[Path]:
    files = [p for p in _REPO.glob("infra/**/*.yml") if "compose" in p.name.lower()]
    files += [p for p in _REPO.glob("*.yml") if "compose" in p.name.lower()]
    return sorted(set(files))


def check_compose(doc: dict, where: str) -> list[str]:
    """Return violations for one parsed compose doc."""
    violations: list[str] = []
    for name, svc in (doc.get("services") or {}).items():
        if not isinstance(svc, dict):
            continue
        image = svc.get("image")
        # Scope to canonical DATA stores by name. NOT "any service with a volume": observability
        # (prometheus/otel) + model caches (ollama) mount volumes too, but their data is recreatable —
        # pinning those is hygiene, not data-format safety. Keeping the rule precise (not broad).
        stateful = name.lower() in STATEFUL_HINTS
        if image and stateful:
            tag = image.rsplit(":", 1)[-1] if ":" in image else None
            if tag is None or tag == "latest":
                violations.append(f"{where}: stateful service {name!r} uses unpinned image {image!r} (pin a version)")
    return violations


def scan() -> tuple[list[str], int]:
    import yaml
    violations: list[str] = []
    files = _compose_files()
    for p in files:
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception as e:
            violations.append(f"{p.relative_to(_REPO)}: unparseable ({e})")
            continue
        violations.extend(check_compose(doc, p.relative_to(_REPO).as_posix()))
    return violations, len(files)


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    violations, count = scan()
    check(f"found compose files to guard", count >= 1, str(count))
    check("existing compose files pin stateful images (no :latest)", not violations, "; ".join(violations[:3]))

    # NEGATIVE: a stateful service on :latest is flagged
    bad = {"services": {"postgres": {"image": "postgres:latest", "volumes": ["pgdata:/var/lib/postgresql/data"]}}}
    check("postgres:latest is rejected", bool(check_compose(bad, "neg")))
    # NEGATIVE: untagged stateful image is flagged
    bad2 = {"services": {"redis": {"image": "redis"}}}
    check("untagged stateful image is rejected", bool(check_compose(bad2, "neg2")))
    # a pinned stateful image passes; a stateless app build passes
    ok_doc = {"services": {"postgres": {"image": "pgvector/pgvector:pg16", "volumes": ["d:/x"]},
                           "web": {"build": "."}}}
    check("pinned stateful + build service pass", not check_compose(ok_doc, "ok"))

    print(f"\n{'all validate_compose self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Guard docker-compose files: stateful services must pin images.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    violations, count = scan()
    if violations:
        print(f"FAIL — {len(violations)} compose issue(s) across {count} file(s):")
        print("\n".join(f"  - {v}" for v in violations))
        return 1
    print(f"OK — {count} compose file(s) pin stateful images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
