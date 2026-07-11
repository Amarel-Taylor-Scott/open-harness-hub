#!/usr/bin/env python3
"""scripts.app_digestion_primitive_generation_pack — treat app/website DIGESTION tools as a PRIMITIVE-GENERATION
engine (candidate-only).

Owner insight (2026-07-08): tools like the AI website/app cloner are important NOT to rebuild our surfaces, but
because their prompts/skills/systems DIGEST an app — how it is built, how it could be built, its UI/UX templates,
design tokens, components, interactions — and that digestion IDEATES and generates reusable primitives. This is
our own thesis ("decompose real artifacts into typed candidate primitives") applied to the frontend/UX modality:
the SAME source-acquisition -> typed-candidate-primitive supply chain as `document_ingestion_factory_spec.py`,
one modality over (documents -> apps/UI/UX).

Grounded in the real `/clone-website` skill methodology (JCodesMore ai-website-cloner-template, MIT): a
multi-phase pipeline — Reconnaissance (screenshots + design-token extraction + interaction sweep) -> Foundation
(fonts/colors/globals/assets) -> Component Specs (exact getComputedStyle values, states, behaviors, content) ->
Parallel Build (builder agents in git worktrees, one per section) -> Assembly & QA (merge + visual diff vs
original). We do NOT clone-and-pass-off (guardrails below); we digest to GENERATE typed, source-grounded,
USEFUL-by-construction primitive candidates across the UI/UX families base models under-serve.

USEFUL, not just voluminous: every generated candidate carries a lift hypothesis + durability class so it is
screened by the two-axis admission gate (lift over the bare model AND structural durability), is grounded in a
real source (provenance), and emits typed edges so it composes. candidate=true / serves_truth=false throughout.

    python3 scripts/app_digestion_primitive_generation_pack.py --self-test
    python3 scripts/app_digestion_primitive_generation_pack.py --emit
    python3 scripts/app_digestion_primitive_generation_pack.py --show
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"app_digestion_primitive_generation_pack requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
GEN_ID_PREFIX = "prim-appdigest"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
PACK_FILENAME = "app_digestion_primitive_generation_cards.jsonl"
SPEC_FILENAME = "app_digestion_primitive_generation_spec.json"
PACKAGED_AT = "2026-07-08T00:00:00Z"
SOURCE_REFS = [
    "JCodesMore/ai-website-cloner-template (MIT) — /clone-website skill: recon -> foundation -> component "
    "specs (exact getComputedStyle) -> parallel worktree build -> assembly & visual-diff QA",
    "owner directive 2026-07-08: digestion tools are primitive-GENERATION engines (prompts/skills digest an "
    "app -> UI/UX templates, build understanding, rebuild plans -> primitives)",
]

# ── the digestion pipeline as a PRIMITIVE-GENERATION lane. Each stage: what it extracts, which primitive family
#    it generates, and the reusable Action primitive (the prompt/skill/rubric) that performs it. Grounded in the
#    real /clone-website phases, generalized to any app/site/repo. ────────────────────────────────────────────
_DIGESTION_PIPELINE: list[dict[str, Any]] = [
    {"stage": "reconnaissance", "cloner_phase": "Reconnaissance",
     "extracts": ["screenshots", "dom_structure", "asset_inventory", "interaction_sweep(scroll/click/hover)",
                  "responsive_breakpoints"],
     "generates_family": "observation", "action": "recon_sweep_action",
     "input_edge": "AppOrSiteSource", "output_edge": "DigestionObservations"},
    {"stage": "design_token_extraction", "cloner_phase": "Foundation",
     "extracts": ["color_system(oklch)", "typography_scale", "spacing_scale", "radii", "shadows/elevation",
                  "motion/easing", "fonts", "downloaded_assets"],
     "generates_family": "design_token", "action": "design_token_extractor_action",
     "input_edge": "DigestionObservations", "output_edge": "DesignTokenSet"},
    {"stage": "component_decomposition", "cloner_phase": "Component Specs",
     "extracts": ["component_boundaries", "exact_computed_css(getComputedStyle)", "multi_state_content",
                  "behaviors", "responsive_variants", "asset_refs"],
     "generates_family": "component", "action": "component_spec_writer_action",
     "input_edge": "DesignTokenSet", "output_edge": "ComponentSpecSet"},
    {"stage": "interaction_state_modeling", "cloner_phase": "Component Specs",
     "extracts": ["states(hover/focus/active/loading/empty/error)", "transitions", "form_validation",
                  "keyboard_nav", "aria_roles"],
     "generates_family": "interaction_state", "action": "interaction_model_action",
     "input_edge": "ComponentSpecSet", "output_edge": "InteractionStateModels"},
    {"stage": "build_understanding", "cloner_phase": "Component Specs",
     "extracts": ["inferred_stack/framework", "architecture_patterns", "framework_idioms",
                  "data_flow", "routing"],
     "generates_family": "framework_idiom", "action": "build_understanding_action",
     "input_edge": "InteractionStateModels", "output_edge": "BuildUnderstanding"},
    {"stage": "rebuild_planning", "cloner_phase": "Parallel Build",
     "extracts": ["how_it_could_be_built", "alternative_implementations", "per_section_build_specs",
                  "worktree_dispatch_plan"],
     "generates_family": "rebuild_plan", "action": "rebuild_planner_action",
     "input_edge": "BuildUnderstanding", "output_edge": "RebuildPlan"},
    {"stage": "primitive_candidate_generation", "cloner_phase": "Parallel Build",
     "extracts": ["typed_candidate_primitives_per_family", "typed_input_output_edges", "lift_hypotheses"],
     "generates_family": "all", "action": "primitive_candidate_writer_action",
     "input_edge": "RebuildPlan", "output_edge": "PrimitiveCandidateSet"},
    {"stage": "assembly_qa_verification", "cloner_phase": "Assembly & QA",
     "extracts": ["visual_diff_vs_original", "spec_conformance", "a11y_audit", "responsive_audit"],
     "generates_family": "verifier", "action": "visual_diff_qa_action",
     "input_edge": "PrimitiveCandidateSet", "output_edge": "VerifiedCandidateSet"},
]

# ── the UI/UX/frontend primitive FAMILIES this engine generates (the negative space we under-serve today) ────
_GENERATED_FAMILIES: dict[str, list[str]] = {
    "observation": ["capture_screenshot", "sweep_dom_structure", "inventory_assets", "sweep_interactions",
                    "probe_responsive_breakpoints"],
    "design_token": ["extract_color_system_oklch", "extract_typography_scale", "extract_spacing_scale",
                     "extract_radius_scale", "extract_elevation_shadows", "extract_motion_easing",
                     "extract_breakpoint_map"],
    "component": ["nav_bar", "hero_section", "feature_card", "pricing_table", "form_field", "data_table",
                  "modal_dialog", "tabs", "accordion", "toast", "dropdown_menu", "pagination", "carousel",
                  "footer"],
    "layout": ["responsive_grid", "flex_stack", "sidebar_shell", "holy_grail", "masonry", "container_query_wrap"],
    "interaction_state": ["hover_focus_active_states", "loading_empty_error_states", "form_validation_flow",
                          "optimistic_update", "drag_and_drop", "focus_trap"],
    "responsive": ["breakpoint_map", "fluid_typography", "adaptive_navigation", "container_query_component"],
    "a11y": ["aria_role_map", "keyboard_nav_order", "focus_visible_ring", "contrast_check", "reduced_motion"],
    "framework_idiom": ["react_hook_pattern", "next_app_router_route", "server_component", "shadcn_primitive",
                        "tailwind_token_binding"],
    "rebuild_plan": ["platform_migration_wp_to_next", "lost_source_recovery", "legacy_stack_modernization",
                     "design_system_extraction"],
    "verifier": ["visual_diff_verifier", "computed_css_conformance", "a11y_audit_verifier",
                 "responsive_audit_verifier"],
}

# ── the digestion PROMPTS/SKILLS themselves as reusable Action primitives (persona/tool/processor/harness/rubric
#    = an Action in our taxonomy). This is the owner's "they have the prompts, skills, and systems" made concrete. ─
_DIGESTION_ACTIONS: list[dict[str, str]] = [
    {"action": "recon_sweep_action", "action_kind": "harness",
     "role": "drive a browser to screenshot, sweep DOM/assets, and record scroll/click/hover/responsive behavior"},
    {"action": "design_token_extractor_action", "action_kind": "processor",
     "role": "derive a normalized design-token set (color/type/spacing/radius/shadow/motion) from observations"},
    {"action": "component_spec_writer_action", "action_kind": "rubric",
     "role": "write a component spec with EXACT computed CSS, multi-state content, behaviors, responsive variants"},
    {"action": "interaction_model_action", "action_kind": "processor",
     "role": "model states/transitions/validation/keyboard-nav/aria for each component"},
    {"action": "build_understanding_action", "action_kind": "persona",
     "role": "infer stack/framework/architecture/idioms — how the app is built"},
    {"action": "rebuild_planner_action", "action_kind": "persona",
     "role": "plan how it could be (re)built from primitives — alternative implementations, per-section specs"},
    {"action": "primitive_candidate_writer_action", "action_kind": "processor",
     "role": "emit typed candidate primitives per family with typed input/output edges + lift hypotheses"},
    {"action": "visual_diff_qa_action", "action_kind": "rubric",
     "role": "verify generated output vs the original (visual diff, computed-CSS conformance, a11y, responsive)"},
]

# ── USEFUL-by-construction: the disciplines that keep generation useful, not just voluminous ─────────────────
_USEFULNESS_DISCIPLINES: dict[str, str] = {
    "two_axis_admission": "every candidate carries lift_reason + durability_class -> screened by the durable-gap "
                          "harness (lift over bare model AND structural), routed non-destructively by the "
                          "usefulness gate (never discarded, weighted/deprioritized).",
    "source_grounded": "each candidate cites the digested source (app/site/repo) + observation refs -> provenance, "
                       "not hallucination.",
    "typed_edges": "each candidate emits typed input/output edges so it composes (the composition frontier).",
    "negative_space": "UI/UX/frontend exactness (computed CSS, a11y, responsive edges, framework idioms) is a real "
                      "model gap -> lift is likely, not transient.",
    "candidate_only": "born candidate=true/serves_truth=false; digestion is generation, never promotion.",
}

# ── how EVERYTHING the owner provided feeds primitive generation (the unifying answer) ───────────────────────
_CROSS_SOURCE_GENERATION_MAP: dict[str, str] = {
    "app_website_cloner": "apps/sites -> design-token/component/layout/interaction/a11y/framework/rebuild "
                          "primitives + the digestion prompts as Action primitives (THIS pack).",
    "open_vlm_ocr": "document corpora -> parser/table/lookup/rule/workflow primitives "
                    "(document_ingestion_factory_spec + document_extraction_ocr_pack).",
    "harness_engineering": "harness canon -> scaffolding primitives (task-contract, tool-registry, policy-gate, "
                           "budget/kill-switch, report, router) + auto-evolution (generalize graph_autotune).",
    "databricks_pr_benchmark": "our own merged PRs (un-leaked) + held-out tests -> task/verifier primitives; "
                               "context-re-fed-per-turn as the usefulness metric.",
    "esoteric_platform_formats": "obscure platform formats -> deterministic parse/transform primitives "
                                 "(esoteric_platform_primitive_pack).",
    "local_30b_moe": "a generation LANE (DGX Spark) that bypasses the 429 throttle for all of the above.",
}

# ── guardrails (repo law) — digest to GENERATE primitives, never to clone-and-pass-off ───────────────────────
_GUARDRAILS: list[str] = [
    "no_impersonation_or_deceptive_use",
    "no_passing_off_others_design_or_brand_assets",
    "respect_target_terms_of_service_no_scrape_evasion",
    "serve_our_built_out_surfaces_never_rebuild_as_skinny_replacements",
    "digestion_output_is_candidate_primitives_not_a_copied_site",
]


def build_spec() -> dict[str, Any]:
    spec_id = canonical_id(GEN_ID_PREFIX, "spec", str(len(_DIGESTION_PIPELINE)), "v1")
    return {
        "record_type": "app_digestion_primitive_generation_spec",
        "spec_id": spec_id,
        "title": "App/website digestion as a primitive-GENERATION engine (UI/UX modality)",
        "framing": "digestion tools generate primitives: decompose a real app into typed, source-grounded, "
                   "useful-by-construction candidate primitives + the digestion prompts as reusable Actions.",
        "digestion_pipeline": _DIGESTION_PIPELINE,
        "generated_families": {k: {"members": v, "n": len(v)} for k, v in _GENERATED_FAMILIES.items()},
        "digestion_actions": _DIGESTION_ACTIONS,
        "usefulness_disciplines": _USEFULNESS_DISCIPLINES,
        "cross_source_generation_map": _CROSS_SOURCE_GENERATION_MAP,
        "guardrails": _GUARDRAILS,
        "source_refs": SOURCE_REFS,
        "packaged_at": PACKAGED_AT,
        **BOUNDARY,
    }


def build_cards() -> list[dict[str, Any]]:
    """One candidate card per digestion-Action primitive (the reusable prompts/skills) — immediately registerable."""
    cards: list[dict[str, Any]] = []
    stage_by_action = {s["action"]: s for s in _DIGESTION_PIPELINE}
    for act in _DIGESTION_ACTIONS:
        stg = stage_by_action.get(act["action"], {})
        in_edge = stg.get("input_edge", "AppOrSiteSource")
        out_edge = stg.get("output_edge", "PrimitiveCandidateSet")
        cid = canonical_id(GEN_ID_PREFIX, act["action"], act["action_kind"])
        cards.append({
            "record_type": "app_digestion_action_primitive_candidate",
            "kind": "action_primitive",
            "action_kind": act["action_kind"],
            "card_id": cid,
            "primitive_id": cid,
            "title": f"{act['action']} — {act['action_kind']} (app-digestion generation Action)",
            "blackbox": f"{act['role']}. Digestion stage: {stg.get('stage','?')} "
                        f"(cloner phase: {stg.get('cloner_phase','?')}); generates the "
                        f"'{stg.get('generates_family','?')}' primitive family.",
            "blocking_keys": sorted({"app digestion", "primitive generation", "ui ux", act["action"],
                                     act["action_kind"], stg.get("generates_family", "")} - {""}),
            "domains": ["app_digestion", "primitive_generation", "ui_ux", "frontend", act["action_kind"]],
            "candidate": True, "serves_truth": False,
            "visible_edge": f"{in_edge} -> {out_edge}",
            "edge_contract": {"candidate": True, "input_edge": in_edge, "output_edge": out_edge,
                              "input_contract": {"Edge": in_edge}, "output_contract": {"Edge": out_edge}},
            "composition_hints": {"candidate_only": True, "serves_truth": False,
                                  "consumes_edge": in_edge, "produces_edge": out_edge,
                                  "route_signature": f"{in_edge} -> {out_edge}",
                                  "proofs_to_run_before_linking": ["candidate_boundary_gate",
                                                                   "guardrail_check", "two_axis_lift_screen"]},
            "lift_reason": "MODEL_INDEPENDENT_STRUCTURAL: reusable digestion prompt/skill that turns a real app "
                           "into typed, source-grounded UI/UX primitives — a durable generation capability.",
            "source_refs": SOURCE_REFS,
            "packaged_at": PACKAGED_AT,
        })
    return cards


def emit() -> dict[str, Any]:
    spec = build_spec()
    cards = build_cards()
    out_dir = resource(PACK_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / SPEC_FILENAME).write_text(json.dumps(spec, indent=2, sort_keys=True), encoding="utf-8")
    with (out_dir / PACK_FILENAME).open("w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    return {"spec_path": str(out_dir / SPEC_FILENAME), "pack_path": str(out_dir / PACK_FILENAME),
            "n_stages": len(_DIGESTION_PIPELINE), "n_action_cards": len(cards),
            "families": {k: len(v) for k, v in _GENERATED_FAMILIES.items()}}


def self_test() -> bool:
    """Mutation-gated: broken pipeline chain, empty family, non-Action card, dropped guardrail, or missing
    cross-source mapping goes RED."""
    # (1) digestion pipeline chains end-to-end (output_edge[i] == input_edge[i+1]).
    for a, b in zip(_DIGESTION_PIPELINE, _DIGESTION_PIPELINE[1:]):
        assert a["output_edge"] == b["input_edge"], f"pipeline chain break: {a['stage']} -> {b['stage']}"
    assert _DIGESTION_PIPELINE[0]["input_edge"] == "AppOrSiteSource"

    # (2) every stage names a generated family that exists (or 'all') + an action that exists.
    action_names = {a["action"] for a in _DIGESTION_ACTIONS}
    for s in _DIGESTION_PIPELINE:
        assert s["generates_family"] in _GENERATED_FAMILIES or s["generates_family"] == "all"
        assert s["action"] in action_names, f"stage {s['stage']} references unknown action {s['action']}"

    # (3) families non-empty; actions are real Action kinds.
    assert all(_GENERATED_FAMILIES.values()), "an empty generated family"
    valid_kinds = {"persona", "tool", "processor", "harness", "rubric"}
    assert all(a["action_kind"] in valid_kinds for a in _DIGESTION_ACTIONS), "non-Action kind"

    # (4) usefulness discipline present (this is what makes generation USEFUL, not just voluminous).
    for k in ("two_axis_admission", "source_grounded", "typed_edges", "candidate_only"):
        assert k in _USEFULNESS_DISCIPLINES, f"missing usefulness discipline {k}"

    # (5) guardrails present (no impersonation; serve built-out surfaces).
    assert "no_impersonation_or_deceptive_use" in _GUARDRAILS
    assert "serve_our_built_out_surfaces_never_rebuild_as_skinny_replacements" in _GUARDRAILS

    # (6) the cross-source map covers everything the owner provided.
    for k in ("app_website_cloner", "open_vlm_ocr", "harness_engineering", "databricks_pr_benchmark",
              "esoteric_platform_formats"):
        assert k in _CROSS_SOURCE_GENERATION_MAP, f"cross-source map missing {k}"

    # (7) cards: candidate-only Action primitives, deterministic ids.
    cards = build_cards()
    assert len(cards) == len(_DIGESTION_ACTIONS)
    ids = [c["card_id"] for c in cards]
    assert len(set(ids)) == len(ids)
    for c in cards:
        assert c["candidate"] is True and c["serves_truth"] is False and c["kind"] == "action_primitive"
    assert build_spec()["spec_id"] == build_spec()["spec_id"]

    n_members = sum(len(v) for v in _GENERATED_FAMILIES.values())
    print(f"OK app_digestion_primitive_generation_pack self-test: {len(_DIGESTION_PIPELINE)} digestion stages "
          f"(chained), {len(_GENERATED_FAMILIES)} generated families / {n_members} members, "
          f"{len(_DIGESTION_ACTIONS)} Action primitives, {len(_CROSS_SOURCE_GENERATION_MAP)} sources mapped, "
          f"serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="App/website digestion as a primitive-generation engine.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.emit:
        print(json.dumps(emit(), indent=2))
        return
    if args.show:
        print(json.dumps({"spec": build_spec(), "cards": build_cards()}, indent=2, sort_keys=True))
        return
    self_test()


if __name__ == "__main__":
    main()
