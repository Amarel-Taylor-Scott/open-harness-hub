# Baltor Harness Tools v0.3.1 — native motion-composer CLI

A working, **closed-operator, deterministic-on-the-same-runtime** DAG executor for original programmatic video generation and authorized local video analysis. Built as standalone Go executables, with FFmpeg/ffprobe used only for media encode/decode/probe. Extends the earlier Baltor Spatial Studio v0.2 without modifying its original files.

## Finished proof runs

- `recipes/showcase.json`: native 20-second vertical animation, 7 operations, H.264/AAC MP4.
- `recipes/composed.json`: **11-node** post-render camera, color grade, spatial analysis, graphic overlay and MP4 workflow.
- `recipes/layered.json`: **11-node** layering improvement — bare procedural scene → camera transform → per-shot anchored text/panels/border/progress via z-sorted frame overlays → encoded MP4.
- `recipes/analyze_existing.json`: an **audit-only** workflow for a staged reference MP4 and existing Spatial Studio v0.2 layouts.

The original authored art is simple pixel/vector-style graphics, not neural generative video or model-inferred articulation. Not suitable as polished marketing without additional art, sound and human QA.

## Operator catalog

`scene.frames`, `audio.synth`, `timeline.compile`, `frames.transform`, `frames.overlay`, `frames.metrics`, `frames.spatial`, `frames.contact`, `video.encode`, `video.sample`, `video.probe`, `layout.lint`, `artifact.hash`. See [machine-readable contracts](docs/OPERATOR_CONTRACTS.json), the [recipe schema](docs/recipe.schema.json) and the explicitly separate [operator backlog](docs/OPERATOR_ROADMAP.md).

## Running natively

Choose your executable from `bin/` for Linux x86_64 / Linux ARM64 / macOS Apple Silicon / Windows x86_64. Only Linux x86_64 was executed in this environment. The Go executable is self-contained, but video encode/sample/probe require `ffmpeg` and `ffprobe` available on PATH. Other platforms may produce different output bytes.

```bash
chmod +x bin/baltorctl-linux-amd64
bin/baltorctl-linux-amd64 doctor
bin/baltorctl-linux-amd64 catalog --json
bin/baltorctl-linux-amd64 validate --recipe recipes/layered.json
bin/baltorctl-linux-amd64 plan --recipe recipes/layered.json --workspace ./work --json
bin/baltorctl-linux-amd64 graph --recipe recipes/layered.json --out ./work_graph.dot
bin/baltorctl-linux-amd64 run --recipe recipes/layered.json --workspace ./work --json
bin/baltorctl-linux-amd64 verify --run ./work/runs/<run-id>
bin/baltorctl-linux-amd64 inspect --run ./work/runs/<run-id>
bin/baltorctl-linux-amd64 pack --run ./work/runs/<run-id> --out ./run-bundle.tar.gz
```

### Auditing a permitted local reference video

```bash
bin/baltorctl-linux-amd64 ingest --file /your/authorized/video.mp4 --as reference.mp4 --workspace ./work_audit
bin/baltorctl-linux-amd64 ingest --file /path/to/layouts.json --as layouts.json --workspace ./work_audit
bin/baltorctl-linux-amd64 run --recipe recipes/analyze_existing.json --workspace ./work_audit --json
```

The video analysis returns pixel-based metrics and guesses about possible cuts and quiet regions. It does NOT perform OCR, semantic action recognition, recreate 3D geometry, or prove exact filming methods.

### Multi-call CLI tools

The binary detects these executable names and dispatches automatically: `baltor-run`, `baltor-plan`, `baltor-verify`, `baltor-diff`, `baltor-pack`, `baltor-graph`, `baltor-inspect`, `baltor-catalog`, `baltor-validate`, `baltor-ingest`, `baltor-doctor`.

On Linux, create hardlinks/symlinks with `scripts/install_aliases.sh bin/baltorctl-linux-amd64 bin`. These are multiple entrypoints to the **same tested executable**; they are not 11 distinct packaged engine implementations.

## Encapsulated harness operation

**The native working-directory scope is not an OS security boundary.** For third-party assets and agent-generated recipes, run the binary inside a network-disabled, read-only-root, low-privilege OCI container or a VM. A recommended Docker/Podman launcher is supplied:

```bash
docker build -f Containerfile -t baltor/harness-tools:0.3.1 .
# Example, ONLY when Docker/Podman is installed:
scripts/run_container.sh run --recipe /recipes/layered.json --workspace /work --json
```

`run_container.sh` refuses to fall back to native execution if the container runtime is absent. **Container isolation has not been exercised in this workspace**, since Docker/Podman are unavailable. The container build may require internet access; runtime specifies `--network none`.

## Determinism and receipt contract

- Validated dependency DAG with unknown-operation, unknown-parameter, cycle and dependency checks.
- Bounded workspace paths and symlink refusal, explicit asset staging, no arbitrary commands or network operations in the supported graph.
- Fingerprint includes canonical recipe, staged inputs, tool version, and FFmpeg version where relevant.
- Per-run `manifest.json` stores every generated artifact path/size/SHA256, plus op receipts. Cache must pass hash verification before reuse.
- Stable normalized tar.gz bundles.
- `--force` rebuilds explicitly; prior output stays intact during node execution, with final replacement only after a successful build.
- Process timeouts and bounded frame counts. This is **not** a signed supply-chain record or kernel sandbox.

## Limitations and next priorities

Raster currently uses an intentionally small 5x7 coded pixel alphabet; high-end type rendering, subject-aware positioning, character rig constraints, true 3D meshes, full-resolution output, neural narration, Word-aligned captions and 300-second video delivery require additional workers. The demonstration's near-black and scene-cut reports are sampled heuristics. No social publication is performed; final assets require approval.

See [`AGENTS.md`](AGENTS.md), [`SKILL.md`](SKILL.md), and [`docs/IMPLEMENTATION_MATRIX.md`](docs/IMPLEMENTATION_MATRIX.md).
