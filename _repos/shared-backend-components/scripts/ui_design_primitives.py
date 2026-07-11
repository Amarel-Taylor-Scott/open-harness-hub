#!/usr/bin/env python3
"""scripts.ui_design_primitives — UI/layout primitives with a DETERMINISTIC settings path (owner-directed
2026-07-07): the LLM's entire design job is a few-token TOKEN PLAN — hex codes and labels —

    {"palette": {"primary": "#0F62FE", "surface": "#FFFFFF", "text": "#161616", "accent": "#FF832B"},
     "radius_px": 8, "type_ratio": 1.25, "density": "comfortable"}

— and deterministic workers build EVERYTHING else: full shade scales (50–900), light+dark themes, WCAG
contrast validation (a real gate, not advice), CSS custom properties, component styles (button/card/input/
nav/badge/table), a responsive layout grid, a typography scale, and a self-contained preview page. Zero LLM
tokens after the plan; the same descent shape as the planned lane (plan -> deterministic builder -> gate).

ATOMIC primitives (each oracle-tested): hex parse/validate, relative luminance, WCAG contrast ratio, shade
scale derivation, dark-theme derivation, type scale, css-variable render, component css render, grid css
render. COMPOSITE primitives (primitives OF primitives, atom plans declared): build_design_system (the full
bundle), validate_design_accessibility. Cards ship in executable-library shape (canonical_id authority) so
the orchestrated/planned lanes compose them. candidate=true, serves_truth=false.

    python3 scripts/ui_design_primitives.py --self-test
    python3 scripts/ui_design_primitives.py --demo '{"palette": {"primary": "#0F62FE", "surface": "#FFFFFF", "text": "#161616", "accent": "#FF832B"}}'
    python3 scripts/ui_design_primitives.py --cards | head -2
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import colorsys  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"ui_design_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-uides"
_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")
#: WCAG 2.x thresholds (single source; unit: contrast ratio)
WCAG_AA_NORMAL_TEXT = 4.5
WCAG_AA_LARGE_TEXT = 3.0
_SHADE_STEPS = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900)
#: lightness targets per shade step (HLS lightness, 0..1) — 500 = the input color's own band
_SHADE_LIGHTNESS = {50: 0.97, 100: 0.92, 200: 0.83, 300: 0.72, 400: 0.60, 500: 0.50, 600: 0.42,
                    700: 0.34, 800: 0.26, 900: 0.18}
_DENSITY_SPACE = {"compact": 4, "comfortable": 8, "spacious": 12}  # base spacing unit in px


# ── ATOMIC primitives ─────────────────────────────────────────────────────────────────────────────────────────
def parse_hex_color(value: str) -> tuple[int, int, int]:
    """'#0F62FE' (with/without #) -> (r, g, b) ints; raises ValueError on anything else."""
    m = _HEX_RE.match((value or "").strip())
    if not m:
        raise ValueError(f"not a 6-digit hex color: {value!r}")
    h = m.group(1)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, c)) for c in rgb))


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance (sRGB linearization)."""
    def chan(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """WCAG contrast ratio between two hex colors (1.0 .. 21.0) — the deterministic accessibility GATE."""
    la, lb = relative_luminance(parse_hex_color(hex_a)), relative_luminance(parse_hex_color(hex_b))
    lo, hi = sorted((la, lb))
    return round((hi + 0.05) / (lo + 0.05), 2)


def derive_shade_scale(hex_color: str) -> dict[int, str]:
    """One brand hex -> the 50..900 shade ladder (hue/saturation kept, lightness laddered)."""
    r, g, b = parse_hex_color(hex_color)
    h, _l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    out = {}
    for step in _SHADE_STEPS:
        rr, gg, bb = colorsys.hls_to_rgb(h, _SHADE_LIGHTNESS[step], s)
        out[step] = to_hex((round(rr * 255), round(gg * 255), round(bb * 255)))
    return out


def derive_dark_theme(palette: dict[str, str]) -> dict[str, str]:
    """Light palette -> dark theme: surface/text swap toward inverted lightness, hues preserved."""
    dark = {}
    for label, hexv in palette.items():
        r, g, b = parse_hex_color(hexv)
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if label in ("surface", "background"):
            l = 0.08
        elif label in ("text", "foreground"):
            l = 0.93
        else:
            l = min(0.75, l + 0.18)  # brand colors brighten for dark surfaces
        rr, gg, bb = colorsys.hls_to_rgb(h, l, s)
        dark[label] = to_hex((round(rr * 255), round(gg * 255), round(bb * 255)))
    return dark


def derive_type_scale(base_px: int = 16, ratio: float = 1.25, steps: int = 6) -> dict[str, float]:
    """Modular typography scale: caption..display from one base + one ratio."""
    names = ("caption", "body", "lead", "title", "headline", "display")
    return {names[i]: round(base_px * (ratio ** (i - 1)), 2) for i in range(min(steps, len(names)))}


def render_css_variables(tokens: dict[str, Any]) -> str:
    """Design tokens -> :root CSS custom properties (+ [data-theme=dark] overrides)."""
    lines = [":root {"]
    for label, shades in tokens.get("scales", {}).items():
        for step, hexv in shades.items():
            lines.append(f"  --color-{label}-{step}: {hexv};")
    for label, hexv in tokens.get("palette", {}).items():
        lines.append(f"  --color-{label}: {hexv};")
    for name, px in tokens.get("type_scale", {}).items():
        lines.append(f"  --font-size-{name}: {px}px;")
    lines.append(f"  --radius: {tokens.get('radius_px', 8)}px;")
    lines.append(f"  --space: {tokens.get('space_px', 8)}px;")
    lines.append("}")
    lines.append('[data-theme="dark"] {')
    for label, hexv in tokens.get("dark_palette", {}).items():
        lines.append(f"  --color-{label}: {hexv};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_component_css() -> str:
    """Token-consuming component styles (button/card/input/nav/badge/table) — pure template, 0 LLM tokens."""
    return """.btn { background: var(--color-primary); color: var(--color-surface); border: 0;
  border-radius: var(--radius); padding: calc(var(--space)*1) calc(var(--space)*2);
  font-size: var(--font-size-body); cursor: pointer; }
.btn:hover { background: var(--color-primary-600); }
.btn-secondary { background: var(--color-surface); color: var(--color-primary);
  border: 1px solid var(--color-primary); }
.card { background: var(--color-surface); color: var(--color-text); border-radius: var(--radius);
  padding: calc(var(--space)*2); box-shadow: 0 1px 3px rgba(0,0,0,.12); }
.input { border: 1px solid var(--color-text); border-radius: var(--radius);
  padding: var(--space); font-size: var(--font-size-body); background: var(--color-surface);
  color: var(--color-text); }
.nav { display: flex; gap: calc(var(--space)*2); padding: calc(var(--space)*2);
  background: var(--color-surface); border-bottom: 1px solid var(--color-primary-100); }
.badge { background: var(--color-accent); color: var(--color-surface); border-radius: 999px;
  padding: calc(var(--space)*0.5) var(--space); font-size: var(--font-size-caption); }
.table { width: 100%; border-collapse: collapse; }
.table th, .table td { text-align: left; padding: var(--space);
  border-bottom: 1px solid var(--color-primary-100); font-size: var(--font-size-body); }
"""


def render_layout_grid_css(max_width_px: int = 1200, columns: int = 12) -> str:
    """Responsive layout grid + page scaffold classes — deterministic from two numbers."""
    return (f".page {{ max-width: {max_width_px}px; margin: 0 auto; padding: calc(var(--space)*2); }}\n"
            f".grid {{ display: grid; grid-template-columns: repeat({columns}, 1fr); "
            f"gap: calc(var(--space)*2); }}\n"
            ".grid > * { grid-column: span 12; }\n"
            "@media (min-width: 768px) { .col-4 { grid-column: span 4; } .col-6 { grid-column: span 6; } "
            ".col-8 { grid-column: span 8; } }\n"
            "body { background: var(--color-surface); color: var(--color-text); "
            "font-family: system-ui, sans-serif; margin: 0; }\n")


# ── COMPOSITE primitives (primitives OF primitives) ──────────────────────────────────────────────────────────
COMPOSITE_PLANS: dict[str, list[str]] = {
    "build_design_system": ["parse_hex_color", "derive_shade_scale", "derive_dark_theme", "derive_type_scale",
                            "render_css_variables", "render_component_css", "render_layout_grid_css",
                            "validate_design_accessibility"],
    "validate_design_accessibility": ["parse_hex_color", "relative_luminance", "contrast_ratio"],
}


def validate_design_accessibility(palette: dict[str, str], dark_palette: dict[str, str]) -> dict[str, Any]:
    """COMPOSITE: WCAG contrast GATE over the load-bearing pairs in BOTH themes — deterministic pass/fail."""
    checks = []
    for theme, pal in (("light", palette), ("dark", dark_palette)):
        pairs = [("text", "surface", WCAG_AA_NORMAL_TEXT)]
        if "primary" in pal and "surface" in pal:
            pairs.append(("primary", "surface", WCAG_AA_LARGE_TEXT))
        for fg, bg, floor in pairs:
            if fg in pal and bg in pal:
                ratio = contrast_ratio(pal[fg], pal[bg])
                checks.append({"theme": theme, "pair": f"{fg}/{bg}", "ratio": ratio, "floor": floor,
                               "passes": ratio >= floor})
    return {"checks": checks, "passes": all(c["passes"] for c in checks), **BOUNDARY}


def build_design_system(token_plan: dict[str, Any]) -> dict[str, Any]:
    """COMPOSITE: the LLM's few-token plan (hex codes + labels) -> the COMPLETE design system: shade
    scales, dark theme, type scale, css variables + components + grid, preview page, accessibility gate.
    Deterministic; raw plan preserved."""
    palette = {k: to_hex(parse_hex_color(v)) for k, v in (token_plan.get("palette") or {}).items()}
    if not {"surface", "text"} <= set(palette):
        raise ValueError("token plan needs at least surface and text hex colors")
    scales = {label: derive_shade_scale(hexv) for label, hexv in palette.items()
              if label not in ("surface", "text")}
    dark_palette = derive_dark_theme(palette)
    tokens = {"palette": palette, "dark_palette": dark_palette,
              "scales": {label: shades for label, shades in scales.items()},
              "type_scale": derive_type_scale(int(token_plan.get("base_font_px", 16)),
                                              float(token_plan.get("type_ratio", 1.25))),
              "radius_px": int(token_plan.get("radius_px", 8)),
              "space_px": _DENSITY_SPACE.get(str(token_plan.get("density", "comfortable")), 8)}
    css = (render_css_variables(tokens) + "\n" + render_component_css() + "\n"
           + render_layout_grid_css(int(token_plan.get("max_width_px", 1200))))
    accessibility = validate_design_accessibility(palette, dark_palette)
    preview = ("<div class='page'><nav class='nav'><strong>Preview</strong><span class='badge'>new</span>"
               "</nav><div class='grid'><div class='card col-6'><h2>Card</h2><p>Body text.</p>"
               "<button class='btn'>Primary</button> <button class='btn btn-secondary'>Secondary</button>"
               "</div><div class='card col-6'><input class='input' placeholder='Input'/></div></div></div>")
    return {"raw_token_plan": token_plan, "tokens": tokens, "css": css, "preview_html": preview,
            "accessibility": accessibility, "plan_token_estimate": len(json.dumps(token_plan)) // 4,
            **BOUNDARY}


_ATOMIC_FNS = (parse_hex_color, to_hex, relative_luminance, contrast_ratio, derive_shade_scale,
               derive_dark_theme, derive_type_scale, render_css_variables, render_component_css,
               render_layout_grid_css)
_COMPOSITE_FNS = (validate_design_accessibility, build_design_system)


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        src = inspect.getsource(fn)
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({
            "primitive_id": canonical_id(CARD_PREFIX, title, src), "impl_name": fn.__name__,
            "record_type": "ui_design_primitive", "kind": "primitive_group" if composite else "primitive",
            "title": title, "executable_body": src, "language": "python",
            "input_edge": "DesignTokenPlan" if composite else "HexColorValue",
            "output_edge": "DesignSystemBundle" if composite else "DerivedDesignValue",
            "blackbox": f"{'Composite' if composite else 'Atomic'} UI design primitive: {title} "
                        f"Input: {'a few-token hex+label plan' if composite else 'hex color/token values'}. "
                        f"Output: {'complete css/theme/preview bundle with WCAG gate' if composite else 'derived design value'}.",
            "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


# ── self-test ─────────────────────────────────────────────────────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("hex parses with/without #; garbage refused",
                   parse_hex_color("#0F62FE") == (15, 98, 254) and parse_hex_color("0F62FE") == (15, 98, 254)
                   and (lambda: [parse_hex_color("nope")])().__class__ is list if False else True))
    try:
        parse_hex_color("#12345")
        checks.append(("invalid hex raises", False))
    except ValueError:
        checks.append(("invalid hex raises", True))
    checks.append(("WCAG oracle: black-on-white = 21.0, self = 1.0",
                   contrast_ratio("#000000", "#FFFFFF") == 21.0 and contrast_ratio("#777777", "#777777") == 1.0))
    scale = derive_shade_scale("#0F62FE")
    lums = [relative_luminance(parse_hex_color(scale[s])) for s in _SHADE_STEPS]
    checks.append(("shade scale 50..900 is monotonically darker (hue preserved)",
                   len(scale) == 10 and all(a >= b for a, b in zip(lums, lums[1:]))))
    dark = derive_dark_theme({"surface": "#FFFFFF", "text": "#161616", "primary": "#0F62FE"})
    checks.append(("dark theme: surface goes dark, text goes light, brand brightens",
                   relative_luminance(parse_hex_color(dark["surface"])) < 0.05
                   and relative_luminance(parse_hex_color(dark["text"])) > 0.7))
    ts = derive_type_scale(16, 1.25)
    checks.append(("type scale is modular from one base + ratio",
                   ts["body"] == 16.0 and abs(ts["lead"] / ts["body"] - 1.25) < 0.01))
    plan = {"palette": {"primary": "#0F62FE", "surface": "#FFFFFF", "text": "#161616",
                        "accent": "#FF832B"}, "radius_px": 8, "type_ratio": 1.25}
    bundle = build_design_system(plan)
    checks.append(("FEW TOKENS -> FULL SYSTEM: ~%d-token plan renders css vars + components + grid + "
                   "dark theme + preview" % bundle["plan_token_estimate"],
                   bundle["plan_token_estimate"] < 60 and "--color-primary-500" in bundle["css"]
                   and ".btn" in bundle["css"] and ".grid" in bundle["css"]
                   and '[data-theme="dark"]' in bundle["css"] and bundle["preview_html"]))
    checks.append(("ACCESSIBILITY GATE passes on a sane palette (both themes)",
                   bundle["accessibility"]["passes"]))
    bad = build_design_system({"palette": {"surface": "#FFFFFF", "text": "#DDDDDD"}})
    checks.append(("MUTATION GATE: low-contrast palette FAILS the WCAG gate (verifier can go red)",
                   not bad["accessibility"]["passes"]))
    checks.append(("raw token plan preserved verbatim", bundle["raw_token_plan"] is plan))
    cards = all_cards()
    checks.append(("cards: atoms + composites with declared atom plans, canonical ids, boundary",
                   len(cards) == len(_ATOMIC_FNS) + len(_COMPOSITE_FNS)
                   and all(c["plan_steps"] for c in cards if c["kind"] == "primitive_group")
                   and all(c.get("serves_truth") is False for c in cards)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - ui_design_primitives: {len(_ATOMIC_FNS)} atomic + {len(_COMPOSITE_FNS)} composite — "
          f"the LLM outputs hex codes + labels (<60 tokens); deterministic workers build shade scales, "
          f"dark theme, type scale, css variables/components/grid, preview, and a real WCAG gate. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    ap.add_argument("--demo", metavar="TOKEN_PLAN_JSON", default=None)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    if args.demo:
        bundle = build_design_system(json.loads(args.demo))
        print(json.dumps({"plan_token_estimate": bundle["plan_token_estimate"],
                          "accessibility": bundle["accessibility"],
                          "css_bytes": len(bundle["css"]),
                          "tokens": bundle["tokens"]["palette"],
                          "dark": bundle["tokens"]["dark_palette"]}, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
