#!/usr/bin/env python3
"""scripts.check_native_ui — proof (C-NATIVE-UI-1): _repos/baltor/frontend/native.html is a PROJECTION/PREVIEW ONLY.

Model: _repos/shared-backend-components/scripts/check_memory_page_projection_only.py. The native preview page lets a user paste a small
JSON/CSV/Markdown doc, pick a format + an output_mode, click Preview, and see THREE result panels —
(1) Native output (same shape as input), (2) Sidecar (field_facts/held_out_claims/conflicts/receipts/
field_map), (3) Diff (changed_fields with old→new + receipt_id). It POSTs /api/native/ingest (store-only,
carries ?token= for the gate like hub.html) then GETs /api/native/export/<id>?mode=… plus sidecar + diff.

It must:
  - fetch ONLY /api/native/* endpoints (no other API touched);
  - perform NO durable canonical-truth write from the page (ingest stores a SOURCE only);
  - store NO truth in localStorage/sessionStorage and leak NO secret (no hardcoded token / sk- / api_key);
  - carry the token from the URL (never a literal) for the gated POST;
  - have the doc <textarea>, the format picker, the output_mode picker (all 8 modes), the 3 result panels,
    and loading / empty / error / degraded states;
  - show "original never overwritten" + source_hash.

Static source scan — deterministic, offline, no socket, no RNG, tempfile-free (reads only the committed page).

CLI: python3 _repos/shared-backend-components/scripts/check_native_ui.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import re
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_PAGE = _resource("web/baltor/native.html")

#: fetch() targets that are allowed (the page may read ONLY the native projection/preview API).
_ALLOWED_FETCH_PREFIX = "/api/native/"

#: the 8 canonical output_mode ids the picker must offer (single source: _repos/shared-backend-components/architecture/native_output_modes.json).
_REQUIRED_MODES = (
    "native_passthrough", "native_passthrough_with_sidecar", "schema_preserving",
    "schema_preserving_with_sidecar", "annotated_native", "baltor_native", "dual", "compare",
)

#: anything that would imply the page computes/persists canonical truth or stores a secret.
_FORBIDDEN = (
    "localStorage", "sessionStorage", "indexedDB",     # no client-side truth/secret storage
    "api_key", "Authorization", "Bearer ", "OH_SHOWCASE_TOKEN",  # no secrets
)
#: projection-only forbidden tokens (must never appear anywhere in a projection page).
_FORBIDDEN_TOKENS = (".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/", "INSERT INTO", "sqlite3")

#: the three result panels (native output / sidecar / diff) + the sidecar's governed pieces must be present.
_REQUIRED_PANELS = ("Native output", "Sidecar", "Diff")
_REQUIRED_SIDECAR_PIECES = ("field_facts", "held_out_claims", "conflicts", "receipts", "field_map")
#: diff must show old→new + receipt_id; ingest banner must show the lossless invariant + source_hash.
_REQUIRED_DIFF = ("changed_fields", "receipt_id")
_REQUIRED_INVARIANT = ("original never overwritten", "source_hash")
#: the doc input + the two pickers must exist.
_REQUIRED_INPUTS = ("<textarea", 'id="format"', 'id="mode"')
#: loading / empty / error / degraded states must be handled.
_REQUIRED_STATES = ("loading", "empty", "error", "degraded")


def _fetch_targets(text: str) -> list[str]:
    """Every fetch(...) argument literal (the leading string of the URL expression)."""
    out: list[str] = []
    for m in re.finditer(r"fetch\(\s*([^,)]*)", text):
        arg = m.group(1)
        lit = re.search(r"""['"]([^'"]+)['"]""", arg)
        if lit:
            out.append(lit.group(1))
    return out


def _endpoint_literals(text: str) -> list[str]:
    """All /api/... string literals that appear in the page (the EP map + fetch args)."""
    return re.findall(r"""['"](/api/[^'"]+)['"]""", text)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("_repos/baltor/frontend/native.html exists", _PAGE.exists())
    if not _PAGE.exists():
        print("\n1 FAILURES: missing page"); return 1
    text = _PAGE.read_text(encoding="utf-8")

    # 1) every /api/ endpoint the page references is under /api/native/ (projection-only — no other API touched)
    eps = _endpoint_literals(text)
    off_eps = [e for e in eps if not e.startswith(_ALLOWED_FETCH_PREFIX)]
    check("page references ONLY /api/native/* endpoints", off_eps == [], str(off_eps))
    routes = {e.split("?")[0].rstrip("/") for e in eps}
    # the four native routes the page exercises (ingest/export/sidecar/diff) must all be present.
    for want in ("/api/native/ingest", "/api/native/export", "/api/native/sidecar", "/api/native/diff"):
        check(f"page references {want}", any(r == want or r.startswith(want) for r in routes), str(sorted(routes)))

    # 2) every literal fetch() target is a native endpoint (or a function-built URL); none escapes /api/native/
    for t in _fetch_targets(text):
        if t.startswith("/") and not t.startswith(_ALLOWED_FETCH_PREFIX):
            check(f"fetch target {t} is under /api/native/", False, t)
    check("all literal fetch() targets are native endpoints", True)

    # 3) no durable canonical-truth write / truth storage / secrets / forbidden projection tokens
    off = [f for f in _FORBIDDEN if f in text]
    off += [f for f in _FORBIDDEN_TOKENS if f in text]
    sk_prefix = "sk" + "-"
    if sk_prefix in text:
        off.append(sk_prefix)
    # a hardcoded token literal (token=<something-not-built-from-URL>) is forbidden; token must come from the URL.
    if re.search(r"""token\s*[:=]\s*['"][A-Za-z0-9]{8,}['"]""", text):
        off.append("hardcoded token literal")
    check("page performs no durable truth write / truth storage / secret / forbidden token", off == [], str(off))

    # 3b) the token used for the gated POST is read from the URL (URLSearchParams), never hardcoded.
    check("token is read from the URL for the gated POST (not hardcoded)",
          "URLSearchParams" in text and 'get("token")' in text)

    # 3c) ingest is store-only: the page asserts it writes no canonical truth / serves no fact (governance copy).
    check("page states ingest writes no canonical truth / serves no fact",
          ("no canonical truth" in text) and ("computes no truth" in text or "computes, stores" in text))

    # 4) the doc input + format + output_mode pickers are present, and all 8 modes are offered
    missing_inputs = [i for i in _REQUIRED_INPUTS if i not in text]
    check("doc <textarea> + format picker + output_mode picker present", missing_inputs == [], str(missing_inputs))
    missing_modes = [m for m in _REQUIRED_MODES if f'value="{m}"' not in text]
    check("all 8 output_mode options are offered", missing_modes == [], str(missing_modes))

    # 5) the three result panels (native output / sidecar / diff) + sidecar pieces + diff fields are present
    missing_panels = [p for p in _REQUIRED_PANELS if p not in text]
    check("the 3 result panels are present (native output / sidecar / diff)", missing_panels == [], str(missing_panels))
    missing_pieces = [s for s in _REQUIRED_SIDECAR_PIECES if s not in text]
    check("sidecar shows field_facts/held_out_claims/conflicts/receipts/field_map", missing_pieces == [], str(missing_pieces))
    missing_diff = [d for d in _REQUIRED_DIFF if d not in text]
    check("diff shows changed_fields + receipt_id (old→new)", missing_diff == [], str(missing_diff))
    check("diff renders old → new transition", ("diff-old" in text and "diff-new" in text) or "old)" in text)

    # 6) the lossless invariant is visible: original never overwritten + source_hash
    missing_inv = [i for i in _REQUIRED_INVARIANT if i not in text]
    check("page shows 'original never overwritten' + source_hash", missing_inv == [], str(missing_inv))

    # 7) loading / empty / error / degraded states are handled
    missing_states = [s for s in _REQUIRED_STATES if s.lower() not in text.lower()]
    check("loading / empty / error / degraded states handled", missing_states == [], str(missing_states))

    # 8) projection-only declaration is on the page
    check("page declares itself projection-only", "PROJECTION ONLY" in text.upper() or "projection-only" in text)

    print(f"\n{'PASS — check_native_ui: native.html fetches ONLY /api/native/* (no other API), POSTs ingest store-only (token from URL, no hardcoded secret), offers the doc input + format + 8 output_modes, renders the native-output / sidecar / diff panels, shows the lossless invariant (original never overwritten + source_hash), and handles loading/empty/error/degraded.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: native.html is a projection/preview-only page.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
