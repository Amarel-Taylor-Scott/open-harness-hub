"""src.openhubforai.hub_settings — the SETTINGS PLANE for populating each Open*Hub (typed per-hub settings objects).

Per hub, the OPERATIONAL policy (the knobs an operator sets): enabled · cadence · rate_limit_per_cycle · tool_allowlist
· auto_verify · visibility. These MERGE with `_repos/shared-backend-components/architecture/hub_population_strategy.json` (sources + freshness/verify
bars — the WHAT) into a resolved ``HubSettings``. Single source per concern: the STRATEGY owns sources/bars, the
SETTINGS plane owns policy. UI/CLI-editable (same pattern as medium_config.json + config_ui_server). Validated before
save. serves_truth=false. Open layer; stdlib only; no src.baltor / src.teleon import.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from dataclasses import dataclass, field, replace
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
SETTINGS_PATH = _resource("architecture") / "hub_settings.json"
STRATEGY_PATH = _resource("architecture") / "hub_population_strategy.json"
_VISIBILITY = ("global", "tenant_first")
#: defaults (one definition; used when a hub has no explicit setting).
_DEFAULTS = {"enabled": True, "cadence": 7, "rate_limit_per_cycle": 25, "tool_allowlist": (),
             "auto_verify": True, "visibility": "global"}


@dataclass
class HubSettings:
    hub_id: str
    enabled: bool = True
    cadence: int = 7                  # cycles between populating this hub (the hubs flywheel skips when not due)
    rate_limit_per_cycle: int = 25    # max candidates ingested per cycle (protects sources + the store)
    tool_allowlist: tuple = ()        # () = all tools allowed; else only these tool names (e.g. exclude scrape)
    auto_verify: bool = True          # run the verify gate automatically (else candidates wait for manual verify)
    visibility: str = "global"        # global | tenant_first
    freshness_bar: float = 0.5        # merged from the strategy
    verify_bar: str = ""              # merged from the strategy
    sources: dict = field(default_factory=dict)   # merged from the strategy
    serves_truth: bool = False

    def validate(self) -> list[str]:
        p = []
        if self.cadence < 1:
            p.append("cadence must be >= 1")
        if self.rate_limit_per_cycle < 1:
            p.append("rate_limit_per_cycle must be >= 1")
        if not (0.0 <= self.freshness_bar <= 1.0):
            p.append("freshness_bar must be 0..1")
        if self.visibility not in _VISIBILITY:
            p.append(f"visibility must be one of {_VISIBILITY}")
        if not all(isinstance(t, str) for t in self.tool_allowlist):
            p.append("tool_allowlist must be a list of tool-name strings")
        return p


def _read(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def load_settings(hub_id: str) -> HubSettings:
    """The resolved settings for one hub: operational policy (hub_settings.json) merged with the strategy (sources/bars)."""
    ops = {**_DEFAULTS, **_read(SETTINGS_PATH).get("hubs", {}).get(hub_id, {})}
    strat = _read(STRATEGY_PATH).get("hubs", {}).get(hub_id, {})
    return HubSettings(
        hub_id=hub_id, enabled=bool(ops["enabled"]), cadence=int(ops["cadence"]),
        rate_limit_per_cycle=int(ops["rate_limit_per_cycle"]), tool_allowlist=tuple(ops["tool_allowlist"]),
        auto_verify=bool(ops["auto_verify"]), visibility=str(ops["visibility"]),
        freshness_bar=float(strat.get("freshness_bar", 0.5)), verify_bar=str(strat.get("verify_bar", "")),
        sources=dict(strat.get("sources", {})))


def all_hub_ids() -> list[str]:
    return sorted(set(_read(STRATEGY_PATH).get("hubs", {})) | set(_read(SETTINGS_PATH).get("hubs", {})))


def all_settings() -> dict[str, HubSettings]:
    return {h: load_settings(h) for h in all_hub_ids()}


def save_settings(hub_id: str, **updates) -> HubSettings:
    """Update a hub's OPERATIONAL settings (validated against the resolved object before writing). Returns the resolved."""
    resolved = replace(load_settings(hub_id), **{k: v for k, v in updates.items() if k in _DEFAULTS or k == "freshness_bar"})
    problems = resolved.validate()
    if problems:
        raise ValueError("; ".join(problems))
    data = _read(SETTINGS_PATH)
    data.setdefault("hubs", {})
    cur = dict(data["hubs"].get(hub_id, {}))
    cur.update({k: (list(v) if isinstance(v, tuple) else v) for k, v in updates.items()})
    data["hubs"][hub_id] = cur
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return load_settings(hub_id)


def tools_for(settings: HubSettings, tools: list) -> list:
    """Filter the tool repository by the hub's allowlist (() = all tools; never returns empty if the allowlist excludes all)."""
    if not settings.tool_allowlist:
        return tools
    allow = set(settings.tool_allowlist)
    return [t for t in tools if getattr(t, "name", None) in allow] or tools


__all__ = ["HubSettings", "load_settings", "all_settings", "all_hub_ids", "save_settings", "tools_for", "SETTINGS_PATH"]
