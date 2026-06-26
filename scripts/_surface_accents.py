"""Single-source per-surface accent colors — read from architecture/surface_capability_spec.json so the standalone
servers never hard-code a hex (No-Magic-Values / one-design-system). serves_truth=false."""
import json
from pathlib import Path

_SPEC = Path(__file__).resolve().parents[1] / "architecture" / "surface_capability_spec.json"


def accent(surface_id: str, default: str = "#7c8aa0") -> str:
    try:
        for p in json.loads(_SPEC.read_text(encoding="utf-8")).get("pillars", []):
            if p.get("id") == surface_id:
                return p.get("accent") or default
    except Exception:
        pass
    return default
