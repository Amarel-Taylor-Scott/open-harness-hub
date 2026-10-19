# Particulate → Video Factory for Baltor.ai

**Research integration plan + working proof of concept, 2026-10-18.**

## Status and honesty labels

- ✅ **Working:** 42-second 720×1280 H.264/AAC MP4. Procedural VTK 3D lamp, authored joint hierarchy, actual frame-by-frame motion, camera orbit, captions, part colors, synth soundtrack, progressive stages. `particulate_motion_demo.py` and `particulate_motion_soundtrack.py` reproduce it with Python, VTK, Pillow, NumPy, SciPy and FFmpeg. The render was produced in shorter segments and concatenated for runtime stability.
- 🟡 **Not yet integrated:** The *Particulate* checkpoint has **not** been executed. This proof of concept uses hand-defined geometry and motion, not ML-inferred segmentation or joints. The on-video footer explicitly says so.
- 🟡 **Not yet integrated:** Instruct-Particulate conditioning, Articraft SDK, Blender and browser engines. These are proposed adapters, not tested components in this delivery.
- ✅ **Verified upstream:** Particulate inference exports `animated_textured*.glb`, `mesh_parts_with_axes*.glb`, and can optionally export URDF/MJCF. The official `infer.py` checks `torch.cuda.is_available()` and requires CUDA.

## Primary sources

- Particulate: https://github.com/RuiningLi/particulate
- Peer-reviewed CVPR 2026 paper: https://openaccess.thecvf.com/content/CVPR2026/html/Li_Particulate_Feed-Forward_3D_Object_Articulation_CVPR_2026_paper.html
- Pretrained model card: https://huggingface.co/rayli/Particulate (model weights CC-BY-4.0, code Apache-2.0 per model card; review individual dependent assets)
- Hosted demo: https://huggingface.co/spaces/rayli/particulate
- Instruct-Particulate: https://instruct-particulate.github.io/ (conditional kinematic specifications, June 2026 report)
- Articraft (maintained): https://github.com/articraftresearch/Articraft (agent-authored 3D assemblies with checks and USDZ output)

## Proposed architecture

Input source
→ rights/provenance and mesh validation
→ mesh preprocessing (up-axis, normalization, geometry quality)
→ articulation adapter [Particulate | Instruct-Particulate | Articraft | known rig | manual authoring]
→ canonical rigid-part / joint / limits interchange representation
→ joint graph validation, joint-limit tests, contact/collision checks
→ motion recipe sampler (loop, reciprocation, staged reveal, exploded view, assembly, physics)
→ storyboard planner (single hero + continuity bible + subsidiary support shots)
→ renderer [Blender | Three.js | Babylon.js | Godot | VTK]
→ video compositor (background full video, blur/translucency layer, inset working area, moving border, text, PIP, VFX)
→ soundtrack/narration/subtitles
→ automated QA [geometry, motion, cropping, captions, scene consistency, audio]
→ human approval of final video and post copy
→ MP4 + manifest + source provenance

### Canonical interchange schema example

```json
{
  "schema": "baltor.articulated_asset.v1",
  "asset_id": "sha256:...",
  "source": {"asset_uri": "asset.glb", "license": "REVIEW_REQUIRED", "sha256": "..."},
  "articulation": {
    "provider": "particulate|instruct-particulate|articraft|manual",
    "checkpoint_id": null,
    "inference_complete": false,
    "parts": [{"id": "base", "mesh": "base.glb", "confidence": null}],
    "joints": [{"id": "hinge_a", "type": "revolute", "parent": "base", "child": "arm_a", "axis": [0, 1, 0], "limits_radians": [-0.3, 1.7]}],
    "validation": {"valid_graph": null, "collision_free": null, "joint_limit_ok": null}
  },
  "animation": {"fps": 24, "seconds": 60, "loop_policy": "seamless"},
  "render": {"targets": [[1080, 1920], [1080, 1080], [1920, 1080]], "formats": ["mp4"]},
  "provenance_label": "research-inference|procedural-illustration|simulated-example"
}
```

## 60-second storyboard: "This 3D Object Learns to Move"

Each primary shot can contain independently scheduled secondaries, not just a single still per panel. Text lengths assume 1080×1920 framing with 5–8% safe margins.

| Shot | Time | Main shot / camera | Secondary shots and layers | On-screen headline | Proposed narration | Motion constraints / QA |
|---|---|---|---|---|---|---|
| 01 | 0–3 s | Macro orbit of static chair/lamp | film grain; animated frame; background loop | ONE STATIC MESH | "This is just a 3D mesh." | Orbit stable; readable first frame |
| 02 | 3–6 s | Show mesh wireframe, rotate 35° | wireframe inset; triangle count | BUT CAN IT MOVE? | "What if it could move?" | No rig inference claims yet |
| 03 | 6–9 s | Colorize likely independent regions | part ID overlays; flicker scan | FIND THE PARTS | "First, we need to find its parts." | Colors match labels |
| 04 | 9–12 s | Exploded-view animation | shadows; tiny particle trails | SEGMENT THE OBJECT | "Separate the components that should move." | No detached pieces left at end |
| 05 | 12–15 s | Show hierarchy tree in PIP | node graph; animated connector lines | BUILD A MOTION GRAPH | "Then discover how they connect." | Valid parent-child tree |
| 06 | 15–18 s | Highlight revolute hinge | animated arc; rotation arrow | REVOLUTE JOINT | "Some joints rotate." | Joint axis correct |
| 07 | 18–21 s | Demonstrate telescoping/sliding component | long-axis arrow; distance tracker | PRISMATIC JOINT | "Others slide along an axis." | Respect linear limits |
| 08 | 21–24 s | Freeze frame and show bound values | timeline ruler; red endstops | JOINT LIMITS | "And each joint has limits." | Do not exceed travel limits |
| 09 | 24–27 s | Reassemble components | particle trails; impact flashes | REASSEMBLE | "Now put it back together." | Parts return to shared coordinate space |
| 10 | 27–30 s | First coherent motion cycle | camera dolly-in; path line | IT MOVES | "The object can finally animate." | Test all frames for collisions |
| 11 | 30–33 s | Motion from reverse angle | second camera PIP; silhouette | VIEW 01 / 02 | "And move from every angle." | Stable scale and lighting |
| 12 | 33–36 s | Slow mechanical orbit | depth-of-field look; speculars | REAL 3D MOTION | "Not just a video trick." | Motion comes from joint animation |
| 13 | 36–39 s | Move on a music beat | waveform; reactive bloom | SOUND-SYNCHRONIZED | "Even synchronized to music." | Beat marker sync ±2 frames |
| 14 | 39–42 s | Three-shot cinematic montage | inset duplicate cameras | ONE RIG, MANY SHOTS | "One rig becomes many shots." | All views same canonical asset |
| 15 | 42–45 s | Export animated 3D object | icon columns | GLB / URDF / MJCF | "Export it for animation or simulation." | Formats only when actually exported |
| 16 | 45–48 s | Blender cinematic compositing example | scene layer diagram | LIGHTS / FX / CAMERA | "Then add lighting, effects and cinematography." | Check render metadata |
| 17 | 48–51 s | 1×1 / 9×16 / 16×9 simultaneous | crop safe frame boxes | EVERY FORMAT | "Deliver in every format." | No text cropping |
| 18 | 51–54 s | Animated variations gallery | 2×2 grid; branded border | REUSE THE COMPONENTS | "Without rebuilding the rig." | Cache motion curves |
| 19 | 54–57 s | Before/after on one screen | split view | FROM STATIC TO CINEMATIC | "From static mesh to moving story." | Original/correct attribution |
| 20 | 57–60 s | Final hero mechanical loop | engagement question; brand small footer | WHAT SHOULD MOVE NEXT? | "What would you animate next?" | Leave CTA visible ≥2 seconds |

## Repeatable content recipes (suggestions, not benchmarked)

1. Ten common objects that were previously static, now articulated.
2. The most satisfying drawer mechanisms in slow motion.
3. Fictional transforming robots assembled from constrained rigid parts.
4. AI-generated chairs folding and unfolding (QA realism).
5. Automatic exploded technical illustrations.
6. Satisfying mechanical ASMR synchronized to original soundtracks.
7. 3D animation before and after adding explicit kinematic rules.
8. Particulate vs. Instruct-Particulate on held-out object classes (with objective tests).
9. Blender vs. Three.js render style comparisons from identical joint keyframes.
10. Animated product instruction sheets.
11. Interactive browser viewers with movable joints; record interaction into MP4.
12. Character / creature control experiments: only if rigid articulation is appropriate; skin deformation and biological locomotion require other rigs or models.

## Actual inference integration (not run in current environment)

```bash
# GPU host with compatible CUDA, Python 3.10 and PyTorch environment.
git clone https://github.com/RuiningLi/particulate.git
cd particulate
conda create -n particulate python=3.10
conda activate particulate
pip install -r requirements.txt
python infer.py --input_mesh ./hunyuan3d-examples/foldingchair.glb \
  --output_dir ./renders/chair \
  --animation_frames 120 \
  --export_urdf --export_mjcf
# Inspect ./renders/chair/animated_textured*.glb for an actual inferred, animated rig.
```

The `--up_dir` parameter must reflect the original mesh coordinate convention; sample defaults are not universal. Use the predicted articulation GLB and exported metadata to create multiple motion curves. Do not equate predicted kinematics with physically valid motion. Check joint axes, hierarchy, collisions, detachments, stability, and plausibility.

## Render/repro prototype (tested here)

```bash
# Demo requires: Python packages vtk numpy pillow scipy and ffmpeg.
python particulate_motion_demo.py --out segment1.mp4 --start 0 --end 14
python particulate_motion_demo.py --out segment2.mp4 --start 14 --end 28
python particulate_motion_demo.py --out segment3.mp4 --start 28 --end 42
printf "file 'segment1.mp4'\nfile 'segment2.mp4'\nfile 'segment3.mp4'\n" > segments.txt
ffmpeg -f concat -safe 0 -i segments.txt -c copy -movflags +faststart silent.mp4
# Audio script currently expects the video to be named and located at
# /mnt/data/particulate_motion_demo_9x16.mp4.
python particulate_motion_soundtrack.py
```

## QA gates

- **Integrity:** source geometry and model version hash, clearly attributed; no invented method or inference claims.
- **Articulation:** valid directed joint graph, positive segment surface area, no unintended detached components, valid axes and units.
- **Physical plausibility:** collision, joint range, self-intersection, penetration, snapping, frame-to-frame velocity continuity.
- **Rendering:** no black frames, visible hero mesh, smooth camera motion, stable frame rate, anti-aliased captions and 5% safe margin.
- **Continuity:** fixed color mapping for part IDs, stable series art bible and scene coordinates, no unexplained material or axis changes.
- **Publishing:** approval of exact video + copy; comply with group rules and license/attribution. Avoid pretending an authored procedural rig was inferred by a neural network.

## Licensing and operational caveats

The Particulate HF model card labels weights CC-BY-4.0 and code Apache-2.0. Check third-party mesh/source licenses and pretrained dependencies separately. Do not execute arbitrary downloaded authoring scripts without sandboxing; Articraft projects may include generated Python. Particulate inference requires a CUDA GPU in its current official script. The fallback used in the prototype is **manual procedural articulation**, not an equivalent implementation of the paper.
