"""Shared helpers for the standards emitters under scripts/emit/."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG = ROOT / "catalog"
DIST = ROOT / "dist"


def load_catalog() -> dict[str, tuple[Path, dict]]:
    """Load every manifest and return id → (path, manifest)."""
    out: dict[str, tuple[Path, dict]] = {}
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts or any(p == "data" for p in path.parts):
            continue
        try:
            data = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and "id" in data and "type" in data:
            out[data["id"]] = (path, data)
    return out


def by_type(catalog: dict[str, tuple[Path, dict]], type_: str) -> Iterable[tuple[Path, dict]]:
    for _, (path, m) in catalog.items():
        if m.get("type") == type_:
            yield path, m


def slug_only(artifact_id: str) -> str:
    """Strip the `type/` prefix from an artifact id."""
    return artifact_id.split("/", 1)[-1] if "/" in artifact_id else artifact_id


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def spdx_license_url(license_id: str | None) -> str:
    """Convert a license string to the canonical URL when possible."""
    if not license_id:
        return ""
    if license_id.startswith("http"):
        return license_id
    safe = license_id.strip().replace(" ", "-")
    return f"https://spdx.org/licenses/{safe}.html"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def iter_jsonl(path: Path) -> Iterable[dict]:
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue
