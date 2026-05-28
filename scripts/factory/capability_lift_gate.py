#!/usr/bin/env python3
"""Capability-lift gate for catalog manifests.

Admission bar (``docs/codex/master-goal.md``): a component is useful **iff it
lets a model do something it cannot do reliably alone.** This gate turns that
bar into a deterministic, stdlib-only decision over catalog YAML manifests:

  1. **Capability-lift score** (0..1) from structural + provenance + evaluation
     + domain-specificity signals, with a HARD floor (``--lift-floor``). The
     dominant axis is "not solved by an out-of-box LLM" — boilerplate clones and
     self-labelled volume expansion fall below the floor.
  2. **Novelty** via SimHash + LSH banding: near-duplicate manifests (the
     ``scale-*-arm-007`` / ``-015`` clone families) are culled, keeping one
     canonical per cluster. LSH banding avoids the O(n^2) blow-up that hangs
     monolithic dedup runs.

A manifest is **kept** iff ``lift >= floor`` AND it is not a near-duplicate;
otherwise it is **culled** with explicit reasons.

``--apply`` deletes culled files, but **only ones not tracked by git** — curated,
committed components are never deleted, only reported. Default is a dry run.

Run ``--self-test`` for an offline check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write("pyyaml is required: pip install pyyaml\n")
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG = ROOT / "catalog"

# --- tunables (single source; no magic literals scattered downstream) --------
# Filler is culled primarily on explicit markers (HARD_FILLER_MARKS) and
# near-duplicate detection. The lift floor is a low "near-empty" backstop, NOT
# the main lever — a raw model adapter legitimately scores low on capability
# lift (it is a transport, not a capability) and must not be culled for that.
DEFAULT_LIFT_FLOOR = 0.20          # below this => effectively empty => cull
DEFAULT_SIMHASH_BITS = 64
DEFAULT_LSH_BANDS = 4              # 4 x 16-bit bands over a 64-bit simhash
DEFAULT_HAMMING_MAX = 3           # <= this distance within a band => near-dup

# Self-labelled volume-expansion / boilerplate markers. A component that
# describes itself as a "scale arm" or "regression fixture" is, by definition,
# not lifting capability beyond the model — it is padding.
FILLER_TAGS = {"scale-expansion"}
BOILERPLATE_MARKERS = (
    "scale-expand", "scaled regression", "benchmark arms", "harness portability",
    "for scale-expanded", "reusable google_gemini adapter profile",
    "regression testing", "portability checks",
)
# Industry tags that carry no domain specificity on their own.
GENERIC_INDUSTRY = {"ai", "cross_industry", "software", "software.devops", "general"}
# Permissive licenses we recognise as redistributable.
PERMISSIVE_LICENSES = ("mit", "apache", "bsd", "cc-by", "cc0", "public-domain", "isc", "unlicense")
# Markers that, on their own, identify generated padding (vs. low-but-real lift).
HARD_FILLER_MARKS = {
    "self-labelled scale-expansion",
    "numeric-arm suffix (templated clone)",
    "boilerplate description",
    "fabricated default_model",
}


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def load_manifests(root: Path) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for path in sorted(root.rglob("*.yaml")):
        if "_inbox" in path.parts:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and "type" in data:
            out.append((path, data))
    return out


def git_tracked_set() -> set[Path]:
    """All git-tracked files as absolute paths. Run from the repo ROOT (not the
    scan root) so the path argument resolves correctly — otherwise every file
    looks untracked and curated components would be eligible for deletion."""
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    return {(ROOT / line).resolve() for line in out.splitlines() if line.strip()}


# --------------------------------------------------------------------------- #
# capability-lift score
# --------------------------------------------------------------------------- #
def _str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _has_provenance(m: dict) -> bool:
    attr = m.get("attribution") if isinstance(m.get("attribution"), dict) else {}
    return bool(attr.get("source_url") or attr.get("author") or m.get("source_url"))


def _permissive_license(m: dict) -> bool:
    lic = _str(m.get("license")).lower()
    return any(term in lic for term in PERMISSIVE_LICENSES)


def _structural_depth(m: dict) -> float:
    """Reward manifests that encode real structure a bare model lacks."""
    t = m.get("type")
    if t == "pipeline":
        steps = _list(m.get("steps")) or _list((m.get("graph") or {}).get("nodes"))
        return 1.0 if len(steps) >= 2 else 0.3
    if t == "tool":
        params = m.get("parameters") if isinstance(m.get("parameters"), dict) else {}
        props = params.get("properties") if isinstance(params, dict) else {}
        impls = _list(m.get("implementations"))
        score = 0.0
        if isinstance(props, dict) and len(props) >= 2:
            score += 0.6
        if impls:
            score += 0.4
        return min(1.0, score)
    if t in {"rule-pack", "rulepack"}:
        rules = _list(m.get("rules")) or _list(m.get("patterns"))
        return 1.0 if rules else 0.4
    if t == "harness":
        ok_targets = bool(m.get("model_targets"))
        ok_packs = bool(m.get("consumes") or m.get("emits") or m.get("packs"))
        return 0.5 * ok_targets + 0.5 * ok_packs
    if t == "benchmark":
        return 1.0 if (m.get("dataset") and (m.get("rubric") or m.get("judge"))) else 0.4
    if t == "rubric":
        return 1.0 if len(_list(m.get("dimensions"))) >= 2 else 0.3
    if t in {"knowledge-pack", "logic-pack"}:
        return 0.7 if (m.get("data") or m.get("records") or m.get("files") or m.get("entries")) else 0.3
    if t == "processor":
        return 0.7 if (m.get("implementation") or m.get("implementations") or m.get("parameters")) else 0.3
    if t == "pattern":
        return 0.6  # patterns are inherently structural know-how
    if t == "adapter":
        # An adapter is a transport profile; on its own it adds little lift
        # unless it encodes a non-trivial capability set + cost/routing detail.
        caps = _list(m.get("capabilities"))
        return 0.4 if len(caps) >= 2 and m.get("cost_model") else 0.15
    if t == "persona":
        return 0.3
    if t == "dataset":
        return 0.6 if (m.get("records") or m.get("files") or m.get("samples")) else 0.2
    return 0.3


def _domain_specificity(m: dict) -> float:
    inds = {str(i).lower() for i in _list(m.get("industry"))}
    specific = inds - GENERIC_INDUSTRY
    return 1.0 if specific else 0.0


def _eval_linked(m: dict) -> float:
    if m.get("type") in {"benchmark", "rubric"}:
        return 1.0
    if m.get("rubric") or m.get("benchmark") or m.get("acceptance_criteria"):
        return 1.0
    text = json.dumps(m)
    return 0.6 if ("rubric/" in text or "benchmark/" in text) else 0.0


def _filler_markers(m: dict) -> list[str]:
    marks: list[str] = []
    tags = {str(t).lower() for t in _list(m.get("tags"))}
    if tags & FILLER_TAGS:
        marks.append("self-labelled scale-expansion")
    # Only the id slug, and only a hyphen-delimited trailing run (-007, arm-15)
    # — so legit names ending in a number ("ISO 8601", "GPT 4") are not flagged.
    ident = _str(m.get("id")).lower()
    if re.search(r"-\d{2,}$", ident) or re.search(r"\barm[-_]?\d+\b", ident):
        marks.append("numeric-arm suffix (templated clone)")
    desc = _str(m.get("description")).lower()
    if any(mk in desc for mk in BOILERPLATE_MARKERS):
        marks.append("boilerplate description")
    default_model = _str(m.get("default_model"))
    if re.search(r"-\d{2,}$", default_model):
        marks.append("fabricated default_model")
    # duplicated modality entries are a generator artefact, not authoring
    mods = _list(m.get("modality"))
    if len(mods) != len(set(map(str, mods))):
        marks.append("duplicated modality (generator artefact)")
    return marks


def lift_score(m: dict) -> tuple[float, dict[str, float], list[str]]:
    signals = {
        "provenance": 0.25 if _has_provenance(m) else 0.0,
        "permissive_license": 0.10 if _permissive_license(m) else 0.0,
        "structural_depth": 0.25 * _structural_depth(m),
        "eval_linked": 0.15 * _eval_linked(m),
        "domain_specificity": 0.15 * _domain_specificity(m),
        "description_substance": 0.10 if len(_str(m.get("description"))) >= 240 else 0.0,
    }
    marks = _filler_markers(m)
    penalty = 0.0
    if "self-labelled scale-expansion" in marks:
        penalty += 0.50
    if "numeric-arm suffix (templated clone)" in marks:
        penalty += 0.25
    if "boilerplate description" in marks:
        penalty += 0.30
    if "fabricated default_model" in marks:
        penalty += 0.20
    if "duplicated modality (generator artefact)" in marks:
        penalty += 0.10
    raw = sum(signals.values()) - penalty
    return max(0.0, min(1.0, raw)), signals, marks


# --------------------------------------------------------------------------- #
# novelty: SimHash + LSH banding
# --------------------------------------------------------------------------- #
_TOKEN = re.compile(r"[a-z]+")
_REF_RE = re.compile(
    r"(?:harness|pipeline|benchmark|rule-pack|knowledge-pack|logic-pack|tool|"
    r"persona|adapter|rubric|dataset|schema|processor|pattern)/[a-z0-9]+(?:-[a-z0-9]+)*"
)


def _refs_in(m: dict) -> set[str]:
    """Component ids this manifest references (excluding its own id)."""
    out = {mt.group(0) for mt in _REF_RE.finditer(json.dumps(m, ensure_ascii=False))}
    out.discard(_str(m.get("id")))
    return out


def _fingerprint_text(m: dict) -> str:
    """Semantic fingerprint, digit-stripped so ``arm-007`` == ``arm-015``."""
    parts = [
        _str(m.get("type")),
        _str(m.get("name")),
        _str(m.get("description")),
        " ".join(sorted(str(c) for c in _list(m.get("capability")))),
        " ".join(sorted(str(i) for i in _list(m.get("industry")))),
        " ".join(sorted(str(t) for t in _list(m.get("tags")) if str(t).lower() not in FILLER_TAGS)),
    ]
    text = " ".join(parts).lower()
    return re.sub(r"\d+", "", text)


def simhash(text: str, bits: int = DEFAULT_SIMHASH_BITS) -> int:
    counts = defaultdict(int)
    for tok in _TOKEN.findall(text):
        counts[tok] += 1
    if not counts:
        return 0
    vec = [0] * bits
    for tok, weight in counts.items():
        h = int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=bits // 8).digest(), "big")
        for i in range(bits):
            vec[i] += weight if (h >> i) & 1 else -weight
    out = 0
    for i in range(bits):
        if vec[i] > 0:
            out |= 1 << i
    return out


def _bands(value: int, bits: int, n_bands: int) -> list[tuple[int, int]]:
    width = bits // n_bands
    mask = (1 << width) - 1
    return [(b, (value >> (b * width)) & mask) for b in range(n_bands)]


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def find_near_duplicates(
    items: list[tuple[Path, dict, int]],
    *, bits: int, n_bands: int, hamming_max: int,
) -> dict[Path, Path]:
    """Return {duplicate_path: canonical_path}. LSH-blocked, stable order."""
    buckets: dict[tuple[int, int], list[tuple[Path, int]]] = defaultdict(list)
    dupe_of: dict[Path, Path] = {}
    for path, manifest, sh in items:  # items already sorted by path
        mtype = _str(manifest.get("type"))
        found_canonical: Path | None = None
        band_keys = [(mtype, b, bits_val) for (b, bits_val) in _bands(sh, bits, n_bands)]
        for key in band_keys:
            for (cand_path, cand_sh) in buckets.get(key, ()):  # type: ignore[arg-type]
                if _hamming(sh, cand_sh) <= hamming_max:
                    found_canonical = dupe_of.get(cand_path, cand_path)
                    break
            if found_canonical:
                break
        if found_canonical is not None:
            dupe_of[path] = found_canonical
        else:
            for key in band_keys:
                buckets[key].append((path, sh))
    return dupe_of


# --------------------------------------------------------------------------- #
# gate
# --------------------------------------------------------------------------- #
def run_gate(
    root: Path,
    *,
    lift_floor: float = DEFAULT_LIFT_FLOOR,
    bits: int = DEFAULT_SIMHASH_BITS,
    n_bands: int = DEFAULT_LSH_BANDS,
    hamming_max: int = DEFAULT_HAMMING_MAX,
) -> dict[str, Any]:
    manifests = load_manifests(root)
    tracked = git_tracked_set()

    scored = []
    for path, m in manifests:
        lift, signals, marks = lift_score(m)
        scored.append((path, m, lift, signals, marks, simhash(_fingerprint_text(m), bits)))

    dupe_of = find_near_duplicates(
        [(p, m, sh) for (p, m, _l, _s, _mk, sh) in scored],
        bits=bits, n_bands=n_bands, hamming_max=hamming_max,
    )

    decisions: list[dict[str, Any]] = []
    for path, m, lift, signals, marks, _sh in scored:
        reasons: list[str] = []
        hard = sorted(set(marks) & HARD_FILLER_MARKS)
        if hard:
            reasons.append("filler markers: " + ", ".join(hard))
        if path in dupe_of:
            reasons.append(f"near-duplicate of {dupe_of[path].relative_to(root)}")
        if lift < lift_floor:
            reasons.append(f"capability-lift {lift:.2f} < floor {lift_floor:.2f} (near-empty)")
        is_tracked = path.resolve() in tracked
        decisions.append({
            "path": str(path.relative_to(root)),
            "id": m.get("id"),
            "type": m.get("type"),
            "lift": round(lift, 3),
            "signals": {k: round(v, 3) for k, v in signals.items()},
            "filler_markers": marks,
            "tracked": is_tracked,
            "decision": "keep" if not reasons else "cull",
            "reasons": reasons,
        })

    # Referential integrity: never cull a manifest that a SURVIVING manifest
    # references — that would create a dangling ref and re-break the validator.
    # Iterate to a fixpoint (a reprieved file may itself reference others).
    rel_to_manifest = {str(p.relative_to(root)): m for (p, m, *_x) in scored}
    for _ in range(10):
        referenced: set[str] = set()
        for d in decisions:
            if d["decision"] == "keep":
                referenced |= _refs_in(rel_to_manifest[d["path"]])
        flipped = 0
        for d in decisions:
            if d["decision"] == "cull" and d["id"] in referenced:
                d["decision"] = "keep"
                d["reasons"].append("kept for referential integrity (referenced by a surviving component)")
                flipped += 1
        if not flipped:
            break

    kept = [d for d in decisions if d["decision"] == "keep"]
    culled = [d for d in decisions if d["decision"] == "cull"]
    cull_tracked = [d for d in culled if d["tracked"]]
    cull_untracked = [d for d in culled if not d["tracked"]]

    by_type_cull: dict[str, int] = defaultdict(int)
    for d in culled:
        by_type_cull[str(d["type"])] += 1

    try:
        root_label = str(root.relative_to(ROOT))
    except ValueError:
        root_label = str(root)
    return {
        "root": root_label,
        "lift_floor": lift_floor,
        "total": len(decisions),
        "keep": len(kept),
        "cull": len(culled),
        "cull_tracked_curated_DO_NOT_DELETE": len(cull_tracked),
        "cull_untracked_safe_to_delete": len(cull_untracked),
        "cull_by_type": dict(sorted(by_type_cull.items(), key=lambda kv: -kv[1])),
        "decisions": decisions,
    }


def apply_cull(report: dict[str, Any], root: Path) -> dict[str, Any]:
    """Delete culled files that are NOT git-tracked. Curated files are kept."""
    deleted: list[str] = []
    skipped_tracked: list[str] = []
    for d in report["decisions"]:
        if d["decision"] != "cull":
            continue
        if d["tracked"]:
            skipped_tracked.append(d["path"])
            continue
        target = root / d["path"]
        if target.exists():
            target.unlink()
            deleted.append(d["path"])
    # prune now-empty dirs under the SCANNED root (not the module-global CATALOG,
    # which would touch unrelated dirs when --root points elsewhere)
    for p in sorted(root.rglob("*"), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()
    return {"deleted": len(deleted), "skipped_tracked": len(skipped_tracked)}


def _self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "catalog"
        (base / "adapters" / "scale").mkdir(parents=True)
        (base / "pipelines").mkdir(parents=True)
        # two near-identical filler clones
        for n in ("007", "015"):
            (base / "adapters" / "scale" / f"scale-arm-{n}.yaml").write_text(
                "id: \"adapter/scale-arm-%s\"\ntype: adapter\nname: \"Scale Arm %s\"\n"
                "description: \"Reusable google_gemini adapter profile for benchmark arms.\"\n"
                "license: MIT\nindustry: [ai, cross_industry]\ntags: [scale-expansion]\n"
                "capabilities: [text_generation, vision]\ncost_model: paid\n"
                "default_model: \"gemini-review-%s\"\n" % (n, n, n),
                encoding="utf-8",
            )
        # one substantive, grounded, structured pipeline
        (base / "pipelines" / "real.yaml").write_text(
            "id: \"pipeline/forced-labor-disclosure-grading\"\ntype: pipeline\n"
            "name: \"Forced-labor disclosure grading\"\n"
            "description: \"" + ("Grade supplier disclosures against CSDDD articles and ILO "
            "forced-labor indicators with citations and a right-of-reply path. " * 3) + "\"\n"
            "license: CC-BY-4.0\nindustry: [esg, supply_chain]\n"
            "attribution: {source_url: \"https://eur-lex.europa.eu/x\", author: EU}\n"
            "steps: [{ref: harness/a}, {ref: tool/b}, {ref: rubric/c}]\n"
            "rubric: \"rubric/esg\"\n",
            encoding="utf-8",
        )
        rep = run_gate(base, lift_floor=DEFAULT_LIFT_FLOOR)
        print(json.dumps({k: v for k, v in rep.items() if k != "decisions"}, indent=2))
        assert rep["total"] == 3, rep["total"]
        assert rep["keep"] == 1, f"expected 1 keep, got {rep['keep']}"
        assert rep["cull"] == 2, f"expected 2 cull, got {rep['cull']}"
        kept_ids = [d["id"] for d in rep["decisions"] if d["decision"] == "keep"]
        assert kept_ids == ["pipeline/forced-labor-disclosure-grading"], kept_ids
        # one clone culled for low lift, the other also as near-duplicate
        dup_reasons = [r for d in rep["decisions"] if d["decision"] == "cull" for r in d["reasons"]]
        assert any("near-duplicate" in r for r in dup_reasons), dup_reasons
        print("self-test OK")
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capability-lift + novelty gate for catalog manifests.")
    parser.add_argument("--root", default=str(CATALOG), help="Catalog root to scan (default: catalog/).")
    parser.add_argument("--lift-floor", type=float, default=DEFAULT_LIFT_FLOOR)
    parser.add_argument("--hamming-max", type=int, default=DEFAULT_HAMMING_MAX)
    parser.add_argument("--report", help="Write the full per-manifest report JSON here.")
    parser.add_argument("--apply", action="store_true", help="Delete culled UNTRACKED files (curated files are never deleted).")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()

    root = Path(args.root).resolve()
    report = run_gate(root, lift_floor=args.lift_floor, hamming_max=args.hamming_max)
    summary = {k: v for k, v in report.items() if k != "decisions"}
    print(json.dumps(summary, indent=2))

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nfull report -> {args.report}")

    if args.apply:
        result = apply_cull(report, root)
        print(f"\nAPPLIED cull: deleted {result['deleted']} untracked files; "
              f"skipped {result['skipped_tracked']} tracked (curated, never deleted).")
    else:
        print("\n(dry run — re-run with --apply to delete culled UNTRACKED files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
