#!/usr/bin/env python3
"""scripts.primitive_package_contract — the FORMAL-PRIMITIVE-PACKAGE contract (2026-07-08): the single source
that turns a bare executable-pack card into a formal primitive package by ADDING (never removing) the fields
the 2026 skills-as-an-OS research says a production primitive needs — verifier link, declared failure modes,
a permission manifest derived from a deterministic code-safety scan, marginal-utility evidence (honest:
unmeasured until benched), runtime/model compatibility, a determinism level, a 5-stage lifecycle stage, an
artifact hash + provenance, and governance retrieval tags that flow into the multi-index as NEW facet
dimensions. Grounded in Formal Skill (2605.19604), SkVM (2604.03088), SWE-Skills-Bench (2603.15401).

This is ADDITIVE and lossless: `formalize_card` keeps every existing card field + `primitive_id` byte-for-byte
and only appends. The governance vocabulary is the single source `vocabularies/primitive-governance-role-matrix.
yaml` (also auto-loaded as multi-index facet columns — one seam, two consumers). The code-safety scan here is
DESCRIPTIVE (what the body touches → permission_manifest); the PRESCRIPTIVE allow/deny policy is the separate
`scripts/primitive_security_gate.py`. Nothing here promotes anything — every card stays candidate=true,
serves_truth=false; lifecycle_stage starts at "candidate" and only `promote_primitive` (with receipts) moves it.

    python3 scripts/primitive_package_contract.py --self-test
    python3 scripts/primitive_package_contract.py --demo   # formalize a sample card, print it
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
import ast  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the data-plane hash authority (no hashlib)
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"primitive_package_contract requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CONTRACT_VERSION = "primitive-package-contract-v1"
#: the formal-package fields this contract guarantees are present on every formalized card (the lint gate keys)
FORMAL_FIELDS: tuple[str, ...] = (
    "execution_model", "determinism_level", "lifecycle_stage", "verifier_id", "verifier_kind",
    "failure_modes", "permission_manifest", "marginal_utility_evidence", "runtime_target",
    "compatible_runtimes", "compatible_models", "risk_tier", "artifact_hash", "provenance",
    "promotion_receipts", "retrieval_tags")

# ── deterministic code-safety scan (descriptive; feeds permission_manifest + the security-gate seed) ─────────
#: import root -> side-effect class (single source; the security gate's YAML is the prescriptive twin)
_NETWORK_MODS = frozenset({"socket", "urllib", "http", "requests", "httpx", "aiohttp", "ftplib", "telnetlib"})
_SUBPROCESS_MODS = frozenset({"subprocess", "pty"})
_DESERIALIZE_MODS = frozenset({"pickle", "marshal", "ctypes", "cffi", "shelve"})
_DYNAMIC_CALLS = frozenset({"eval", "exec", "compile", "__import__"})
_FS_WRITE_RE = re.compile(r"open\s*\([^)]*['\"][wax]\+?b?['\"]|\.write_(text|bytes)\s*\(|shutil\.(rmtree|move|copy)")
_ENV_RE = re.compile(r"os\.environ|os\.getenv|getpass")
_UNSAFE_YAML_RE = re.compile(r"yaml\.load\s*\((?![^)]*SafeLoader)")


def code_safety_scan(body: str) -> dict[str, Any]:
    """AST + regex scan of an executable body → the side-effect classes it touches. Deterministic, pure.
    DESCRIPTIVE only: it reports what the code does, it does not allow/deny (that is the security gate)."""
    flags: set[str] = set()
    imports: set[str] = set()
    try:
        tree = ast.parse(body or "")
    except SyntaxError:
        return {"parse_error": True, "flags": ["unparseable"], "imports": [], "side_effect_free": False}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            fn = node.func
            # ONLY the bare builtins eval/exec/compile/__import__ are dynamic execution. An ATTRIBUTE call
            # like re.compile(...) / ast.compile is NOT — flagging it was a false positive that quarantined
            # every regex-using primitive (verify-the-verifier: the gate itself must be correct).
            if isinstance(fn, ast.Name) and fn.id in _DYNAMIC_CALLS:
                flags.add("dynamic_exec")
            if isinstance(fn, ast.Attribute) and fn.attr in ("system", "run", "Popen", "call", "check_output") \
                    and isinstance(fn.value, ast.Name) and fn.value.id in ("subprocess", "os"):
                flags.add("subprocess")
    roots = imports
    if roots & _NETWORK_MODS:
        flags.add("network")
    if roots & _SUBPROCESS_MODS:
        flags.add("subprocess")
    if roots & _DESERIALIZE_MODS:
        flags.add("unsafe_deserialize")
    if _FS_WRITE_RE.search(body or ""):
        flags.add("filesystem_write")
    if _ENV_RE.search(body or ""):
        flags.add("environment_read")
    if _UNSAFE_YAML_RE.search(body or ""):
        flags.add("unsafe_yaml_load")
    return {"parse_error": False, "flags": sorted(flags), "imports": sorted(roots),
            "side_effect_free": not flags}


def permission_manifest(body: str) -> dict[str, Any]:
    """The declared-capability record: what a primitive is permitted/observed to touch (§security)."""
    scan = code_safety_scan(body)
    fl = set(scan["flags"])
    if fl & {"subprocess", "dynamic_exec", "unsafe_deserialize"}:
        pclass = "subprocess" if "subprocess" in fl else "dynamic_exec"
    elif "network" in fl:
        pclass = "network egress"
    elif "filesystem_write" in fl:
        pclass = "filesystem write"
    elif "environment_read" in fl:
        pclass = "environment read"
    else:
        pclass = "pure"
    return {"permission_class": pclass, "side_effect_free": scan["side_effect_free"],
            "network_access": "network" in fl, "filesystem_write": "filesystem_write" in fl,
            "subprocess": "subprocess" in fl, "dynamic_exec": "dynamic_exec" in fl,
            "secret_access": "environment_read" in fl, "security_flags": scan["flags"],
            "imports": scan["imports"]}


def classify_determinism(manifest: dict[str, Any], body: str) -> str:
    """Determinism budget D0..D4 (owner spec §B). Truth-serving usually needs D0/D1 (occasionally D2)."""
    fl = set(manifest.get("security_flags", []))
    if fl & {"dynamic_exec", "unsafe_deserialize", "subprocess"}:
        return "D4_stochastic"        # unbounded/unsafe → may not serve truth
    if "network" in fl:
        return "D2_bounded_external"   # external call → needs provenance/caching
    if re.search(r"\b(random|secrets\.token|uuid4|datetime\.now|time\.time|Math\.random)\b", body or ""):
        return "D1_seeded"             # nondeterministic-by-default unless seeded/frozen
    return "D0_pure"


def _execution_model(card: dict[str, Any], manifest: dict[str, Any]) -> str:
    if not manifest["side_effect_free"]:
        return "external_tool" if manifest["network_access"] or manifest["subprocess"] else "stateful_fit_transform"
    return "compiled_workflow" if card.get("kind") == "primitive_group" else "pure_function"


def _risk_tier(manifest: dict[str, Any]) -> str:
    fl = set(manifest.get("security_flags", []))
    if fl & {"dynamic_exec", "unsafe_deserialize"}:
        return "quarantined"
    if fl & {"subprocess", "network", "filesystem_write"}:
        return "review required"
    if fl:
        return "low risk"
    return "safe"


def formalize_card(card: dict[str, Any]) -> dict[str, Any]:
    """Bare card → formal primitive package (ADDITIVE: keeps every existing field + primitive_id)."""
    body = card.get("executable_body") or ""
    manifest = permission_manifest(body)
    determinism = classify_determinism(manifest, body)
    artifact_hash = canonical_id("artifact", body, card.get("impl_name") or card.get("title") or "")
    runtime = {"python": "python function"}.get(card.get("language", "python"), card.get("language", "python"))
    govern_tags = [determinism, manifest["permission_class"], _risk_tier(manifest), "candidate", runtime,
                   "oracle self test"]
    existing_tags = card.get("retrieval_tags") or card.get("tags") or []
    if isinstance(existing_tags, str):
        existing_tags = [existing_tags]
    formal = {
        "execution_model": _execution_model(card, manifest),
        "determinism_level": determinism,
        "lifecycle_stage": "candidate",  # nothing auto-promotes; promote_primitive moves this with receipts
        "verifier_id": f"{card.get('pack_module') or card.get('record_type', 'primitive')}::_self_test",
        "verifier_kind": "oracle self test",
        "failure_modes": card.get("failure_modes", []),  # honest: unenumerated until a trace/bench populates
        "permission_manifest": manifest,
        "marginal_utility_evidence": {"status": "unmeasured", "lift": None, "measured_against": None,
                                      "benchmark_id": None},  # honest: no lift proven yet (SWE-Skills-Bench law)
        "runtime_target": runtime,
        "compatible_runtimes": ["python"] if card.get("language", "python") == "python" else [card["language"]],
        "compatible_models": ["*"] if manifest["side_effect_free"] else [],  # deterministic → model-agnostic
        "risk_tier": _risk_tier(manifest),
        "artifact_hash": artifact_hash,
        "provenance": {"artifact_hash": artifact_hash, "contract_version": CONTRACT_VERSION,
                       "source_pack": card.get("pack_module"), "verifier": "oracle self test"},
        "promotion_receipts": {},  # filled by promote_primitive as gates pass
        "retrieval_tags": sorted(set(list(existing_tags) + govern_tags)),
    }
    return {**card, **formal, **BOUNDARY}  # BOUNDARY last: never accidentally serves_truth


def formalize_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [formalize_card(c) for c in cards]


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    pure = {"primitive_id": "p1", "impl_name": "strip_fn", "language": "python", "kind": "primitive",
            "title": "t", "executable_body": "def strip_fn(x):\n    return x.strip()\n", "serves_truth": False}
    f = formalize_card(pure)
    checks.append(("pure card: all FORMAL_FIELDS present, additive (keeps primitive_id + body)",
                   all(k in f for k in FORMAL_FIELDS) and f["primitive_id"] == "p1"
                   and f["executable_body"] == pure["executable_body"]))
    checks.append(("pure card: side_effect_free, D0_pure, pure permission_class, safe risk, model-agnostic",
                   f["permission_manifest"]["side_effect_free"] and f["determinism_level"] == "D0_pure"
                   and f["permission_manifest"]["permission_class"] == "pure"
                   and f["risk_tier"] == "safe" and f["compatible_models"] == ["*"]))
    checks.append(("never serves truth; starts candidate lifecycle; honest unmeasured utility",
                   f["serves_truth"] is False and f["lifecycle_stage"] == "candidate"
                   and f["marginal_utility_evidence"]["status"] == "unmeasured"))
    checks.append(("governance retrieval_tags carry facet terms for the multi-index (determinism/risk/stage)",
                   "D0_pure" in f["retrieval_tags"] and "candidate" in f["retrieval_tags"]
                   and "safe" in f["retrieval_tags"]))
    # dangerous bodies are classified correctly (the security-gate seed)
    net = formalize_card(dict(pure, executable_body="import requests\ndef f():\n    return requests.get('x')"))
    checks.append(("network body: network_access, D2_bounded_external, review-required, NOT model-agnostic",
                   net["permission_manifest"]["network_access"] and net["determinism_level"] == "D2_bounded_external"
                   and net["risk_tier"] == "review required" and net["compatible_models"] == []))
    ev = formalize_card(dict(pure, executable_body="def f(s):\n    return eval(s)\n"))
    checks.append(("eval body: dynamic_exec flag, D4_stochastic, QUARANTINED",
                   "dynamic_exec" in ev["permission_manifest"]["security_flags"]
                   and ev["determinism_level"] == "D4_stochastic" and ev["risk_tier"] == "quarantined"))
    sub = code_safety_scan("import subprocess\ndef f():\n    subprocess.run(['ls'])")
    checks.append(("subprocess detected via import + call", "subprocess" in sub["flags"]))
    checks.append(("unsafe yaml.load flagged; SafeLoader not flagged",
                   "unsafe_yaml_load" in code_safety_scan("import yaml\nyaml.load(x)")["flags"]
                   and "unsafe_yaml_load" not in
                   code_safety_scan("import yaml\nyaml.load(x, Loader=yaml.SafeLoader)")["flags"]))
    checks.append(("artifact_hash is deterministic + content-addressed (same body -> same hash)",
                   formalize_card(pure)["artifact_hash"] == f["artifact_hash"]
                   and f["artifact_hash"].startswith("artifact-")))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - primitive_package_contract: {len(FORMAL_FIELDS)} formal fields, additive+lossless, "
          f"deterministic code-safety scan → permission manifest + determinism budget (D0..D4) + risk tier + "
          f"content-addressed provenance. Governance tags feed the multi-index. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.demo:
        sample = {"primitive_id": "demo", "impl_name": "demo_fn", "language": "python", "kind": "primitive",
                  "title": "demo", "executable_body": "def demo_fn(x):\n    return x.upper()\n"}
        print(json.dumps(formalize_card(sample), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
