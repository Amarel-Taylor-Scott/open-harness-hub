# Baltor Skill-to-Binary Distillation Playbook

## Fundamental rule
**Instructions do not magically compile into deterministic code.** Distill task semantics into minimal operations, then implement independently or safely wrap a licensed pinned dependency. Keep uncertain human/model decisions explicit.

## Seven-stage promotion path
1. **Discover:** scan approved local source trees, record source checksums, license metadata, related scripts and dependencies.
2. **Classify:** identify pure deterministic operations, seeded probabilistic operations, stateful operations, model inference, human judgments, and external effects. Record side-effect privileges.
3. **Slice:** split workflows into small transformations with explicit JSON Schema for input/output. Avoid huge monolithic “run entire skill” tools.
4. **Implement:** prefer vetted native CLIs or thin wrappers around pinned libraries; no arbitrary argument passthrough, shell injection or network by default.
5. **Prove:** golden fixtures, independent baseline, cross-validation, adversarial invalid inputs, resource ceilings, checksum verification, regression tests.
6. **Package:** static native binary when possible, or OCI/WASI/Python wheel pinned to dependencies; SBOM, hash, optional signature, read-only input filesystem.
7. **Promote:** move a capability from `candidate` to `tested` to `enabled`; capture execution logs, use monotonic versioning, and provide rollback.

## Example: cinematic-video-production skill
The source skill is editorial guidance. Proposed operators: `storyboard.compile`, `layout.lint`, `camera.spline`, `fx.parallax`, `audio.duck`, `video.xfade`, `video.master`, `video.qc`.
- `storyboard.compile`/`layout.lint`: implemented here in pure Go.
- `camera.spline`, `fx.parallax`, `audio.duck`, `video.xfade`, `video.master`: recommended future typed adapters to pinned FFmpeg/Blender components.
- `video.qc`: compose pixel, subtitle, volume, metadata and human review checks. Never use automated checks as blanket proof of creative quality.

## Deterministic run manifest
A worker's execution manifest should capture:
- capability_id and semantic version
- implementation digest, model digest if any, and external tool build versions
- schema version; canonical input JSON hash; input asset hashes; seed if stochastic
- allowlisted read/write mounts, network policy, time/CPU/memory/frame/byte ceilings
- output filenames, MIME types, byte lengths, SHA-256 digests, validation results
- reproducibility class: pure / environment pinned / seeded stochastic / nondeterministic
- rights/provenance/consent for incoming third-party media
- peer review/test evidence and explicit publish approval

## Non-equivalences to preserve
- A tested video encode in one FFmpeg build is not proven byte-identical across builds.
- A CLIP/image embedding or LLM grade is not a verified ground-truth quality metric.
- Agent Skills are procedural guidance; they may include scripts that require permission and containment.
- A repo's license does not automatically permit repackaging model weights, examples, sample images, bundled third-party libraries, or remote data.
- `SKILL.md` scanner findings are heuristic and can miss sophisticated malware, side effects, licensing restrictions, or malicious prompts.

## Recommended extraction ranking
**P0 now:** scene cut detection; timed subtitle compiler; graphics safezones; CLI/skill metadata; SBOM; materialized dependencies; test result parsing; auditable caching.
**P1 next:** camera fitting, image masking, text-aware reflow, optical flow, GLB optimization, audio speech/beat alignment, full-resolution rendering, OTIO timeline exchange.
**P2 after QA:** GPU articulation, neural TTS, latent/depth segmentation, automatic editorial decisions, complex agent-driven experimentation.
