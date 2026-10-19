# AGENTS.md — Baltor Shot Composer

Purpose: analyze permitted reference clips as *technique exemplars* and create original 2D/2.5D/3D animation. Do not hallucinate observation of unreachable links. `reference_manifest.json` tracks access states.

1. Review `README.md`, `storyboard.json`, `graph.json` and `operator_catalog.json`.
2. If reference media is provided locally, compute hash and run `analyze_references.py --input ... --out ... --every 1`. Preserve original media outside output packages; never redistribute without rights.
3. Interpret cut/flow/zoom outputs as candidates, confirm with visual contact sheet. Don't claim camera operations were identified if they are ambiguous.
4. Author a new canon in the story bible; avoid copying distinctive characters, music, footage or visual compositions from third parties.
5. Each scene must have `start/end`, frame budget, actor pose, camera curves, effect values, background stack, subtitle/narration cues. Keep hero palette and scarf consistent unless an approved canon change occurs.
6. Build source assets, run tests, render complete MP4, mux original licensed audio, inspect frames from opening/middle/finale, spot-check technical QA, and review for publication readiness.
7. Run `quality_audit.py`, but do not present numeric QA as human aesthetic approval. Do not post without the user's explicit approval of the final asset and copy.
8. When adding 3D Particulate/Articraft/UniMate adapters, truthfully mark GPU availability, inference evidence, and model licensing.
