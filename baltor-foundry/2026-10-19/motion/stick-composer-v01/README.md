# Baltor 🎬 Shot Composer — Stick-Animation / 2D-to-Video DAG

**Status: working original-animation prototype; NOT a frame-by-frame reconstruction of the inaccessible Facebook/YouTube references.**

## Deliverables

- `outputs/the_last_signal_70s_FINAL.mp4` — **70 seconds, 1080×1920 delivery, 24 FPS**, H.264/AAC, original procedural graphics and atmospheric SFX. Rendered internally at 540×960 and upscaled with Lanczos; not native 1080 vector sampling.
- `outputs/original_story_contact_sheet.jpg` — fourteen frames from fourteen moments, including text, 1×2 panel, effects and staging.
- `storyboard.json` — fifteen timed shots with **45 supporting beat descriptions**, locked continuity, title and effects.
- `graph.json` — **19-node, dependency-validated shot-composer DAG**; selected operations are exercised per frame, encode/mux/QA run as post stages.
- `assets/*.png` — seven original transparent or RGBA 2D image plates.
- `operator_catalog.json` — ~150 pipeline building blocks, each marked implemented/basic vs proposed/unimplemented.
- `analyze_references.py` — native-frame-step optical flow, cut candidates, per-frame metrics, thumbnails, provenance, JSON/Markdown report.
- `reference_manifest.json` — original 13 Facebook/YouTube references, all marked **not accessible**; no false attribution.
- `download_references.py` — optional `yt-dlp` adapter for locally permitted/publicly downloadable YouTube references. Not executed here.
- `quality_audit.py`, `tests/` — spot video checks, 9 unit tests, deterministic renderer assertions.

## Quickstart

```bash
python -m pip install pillow numpy scipy soundfile opencv-python
# System requirements: ffmpeg / ffprobe on PATH
cd baltor_motion_foundry/stick_composer
python build_assets.py
python -m unittest discover -s tests -v
python sound_design.py --out outputs/original_atmosphere.wav
python composer.py --preview 11.8 --layers --out outputs/frame_12.png
python composer.py --out outputs/video_only.mp4 --duration 70 --fps 24
ffmpeg -y -i outputs/video_only.mp4 -i outputs/original_atmosphere.wav \
  -c:v copy -c:a aac -b:a 144k -shortest outputs/final.mp4
python quality_audit.py
```

To change content: edit `storyboard.json`; to replace the plates, edit/rebuild `assets/*.png`; to add operations, add a node in `graph.json` and implement an associated step in `composer.py`.

## Optional reference analysis: exact frames

Bring your own local video file that you're entitled to analyze; this environment could not access the supplied videos.

```bash
# Optionally, on your own Internet-connected machine, with proper authorization:
python -m pip install yt-dlp
python download_references.py --id yt-07qXw53UcQg --authorized

# Frame-by-frame analysis (every=1):
python analyze_references.py --input inputs/yt-07qXw53UcQg.mp4 \
  --out outputs/ref-07qXw53UcQg --every 1

# Outputs: every analyzed source-frame metric, contact sheet, edit candidates and an analysis report.
```

`yt-dlp` filenames depend on original stream/container availability. Use the actual downloaded filename. The analyzer does not claim to identify object geometry or copyrighted characters; candidate camera/zoom motion can be contaminated by moving subjects. Review frame and cut classifications manually.

## Two independent DAGs

### A. Reference understanding (unrun on user URLs)

`rights/provenance → acquisition → decode → every-frame optical flow & image difference → scene cuts → motion taxonomy → color/contrast → shot timing → human interpretation → parameterized edit recipe`

Frame record schema: `frame, second, pixel_difference, hist_correlation, candidate_dx, candidate_dy, candidate_zoom, inlier_confidence, cut_candidate`. The status is *candidate* because foreground motion can confuse global flow.

### B. Original content production (tested)

`storyline → 15-shot storyboard → 7 2D plates → parallax → landmarks → authored stick rig → foreground occlusion → effects → camera/zoom → split/PIP → transition → typography/borders → FFmpeg video → atmospheric audio → mux → QA`

The part that matters: **the reference-media analysis results are parameter suggestions only, never footage reused in the published output.** Every clip stays attributable to its creator and outside the generated-media branch unless licensed.

## Scene-level parameterization

Each `storyboard.json` shot includes `start`, `end`, `mode`, `world_x`, `actor`, `fx`, `title`, `line`, and `beats`. Implemented camera modes:

- `establish`: slow panoramic pan + subtle push.
- `follow`: steady target tracking and fixed camera distance.
- `push`: dramatic center-cropped enlargement, plus PIP close-up.
- `cover`: subject hiding behind foreground occlusion layers.
- `split`: cyan/coral 1×2 decision comparison with two camera treatments.
- `reveal`: pan toward a radio landmark and expanding cyan concentric rings.
- `whip`: accelerated pan, shake/transition flash, alert red border.
- `chase`: faster tracked movement and ambient rain.
- `close`: magnified detail frame plus subtle knock impact.
- `flare`: authored parabolic object trajectory with trails and glow.
- `pull`: reverse zoom and anticipation beat.
- `end`: final suspense beat and continuation invitation.

### Why this matters

The whole series can retain consistent character, map, lighting and palette while changing the shot language. Titles and story beats are variable; CSS/PNG-like visual layers and pose data are reusable. This is the nucleus of a **general media-DAG harness skill**, not a monolithic video-generation prompt.

## Extension priorities

1. **Reference source intake:** Upload locally downloaded, authorized MP4s from the supplied list. Run analyzer at every frame and manually annotate five representative scenes. This is the missing prerequisite for genuine reference-specific reverse engineering.
2. **Multi-depth / better 2D rigs:** SVG cutout figures, head/limb/body independent layers, IK, contact-aware feet, secondary cloth/hair, effect occlusion and multiple actors.
3. **Cinema editor:** Browser timeline with nodes/keyframes, view waveforms, curve editor, proxy previews. Recommend **Motion Canvas** (TypeScript generator/editor) or **Remotion** (React compositing) adapters; evaluate their licensing/rights for commercial deployment before choosing.
4. **Add 2.5D and 3D:** Depth maps, 3D camera projection, Blender Grease Pencil, Three.js, Godot, Particulate-rigged GLBs imported as separate motion objects; don't claim these are implemented in this 2D demo.
5. **Audio:** Human-recorded or natural neural TTS with alignment to shot cues; avoid robotic offline voices; side-chain music ducking; lip sync for dialogue only when appropriate.
6. **Editorial QA:** Human reviews of pacing, scene comprehension, IP originality, character continuity, audio comfort, legibility and mobile safe zones.
7. **Variant search:** Generate 10+ variants per creative with different pacing, POV, layouts, borders, impacts, light and caption density. Keep continuity fixed and rank on objective QA plus viewer preference—not invented engagement metrics.
8. **Library integration:** Package nodes as `SKILL.md`, reusable `AGENTS.md`, presets, reference-rights metadata and source manifest; index at baltor.ai and related components.

## Relevant external projects (not installed/tested here)

- [Motion Canvas](https://github.com/motion-canvas/motion-canvas) — TypeScript generator-based 2D animation + preview editor.
- [Remotion](https://www.remotion.dev/docs/composition) — React video compositions/sequences; check commercial licensing.
- [PySceneDetect](https://www.scenedetect.com/docs/cli.html) — more sophisticated cut detection than this prototype's histogram heuristic.
- [Stick Nodes](https://play.google.com/store/apps/details?id=org.fortheloss.sticknodes) — examples of virtual-camera pan/zoom and reusable 2D animation clips.
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) — `zoompan`, `xfade`, `overlay`, `crop`, `scale` and more.

## Ethics, permissions and release state

All delivered visuals and audio are newly authored procedural assets. Nothing from the Facebook or YouTube clips is embedded. The prototype's staging draws on common genre conventions; it is **not represented as a perfect recreation** of any identifiable creator's video. Avoid republishing copyrighted reference frames or soundtracks without rights. No videos have been published to social accounts. **Final publication requires explicit approval of the asset and accompanying post copy.**
