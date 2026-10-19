# Baltor Motion Foundry — Format, Spatial & Motion Bible v0.2

> **Source discipline:** This document records actual methods built in Baltor and editable editorial proposals. It does not claim the previously linked Stickvival/Facebook/YouTube videos were accessed frame-by-frame. Ideas such as serialized resource tension, level cards, and a cliffhanger came from earlier user-provided planning material and are genre-level inspiration, not verified source-footage observations. Build original fiction and distinct visual identity.

## I. Five complementary grammars

1. **Story grammar:** Hook → establish an explicit need → introduce a measurable constraint → demonstrate a choice/experiment → let a consequence change the state → unresolved ending. A day/level/inventory device works when numbers actually affect the story; don't print arbitrary counters simply to imitate a game.
2. **Motion grammar:** Static visual region + independent subject movement + virtual camera movement + layered depth + foreground occlusion + designed transition. Motion can be informative, emotional, or purely decorative; decorative movement must remain subordinate to readability.
3. **Composition grammar:** One subject focal region, one dominant text hierarchy, optional supporting metadata, controlled negative space, and deliberate borders/panels. The frame is treated as editable geometry, not a background with permanent caption slots.
4. **Rhythm grammar:** Shot → secondary beats → individual element animation → sound event → re-evaluation of readability. The v0.2 film has ten 6.5-second primary shots; `microbeat_plan_50_beats.json` is a *second-pass plan* for five sub-beats each. A separate **40-shot, 400-microbeat, 300-second storyboard** is an *unrendered proposal*.
5. **Evidence grammar:** Separate source observations, measurable programmatic metrics, inferred motion, artistic decisions, and post-publication engagement tests. Only measured facts may be reported as measured.

## II. Working coordinate model

Working raster: **540×960**, 9:16. Final export: **1080×1920** after high-quality upscale, 24fps, 65 seconds. Per-shot layout profile is a configuration, not a hard-coded caption routine.

**Coordinate spaces:** full canvas, platform-oriented safe region, previously placed parent element, and optional authored subject region. Positions are normalized to a coordinate-space rectangle, so x/y/width/height can adapt when that rectangle changes. Base pixel overrides use working-canvas reference pixels.

**Fifteen anchors:** top-left/top-center/top-right; middle-left/center/middle-right; bottom-left/bottom-center/bottom-right; upper-third-left/center/right; lower-third-left/center/right.

**Spacing model:** separate top/right/bottom/left padding; margin planning for each side; horizontal/vertical gaps and line spacing. **Implemented now:** per-element four-sided padding, normalized sizes and offsets, panel gutters, font tracking and line spacing. **Not automatically solved:** flexbox-like content redistribution, full nested grid constraints, baseline snapping across independent elements, actual subtitle word timing.

**Text location candidates:** top editorial masthead, corner eyebrow, central intertitle, left/right rail, lower third, subtitle box, behind-subject negative space, in-scene callout, picture-in-picture label, dashboard metric, side-by-side panel tag, 2×2 camera stamp. Content placement should depend on the visible subject and meaning of the text, not random coordinates.

**Safe regions:** the built-in Reels/Shorts/TikTok profiles are *customizable conservative heuristics only*. Their inset percentages are defined in `layout_engine._screen_safe`. They are not claims about current platform UI; validate previews in actual apps before posting. Full-bleed effects may extend beyond safe areas, but titles, captions, and essential indicators should not.

## III. Ten built compositions

| Preset | Story beat | Spatial language | Signature treatment |
|---|---|---|---|
| `cinematic` | Isolated survivor | Large upper-left type, negative space, subtle timestamp | Film trailer |
| `survival_hud` | Supplies and time | Padded inventory card, three metric columns, thin countdown | Survival game UI |
| `split_decision` | Choose between routes | Two tall parallel image windows, distinct camera crops | Comic/editorial comparison |
| `forensic` | Isolate evidence | Magnified picture-in-picture and leader annotation | Documentary analysis |
| `comic` | Abrupt interruption | Asymmetric coral caption slab, concentric impact lines | Graphic novel |
| `blueprint` | Track unknown signal | Reticles, telemetry labels, compact technical plate | Procedural technical |
| `art_deco` | Suspense intertitle | Centered serif, ornamental horizontal guides | 1930s-inspired title card |
| `dashboard` | Resource forecast | Large percentage, precise status rows, progress scale | Infographic |
| `quadrant` | Multiple points of view | Four independent crops, labeled camera windows | Surveillance montage |
| `minimal_finale` | Cliffhanger | Almost no panels, large declarative type, waveform | Minimal cinematic |

A **new style** must change at least two of: information hierarchy, panel topology, focal region, text geometry, camera, transition grammar, scene depth, framing, or temporal cadence. Recoloring alone is a palette variant, not a new style family.

## IV. Explicit layering order

The current source has semantically named layers. More detailed layering is expressed as an element `z` priority:

```text
00  SKY / WORLD BACKPLATE
05  DISTANT LANDSCAPE AND CITY
08  LANDMARKS AND PROPS
10  CANONICAL CHARACTER
13  FOREGROUND / OCCLUDERS
17  ATMOSPHERE / WEATHER
20  CROP / CAMERA FRAMING
25  UI PANELS / GRIDS
27  CLOSE-UP INSETS
28  IMPACT LINES / RETICLES
35  DECORATION / RULES
38  AUDIO WAVEFORM / SIGNAL VISUAL
40  LARGE TYPE / TITLES
45  LABELS / TAGS
50  PROGRESS AND HUD STATE
```

The engine sorts elements by `z`. In layered design, the visible subject should usually appear in front of broad background accents but behind intentional diegetic effects. Full-screen shades, comic grid overlays, and inset masks are explicit nodes; their placement is not an unexplained filter.

**Implemented blend modes:** normal alpha composite, screen, multiply, add. The local compositor has rounded image crops, progress bars, waveforms and reticles. Per-pixel depth-aware masking, keyframed 3D motion and chromatic effects remain proposed work.

## V. Text and captions

- **Headline:** usually one to three lines, high contrast, enough time to read. Reels working-canvas sample fonts commonly range 26–58 pixels depending on available width. These values are design experiments, not accessibility standards.
- **Eyebrow:** a short scene/level indicator, typically 10–16 pixels in working space, inside an unobtrusive colored pill. Small text is decorative on mobile; essential information needs larger sizes.
- **Narration caption:** not implemented as word-aligned subtitles yet; future versions need high-quality narration timestamps and sentence-aligned highlight events.
- **Counters:** use explicit quantities and units; if the fiction claims dwindling resources, values must remain consistent from one shot to the next.
- **Typographic safety:** engine can shrink/wrap long strings inside a box and report truncation. The browser editor is useful for authoring but is not pixel-identical with the Pillow compositor. Test at actual screen size, not just 4K desktop preview.
- **Avoid padding mistakes:** array `padding:[top,right,bottom,left]`, not CSS shorthand order confusion; a single number applies on all sides, two numbers are vertical/horizontal, an object can specify each side independently.

## VI. Camera, framing and depth

Record a movement type **and** its parameters: horizontal/vertical distance, rate, easing, subject lead, zoom center, zoom ratio, shake window, parallax multiplier, foreground transition timing, and intent. The current source provides background parallax plus a handful of deterministic camera modes inherited from v0.1. It does not identify true movement from any external source.

Useful controls to add next: anchored rack focus for an inset, 2.5D depth cards, spline path cameras, match-on-action cuts, camera dead zone around a moving actor, subject-aware title repositioning, and orientation-preserving rotations.

## VII. Sound, pacing and causality

- Original ambient bed, sound events and accents are rendered and mixed with FFmpeg.
- All ten shot boundaries carry intentional edit rhythm; the final video includes generated knocks, chimes or whooshes on appropriate beats.
- **No narration is present in the delivered MP4.** `narration_cue` fields specify future recording/editing intent and must not be confused with spoken audio.
- A natural neural narrator should be separately tested, licensed/approved, loudness-normalized, and forced-aligned to word-level captions. Avoid robotic offline voices merely to fill the gap.

## VIII. Reverse engineering with limited evidence

For owned or otherwise authorized MP4s:

1. Hash/record the local source, fps, codec, source license and original URLs.
2. Run the existing `analyze_references.py --every 1` to measure frame differences and estimate candidate affine transforms and shot boundaries.
3. Run `spatial_v02/analyze_spatial_video.py --stride 1` for edge/contrast/motion activity in 3×3 zones and potential low-activity caption areas.
4. Review actual frames manually and annotate **observed** pan/zoom, titles, masks, layers and cuts; don't infer factual visual methods solely from narrator transcripts or text descriptions.
5. Write a shot recipe independent of the original visual/media identity. Recreate common techniques on original art, not protected footage/characters.
6. Score against original creative targets, not against pixel-level copyrighted source reconstruction. Preserve decision logs, QA and rights metadata.

## IX. Quality gates

**Technical gates run:** JSON shape/time validation, DAG topological validation, 25 geometry/render tests, 30 static layout checks, actual media probe, 14 encoded-video sample frames, and a 1,560-row frame spatial audit. The 65s output passes the implemented technical checks.

**Not run/unknown:** Accessibility review, empirical on-platform safe-zone check, third-party frame-by-frame matching, licensed music clearance beyond original synthesized material, narrators, compression performance after Facebook upload, long-term character canon consistency, human-subject occlusion detection, actual user engagement.

## X. Future editor and DAG expansions

The **180 dimensions in `layouts.json` are a broad catalog**, not 180 independently tested controls. Candidate improvements include automated safe-position search constrained by the actor bounding box, nested stack/grid layouts, font/caption contrast testing, beat-level dynamic text, panel track matte animation, sound-to-motion synchronization, semantic layer naming, 3D articulated inputs, map overlays, shader/particle layers, and genuine browser timeline previews that match authoritative renders.

The **300-second unrendered feature storyboard** has 40 named shots and 400 fine-grained time ranges. It specifies exactly when a supporting camera, parallax, character, prop, inset, text, FX, audio, or transition action would occur. Rendering it requires implementing and reviewing that second-pass microbeat pipeline. The current 65-second video is the tested prototype.
