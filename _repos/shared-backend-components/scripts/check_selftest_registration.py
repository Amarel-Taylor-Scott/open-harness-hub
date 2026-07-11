#!/usr/bin/env python3
"""scripts.check_selftest_registration — the META-gate: verify-the-verifier.

Every verifier-shaped script under ``scripts/`` (basename ``check_*`` / ``validate_*`` / ``verify_*``)
that exposes the repo's ``--self-test`` convention is a proof that only EARNS its keep when the honest
proof runner (``scripts/run_proofs.py`` over ``scripts.flywheel_proof_modules.PROOF_MODULES``) actually
runs it. A verifier that self-tests but is NOT registered is a silent hole: its ``--self-test`` never
runs in the suite, so a genuine red hides behind a green ``run_proofs`` (the audit that spawned this gate
found ~269 self-testing scripts unregistered and **2 shipping real bugs**).

This gate closes that hole. It statically:

  1. discovers verifier-shaped scripts under ``scripts/`` that carry the ``--self-test`` token,
  2. subtracts everything ``PROOF_MODULES`` already registers (matched by basename — names are
     globally unique by repo law, so basename identity is exact and path-form-drift proof),
  3. subtracts a curated grandfather ``STANDALONE_ALLOWLIST`` of verifiers that are legitimately NOT in
     the suite (live/network/manual-recording checks that cannot run offline in the flywheel), and
  4. **FAILS, printing the offenders**, if anything remains.

The allowlist is a **ratchet-DOWN baseline** (same shape as the canonical_id / pyprefix baselines): a NEW
verifier-shaped ``--self-test`` script that is neither registered nor allowlisted fails this gate, forcing
the author to register it (the honest default) or justify it into the allowlist in the SAME change. As the
orchestrator registers the grandfathered entries, they are pruned from the allowlist here.

This file does NOT edit ``flywheel_proof_modules.py`` — the orchestrator wires this check into
``PROOF_MODULES`` itself; this gate only reads the registry.

CLI:
    python3 _repos/shared-backend-components/scripts/check_selftest_registration.py             # audit the real repo
    python3 _repos/shared-backend-components/scripts/check_selftest_registration.py --list      # audit + dump the full unregistered set for triage
    python3 _repos/shared-backend-components/scripts/check_selftest_registration.py --self-test  # mutation-gate proof (the detector catches a planted hole) + the real-repo audit
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()),
             Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:                      # self-bootstrap: a gate must not false-RED just because
    sys.path.insert(0, str(_REPO))                  # the caller forgot PYTHONPATH=. (mirror run_proofs.py).

#: This file lives IN the scripts dir, so its parent IS the real on-disk scripts/ root — robust to CWD
#: and to the _repos/ migration (no path guessing).
_SCRIPTS_DIR = Path(__file__).resolve().parent

#: Basename prefixes that mark a script as "verifier-shaped" (a proof/gate, not product or a data emitter).
VERIFIER_PREFIXES: tuple[str, ...] = ("check_", "validate_", "verify_")

#: The repo convention token every runner-executable proof carries. `run_proofs.py` invokes each registered
#: module as `python <path> --self-test`; a file that never spells this literal is not a `--self-test` proof.
SELFTEST_TOKEN: str = "--self-test"

#: Curated GRANDFATHER baseline — verifier-shaped `--self-test` scripts that are intentionally NOT in
#: PROOF_MODULES because they cannot run offline in the flywheel (live network / browser recording /
#: paid-endpoint / manual-capture readiness), or are pending triage-then-registration by the orchestrator.
#: RATCHET-DOWN law: this set only SHRINKS. Never add a new entry to silence this gate without a warrant;
#: the honest fix for a NEW offender is to register it in PROOF_MODULES. Basenames (names are globally unique).
STANDALONE_ALLOWLIST: frozenset[str] = frozenset({
    # AIDevObserver launch/session/registry surfaces — depend on the observer local service / live registry
    "check_aidevobserver_launch_readiness.py",
    "check_aidevobserver_local_registry_connector.py",
    "check_aidevobserver_operational_primitive_search.py",
    "check_aidevobserver_session_benchmark.py",
    "check_aidevobserver_source_acquisition_surfaces.py",
    # runtime / provider / plane checks that exercise moved product code (src.<x> under _repos/<x>/backend)
    "check_byo_compute.py",
    "check_capability_self_heal_on_source_change.py",
    "check_context_compressor.py",
    "check_dag_pipeline.py",
    "check_eval_suite_contract.py",
    "check_execution_provider_factory.py",
    "check_global_multimodel_primitive_foundry.py",
    "check_high_priority_primitive_opportunity_rankings.py",
    "check_interest_rate_caps_e2e.py",
    "check_local_dev_tunnel_auth_runtime.py",
    "check_marketplace_primitive_source_surface_pack.py",
    "check_medium_config.py",
    "check_model_plane.py",
    "check_multi_set_membership_index.py",
    "check_plane_separation.py",
    "check_primitive_agent_graph_path_mixtures.py",
    "check_primitive_cloud_guardrail_runtime.py",
    "check_primitive_customization_overlays.py",
    "check_primitive_problem_solution_details.py",
    "check_primitive_variation_dimension_atlas.py",
    "check_recording_readiness.py",
    "check_scalable_record_store.py",
    "check_service_auth_consumption_model.py",
    "check_substrate_backed_descent.py",
    "check_surface_map.py",
    "check_teleon_control_plane.py",
    "check_teleon_example_descents.py",
    # live/manual capture — need a browser or a paid/live endpoint, never green offline
    "check_yc_demo_recording.py",
    # candidate-emitter verifier that runs against generated candidate rows, not offline fixtures
    "verify_primitive_candidates.py",
})

#: This gate would discover ITSELF (it is `check_*` and spells `--self-test`). A gate need not gate its own
#: registration — the orchestrator registers it — so it is excluded from its own audit by name.
_OWN_BASENAME: str = os.path.basename(__file__)


def _selftest_reg_is_verifier_shaped(basename: str) -> bool:
    """True when *basename* is a `.py` whose name marks it a verifier (check_/validate_/verify_)."""
    return basename.endswith(".py") and basename.startswith(VERIFIER_PREFIXES)


def _selftest_reg_exposes_selftest(text: str) -> bool:
    """True when source *text* spells the `--self-test` convention token (i.e. it is a runnable proof)."""
    return SELFTEST_TOKEN in text


def _selftest_reg_discover(scripts_dir: Path) -> set[str]:
    """Basenames of verifier-shaped scripts under *scripts_dir* that expose `--self-test` (own file excluded)."""
    found: set[str] = set()
    for path in scripts_dir.rglob("*.py"):
        name = path.name
        if name == _OWN_BASENAME or not _selftest_reg_is_verifier_shaped(name):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _selftest_reg_exposes_selftest(text):
            found.add(name)
    return found


def _selftest_reg_registered_basenames(proof_modules: list[tuple[str, str]]) -> set[str]:
    """The set of registered proof basenames from PROOF_MODULES (path column)."""
    return {os.path.basename(path) for path, _label in proof_modules}


def _selftest_reg_unregistered(discovered: set[str], registered: set[str], allowlist: frozenset[str]) -> list[str]:
    """Sorted verifier-shaped self-tests that are neither registered NOR allowlisted (the failure set)."""
    return sorted(discovered - registered - allowlist)


def _selftest_reg_dead_allowlist(discovered: set[str], allowlist: frozenset[str]) -> list[str]:
    """Allowlist entries that are NO LONGER a verifier-shaped self-test on disk (rot: stale / renamed / typo)."""
    return sorted(allowlist - discovered)


def _selftest_reg_redundant_allowlist(registered: set[str], allowlist: frozenset[str]) -> list[str]:
    """Allowlist entries that are ALSO registered — harmless but should be pruned (ratchet-down housekeeping)."""
    return sorted(allowlist & registered)


def _selftest_reg_audit(scripts_dir: Path, proof_modules: list[tuple[str, str]]) -> dict:
    """Run the real-repo audit; return a structured result (does not print / exit)."""
    discovered = _selftest_reg_discover(scripts_dir)
    registered = _selftest_reg_registered_basenames(proof_modules)
    return {
        "discovered": discovered,
        "registered_verifier_selftests": sorted(discovered & registered),
        "unregistered": _selftest_reg_unregistered(discovered, registered, STANDALONE_ALLOWLIST),
        "dead_allowlist": _selftest_reg_dead_allowlist(discovered, STANDALONE_ALLOWLIST),
        "redundant_allowlist": _selftest_reg_redundant_allowlist(registered, STANDALONE_ALLOWLIST),
    }


def _run_real(show_list: bool) -> int:
    from scripts.flywheel_proof_modules import PROOF_MODULES

    res = _selftest_reg_audit(_SCRIPTS_DIR, PROOF_MODULES)
    disc, reg = res["discovered"], res["registered_verifier_selftests"]
    unreg, dead, redundant = res["unregistered"], res["dead_allowlist"], res["redundant_allowlist"]

    print(f"verifier-shaped --self-test scripts discovered: {len(disc)}")
    print(f"  registered in PROOF_MODULES:                  {len(reg)}")
    print(f"  grandfathered in STANDALONE_ALLOWLIST:        {len(STANDALONE_ALLOWLIST)} "
          f"(covering {len(STANDALONE_ALLOWLIST) - len(redundant)} still-unregistered)")
    print(f"  UNREGISTERED & UNALLOWLISTED (must be 0):     {len(unreg)}")

    if redundant:
        print(f"\nNOTICE: {len(redundant)} allowlist entr{'y is' if len(redundant) == 1 else 'ies are'} now "
              f"registered — prune from STANDALONE_ALLOWLIST (ratchet down): {redundant}")

    if show_list and (unreg or dead):
        print("\n--- full triage dump ---")
        for b in unreg:
            print(f"  UNREGISTERED  {b}")
        for b in dead:
            print(f"  DEAD-ALLOWLIST {b}")

    fails: list[str] = []
    if unreg:
        fails.append(f"{len(unreg)} verifier-shaped --self-test script(s) hide from the proof suite (register "
                     f"them in PROOF_MODULES, or allowlist with a warrant): {unreg}")
    if dead:
        fails.append(f"{len(dead)} STANDALONE_ALLOWLIST entr{'y' if len(dead) == 1 else 'ies'} no longer name a "
                     f"verifier-shaped --self-test script (rot — prune or fix the name): {dead}")

    if fails:
        print("\nFAIL - check_selftest_registration:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nPASS - check_selftest_registration: every verifier-shaped --self-test under scripts/ is either "
          "registered in PROOF_MODULES or carries an explicit standalone warrant; no proof hides from run_proofs.")
    return 0


def _self_test() -> int:
    """Mutation gate: prove the detector + diff actually CATCH a planted hole (not just pass vacuously)."""
    fails: list[str] = []

    def ck(label: str, cond: bool, extra: str = "") -> None:
        if not cond:
            fails.append(label + (f" [{extra}]" if extra else ""))

    # 1) shape classifier — positive + negative.
    ck("check_ is verifier-shaped", _selftest_reg_is_verifier_shaped("check_x.py"))
    ck("validate_ is verifier-shaped", _selftest_reg_is_verifier_shaped("validate_y.py"))
    ck("verify_ is verifier-shaped", _selftest_reg_is_verifier_shaped("verify_z.py"))
    ck("product code is NOT verifier-shaped", not _selftest_reg_is_verifier_shaped("build_catalog_pages.py"))
    ck("non-.py is NOT verifier-shaped", not _selftest_reg_is_verifier_shaped("check_x.txt"))

    # 2) token detector — only the real convention token counts.
    ck("exposes --self-test", _selftest_reg_exposes_selftest("if arg == '--self-test':"))
    ck("bare 'self_test' fn name does NOT count as the token", not _selftest_reg_exposes_selftest("def self_test():"))

    # 3) diff logic — a discovered verifier that is neither registered nor allowlisted is REPORTED.
    discovered = {"check_registered.py", "check_allowed.py", "check_HOLE.py"}
    registered = {"check_registered.py", "unrelated_module.py"}
    allowlist = frozenset({"check_allowed.py"})
    unreg = _selftest_reg_unregistered(discovered, registered, allowlist)
    ck("planted unregistered verifier is caught", unreg == ["check_HOLE.py"], str(unreg))
    ck("registered verifier is NOT flagged", "check_registered.py" not in unreg)
    ck("allowlisted verifier is NOT flagged", "check_allowed.py" not in unreg)

    # 4) MUTATION — if the diff wrongly treated 'registered' as covering everything, the hole would pass.
    #    Assert the failure set is non-empty exactly because of the planted hole.
    ck("mutation: removing the hole from discovery makes it green",
       _selftest_reg_unregistered(discovered - {"check_HOLE.py"}, registered, allowlist) == [])

    # 5) allowlist hygiene helpers.
    ck("dead allowlist entry (not on disk) is caught",
       _selftest_reg_dead_allowlist({"check_a.py"}, frozenset({"check_a.py", "check_ghost.py"})) == ["check_ghost.py"])
    ck("redundant allowlist entry (also registered) is caught",
       _selftest_reg_redundant_allowlist({"check_a.py"}, frozenset({"check_a.py"})) == ["check_a.py"])

    # 6) self-exclusion — this gate never audits itself.
    ck("own basename excluded from discovery", _OWN_BASENAME not in _selftest_reg_discover(_SCRIPTS_DIR))

    # 7) allowlist is TIGHT today: every entry currently exists as a verifier-shaped --self-test on disk
    #    (no rot) — this is what lets the real audit go GREEN now.
    from scripts.flywheel_proof_modules import PROOF_MODULES
    res = _selftest_reg_audit(_SCRIPTS_DIR, PROOF_MODULES)
    ck("no dead allowlist entries in the real repo", res["dead_allowlist"] == [], str(res["dead_allowlist"]))
    ck("real repo audit is GREEN (0 unregistered-and-unallowlisted)", res["unregistered"] == [],
       str(res["unregistered"]))

    print("check_selftest_registration self-test: "
          + ("PASS - detector catches a planted unregistered verifier; allowlist is tight; real repo green."
             if not fails else f"{len(fails)} FAILURES: {fails}"))
    if fails:
        return 1
    # the self-test also asserts the LIVE gate is green today.
    return _run_real(show_list=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run the mutation-gate proof, then the real audit")
    parser.add_argument("--list", action="store_true", help="dump the full unregistered/dead set for triage")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    return _run_real(show_list=args.list)


if __name__ == "__main__":
    raise SystemExit(main())
