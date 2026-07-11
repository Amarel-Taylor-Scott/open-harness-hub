# Teleon Multimodal Media Primitive Registry

This note extends the Teleon primitive/compiler architecture from code primitives to multimodal primitives:
images, video, audio, model components, media transforms, timelines, scene plans, and node-graph workflows.

The core answer is:

```text
Teleon should not be only a code-primitive compiler.
Teleon should be a typed multimodal capability compiler.
```

Code functions, media models, ComfyUI nodes, Diffusers components, FFmpeg transforms, ASR/TTS models,
safety classifiers, scene planners, and artifact validators can all be represented as typed primitives with
declared inputs, outputs, side effects, memory policy, runtime requirements, proof obligations, and
promotion status.

## Research Anchors

These are the most relevant references found while researching this direction:

- [Compiled AI](https://arxiv.org/abs/2604.05150): LLM generates/validates artifacts during a compile
  phase; runtime execution is deterministic and does not require further model calls.
- [LLMCompiler](https://arxiv.org/abs/2312.04511): LLM emits a task/function-call plan that an executor can
  schedule, including parallel dispatch.
- [LLM+P](https://arxiv.org/abs/2304.11477): LLM translates natural language into a formal planning problem,
  then a deterministic planner solves it.
- [ComfyUI Server Routes](https://docs.comfy.org/development/comfyui-server/comms_routes): ComfyUI exposes
  workflow submission, node metadata, queue/history, WebSocket execution progress, and image upload/view
  routes. This is a practical model for media graph execution.
- [ComfyUI Workflow JSON](https://docs.comfy.org/specs/workflow_json): ComfyUI workflow JSON is specified by
  JSON Schema and includes nodes, links, inputs, outputs, widget values, and graph metadata.
- [ComfyBench](https://arxiv.org/abs/2409.01392): benchmarks LLM agents generating ComfyUI workflows; the
  low creative-task resolve rate is evidence that raw autonomous workflow generation is brittle.
- [ComfyGPT](https://arxiv.org/abs/2503.17671): focuses on generating node links rather than entire workflows
  monolithically, which supports Teleon's "LLM proposes bindings, compiler validates graph" direction.
- [ComfySearch](https://arxiv.org/abs/2601.04060): validates the importance of search/exploration plus
  workflow validation for complex ComfyUI pipelines.
- [ComfyMind](https://arxiv.org/abs/2505.17908) and
  [ComfyUI-R1](https://arxiv.org/abs/2506.09790): both reinforce the same lesson from different angles:
  high-level semantic workflow abstractions, execution feedback, and rule/metric validation matter more than
  raw node-JSON generation.
- [VideoDirectorGPT](https://arxiv.org/abs/2309.15091): LLM expands a prompt into a structured video plan
  with scenes, entities, layouts, backgrounds, and consistency groupings before downstream generation.
- [Agentic Video Generation](https://arxiv.org/abs/2604.10383): turns text into a formal graph of events in
  space and time, then executes that graph deterministically in a 3D engine. This is the clearest media-domain
  analogue for "LLM plans; compiler/runtime enforces constraints."
- [ELLMPEG](https://arxiv.org/abs/2602.00028): uses tool-aware retrieval and local verification to generate
  FFmpeg/VVenC commands, which supports treating deterministic media command surfaces as registry primitives.
- [Diffusers ComponentSpec / ComponentsManager](https://huggingface.co/docs/diffusers/main/en/api/modular_diffusers/pipeline_components):
  Hugging Face Diffusers has emerging concepts for component specs, loading configs, component managers,
  reuse, duplicate detection, and memory/offload management.
- [Stable Video Diffusion model card](https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt):
  example of an image-to-video model card with model type, input/output behavior, usage limits, license,
  safety notes, and runtime characteristics.
- [AudioLDM](https://arxiv.org/abs/2301.12503): text-to-audio generation can be represented as a model
  primitive with prompt/audio artifact contracts.
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html): deterministic audio/video transforms already
  have a graph-like filter model and are good media-transform primitives.

## Generalized Primitive Definition

The primitive is not "a Python function." The primitive is:

```text
a typed capability with declared inputs, outputs, side effects, runtime constraints, provenance,
mutation/remix affordances, and proof requirements.
```

That capability may be backed by:

```text
Python callable
external API operation
local diffusion model
ComfyUI node
ComfyUI workflow/subgraph
Diffusers pipeline
Diffusers component
FFmpeg filtergraph
ASR/TTS model
vision classifier
safety gate
container job
human review step
composite PlanLock
```

## Primitive Families

Teleon should keep one registry model with modality-specific subtypes.

```text
PrimitiveCard
  CodePrimitive
  ModelPrimitive
  MediaModelPrimitive
  MediaTransformPrimitive
  ArtifactTransformPrimitive
  ScenePlanPrimitive
  TimelinePrimitive
  GatePrimitive
  RouterPrimitive
  CompositePrimitive
```

Examples:

```text
code.normalize_invoice
image.generate.sdxl
image.upscale.esrgan
image.segment.subject
image.mask.generate
video.generate.image_to_video.svd
video.generate.text_to_video.provider
video.stabilize.temporal
video.encode.ffmpeg
audio.generate.audioldm
audio.transcribe.whisper
audio.mix.ffmpeg
scene.plan.video_director
timeline.compose.shots
safety.media_gate
comfyui.workflow.product_video
```

## Artifact Type System

Media pipelines need typed artifacts, not generic files.

Core artifact contracts:

```text
TextPrompt
PromptSpec
NegativePrompt
ImageArtifact
MaskArtifact
DepthMapArtifact
SegmentationArtifact
PoseSequenceArtifact
LatentArtifact
VideoArtifact
AudioArtifact
SubtitleArtifact
TranscriptArtifact
ScenePlan
ShotPlan
TimelinePlan
CameraPath
MotionPrompt
StyleSpec
ModelWeightsRef
LoRARef
EmbeddingRef
ControlSignal
SafetyDecision
QualityReport
DeliveryReceipt
```

Media contracts need dimensions and units:

```text
resolution
aspect_ratio
fps
duration_seconds
frame_count
sample_rate_hz
channels
codec
container
colorspace
bit_depth
latents_shape
model_family
license_class
safety_class
identity/consent constraints
```

## Media Primitive Card

Example:

```yaml
primitive_id: media.video.image_to_video.svd_xt
kind: media_model
modality:
  input: [image, prompt]
  output: [video]

surface:
  adapter: diffusers
  model_ref: stabilityai/stable-video-diffusion-img2vid-xt
  callable: diffusers.DiffusionPipeline.from_pretrained

inputs:
  image:
    type: ImageArtifact
    required: true
    constraints:
      aspect_ratio: "16:9"
  motion_prompt:
    type: TextPrompt
    required: false
  seed:
    type: int
    required: true

outputs:
  video:
    type: VideoArtifact
    constraints:
      max_duration_seconds: 4

effects:
  - gpu_compute
  - model_inference

determinism:
  class: seeded_approximate
  requires_seed: true
  replay_safe: best_effort

runtime:
  compatible:
    - local_gpu_worker
    - kubernetes_gpu_job
    - comfyui_node
  vram_gb: 16
  timeout_seconds: 900

memory:
  input_policy: artifact_ref
  output_policy: artifact_ref
  max_inline_bytes: 0

policy:
  requires_before:
    - image.safety_gate
  requires_after:
    - video.quality_gate
  license_check: required

proof:
  required:
    - smoke_generation
    - artifact_hash_recorded
    - safety_gate_passed
```

## Multi-Model Pipeline Example

Still image to short product video:

```text
InputSpec
  -> image.validate
  -> image.safety_gate
  -> image.describe
  -> scene.plan_from_image
  -> motion_prompt.derive
  -> image.mask.subject
  -> video.generate.image_to_video
  -> video.stabilize
  -> audio.generate.music_bed
  -> audio.mix.ducking
  -> subtitles.generate
  -> video.compose.timeline
  -> video.encode.ffmpeg
  -> video.quality_gate
  -> output.package
```

This uses multiple model families:

```text
vision model / VLM for image description
safety classifier
LLM for scene/timeline planning
segmentation model
image-to-video model
video stabilization transform
text-to-audio model
audio mixer
subtitle/ASR/TTS model
FFmpeg encoder/filtergraph
quality classifier
```

The LLM should not emit raw ComfyUI JSON or FFmpeg commands by default. It should emit a constrained
MediaPipelineIR or PlanDelta:

```json
{
  "v": 1,
  "template": "media.image_to_short_video",
  "bindings": [
    ["describe", "C0.0"],
    ["scene_plan", "C1.0"],
    ["generate_video", "C2.1"],
    ["stabilize", "C3.0"],
    ["encode", "C4.0"]
  ],
  "remix": [
    ["generate_video", "lower_resolution_if_vram_lt_16gb"]
  ],
  "gaps": []
}
```

The compiler then expands aliases, validates artifact contracts, checks policy, locks models and
parameters, and emits runtime-specific manifests.

## Multi-Model Capability Routing

The registry should not assume one model per capability. A single logical slot may have many model-backed
implementations:

```text
video.generate.image_to_video
  -> local Diffusers SVD worker
  -> ComfyUI SVD workflow
  -> ComfyUI AnimateDiff workflow
  -> external image-to-video API
  -> deterministic 3D/event-graph renderer
  -> promoted composite pipeline
```

The compiler should route by capability contract and constraints, not by brand or provider name.

```text
slot contract:
  ImageArtifact + MotionPrompt + DurationSpec -> VideoArtifact

route candidates:
  local_svd_xt:
    determinism: seeded_approximate
    runtime: local_gpu_worker
    vram_gb: 16
    max_duration_seconds: 4
    cost_class: local_compute

  comfyui_animatediff:
    determinism: seeded_approximate
    runtime: comfyui_server
    vram_gb: 12
    max_duration_seconds: 6
    cost_class: local_compute

  external_provider_i2v:
    determinism: external_nondeterministic
    runtime: external_api_activity
    vram_gb: 0
    max_duration_seconds: 10
    cost_class: paid_api

  engine_event_graph:
    determinism: deterministic_binary
    runtime: container_job
    style: simulated_3d
    max_duration_seconds: 30
    cost_class: cpu_or_gpu_container
```

Route selection should be deterministic:

```text
1. Prefer promoted composite route if it satisfies the requested style, policy, and budget.
2. Prefer deterministic_binary or seeded_deterministic when exact replay matters.
3. Prefer local seeded_approximate when artifact quality is acceptable and GPU is available.
4. Use ComfyUI workflow adapter when node graph coverage is better than direct model API coverage.
5. Use external provider only when local routes fail constraints or quality/cost policy allows it.
6. Record every fallback decision in the PlanLock and ledger.
```

The LLM may suggest a model family, but it should not decide final placement. The compiler owns final route
selection using:

```text
artifact contracts
resolution/fps/duration constraints
runtime availability
VRAM and memory pressure
provider policy
license and usage rights
determinism requirement
quality history
cost budget
safety/consent policy
known successful chains
recent failure memory
```

This also means the same MediaPipelineIR can compile into different physical plans:

```text
MediaPipelineIR
  -> local Diffusers worker plan
  -> ComfyUI workflow JSON
  -> FFmpeg filtergraph commands
  -> external model API activities
  -> 3D engine event graph execution
  -> hybrid route with local generation + deterministic postprocess
```

The route itself should become a first-class record:

```yaml
route_id: route.media.i2v.local_svd_then_ffmpeg@1
capability: video.generate.image_to_video
logical_contract: ImageArtifact+MotionPrompt+DurationSpec -> VideoArtifact
physical_plan:
  - media.video.image_to_video.svd_xt
  - media.video.stabilize.ffmpeg
  - media.video.encode.ffmpeg_h264
determinism_class: seeded_approximate
fallback_after:
  - route.media.i2v.comfyui_animatediff@1
  - route.media.i2v.external_provider@1
promotion:
  status: candidate
  serves_truth: false
```

## ComfyUI As A Runtime Adapter, Not The Registry Truth

ComfyUI is a useful media graph runtime and reference architecture, but Teleon should not make ComfyUI JSON
the canonical IR.

ComfyUI has:

```text
node types
workflow JSON
links
inputs/outputs
widget values
prompt submission
execution queue
history
WebSocket progress
object_info node metadata
image upload/view routes
```

Teleon should use that as:

```text
Teleon MediaPipelineIR
  -> compiler
  -> ComfyUI workflow JSON adapter
  -> ComfyUI /prompt execution
  -> WebSocket progress events
  -> artifact and ledger ingestion
```

Do not give the LLM raw ComfyUI node JSON unless a compact node card fails. Generate compact node cards:

```text
C2.1 svd_img2vid ImageArtifact+MotionPrompt+Seed>VideoArtifact fx:gpu tools:lowres,batch tr:V
```

Then deterministically lower to ComfyUI workflow JSON.

## Diffusers As A Model-Component Registry Source

Diffusers has concepts that map well to Teleon:

```text
ComponentSpec
ConfigSpec
ComponentsManager
pipeline components
component loading
from_pretrained
memory/offload management
```

Teleon should ingest these as candidate model/component records:

```text
Diffusers pipeline -> ModelPrimitive
UNet/VAE/text encoder/scheduler -> ModelComponentPrimitive
pipeline config -> TemplateCapsule or ModelConfigCard
ComponentsManager memory/offload info -> RuntimeCard
```

But Hugging Face component IDs and Python object IDs are not canonical Teleon identities. They are surfaces
and aliases under `PrimitiveIdentity`.

## FFmpeg As Deterministic Media Transform Surface

FFmpeg filtergraphs are strong deterministic media primitives:

```text
video.trim
video.scale
video.crop
video.concat
video.overlay
video.encode
audio.resample
audio.normalize
audio.mix
audio.fade
subtitle.burn_in
container.mux
```

Unlike diffusion/model generation, many FFmpeg transforms are highly replayable if binary version, command,
inputs, codec, parameters, and environment are locked.

Teleon should represent FFmpeg transforms as:

```yaml
primitive_id: media.video.encode.ffmpeg_h264
kind: media_transform
determinism:
  class: deterministic_binary
runtime:
  compatible: [container_job, local_worker]
proof:
  required:
    - ffmpeg_version_locked
    - command_hash_recorded
    - input_artifact_hashes_recorded
    - output_artifact_hash_recorded
```

## Determinism Classes For Media

Media generation needs more precise determinism classes than code transforms.

```text
deterministic_binary:
  same binary + same inputs + same params should reproduce output

seeded_deterministic:
  local model with locked weights, seed, scheduler, device policy; expected reproducible within defined tolerance

seeded_approximate:
  seed is controlled but GPU/library/provider nondeterminism may cause small differences

external_nondeterministic:
  hosted API or opaque model; output artifact is locked, replay may regenerate different media

human_reviewed:
  manual approval or curation required
```

Policy:

```text
The orchestrator can be deterministic even when leaf media generation is not.
PlanLock must honestly record leaf determinism class.
Ledger must store output artifact hashes.
Replay must distinguish exact reproduction from provenance replay.
```

## Media-Specific Compiler Checks

The compiler should validate:

```text
artifact type compatibility
resolution/aspect/fps/sample-rate/duration compatibility
colorspace and codec compatibility
model input limits
model license and commercial-use constraints
identity/consent constraints
safety gates before generation/delivery
watermark/provenance policy
VRAM/resource placement
artifact-ref memory policy
seed/parameter lock
provider nondeterminism declaration
cost and timeout budgets
large-output storage policy
branch convergence for alternate models
quality gate before publish
```

Examples:

```text
ImageArtifact -> image_to_video model is valid.
VideoArtifact -> audio_mixer is invalid unless mixer accepts video+audio timeline.
Generated video -> delivery.publish is invalid before video.quality_gate.
Large frame tensor inline state is invalid; must be ArtifactRef or LatentArtifactRef.
External API model without replay guarantees cannot be marked deterministic.
```

## Media Remix Tools

Media needs deterministic remixes:

```text
lower_resolution
crop_or_pad_to_aspect
fps_convert
duration_chunk
batch_frames
artifact_materialize
artifact_reference
model_downshift
api_to_local_model_swap
local_to_api_model_swap
comfyui_node_adapter
diffusers_pipeline_adapter
ffmpeg_filter_adapter
watermark_inserter
safety_gate_inserter
quality_gate_inserter
caption_burn_in
audio_ducking
```

Each remix must define:

```text
preconditions
contract delta
effect delta
memory delta
runtime delta
proof obligations
quality impact
promotion status
```

Example:

```yaml
remix_id: mut:media:lower_resolution@1
from: ImageArtifact[1024x576] -> VideoArtifact[1024x576]
to: ImageArtifact[768x432] -> VideoArtifact[768x432]
preconditions:
  - target_model.supports_resolution_768x432
  - user_constraints.allow_resolution_downshift
proof_obligations:
  - output_resolution_matches
  - quality_gate_still_passes
  - cost_or_vram_reduction_recorded
```

## Media CandidateBundle

The LLM should see compact candidate bundles like:

```text
Q make_short_product_video_from_image
O VideoArtifact
T0 media.image_to_short_video

S0 inspect ImageArtifact>ImageDescription
S1 plan ImageDescription>ScenePlan
S2 motion ScenePlan>MotionPrompt
S3 gen ImageArtifact+MotionPrompt+Seed>VideoArtifact req:safety_before
S4 stabilize VideoArtifact>VideoArtifact
S5 encode VideoArtifact>VideoArtifact
S6 qc VideoArtifact>QualityReport gate

C3.0 svd_xt ImageArtifact+MotionPrompt+Seed>VideoArtifact fx:gpu mem:a tools:lowres tr:V
C3.1 api_kling ImageArtifact+MotionPrompt>VideoArtifact fx:api mem:a tools:none tr:C
C4.0 ffmpeg_stabilize VideoArtifact>VideoArtifact fx:cpu mem:a tools:batch tr:V
C5.0 ffmpeg_h264 VideoArtifact>VideoArtifact fx:cpu mem:a tools:none tr:V
```

LLM output:

```json
{"v":1,"p":"dense","t":0,"b":[0,0,0,0,0,0,0],"r":[[3,"lowres"]],"g":[]}
```

Compiler output:

```text
PlanLock with canonical primitive identities, model refs, seeds, parameters, artifact refs, runtime
placement, policy report, and proof obligations.
```

## Registry Tables / Records To Add

Add these record families:

```text
media_artifact_type
media_primitive_card
model_card
model_component_card
media_template_card
media_runtime_card
media_remix_card
media_quality_gate_card
media_safety_policy_card
media_planlock
media_artifact_manifest
```

Do not create a separate media registry silo. Add modality fields to the same primitive registry.

## Runtime Placement

Media workloads need runtime placement:

```text
local_cpu_worker:
  metadata, ffmpeg, small transforms

local_gpu_worker:
  local diffusion, VLM, ASR/TTS

comfyui_server:
  node-graph image/video workflows

diffusers_worker:
  Python model pipelines

kubernetes_gpu_job:
  heavyweight bounded model jobs

cloud_run_job / ECS task:
  bounded containerized media transforms

external_api_activity:
  Runway/Kling/OpenAI/etc style hosted model calls

temporal_workflow:
  orchestration, retries, queues, human review
```

The runtime should pass artifact references, not large media blobs.

## Proof And Promotion For Media

Media proof is not just unit tests.

Proof artifacts:

```text
input artifact hashes
model identity and version
weights hash or provider model ID
seed and params
runtime image digest
output artifact hash
duration/resolution/fps/codec probe
safety gate report
quality gate report
license/policy report
human review receipt if required
```

Promotion policy:

```text
Generated media output is an artifact, not truth by itself.
Model/component can be promoted if proof gates pass.
Pipeline can be promoted as a composite if repeated executions meet quality/cost/safety thresholds.
External API outputs can be locked as artifacts even if generation is not replayable.
```

## How This Changes Teleon

This does not change the north-star architecture. It broadens what counts as a primitive.

Before:

```text
primitive = Python/code component
```

After:

```text
primitive = typed capability over code, models, media, artifacts, tools, and workflows
```

The same route/fallback system still applies:

```text
promoted composite reuse
deterministic template fill
compact LLM PlanDelta
deterministic remix repair
patch PlanDelta
evidence replan
gap record
generated adapter candidate
source/workflow rewrite
human review
```

## First Implementation Slice

Add a candidate-only media registry contract and benchmark.

Business workflow:

```text
still image -> short product video package
```

Steps:

```text
validate image
safety gate
describe image
derive scene plan
derive motion prompt
generate video
stabilize/encode
quality gate
emit package
```

Variants:

```text
direct Diffusers pipeline
ComfyUI workflow adapter
external API model adapter
FFmpeg-only transform path
hybrid local generation + FFmpeg postprocess
```

Failure cases:

```text
inline video bytes rejected
missing safety gate rejected
unsupported aspect ratio repaired by crop/pad remix
VRAM too low repaired by lower_resolution or model_downshift
external nondeterministic provider marked honestly
delivery before quality gate rejected
```

Metrics:

```text
LLM input tokens
PlanDelta output tokens
compile success
runtime success
artifact hashes recorded
media metadata probe pass
quality gate pass
safety gate pass
runtime cost
VRAM estimate
fallback route taken
```

## Final Position

Teleon can support code, images, video, audio, documents, scraping, RAG, and model chains under one registry
if it treats everything as a typed primitive with artifact contracts.

The LLM plans a graph. The compiler validates and locks it. The runtime executes locked nodes. The ledger
records artifacts and reality. Proof/promotion decides what becomes reusable.
