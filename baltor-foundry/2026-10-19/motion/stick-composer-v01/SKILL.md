---
name: baltor-motion-shot-composer
summary: Original stick-animation, 2D image-to-video, parallax, shot-camera, effects, frame-analysis and MP4 production.
---

Use this local harness skill to create an **original** 9:16 procedural animated short from `storyboard.json` + image plates, or to analyze a locally available authorized reference video.

## Inputs
- Storyboard shot JSON, 2D image plate PNGs or authored vectors, optional original/local audio.
- Reference local MP4 only if available and lawful to analyze. Don't infer unavailable content from a link.

## Output
- Completed H.264/AAC MP4 (not screenshots/ZIP alone), contact sheet, DAG JSON, QA report, provenance manifest.

## Execution
Run `build_assets.py`, `sound_design.py`, `composer.py`, and `quality_audit.py`. For reference research run `analyze_references.py --every 1` and human verification of keyframes.

## Grounding
All video content is new: do not reuse unlicensed footage or music; do not claim specific shots in inaccessible videos were observed.
