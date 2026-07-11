#!/usr/bin/env python3
"""check_fundamental_primitives_taxonomy — proof that the canonical fundamental-primitives map is REAL and complete.

_repos/shared-backend-components/architecture/fundamental_primitives_taxonomy.json is one single-source map of the system's fundamental primitives
(data storage/transfer/computation/unit/medium · interop/context/skill standards · k8s/cloud-function/execution/
environment runtime · the seven-primitive capability grammar · the assurance wedge), each pointing to the ACTUAL
artifact that implements it. This gate verifies every artifact path exists (no fantasy mapping), every primitive
family the owner asked for is covered, the assurance layer is first-class, and the generated code/file MAP is fresh.

  --build      (re)write the human code/file map from the taxonomy
  --self-test  validate the taxonomy + map (the registered proof)

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_fundamental_primitives_taxonomy.py --build | --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TAX = _resource("architecture") / "fundamental_primitives_taxonomy.json"
_MAP = _resource("docs") / "architecture" / "fundamental-primitives-map.md"


def load() -> dict:
    return json.loads(_TAX.read_text())


def render_map(t: dict) -> str:
    lines = ["# Fundamental primitives — code/file map (generated)",
             "",
             f"> GENERATED from `architecture/fundamental_primitives_taxonomy.json` by "
             f"`scripts/check_fundamental_primitives_taxonomy.py` — do not hand-edit. Updated {t['updated']}.",
             "", f"**Principle.** {t['principle']}", "", f"**PMF alignment.** {t['pmf_alignment']}", ""]
    for layer in t["layers"]:
        fams = [f for f in t["primitive_families"] if f["layer"] == layer]
        lines.append(f"## Layer: `{layer}` ({len(fams)} primitives)")
        lines.append("")
        for f in fams:
            lines.append(f"### `{f['id']}` — {f['definition']}")
            lines.append(f"- **implemented by:** {', '.join('`' + a + '`' for a in f['canonical_artifacts'])}")
            lines.append(f"- **standards:** {', '.join(f['standards']) or '—'}")
            lines.append(f"- **PMF role:** {f['pmf_role']}")
            lines.append("")
    lines.append("## Owner-requested family coverage")
    lines.append("")
    for req, pid in t["requested_family_coverage"].items():
        lines.append(f"- **{req}** → `{pid}`")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_map() -> str:
    _MAP.parent.mkdir(parents=True, exist_ok=True)
    _MAP.write_text(render_map(load()))
    return str(_MAP.relative_to(_REPO))


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    t = load()
    fams = t["primitive_families"]
    ck("taxonomy carries the principle + PMF alignment + serves_truth false",
       bool(t.get("principle")) and bool(t.get("pmf_alignment")) and t.get("serves_truth") is False)
    ck("every family has id/group/layer/definition/canonical_artifacts/standards/pmf_role",
       all({"id", "family_group", "layer", "definition", "canonical_artifacts", "standards", "pmf_role"} <= set(f) for f in fams))
    ck("primitive ids are unique", len({f["id"] for f in fams}) == len(fams))

    # the load-bearing check: every mapped artifact actually EXISTS (the map is real, not a fantasy)
    missing = sorted({a for f in fams for a in f["canonical_artifacts"] if not (_resource(a)).exists()})
    ck("every canonical artifact path exists on disk (no fantasy mapping)", not missing, str(missing))

    # every declared layer is populated; assurance (the wedge) is first-class (>=4 primitives)
    ck("every declared layer has >= 1 primitive", all(any(f["layer"] == L for f in fams) for L in t["layers"]))
    ck("the ASSURANCE layer is first-class (>= 4 primitives — the PMF wedge)",
       sum(1 for f in fams if f["layer"] == "assurance") >= 4)

    # every owner-requested family maps to a REAL primitive id present in the taxonomy
    ids = {f["id"] for f in fams}
    req = t["requested_family_coverage"]
    bad_req = {k: v for k, v in req.items() if v not in ids}
    ck("every owner-requested family (storage/transfer/computation/units/mediums/standards/context/skill/k8s/cloud-fn) maps to a real primitive",
       not bad_req and len(req) >= 10, str(bad_req))

    # the generated map is fresh if present; always deterministic
    page = render_map(t)
    ck("the code/file map renders from the taxonomy (every primitive id appears)",
       all(f["id"] in page for f in fams))
    if _MAP.exists():
        ck("the on-disk code/file map is fresh vs the taxonomy (regenerate with --build)", _MAP.read_text() == page)
    ck("deterministic", render_map(load()) == page)

    groups = sorted({f["family_group"] for f in fams})
    print("\n" + (f"PASS - check_fundamental_primitives_taxonomy: {len(fams)} fundamental primitives across "
                  f"{len(t['layers'])} layers / {len(groups)} groups, each mapped to a REAL artifact; all "
                  f"{len(req)} owner-requested families covered; assurance is first-class; the code/file map is "
                  f"generated (no drift). Non-destructive index — never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--build" in argv:
        print("wrote:", write_map())
        return 0
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_fundamental_primitives_taxonomy.py --build | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
