"""src.openharnesshub.generators — the GENERATE channel: named producers that emit hub candidates from OUR systems.

The third contribution channel, complementing DISCOVER (public search via OpenClaw) and INTAKE (owner-provided via
--ingest). Some hubs store content that does NOT exist in the wild — method primitives, learned routing policies,
run receipts, rendered templates. A generator reads a REAL internal source and emits CANDIDATE components
(serves_truth=false; the hub's verify gate still applies — discovery≠trust).

Single-sourced: method primitives come from architecture/descent_method_catalog.json (filtered by axis/keyword).
Generators that read Teleon/Baltor internals (e.g. ``descent_brain`` over the descent_attempt_store) are NOT imported
here — the dependency law forbids OpenHarnessHub importing Teleon — they are INJECTED by the operator layer via
``extra_generators`` (Teleon may import OHH, not the reverse; the hub stays a clean open layer). Generators that aren't
wired to a producer yet return a structured ``pending`` marker — NEVER fabricated candidates (honest population). The
strategy (architecture/hub_population_strategy.json) names each hub's generator + optional generator_args.

Open layer: stdlib only (catalog JSON read); resilient (any source error -> [] / pending, never raise).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_METHOD_CATALOG = _REPO / "architecture" / "descent_method_catalog.json"
_STRATEGY = _REPO / "architecture" / "hub_population_strategy.json"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "component"


# ── wired generators (read REAL single sources) ──────────────────────────────────────────────────────────────
def _gen_method_catalog(args: dict) -> list[dict]:
    """Emit method primitives from the canonical descent method catalog, filtered by ``axes`` or ``keywords``.
    Each method carries its real vendorable ``modules`` (repos) so the same record also seeds OpenToolsHub."""
    try:
        cat = json.loads(_METHOD_CATALOG.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    axes = set(args.get("axes", []))
    kws = [k.lower() for k in args.get("keywords", [])]
    out: list[dict] = []
    for dim in cat.get("dimensions", []):
        axis = dim.get("axis")
        for m in dim.get("methods", []):
            name = m.get("method") or m.get("name") or ""
            if not name:
                continue
            hay = (name + " " + m.get("how", "")).lower()
            if (axes and axis in axes) or (kws and any(k in hay for k in kws)):
                out.append({"component_id": _slug(name), "name": name, "summary": (m.get("how", "") or name)[:240],
                            "axis": axis, "modules": m.get("modules", []), "generated_via": "method_catalog",
                            "serves_truth": False})
    return out


#: OHH-NATIVE generators (law-clean: read only architecture/ JSON). Operator-layer generators (descent_brain, run
#: receipts/state — which read Teleon internals) are injected via extra_generators, never imported here.
_WIRED = {"method_catalog": _gen_method_catalog}


def make_descent_brain_generator(attempts_loader) -> "callable":
    """Build a ``descent_brain`` generator from an injected attempts loader (``()->list[dict]``). The operator layer
    passes Teleon's descent_attempt_store.all here, so OHH never imports Teleon (dependency law). Emits learned
    routing/optimization policy candidates (serves_truth=false)."""
    def gen(args: dict) -> list[dict]:
        try:
            attempts = attempts_loader() or []
        except Exception:  # noqa: BLE001
            return []
        out: list[dict] = []
        for a in attempts:
            cap = a.get("capability") or a.get("capability_id") or a.get("task") or "capability"
            tool = a.get("bounded_tool") or a.get("winner") or a.get("chosen") or a.get("to") or ""
            saved = a.get("pct_saved") or a.get("reward") or a.get("improvement") or ""
            name = f"route {cap} -> {tool}" if tool else f"policy for {cap}"
            out.append({"component_id": _slug(name), "name": name,
                        "summary": f"learned descent: {cap} descends to {tool or 'a bounded path'} ({saved})"[:240],
                        "capability": cap, "bounded_tool": tool, "evidence": saved,
                        "generated_via": "descent_brain", "serves_truth": False})
        return out
    return gen


def generate_for(hub_id: str, *, strategy_path: Path | None = None, extra_generators: dict | None = None) -> dict:
    """Run the GENERATE channel for one hub per its strategy entry. ``extra_generators`` (name->callable) are merged
    over the OHH-native set so the operator layer can inject Teleon-backed generators. Returns {hub, generator,
    candidates, pending}. pending=True (with a reason) when the named generator isn't wired — candidates [] (never
    fabricated)."""
    strat = {}
    try:
        strat = json.loads((strategy_path or _STRATEGY).read_text(encoding="utf-8")).get("hubs", {}).get(hub_id, {})
    except Exception:  # noqa: BLE001
        pass
    gen = strat.get("generator", "")
    args = strat.get("generator_args", {})
    registry = {**_WIRED, **(extra_generators or {})}
    if not gen:
        return {"hub": hub_id, "generator": "", "candidates": [], "pending": True,
                "reason": "no generator declared (discover/intake only)", "serves_truth": False}
    fn = registry.get(gen)
    if fn is None:
        return {"hub": hub_id, "generator": gen, "candidates": [], "pending": True,
                "reason": f"generator '{gen}' declared but not yet wired to its producer", "serves_truth": False}
    return {"hub": hub_id, "generator": gen, "candidates": fn(args), "pending": False, "serves_truth": False}


__all__ = ["generate_for", "make_descent_brain_generator"]
