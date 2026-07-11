# ADR 0009 — Media/creative primitives: a candidate branch, Fable-as-compiler, not a vertical

## Status
Accepted (2026-07-04) as a **pattern adoption + candidate branch**. Media as a *revenue vertical* is
**deferred** under depth-before-breadth.

## Context
Owner fed a detailed proposal: use **Fable 5 as a creative COMPILER** (scene/shot/route planner + code
generator + vision critic), NOT a pixel generator, for image / 3D / video / music-sync media — pattern
**"Fable compiles · engines render · receipts prove · registry remembers."** It includes ~20 media primitive
families, edge cards in our exact primitive-group schema (`input_edge`/`output_edge`/`blackbox`/
`runtime_targets`/`effects`/`proof_requirements`/`candidate`/`serves_truth`), a multi-stage compile route, and
a visual/media benchmark set. Assessed reuse-first + depth-before-breadth.

## Decision
1. **The pattern IS our compiled-route thesis** — "one-time LLM compilation → deterministic execution →
   mandatory proof-gate → remember" = the CapabilityTask descent + the generic executor + candidate/truth +
   the registry. **Fable-as-compiler-not-generator is correct and aligns with `serves_truth = false`:** the
   model plans and emits evidence; engines execute; receipts verify. Adopt the framing.
2. **The generic executor already supports media — no new architecture.** Its pluggable `runner` port + the
   `runtime` field ARE the "engines render" layer: a media primitive is just a primitive whose runner is
   Blender / ComfyUI / FFmpeg / Manim / Three.js instead of Python. The `proof_requirements`
   (`nonblank_frame_check`, `beat_keyframe_alignment_error`, `duration_match`, …) map onto our receipt/proof
   system + the two-axis lift gate. The edge cards fit the store's model directly.
3. **Adopt media as a CANDIDATE branch of the primitive universe** (`candidate = true, serves_truth = false`)
   — consistent with the factory generating broadly. Captured families (candidate backlog):
   `creative_brief_to_scene_spec` · `storyboard_to_shot_list` · `scene_spec_to_blender_script` ·
   `scene_spec_to_manim_scene` · `scene_spec_to_webgpu_shader_pipeline` · `audio_track_to_beat_map` ·
   `beat_map_to_keyframes` · `music_sections_to_scene_transitions` · `prompt_brief_to_image_prompt_pack` ·
   `prompt_pack_to_comfyui_workflow` · `image_candidate_set_to_ranked_selection` · `frame_sequence_to_video` ·
   `render_artifact_to_visual_quality_receipt` · `generated_media_to_license_and_provenance_receipt` (+ ~6 more).
4. **DEPTH-BEFORE-BREADTH holds — media is NOT a revenue vertical now.** The proven vertical stays
   sanctions / healthcare-admin (foundational-law filter #4). Media primitives are candidate routes in the
   factory backlog, promoted only if a paying customer pulls them. A candidate branch is not breadth-chasing;
   a media *product* would be, and that's the failure mode we don't repeat.

## Consequences
A large, validated candidate branch that the executor / proof / registry generalize to unchanged; a clear,
correct role for Fable 5 (compiler + vision critic, never the only runtime or the pixel generator); no vertical
commitment. The benchmark set (`formula_to_manim_animation`, `music_to_beat_synced_visualizer`, …) is a good
future eval harness for the branch.

## Enforcement / links
The compiled-route thesis; the generic executor (ADR 0007); the two-axis lift gate; the candidate/truth
boundary; depth-before-breadth (`architecture/substrate_layers.json` → foundational_law filter #4).
