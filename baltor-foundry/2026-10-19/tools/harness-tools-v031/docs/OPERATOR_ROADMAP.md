# Operator backlog — candidates, NOT executable components

The 13 operations in `OPERATOR_CONTRACTS.json` are the ones in the current compiled binary. The following 45 are **research and engineering ideas** that require implementation and verification. Split each candidate into a separate small module/CLI wrapper before moving it into a production agent harness.

## Visual analysis (8)
- `video.shots.detect` — adaptive scene cuts with explicit confidence thresholds.
- `video.camera.estimate` — optical-flow decomposition; caveat: no true camera recovery from pixels alone.
- `video.motion.separate` — coarse subject motion vs background motion.
- `video.palette.extract` — per-shot color harmonization.
- `video.typography.propose` — text bounding box proposals, with OCR optional.
- `video.saliency.heatmap` — face/subject/background occupancy and uncertainty.
- `video.borders.measure` — estimate frame edges and letterboxing.
- `video.style.fingerprint` — compare generalized cinematography styles, not copyrighted expressions.

## Character / image assets (7)
- `image.cutouts.segment` — produce alpha-separated semantic image layers.
- `image.parallax.depth` — rough monocular depth, with uncertainty and human correction.
- `rig.stick.solve` — pose interpolation with bone lengths/constraints.
- `rig.kinematics.load` — GLB/URDF articulated source import.
- `rig.particulate.infer` — CUDA-only external worker adapter (model not bundled).
- `image.character.consistency` — compare locked character sheets against generated frames.
- `image.asset.provenance` — store source, licensing, rights and reviewer notes.

## Animation & layout (8)
- `camera.path.keyframe` — cubic and piecewise easing with authored landmarks.
- `camera.path.optimize` — minimize subject occlusion / overshoot under constraints.
- `scene.occlusion.render` — depth-order compositing and mask validation.
- `scene.parallax.render` — per-plate virtual-camera speeds and depth.
- `text.caption.align` — per-word timing with narration transcript evidence.
- `layout.semantic.safe` — constrain text away from subjects/UI overlays.
- `layout.grid.solve` — responsive 1x2, 2x2, picture-in-picture panels.
- `layout.a11y.audit` — text contrast, minimum sizes and readability checks.

## Video / sound output (6)
- `audio.neural.tts` — speech model adapter, license-approved voices.
- `audio.beat.detect` — identify beat grid and key impacts.
- `audio.mix.duck` — side-chain ducking for natural narration.
- `audio.cues.place` — synchronize footprints, hits, doors, radios, etc.
- `video.encode.platform` — bitrate and aspect presets per social destination.
- `video.master.render` — generate source-res and delivery-res masters without upscaling.

## Harness / reliability (8)
- `harness.container.launch` — actual network-disabled OS sandbox through OCI/gVisor/VM.
- `harness.resources.enforce` — CPU/memory/egress quotas with OS-level evidence.
- `harness.cache.cas` — content-addressable deduplication across different DAG jobs.
- `harness.job.resume` — partial-failure recovery by per-node checkpoint.
- `harness.job.cancel` — cooperative cancellation and process-group cleanup.
- `harness.binary.sbom` — dependency inventory and signature verification.
- `harness.artifact.sign` — cryptographic signatures, not just unsalted hashes.
- `harness.agent.mcp` — documented tool registry with scoped resources and auth.

## Research and scale (8)
- `research.paper.extract` — figure/citation/experiment extraction.
- `research.repo.map` — source/API graph for authorized repositories.
- `research.claim.verify` — check claims against experiments and evidence.
- `research.discovery.feed` — structured feed metadata, rights and freshness.
- `video.variant.design` — factorial variation over layout/style/time dimensions.
- `video.variant.score` — human-reviewed quality and diversity metrics.
- `video.series.canon` — stateful bibles and continuity checks.
- `video.social.approval` — explicit human gate; no publishing by default.

## Priority order

1. True OCI/VM confinement, per-node cache, job resume and audit/signatures.
2. Source frame layers and full-resolution scene renderer with subject-aware caption placement.
3. Face/saliency/semantic QA and text placement before final MP4 generation.
4. Rigged 2D / 3D adapter and Particulate GPU integration where hardware permits.
5. Narration + word-level alignment, audio ducking, impact beats and longer videos.
6. Large batch evaluation with dedupe, provenance, market-relevance and ROI scoring.
