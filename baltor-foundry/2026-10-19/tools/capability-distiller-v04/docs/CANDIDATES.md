# Baltor — candidate capabilities (NOT BUILT)

All projects and operator names below are **research/planning candidates**. An official documentation URL indicates a source to evaluate, not that a wrapper exists, its use is licensed, or its results are deterministic.

**68 sources**, **294 proposed operators** across **8 families**.

| Priority | Family | Source | Proposals | Execution profile |
|---|---|---|---:|---|
| P1 | Code | [Git](https://git-scm.com/docs/git) | 4 | deterministic_local |
| P1 | Code | [Pytest](https://github.com/pytest-dev/pytest) | 4 | algorithmic_local |
| P1 | Code | [Ruff](https://github.com/astral-sh/ruff) | 4 | deterministic_local |
| P1 | Code | [Tree-sitter](https://github.com/tree-sitter/tree-sitter) | 5 | deterministic_local |
| P1 | Code | [ast-grep](https://github.com/ast-grep/ast-grep) | 4 | deterministic_local |
| P1 | Code | [ripgrep](https://github.com/BurntSushi/ripgrep) | 4 | deterministic_local |
| P1 | Code | [uv](https://github.com/astral-sh/uv) | 4 | environment_sensitive |
| P1 | Data | [DuckDB](https://duckdb.org/docs/stable/clients/cli/overview) | 5 | deterministic_local |
| P1 | Data | [SQLite](https://sqlite.org/cli.html) | 5 | deterministic_local |
| P1 | Eval | [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | 5 | model_inference |
| P1 | Eval | [Promptfoo](https://github.com/promptfoo/promptfoo) | 5 | model_inference |
| P1 | Motion | [Blender](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) | 7 | algorithmic_local |
| P1 | Motion | [FFmpeg](https://ffmpeg.org/ffmpeg-filters.html) | 14 | deterministic_local |
| P1 | Motion | [OpenCV](https://github.com/opencv/opencv) | 7 | algorithmic_local |
| P1 | Motion | [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | 5 | deterministic_local |
| P1 | Motion | [Playwright](https://github.com/microsoft/playwright) | 6 | environment_sensitive |
| P1 | Motion | [PySceneDetect](https://www.scenedetect.com/docs/cli.html) | 5 | algorithmic_local |
| P1 | Motion | [glTF Transform](https://github.com/donmccurdy/glTF-Transform) | 6 | algorithmic_local |
| P1 | Motion | [resvg](https://github.com/linebender/resvg) | 4 | deterministic_local |
| P1 | Optimization | [Google OR-Tools](https://github.com/google/or-tools) | 6 | algorithmic_local |
| P1 | Optimization | [Optuna](https://github.com/optuna/optuna) | 5 | seeded_stateful |
| P1 | Security | [Cosign](https://github.com/sigstore/cosign) | 4 | identity_stateful |
| P1 | Security | [Syft](https://github.com/anchore/syft) | 4 | deterministic_local |
| P1 | Skills | [Agent Skills Specification](https://github.com/agentskills/agentskills) | 5 | deterministic_local |
| P1 | Skills | [Anthropic Skills](https://github.com/anthropics/skills) | 4 | human_review |
| P1 | Skills | [MCP Reference Servers](https://github.com/modelcontextprotocol/servers) | 5 | environment_sensitive |
| P1 | Skills | [Official MCP Registry](https://github.com/modelcontextprotocol/registry) | 5 | network_stateful |
| P1 | Skills | [OpenAI Skills](https://github.com/openai/skills) | 4 | human_review |
| P2 | Audio | [Rubber Band](https://breakfastquay.com/rubberband/) | 3 | algorithmic_local |
| P2 | Audio | [Silero VAD](https://github.com/snakers4/silero-vad) | 3 | model_inference |
| P2 | Audio | [aubio](https://github.com/aubio/aubio) | 4 | algorithmic_local |
| P2 | Audio | [librosa](https://github.com/librosa/librosa) | 5 | algorithmic_local |
| P2 | Audio | [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | 4 | model_inference |
| P2 | Code | [Gitleaks](https://github.com/gitleaks/gitleaks) | 3 | deterministic_local |
| P2 | Code | [Semgrep](https://github.com/semgrep/semgrep) | 3 | algorithmic_local |
| P2 | Data | [Apache Arrow](https://arrow.apache.org/) | 3 | deterministic_local |
| P2 | Data | [MarkItDown](https://github.com/microsoft/markitdown) | 3 | environment_sensitive |
| P2 | Data | [NetworkX](https://github.com/networkx/networkx) | 4 | deterministic_local |
| P2 | Data | [Polars](https://github.com/pola-rs/polars) | 4 | deterministic_local |
| P2 | Data | [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) | 3 | deterministic_local |
| P2 | Data | [Trafilatura](https://github.com/adbar/trafilatura) | 4 | network_stateful |
| P2 | Data | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 3 | network_stateful |
| P2 | Eval | [Garak](https://github.com/NVIDIA/garak) | 4 | model_inference |
| P2 | Eval | [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | 4 | model_inference |
| P2 | Motion | [Godot](https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html) | 5 | environment_sensitive |
| P2 | Motion | [ImageMagick](https://imagemagick.org/) | 5 | deterministic_local |
| P2 | Motion | [Manim](https://github.com/ManimCommunity/manim) | 6 | algorithmic_local |
| P2 | Motion | [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) | 4 | algorithmic_local |
| P2 | Motion | [Motion Canvas](https://github.com/motion-canvas/motion-canvas) | 4 | algorithmic_local |
| P2 | Motion | [Sharp](https://github.com/lovell/sharp) | 4 | deterministic_local |
| P2 | Motion | [trimesh](https://github.com/mikedh/trimesh) | 5 | algorithmic_local |
| P2 | Optimization | [PyPSA](https://github.com/PyPSA/PyPSA) | 3 | solver_dependent |
| P2 | Optimization | [RDKit](https://github.com/rdkit/rdkit) | 4 | algorithmic_local |
| P2 | Optimization | [SciPy](https://github.com/scipy/scipy) | 4 | algorithmic_local |
| P2 | Security | [Grype](https://github.com/anchore/grype) | 3 | environment_sensitive |
| P2 | Security | [OPA](https://github.com/open-policy-agent/opa) | 3 | deterministic_local |
| P2 | Security | [Trivy](https://github.com/aquasecurity/trivy) | 3 | environment_sensitive |
| P2 | Security | [Wasmtime](https://github.com/bytecodealliance/wasmtime) | 3 | bounded_sandbox |
| P2 | Skills | [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) | 5 | human_review |
| P2 | Skills | [Superpowers](https://github.com/obra/superpowers) | 4 | human_review |
| P2 | Skills | [Trail of Bits Skills](https://github.com/trailofbits/skills) | 4 | human_review |
| P2 | Skills | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) | 4 | human_review |
| P2 | Skills | [Vercel Skills CLI](https://github.com/vercel-labs/skills) | 4 | network_stateful |
| P3 | Audio | [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M) | 3 | model_inference |
| P3 | Motion | [Instruct-Particulate](https://instruct-particulate.github.io/) | 2 | model_inference |
| P3 | Motion | [Particulate](https://github.com/RuiningLi/particulate) | 3 | model_inference |
| P3 | Motion | [Remotion](https://www.remotion.dev/docs/) | 4 | licensing_review |
| P3 | Optimization | [OpenMM](https://github.com/openmm/openmm) | 3 | gpu_dependent |

## Proposed operations by source

### Git

`repo.diff`, `repo.history`, `repo.worktree`, `repo.blame`

### Pytest

`test.collect`, `test.run`, `test.junit_export`, `test.failures`

### Ruff

`python.lint`, `python.format`, `python.imports`, `python.rules.audit`

### Tree-sitter

`code.parse`, `code.syntax_tree`, `code.symbols`, `code.complexity_features`, `code.dependency_edges`

### ast-grep

`code.ast.search`, `code.ast.replace`, `code.ast.lint`, `code.ast.query`

### ripgrep

`repo.search`, `repo.files`, `repo.regex_matches`, `repo.ignore_aware`

### uv

`python.env.lock`, `python.script.run`, `python.tool.resolve`, `python.package.audit`

### DuckDB

`data.query`, `data.csv_to_parquet`, `data.aggregate`, `data.dedupe`, `data.validate`

### SQLite

`db.query`, `db.migrate`, `db.index`, `db.integrity`, `db.export`

### Inspect AI

`eval.inspect.run`, `eval.scorers`, `eval.sample.trace`, `eval.model.compare`, `eval.dataset`

### Promptfoo

`eval.dataset.run`, `eval.agent.redteam`, `eval.report`, `eval.baselines`, `eval.testcase.generate`

### Blender

`blender.scene.build`, `blender.camera.animate`, `blender.material.apply`, `blender.render.frames`, `blender.render.turntable`, `blender.export.glb`, `blender.compositor`

### FFmpeg

`video.xfade`, `video.zoompan`, `video.crop`, `video.concat`, `video.scale`, `video.stabilize`, `video.subtitle.burn`, `video.palette`, `video.framerate`, `video.encode`, `audio.duck`, `audio.loudnorm`, `audio.mix`, `audio.fade`

### OpenCV

`vision.flow`, `vision.motion_segments`, `vision.track`, `vision.feature_match`, `vision.camera_hint`, `vision.edge`, `vision.histogram`

### OpenTimelineIO

`timeline.read`, `timeline.write`, `timeline.validate`, `timeline.merge`, `timeline.export_edl`

### Playwright

`browser.screenshot`, `browser.record`, `browser.trace`, `browser.scroll_capture`, `browser.layout.measure`, `browser.dom.snapshot`

### PySceneDetect

`shots.content_detect`, `shots.adaptive_detect`, `shots.fade_detect`, `shots.split`, `shots.keyframes`

### glTF Transform

`gltf.inspect`, `gltf.optimize`, `gltf.simplify`, `gltf.compress`, `gltf.partition`, `gltf.texture.optimize`

### resvg

`svg.rasterize`, `svg.check`, `svg.thumbnail`, `graphics.overlay.render`

### Google OR-Tools

`opt.assignment`, `opt.schedule`, `opt.knapsack`, `opt.routing`, `opt.cp_sat`, `opt.min_cost_flow`

### Optuna

`opt.search`, `opt.prune`, `opt.study`, `opt.pareto`, `opt.parameter_grid`

### Cosign

`artifact.sign`, `artifact.verify`, `artifact.attest`, `oci.verify`

### Syft

`artifact.sbom`, `artifact.dependencies`, `artifact.license_inventory`, `artifact.provenance`

### Agent Skills Specification

`skill.frontmatter.validate`, `skill.inventory`, `skill.schema.emit`, `skill.lint`, `skill.provenance`

### Anthropic Skills

`skill.workflow.extract`, `skill.script.inventory`, `skill.templates.index`, `skill.fixtures.plan`

### MCP Reference Servers

`mcp.filesystem.read`, `mcp.git.inspect`, `mcp.fetch.extract`, `mcp.tool.catalog`, `mcp.tool.schema`

### Official MCP Registry

`mcp.registry.discover`, `mcp.registry.metadata`, `mcp.registry.version`, `mcp.registry.dedupe`, `mcp.registry.classify`

### OpenAI Skills

`skill.workflow.test`, `skill.readme.generate`, `skill.cli_contract.propose`, `skill.agents_yaml.describe`

### Rubber Band

`audio.time_stretch`, `audio.pitch_shift`, `audio.transient_preserve`

### Silero VAD

`audio.vad`, `audio.speech_regions`, `audio.silence_trim`

### aubio

`audio.pitch`, `audio.beat`, `audio.onset.aubio`, `audio.silence`

### librosa

`audio.tempo`, `audio.onset`, `audio.beats`, `audio.spectral`, `audio.features`

### whisper.cpp

`speech.transcribe`, `speech.segment`, `speech.translate`, `speech.confidence`

### Gitleaks

`repo.secrets.scan`, `repo.secrets.redact`, `repo.leak.report`

### Semgrep

`code.semgrep.scan`, `code.security.findings`, `code.rule.quality`

### Apache Arrow

`data.arrow.convert`, `data.schema.validate`, `data.columnar.write`

### MarkItDown

`document.markdown.convert`, `document.metadata.extract`, `document.batch_extract`

### NetworkX

`graph.components`, `graph.centrality`, `graph.shortest_path`, `graph.layout`

### Polars

`data.lazy_transform`, `data.group`, `data.join`, `data.profile`

### RapidFuzz

`text.fuzzy_match`, `text.deduplicate`, `text.similarity`

### Trafilatura

`web.article.extract`, `web.links.extract`, `web.metadata`, `web.cleantext`

### yt-dlp

`video.reference.metadata`, `video.reference.download_authorized`, `video.reference.subtitles`

### Garak

`eval.probes`, `eval.detectors`, `eval.safety_report`, `eval.batch`

### lm-evaluation-harness

`eval.lm_bench`, `eval.task_suite`, `eval.metrics`, `eval.model_matrix`

### Godot

`game.scene.render`, `game.physics.simulate`, `game.assets.import`, `game.capture`, `game.headless.test`

### ImageMagick

`image.compose`, `image.resize`, `image.trim`, `image.montage`, `image.compare`

### Manim

`math.scene.render`, `math.axes.animate`, `math.formula.transition`, `math.chart.animate`, `math.geometry.visualize`, `math.explainer.sequence`

### Mermaid CLI

`diagram.flowchart`, `diagram.sequence`, `diagram.export_svg`, `diagram.export_png`

### Motion Canvas

`motioncanvas.scene.render`, `motioncanvas.vector.animate`, `motioncanvas.timeline`, `motioncanvas.graphs`

### Sharp

`image.batch_resize`, `image.transcode`, `image.composite`, `image.metadata`

### trimesh

`mesh.inspect`, `mesh.repair`, `mesh.measure`, `mesh.slice`, `mesh.export`

### PyPSA

`sdg.grid.optimize`, `sdg.energy_balance`, `sdg.scenario_compare`

### RDKit

`chem.molecule.validate`, `chem.descriptors`, `chem.substructure`, `chem.conformers`

### SciPy

`opt.nonlinear`, `opt.root`, `opt.integrate`, `opt.stats`

### Grype

`artifact.vulnerability.scan`, `artifact.advisory.matches`, `artifact.remediation`

### OPA

`policy.rego.eval`, `policy.deny`, `policy.constraints`

### Trivy

`container.vuln.scan`, `repo.config.scan`, `artifact.license.scan`

### Wasmtime

`wasm.module.run`, `wasm.component.validate`, `wasm.fuel_bound`

### BMad Method

`workflow.prd.validate`, `workflow.architecture.audit`, `workflow.story.compile`, `workflow.testplan`, `workflow.requirement_trace`

### Superpowers

`workflow.red_green_refactor`, `workflow.checkpoint`, `workflow.baseline_eval`, `workflow.verification`

### Trail of Bits Skills

`security.review.plan`, `security.issue_triage`, `security.rule_check`, `security.test_harness`

### Vercel Agent Skills

`skill.react.rules`, `web.performance.audit`, `web.patterns.check`, `web.accessibility.rules`

### Vercel Skills CLI

`skill.package.discover`, `skill.package.install_plan`, `skill.package.diff`, `skill.package.inventory`

### Kokoro TTS

`audio.tts`, `audio.voice.select`, `audio.tts.batch`

### Instruct-Particulate

`rig.instruct.predict`, `rig.instruct.constraints`

### Particulate

`rig.particulate.predict`, `rig.particulate.export_urdf`, `rig.particulate.export_glb`

### Remotion

`remotion.render`, `remotion.composition`, `remotion.props.variant`, `remotion.snapshot`

### OpenMM

`molecular.energy`, `dynamics.simulate`, `molecular.forcefield`

