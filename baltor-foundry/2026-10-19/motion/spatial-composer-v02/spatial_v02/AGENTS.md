# AGENTS.md — Baltor Spatial Studio v0.2

Purpose: turn original or authorized 2D/2.5D/3D material into reusable shot recipes, analyze candidate spatial patterns, and produce completed MP4s with rigorous compositional and provenance checks.

## Inputs and source discipline

1. Read `README.md`, `layouts.json`, `spatial_graph.json`, and `series_bible_v02.json` before authoring modifications.
2. Treat links and chat summaries about Stickvival, YouTube Shorts, or other creators as leads rather than proof of observed frame events. Do not claim to have downloaded or frame-analyzed unprovided media.
3. For approved local reference clips, preserve the hash, duration, licensing note, observation-vs-inference distinction, and high-level editing-technique notes. Do not include copied third-party artwork or sound in output videos without rights.
4. The existing `composer.py` and `assets/` implement an original survivor illustration and deterministic animation; maintain `beacon-01` character design and world topology unless canon is explicitly revised.

## Build / component protocol

1. Select a shot goal and a spatial layout preset. Reuse nodes from the validated `spatial_graph.json` rather than hard-coding offsets into a new renderer.
2. Specify exact duration, shot start/end, local text/narration/subtitle timing, subject position, target aspect ratio, frame rate, fallback fonts and deterministic seeds.
3. Use the `Engine` normalized coordinate system with a 15-position anchor; specify all four padding edges and semantic layers. Allow a single layout preset to be used on multiple shots.
4. Use at least three timing beats per shot, including secondary motion/camera/audio activity. The `microbeat_plan_50_beats.json` supplies **planned** beats, not pre-existing implemented animations.
5. Keep titles inside a configurable safe zone; avoid covering the character's face/scarf, interactive elements, footage evidence, and essential scene action. Do not equate rectangular safe-zone checks with semantic subject avoidance.
6. Style families must differ in actual composition (layout, number of panels, camera, type hierarchy, information density, rhythm), not merely change the palette.
7. Build/originalize visual assets. Run original scene generation → v0.2 spatial overlay → audio → FFmpeg encoding → programmatic QA.
8. For reference measurements run `analyze_spatial_video.py --stride 1` and preserve all measured-frame CSV rows. Label the resulting rectangles as heuristics, not discovered true text positions.
9. Run `python -m unittest discover -s tests -v`, inspect the ten-style contact sheet, watch the complete MP4 and make sure the audio is not overpowering. Test at the actual publishing platform resolution and UI overlay.
10. No social-media publishing without the user's explicit approval of the exact final video and post copy.

## Component output contract

Each node should carry: `op`, `inputs`, `outputs`, `execution_mode` (frame/shot/batch), `config_schema`, `determinism`, `seed`, `resource_limit`, `source_rights`, `cache_key`, `qa_assertions`, `failure_fallback`, and `implementation_status`. `spatial_graph.json` is currently a *validated declarative DAG*, not a universal graph executor; source code dispatches its implemented operations. Planned nodes remain labeled planned until implemented and tested.

## Prioritized next upgrades

- Text occupancy and subject-tracking masks with occlusion avoidance.
- Genuine motion curves and frame-level captions aligned with approved neural narration.
- Actual permitted reference-frame labeling and manual confirmation.
- A full responsive rendering path for landscape/square (not simply cropping 9:16 source plates).
- True hierarchy clips, shapes, 3D-to-2D articulated motion adapters, and live browser preview parity with final PIL render.
- Platform-specific previews and empirical A/B audience tests after manual publishing approval.
