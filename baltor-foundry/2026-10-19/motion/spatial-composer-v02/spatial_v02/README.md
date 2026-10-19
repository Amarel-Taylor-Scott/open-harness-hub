# Baltor Spatial Studio v0.2 — Original Video Composition Factory

**Status:** Working local prototype, **not** verified frame-by-frame reverse engineering of Stickvival or the YouTube/Facebook references. The 65-second film demonstrates original animation plus reusable generalized editing techniques. All title, image, music, and character assets used in this delivery were authored procedurally for Baltor in the preceding workflow.

## Open these first

- `outputs/baltor_spatial_layout_study_65s_FINAL.mp4` — 65-second 1080×1920 vertical MP4 with AAC ambient audio.
- `outputs/spatial_10_style_contact_sheet.jpg` — the ten genuinely different composition arrangements.
- `Baltor_Spatial_Studio_Editor.html` — **offline interactive editor** with canvas drag/selection, safe-area guides, editable position, padding, text, z-index, shapes, styles and JSON export. All assets are embedded; no internet required. Browser preview differs slightly from authoritative Pillow rendering.
- `layouts.json` — authoritative 10 templates, timelines, and 180-field dimensional *catalog*.
- `spatial_graph.json` — 36-node dependency graph with honest implementation status for each node.
- `outputs/spatial_analysis/frame_spatial_metrics.csv` — per-frame spatial measurements for all 1,560 frames.
- `outputs/spatial_analysis/per_shot_placement_sheet.jpg` — 10 shots and **heuristic** suggestions for less active caption regions. These are not automatic evidence of safe or readable placement.

## What has been implemented and tested

**10 layouts:** cinematic title, survival inventory, horizontal editorial split, documentary inset, graphic novel, annotated blueprint, art-deco title, analytics dashboard, four-view montage, minimalist waveform finale.

**Spatial system:** 15 anchor presets, 4-edge padding, parent-relative placement, relative/pixel width and height, explicit safe-area profiles, text wrapping and font-size fitting, text stroke/shadows, layer z-order, element timing (fade and slide), transparent panels, compositing with normal/screen/multiply/add, source-image crops, 1×2 and 2×2 grids, reticles, progress indicators, waveforms, and JSON-editable properties.

**Verified:** 25 spatial unit tests passing; all ten layouts generated; 30 sampled layout inspections found no program-detectable safe-zone errors or overlapping text boxes; source MP4 has 1,560 H.264 frames at 24 FPS, 1080×1920, AAC audio and 65-second duration; spatial analyzer generated per-frame metrics. **These automated checks cannot judge storytelling, actual app UI, aesthetic quality, or text overlapping dynamic characters.**

**Catalog ≠ executable:** `layouts.json` includes 180 **candidate dimensions** organized into 12 research/design families. Only the subset described above is currently operational. `spatial_graph.json` explicitly marks implemented, prototype, planned, and human-required stages. `future_style_ideas_50.json` contains 50 backlog ideas, not 50 rendered templates.

## Design-time architecture

```text
Storyboard / rights / original plates
          ├── Camera → Background → Character → Parallax/Effects
          └── Canvas → Safe Areas → Anchored Boxes → Four-Edge Padding
                       → Text Wrapping & Fitting
                       → Shape/Image/Panel/Type Layers
                       → Z-Sort + Transparency + Blend
                       → RGB Frames → H264 Video
Audio Bed + Time-aligned Cues ──────────────┘
                         ↓
                     Final MP4
                         ↓
               Frame-by-Frame Spatial Audit
                         ↓
                 Candidate Caption Areas
```

## Build from the source archive

Requires: Python 3.10+, Pillow, numpy, scipy, soundfile, opencv-python, FFmpeg/ffprobe, and optionally Graphviz + Chromium (to test the browser editor).

From the archive's `stick_composer/spatial_v02/` folder:

```bash
python -m unittest discover -s tests -v
python composer_v02.py --preview 24.0 --out outputs/my_frame.png
python composer_v02.py --contact-sheet --out outputs/my_contact_sheet.jpg
python build_editor.py
python composer_v02.py --out outputs/video_only.mp4
python ../sound_design.py --out outputs/original_atmosphere.wav
python make_spatial_audio.py --out outputs/spatial_original_audio.wav
ffmpeg -y -i outputs/video_only.mp4 -i outputs/spatial_original_audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest outputs/final.mp4
python analyze_spatial_video.py --input outputs/final.mp4 --out outputs/analysis --stride 1 --timeline layouts.json
```

**Important:** The parent folder must contain `composer.py`, `storyboard.json`, `graph.json`, `sound_design.py` and the original `assets/` image plates from the source package. `make_spatial_audio.py` loads the original music bed if it exists under `../outputs/original_atmosphere.wav`. If no bed exists, the code produces a sparser synthesized cue-only track rather than silently downloading music. For reproduction of the packaged soundtrack, generate the bed using the parent-level `sound_design.py` first, as shown above. `outputs/` is resolved relative to the script's own module directory for most v0.2 commands.

## Editable placement model

```json
{
  "id":"chapter_label",
  "kind":"text",
  "layer":"typography",
  "z":40,
  "box":{"space":"safe", "anchor":"top_left", "dx":0.02, "dy":0.05, "w":0.75, "h":0.12},
  "padding":{"top":8,"right":18,"bottom":6,"left":14},
  "text":"DAY 04 / THE LAST SIGNAL",
  "font":"bold", "font_size":30, "min_font_size":14,
  "max_lines":2, "align":"left", "valign":"center",
  "color":"#F4F3E6", "background":true,
  "fill":"#081521D8", "radius":12,
  "start":0, "end":6.5, "in":0.2, "out":0.3,
  "enter":"slide_up", "opacity":1
}
```

`dx`, `dy`, `w`, `h` are fractions of the parent coordinate rectangle. Padding is **top, right, bottom, left** in working-canvas pixels (scaled to other canvas sizes). The `anchor` controls which point of the child box attaches to which point of its safe/canvas/parent space. Supported anchor presets: top/middle/bottom × left/center/right, plus upper-third and lower-third × left/center/right. `w_px`/`h_px` are optional alternative size overrides. Child elements can reference a previously resolved parent's `id` as their coordinate space.

When a node requests `must_safe=true` (default), the QA checks its rectangular bounds are inside the selected **heuristic** platform safe zone. Elements such as full-screen underlays explicitly set `must_safe=false`. No selected platform zone is certified by Meta, Google or TikTok; verify final UI occlusion on-device.

## Editor directions

1. Open `Baltor_Spatial_Studio_Editor.html` in a normal web browser (local file; offline).
2. Pick one of ten layouts, and optionally switch between Reels, Shorts, TikTok or full-canvas guide presets.
3. Click a component in the preview or the ordered layers list.
4. Edit x/y/w/h, 15-point anchor, padding on four sides, font family, color, z-order, opacity and background.
5. Drag the selection box to refine placement. Export the JSON or the approximate preview PNG.
6. Transfer exported `elements` into the relevant layout in `layouts.json`, then render with the Python pipeline for authoritative output. **The browser export is layout-level JSON, not a complete ready-to-render storyboard** until merged into the source configuration.

## Reference media analysis

Only use reference clips you have rights to download/inspect. The previous work could not access the user-linked social video streams. Their shared links and earlier chat summaries are useful research leads, **not verified frame observations**.

```bash
python ../analyze_references.py --input /path/to/permitted_reference.mp4 --out outputs/ref_01 --every 1
python analyze_spatial_video.py --input /path/to/permitted_reference.mp4 --out outputs/ref_01/spatial --stride 1
```

The analyzer measures edge energy, brightness/contrast variation and pixel changes in a 3×3 spatial grid; it proposes lower-activity text regions. **It does not perform OCR, reverse-engineer original source layers, identify character faces, prove a zoom, or infer exact shot construction.** Confirm candidates by viewing the actual footage.

## Source and use policies

Do not redistribute third-party reference videos, protected character art, music or narration without appropriate rights. Learn generalized pacing, composition and effects rather than cloning any particular creator's distinctive story/characters. This research and all original output are unpublished. Final Facebook/YouTube publication and accompanying copy require explicit approval.
