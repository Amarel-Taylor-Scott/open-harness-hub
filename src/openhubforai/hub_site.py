"""src.openharnesshub.hub_site — ONE standardized Open*Hub page template rendered for all 22 surfaces.

Every Open*Hub gets the SAME branded layout + the SAME sections (so the surfaces are consistent, not 22 bespoke pages):
  1. hero          — Open*Hub eyebrow · hub name · what it stores · a governance badge
  2. contribute    — the THREE channels (Discover · Generate · Intake) with this hub's real sources + generator
  3. browse        — served components (count + a sample) or a "populating…" state
  4. settings      — the resolved operational settings (cadence · rate · visibility · auto-verify)
  5. substrate     — powered-by-Teleon / feeds-Baltor (the funnel), per the dependency law
Design system (portfolio canonical): Hanken Grotesk + IBM Plex Mono. Counts are COMPUTED (no magic values).
serves_truth=false. Open layer: stdlib only. scaffold_hub + build_hub_sites both call this — single source of the hub UI.
"""
from __future__ import annotations

import html
import re

_ACCENT = "#4f46e5"
_CSS = (
    "body{margin:0;background:#fbfbfd;color:#0f1222;font-family:'Hanken Grotesk',system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.55}"
    ".wrap{max-width:880px;margin:0 auto;padding:56px 24px}.mono{font-family:'IBM Plex Mono',ui-monospace,monospace}"
    "h1{font-size:42px;letter-spacing:-.02em;margin:0 0 8px}h2{font-size:15px;text-transform:uppercase;letter-spacing:.09em;color:#6b7280;margin:40px 0 12px}"
    f".tag{{color:{_ACCENT};font-weight:700;text-transform:uppercase;letter-spacing:.1em;font-size:12px}}"
    "p{font-size:18px;color:#33384a;max-width:660px}.muted{color:#6b7280}"
    ".pill{display:inline-block;border:1px solid #e6e8ef;border-radius:999px;padding:4px 12px;font-size:13px;margin:3px 6px 3px 0}"
    f".badge{{background:{_ACCENT}10;border:1px solid {_ACCENT}40;color:{_ACCENT};border-radius:999px;padding:4px 12px;font-size:12px;font-weight:600}}"
    ".grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}@media(max-width:640px){.grid{grid-template-columns:1fr}}"
    ".card{border:1px solid #e6e8ef;border-radius:14px;padding:16px;background:#fff}.card h3{margin:0 0 6px;font-size:15px}"
    ".card p{font-size:13.5px;color:#6b7280;margin:0}.k{font-size:13px;color:#6b7280}.k b{color:#0f1222;font-weight:600}"
    "ul{padding-left:18px}li{font-size:14px;color:#33384a;margin:3px 0}"
)


def _esc(s) -> str:
    return html.escape(str(s))


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "hub"


def _channels_html(mode: str, sources: dict, generator: str) -> str:
    src_terms = []
    for k, v in (sources or {}).items():
        src_terms += [f"{k}:{x}" for x in (v if isinstance(v, list) else [v])]
    discover = (f"<b>public sources</b> — {_esc(', '.join(src_terms[:5]) or 'curated')}" if mode in ("discover", "both")
                else "<span class=muted>not this hub's primary channel</span>")
    gen = (f"<b>{_esc(generator)}</b> emits candidates from our own systems" if generator and mode in ("generate", "both")
           else "<span class=muted>n/a</span>")
    return (
        "<div class=grid>"
        f"<div class=card><h3>1 · Discover</h3><p>{discover}</p></div>"
        f"<div class=card><h3>2 · Generate</h3><p>{gen}</p></div>"
        "<div class=card><h3>3 · Intake</h3><p>owner-provided <b>OKF / links / text</b> via <span class=mono>--ingest</span></p></div>"
        "</div>")


def _browse_html(served: list, content_kind: str) -> str:
    served = served or []
    if not served:
        return f"<p class=muted>Populating… no verified {_esc(content_kind)} served yet. Candidates appear here once they pass the verify gate (discovery≠trust).</p>"
    names = [(_esc(r.get("body", r).get("name") if isinstance(r.get("body", r), dict) else r.get("component_id", "")) or r.get("component_id", "")) for r in served[:8]]
    items = "".join(f"<li>{n}</li>" for n in names if n)
    more = f"<p class=muted>+ {len(served) - 8} more</p>" if len(served) > 8 else ""
    return f"<p><b>{len(served)}</b> verified {_esc(content_kind)} served.</p><ul>{items}</ul>{more}"


def render_hub_page(hub_id: str, *, content_kind: str = "components", one_liner: str = "", tier: str = "",
                    consumed_by: str = "", contribution_mode: str = "both", sources: dict | None = None,
                    generator: str = "", settings=None, served: list | None = None, funnel: dict | None = None,
                    verify_bar: str = "") -> str:
    """Render ONE hub's standardized page. All counts computed; missing data degrades to honest empty states."""
    one_liner = one_liner or f"{content_kind.capitalize()} — governed, continuously updated, verify-gated."
    st = settings
    set_line = (f"cadence <b>{st.cadence}</b> cycles · rate <b>{st.rate_limit_per_cycle}</b>/cycle · "
                f"visibility <b>{_esc(st.visibility)}</b> · auto-verify <b>{st.auto_verify}</b>") if st else "defaults"
    sig = (funnel or {}).get("signals", 0)
    consumed = _esc(consumed_by) or "Teleon / Baltor substrate"
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{_esc(hub_id)} — Open*Hub</title><style>{_CSS}</style></head><body><div class=wrap>"
        f"<div class=tag>Open*Hub</div><h1>{_esc(hub_id)}</h1><p>{_esc(one_liner)}</p>"
        f"<div style='margin:14px 0'><span class=badge>governed · serves_truth=false · verify-gated</span>"
        f"<span class=pill>stores: {_esc(content_kind)}</span>{f'<span class=pill>{_esc(tier)}</span>' if tier else ''}"
        "<span class=pill>powered by Teleon</span></div>"
        f"<h2>What it stores</h2><p class=muted>Bar to serve: {_esc(verify_bar or 'verified + named + sourced')}.</p>"
        f"<h2>How it's populated — 3 channels</h2>{_channels_html(contribution_mode, sources or {}, generator)}"
        f"<h2>Browse</h2>{_browse_html(served or [], content_kind)}"
        f"<h2>Settings</h2><p class=k>{set_line}</p>"
        f"<h2>Substrate</h2><p class=muted>Opt-in contributions + the usage funnel (<b>{sig}</b> signals) feed "
        f"<b>{consumed}</b> — the hub imports neither (dependency law). Your private versions stay private until you contribute.</p>"
        "<p class=mono muted style='font-size:12px;margin-top:40px;color:#9aa'>One standardized template "
        "(src/openharnesshub/hub_site.py) renders all 22 Open*Hub surfaces. Populated by OpenClaw/Hermes + "
        "keep_hub_fresh + generators + owner --ingest.</p>"
        "</div></body></html>\n")


__all__ = ["render_hub_page", "slugify"]
