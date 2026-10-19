# BALTOR.AI — MASTER AGENT HANDOFF, CAPABILITY FOUNDRY & MEDIA SYSTEM

**Edition:** 2026-10-19  
**Audience:** An autonomous engineering/research/creative agent continuing this work with access to the user's authorized workspaces.  
**Scope:** Consolidates the present conversation, its two attached conversation exports, relevant earlier Baltor project context, and currently mounted source repositories, binaries, manifests, videos, recipes, tests, and catalogs.  
**Primary deliverable:** This Markdown document is intended to be independently useful even without the accompanying local files.  
**Critical limitation:** This is a comprehensive synthesis of **accessible** context, not proof that every past ChatGPT conversation, search, external web page, or unretrieved artifact has been imported. Do not claim complete historical coverage without an export/import reconciliation report.

> **MISSION IN ONE SENTENCE:** Build Baltor.ai into a continuously improving, evidence-backed, discoverable library of **small, composable, parameterized, executable AI/engineering/creative capabilities**, with rigorous provenance, testing, sandboxed execution, ranking, and agent-native delivery; use this infrastructure to create genuinely polished original media and solve consequential problems beyond the AI industry.

---

## Navigation / table of contents

- [0. Next-agent instructions and evidence labels](#0-instructions-to-the-next-agent--read-this-first)
- [1. Vision, products, websites and full-history ingestion](#1-vision-positioning-and-the-unifying-product)
- [2. Loop Engine, skills-to-binaries and deterministic harnesses](#2-loop-engine-universal-harness-and-deterministic-workers)
- [3. Video/motion foundries: Particulate, 2D, 3D, style composer, commercials](#3-video-games-creative-graphics-and-motion-foundries)
- [4. Facebook communities, naming, marketing and distribution](#4-promotion-audiences-communities-and-distribution)
- [5. Research, red teaming, SDGs and evaluation](#5-research-and-high-impact-applications)
- [6. External tools, standards, repositories and links](#6-research-tools-standards-and-integrations--reference-map)
- [7. Inspected local videos, source packages, CLI binaries and manifests](#7-local-deliverables-and-verification-status-2026-10-19)
- [8. Prioritized next work orders and acceptance criteria](#8-immediate-engineering-work-orders--prioritized)
- [9. Receiving-agent startup and QA rules](#9-handoff-checklists-and-operating-rules-for-the-receiving-agent)
- [10. Paste-ready receiving-agent mandate](#10-paste-ready-mandate-for-the-receiving-agent)
- [Appendix A. All 68 source ecosystems](#appendix-a--the-68-source-ecosystems-from-v04-complete-local-catalog)
- [Appendix B. All 294 proposed operator IDs](#appendix-b--all-294-proposed-v04-operator-ids-complete-local-candidate-registry)
- [Appendix C. All 180 spatial dimensions](#appendix-c--the-full-180-dimension-spatial-design-inventory)
- [Appendix D. 120 motion-content recipe candidates](#appendix-d--120-candidate-motion-content-recipes)
- [Appendix E. 132 motion-harness components](#appendix-e--132-motion-harness-component-candidatesprototypes)
- [Appendix F. 50 future styles](#appendix-f--50-additional-compositionstyle-ideas)
- [Appendix G. 45 future v0.3.1 operators](#appendix-g--45-v031-future-operator-ideas)
- [Appendix H. SHA-256 manifest](#appendix-h--small-verified-workspace-artifact-digest-manifest)
- [Appendix I. Source/URL index](#appendix-i--user-supplied-additional-linkraw-source-index)
- [Appendix J. Known gaps and uncertainties](#appendix-j--source-interpretation-and-known-gaps)

---

## 0. Instructions to the next agent — read this first

1. **Continue implementation, not just ideation.** Inspect source and test fixtures, select a bounded work order, build one useful new operator/adapter/asset, run tests, make a finished deliverable, and record what actually executed.
2. **Preserve status distinctions:** `idea` → `researched` → `specified` → `implemented` → `tested` → `reproducible` → `sandbox-validated` → `human-approved` → `published`. A catalog entry, written skill, compiled cross-target binary, or generated test is not evidence of the later stages.
3. **Do not silently substitute a still image, screenshot, storyboard, transcript, or mocked simulation for a playable 60–300s video** if a user asked for an actual video. A finished MP4 is preferred for production requests; include editable source, manifests, and QA.
4. **NEVER publish social posts, change live websites, or launch a campaign unless the user explicitly approves the exact final media and post copy.** Drafting, rendering, analysis, and local packaging are allowed within normal authorizations; posting and deployment remain separate approval gates.
5. **For reference videos:** use authorized acquisition and respect source/platform rights. Learn general cinematic grammar; do not redistribute copyrighted footage/music, clone a creator's identifiable story beat-for-beat, or imply a third-party video was analyzed when it was not.
6. **Preserve original creative assets and source.** A final MP4 without the editable scene, JSON graph, rig, audio stems, style bible, and QA report is an incomplete production package.
7. **Prefer bounded/deferred execution with fine-grained typed DAG nodes.** Avoid giant synchronous loops or monolithic 'do everything' skills. Cache by content/config/implementation digests; ensure resumability, time/memory/process limits, and honest failure reporting.
8. **No uncontrolled execution of downloaded `SKILL.md` scripts or GitHub code.** Scan as untrusted content, perform licensing/security review, implement independent code or a pinned narrow adapter, and run only in a truly isolated worker when risk warrants it. Existing Containerfiles have **not** been live tested with Docker/Podman here.
9. **No fake performance numbers or site inventory counts.** Site-scale figures reported in past conversations are dated snapshots or previous assistant claims, not permanent facts. Verify against the live source before reuse.
10. **Make the deliverables portable.** The `sandbox:/mnt/data/...` links in this document only work while the artifacts are accessible to this ChatGPT session. On another host, transfer/clone the actual files and use ordinary local paths.
11. **Keep user intent central:** very broad creativity, many genuinely different styles rather than palette recolors; more varied compositions, camera moves, text/spacing/layouts/layers, natural speech, cohesive audio, large shot counts, and human-benefiting applications.
12. **Don't overclaim cross-platform portability or visual polish.** A Linux binary executed here is not a Windows/macOS integration test; a contact-sheet or MP4 decode check is not human creative approval.

### Evidence/status legend

| Label | Meaning |
|---|---|
| `LOCAL-VERIFIED` | File exists and has been directly inspected/probed in the present execution environment. |
| `PROJECT-TESTED` | Project's own stored tests/QA report or reproducibility run says it passed; verify again after any modification. |
| `PREVIOUSLY-REPORTED` | Claimed in an earlier assistant/project conversation, not independently reproduced now. |
| `WEB-SPOT-CHECKED` | Official/project page or source checked during this handoff (2026-10-19). Not a full integration test. |
| `SPECIFIED` | Schema, storyboard, instruction, design, or prototype exists; not the full production functionality. |
| `CANDIDATE` | Research/library/proposed operator; not executable in Baltor until promoted. |
| `BLOCKED` | Missing access, model weights, GPU, explicit permission, validation, or runtime support. |

---

## 1. Vision, positioning and the unifying product

### 1.1 The core observation

LLMs repeatedly regenerate large amounts of code, search for the same information, read newsletters on behalf of people, and rediscover existing reusable functionality. Much of this work can be **distilled into small, parameterized, source-inspectable, reusable implementations** rather than long prompts and generated one-off scripts.

Baltor's goal is to ingest and qualify agent skills, code libraries, CLI tools, MCP servers, papers, datasets, sites, workflows, conversations, media assets, experiment results, and prior run outcomes. It should extract their **useful capability semantics**, preserve raw sources and rights, and only promote genuinely tested executable implementations into agent harnesses.

A practical slogan previously selected for agent-native feeds: **“Stop scrolling LinkedIn or reading newsletters just to be a human/meat proxy for an AI agent; feed the agent directly.”** Related marketing phrases: “Build on what exists,” “Stop searching. Start building,” “Less noise. More signal,” “Build once. Help everywhere,” and “Don't be the middleman between information and your AI.” These are proposed copy, not permission to publish.

### 1.2 Public product/surface map

**Domains have distinct jobs.** Treat this as a working map assembled from discussions, not a live uptime/feature audit of all URLs.

| Website / route | Intended role | Notes |
|---|---|---|
| https://baltor.ai/ | Main capability/discovery platform | Agent-native reusable harness assets and search. |
| https://baltor.ai/library | Public component library | Historical reported counts changed significantly; check live catalog revision. |
| https://baltor.ai/harness-files | Harness files, skills, schemas, source components | Key commercial developer landing area. |
| https://baltor.ai/feeds | Evidence-backed/agent-readable feed surface | Different from cataloging raw component files. |
| https://baltor.ai/feeds/setup | Feed setup | Suggested conversion path. |
| https://baltor.ai/setup | Harness integration/setup | Verify exact instructions before directing traffic. |
| https://baltor.ai/gallery | Creative gallery/assets | Prior snapshots reported hundreds of examples. |
| https://baltor.ai/public-good | Public-good/SDG surface | Align with accessibility and human-impact work. |
| https://systems.baltor.ai/ | Technical systems, harness architecture, toolchain | Some past monitoring saw authentication restrictions; no bypass. |
| https://index.baltor.ai/ | Product/site directory | Use to map social audiences to correct destinations. |
| https://assets.baltor.ai/ | 3D/procedural/generated asset catalog | Earlier discussion mentioned ~120 parametric generators; recheck. |
| https://demos.baltor.ai/ | Browser demos, animations, games, graphics, interactive simulations | Ideal original social-demo source. |
| https://compare.baltor.ai/ | Side-by-side examples/evaluation comparisons | Never imply controlled comparison without documented setups. |
| https://fox.baltor.ai/ | Foxglade / browser 3D character and animation experiments | User-supplied reference. |
| https://fox.baltor.ai/motion-study.html | Specific character motion study | User-supplied reference. |
| https://agentfeeds.si/ | Agent-readable feeds and research discovery | Broad feed catalogs and updates. |
| https://agentbriefs.si/ | **Selected** executive intelligence brand | Personalized tech/competitor/vendor monitoring, tests, thresholded evidence alerts; development status must be verified. |
| https://agentstudios.si/ | Creative and media studio concept | Supports motion-graphics and video factories; verify deployment status. |
| https://agentafk.si/ | Agent execution/overnight work concept | Restricted/bounded unattended workflows. |
| https://dontbeameatproxy.si/ | Automating human relay/reading work | Proposed marketing and product surface. |
| https://getagentfoundry.si/ | Agent factory / skills/tools examples | Reusable developer components. |
| https://LuxePrompting.com/ | Related creative/promotional presence | Independent of Baltor core product. |
| https://linktr.ee/LuxePrompting | Community link hub | Discord/Telegram distribution. |

**Historical scale signals — do not present as current fact:** prior discussions cited ~27K in early development, then ~1,353,029 distinct library files/218,151 packages around 2026-10-08/09, then ~1,560,856 files and ~256,380 items around 2026-10-14. An internal corpus was also described as ~1.7M vectorized items, ~130,385 curated, targeting 20–50M+. These are different populations, dates, and counting methods. Reconcile live counts by snapshot ID, canonical key, category, rights, rank, verification level, and accepted-task outcomes.

### 1.3 AgentFeeds vs. AgentBriefs

- **AgentFeeds:** discover, normalize, rank, update, and expose machine-readable information with evidence/coverage metadata. Ideal consumer is an agent or harness, not someone reading a newsletter.
- **AgentBriefs:** user provides executive role, goals, plan, stack, competitors, vendors, constraints; agents monitor incoming change, investigate, compare against current environment, run bounded proof-of-concept tests when permitted, and notify **only when personalized thresholds are met** with evidence and actionable next steps.
- **Baltor core:** catalog of skills, harness components, agents, CLI binaries, templates, data transforms, tests, tools, environments and invocation recipes that make feed discovery and agent implementation possible.
- **Systems:** infrastructure/architecture and execution substrates; **Studio:** creative/media execution; **AFK:** bounded delegated recurring jobs.

### 1.4 Discovery and ranking

Research dimensions previously requested: **cost, speed, flexibility, maintainability, control, extensibility, scalability, accuracy, reliability, licensing, privacy, rights, data locality, vendor risk** and hundreds of more specific criteria. Preserve raw measurements, units, uncertainty, missingness, cohorts, environments, and proof receipts; do not collapse incompatible measures into a single misleading score. Multiobjective/Pareto comparison is often preferable.

Feeds/sources: MCP Registry, GitHub, PyPI, npm, Hugging Face, model release pages, RapidAPI/API directories, research papers, benchmarks/leaderboards, developer registries, software documentation, forums, subreddits, X/Bluesky/Reddit, newsletters/news sites, discovery from job descriptions and operational tasks, prior agent runs, old prompts and chats, websites, tools and asset registries.

**Recommended normalized entities:** `Source`, `Snapshot`, `Evidence`, `Claim`, `Question`, `DiscoveryBranch`, `DiscoveryAttempt`, `Candidate`, `Capability`, `Implementation`, `Environment`, `Artifact`, `Dependency`, `LicenseRecord`, `BenchmarkRun`, `AcceptedTaskOutcome`, `Feed`, `DecisionRule`, `MediaAsset`, `StyleBible`, `Approval`, `DistributionEvent`. Store relationships, don't flatten everything into one vector embedding.

### 1.5 Reusing full conversation history

The user has explicitly asked to mine **every accessible chat, tool call, webpage, prior search, prompt, code block, media experiment, product idea, correction, failure and accepted deliverable** into useful artifacts. Previous attempts recovered partial archives (e.g. ~961 conversation records in a past snapshot) but did **not** establish complete historical access. An authorized official export plus an ingestion receipt/coverage report remains the reliable prerequisite for claiming total-history coverage.

Suggested compilation stages:

```text
Authorized history export / accessible connected sources
  → canonical message + tool-event parser
  → URLs + artifacts + task intents + user corrections
  → normalized evidence/claims/decisions
  → bounded why/what/how/who/where interrogation
  → gap discovery and anti-convergence branch generation
  → idea-to-capability candidate compiler
  → rights/provenance/security validation
  → implementation or licensed wrapper
  → benchmark, ranking, acceptance, rollback
  → public/private registry + agent feeds
```

Do not mistake a large Cartesian product of configuration parameters for a corresponding number of useful or tested capabilities. Deduplication, actual execution, quality and evidence gates are essential.

---

## 2. Loop Engine, universal harness and deterministic workers

### 2.1 Architectural concept

The broader Loop Engine/harness work envisions: **intent → typed primitives → JSON intermediate representation (IR) → compiler → bounded runtime**. A model proposes or revises the graph; typed operators perform predictable parts. These can combine deterministic logic and explicitly marked non-deterministic/model decisions. Individual sub-tasks should map to fine-grained nodes; execution can be deferred, cached, interrupted, resumed, observed and compared.

Prior discussions referenced a 7/7 acceptance experiment and ~37.48% fewer tokens in one configuration. Treat those as earlier project-reported results requiring the original evaluation fixtures, environments and denominators before any public claim.

Main component domains: model routing, context/RAG, tools/MCP, skill loading, memory, task decomposition, safety approval gates, red teaming, evals, optimizers, graph compiler, backend jobs, browser actions, creative rendering, media analysis, remote inference, data science, monitoring, software delivery, SDG research.

### 2.2 Typed capability contract (recommended)

```json
{
  "capability_id": "baltor.media.camera.dolly.v1",
  "version": "1.0.0",
  "kind": "deterministic_native_operator",
  "status": "candidate",
  "description": "Calculate a validated camera transform curve",
  "inputs_schema": "schemas/camera_dolly_input_v1.json",
  "outputs_schema": "schemas/camera_transform_v1.json",
  "implementation": {
    "type": "native_binary",
    "digest": "sha256:<required after build>",
    "entrypoint": ["baltorctl", "camera.dolly"]
  },
  "determinism": "bit_stable_on_pinned_runtime",
  "resource_limits": {"time_seconds": 15, "memory_mb": 256, "max_output_mb": 20},
  "permissions": {"network": false, "read_mounts": ["/inputs"], "write_mounts": ["/outputs"]},
  "rights": {"source": "original", "license": "review before publication"},
  "tests": ["fixtures/camera_dolly/basic.json", "fixtures/camera_dolly/bounds.json"],
  "documentation": "skills/camera-dolly/SKILL.md"
}
```

This is a **target schema**, not a claim that the example `camera.dolly` command already ships.

### 2.3 Run model and evidence

A harness job should generate a canonical manifest recording input hashes, versions, tool binary digests, model/checkpoint versions when relevant, seed, environment fingerprint, CPU/GPU/runtime specs, actual CLI argv, access policy, graph ordering, per-node start/end/error, output hashes, QA/benchmark scores, optional signed provenance, and a publish-approval identifier. This makes experiments attributable and future cache re-use defensible.

Per-node states: `queued`, `admitted`, `running`, `succeeded`, `failed`, `timed_out`, `cancelled`, `cache_hit`, `needs_review`. Control requirements: allowlisted operations, bounded paths, no arbitrary shell command injection, no implicit network, per-node resource ceilings, retry only idempotent nodes, safe cancellation and rollback, quarantine untrusted inputs.

**Execution classes:** `pure_deterministic`, `pinned_environment_deterministic`, `seeded_stochastic`, `GPU/model_nondeterministic`, `stateful_external`, `human_review`. A deterministic seed is insufficient to guarantee cross-platform deterministic output when decoders, fonts, codecs, libraries or GPUs differ.

### 2.4 Distilling skills into CLIs — actual promotion ladder

`SKILL.md` is an instruction/metadata standard; optional scripts/references/assets may accompany it. Its text **cannot magically be compiled to an executable**. A distiller must discover and classify the operations, write explicit input/output contracts, build an implementation or a narrowly parameterized adapter to pinned upstream software, test golden fixtures, audit dependencies/rights, package, and only then promote to supported status. Official format reference: https://github.com/agentskills/agentskills and https://agentskills.io/specification.

```text
SKILL / repo / docs / paper
 → metadata scan (NO execution)
 → semantic classification and side-effect map
 → minimal typed operators (CANDIDATES)
 → license/security/source-code review
 → independent implementation or pinned CLI wrapper
 → golden fixtures / negative tests / baselines
 → bounded isolated execution
 → signed/hashed reproducible build
 → published registry entry, runtime environment, rank evidence
```

**Avoid giant wrappers:** `ffmpeg -i ... <arbitrary shell args>` isn't a safe typed operator. Prefer `video.xfade({transition,duration,offset,...})` with a narrow allowlist and explicit input/output paths, resource ceilings and predictable failures.

### 2.5 Search and agent decision workflow

1. Parse task, constraints, environment, side effects, creative intent and success criteria.
2. Retrieve lexical and semantic candidates, source-code/AST and dependency graph matches, contracts and previous accepted runs.
3. Filter by permission, rights, runtime, installability, version, evidence grade, budget and compatibility.
4. Rank for task fit and reproducible observed outcome, preserving uncertainty.
5. Compile selected typed nodes into a DAG; identify data transformations/joins and independent parallel branches.
6. Run a cheap plan and dry-run first; bounded execution after relevant approval.
7. Validate outputs against objective and human-quality gates; record costs, failures, rejection, accepted artifacts and model-specific performance.
8. Generalize proven useful subgraphs into candidate modules; regression test before enabling them for other tasks.

---
## 3. Video, games, creative graphics and motion foundries

### 3.1 Unifying creative ambition

Create **fully finished original video episodes, commercials, motion-graphics explainers, interactive games and animated research demonstrations** using reusable programmatic 2D, 2.5D and 3D engines. Use **actual moving objects and editable source**, not merely still images with an indiscriminate zoom. Extract general techniques from reference footage but author original characters, scenes and narratives. Reuse these tools for Baltor marketing **and** sellable/open reusable agent skills/assets.

Preferred outputs: finished MP4 **first** (not merely a storyboard, contact sheet or ZIP), vertical 1080×1920 for social shorts/reels, separate genuine landscape render when asked, preferably 60s or longer for original content, optional 300s+ feature and long-form episodes. Use original/high-quality music, ambience, Foley, SFX and natural neural/recorded narration timed to captions. Previous robotic TTS was rejected. Avoid a black first frame, clipping, unreadable text, gratuitous overlays, fake finished-video claims, weak hooks or repetitive recycled background arrangements.

**Visual-styles palette** (each should be a distinct grammar with own source, shading, scene logic, lighting, typography and movement; not only recolors):

- Realistic live-action-inspired cinematic, macro product photography, clay/miniature sets, low-poly animation, voxel, pixel art, line-drawn stick figures, anime/Japanese animation, comic/manga, graphic novel/ink, paper cut, stop-motion, isometric technical blueprint, golden art deco, collage, 3D gallery, 2D motion graphics, 2.5D parallax, WebGL shaders and particles, interactive platformer recordings, scientific visualization, math/Manim, data-chronology, music-reactive physics, documentary/editorial, arcade HUD, screen-recorded browser/software explainers.
- Effects/components: camera orbit, pan, dolly, zoom punch, match cut, jump cut, parallax, depth reprojection, spatial wipe, push transition, impact frames, screen shake, slow-mo, blur, bloom, fog, dust, snow, rain, lightning, shadows, reflections, shader oceans, path tracing, lighting rigs, rigged limbs, procedural IK, collisions, particles, animated borders, SVG masks, paper textures, halftone, glows, infographic cards, pips, split-screen, lower thirds, subtitles highlighted word by word, pinned title plates and typography motion.
- Aim for multiple image/shot changes per fact, layered camera space and meaningful narrative beats, not a single static asset held for 10 seconds.

### 3.2 General creative-to-video workflow

```text
Research / creative brief / audience / rights / product truth
                 ↓
 Story premise + characters + acts + continuity bible
                 ↓
 Script with narration, claim receipts, voice/sound cues
                 ↓
 Primary storyboard (timestamps and exact shot duration)
                 ↓
 10+ secondary beats per primary shot, where appropriate
                 ↓
 Scene graph + canonical asset IDs + location map
                 ↓
 Camera paths, pose/motion curves, typography layouts
                 ↓
 2D/2.5D/3D source assets and animation execution
                 ↓
 Isolated render and compositor DAG nodes
                 ↓
 Audio: speech alignment → SFX/Foley → score → ducking
                 ↓
 Frame-level checks + contact sheet + full playback review
                 ↓
 Multiple original variations and true aspect-ratio layouts
                 ↓
 Master MP4 + editable native source + manifests + QA
                 ↓
 Human signoff on exact media and copy → optional publishing
```

### 3.3 Storyboard discipline and continuity

The user repeatedly requested **far more than 12 storyboard panels**: hundreds of seconds of content should have dozens of primary shots and many additional microbeats, with per-shot seconds, narration, text, background, character, action, camera, FX, sound, transition and continuity attributes. Treat the following as coexist­ing templates, not one single completed movie:

- Particulate-inspired original 300s motion explainer: **60 shots × 5s**, 600 supporting cues. `baltor_motion_foundry/docs/FEATURE_STORYBOARD_300S.json` — specified, unrendered.
- Stickvival-inspired original *The Last Signal*: a **70-second rendered MP4** based on 15 shots and 45 beats; a distinct **300s draft** contains 40 shots × 7.5s and 400 microbeats; the latter remains unrendered.
- Full 60-second emotional Baltor flagship commercial: **20 shots at 24fps, 1,440 frame slots**, compiled preproduction plan; the completed 60-second cinematic film is **not** available.

Continuity requires a versioned **story bible**: character morphology/wardrobe/reference sheets; prop identities and inventory; environment maps and consistent left/right screen geography; rigs and skeleton schemas; lighting/time/weather; series palette and font specifications; visual language of flashbacks vs present; immutable events and append-only episode logs; story facts; previously-on checks; voice casting; recurring sound motifs; visual review cards; acceptance of migrations only with documented review. User prefers a mixture of styles *between series or experiments* but visual cohesion *within one series*.

### 3.4 Particulate → articulated object → video factory

**Scientific source:** [Particulate: Feed-Forward 3D Object Articulation, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Li_Particulate_Feed-Forward_3D_Object_Articulation_CVPR_2026_paper.html); [official code](https://github.com/RuiningLi/particulate); [Hugging Face demo](https://huggingface.co/spaces/rayli/particulate). Given a static mesh, Particulate infers rigid parts, kinematic structure, joints and motion constraints. Its research authors describe roughly ten-second GPU inference for certain inputs; **no actual Particulate inference is verified in the local prototypes**. Its supported upstream formats can bridge to articulated GLB/URDF/MJCF-style workflows where the specific version/export path supports them.

Companion research:

- [Instruct-Particulate](https://instruct-particulate.github.io/) — uses a target kinematic specification with part descriptions/connectivity/joint types and optional point hints; integration **proposed, not running here**.
- [Articraft](https://github.com/articraftresearch/Articraft) — agent-authored programmatic articulated 3D assets; generated Python is untrusted and needs isolation; API/model requirements and supported exports should be version-pinned. Another project/reference implementation: https://github.com/mattzh72/articraft.
- [UniMate](https://github.com/Friedrich-M/UniMate) — animation generation for **already rigged** diverse skeletons; checkpoint/GPU/runtime/rights requirements. Not a replacement for Particulate's mesh-to-rig estimation. Its authors acknowledge failed motions and skeletons. Some datasets contain third-party assets with distinct commercial rights.

Routing: input text/image/mesh/GLB/FBX/URDF/paper → inspect and normalize → existing rig vs infer rigid joints vs author custom rig → validate part hierarchy, units, axes, limits, rotations, skinning/colliders → pose/motion generation → physics/collision QA where required → scene/camera/light/material/sound → story/post → MP4 and optional interactive export.

**Prototype history and actual files:**

- `particulate_motion_demo.py` and `particulate_motion_demo_with_audio.mp4`: 42-second manually rigged 3D lamp explain­er, 720×1280, 24fps, audio; **not model inference**.
- `baltor_motion_foundry/kinematics.py`, `rigs/{robot,drawer,chair}.json`, `render_foundry.py`, `import_urdf.py`: JSON-authored rigid parts, rotation/prismatic joints, joint-limit checks and forward kinematics. Three 36s MP4s render a robot arm, sliding drawers and folding chair, plus a 60s montage and 1×2/2×2 compositions. Source manifests and joint CSVs exist.
- `baltor_motion_foundry/particulate_worker.py`: prepared/dry-run invocation path. **Actual GPU model, checkpoint and preprocessing execution remains unverified.**
- `baltor_motion_foundry/browser/*`: source for a rig viewer; prior browser runtime was blocked. Do not claim browser integration testing without re-running.
- `baltor_motion_foundry/docs/COMPONENT_CATALOG.json`: **132 component ideas**, only a smaller subset prototype-backed. `CONTENT_RECIPES.json`: **120 content recipes**, not 120 rendered movies. `FEATURE_STORYBOARD_300S.*`: 60 primary shots/600 microbeats, unrendered. `SERIES_BIBLE_3D.json`: rig/lighting/color/continuity policy.

Potential video series: *From Static Mesh to Motion*, *Satisfying Mechanical Transformation*, robotic grippers, folding furniture, exploded product views, reassembled machines, character motion tests, interactive game props, scientific cutaways, AI-generated contraptions, physics musical instruments, factory assembly, synthetic data generation, and accessibility-oriented educational animations. Realistic mechanisms need actual collision/kinematic validation; a plausible image is not engineering proof.

### 3.5 Stickvival, survival stories and cinematic reverse engineering

**Original user references:**

- Facebook: https://www.facebook.com/Stickvival.FB
- Facebook Reels: https://www.facebook.com/profile.php?id=61594987697295&sk=reels_tab
- YouTube channel: https://www.youtube.com/@Stickvival-YT

Past assistant summaries of Stickvival scripts/transcripts described an engaging **format hypothesis**: serial episodes, immediate crisis, second-person present-tense narration, chapter/level cards, visible inventory/resource depletion, calculated deadlines and resource constraints, unexpected signal or artifact, escalation/seasonal pressure, a cliffhanger. Specific described motifs included a notebook, repeated knocks and radio messages. **These are previous conversation observations, not verified frame-level measurements; current workspace includes no confirmed third-party source video downloads.** Do not present the exact patterns/timing/engagement counts as independently verified.

**User-supplied YouTube references (eleven distinct clips):**

1. https://www.youtube.com/shorts/07qXw53UcQg
2. https://www.youtube.com/shorts/cm8TMqlfo8k
3. https://www.youtube.com/shorts/6052j4zquic
4. https://www.youtube.com/shorts/KmEDRpgYD6Y
5. https://www.youtube.com/shorts/B-YR2K-MORw
6. https://www.youtube.com/shorts/nnN8zHnKaLM
7. https://www.youtube.com/watch?v=CCUSpJkAfgU
8. https://www.youtube.com/watch?v=SIZXW0ABD9g
9. https://www.youtube.com/watch?v=k_z3nxFsxyo
10. https://www.youtube.com/watch?v=L3FZk417lxs
11. https://www.youtube.com/watch?v=brWjBipZHVU

**Reference-analysis goal:** authorized local MP4 → preserve source URL/creator/license and hashes → sample/analyze every frame → detect candidate cuts/fades/whip pans → camera estimation and optical flow → actor/subject tracking → depth segmentation and parallax inference → typography OCR/region detection if appropriate → palette/light/texture/FX analysis → face/subject occlusion & safe zones → music/beat/voice alignment → inferred shot recipe → human spot-check → **original** replacement characters/assets/stories and licensed or original sound.

Measured vs inferred vs reviewed must stay distinct:

- **Measurable:** frame size, timestamps, brightness/edge maps, frequency response, optical flow, probable edit boundaries, typography box positions where detectable.
- **Inferred:** whether the movement is camera pan vs independently animated background, 2D-to-3D depth, original rigging method, intent of a shot and specific software used.
- **Human-verified:** real story grammar, edit classification, image/source rights, whether an animation looks natural and whether a clip is suitably differentiated.

Prior attempts to download third-party Facebook/YouTube MP4s were blocked. Some past narration/transcript summaries came from a separate agent; the actual reference-media acquisition and direct per-frame reverse engineering should remain **BLOCKED** until accessible and appropriately authorized videos are staged. `download_references.py` is an adapter, not evidence it succeeded on those URLs. Do not work around access controls.

### 3.6 Implemented original 2D stick motion composer

`baltor_motion_foundry/stick_composer/` contains original layered illustrated assets, `composer.py`, `storyboard.json`, `graph.json`, `analyze_references.py`, `quality_audit.py`, sound synthesis, and an operator catalog.

**Demonstration:** *The Last Signal* — original 70s 1080×1920/24fps vertical MP4 with audio (`outputs/the_last_signal_70s_FINAL.mp4`), 15 shots, 45 microbeats. Techniques include seven layered 2D images, camera establish/follow/push/cover/split/reveal/whip/chase/close/flare/pull/end modes, stick character posing, rain/parallax, PIP, 1×2 comparisons, signals, text and graphic framing. It is **not** a creator-specific reconstruction.

The `operator_catalog.json` once counted 185 candidate operators with 44 tagged as prototype-supported. The totals are catalog labels, not proof of 185 independent tools or 44 production-quality plug-ins. A video file and per-frame self-audit CSV exist; that analyzer's agreement with authored shot boundaries does not establish general performance on unseen videos.

### 3.7 Spatial Studio v0.2 — video layout as data

`baltor_motion_foundry/stick_composer/spatial_v02/` adds ten original visual compositions over the same underlying story. Its finished 65s MP4 is 1080×1920/24fps with audio; rendered internally at 540×960 then upscaled — **not native-resolution original art**.

**Ten layouts:** `cinematic`, `survival_hud`, `split_decision`, `forensic`, `comic`, `blueprint`, `art_deco`, `dashboard`, `quadrant`, `minimal_finale`.

**Operational systems include:**

- 15 text/container anchor positions (corners, central edges, center and upper/lower-third slots).
- Four-sided independent `padding.{top,right,bottom,left}`, margins, relative/pixel units, minimum/maximum sizes, parent-relative position, safe profiles and text-fit/wrapping.
- Layer z-order, opacity, masking, clipping, blend modes, panel dimensions, transparent cards, borders, reticles, progress bars, motion curves, word emphasis, PIP and 1×2/2×2 compositions.
- A self-contained offline HTML editor (`Baltor_Spatial_Studio_Editor.html`) with drag/select, element inspector, title and panel edits, anchor/opacity/z changes, exported JSON and PNG previews. Browser UI is an approximate preview, not an authoritative pixel-perfect renderer.
- `layouts.json`: ten working templates plus **180-field design-dimension catalog**; the full catalog is **not** 180 implemented controls.
- `spatial_graph.json`: 36-node graph, mix of implemented, prototype, planned, human-review required; inspect statuses.
- Automated geometry/layout tests (previously reported 25 passing), 65s video analysis at 1,560 frames, per-shot caption-placement heatmap. The caption-placement estimator is heuristic, not face/actor semantic collision detection.

**Normalized sample layout element** (matches structure of this project's JSON, not necessarily every field required for future engines):

```json
{
  "id": "chapter_label", "kind": "text", "layer": "typography", "z": 40,
  "box": {"space": "safe", "anchor": "top_left", "dx": 0.02, "dy": 0.05, "w": 0.75, "h": 0.12},
  "padding": {"top": 8, "right": 18, "bottom": 6, "left": 14},
  "text": "DAY 04 / THE LAST SIGNAL", "font": "bold", "font_size": 30,
  "min_font_size": 14, "max_lines": 2, "align": "left", "valign": "center",
  "color": "#F4F3E6", "background": true, "fill": "#081521D8",
  "radius": 12, "start": 0, "end": 6.5, "in": 0.2, "out": 0.3,
  "enter": "slide_up", "opacity": 1
}
```

For future expansion, treat panel compositions as responsive constraint programs, not arbitrary screen coordinates. Include subject-awareness, geometric hierarchy, exclusion masks, saliency/legibility checks, subtitle line timing, true device-preview occlusion and platform-specific reflow. Preserve a style-specific lock file so a series does not randomly vary characters, palette, geography or typography between episodes.

### 3.8 Native Baltor Harness Tools v0.3.1 — what actually runs

`baltor_harness_tools_v01/` is a Go-based closed-operator DAG runner, unlike the purely descriptive graphs in earlier projects. Linux x86-64 runnable binary tested here; Linux ARM64, macOS ARM64, Windows AMD64 binaries cross-compiled but not runtime-tested on target OSes. FFmpeg/ffprobe remain runtime dependencies for encoding/decoding/probing.

**13 implemented operator IDs:**

```text
scene.frames            audio.synth             timeline.compile
frames.transform        frames.overlay          frames.metrics
frames.spatial          frames.contact          video.encode
video.sample            video.probe              layout.lint
artifact.hash
```

**CLI entrypoints:** `catalog`, `doctor`, `validate`, `plan`, `graph`, `ingest`, `run`, `verify`, `inspect`, `diff`, `pack`. Native runs use recipe JSON, workspace-relative paths, content hashes, archived artifacts, basic limit checks, output verification and graph validation (including cycle/path traversal/invalid settings checks).

**Recipes and evidence:**

| Recipe | Demonstration | State |
|---|---|---|
| `recipes/showcase.json` | 20s 400×720/15fps audio-visual video with five original scene families | LOCAL-VERIFIED media |
| `recipes/composed.json` | Scene → camera/color stage → graphics/text stage → spatial metrics → encode | PROJECT-TESTED |
| `recipes/layered.json` | Crucial change: camera affects artwork **before** screen-fixed captions/panels/borders | LOCAL-VERIFIED media |
| `recipes/analyze_existing.json` | Sample & analyze staged existing MP4 + v0.2 layouts | PROJECT-TESTED |

A prior two-workspace repeatability test reported SHA-256 equality for 308 artifacts on one recipe and **910 artifact matches** on the 11-node layered recipe, including the MP4. This indicates deterministic execution **with the same environment and FFmpeg build**; it does not prove universal platform byte-for-byte identity. The package reported 18 tests passing; re-run after changes.

Example commands:

```bash
./bin/baltorctl-linux-amd64 validate --recipe recipes/layered.json
./bin/baltorctl-linux-amd64 plan --recipe recipes/layered.json --workspace ./work --json
./bin/baltorctl-linux-amd64 graph --recipe recipes/layered.json --out layered.dot
./bin/baltorctl-linux-amd64 run --recipe recipes/layered.json --workspace ./work --json
./bin/baltorctl-linux-amd64 verify --run ./work/runs/<run-id>
```

Consult `README.md`/binary help and actual schema for precise CLI syntax; the example `graph`/`verify` flags should be confirmed against the installed version before automation. The Docker/Containerfile defines a deny-by-default profile **but was not live executed** on OCI here.

### 3.9 Capability Distiller v0.4 — intake and preproduction, not a magic compiler

`Baltor_Capability_Distiller_v04/` includes a distinct Go binary, source, tests and four cross-built OS targets. Seven implemented commands:

| Command | Function |
|---|---|
| `scan` | Read local `SKILL.md` metadata and nearby file inventory **without executing scripts**. |
| `propose` | Generate heuristic **non-executable** operator proposal records. |
| `layout` | Validate a specified ad/spatial layout's dimensions, anchors, safe zones and overlaps. |
| `timeline` | Compile shot durations into frame slots, CSV and timed subtitle plan. |
| `variants` | Produce deterministic variant grids over specified camera/style/story parameters. |
| `hash` | Compute source/artifact SHA-256. |
| `doctor` | Show runtime/environment contract. |

**Actual reported checks:** Go tests pass (10); local scan found three Baltor skills and three non-executable candidate sets; 60s/20-shot/1,440-frame storyboard compiled; 32 variants generated. Binaries were built for Linux x86-64, Linux ARM64, macOS ARM64, Windows AMD64; only Linux x86-64 ran here.

**Catalog inventory:** `docs/RESEARCH_SOURCE_CATALOG.json`: **68 source ecosystems**. `docs/CANDIDATE_OPERATOR_REGISTRY.json`: **294 proposed operation names** (Audio 22, Code 35, Data 34, Eval 18, Motion 96, Optimization 25, Security 20, Skills 44). **Neither number is a count of newly shipped executable operations.** Full listings follow in the appendices.

### 3.10 Working original 30-second ad prototypes

`Baltor_Capability_Distiller_v04/outputs/commercial/` contains two 30s 720×1280 24fps MP4s with synthesized sound, original artwork and different design grammars:

1. **The Last Tab — Kinetic Tech:** developer overwhelmed by browser tabs → reusable capability graph → Baltor brand. Dark/kinetic interface motion and comic timing.
2. **The Last Tab — Paper Collage:** same narrative, warm paper-cut graphic language, hand-drawn diagram surfaces and editorial layout.

Neither is broadcast-ready or a full 60s emotional spot. Both lack the desired professional narration, polished character/scene animation and human editorial review. The complete 60s/20-shot cinematic concept is **storyboard only**.

### 3.11 Commercial campaign directions — Super Bowl-level ambition, genuine quality gates

The user wants **story-led, emotionally engaging, genuinely polished commercials** rather than endless software HUDs. Example campaigns from the production brief:

| Working title | Narrative | Look and key motif | CTA |
|---|---|---|---|
| *The Unseen Problem* (60s, storyboard) | Small nonprofit/research team almost misses a quiet but important signal; composable system surfaces evidence | Restrained midnight→warm dawn; recurring amber dot; no gratuitous UI first 15s | “Build once. Help everywhere.” |
| *The Last Tab* (30s, two prototype videos) | Developer opens absurd number of tabs to find one reusable AI capability | Two distinct treatments: kinetic-tech, paper collage | “Stop searching. Start building.” |
| *The Smallest Part* (60s, proposed) | Tiny reusable module travels through factory, classroom, research lab, rescue-planning center | Macro/micro 3D miniature worlds | “A capability in one world. A possibility in another.” |
| *The Wrong Alert* (45s, proposed) | Constant irrelevant agent alerts mask a consequential event | Documentary-tech thriller, time/evidence typography | “Less noise. More signal.” |
| *Let the Computer Read It* (30s, proposed) | Human as an unnecessary relay between newsletters and AI agents | Surreal paper conveyor and impossible perspectives | “Don't be the middleman between information and your AI.” |

**Professional production checklist:** hook in first 1–5s; causal character conflict and emotional stakes; one primary dramatic arc; actual art direction, recurring props, shot-size variety, camera motivated by attention/story, timing contrast and moments of silence; original licensed sound design/music and well-acted/natural narration; caption alignment at word-level when spoken; believable lighting, texture, occlusion, motion; consistent canon; authentic product demonstrations and evidence citations; multi-format true recompositions instead of stretched or center-cropped output; real 1080p master when requested, not simply upscaled low-resolution art; device safe-area verification; complete end-to-end viewing, audio loudness/clipping checks, frozen/black-frame detection, spelling/contrast review; an explicit final-asset/copy approval gate.

Automated QA is necessary but insufficient: final publication quality needs human creative assessment and proof that product claims were actually tested.

### 3.12 Additional video/animation/content series backlog

Potential original series, formats and reusable libraries gathered across these conversations:

- **Survival/serialized stories:** post-apocalyptic survival, zombies, resource scarcity, radio mysteries, decision charts, collapsing supply lines, real consequences; simple canonical stick figures, repeat motifs, location maps, gradual escalation, arcs with serialized canon.
- **Research explainers:** Particulate, Instruct-Particulate, evaluation methods, prompt injection, agent architecture, small vs large models, reliability, LLM novelty, code-graph composition, market/feed ranking and proof packs.
- **ML/visualizations:** Kaggle notebooks → animated model diagrams, neural network behavior, cluster comparison, collinearity and feature interactions, ablation summaries, model calibration, frontier discovery.
- **Creative physics:** bouncing-note music, shader oceans, rigging motions, gravity puzzles, optical illusions, spring systems, ant swarms, weather, fluids and particles.
- **Games as animation engines:** playable platformer host, zombie maze, survival.io-style battlefield, ant/snowman/drone variants, browser game recording, physics scenes, Godot/Three.js/Babylon and matching 2D/3D replays.
- **3D media:** gallery walkthroughs, cube-face storytelling, low-poly/voxel worlds, articulated mechanical parts, procedural landscapes/terrain, CAD exploding views, robots, character rigs, 3D asset turntables.
- **Software screen recordings:** browser scroll through GitHub or source code, zoom to a function, animated highlighters on exact narrated words, bug-to-fix narrative, code node assembly and graph execution. Use screen recording only where user has lawful access.
- **Education/topics:** human body, food science, language, animal biology, history, geography, tech news, scientific discoveries, plants, energy, optimization, environmental research, AI for Good.
- **Social formats:** this-vs-that comparisons, listicles, time-series chronologies, split/picture-in-picture 1×2/2×2, comic strip pans, captions over screen-recorded demos, ambient looping backgrounds, vertical shorts and separately staged long-form.
- **Ad/brand:** aspirational technology ads, humorous high-production ads, real-world emotional stakes, technical product proof, research-to-action explainers, launch teasers, verified benchmarks, community content, episodic serialized brand narratives.

**Main creative constraint:** Each variant should differ in storytelling grammar, scene design, motion, soundtrack and layout, not simply have a different palette. For image galleries, favor large unobstructed visuals and fewer non-value labels/ornamental borders.

---
## 4. Promotion, audiences, communities and distribution

### 4.1 Strategy

Build authentic topic-based communities **around useful problems**, not merely branded groups that function as advertising channels. Separate broad discovery audiences, technical specialized groups, and branded customer/support communities. Use original reproducible demonstrations and respectful community engagement; allow discussion of alternatives/competitors and follow each group's rules. Measure qualified referral/engagement/signups/accepted user actions, not just views or account counts.

The user previously reported **10+ Facebook accounts and associated pages/groups, ~500 Pinterest accounts, ~20–80+ Bluesky accounts (later 80+), some TikTok and X accounts, plus Discord/Telegram communities**. This is user-reported inventory, not connector-verified. **Do not create inauthentic engagement, flood duplicate posts, or bypass platform rate limits.** Treat accounts as permissioned entities with roles/policy/target audience, not interchangeable amplification machines. Build an approval queue and per-account allowed-frequency, privacy and audit policies.

### 4.2 Facebook group naming preference

**User specifically corrected us:** emojis must not appear **only as the first character**. Distribute them naturally **between terms and/or at the end**, while preserving searchable plain text keywords. Example: `AI Agent 🤖 Skills & Harness 🧩 Database 📚` (not just `🤖 AI Agent Skills Database`).

Suggested primary group portfolio (names are **proposals**, availability and exact Facebook activity unverified):

| Group name | Primary interest / conversion |
|---|---|
| **AI Agent 🤖 Skills & Harness 🧩 Database 📚** | Skills, harnesses, `SKILL.md`, `AGENTS.md` → Baltor library. |
| **AI Agent Skills 📚 MCP Servers 🔌 & Tools 🛠️** | Skills/MCP discovery; repeatable integration guides. |
| **MCP Servers 🔌 Tools & Skills Database 📚** | Tool servers, contracts, source comparisons, security. |
| **AI Harness 🏗️ Skills & Components Marketplace 🧩** | Rigorous source/contract/distribution. |
| **Claude Code 💻 Codex ⚡ & Cursor Skills 🧩** | Tool-specific skills/commands/hooks/rules. |
| **AI Coding Agents 🤖 Tools, Skills & Plugins 🔌** | Coding assistants, workflow reliability, cost, speed. |
| **OpenCode 🤖 Claude Code & Codex Builders 🏗️** | Harness comparison and developer education. |
| **Agent Harness Engineering ⚙️ Tools & Templates 📚** | More advanced agent developers. |
| **AI Agent Graphs 🧠 Nodes & Workflows 🔄** | Node-based orchestration and execution. |
| **Agent Skills 🧠 Database & Resource Hub 🌐** | Discovery/search and downloadable files. |
| **AI Motion Graphics 🎬 Animation & VFX ✨** | Broad creative community; visual demos. |
| **AI Motion Graphics 📚 Free Templates, Tools & Assets 🧩** | Reusable creative skills, effects, overlays, videos. |
| **Programmatic Motion Graphics 💻 AI Animation & Creative Coding 🎨** | Technical Blender/Three.js/Godot/FFmpeg/Manim audiences. |
| **AI Video Generation 🎬 Motion Graphics & VFX ✨** | Creators combining generation and deterministic editing. |
| **AI 3D Motion Graphics 🧊 Animation & VFX ✨** | Rigging, camera moves, product motion. |
| **Blender 3D 🧊 AI Animation & Motion Design 🎬** | Blender/MCP/rigging/3D tutorials. |
| **Procedural Animation 🧬 AI Graphics & 3D Worlds 🌍** | Procedural 3D and animation engines. |
| **Three.js 🌐 Babylon.js & WebGL Graphics 🎨** | Browser creative coders. |
| **AI Video Factory 🏭 Animation, Motion & VFX ⚡** | Repeatable videos and template downloads. |
| **AI Video Assets 📦 Backgrounds, Borders & Transitions 🎞️** | Asset/tool/overlay discovery. |
| **Creative Coding 💻 AI Art & Animations 🎭** | Broader procedural graphics. |
| **AI Tools 🛠️ Models 🤖 & Breakthroughs 🚀** | AgentFeeds discovery. |
| **AI News 📰 Research Papers & Benchmarks 📊** | Evidence-backed digest and research. |
| **AI Automation ⚡ Agents & Business Workflows 💼** | Business automation and AgentBriefs. |
| **AI for Good ❤️ Open Source Tools & SDGs 🌍** | Public-good collaborators and component sharing. |
| **AI Research 🔬 Papers, Models & Benchmarks 📊** | Eval researchers and Kaggle practitioners. |
| **AI Red Teaming 🛡️ LLM Safety & Evaluation 🔬** | Safe, evidence-backed research. |
| **AI Agent Reliability 🧪 Debugging & Testing ⚙️** | Fault injection, evals, production work. |
| **AI Motion Design ✨ Animation, VFX & Video Creation 🎬** | Freelance/pro motion designers. |
| **AI Social Videos 📱 Motion Graphics & Animation 🎬** | Content creators, short-form workflows. |

**Recommended initial group set** before expanding: agent skills/database, MCP/tools, coding agents, AI motion graphics, programmatic graphics, AI tools/models, business automation, and AI for Good; only operate as many as can be supported with distinctive real member value. Branded support/community: *Baltor Builders Lab*, visibly identified as vendor-run.

### 4.3 Existing external Facebook communities previously mentioned (verify live rules)

- https://www.facebook.com/groups/claudecode/
- https://www.facebook.com/groups/n8ndevelopers/
- https://www.facebook.com/groups/aibusinesstools/
- https://www.facebook.com/groups/3dartistsb/
- https://www.facebook.com/groups/godotengine/
- https://www.facebook.com/groups/IndieGameDevs/
- https://www.facebook.com/groups/ml4good/

These were cited as **potential communities**, not verified permission to promote. Always read group rules and verify the group is active before engaging. Facebook APIs have had group-publishing restrictions; do not promise direct group auto-publishing unless confirmed supported today.

### 4.4 Reusable content series and acquisition paths

Examples: *Skill of the Day*, *MCP Server Spotlight*, *Fix My Agent*, *Skill Security Review*, *Agent Battle*, *Open Source Discovery*, *Harness of the Week*, *AI Breakthrough Radar*, *Research to Production*, *Automate This*, *Overnight Build Challenge*, *30–60s Motion Graphics Breakdown*, *10 Ways to Animate It*, *2D vs 2.5D vs 3D*, *VFX Layer Breakdown*, *Free Template Friday*, *Motion Graphics of the Day*, *Physics Music*, *AI for Good Challenge*.

A single credible technical artifact may produce different **original** posts for different communities: developer operator contract, comparative performance chart, 3D motion loop, creative breakdown, accessibility/SDG use case, founder decision brief. Do not spam identical captions/links across accounts. Each post should be independently useful. Use explicit UTM/referral parameters and measure downstream action.

**Suggested funnel:** community member → original useful demo → correct narrow product landing page → inspect source/test results → try component/feed/demo → optionally save/subscribe/compose → measure value. A Facebook post is not proof a product feature is already live. Don't claim engagement, signup or conversion rates without actual analytics.

### 4.5 Distribution automation architecture (proposed)

```text
Product / research / repo / feed changes
        ↓
Evidence and rights verification
        ↓
Story & creative brief
        ↓
Native animation / screen recording / media foundries
        ↓
Caption alignment, alternate originals, multi-format render
        ↓
Automated QA → full human screening
        ↓
Explicit approval of final media **AND exact post copy**
        ↓
Permitted channel/account-specific queue (Buffer / Make / APIs where supported)
        ↓
Publish receipt / takedown controls / analytics
        ↓
Causal learning, not fake engagement
```

Where authorization permits, automate **content preparation, QA, scheduling drafts, analytics extraction and alerts**; be conservative with the act of posting. User has requested no publication without approval. Preserve a central kill switch, per-account policy and content/audience rights.

---

## 5. Research and high-impact applications

### 5.1 Safety, red teaming and the “Bad Investigator Problem”

Related work discussed in the application and research portfolio: previous work applying technology to migration/human trafficking/financial-crime prevention; GPT-OSS red teaming on concealed exploitation patterns; DueCare; responsible safety harnesses; model evaluation. A key hypothesis: models sometimes fail to identify and clearly explain consequential evidence when it is distributed across multiple individually plausible activities. Other concerns: over-refusal, harmful-enablement, provenance, synthetic benchmark contamination, weak calibration, and evaluations rewarding superficial style instead of actual harm reduction.

**Research protocol idea:** define ground-truth or expert-reviewed scenarios; compare base model, safety prompt, retrieval, deterministic tools, structured evidence extraction and composed harness; measure detection precision/recall, false positives, explanatory usefulness, harmful-enablement, calibration, latency/cost, domain transfer and robustness. Establish independent expert ratings and a clear split between development and unseen tests. Do not claim experimental results from a written proposal.

Research URLs:

- [OpenAI gpt-oss-20b red-teaming write-up](https://www.kaggle.com/competitions/openai-gpt-oss-20b-red-teaming/writeups/llm-complicity-in-modern-slavery-from-native-blind)
- [Gemma 4 Good Kaggle write-up](https://www.kaggle.com/competitions/gemma-4-good-hackathon/writeups/new-writeup-1779103293133)
- [Kaggle user profile](https://www.kaggle.com/taylorsamarel)
- [DueCare](https://tayloramareltech.github.io/duecare/)
- [LLM safety framework](https://github.com/TaylorAmarelTech/llm-safety-framework)
- [Evaluator index](https://evals.tayloramarel.com/agents.md), [evals LLM index](https://evals.tayloramarel.com/llms.txt), [evaluation JSON](https://evals.tayloramarel.com/evals.json)
- [Master portfolio machine index](https://index.tayloramarel.com/index.json)
- [Consolidated portfolio AGENTS.md](https://github.com/Amarel-Taylor-Scott/ai-safety-papers-and-monographs-2026/blob/main/AGENTS.md)
- [Fellowship application website](https://tayloramarelfellowshipapp.baltor.ai/)
- [Notebook site](https://notebooks.tayloramarel.com/), [papers](https://papers.tayloramarel.com/), [blog](https://blog.tayloramarel.com/), [blog index](https://blog.tayloramarel.com/posts/index.json), [repos](https://repos.tayloramarel.com/), [main portfolio](https://tayloramarel.com/)
- [GitHub profile](https://github.com/TaylorAmarelTech)

The user grouped research submissions into **personally polished/reviewed vs agent-managed exploratory**. Preserve those labels. `?category=polished` on a URL is the user's classification cue, **not a third-party standardized review tag**. Never imply automated portfolios were all personally reviewed or that a proposed model-based judge is an independent human expert.

### 5.2 Non-video science and SDG capability expansions

Related threads asked why frontier AI is primarily used for ordinary Q&A rather than proactively exploring material human problems, and whether LLM training/RL from public information may cause convergence on familiar solution spaces, suppressing novel dimensional parameter searches. Example question: plant growth optimized not just by adding sun/water, but by controlling microscopic/molecular inputs, energy pathways, nutrients, thermal gradients, and controlled experiment grids. The resulting *research program* must be physically plausible and safe; it should make useful hypotheses, quantify unknowns, and avoid inventing breakthroughs.

General Baltor Scientific Experiment Foundry:

1. Pick a consequential outcome and an evidence-supported model of its dependencies.
2. Construct a dimensional search space (continuous, discrete, conditional, hierarchical, latent variables).
3. Enumerate constraints, priors, budgets, safety limits, hard incompatibilities, known false assumptions, observability and measurement error.
4. Use grid/random/Sobol/Bayesian/evolutionary/sprouting/active learning where useful. Compare algorithms on held-out tasks and fixed budgets, not hype.
5. Assign cheap simulation/surrogate/analytical filters before expensive inference/physical experiments. Do not claim simulated success as real-world validation.
6. Maintain negative controls, exploration diversity, anti-convergence mechanisms, independent critics and falsifiable stopping conditions.
7. Capture every trial as a portable, inspectable `ExperimentRun` and extract reusable operators/lessons into the Baltor catalog after review.

Proposed domains: plants/agriculture, energy-grid optimization, environmental monitoring, education, humanitarian logistics, medicine/public-health research with proper oversight, scientific instrumentation, geometry/robotics, safe financial-crime/trafficking detection and explanations, open-source nonprofit tools. **Do not frame high-stakes outputs as clinically or operationally validated without actual validation.**

### 5.3 Evaluation science and continuous harness improvement

Priorities: multi-seed paired tests, regression fixtures, confidence intervals, effect-size and latency/cost profiles; evaluate *accepted outcomes*, not token savings alone. Distinguish true novelty vs remix of training/public data; measure whether a composable graph of prewritten parameterized code improves quality and reduces generated-code tokens; test generalization and search diversity, not only benchmark exploitation. Explore small specialized models for well-defined tasks, external optimizers for graph composition, benchmark grading and small-agent fingerprinting; preserve development/production rule sets.

Research candidates mentioned in the wider project history include harness self-improvement, proposed safety wrappers, fault injection, code retrieval, prompt-injection defenses, evaluation suites, generalized script/model-to-operator extraction and scheduled discovery of new models/endpoints. **Do not schedule intrusive background work or publish research without explicit authorization.**

### 5.4 Other previously discussed projects (adjacent, not necessarily media deliverables)

- CPS Technologies monitoring, defense/industrial research, enterprise insurance benchmarking and restricted floor-rule disparity analysis; high-stakes facts are outside this media handoff and require fresh sources/privacy/permissions.
- Mathematical/manifold animations, Kaggle notebook visualization, AI-related comparisons, programmatic models of small mechanisms, stock/data chronologies.
- Browser-native interactive demos, procedural landscape/simulation recreation, open-source compositor integrations.
- Various scientific design/evaluation and Red Team methodologies that can become responsibly permissioned skills, checklists, executable test fixtures and evidence packs.

---

## 6. Research tools, standards and integrations — reference map

### 6.1 Creative, 3D, audio, video and browser

Use original source pages and pinned versions; commercial licences, model weights and distributed example assets may have different rights than code. A tool being *interesting* does not mean it has already been integrated into Baltor.

| Tool/source | Starting URL | Intended extraction |
|---|---|---|
| FFmpeg / FFprobe | https://ffmpeg.org/ | Video encode, trim, xfade, compositing, loudness, audio mixing. |
| PySceneDetect | https://www.scenedetect.com/ | Shot boundary detection and candidate edit events. |
| OpenTimelineIO | https://github.com/PixarAnimationStudios/OpenTimelineIO | Timeline assembly/interchange for editor-native revisions. |
| Motion Canvas | https://github.com/motion-canvas/motion-canvas | TypeScript-based programmatic motion graphics. |
| Remotion | https://www.remotion.dev/ | React/JavaScript video composition; evaluate licence for commercial/server use. |
| Blender | https://www.blender.org/ | Headless 3D, rigging, materials, camera, rendering and compositing. |
| Three.js | https://threejs.org/ | Web 3D and procedural visuals. |
| Babylon.js | https://www.babylonjs.com/ | Interactive 3D scenes and materials. |
| Godot | https://godotengine.org/ | Game-native animation/render/physics and recording. |
| glTF Transform | https://gltf-transform.dev/ | Inspect/compress/modify GLB and glTF assets. |
| resvg | https://github.com/linebender/resvg | Deterministic SVG rasterization / titling. |
| Manim | https://www.manim.community/ | Mathematical and technical motion graphics. |
| MediaPipe | https://ai.google.dev/edge/mediapipe/solutions/guide | Pose estimation and tracking as permitted. |
| Playwright | https://playwright.dev/ | Controlled browser interactions/screenshots/recordings. |
| ComfyUI | https://github.com/comfyanonymous/ComfyUI | Node-based generative media workflows (models/weights separately reviewed). |
| n8n | https://n8n.io/ | Workflow orchestration; not a replacement for safe agent-worker isolation. |
| Huashu Art Motion | https://github.com/alchaincyf/huashu-art-motion | User-supplied programmatic art/motion candidate. |
| whisper.cpp | https://github.com/ggml-org/whisper.cpp | Local speech recognition/transcription. |
| Silero VAD | https://github.com/snakers4/silero-vad | Speech activity detection. |
| OpenCV | https://opencv.org/ | Frames, optical flow, masks, tracking, analysis. |
| PyTorch | https://pytorch.org/ | Inference/training environment for supported models. |
| Particulate | https://github.com/RuiningLi/particulate | Static mesh → joint/part inference (GPU integration pending). |
| Instruct-Particulate | https://instruct-particulate.github.io/ | Guided mesh articulation inference. |
| Articraft | https://github.com/articraftresearch/Articraft | AI-authored articulated-asset scripts; sandbox required. |
| UniMate | https://github.com/Friedrich-M/UniMate | Text-directed motion for rigged skeletons. |

Further candidates previously mentioned for verification: ManimGX, mortiflix-oss, shader/ocean/path-tracing libraries, voxel terrain generators, CascadeStudio/CAD tools, interactive glTF, Effekseer, multiple VFX/compositing implementations. Do not fabricate repo URLs for names whose exact upstream has not been confirmed.

### 6.2 Agent skills, MCP, software engineering, optimization, evaluation

| Source | URL |
|---|---|
| Agent Skills specification | https://agentskills.io/specification |
| Agent Skills repo | https://github.com/agentskills/agentskills |
| Anthropic public skills | https://github.com/anthropics/skills |
| OpenAI public skills | https://github.com/openai/skills |
| Vercel Agent Skills | https://github.com/vercel-labs/agent-skills |
| Superpowers development skills | https://github.com/obra/superpowers |
| Trail of Bits skills | https://github.com/trailofbits/skills |
| BMad Method | https://github.com/bmad-code-org/BMAD-METHOD |
| MCP reference servers | https://github.com/modelcontextprotocol/servers |
| MCP Registry | https://github.com/modelcontextprotocol/registry |
| Git | https://git-scm.com/ |
| Tree-sitter | https://github.com/tree-sitter/tree-sitter |
| ast-grep | https://github.com/ast-grep/ast-grep |
| ripgrep | https://github.com/BurntSushi/ripgrep |
| uv | https://github.com/astral-sh/uv |
| pytest | https://github.com/pytest-dev/pytest |
| Ruff | https://github.com/astral-sh/ruff |
| DuckDB | https://duckdb.org/ |
| SQLite | https://www.sqlite.org/ |
| OR-Tools | https://github.com/google/or-tools |
| Promptfoo | https://github.com/promptfoo/promptfoo |
| Inspect AI | https://github.com/UKGovernmentBEIS/inspect_ai |
| Syft SBOM | https://github.com/anchore/syft |
| Cosign | https://github.com/sigstore/cosign |
| Grype | https://github.com/anchore/grype |
| Trivy | https://github.com/aquasecurity/trivy |

**Competitive discovery context:** MCPMarket, Glama, MCP.so, Smithery, Arcade, PulseMCP, Docker MCP Catalog, Composio and official registry were previously discussed as competing/adjacent discovery platforms. Their dates, funding and counts require new verification if used in external marketing. Baltor's intended differentiation is not merely a larger list: executable qualification, cross-harness retrieval, measured outcomes, environment contracts, provenance, and reliable provisioning.

### 6.3 Local tools and isolation priorities

- **Use pinned native CLI binaries** when practical, with typed wrappers and per-command JSON Schema. Small Go/Rust/static tools are suitable for parsing, layouts, hashing, normalization, metadata extraction and simple deterministic renderers.
- **Wrap heavy Python/GPU modules** as isolated workers instead of pretending everything can be a self-contained static executable: CUDA/PyTorch models, Blender, ComfyUI, speech models, simulations and third-party engines have heavyweight dependencies and sometimes non-determinism.
- **Consider OCI, microVM, WASI** as policy-separated executor types; evaluate actual workload fit, syscalls, network/device needs and safety. A text Containerfile is not sandbox proof.
- **Secrets and side effects:** never put API keys inside skill text, model prompts, logs, public manifests or checked-in configuration; use a permissioned vault and service boundary. Writing code, contacting external services, spending money and publishing are independently gated operations.
- **Licenses and rights:** separately inspect repository source license, weights, examples, fonts, icons, sound, music, third-party footage, data and model-generated content. Some licenses impose attribution/share-alike or other limits.

---

## 7. Local deliverables and verification status (2026-10-19)

All **paths in the next tables are verified to exist in this working container** unless explicitly marked otherwise. Video metadata was read with FFprobe directly. The files may not follow another agent to a new session without explicit transfer.

### 7.1 MP4 demonstrations (checked with ffprobe)

| Duration / format | File (relative to `/mnt/data/`) | Meaning / limitation |
|---|---|---|
| 42s · 720×1280 · 24fps | `particulate_motion_demo_with_audio.mp4` | Manually authored desk-lamp kinematic motion; **not neural Particulate inference**. |
| 36s · 720×1280 · 18fps | `baltor_motion_foundry/outputs/robot_arm_motion.mp4` | JSON rigid-part robot arm. |
| 36s · 720×1280 · 18fps | `baltor_motion_foundry/outputs/twin_drawer_motion.mp4` | Sliding prismatic joints. |
| 36s · 720×1280 · 18fps | `baltor_motion_foundry/outputs/folding_chair_motion.mp4` | Folding chair revolute joints. |
| 60s · 720×1280 · 18fps | `baltor_motion_foundry/outputs/baltor_motion_foundry_60s.mp4` | Three-object montage; technically valid, not photorealistic. |
| 70s · 1080×1920 · 24fps | `baltor_motion_foundry/stick_composer/outputs/the_last_signal_70s_FINAL.mp4` | Original 2D stick survival story. |
| 65s · 1080×1920 · 24fps | `baltor_motion_foundry/stick_composer/spatial_v02/outputs/baltor_spatial_layout_study_65s_FINAL.mp4` | Ten compositions; upscaled working artwork. |
| 20s · 400×720 · 15fps | `baltor_harness_tools_v01/outputs/layered-release/runs/d987989f8d245d5b2fff/media/video.mp4` | Native Go layered DAG run. |
| 30s · 720×1280 · 24fps | `Baltor_Capability_Distiller_v04/outputs/commercial/last_tab_kinetic_30s.mp4` | Kinetic-tech advertising prototype. |
| 30s · 720×1280 · 24fps | `Baltor_Capability_Distiller_v04/outputs/commercial/last_tab_paper_30s.mp4` | Distinct paper-collage advertising prototype. |

These MP4s have audio tracks. The first two advertising proofs **do not** contain polished natural narration. An ad campaign with five-minute storytelling, voice acting, photorealism or true native 1080 master delivery remains **future work**.

### 7.2 Major packages and machine-readable inventories

| Local file/path | Contains |
|---|---|
| `BALTOR_MOTION_FOUNDRY_SOURCE.zip` | Original 3D motion foundry code and docs. |
| `Baltor_Stick_Motion_Composer_Source.zip` | Layered 2D stick survival composer. |
| `Baltor_Spatial_Motion_Composer_v02_Source.zip` | Ten-style spatial composer, editor, QA, source. |
| `Baltor_Harness_Tools_v031_Binaries_and_Source.zip` | Go DAG runner, tests, four cross-target executables. |
| `Baltor_Capability_Foundry_v04_COMPLETE.zip` | Distiller source+binaries, catalogs, commercial proofs. |
| `Baltor_Capability_Distiller_v04_Binaries_Source.zip` | Distiller executable/source package. |
| `Baltor_Original_Ad_Prototypes_30s.zip` | Original 30s ads with source. |
| `baltor_motion_foundry/docs/COMPONENT_CATALOG.json` | 132 prototype/proposal component records. |
| `baltor_motion_foundry/docs/CONTENT_RECIPES.json` | 120 original motion/content recipe candidates. |
| `baltor_motion_foundry/docs/FEATURE_STORYBOARD_300S.json` | 60 shot / 600 cue 300s **unrendered** storyboard. |
| `baltor_motion_foundry/docs/SERIES_BIBLE_3D.json` | Canonical rig/style/world continuity. |
| `baltor_motion_foundry/stick_composer/operator_catalog.json` | 185 motion-DAG catalog ideas with prototype status field. |
| `baltor_motion_foundry/stick_composer/spatial_v02/layouts.json` | Ten templates + 180-dimension catalog. |
| `baltor_motion_foundry/stick_composer/spatial_v02/spatial_graph.json` | 36-node mixed-status composition graph. |
| `baltor_motion_foundry/stick_composer/spatial_v02/Baltor_Spatial_Studio_Editor.html` | Self-contained authoring/editor UI. |
| `baltor_motion_foundry/stick_composer/spatial_v02/feature_300s_storyboard_DRAFT.md` | 40×7.5s storyboard, 400 beats — **not rendered**. |
| `baltor_harness_tools_v01/docs/OPERATOR_CONTRACTS.json` | **13 implemented** motion CLI operator contracts. |
| `baltor_harness_tools_v01/docs/OPERATOR_ROADMAP.md` | **45 unimplemented** future operations. |
| `baltor_harness_tools_v01/recipes/layered.json` | Data-driven post-render layer separation. |
| `Baltor_Capability_Distiller_v04/docs/RESEARCH_SOURCE_CATALOG.json` | **68** external source ecosystems. |
| `Baltor_Capability_Distiller_v04/docs/CANDIDATE_OPERATOR_REGISTRY.json` | **294** proposed operator names, **not implemented**. |
| `Baltor_Capability_Distiller_v04/docs/IMPLEMENTED_CONTRACTS.json` | **7 implemented** v0.4 CLI commands. |
| `Baltor_Capability_Distiller_v04/docs/DISTILLATION_PLAYBOOK.md` | Skill-to-binary promotion and trust-boundary methodology. |
| `Baltor_Capability_Distiller_v04/examples/flagship_superbowl_style_storyboard.json` | **Unrendered** 60s/20-shot cinematic brief. |
| `Baltor_Capability_Distiller_v04/examples/ad_campaign_variants.json` | Variant generation dimensions. |
| `Baltor_Capability_Distiller_v04/docs/AD_PRODUCTION_SYSTEM.md` | Five distinct campaign narratives and QA standards. |
| `Baltor_Capability_Distiller_v04/outputs/RELEASE_QA.json` | Historical v0.4 test/media audit record. |
| `Pasted text(20261019-020911).txt` | Attached prior Muse conversation transcript, including Stickvival/video-bank ideas and **unverified** claims. |
| `Pasted text(20261018-202008).txt` | Attached application/portfolio conversation; research links and agent discovery. |

### 7.3 Cross-platform binaries present

- `baltor_harness_tools_v01/bin/baltorctl-linux-amd64`
- `baltor_harness_tools_v01/bin/baltorctl-linux-arm64`
- `baltor_harness_tools_v01/bin/baltorctl-darwin-arm64`
- `baltor_harness_tools_v01/bin/baltorctl-windows-amd64.exe`
- `Baltor_Capability_Distiller_v04/bin/baltor-distill-linux-amd64`
- `Baltor_Capability_Distiller_v04/bin/baltor-distill-linux-arm64`
- `Baltor_Capability_Distiller_v04/bin/baltor-distill-darwin-arm64`
- `Baltor_Capability_Distiller_v04/bin/baltor-distill-windows-amd64.exe`

Cross-platform **build output exists**; execution on Apple Silicon, Windows or Linux ARM64 remains untested in this session. Native source is in the associated packages; requires a compatible host/runtime and FFmpeg for actual media jobs.

---

## 8. Immediate engineering work orders — prioritized

Each work order must produce (i) reproducible source, (ii) at least one working output, (iii) tests, (iv) a status/provenance manifest, (v) a rollback path, and (vi) no publishing without exact user approval.

| ID / Priority | Work order | Implementation & acceptance |
|---|---|---|
| **P0-01** | Unified capability registry | Merge 13 motion ops and 7 distiller commands into one **namespaced** schema, preserve distinct implementations; no duplicate ID collisions; validate all old recipes. |
| **P0-02** | Deterministic stage caching | Per-node canonical parameter/asset/tool hash; resuming a failed DAG only reruns affected nodes. Repeated builds produce exactly equal outputs on pinned host. |
| **P0-03** | Strict OCI sandbox validation | Deploy and **execute** a minimal native worker in real Docker/Podman/microVM, no network or extra privileges, bounded mounts/memory/CPU/pids; adversarial path and fork tests. |
| **P0-04** | Typed FFmpeg adapter pack | Deliver `video.cut`, `video.xfade`, `video.crop_reframe`, `audio.duck`, `audio.loudness`, `subtitle.burn` with input validation/escape-safe exec and golden media fixtures. |
| **P0-05** | Reference-media intake | Support authorized local MP4, source URL, rights status and source hashes; annotate **five actual shots** across ≥3 acquired references before inferring creator-specific grammar. |
| **P0-06** | Scene and camera analyzer | Optical flow, candidate cut/fade/zoom/pan/shake, subject movement separation, confidence & per-clip QA; benchmark against manually labeled originals. |
| **P0-07** | Text placement QA | Saliency/subject masks, text-box OCR/contrast, occlusion risk, responsive safe-zone reflow; measure false-clear rate over selected frames. |
| **P0-08** | Full-res independent art/graphics | Native 1080×1920 source artwork, not an upscale; retain scene graph, UI anchors and masks; master graphics after camera stage. |
| **P0-09** | Audio/narration | Local/naturally voiced speech option, explicit model licensing, word timing, music ducking, Foley and loudness QA. Compare naturalness with human approval. |
| **P0-10** | One genuinely finished 60s brand story | Choose *The Unseen Problem* or *The Smallest Part*; implement ≤20 primary shots, adequate sub-beats, actors/sets, original score, voice, coherent story, exact release checks; render both portrait and re-composed landscape. |
| **P1-11** | Particulate GPU inference test | Pin official repo/checkpoint/environment; run 2–3 permissively licensed meshes; inspect outputs, ground truth, geometry mapping and URDF/GLB conversion; compare with authored rigs. |
| **P1-12** | Articraft isolated importer | Review generated Python, run only in sandbox, output articulated rig/mesh with hashes, test rig constraints, license provenance and GLB/MJCF exporter. |
| **P1-13** | UniMate on approved rig | Rig preprocess, checkpoint test, seed-controlled replicates, motion quality and animation-to-mesh export; report failure rate and licensing. |
| **P1-14** | Browser-video node | Controlled WebGL/Three.js or Godot captures; preserve scene source, deterministic inputs, stage sync and reproducibility class. |
| **P1-15** | OpenTimelineIO exporter | Export editable timeline of clips/cuts/audio/stills/titles; round-trip validation in a supported editor. |
| **P1-16** | Real SKILL.md distillation | Select 5 reviewed skills; implement ≥3 **new real binaries/adapters**, not merely proposals; golden tests, permissions, license, docs. |
| **P1-17** | Skill source security intake | Source signing/SBOM, prompt-injection scanning, side-effect classification, environment fingerprints, trusted/untrusted quarantine. |
| **P1-18** | Comparative tool ranking | Benchmark 3 implementations of the same bounded operation across correctness, peak RSS, latency, dependency weight, reproducibility and licensing. |
| **P1-19** | Original serialized 300s movie | Develop the 40/60-shot draft into a full rendered episode with canonical characters/environment, narration, SFX, continuity and detailed human QA. |
| **P1-20** | Private history archive importer | Authorized full export; coverage receipts, URL/idea/asset dedup, source provenance, gaps. No claim of total-history ingestion until coverage proven. |
| **P2-21** | AgentBriefs verified action loop | Personal context → relevant change → research → isolated test → evidence threshold → approval-based notification. |
| **P2-22** | SDG experiment grid foundry | Scoped scientific benchmarks, multidimensional parameter schema, optimizer comparisons, negative controls, reproducibility receipts. |
| **P2-23** | Media campaign batch generator | Variation design from preapproved script/asset set, human selection, independent graphic compositions and approved publishing queue. |
| **P2-24** | Search/feeds evidence ranking | Indexed tool/libraries/MCP/skills/capabilities and decision feeds; keep source/quality/rights/coverage/version separate. |

### Recommended next-agent first execution

A sensible **bounded first engineering increment** is P0-04, typed FFmpeg effects/audio wrappers, because it materially increases the video DAG's composability while keeping input/output checks deterministic and minimizing GPU/model dependencies. Use the existing v0.3.1 Go runner as baseline; choose 2–3 operations, implement with strongly typed parameters and fixtures, generate an original 20–60s proof MP4, then run tests and record hashes/versions. Alternative P0-01 is a prerequisite if the runner/Distiller registry must be unified before any adapter is added.

### Definition of Done — any new operator

```text
[ ] Source/owner/rights recorded; upstream link and pinned version
[ ] Exact semantic contract + schema + side effects + cost class
[ ] Resource/permission model; no arbitrary execution or network by default
[ ] Deterministic or non-deterministic status accurately classified
[ ] Working implementation or narrow existing-tool adapter
[ ] Valid and invalid fixture tests, baseline comparator, errors
[ ] Execution trace, byte counts, SHA-256s, environment fingerprint
[ ] Reproducibility re-run where achievable; explain differences
[ ] Compiled/tested only on OSes actually named as tested
[ ] Security/license/attribution and artifact provenance checks
[ ] Docs and usable examples; if video, actual playable MP4
[ ] Human review and explicit publication gate
```

---

## 9. Handoff checklists and operating rules for the receiving agent

### 9.1 Technical startup

1. Import this Markdown and any companion source ZIPs. Map all `sandbox:/mnt/data` or absolute container paths to the new machine's actual directories; log missing files.
2. Identify runtime OS and capabilities: Go, Python, FFmpeg/FFprobe, Blender, Node, Chromium/Playwright, Docker/Podman/VM, CUDA/GPU, disk and available rights/licenses.
3. Read `baltor_harness_tools_v01/README.md`, `docs/OPERATOR_CONTRACTS.json`, recipes and tests; run `doctor`, `validate`, and one pinned known-good video recipe.
4. Read `Baltor_Capability_Distiller_v04/README.md`, `AGENTS.md`, contracts, source registry, candidate registry and tests; run `doctor`, `scan` on a benign fixture, `timeline` and `variants`.
5. Run `ffprobe` on provided MP4s; inspect at least first/middle/last frames and listen to full audio before claiming polished output.
6. Reconcile graph status (`implemented` vs `candidate`) and key release artifact SHA-256s. Use archived manifests; never invent missing hashes.
7. Begin next selected work order in a fresh versioned branch/output directory; never overwrite prior verified masters or the user's source assets.

### 9.2 Design-quality rules

- Narrative before decorations; use minimal labels and clear subject. Avoid a generic dashboard overlay on every shot.
- Protect text from face/character/prop/action regions and platform UI, allow 1–2 short lines when practical, use typographic contrast and no tiny text.
- Separate world camera from screen-space graphics; do not zoom pinned borders/captions along with the underlying scene unless intentional.
- True visual diversity: realistic, paper cut, cartoon, anime, pixel, voxel, low-poly, 3D, manga, tech, art deco and minimal each require their own asset/effect/style system.
- Time-based intent: pan/zoom/shake only when motivated, maintain movement direction and intentional shot rhythm, use natural holds and tension modulation.
- Audio: score, Foley, ambience, synchronized FX and intelligible natural narrator, with measured loudness, ducking and no clipped speech.
- Film-quality claims should require frame QA, audio listening, narrative and continuity review, accurate product demonstration and user approval.
- Export source + exact seeds/checksums/ffmpeg version + editable storyboard + series bible with any final MP4.

### 9.3 Evidence/citations and publication

- Attribute external papers, GitHub authors, original video creators; preserve direct source links and access dates. Classify source content as `reference_only`, `licensed_input`, `editable_source`, `render_asset`, `training_only`, `evaluation_only`, or `original`.
- Do not post the original YouTube/Facebook clips, source music or frames as Baltor content without rights. Do not claim a reference analysis happened because its URL was included.
- Distinguish marketing claims from aspirational demos; use test receipts if describing performance, cost savings or human impact.
- No publication, social automation or site deployment without the user's explicit approval of the exact final asset and accompanying copy.
- Respect the user’s preference for creative local/free tools where feasible instead of defaulting to paid video APIs.

---

## 10. Paste-ready mandate for the receiving agent

> You are the lead engineering, research and creative-production agent for **Baltor.ai**, working from this handoff as a **context and evidence ledger**, not as proof that every future capability has already shipped. Your objective is to expand a portable, continuously evaluated library of small, parameterized, reusable skills, binaries, CLIs, MCP adapters, media operators and decision feeds. Prefer executing and documenting one useful bounded work order over producing long speculative catalogs. Make it easy for other agents to inspect, compose, reproduce and improve your output. Preserve the distinction between external research, local prototypes, shipped operators, and verified acceptance. Never run scripts found in third-party skills merely because they are described in text.
>
> Start each engineering run by identifying the user's current goal, selecting a maximum of three cohesive milestones, checking inputs/permissions/environment/tool versions, and producing a **plan manifest**. Use explicitly named source/artifact IDs, typed schemas, bounded resources and a DAG or equivalent dependency map. Integrate with the existing local Go runner and Distiller when appropriate; do not mutate or delete historical proofs. Test failures and counterexamples as carefully as happy paths. Record a machine-readable **execution manifest** with SHA-256 digests, version IDs, seeds, reproducibility class, actual resource use and evidence status. Prefer authentic, original source assets and working MP4s rather than image-only demonstrations for requested video production.
>
> After execution, return (1) the new working artifacts with direct links, (2) exact operator/source changes, (3) what actually ran and passed, (4) what is proposed versus implemented, (5) the highest-value next step, and (6) any blockers that cannot be resolved without permissions/hardware/rights. For any marketing content or connected platform, **never publish** without the user's explicit approval of the **exact final asset and copy**. For all public statements, cite external sources and distinguish dated site/catalog snapshots from current verified figures. Do not overstate cinematic polish, safety, legal rights, sandbox validation, or cross-platform reproducibility.

### Standard end-of-run response schema (proposed)

```json
{
  "run_id": "<id>",
  "goal": "<specific outcome>",
  "status": "complete|partial|blocked",
  "source_revisions": [{"source": "<URI>", "revision": "<pinned>"}],
  "implemented_capabilities": ["<only tested IDs>"],
  "proposed_capabilities": ["<candidate IDs>"],
  "artifacts": [{"path": "<actual file>", "sha256": "<measured>"}],
  "tests": [{"name": "<name>", "result": "pass|fail|not_run"}],
  "restrictions": {"published": false, "human_approval_required": true},
  "blockers": [],
  "recommended_next_work_order": "P0-04"
}
```

---

## Appendix A — The 68 source ecosystems from v0.4 (complete local catalog)
**Status of every row: candidate research, NOT proof of adapter integration.** Source URLs are transcribed from the local JSON catalog; licenses and external project contents must be checked per version. Priority `P1/P2/P3` is the candidate ranking in that catalog, not a release state.

### A.Audio — 6 sources
| Source/project | Runtime | Candidate capability examples | Priority |
|---|---|---|---|
| [aubio](https://github.com/aubio/aubio) | `native_cli` | `audio.pitch`, `audio.beat`, `audio.onset.aubio`, `audio.silence` | P2 |
| [librosa](https://github.com/librosa/librosa) | `python_lib` | `audio.tempo`, `audio.onset`, `audio.beats`, `audio.spectral`, `audio.features` | P2 |
| [Rubber Band](https://breakfastquay.com/rubberband/) | `native_cli` | `audio.time_stretch`, `audio.pitch_shift`, `audio.transient_preserve` | P2 |
| [Silero VAD](https://github.com/snakers4/silero-vad) | `onnx_model` | `audio.vad`, `audio.speech_regions`, `audio.silence_trim` | P2 |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | `native_model_binary` | `speech.transcribe`, `speech.segment`, `speech.translate`, `speech.confidence` | P2 |
| [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M) | `model_worker` | `audio.tts`, `audio.voice.select`, `audio.tts.batch` | P3 |

### A.Code — 9 sources
| Source/project | Runtime | Candidate capability examples | Priority |
|---|---|---|---|
| [ast-grep](https://github.com/ast-grep/ast-grep) | `native_cli` | `code.ast.search`, `code.ast.replace`, `code.ast.lint`, `code.ast.query` | P1 |
| [Git](https://git-scm.com/docs/git) | `native_cli` | `repo.diff`, `repo.history`, `repo.worktree`, `repo.blame` | P1 |
| [Pytest](https://github.com/pytest-dev/pytest) | `python_cli` | `test.collect`, `test.run`, `test.junit_export`, `test.failures` | P1 |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | `native_cli` | `repo.search`, `repo.files`, `repo.regex_matches`, `repo.ignore_aware` | P1 |
| [Ruff](https://github.com/astral-sh/ruff) | `native_cli` | `python.lint`, `python.format`, `python.imports`, `python.rules.audit` | P1 |
| [Tree-sitter](https://github.com/tree-sitter/tree-sitter) | `native_parser` | `code.parse`, `code.syntax_tree`, `code.symbols`, `code.complexity_features`, `code.dependency_edges` | P1 |
| [uv](https://github.com/astral-sh/uv) | `native_cli` | `python.env.lock`, `python.script.run`, `python.tool.resolve`, `python.package.audit` | P1 |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | `native_cli` | `repo.secrets.scan`, `repo.secrets.redact`, `repo.leak.report` | P2 |
| [Semgrep](https://github.com/semgrep/semgrep) | `cli_engine` | `code.semgrep.scan`, `code.security.findings`, `code.rule.quality` | P2 |

### A.Data — 9 sources
| Source/project | Runtime | Candidate capability examples | Priority |
|---|---|---|---|
| [DuckDB](https://duckdb.org/docs/stable/clients/cli/overview) | `native_cli` | `data.query`, `data.csv_to_parquet`, `data.aggregate`, `data.dedupe`, `data.validate` | P1 |
| [SQLite](https://sqlite.org/cli.html) | `native_cli` | `db.query`, `db.migrate`, `db.index`, `db.integrity`, `db.export` | P1 |
| [Apache Arrow](https://arrow.apache.org/) | `native_lib` | `data.arrow.convert`, `data.schema.validate`, `data.columnar.write` | P2 |
| [MarkItDown](https://github.com/microsoft/markitdown) | `python_cli` | `document.markdown.convert`, `document.metadata.extract`, `document.batch_extract` | P2 |
| [NetworkX](https://github.com/networkx/networkx) | `python_lib` | `graph.components`, `graph.centrality`, `graph.shortest_path`, `graph.layout` | P2 |
| [Polars](https://github.com/pola-rs/polars) | `python_rust` | `data.lazy_transform`, `data.group`, `data.join`, `data.profile` | P2 |
| [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) | `python_native` | `text.fuzzy_match`, `text.deduplicate`, `text.similarity` | P2 |
| [Trafilatura](https://github.com/adbar/trafilatura) | `python_cli` | `web.article.extract`, `web.links.extract`, `web.metadata`, `web.cleantext` | P2 |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | `python_cli` | `video.reference.metadata`, `video.reference.download_authorized`, `video.reference.subtitles` | P2 |

### A.Eval — 4 sources
| Source/project | Runtime | Candidate capability examples | Priority |
|---|---|---|---|
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | `python_framework` | `eval.inspect.run`, `eval.scorers`, `eval.sample.trace`, `eval.model.compare`, `eval.dataset` | P1 |
| [Promptfoo](https://github.com/promptfoo/promptfoo) | `cli_framework` | `eval.dataset.run`, `eval.agent.redteam`, `eval.report`, `eval.baselines`, `eval.testcase.generate` | P1 |
| [Garak](https://github.com/NVIDIA/garak) | `python_cli` | `eval.probes`, `eval.detectors`, `eval.safety_report`, `eval.batch` | P2 |
| [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | `python_framework` | `eval.lm_bench`, `eval.task_suite`, `eval.metrics`, `eval.model_matrix` | P2 |

### A.Motion — 18 sources
| Source/project | Runtime | Candidate capability examples | Priority |
|---|---|---|---|
| [Blender](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) | `headless_app` | `blender.scene.build`, `blender.camera.animate`, `blender.material.apply`, `blender.render.frames`, `blender.render.turntable`, `blender.export.glb`, `blender.compositor` | P1 |
| [FFmpeg](https://ffmpeg.org/ffmpeg-filters.html) | `native_binary` | `video.xfade`, `video.zoompan`, `video.crop`, `video.concat`, `video.scale`, `video.stabilize`, `video.subtitle.burn`, `video.palette`, `video.framerate`, `video.encode`, `audio.duck`, `audio.loudnorm`, `audio.mix`, `audio.fade` | P1 |
| [glTF Transform](https://github.com/donmccurdy/glTF-Transform) | `node_cli` | `gltf.inspect`, `gltf.optimize`, `gltf.simplify`, `gltf.compress`, `gltf.partition`, `gltf.texture.optimize` | P1 |
| [OpenCV](https://github.com/opencv/opencv) | `native_python` | `vision.flow`, `vision.motion_segments`, `vision.track`, `vision.feature_match`, `vision.camera_hint`, `vision.edge`, `vision.histogram` | P1 |
| [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | `python_adapter` | `timeline.read`, `timeline.write`, `timeline.validate`, `timeline.merge`, `timeline.export_edl` | P1 |
| [Playwright](https://github.com/microsoft/playwright) | `browser_worker` | `browser.screenshot`, `browser.record`, `browser.trace`, `browser.scroll_capture`, `browser.layout.measure`, `browser.dom.snapshot` | P1 |
| [PySceneDetect](https://www.scenedetect.com/docs/cli.html) | `python_cli` | `shots.content_detect`, `shots.adaptive_detect`, `shots.fade_detect`, `shots.split`, `shots.keyframes` | P1 |
| [resvg](https://github.com/linebender/resvg) | `rust_native_cli` | `svg.rasterize`, `svg.check`, `svg.thumbnail`, `graphics.overlay.render` | P1 |
| [Godot](https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html) | `headless_app` | `game.scene.render`, `game.physics.simulate`, `game.assets.import`, `game.capture`, `game.headless.test` | P2 |
| [ImageMagick](https://imagemagick.org/) | `native_cli` | `image.compose`, `image.resize`, `image.trim`, `image.montage`, `image.compare` | P2 |
| [Manim](https://github.com/ManimCommunity/manim) | `python_renderer` | `math.scene.render`, `math.axes.animate`, `math.formula.transition`, `math.chart.animate`, `math.geometry.visualize`, `math.explainer.sequence` | P2 |
| [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) | `node_cli` | `diagram.flowchart`, `diagram.sequence`, `diagram.export_svg`, `diagram.export_png` | P2 |
| [Motion Canvas](https://github.com/motion-canvas/motion-canvas) | `node_renderer` | `motioncanvas.scene.render`, `motioncanvas.vector.animate`, `motioncanvas.timeline`, `motioncanvas.graphs` | P2 |
| [Sharp](https://github.com/lovell/sharp) | `node_native` | `image.batch_resize`, `image.transcode`, `image.composite`, `image.metadata` | P2 |
| [trimesh](https://github.com/mikedh/trimesh) | `python_lib` | `mesh.inspect`, `mesh.repair`, `mesh.measure`, `mesh.slice`, `mesh.export` | P2 |
| [Instruct-Particulate](https://instruct-particulate.github.io/) | `model_worker` | `rig.instruct.predict`, `rig.instruct.constraints` | P3 |
| [Particulate](https://github.com/RuiningLi/particulate) | `cuda_model` | `rig.particulate.predict`, `rig.particulate.export_urdf`, `rig.particulate.export_glb` | P3 |
| [Remotion](https://www.remotion.dev/docs/) | `node_renderer` | `remotion.render`, `remotion.composition`, `remotion.props.variant`, `remotion.snapshot` | P3 |

### A.Optimization — 6 sources
| Source/project | Runtime | Candidate capability examples | Priority |
|---|---|---|---|
| [Google OR-Tools](https://github.com/google/or-tools) | `native_solver` | `opt.assignment`, `opt.schedule`, `opt.knapsack`, `opt.routing`, `opt.cp_sat`, `opt.min_cost_flow` | P1 |
| [Optuna](https://github.com/optuna/optuna) | `python_lib` | `opt.search`, `opt.prune`, `opt.study`, `opt.pareto`, `opt.parameter_grid` | P1 |
| [PyPSA](https://github.com/PyPSA/PyPSA) | `python_model` | `sdg.grid.optimize`, `sdg.energy_balance`, `sdg.scenario_compare` | P2 |
| [RDKit](https://github.com/rdkit/rdkit) | `native_python` | `chem.molecule.validate`, `chem.descriptors`, `chem.substructure`, `chem.conformers` | P2 |
| [SciPy](https://github.com/scipy/scipy) | `python_native` | `opt.nonlinear`, `opt.root`, `opt.integrate`, `opt.stats` | P2 |
| [OpenMM](https://github.com/openmm/openmm) | `native_gpu` | `molecular.energy`, `dynamics.simulate`, `molecular.forcefield` | P3 |

### A.Security — 6 sources
| Source/project | Runtime | Candidate capability examples | Priority |
|---|---|---|---|
| [Cosign](https://github.com/sigstore/cosign) | `native_cli` | `artifact.sign`, `artifact.verify`, `artifact.attest`, `oci.verify` | P1 |
| [Syft](https://github.com/anchore/syft) | `native_cli` | `artifact.sbom`, `artifact.dependencies`, `artifact.license_inventory`, `artifact.provenance` | P1 |
| [Grype](https://github.com/anchore/grype) | `native_cli` | `artifact.vulnerability.scan`, `artifact.advisory.matches`, `artifact.remediation` | P2 |
| [OPA](https://github.com/open-policy-agent/opa) | `native_cli` | `policy.rego.eval`, `policy.deny`, `policy.constraints` | P2 |
| [Trivy](https://github.com/aquasecurity/trivy) | `native_cli` | `container.vuln.scan`, `repo.config.scan`, `artifact.license.scan` | P2 |
| [Wasmtime](https://github.com/bytecodealliance/wasmtime) | `wasm_runtime` | `wasm.module.run`, `wasm.component.validate`, `wasm.fuel_bound` | P2 |

### A.Skills — 10 sources
| Source/project | Runtime | Candidate capability examples | Priority |
|---|---|---|---|
| [Agent Skills Specification](https://github.com/agentskills/agentskills) | `metadata_rules` | `skill.frontmatter.validate`, `skill.inventory`, `skill.schema.emit`, `skill.lint`, `skill.provenance` | P1 |
| [Anthropic Skills](https://github.com/anthropics/skills) | `skill_library` | `skill.workflow.extract`, `skill.script.inventory`, `skill.templates.index`, `skill.fixtures.plan` | P1 |
| [MCP Reference Servers](https://github.com/modelcontextprotocol/servers) | `mcp_servers` | `mcp.filesystem.read`, `mcp.git.inspect`, `mcp.fetch.extract`, `mcp.tool.catalog`, `mcp.tool.schema` | P1 |
| [Official MCP Registry](https://github.com/modelcontextprotocol/registry) | `api_registry` | `mcp.registry.discover`, `mcp.registry.metadata`, `mcp.registry.version`, `mcp.registry.dedupe`, `mcp.registry.classify` | P1 |
| [OpenAI Skills](https://github.com/openai/skills) | `skill_library` | `skill.workflow.test`, `skill.readme.generate`, `skill.cli_contract.propose`, `skill.agents_yaml.describe` | P1 |
| [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) | `skill_library` | `workflow.prd.validate`, `workflow.architecture.audit`, `workflow.story.compile`, `workflow.testplan`, `workflow.requirement_trace` | P2 |
| [Superpowers](https://github.com/obra/superpowers) | `skill_library` | `workflow.red_green_refactor`, `workflow.checkpoint`, `workflow.baseline_eval`, `workflow.verification` | P2 |
| [Trail of Bits Skills](https://github.com/trailofbits/skills) | `skill_library` | `security.review.plan`, `security.issue_triage`, `security.rule_check`, `security.test_harness` | P2 |
| [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) | `skill_library` | `skill.react.rules`, `web.performance.audit`, `web.patterns.check`, `web.accessibility.rules` | P2 |
| [Vercel Skills CLI](https://github.com/vercel-labs/skills) | `node_cli` | `skill.package.discover`, `skill.package.install_plan`, `skill.package.diff`, `skill.package.inventory` | P2 |


## Appendix B — All 294 proposed v0.4 operator IDs (complete local candidate registry)
**WARNING:** Every operator in this section is `PROPOSAL_ONLY_NOT_EXECUTABLE`. There may be conceptual duplicates and implementation mismatches. This index is useful for work-order selection and deduplication, not invocation.

### B.Audio — 22 proposed IDs

- `audio.beat` — **aubio**; P2; execution class `algorithmic_local`. Source: https://github.com/aubio/aubio
- `audio.beats` — **librosa**; P2; execution class `algorithmic_local`. Source: https://github.com/librosa/librosa
- `audio.features` — **librosa**; P2; execution class `algorithmic_local`. Source: https://github.com/librosa/librosa
- `audio.onset` — **librosa**; P2; execution class `algorithmic_local`. Source: https://github.com/librosa/librosa
- `audio.onset.aubio` — **aubio**; P2; execution class `algorithmic_local`. Source: https://github.com/aubio/aubio
- `audio.pitch` — **aubio**; P2; execution class `algorithmic_local`. Source: https://github.com/aubio/aubio
- `audio.pitch_shift` — **Rubber Band**; P2; execution class `algorithmic_local`. Source: https://breakfastquay.com/rubberband/
- `audio.silence` — **aubio**; P2; execution class `algorithmic_local`. Source: https://github.com/aubio/aubio
- `audio.silence_trim` — **Silero VAD**; P2; execution class `model_inference`. Source: https://github.com/snakers4/silero-vad
- `audio.spectral` — **librosa**; P2; execution class `algorithmic_local`. Source: https://github.com/librosa/librosa
- `audio.speech_regions` — **Silero VAD**; P2; execution class `model_inference`. Source: https://github.com/snakers4/silero-vad
- `audio.tempo` — **librosa**; P2; execution class `algorithmic_local`. Source: https://github.com/librosa/librosa
- `audio.time_stretch` — **Rubber Band**; P2; execution class `algorithmic_local`. Source: https://breakfastquay.com/rubberband/
- `audio.transient_preserve` — **Rubber Band**; P2; execution class `algorithmic_local`. Source: https://breakfastquay.com/rubberband/
- `audio.tts` — **Kokoro TTS**; P3; execution class `model_inference`. Source: https://huggingface.co/hexgrad/Kokoro-82M
- `audio.tts.batch` — **Kokoro TTS**; P3; execution class `model_inference`. Source: https://huggingface.co/hexgrad/Kokoro-82M
- `audio.vad` — **Silero VAD**; P2; execution class `model_inference`. Source: https://github.com/snakers4/silero-vad
- `audio.voice.select` — **Kokoro TTS**; P3; execution class `model_inference`. Source: https://huggingface.co/hexgrad/Kokoro-82M
- `speech.confidence` — **whisper.cpp**; P2; execution class `model_inference`. Source: https://github.com/ggml-org/whisper.cpp
- `speech.segment` — **whisper.cpp**; P2; execution class `model_inference`. Source: https://github.com/ggml-org/whisper.cpp
- `speech.transcribe` — **whisper.cpp**; P2; execution class `model_inference`. Source: https://github.com/ggml-org/whisper.cpp
- `speech.translate` — **whisper.cpp**; P2; execution class `model_inference`. Source: https://github.com/ggml-org/whisper.cpp

### B.Code — 35 proposed IDs

- `code.ast.lint` — **ast-grep**; P1; execution class `deterministic_local`. Source: https://github.com/ast-grep/ast-grep
- `code.ast.query` — **ast-grep**; P1; execution class `deterministic_local`. Source: https://github.com/ast-grep/ast-grep
- `code.ast.replace` — **ast-grep**; P1; execution class `deterministic_local`. Source: https://github.com/ast-grep/ast-grep
- `code.ast.search` — **ast-grep**; P1; execution class `deterministic_local`. Source: https://github.com/ast-grep/ast-grep
- `code.complexity_features` — **Tree-sitter**; P1; execution class `deterministic_local`. Source: https://github.com/tree-sitter/tree-sitter
- `code.dependency_edges` — **Tree-sitter**; P1; execution class `deterministic_local`. Source: https://github.com/tree-sitter/tree-sitter
- `code.parse` — **Tree-sitter**; P1; execution class `deterministic_local`. Source: https://github.com/tree-sitter/tree-sitter
- `code.rule.quality` — **Semgrep**; P2; execution class `algorithmic_local`. Source: https://github.com/semgrep/semgrep
- `code.security.findings` — **Semgrep**; P2; execution class `algorithmic_local`. Source: https://github.com/semgrep/semgrep
- `code.semgrep.scan` — **Semgrep**; P2; execution class `algorithmic_local`. Source: https://github.com/semgrep/semgrep
- `code.symbols` — **Tree-sitter**; P1; execution class `deterministic_local`. Source: https://github.com/tree-sitter/tree-sitter
- `code.syntax_tree` — **Tree-sitter**; P1; execution class `deterministic_local`. Source: https://github.com/tree-sitter/tree-sitter
- `python.env.lock` — **uv**; P1; execution class `environment_sensitive`. Source: https://github.com/astral-sh/uv
- `python.format` — **Ruff**; P1; execution class `deterministic_local`. Source: https://github.com/astral-sh/ruff
- `python.imports` — **Ruff**; P1; execution class `deterministic_local`. Source: https://github.com/astral-sh/ruff
- `python.lint` — **Ruff**; P1; execution class `deterministic_local`. Source: https://github.com/astral-sh/ruff
- `python.package.audit` — **uv**; P1; execution class `environment_sensitive`. Source: https://github.com/astral-sh/uv
- `python.rules.audit` — **Ruff**; P1; execution class `deterministic_local`. Source: https://github.com/astral-sh/ruff
- `python.script.run` — **uv**; P1; execution class `environment_sensitive`. Source: https://github.com/astral-sh/uv
- `python.tool.resolve` — **uv**; P1; execution class `environment_sensitive`. Source: https://github.com/astral-sh/uv
- `repo.blame` — **Git**; P1; execution class `deterministic_local`. Source: https://git-scm.com/docs/git
- `repo.diff` — **Git**; P1; execution class `deterministic_local`. Source: https://git-scm.com/docs/git
- `repo.files` — **ripgrep**; P1; execution class `deterministic_local`. Source: https://github.com/BurntSushi/ripgrep
- `repo.history` — **Git**; P1; execution class `deterministic_local`. Source: https://git-scm.com/docs/git
- `repo.ignore_aware` — **ripgrep**; P1; execution class `deterministic_local`. Source: https://github.com/BurntSushi/ripgrep
- `repo.leak.report` — **Gitleaks**; P2; execution class `deterministic_local`. Source: https://github.com/gitleaks/gitleaks
- `repo.regex_matches` — **ripgrep**; P1; execution class `deterministic_local`. Source: https://github.com/BurntSushi/ripgrep
- `repo.search` — **ripgrep**; P1; execution class `deterministic_local`. Source: https://github.com/BurntSushi/ripgrep
- `repo.secrets.redact` — **Gitleaks**; P2; execution class `deterministic_local`. Source: https://github.com/gitleaks/gitleaks
- `repo.secrets.scan` — **Gitleaks**; P2; execution class `deterministic_local`. Source: https://github.com/gitleaks/gitleaks
- `repo.worktree` — **Git**; P1; execution class `deterministic_local`. Source: https://git-scm.com/docs/git
- `test.collect` — **Pytest**; P1; execution class `algorithmic_local`. Source: https://github.com/pytest-dev/pytest
- `test.failures` — **Pytest**; P1; execution class `algorithmic_local`. Source: https://github.com/pytest-dev/pytest
- `test.junit_export` — **Pytest**; P1; execution class `algorithmic_local`. Source: https://github.com/pytest-dev/pytest
- `test.run` — **Pytest**; P1; execution class `algorithmic_local`. Source: https://github.com/pytest-dev/pytest

### B.Data — 34 proposed IDs

- `data.aggregate` — **DuckDB**; P1; execution class `deterministic_local`. Source: https://duckdb.org/docs/stable/clients/cli/overview
- `data.arrow.convert` — **Apache Arrow**; P2; execution class `deterministic_local`. Source: https://arrow.apache.org/
- `data.columnar.write` — **Apache Arrow**; P2; execution class `deterministic_local`. Source: https://arrow.apache.org/
- `data.csv_to_parquet` — **DuckDB**; P1; execution class `deterministic_local`. Source: https://duckdb.org/docs/stable/clients/cli/overview
- `data.dedupe` — **DuckDB**; P1; execution class `deterministic_local`. Source: https://duckdb.org/docs/stable/clients/cli/overview
- `data.group` — **Polars**; P2; execution class `deterministic_local`. Source: https://github.com/pola-rs/polars
- `data.join` — **Polars**; P2; execution class `deterministic_local`. Source: https://github.com/pola-rs/polars
- `data.lazy_transform` — **Polars**; P2; execution class `deterministic_local`. Source: https://github.com/pola-rs/polars
- `data.profile` — **Polars**; P2; execution class `deterministic_local`. Source: https://github.com/pola-rs/polars
- `data.query` — **DuckDB**; P1; execution class `deterministic_local`. Source: https://duckdb.org/docs/stable/clients/cli/overview
- `data.schema.validate` — **Apache Arrow**; P2; execution class `deterministic_local`. Source: https://arrow.apache.org/
- `data.validate` — **DuckDB**; P1; execution class `deterministic_local`. Source: https://duckdb.org/docs/stable/clients/cli/overview
- `db.export` — **SQLite**; P1; execution class `deterministic_local`. Source: https://sqlite.org/cli.html
- `db.index` — **SQLite**; P1; execution class `deterministic_local`. Source: https://sqlite.org/cli.html
- `db.integrity` — **SQLite**; P1; execution class `deterministic_local`. Source: https://sqlite.org/cli.html
- `db.migrate` — **SQLite**; P1; execution class `deterministic_local`. Source: https://sqlite.org/cli.html
- `db.query` — **SQLite**; P1; execution class `deterministic_local`. Source: https://sqlite.org/cli.html
- `document.batch_extract` — **MarkItDown**; P2; execution class `environment_sensitive`. Source: https://github.com/microsoft/markitdown
- `document.markdown.convert` — **MarkItDown**; P2; execution class `environment_sensitive`. Source: https://github.com/microsoft/markitdown
- `document.metadata.extract` — **MarkItDown**; P2; execution class `environment_sensitive`. Source: https://github.com/microsoft/markitdown
- `graph.centrality` — **NetworkX**; P2; execution class `deterministic_local`. Source: https://github.com/networkx/networkx
- `graph.components` — **NetworkX**; P2; execution class `deterministic_local`. Source: https://github.com/networkx/networkx
- `graph.layout` — **NetworkX**; P2; execution class `deterministic_local`. Source: https://github.com/networkx/networkx
- `graph.shortest_path` — **NetworkX**; P2; execution class `deterministic_local`. Source: https://github.com/networkx/networkx
- `text.deduplicate` — **RapidFuzz**; P2; execution class `deterministic_local`. Source: https://github.com/rapidfuzz/RapidFuzz
- `text.fuzzy_match` — **RapidFuzz**; P2; execution class `deterministic_local`. Source: https://github.com/rapidfuzz/RapidFuzz
- `text.similarity` — **RapidFuzz**; P2; execution class `deterministic_local`. Source: https://github.com/rapidfuzz/RapidFuzz
- `video.reference.download_authorized` — **yt-dlp**; P2; execution class `network_stateful`. Source: https://github.com/yt-dlp/yt-dlp
- `video.reference.metadata` — **yt-dlp**; P2; execution class `network_stateful`. Source: https://github.com/yt-dlp/yt-dlp
- `video.reference.subtitles` — **yt-dlp**; P2; execution class `network_stateful`. Source: https://github.com/yt-dlp/yt-dlp
- `web.article.extract` — **Trafilatura**; P2; execution class `network_stateful`. Source: https://github.com/adbar/trafilatura
- `web.cleantext` — **Trafilatura**; P2; execution class `network_stateful`. Source: https://github.com/adbar/trafilatura
- `web.links.extract` — **Trafilatura**; P2; execution class `network_stateful`. Source: https://github.com/adbar/trafilatura
- `web.metadata` — **Trafilatura**; P2; execution class `network_stateful`. Source: https://github.com/adbar/trafilatura

### B.Eval — 18 proposed IDs

- `eval.agent.redteam` — **Promptfoo**; P1; execution class `model_inference`. Source: https://github.com/promptfoo/promptfoo
- `eval.baselines` — **Promptfoo**; P1; execution class `model_inference`. Source: https://github.com/promptfoo/promptfoo
- `eval.batch` — **Garak**; P2; execution class `model_inference`. Source: https://github.com/NVIDIA/garak
- `eval.dataset` — **Inspect AI**; P1; execution class `model_inference`. Source: https://github.com/UKGovernmentBEIS/inspect_ai
- `eval.dataset.run` — **Promptfoo**; P1; execution class `model_inference`. Source: https://github.com/promptfoo/promptfoo
- `eval.detectors` — **Garak**; P2; execution class `model_inference`. Source: https://github.com/NVIDIA/garak
- `eval.inspect.run` — **Inspect AI**; P1; execution class `model_inference`. Source: https://github.com/UKGovernmentBEIS/inspect_ai
- `eval.lm_bench` — **lm-evaluation-harness**; P2; execution class `model_inference`. Source: https://github.com/EleutherAI/lm-evaluation-harness
- `eval.metrics` — **lm-evaluation-harness**; P2; execution class `model_inference`. Source: https://github.com/EleutherAI/lm-evaluation-harness
- `eval.model.compare` — **Inspect AI**; P1; execution class `model_inference`. Source: https://github.com/UKGovernmentBEIS/inspect_ai
- `eval.model_matrix` — **lm-evaluation-harness**; P2; execution class `model_inference`. Source: https://github.com/EleutherAI/lm-evaluation-harness
- `eval.probes` — **Garak**; P2; execution class `model_inference`. Source: https://github.com/NVIDIA/garak
- `eval.report` — **Promptfoo**; P1; execution class `model_inference`. Source: https://github.com/promptfoo/promptfoo
- `eval.safety_report` — **Garak**; P2; execution class `model_inference`. Source: https://github.com/NVIDIA/garak
- `eval.sample.trace` — **Inspect AI**; P1; execution class `model_inference`. Source: https://github.com/UKGovernmentBEIS/inspect_ai
- `eval.scorers` — **Inspect AI**; P1; execution class `model_inference`. Source: https://github.com/UKGovernmentBEIS/inspect_ai
- `eval.task_suite` — **lm-evaluation-harness**; P2; execution class `model_inference`. Source: https://github.com/EleutherAI/lm-evaluation-harness
- `eval.testcase.generate` — **Promptfoo**; P1; execution class `model_inference`. Source: https://github.com/promptfoo/promptfoo

### B.Motion — 96 proposed IDs

- `audio.duck` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `audio.fade` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `audio.loudnorm` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `audio.mix` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `blender.camera.animate` — **Blender**; P1; execution class `algorithmic_local`. Source: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- `blender.compositor` — **Blender**; P1; execution class `algorithmic_local`. Source: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- `blender.export.glb` — **Blender**; P1; execution class `algorithmic_local`. Source: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- `blender.material.apply` — **Blender**; P1; execution class `algorithmic_local`. Source: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- `blender.render.frames` — **Blender**; P1; execution class `algorithmic_local`. Source: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- `blender.render.turntable` — **Blender**; P1; execution class `algorithmic_local`. Source: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- `blender.scene.build` — **Blender**; P1; execution class `algorithmic_local`. Source: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- `browser.dom.snapshot` — **Playwright**; P1; execution class `environment_sensitive`. Source: https://github.com/microsoft/playwright
- `browser.layout.measure` — **Playwright**; P1; execution class `environment_sensitive`. Source: https://github.com/microsoft/playwright
- `browser.record` — **Playwright**; P1; execution class `environment_sensitive`. Source: https://github.com/microsoft/playwright
- `browser.screenshot` — **Playwright**; P1; execution class `environment_sensitive`. Source: https://github.com/microsoft/playwright
- `browser.scroll_capture` — **Playwright**; P1; execution class `environment_sensitive`. Source: https://github.com/microsoft/playwright
- `browser.trace` — **Playwright**; P1; execution class `environment_sensitive`. Source: https://github.com/microsoft/playwright
- `diagram.export_png` — **Mermaid CLI**; P2; execution class `algorithmic_local`. Source: https://github.com/mermaid-js/mermaid-cli
- `diagram.export_svg` — **Mermaid CLI**; P2; execution class `algorithmic_local`. Source: https://github.com/mermaid-js/mermaid-cli
- `diagram.flowchart` — **Mermaid CLI**; P2; execution class `algorithmic_local`. Source: https://github.com/mermaid-js/mermaid-cli
- `diagram.sequence` — **Mermaid CLI**; P2; execution class `algorithmic_local`. Source: https://github.com/mermaid-js/mermaid-cli
- `game.assets.import` — **Godot**; P2; execution class `environment_sensitive`. Source: https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html
- `game.capture` — **Godot**; P2; execution class `environment_sensitive`. Source: https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html
- `game.headless.test` — **Godot**; P2; execution class `environment_sensitive`. Source: https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html
- `game.physics.simulate` — **Godot**; P2; execution class `environment_sensitive`. Source: https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html
- `game.scene.render` — **Godot**; P2; execution class `environment_sensitive`. Source: https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html
- `gltf.compress` — **glTF Transform**; P1; execution class `algorithmic_local`. Source: https://github.com/donmccurdy/glTF-Transform
- `gltf.inspect` — **glTF Transform**; P1; execution class `algorithmic_local`. Source: https://github.com/donmccurdy/glTF-Transform
- `gltf.optimize` — **glTF Transform**; P1; execution class `algorithmic_local`. Source: https://github.com/donmccurdy/glTF-Transform
- `gltf.partition` — **glTF Transform**; P1; execution class `algorithmic_local`. Source: https://github.com/donmccurdy/glTF-Transform
- `gltf.simplify` — **glTF Transform**; P1; execution class `algorithmic_local`. Source: https://github.com/donmccurdy/glTF-Transform
- `gltf.texture.optimize` — **glTF Transform**; P1; execution class `algorithmic_local`. Source: https://github.com/donmccurdy/glTF-Transform
- `graphics.overlay.render` — **resvg**; P1; execution class `deterministic_local`. Source: https://github.com/linebender/resvg
- `image.batch_resize` — **Sharp**; P2; execution class `deterministic_local`. Source: https://github.com/lovell/sharp
- `image.compare` — **ImageMagick**; P2; execution class `deterministic_local`. Source: https://imagemagick.org/
- `image.compose` — **ImageMagick**; P2; execution class `deterministic_local`. Source: https://imagemagick.org/
- `image.composite` — **Sharp**; P2; execution class `deterministic_local`. Source: https://github.com/lovell/sharp
- `image.metadata` — **Sharp**; P2; execution class `deterministic_local`. Source: https://github.com/lovell/sharp
- `image.montage` — **ImageMagick**; P2; execution class `deterministic_local`. Source: https://imagemagick.org/
- `image.resize` — **ImageMagick**; P2; execution class `deterministic_local`. Source: https://imagemagick.org/
- `image.transcode` — **Sharp**; P2; execution class `deterministic_local`. Source: https://github.com/lovell/sharp
- `image.trim` — **ImageMagick**; P2; execution class `deterministic_local`. Source: https://imagemagick.org/
- `math.axes.animate` — **Manim**; P2; execution class `algorithmic_local`. Source: https://github.com/ManimCommunity/manim
- `math.chart.animate` — **Manim**; P2; execution class `algorithmic_local`. Source: https://github.com/ManimCommunity/manim
- `math.explainer.sequence` — **Manim**; P2; execution class `algorithmic_local`. Source: https://github.com/ManimCommunity/manim
- `math.formula.transition` — **Manim**; P2; execution class `algorithmic_local`. Source: https://github.com/ManimCommunity/manim
- `math.geometry.visualize` — **Manim**; P2; execution class `algorithmic_local`. Source: https://github.com/ManimCommunity/manim
- `math.scene.render` — **Manim**; P2; execution class `algorithmic_local`. Source: https://github.com/ManimCommunity/manim
- `mesh.export` — **trimesh**; P2; execution class `algorithmic_local`. Source: https://github.com/mikedh/trimesh
- `mesh.inspect` — **trimesh**; P2; execution class `algorithmic_local`. Source: https://github.com/mikedh/trimesh
- `mesh.measure` — **trimesh**; P2; execution class `algorithmic_local`. Source: https://github.com/mikedh/trimesh
- `mesh.repair` — **trimesh**; P2; execution class `algorithmic_local`. Source: https://github.com/mikedh/trimesh
- `mesh.slice` — **trimesh**; P2; execution class `algorithmic_local`. Source: https://github.com/mikedh/trimesh
- `motioncanvas.graphs` — **Motion Canvas**; P2; execution class `algorithmic_local`. Source: https://github.com/motion-canvas/motion-canvas
- `motioncanvas.scene.render` — **Motion Canvas**; P2; execution class `algorithmic_local`. Source: https://github.com/motion-canvas/motion-canvas
- `motioncanvas.timeline` — **Motion Canvas**; P2; execution class `algorithmic_local`. Source: https://github.com/motion-canvas/motion-canvas
- `motioncanvas.vector.animate` — **Motion Canvas**; P2; execution class `algorithmic_local`. Source: https://github.com/motion-canvas/motion-canvas
- `remotion.composition` — **Remotion**; P3; execution class `licensing_review`. Source: https://www.remotion.dev/docs/
- `remotion.props.variant` — **Remotion**; P3; execution class `licensing_review`. Source: https://www.remotion.dev/docs/
- `remotion.render` — **Remotion**; P3; execution class `licensing_review`. Source: https://www.remotion.dev/docs/
- `remotion.snapshot` — **Remotion**; P3; execution class `licensing_review`. Source: https://www.remotion.dev/docs/
- `rig.instruct.constraints` — **Instruct-Particulate**; P3; execution class `model_inference`. Source: https://instruct-particulate.github.io/
- `rig.instruct.predict` — **Instruct-Particulate**; P3; execution class `model_inference`. Source: https://instruct-particulate.github.io/
- `rig.particulate.export_glb` — **Particulate**; P3; execution class `model_inference`. Source: https://github.com/RuiningLi/particulate
- `rig.particulate.export_urdf` — **Particulate**; P3; execution class `model_inference`. Source: https://github.com/RuiningLi/particulate
- `rig.particulate.predict` — **Particulate**; P3; execution class `model_inference`. Source: https://github.com/RuiningLi/particulate
- `shots.adaptive_detect` — **PySceneDetect**; P1; execution class `algorithmic_local`. Source: https://www.scenedetect.com/docs/cli.html
- `shots.content_detect` — **PySceneDetect**; P1; execution class `algorithmic_local`. Source: https://www.scenedetect.com/docs/cli.html
- `shots.fade_detect` — **PySceneDetect**; P1; execution class `algorithmic_local`. Source: https://www.scenedetect.com/docs/cli.html
- `shots.keyframes` — **PySceneDetect**; P1; execution class `algorithmic_local`. Source: https://www.scenedetect.com/docs/cli.html
- `shots.split` — **PySceneDetect**; P1; execution class `algorithmic_local`. Source: https://www.scenedetect.com/docs/cli.html
- `svg.check` — **resvg**; P1; execution class `deterministic_local`. Source: https://github.com/linebender/resvg
- `svg.rasterize` — **resvg**; P1; execution class `deterministic_local`. Source: https://github.com/linebender/resvg
- `svg.thumbnail` — **resvg**; P1; execution class `deterministic_local`. Source: https://github.com/linebender/resvg
- `timeline.export_edl` — **OpenTimelineIO**; P1; execution class `deterministic_local`. Source: https://github.com/AcademySoftwareFoundation/OpenTimelineIO
- `timeline.merge` — **OpenTimelineIO**; P1; execution class `deterministic_local`. Source: https://github.com/AcademySoftwareFoundation/OpenTimelineIO
- `timeline.read` — **OpenTimelineIO**; P1; execution class `deterministic_local`. Source: https://github.com/AcademySoftwareFoundation/OpenTimelineIO
- `timeline.validate` — **OpenTimelineIO**; P1; execution class `deterministic_local`. Source: https://github.com/AcademySoftwareFoundation/OpenTimelineIO
- `timeline.write` — **OpenTimelineIO**; P1; execution class `deterministic_local`. Source: https://github.com/AcademySoftwareFoundation/OpenTimelineIO
- `video.concat` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `video.crop` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `video.encode` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `video.framerate` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `video.palette` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `video.scale` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `video.stabilize` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `video.subtitle.burn` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `video.xfade` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `video.zoompan` — **FFmpeg**; P1; execution class `deterministic_local`. Source: https://ffmpeg.org/ffmpeg-filters.html
- `vision.camera_hint` — **OpenCV**; P1; execution class `algorithmic_local`. Source: https://github.com/opencv/opencv
- `vision.edge` — **OpenCV**; P1; execution class `algorithmic_local`. Source: https://github.com/opencv/opencv
- `vision.feature_match` — **OpenCV**; P1; execution class `algorithmic_local`. Source: https://github.com/opencv/opencv
- `vision.flow` — **OpenCV**; P1; execution class `algorithmic_local`. Source: https://github.com/opencv/opencv
- `vision.histogram` — **OpenCV**; P1; execution class `algorithmic_local`. Source: https://github.com/opencv/opencv
- `vision.motion_segments` — **OpenCV**; P1; execution class `algorithmic_local`. Source: https://github.com/opencv/opencv
- `vision.track` — **OpenCV**; P1; execution class `algorithmic_local`. Source: https://github.com/opencv/opencv

### B.Optimization — 25 proposed IDs

- `chem.conformers` — **RDKit**; P2; execution class `algorithmic_local`. Source: https://github.com/rdkit/rdkit
- `chem.descriptors` — **RDKit**; P2; execution class `algorithmic_local`. Source: https://github.com/rdkit/rdkit
- `chem.molecule.validate` — **RDKit**; P2; execution class `algorithmic_local`. Source: https://github.com/rdkit/rdkit
- `chem.substructure` — **RDKit**; P2; execution class `algorithmic_local`. Source: https://github.com/rdkit/rdkit
- `dynamics.simulate` — **OpenMM**; P3; execution class `gpu_dependent`. Source: https://github.com/openmm/openmm
- `molecular.energy` — **OpenMM**; P3; execution class `gpu_dependent`. Source: https://github.com/openmm/openmm
- `molecular.forcefield` — **OpenMM**; P3; execution class `gpu_dependent`. Source: https://github.com/openmm/openmm
- `opt.assignment` — **Google OR-Tools**; P1; execution class `algorithmic_local`. Source: https://github.com/google/or-tools
- `opt.cp_sat` — **Google OR-Tools**; P1; execution class `algorithmic_local`. Source: https://github.com/google/or-tools
- `opt.integrate` — **SciPy**; P2; execution class `algorithmic_local`. Source: https://github.com/scipy/scipy
- `opt.knapsack` — **Google OR-Tools**; P1; execution class `algorithmic_local`. Source: https://github.com/google/or-tools
- `opt.min_cost_flow` — **Google OR-Tools**; P1; execution class `algorithmic_local`. Source: https://github.com/google/or-tools
- `opt.nonlinear` — **SciPy**; P2; execution class `algorithmic_local`. Source: https://github.com/scipy/scipy
- `opt.parameter_grid` — **Optuna**; P1; execution class `seeded_stateful`. Source: https://github.com/optuna/optuna
- `opt.pareto` — **Optuna**; P1; execution class `seeded_stateful`. Source: https://github.com/optuna/optuna
- `opt.prune` — **Optuna**; P1; execution class `seeded_stateful`. Source: https://github.com/optuna/optuna
- `opt.root` — **SciPy**; P2; execution class `algorithmic_local`. Source: https://github.com/scipy/scipy
- `opt.routing` — **Google OR-Tools**; P1; execution class `algorithmic_local`. Source: https://github.com/google/or-tools
- `opt.schedule` — **Google OR-Tools**; P1; execution class `algorithmic_local`. Source: https://github.com/google/or-tools
- `opt.search` — **Optuna**; P1; execution class `seeded_stateful`. Source: https://github.com/optuna/optuna
- `opt.stats` — **SciPy**; P2; execution class `algorithmic_local`. Source: https://github.com/scipy/scipy
- `opt.study` — **Optuna**; P1; execution class `seeded_stateful`. Source: https://github.com/optuna/optuna
- `sdg.energy_balance` — **PyPSA**; P2; execution class `solver_dependent`. Source: https://github.com/PyPSA/PyPSA
- `sdg.grid.optimize` — **PyPSA**; P2; execution class `solver_dependent`. Source: https://github.com/PyPSA/PyPSA
- `sdg.scenario_compare` — **PyPSA**; P2; execution class `solver_dependent`. Source: https://github.com/PyPSA/PyPSA

### B.Security — 20 proposed IDs

- `artifact.advisory.matches` — **Grype**; P2; execution class `environment_sensitive`. Source: https://github.com/anchore/grype
- `artifact.attest` — **Cosign**; P1; execution class `identity_stateful`. Source: https://github.com/sigstore/cosign
- `artifact.dependencies` — **Syft**; P1; execution class `deterministic_local`. Source: https://github.com/anchore/syft
- `artifact.license.scan` — **Trivy**; P2; execution class `environment_sensitive`. Source: https://github.com/aquasecurity/trivy
- `artifact.license_inventory` — **Syft**; P1; execution class `deterministic_local`. Source: https://github.com/anchore/syft
- `artifact.provenance` — **Syft**; P1; execution class `deterministic_local`. Source: https://github.com/anchore/syft
- `artifact.remediation` — **Grype**; P2; execution class `environment_sensitive`. Source: https://github.com/anchore/grype
- `artifact.sbom` — **Syft**; P1; execution class `deterministic_local`. Source: https://github.com/anchore/syft
- `artifact.sign` — **Cosign**; P1; execution class `identity_stateful`. Source: https://github.com/sigstore/cosign
- `artifact.verify` — **Cosign**; P1; execution class `identity_stateful`. Source: https://github.com/sigstore/cosign
- `artifact.vulnerability.scan` — **Grype**; P2; execution class `environment_sensitive`. Source: https://github.com/anchore/grype
- `container.vuln.scan` — **Trivy**; P2; execution class `environment_sensitive`. Source: https://github.com/aquasecurity/trivy
- `oci.verify` — **Cosign**; P1; execution class `identity_stateful`. Source: https://github.com/sigstore/cosign
- `policy.constraints` — **OPA**; P2; execution class `deterministic_local`. Source: https://github.com/open-policy-agent/opa
- `policy.deny` — **OPA**; P2; execution class `deterministic_local`. Source: https://github.com/open-policy-agent/opa
- `policy.rego.eval` — **OPA**; P2; execution class `deterministic_local`. Source: https://github.com/open-policy-agent/opa
- `repo.config.scan` — **Trivy**; P2; execution class `environment_sensitive`. Source: https://github.com/aquasecurity/trivy
- `wasm.component.validate` — **Wasmtime**; P2; execution class `bounded_sandbox`. Source: https://github.com/bytecodealliance/wasmtime
- `wasm.fuel_bound` — **Wasmtime**; P2; execution class `bounded_sandbox`. Source: https://github.com/bytecodealliance/wasmtime
- `wasm.module.run` — **Wasmtime**; P2; execution class `bounded_sandbox`. Source: https://github.com/bytecodealliance/wasmtime

### B.Skills — 44 proposed IDs

- `mcp.fetch.extract` — **MCP Reference Servers**; P1; execution class `environment_sensitive`. Source: https://github.com/modelcontextprotocol/servers
- `mcp.filesystem.read` — **MCP Reference Servers**; P1; execution class `environment_sensitive`. Source: https://github.com/modelcontextprotocol/servers
- `mcp.git.inspect` — **MCP Reference Servers**; P1; execution class `environment_sensitive`. Source: https://github.com/modelcontextprotocol/servers
- `mcp.registry.classify` — **Official MCP Registry**; P1; execution class `network_stateful`. Source: https://github.com/modelcontextprotocol/registry
- `mcp.registry.dedupe` — **Official MCP Registry**; P1; execution class `network_stateful`. Source: https://github.com/modelcontextprotocol/registry
- `mcp.registry.discover` — **Official MCP Registry**; P1; execution class `network_stateful`. Source: https://github.com/modelcontextprotocol/registry
- `mcp.registry.metadata` — **Official MCP Registry**; P1; execution class `network_stateful`. Source: https://github.com/modelcontextprotocol/registry
- `mcp.registry.version` — **Official MCP Registry**; P1; execution class `network_stateful`. Source: https://github.com/modelcontextprotocol/registry
- `mcp.tool.catalog` — **MCP Reference Servers**; P1; execution class `environment_sensitive`. Source: https://github.com/modelcontextprotocol/servers
- `mcp.tool.schema` — **MCP Reference Servers**; P1; execution class `environment_sensitive`. Source: https://github.com/modelcontextprotocol/servers
- `security.issue_triage` — **Trail of Bits Skills**; P2; execution class `human_review`. Source: https://github.com/trailofbits/skills
- `security.review.plan` — **Trail of Bits Skills**; P2; execution class `human_review`. Source: https://github.com/trailofbits/skills
- `security.rule_check` — **Trail of Bits Skills**; P2; execution class `human_review`. Source: https://github.com/trailofbits/skills
- `security.test_harness` — **Trail of Bits Skills**; P2; execution class `human_review`. Source: https://github.com/trailofbits/skills
- `skill.agents_yaml.describe` — **OpenAI Skills**; P1; execution class `human_review`. Source: https://github.com/openai/skills
- `skill.cli_contract.propose` — **OpenAI Skills**; P1; execution class `human_review`. Source: https://github.com/openai/skills
- `skill.fixtures.plan` — **Anthropic Skills**; P1; execution class `human_review`. Source: https://github.com/anthropics/skills
- `skill.frontmatter.validate` — **Agent Skills Specification**; P1; execution class `deterministic_local`. Source: https://github.com/agentskills/agentskills
- `skill.inventory` — **Agent Skills Specification**; P1; execution class `deterministic_local`. Source: https://github.com/agentskills/agentskills
- `skill.lint` — **Agent Skills Specification**; P1; execution class `deterministic_local`. Source: https://github.com/agentskills/agentskills
- `skill.package.diff` — **Vercel Skills CLI**; P2; execution class `network_stateful`. Source: https://github.com/vercel-labs/skills
- `skill.package.discover` — **Vercel Skills CLI**; P2; execution class `network_stateful`. Source: https://github.com/vercel-labs/skills
- `skill.package.install_plan` — **Vercel Skills CLI**; P2; execution class `network_stateful`. Source: https://github.com/vercel-labs/skills
- `skill.package.inventory` — **Vercel Skills CLI**; P2; execution class `network_stateful`. Source: https://github.com/vercel-labs/skills
- `skill.provenance` — **Agent Skills Specification**; P1; execution class `deterministic_local`. Source: https://github.com/agentskills/agentskills
- `skill.react.rules` — **Vercel Agent Skills**; P2; execution class `human_review`. Source: https://github.com/vercel-labs/agent-skills
- `skill.readme.generate` — **OpenAI Skills**; P1; execution class `human_review`. Source: https://github.com/openai/skills
- `skill.schema.emit` — **Agent Skills Specification**; P1; execution class `deterministic_local`. Source: https://github.com/agentskills/agentskills
- `skill.script.inventory` — **Anthropic Skills**; P1; execution class `human_review`. Source: https://github.com/anthropics/skills
- `skill.templates.index` — **Anthropic Skills**; P1; execution class `human_review`. Source: https://github.com/anthropics/skills
- `skill.workflow.extract` — **Anthropic Skills**; P1; execution class `human_review`. Source: https://github.com/anthropics/skills
- `skill.workflow.test` — **OpenAI Skills**; P1; execution class `human_review`. Source: https://github.com/openai/skills
- `web.accessibility.rules` — **Vercel Agent Skills**; P2; execution class `human_review`. Source: https://github.com/vercel-labs/agent-skills
- `web.patterns.check` — **Vercel Agent Skills**; P2; execution class `human_review`. Source: https://github.com/vercel-labs/agent-skills
- `web.performance.audit` — **Vercel Agent Skills**; P2; execution class `human_review`. Source: https://github.com/vercel-labs/agent-skills
- `workflow.architecture.audit` — **BMad Method**; P2; execution class `human_review`. Source: https://github.com/bmad-code-org/BMAD-METHOD
- `workflow.baseline_eval` — **Superpowers**; P2; execution class `human_review`. Source: https://github.com/obra/superpowers
- `workflow.checkpoint` — **Superpowers**; P2; execution class `human_review`. Source: https://github.com/obra/superpowers
- `workflow.prd.validate` — **BMad Method**; P2; execution class `human_review`. Source: https://github.com/bmad-code-org/BMAD-METHOD
- `workflow.red_green_refactor` — **Superpowers**; P2; execution class `human_review`. Source: https://github.com/obra/superpowers
- `workflow.requirement_trace` — **BMad Method**; P2; execution class `human_review`. Source: https://github.com/bmad-code-org/BMAD-METHOD
- `workflow.story.compile` — **BMad Method**; P2; execution class `human_review`. Source: https://github.com/bmad-code-org/BMAD-METHOD
- `workflow.testplan` — **BMad Method**; P2; execution class `human_review`. Source: https://github.com/bmad-code-org/BMAD-METHOD
- `workflow.verification` — **Superpowers**; P2; execution class `human_review`. Source: https://github.com/obra/superpowers


## Appendix C — The full 180-dimension spatial design inventory
**A dimensional vocabulary, not 180 implemented controls.** Operational features are described in §3.7. Use this inventory to design validated schemas, UI inspectors, variation grids and counterfactual layout evaluations.

### C.Canvas — 12 dimensions
`width`, `height`, `aspect_ratio`, `fps`, `frame_number`, `pixel_aspect`, `render_scale`, `safe_profile`, `bleed_area`, `safe_zone`, `device_preview`, `overscan`.

### C.Spatial position — 15 dimensions
`anchor_15`, `x_relative`, `y_relative`, `offset_px`, `baseline`, `thirds_guide`, `rule_of_fifths`, `subject_anchor`, `focal_point`, `parent_anchor`, `alignment`, `grid_cell`, `column_span`, `row_span`, `sticky_region`.

### C.Sizing — 12 dimensions
`relative_width`, `relative_height`, `max_width`, `min_width`, `max_height`, `min_height`, `font_scale`, `fit_contain`, `fit_cover`, `crop_region`, `auto_fit`, `aspect_lock`.

### C.Spacing — 14 dimensions
`padding_top`, `padding_right`, `padding_bottom`, `padding_left`, `margin_top`, `margin_right`, `margin_bottom`, `margin_left`, `gap_x`, `gap_y`, `line_spacing`, `letter_spacing`, `baseline_gap`, `panel_gutter`.

### C.Typography — 22 dimensions
`family`, `weight`, `size`, `minimum_size`, `stroke_width`, `shadow`, `text_color`, `align_left`, `align_center`, `align_right`, `vertical_align`, `wrap`, `maximum_lines`, `ellipsis`, `tracking`, `kerning`, `leading`, `background_card`, `text_path`, `highlight_per_word`, `highlight_per_char`, `reveal_delay`.

### C.Shapes — 16 dimensions
`rect`, `rounded_rect`, `line`, `divider`, `progress`, `circle`, `reticle`, `ribbon`, `pointer`, `pill`, `metric`, `waveform`, `label`, `corner_marks`, `frame_border`, `grid_overlay`.

### C.Layering — 17 dimensions
`z_index`, `depth`, `alpha`, `blend_normal`, `blend_screen`, `blend_multiply`, `blend_add`, `clip_round`, `foreground_occlusion`, `mask`, `group`, `parent_space`, `nested_container`, `independent_timing`, `visibility`, `solo`, `lock`.

### C.Motion — 20 dimensions
`pan_x`, `pan_y`, `zoom`, `tilt`, `roll`, `crop_x`, `crop_y`, `shake_x`, `shake_y`, `ease_in`, `ease_out`, `stagger`, `hold`, `fade`, `slide`, `scale`, `typewriter`, `pop`, `wipe`, `parallax_depth`.

### C.Camera — 13 dimensions
`framing`, `subject_tracking`, `deadzone`, `lookahead`, `dolly`, `push_in`, `pull_out`, `whip`, `crash_zoom`, `focus_pull`, `overshoot`, `viewpoint`, `picture_in_picture`.

### C.Color — 14 dimensions
`foreground`, `background`, `accent`, `danger`, `temperature`, `tint`, `vignette`, `contrast`, `saturation`, `gamma`, `opacity`, `outline`, `grading`, `palette_lock`.

### C.Audio — 11 dimensions
`narration_cue`, `sound_event`, `music_duck`, `ambient_bed`, `beat_sync`, `stereo_pan`, `loudness`, `fade_in`, `fade_out`, `captions`, `subtitle_sync`.

### C.QA — 14 dimensions
`safe_area`, `font_readability`, `offscreen`, `text_collision`, `subject_collision`, `black_frame`, `subtitle_contrast`, `duration`, `cut_detect`, `camera_flow`, `edit_manifest`, `provenance`, `sample_rate`, `asset_rights`.

**Computed total from `layouts.json`: 180 dimension fields.**

## Appendix D — 120 candidate motion-content recipes
These are recipe **ideas/specifications**, not 120 rendered films. `model_route` can mention third-party models not integrated here. Original source file: `baltor_motion_foundry/docs/CONTENT_RECIPES.json`.

1. **Foldable chair: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Particulate / manual rig.
2. **Foldable chair: exploded assembly journey** — style `exploded_view`; articulation/model route: Particulate / manual rig.
3. **Foldable chair: cinematic product film** — style `macro_cinematic`; articulation/model route: Particulate / manual rig.
4. **Foldable chair: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Particulate / manual rig.
5. **Foldable chair: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Particulate / manual rig.
6. **Foldable chair: game engine interaction video** — style `game_engine`; articulation/model route: Particulate / manual rig.
7. **Foldable chair: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Particulate / manual rig.
8. **Foldable chair: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Particulate / manual rig.
9. **Foldable chair: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Particulate / manual rig.
10. **Foldable chair: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Particulate / manual rig.
11. **Sliding drawer cabinet: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Particulate / manual rig.
12. **Sliding drawer cabinet: exploded assembly journey** — style `exploded_view`; articulation/model route: Particulate / manual rig.
13. **Sliding drawer cabinet: cinematic product film** — style `macro_cinematic`; articulation/model route: Particulate / manual rig.
14. **Sliding drawer cabinet: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Particulate / manual rig.
15. **Sliding drawer cabinet: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Particulate / manual rig.
16. **Sliding drawer cabinet: game engine interaction video** — style `game_engine`; articulation/model route: Particulate / manual rig.
17. **Sliding drawer cabinet: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Particulate / manual rig.
18. **Sliding drawer cabinet: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Particulate / manual rig.
19. **Sliding drawer cabinet: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Particulate / manual rig.
20. **Sliding drawer cabinet: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Particulate / manual rig.
21. **Industrial robotic arm: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Particulate / Articraft.
22. **Industrial robotic arm: exploded assembly journey** — style `exploded_view`; articulation/model route: Particulate / Articraft.
23. **Industrial robotic arm: cinematic product film** — style `macro_cinematic`; articulation/model route: Particulate / Articraft.
24. **Industrial robotic arm: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Particulate / Articraft.
25. **Industrial robotic arm: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Particulate / Articraft.
26. **Industrial robotic arm: game engine interaction video** — style `game_engine`; articulation/model route: Particulate / Articraft.
27. **Industrial robotic arm: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Particulate / Articraft.
28. **Industrial robotic arm: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Particulate / Articraft.
29. **Industrial robotic arm: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Particulate / Articraft.
30. **Industrial robotic arm: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Particulate / Articraft.
31. **Vehicle door and trunk: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Particulate / Instruct-Particulate.
32. **Vehicle door and trunk: exploded assembly journey** — style `exploded_view`; articulation/model route: Particulate / Instruct-Particulate.
33. **Vehicle door and trunk: cinematic product film** — style `macro_cinematic`; articulation/model route: Particulate / Instruct-Particulate.
34. **Vehicle door and trunk: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Particulate / Instruct-Particulate.
35. **Vehicle door and trunk: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Particulate / Instruct-Particulate.
36. **Vehicle door and trunk: game engine interaction video** — style `game_engine`; articulation/model route: Particulate / Instruct-Particulate.
37. **Vehicle door and trunk: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Particulate / Instruct-Particulate.
38. **Vehicle door and trunk: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Particulate / Instruct-Particulate.
39. **Vehicle door and trunk: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Particulate / Instruct-Particulate.
40. **Vehicle door and trunk: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Particulate / Instruct-Particulate.
41. **Hinged blender / food processor: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Particulate / Articraft.
42. **Hinged blender / food processor: exploded assembly journey** — style `exploded_view`; articulation/model route: Particulate / Articraft.
43. **Hinged blender / food processor: cinematic product film** — style `macro_cinematic`; articulation/model route: Particulate / Articraft.
44. **Hinged blender / food processor: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Particulate / Articraft.
45. **Hinged blender / food processor: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Particulate / Articraft.
46. **Hinged blender / food processor: game engine interaction video** — style `game_engine`; articulation/model route: Particulate / Articraft.
47. **Hinged blender / food processor: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Particulate / Articraft.
48. **Hinged blender / food processor: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Particulate / Articraft.
49. **Hinged blender / food processor: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Particulate / Articraft.
50. **Hinged blender / food processor: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Particulate / Articraft.
51. **Gearbox and milling table: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Articraft / manual / physics.
52. **Gearbox and milling table: exploded assembly journey** — style `exploded_view`; articulation/model route: Articraft / manual / physics.
53. **Gearbox and milling table: cinematic product film** — style `macro_cinematic`; articulation/model route: Articraft / manual / physics.
54. **Gearbox and milling table: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Articraft / manual / physics.
55. **Gearbox and milling table: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Articraft / manual / physics.
56. **Gearbox and milling table: game engine interaction video** — style `game_engine`; articulation/model route: Articraft / manual / physics.
57. **Gearbox and milling table: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Articraft / manual / physics.
58. **Gearbox and milling table: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Articraft / manual / physics.
59. **Gearbox and milling table: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Articraft / manual / physics.
60. **Gearbox and milling table: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Articraft / manual / physics.
61. **Automatic doors and louvers: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Particulate / procedural.
62. **Automatic doors and louvers: exploded assembly journey** — style `exploded_view`; articulation/model route: Particulate / procedural.
63. **Automatic doors and louvers: cinematic product film** — style `macro_cinematic`; articulation/model route: Particulate / procedural.
64. **Automatic doors and louvers: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Particulate / procedural.
65. **Automatic doors and louvers: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Particulate / procedural.
66. **Automatic doors and louvers: game engine interaction video** — style `game_engine`; articulation/model route: Particulate / procedural.
67. **Automatic doors and louvers: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Particulate / procedural.
68. **Automatic doors and louvers: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Particulate / procedural.
69. **Automatic doors and louvers: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Particulate / procedural.
70. **Automatic doors and louvers: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Particulate / procedural.
71. **Transforming toy robot: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Articraft / authored rig.
72. **Transforming toy robot: exploded assembly journey** — style `exploded_view`; articulation/model route: Articraft / authored rig.
73. **Transforming toy robot: cinematic product film** — style `macro_cinematic`; articulation/model route: Articraft / authored rig.
74. **Transforming toy robot: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Articraft / authored rig.
75. **Transforming toy robot: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Articraft / authored rig.
76. **Transforming toy robot: game engine interaction video** — style `game_engine`; articulation/model route: Articraft / authored rig.
77. **Transforming toy robot: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Articraft / authored rig.
78. **Transforming toy robot: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Articraft / authored rig.
79. **Transforming toy robot: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Articraft / authored rig.
80. **Transforming toy robot: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Articraft / authored rig.
81. **Microscope stage: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Particulate / authored rig.
82. **Microscope stage: exploded assembly journey** — style `exploded_view`; articulation/model route: Particulate / authored rig.
83. **Microscope stage: cinematic product film** — style `macro_cinematic`; articulation/model route: Particulate / authored rig.
84. **Microscope stage: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Particulate / authored rig.
85. **Microscope stage: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Particulate / authored rig.
86. **Microscope stage: game engine interaction video** — style `game_engine`; articulation/model route: Particulate / authored rig.
87. **Microscope stage: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Particulate / authored rig.
88. **Microscope stage: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Particulate / authored rig.
89. **Microscope stage: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Particulate / authored rig.
90. **Microscope stage: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Particulate / authored rig.
91. **Mechanical dragon or insect: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Articraft / authored rig.
92. **Mechanical dragon or insect: exploded assembly journey** — style `exploded_view`; articulation/model route: Articraft / authored rig.
93. **Mechanical dragon or insect: cinematic product film** — style `macro_cinematic`; articulation/model route: Articraft / authored rig.
94. **Mechanical dragon or insect: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Articraft / authored rig.
95. **Mechanical dragon or insect: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Articraft / authored rig.
96. **Mechanical dragon or insect: game engine interaction video** — style `game_engine`; articulation/model route: Articraft / authored rig.
97. **Mechanical dragon or insect: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Articraft / authored rig.
98. **Mechanical dragon or insect: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Articraft / authored rig.
99. **Mechanical dragon or insect: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Articraft / authored rig.
100. **Mechanical dragon or insect: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Articraft / authored rig.
101. **Rigged fox or bird: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: UniMate / existing skin rig.
102. **Rigged fox or bird: exploded assembly journey** — style `exploded_view`; articulation/model route: UniMate / existing skin rig.
103. **Rigged fox or bird: cinematic product film** — style `macro_cinematic`; articulation/model route: UniMate / existing skin rig.
104. **Rigged fox or bird: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: UniMate / existing skin rig.
105. **Rigged fox or bird: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: UniMate / existing skin rig.
106. **Rigged fox or bird: game engine interaction video** — style `game_engine`; articulation/model route: UniMate / existing skin rig.
107. **Rigged fox or bird: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: UniMate / existing skin rig.
108. **Rigged fox or bird: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: UniMate / existing skin rig.
109. **Rigged fox or bird: guess-the-joint challenge** — style `social_challenge`; articulation/model route: UniMate / existing skin rig.
110. **Rigged fox or bird: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: UniMate / existing skin rig.
111. **Kinetic generative sculpture: before-after rig discovery** — style `mesh_to_motion`; articulation/model route: Authored rig / procedural.
112. **Kinetic generative sculpture: exploded assembly journey** — style `exploded_view`; articulation/model route: Authored rig / procedural.
113. **Kinetic generative sculpture: cinematic product film** — style `macro_cinematic`; articulation/model route: Authored rig / procedural.
114. **Kinetic generative sculpture: satisfying neon transformation** — style `neon_satisfying`; articulation/model route: Authored rig / procedural.
115. **Kinetic generative sculpture: technical cutaway explainer** — style `engineering_cutaway`; articulation/model route: Authored rig / procedural.
116. **Kinetic generative sculpture: game engine interaction video** — style `game_engine`; articulation/model route: Authored rig / procedural.
117. **Kinetic generative sculpture: beat-synced mechanical music video** — style `music_reactive`; articulation/model route: Authored rig / procedural.
118. **Kinetic generative sculpture: 2×2 rig comparison** — style `comparison_2x2`; articulation/model route: Authored rig / procedural.
119. **Kinetic generative sculpture: guess-the-joint challenge** — style `social_challenge`; articulation/model route: Authored rig / procedural.
120. **Kinetic generative sculpture: research-backed 300s tutorial** — style `longform_explainer`; articulation/model route: Authored rig / procedural.

## Appendix E — 132 motion-harness component candidates/prototypes
This list contains mixed statuses; check each local component `status` before use. Catalog source: `baltor_motion_foundry/docs/COMPONENT_CATALOG.json`.

### E.articulation — 12 records
- `baltor.motion.articulation.manual_json_rig` — Manual Json Rig; **status:** `implemented`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.particulate_gpu_adapter` — Particulate Gpu Adapter; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.instruct_particulate_adapter` — Instruct Particulate Adapter; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.articraft_sdk_adapter` — Articraft Sdk Adapter; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.urdf_to_rig` — Urdf To Rig; **status:** `implemented`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.mjcf_to_rig` — Mjcf To Rig; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.gltf_animation_import` — Gltf Animation Import; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.skinning_rig_import` — Skinning Rig Import; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.hierarchy_visualizer` — Hierarchy Visualizer; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.joint_confidence_calibration` — Joint Confidence Calibration; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.part_id_stability` — Part Id Stability; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.
- `baltor.motion.articulation.rig_version_manager` — Rig Version Manager; **status:** `proposed`; suggested implementation: model-specific adapter / JSON.

### E.asset — 12 records
- `baltor.motion.asset.mesh_orientation` — Mesh Orientation; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.mesh_scale_normalizer` — Mesh Scale Normalizer; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.mesh_connected_components` — Mesh Connected Components; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.mesh_repair` — Mesh Repair; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.mesh_retopology` — Mesh Retopology; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.mesh_decimator` — Mesh Decimator; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.mesh_uv_validation` — Mesh Uv Validation; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.material_baker` — Material Baker; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.texture_atlas` — Texture Atlas; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.geometry_deduplicator` — Geometry Deduplicator; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.license_provenance` — License Provenance; **status:** `proposed`; suggested implementation: trimesh / VTK.
- `baltor.motion.asset.asset_sha256` — Asset Sha256; **status:** `proposed`; suggested implementation: trimesh / VTK.

### E.audio — 12 records
- `baltor.motion.audio.procedural_synth_music` — Procedural Synth Music; **status:** `implemented`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.speech_script` — Speech Script; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.local_tts_adapter` — Local Tts Adapter; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.narration_timestamps` — Narration Timestamps; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.word_level_caption_sync` — Word Level Caption Sync; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.beat_grid` — Beat Grid; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.original_foley` — Original Foley; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.audio_ducking` — Audio Ducking; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.loudness_normalizer` — Loudness Normalizer; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.phoneme_check` — Phoneme Check; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.music_rights_metadata` — Music Rights Metadata; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.
- `baltor.motion.audio.silence_detection` — Silence Detection; **status:** `proposed`; suggested implementation: NumPy / FFmpeg / optional TTS.

### E.compose — 12 records
- `baltor.motion.compose.background_full_movie` — Background Full Movie; **status:** `proposed`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.translucent_blur_layer` — Translucent Blur Layer; **status:** `proposed`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.animated_inset_border` — Animated Inset Border; **status:** `implemented`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.working_area_composite` — Working Area Composite; **status:** `proposed`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.kinetic_caption_overlay` — Kinetic Caption Overlay; **status:** `proposed`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.technical_hud` — Technical Hud; **status:** `implemented`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.multiview_pip` — Multiview Pip; **status:** `implemented`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.motion_trails` — Motion Trails; **status:** `proposed`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.particle_bloom` — Particle Bloom; **status:** `proposed`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.reflection_composite` — Reflection Composite; **status:** `proposed`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.ffmpeg_crossfade` — Ffmpeg Crossfade; **status:** `implemented`; suggested implementation: Pillow / FFmpeg / shader graph.
- `baltor.motion.compose.format_reframe` — Format Reframe; **status:** `proposed`; suggested implementation: Pillow / FFmpeg / shader graph.

### E.direct — 12 records
- `baltor.motion.direct.intent_to_storyboard` — Intent To Storyboard; **status:** `proposed`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.narration_script` — Narration Script; **status:** `proposed`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.shot_duration_optimizer` — Shot Duration Optimizer; **status:** `proposed`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.story_bible` — Story Bible; **status:** `proposed`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.location_map` — Location Map; **status:** `proposed`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.character_wardrobe_lock` — Character Wardrobe Lock; **status:** `proposed`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.camera_orbit` — Camera Orbit; **status:** `implemented`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.camera_dolly` — Camera Dolly; **status:** `implemented`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.macro_detail_camera` — Macro Detail Camera; **status:** `proposed`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.split_screen_director` — Split Screen Director; **status:** `proposed`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.storyboard_variation_sampler` — Storyboard Variation Sampler; **status:** `proposed`; suggested implementation: timeline JSON and planner.
- `baltor.motion.direct.continuity_auditor` — Continuity Auditor; **status:** `proposed`; suggested implementation: timeline JSON and planner.

### E.distribute — 12 records
- `baltor.motion.distribute.asset_poster_frame` — Asset Poster Frame; **status:** `implemented`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.video_variant_registry` — Video Variant Registry; **status:** `proposed`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.json_manifest_writer` — Json Manifest Writer; **status:** `implemented`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.thumbnail_selector` — Thumbnail Selector; **status:** `proposed`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.title_ab_tests` — Title Ab Tests; **status:** `proposed`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.post_copy_generator` — Post Copy Generator; **status:** `proposed`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.facebook_group_fit` — Facebook Group Fit; **status:** `proposed`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.utm_campaign_builder` — Utm Campaign Builder; **status:** `proposed`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.engagement_metrics_ingest` — Engagement Metrics Ingest; **status:** `proposed`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.feedback_classifier` — Feedback Classifier; **status:** `proposed`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.content_reuse_scheduler` — Content Reuse Scheduler; **status:** `proposed`; suggested implementation: metadata and human approval.
- `baltor.motion.distribute.competitor_claims_review` — Competitor Claims Review; **status:** `proposed`; suggested implementation: metadata and human approval.

### E.ingest — 12 records
- `baltor.motion.ingest.text_prompt` — Text Prompt; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.reference_photo` — Reference Photo; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.image_sequence` — Image Sequence; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.obj_mesh` — Obj Mesh; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.ply_mesh` — Ply Mesh; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.glb_mesh` — Glb Mesh; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.usd_scene` — Usd Scene; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.urdf_structure` — Urdf Structure; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.mjcf_structure` — Mjcf Structure; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.existing_animation` — Existing Animation; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.github_repo` — Github Repo; **status:** `proposed`; suggested implementation: trimesh or local file readers.
- `baltor.motion.ingest.research_pdf` — Research Pdf; **status:** `proposed`; suggested implementation: trimesh or local file readers.

### E.motion — 12 records
- `baltor.motion.motion.authored_curves` — Authored Curves; **status:** `implemented`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.bounded_joint_sweep` — Bounded Joint Sweep; **status:** `implemented`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.ease_curve_sampler` — Ease Curve Sampler; **status:** `implemented`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.prompt_to_joint_motion` — Prompt To Joint Motion; **status:** `proposed`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.unimate_motion_adapter` — Unimate Motion Adapter; **status:** `proposed`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.motion_retargeting` — Motion Retargeting; **status:** `proposed`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.loop_seam_optimizer` — Loop Seam Optimizer; **status:** `proposed`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.beat_synchronized_motion` — Beat Synchronized Motion; **status:** `proposed`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.gesture_library` — Gesture Library; **status:** `proposed`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.motion_blending` — Motion Blending; **status:** `proposed`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.inverse_kinematics` — Inverse Kinematics; **status:** `proposed`; suggested implementation: numpy / specialized model.
- `baltor.motion.motion.action_timeline` — Action Timeline; **status:** `proposed`; suggested implementation: numpy / specialized model.

### E.qa — 12 records
- `baltor.motion.qa.ffprobe_media_integrity` — Ffprobe Media Integrity; **status:** `implemented`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.temporal_motion_check` — Temporal Motion Check; **status:** `implemented`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.black_frame_check` — Black Frame Check; **status:** `implemented`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.safe_crop_check` — Safe Crop Check; **status:** `proposed`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.caption_readability` — Caption Readability; **status:** `proposed`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.voice_caption_alignment` — Voice Caption Alignment; **status:** `proposed`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.visual_glitches` — Visual Glitches; **status:** `proposed`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.joint_contact_qa` — Joint Contact Qa; **status:** `proposed`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.origin_label_accuracy` — Origin Label Accuracy; **status:** `proposed`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.license_compliance` — License Compliance; **status:** `proposed`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.source_manifest` — Source Manifest; **status:** `implemented`; suggested implementation: Python / ffprobe / review.
- `baltor.motion.qa.human_approval_gate` — Human Approval Gate; **status:** `proposed`; suggested implementation: Python / ffprobe / review.

### E.render — 12 records
- `baltor.motion.render.vtk_scene_renderer` — Vtk Scene Renderer; **status:** `implemented`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.blender_background_worker` — Blender Background Worker; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.threejs_capture_worker` — Threejs Capture Worker; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.babylonjs_capture_worker` — Babylonjs Capture Worker; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.godot_movie_maker` — Godot Movie Maker; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.unreal_sequencer_worker` — Unreal Sequencer Worker; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.pbr_material_presets` — Pbr Material Presets; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.procedural_shader_bank` — Procedural Shader Bank; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.lighting_rigs` — Lighting Rigs; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.volumetric_fog` — Volumetric Fog; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.depth_pass` — Depth Pass; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.
- `baltor.motion.render.normal_pass` — Normal Pass; **status:** `proposed`; suggested implementation: VTK or engine-specific worker.

### E.validate — 12 records
- `baltor.motion.validate.rig_schema_validation` — Rig Schema Validation; **status:** `implemented`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.acyclic_kinematic_graph` — Acyclic Kinematic Graph; **status:** `implemented`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.joint_limit_checker` — Joint Limit Checker; **status:** `implemented`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.axis_normalization` — Axis Normalization; **status:** `proposed`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.fk_consistency` — Fk Consistency; **status:** `implemented`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.ik_trajectory_solver` — Ik Trajectory Solver; **status:** `proposed`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.geometry_overlap_checker` — Geometry Overlap Checker; **status:** `proposed`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.self_collision` — Self Collision; **status:** `proposed`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.external_collision` — External Collision; **status:** `proposed`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.ground_contact` — Ground Contact; **status:** `proposed`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.physics_dynamics` — Physics Dynamics; **status:** `proposed`; suggested implementation: numpy / physics engine optional.
- `baltor.motion.validate.uncertainty_flagging` — Uncertainty Flagging; **status:** `proposed`; suggested implementation: numpy / physics engine optional.

## Appendix F — 50 additional composition/style ideas
All 50 are explicitly **backlog/not implemented** in the style-idea source. Existing working ten templates are in §3.7.

### F.Comic & illustrated
- manga-panel tracking — original reusable composition.
- newspaper halftone — original reusable composition.
- inked noir vignette — original reusable composition.
- paper-cut stop motion — original reusable composition.
- retro pulp covers — original reusable composition.

### F.Community & conversion
- before-after dev demos — original reusable composition.
- five-way tool benchmark — original reusable composition.
- interactive skill request — original reusable composition.
- two-option audience vote — original reusable composition.
- evidence-backed feed alert — original reusable composition.

### F.Dimensional design
- 2.5D diorama — original reusable composition.
- layered depth-card wall — original reusable composition.
- stereoscopic split — original reusable composition.
- floating browser windows — original reusable composition.
- 3D exploded panel — original reusable composition.

### F.Effects & transitions
- particle field split — original reusable composition.
- mask wipe through trees — original reusable composition.
- whip-zoom insert — original reusable composition.
- match-cut camera anchors — original reusable composition.
- shock-wave text reveal — original reusable composition.

### F.Film & photography
- documentary lower-thirds — original reusable composition.
- analog film gate — original reusable composition.
- archival dossier — original reusable composition.
- found-footage camcorder — original reusable composition.
- telescope surveillance — original reusable composition.

### F.Games & arcade
- pixel HUD platformer — original reusable composition.
- roguelike inventory — original reusable composition.
- survival-map minimap — original reusable composition.
- tactical overwatch — original reusable composition.
- simulation replay — original reusable composition.

### F.Infographics
- animated timeline — original reusable composition.
- unit economics waterfall — original reusable composition.
- ranked skill database — original reusable composition.
- radial category explorer — original reusable composition.
- AI feed alert report — original reusable composition.

### F.Sound & rhythm
- physics musical notes — original reusable composition.
- subtle waveform equalizer — original reusable composition.
- ASMR mechanical loops — original reusable composition.
- beat-synced infographic — original reusable composition.
- footstep-driven cuts — original reusable composition.

### F.Tech & research
- isometric CAD projection — original reusable composition.
- annotated node DAG — original reusable composition.
- model evaluation charts — original reusable composition.
- shader laboratory — original reusable composition.
- graph-neural network view — original reusable composition.

### F.Type & typography
- karaoke word highlighting — original reusable composition.
- right-edge vertical titles — original reusable composition.
- center stage kinetic type — original reusable composition.
- text-in-world signboards — original reusable composition.
- minimal type-only vignette — original reusable composition.

## Appendix G — 45 v0.3.1 future operator ideas
**Not implemented in v0.3.1.** This section reproduces the earlier operator roadmap as source text so an agent can retain the candidate names and contextual descriptions.

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

## Appendix H — Small, verified workspace artifact digest manifest
This manifest is produced by hashing selected local files on **this host**. SHA-256 protects file integrity after transfer but does not imply a file is safe, rights-cleared or production-approved.

| File (relative to `/mnt/data/`) | Bytes | SHA-256 |
|---|---:|---|
| `BALTOR_MOTION_FOUNDRY_SOURCE.zip` | 101,913 | `5347ff5b9bb767d678755aa7602aadc01ad508ad0f8ab0f60b4822cb91e0fb4b` |
| `Baltor_Stick_Motion_Composer_Source.zip` | 1,128,173 | `d9c59b3e1ea8d94eaeefaccd71fe98fdcf5615ae7d64d5653e2a776c2be04b5b` |
| `Baltor_Spatial_Motion_Composer_v02_Source.zip` | 2,562,138 | `a25e6e97f9a4f09c8eb8e84904541672b20b9ff3226d5c159d6d17605de1e754` |
| `Baltor_Harness_Tools_v031_Binaries_and_Source.zip` | 8,294,465 | `e931833e284fde0947497ef89022c35295e36b77a37f0948e89d119c8b367aa0` |
| `Baltor_Capability_Foundry_v04_COMPLETE.zip` | 11,520,121 | `39f30eaceaa6b0b586572c1d7d44f71faf3c28a216809305634cbdfbdeecdfaf` |
| `Baltor_Capability_Distiller_v04_Binaries_Source.zip` | 4,166,522 | `3cb1df7e36097f5bb1a6c0faa7a9fa666f48f44a5845aad841838a91afb6ea6a` |
| `Baltor_Original_Ad_Prototypes_30s.zip` | 7,360,541 | `b1d57bd34ee95c2ae74a2c02da256d6a12c002b2a12eec5f3825aeb016d7ccd1` |
| `BALTOR_MASTER_AGENT_HANDOFF_2026-10-19.md` | See postscript | See postscript: self-hash would be circular |
| `particulate_motion_demo_with_audio.mp4` | 3,059,129 | `6e872cc8c802f5184a973a8592aa164f92a011c8f764902900e32db037a0f122` |
| `baltor_motion_foundry/outputs/robot_arm_motion.mp4` | 1,861,698 | `8783879ae0460abe1947b2afea2b63b53c4b7c531e7bddd2ed00c3dbb3ae50fc` |
| `baltor_motion_foundry/outputs/twin_drawer_motion.mp4` | 1,900,843 | `54a2cc28e5579a1e78e7ea0ed16e67a7951594cd4fc76c1e51bb28dcac10bf02` |
| `baltor_motion_foundry/outputs/folding_chair_motion.mp4` | 2,173,958 | `ef991c321e7a881b4d39e27b33e561a15cfd9dec0b8c1a18007105bf9cdac761` |
| `baltor_motion_foundry/outputs/baltor_motion_foundry_60s.mp4` | 3,696,671 | `745e2e8a94f5b604840bfdea368d1c10d20533fcde2081b7377a5ee0e7978592` |
| `baltor_motion_foundry/stick_composer/outputs/the_last_signal_70s_FINAL.mp4` | 14,836,109 | `5dbc3a81faef8b7797206dbb3fffc68cd9b278b92b3d7be3b041f10d5482bf31` |
| `baltor_motion_foundry/stick_composer/spatial_v02/outputs/baltor_spatial_layout_study_65s_FINAL.mp4` | 11,184,680 | `e3f046d5773a5e4230daf807906db82e512799f909a43e5e94ff597eb570c75d` |
| `baltor_harness_tools_v01/outputs/layered-release/runs/d987989f8d245d5b2fff/media/video.mp4` | 1,496,189 | `1d468387f386679c148b5deaca902968185e45117e85fef61d26bf1bbcad9e56` |
| `Baltor_Capability_Distiller_v04/outputs/commercial/last_tab_kinetic_30s.mp4` | 1,699,073 | `a5aa12777c6a81603feecfce7b066092aca267705371ea47f921fca3adc2b5a8` |
| `Baltor_Capability_Distiller_v04/outputs/commercial/last_tab_paper_30s.mp4` | 1,159,708 | `0692e42cbd961053be7d3d3acc37bd246056d3dcfa4ff2bfa39f23d9ec8faf92` |

## Appendix I — User-supplied additional link/raw-source index
These links appeared in attached transcripts or the conversation; tracking/query parameters generally add no source substance, so prefer canonical URLs except where the user’s intended maturity labels are relevant.

| Source | URL |
|---|---|
| Particulate Facebook hashtag | https://www.facebook.com/hashtag/particulate |
| Chai_AI Facebook hashtag | https://www.facebook.com/hashtag/chai_ai |
| Stickvival Facebook page | https://www.facebook.com/Stickvival.FB |
| Stickvival Facebook Reels | https://www.facebook.com/profile.php?id=61594987697295&sk=reels_tab |
| Stickvival YouTube channel | https://www.youtube.com/@Stickvival-YT |
| Particulate paper | https://openaccess.thecvf.com/content/CVPR2026/html/Li_Particulate_Feed-Forward_3D_Object_Articulation_CVPR_2026_paper.html |
| Particulate official code | https://github.com/RuiningLi/particulate |
| Instruct-Particulate | https://instruct-particulate.github.io/ |
| Articraft main | https://github.com/articraftresearch/Articraft |
| UniMate official | https://github.com/Friedrich-M/UniMate |
| Huashu Art Motion | https://github.com/alchaincyf/huashu-art-motion |
| Fox 3D demo | https://fox.baltor.ai/ |
| Fox motion study | https://fox.baltor.ai/motion-study.html |
| Kaggle safety writeup (user maturity tag) | https://www.kaggle.com/competitions/openai-gpt-oss-20b-red-teaming/writeups/llm-complicity-in-modern-slavery-from-native-blind?category=polished |
| Kaggle Gemma writeup (user maturity tag) | https://www.kaggle.com/competitions/gemma-4-good-hackathon/writeups/new-writeup-1779103293133?category=polished |
| DueCare (user maturity tag) | https://tayloramareltech.github.io/duecare/?category=polished |
| Safety framework (user maturity tag) | https://github.com/TaylorAmarelTech/llm-safety-framework?category=polished |
| Papers (user maturity tag) | https://papers.tayloramarel.com/?category=agent-managed |
| Blog (user maturity tag) | https://blog.tayloramarel.com/?category=agent-managed |
| Repos (user maturity tag) | https://repos.tayloramarel.com/?category=agent-managed |
| Portfolio reviewer instructions | https://github.com/Amarel-Taylor-Scott/ai-safety-papers-and-monographs-2026/blob/main/AGENTS.md |
| Evaluation agents.md | https://evals.tayloramarel.com/agents.md |
| Machine index | https://index.tayloramarel.com/index.json |

### YouTube clip reference IDs (exact supplied links)
- https://www.youtube.com/shorts/07qXw53UcQg
- https://www.youtube.com/shorts/cm8TMqlfo8k
- https://www.youtube.com/shorts/6052j4zquic
- https://www.youtube.com/shorts/KmEDRpgYD6Y
- https://www.youtube.com/shorts/B-YR2K-MORw
- https://www.youtube.com/shorts/nnN8zHnKaLM
- https://www.youtube.com/watch?v=CCUSpJkAfgU
- https://www.youtube.com/watch?v=SIZXW0ABD9g
- https://www.youtube.com/watch?v=k_z3nxFsxyo
- https://www.youtube.com/watch?v=L3FZk417lxs
- https://www.youtube.com/watch?v=brWjBipZHVU

## Appendix J — Source interpretation and known gaps

1. **Earlier Muse transcript:** states that a reference style bible and a 200-idea bank were created, but their underlying complete files are not currently mounted here. Do not claim to have the full 200 ideas or downloaded creator footage without inspecting those assets. Art-deco gold/isometric blueprint concepts survive in the present styles list.
2. **Previous claim of 100+ searches and downloadable YouTube streams:** no completed frame-by-frame report on the cited external videos is present in this local workspace. Treat as unverified prior agent intent, not accomplished analysis.
3. **Particulate runtime:** neural inference was not executed in these local demonstrations. Authored 3D rigs must retain their provenance label and should not be compared as though they were inferred predictions.
4. **Composers:** v0.2 authoring editor preview is not necessarily pixel-equal to rendered Python frames; v0.3.1 deterministic claims are environment-scoped; v0.4 external operator catalog names are proposals.
5. **Full 60s/300s cinema:** storyboards, render prototypes and released short MP4s exist, but not a professional narrated 60s flagship ad or fully rendered 300s original feature in the inspected directories.
6. **Full chat-history ingestion:** no current verified complete archive coverage; earlier history compilations had gaps and multiple versions. Obtain user-approved export and reconcile first.
7. **Connected platforms:** links to the user’s websites, social pages, GitHub, Google Drive and Kaggle do not by themselves grant editing/posting permission; capabilities and authorization must be checked separately.
8. **Publishing:** exact final media and accompanying copy always require the user’s explicit approval. All current prototype assets should be treated as unpublished.
9. **Current websites and source libraries:** snapshot dates, API status, licensing, user/market adoption, and benchmarks change; reverify before making public claims.
10. **Safety and humanity-first orientation:** separate speculative research plans from experimentally established results; build tools for human benefit without implying clinical, engineering or criminal-investigation accuracy not demonstrated.

---

## Closing instruction to the receiving agent

**Act as an engineer and researcher maintaining an evidence ledger, not a content-generation machine producing lists.** The next best step is to select a small coherent capability, implement it in a bounded reusable worker, test against golden fixtures and the existing reproducible MP4 workflows, record hashes/version/rights/limits, then demonstrate a genuine finished improvement. Preserve the entire broader road map above as searchable reference material. Ask for explicit publication approval only after final content and copy exist, never as a substitute for doing the permitted engineering work.

