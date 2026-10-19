#!/usr/bin/env python3
"""Manually researched candidate adapters. Each proposed operator is UNIMPLEMENTED.
No packages are downloaded and no third-party code is redistributed.
"""
import json, pathlib, collections
ROOT=pathlib.Path(__file__).parent
# family | project | official source | runtime | target | priority (1-highest) | proposed operations
raw = r'''
Motion|FFmpeg|https://ffmpeg.org/ffmpeg-filters.html|native_binary|deterministic_local|1|video.xfade;video.zoompan;video.crop;video.concat;video.scale;video.stabilize;video.subtitle.burn;video.palette;video.framerate;video.encode;audio.duck;audio.loudnorm;audio.mix;audio.fade
Motion|PySceneDetect|https://www.scenedetect.com/docs/cli.html|python_cli|algorithmic_local|1|shots.content_detect;shots.adaptive_detect;shots.fade_detect;shots.split;shots.keyframes
Motion|OpenTimelineIO|https://github.com/AcademySoftwareFoundation/OpenTimelineIO|python_adapter|deterministic_local|1|timeline.read;timeline.write;timeline.validate;timeline.merge;timeline.export_edl
Motion|Blender|https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html|headless_app|algorithmic_local|1|blender.scene.build;blender.camera.animate;blender.material.apply;blender.render.frames;blender.render.turntable;blender.export.glb;blender.compositor
Motion|glTF Transform|https://github.com/donmccurdy/glTF-Transform|node_cli|algorithmic_local|1|gltf.inspect;gltf.optimize;gltf.simplify;gltf.compress;gltf.partition;gltf.texture.optimize
Motion|resvg|https://github.com/linebender/resvg|rust_native_cli|deterministic_local|1|svg.rasterize;svg.check;svg.thumbnail;graphics.overlay.render
Motion|Manim|https://github.com/ManimCommunity/manim|python_renderer|algorithmic_local|2|math.scene.render;math.axes.animate;math.formula.transition;math.chart.animate;math.geometry.visualize;math.explainer.sequence
Motion|Playwright|https://github.com/microsoft/playwright|browser_worker|environment_sensitive|1|browser.screenshot;browser.record;browser.trace;browser.scroll_capture;browser.layout.measure;browser.dom.snapshot
Motion|OpenCV|https://github.com/opencv/opencv|native_python|algorithmic_local|1|vision.flow;vision.motion_segments;vision.track;vision.feature_match;vision.camera_hint;vision.edge;vision.histogram
Motion|ImageMagick|https://imagemagick.org/|native_cli|deterministic_local|2|image.compose;image.resize;image.trim;image.montage;image.compare
Motion|Sharp|https://github.com/lovell/sharp|node_native|deterministic_local|2|image.batch_resize;image.transcode;image.composite;image.metadata
Motion|Godot|https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html|headless_app|environment_sensitive|2|game.scene.render;game.physics.simulate;game.assets.import;game.capture;game.headless.test
Motion|Motion Canvas|https://github.com/motion-canvas/motion-canvas|node_renderer|algorithmic_local|2|motioncanvas.scene.render;motioncanvas.vector.animate;motioncanvas.timeline;motioncanvas.graphs
Motion|Mermaid CLI|https://github.com/mermaid-js/mermaid-cli|node_cli|algorithmic_local|2|diagram.flowchart;diagram.sequence;diagram.export_svg;diagram.export_png
Motion|Remotion|https://www.remotion.dev/docs/|node_renderer|licensing_review|3|remotion.render;remotion.composition;remotion.props.variant;remotion.snapshot
Motion|trimesh|https://github.com/mikedh/trimesh|python_lib|algorithmic_local|2|mesh.inspect;mesh.repair;mesh.measure;mesh.slice;mesh.export
Motion|Particulate|https://github.com/RuiningLi/particulate|cuda_model|model_inference|3|rig.particulate.predict;rig.particulate.export_urdf;rig.particulate.export_glb
Motion|Instruct-Particulate|https://instruct-particulate.github.io/|model_worker|model_inference|3|rig.instruct.predict;rig.instruct.constraints
Audio|whisper.cpp|https://github.com/ggml-org/whisper.cpp|native_model_binary|model_inference|2|speech.transcribe;speech.segment;speech.translate;speech.confidence
Audio|Silero VAD|https://github.com/snakers4/silero-vad|onnx_model|model_inference|2|audio.vad;audio.speech_regions;audio.silence_trim
Audio|Kokoro TTS|https://huggingface.co/hexgrad/Kokoro-82M|model_worker|model_inference|3|audio.tts;audio.voice.select;audio.tts.batch
Audio|Rubber Band|https://breakfastquay.com/rubberband/|native_cli|algorithmic_local|2|audio.time_stretch;audio.pitch_shift;audio.transient_preserve
Audio|librosa|https://github.com/librosa/librosa|python_lib|algorithmic_local|2|audio.tempo;audio.onset;audio.beats;audio.spectral;audio.features
Audio|aubio|https://github.com/aubio/aubio|native_cli|algorithmic_local|2|audio.pitch;audio.beat;audio.onset.aubio;audio.silence
Skills|Agent Skills Specification|https://github.com/agentskills/agentskills|metadata_rules|deterministic_local|1|skill.frontmatter.validate;skill.inventory;skill.schema.emit;skill.lint;skill.provenance
Skills|Anthropic Skills|https://github.com/anthropics/skills|skill_library|human_review|1|skill.workflow.extract;skill.script.inventory;skill.templates.index;skill.fixtures.plan
Skills|OpenAI Skills|https://github.com/openai/skills|skill_library|human_review|1|skill.workflow.test;skill.readme.generate;skill.cli_contract.propose;skill.agents_yaml.describe
Skills|Vercel Agent Skills|https://github.com/vercel-labs/agent-skills|skill_library|human_review|2|skill.react.rules;web.performance.audit;web.patterns.check;web.accessibility.rules
Skills|Superpowers|https://github.com/obra/superpowers|skill_library|human_review|2|workflow.red_green_refactor;workflow.checkpoint;workflow.baseline_eval;workflow.verification
Skills|Trail of Bits Skills|https://github.com/trailofbits/skills|skill_library|human_review|2|security.review.plan;security.issue_triage;security.rule_check;security.test_harness
Skills|BMad Method|https://github.com/bmad-code-org/BMAD-METHOD|skill_library|human_review|2|workflow.prd.validate;workflow.architecture.audit;workflow.story.compile;workflow.testplan;workflow.requirement_trace
Skills|MCP Reference Servers|https://github.com/modelcontextprotocol/servers|mcp_servers|environment_sensitive|1|mcp.filesystem.read;mcp.git.inspect;mcp.fetch.extract;mcp.tool.catalog;mcp.tool.schema
Skills|Official MCP Registry|https://github.com/modelcontextprotocol/registry|api_registry|network_stateful|1|mcp.registry.discover;mcp.registry.metadata;mcp.registry.version;mcp.registry.dedupe;mcp.registry.classify
Skills|Vercel Skills CLI|https://github.com/vercel-labs/skills|node_cli|network_stateful|2|skill.package.discover;skill.package.install_plan;skill.package.diff;skill.package.inventory
Code|Tree-sitter|https://github.com/tree-sitter/tree-sitter|native_parser|deterministic_local|1|code.parse;code.syntax_tree;code.symbols;code.complexity_features;code.dependency_edges
Code|ast-grep|https://github.com/ast-grep/ast-grep|native_cli|deterministic_local|1|code.ast.search;code.ast.replace;code.ast.lint;code.ast.query
Code|ripgrep|https://github.com/BurntSushi/ripgrep|native_cli|deterministic_local|1|repo.search;repo.files;repo.regex_matches;repo.ignore_aware
Code|Ruff|https://github.com/astral-sh/ruff|native_cli|deterministic_local|1|python.lint;python.format;python.imports;python.rules.audit
Code|Semgrep|https://github.com/semgrep/semgrep|cli_engine|algorithmic_local|2|code.semgrep.scan;code.security.findings;code.rule.quality
Code|Gitleaks|https://github.com/gitleaks/gitleaks|native_cli|deterministic_local|2|repo.secrets.scan;repo.secrets.redact;repo.leak.report
Code|uv|https://github.com/astral-sh/uv|native_cli|environment_sensitive|1|python.env.lock;python.script.run;python.tool.resolve;python.package.audit
Code|Pytest|https://github.com/pytest-dev/pytest|python_cli|algorithmic_local|1|test.collect;test.run;test.junit_export;test.failures
Code|Git|https://git-scm.com/docs/git|native_cli|deterministic_local|1|repo.diff;repo.history;repo.worktree;repo.blame
Data|DuckDB|https://duckdb.org/docs/stable/clients/cli/overview|native_cli|deterministic_local|1|data.query;data.csv_to_parquet;data.aggregate;data.dedupe;data.validate
Data|SQLite|https://sqlite.org/cli.html|native_cli|deterministic_local|1|db.query;db.migrate;db.index;db.integrity;db.export
Data|Polars|https://github.com/pola-rs/polars|python_rust|deterministic_local|2|data.lazy_transform;data.group;data.join;data.profile
Data|Apache Arrow|https://arrow.apache.org/|native_lib|deterministic_local|2|data.arrow.convert;data.schema.validate;data.columnar.write
Data|MarkItDown|https://github.com/microsoft/markitdown|python_cli|environment_sensitive|2|document.markdown.convert;document.metadata.extract;document.batch_extract
Data|Trafilatura|https://github.com/adbar/trafilatura|python_cli|network_stateful|2|web.article.extract;web.links.extract;web.metadata;web.cleantext
Data|yt-dlp|https://github.com/yt-dlp/yt-dlp|python_cli|network_stateful|2|video.reference.metadata;video.reference.download_authorized;video.reference.subtitles
Data|RapidFuzz|https://github.com/rapidfuzz/RapidFuzz|python_native|deterministic_local|2|text.fuzzy_match;text.deduplicate;text.similarity
Data|NetworkX|https://github.com/networkx/networkx|python_lib|deterministic_local|2|graph.components;graph.centrality;graph.shortest_path;graph.layout
Eval|Promptfoo|https://github.com/promptfoo/promptfoo|cli_framework|model_inference|1|eval.dataset.run;eval.agent.redteam;eval.report;eval.baselines;eval.testcase.generate
Eval|Inspect AI|https://github.com/UKGovernmentBEIS/inspect_ai|python_framework|model_inference|1|eval.inspect.run;eval.scorers;eval.sample.trace;eval.model.compare;eval.dataset
Eval|Garak|https://github.com/NVIDIA/garak|python_cli|model_inference|2|eval.probes;eval.detectors;eval.safety_report;eval.batch
Eval|lm-evaluation-harness|https://github.com/EleutherAI/lm-evaluation-harness|python_framework|model_inference|2|eval.lm_bench;eval.task_suite;eval.metrics;eval.model_matrix
Optimization|Google OR-Tools|https://github.com/google/or-tools|native_solver|algorithmic_local|1|opt.assignment;opt.schedule;opt.knapsack;opt.routing;opt.cp_sat;opt.min_cost_flow
Optimization|Optuna|https://github.com/optuna/optuna|python_lib|seeded_stateful|1|opt.search;opt.prune;opt.study;opt.pareto;opt.parameter_grid
Optimization|SciPy|https://github.com/scipy/scipy|python_native|algorithmic_local|2|opt.nonlinear;opt.root;opt.integrate;opt.stats
Optimization|PyPSA|https://github.com/PyPSA/PyPSA|python_model|solver_dependent|2|sdg.grid.optimize;sdg.energy_balance;sdg.scenario_compare
Optimization|RDKit|https://github.com/rdkit/rdkit|native_python|algorithmic_local|2|chem.molecule.validate;chem.descriptors;chem.substructure;chem.conformers
Optimization|OpenMM|https://github.com/openmm/openmm|native_gpu|gpu_dependent|3|molecular.energy;dynamics.simulate;molecular.forcefield
Security|Syft|https://github.com/anchore/syft|native_cli|deterministic_local|1|artifact.sbom;artifact.dependencies;artifact.license_inventory;artifact.provenance
Security|Cosign|https://github.com/sigstore/cosign|native_cli|identity_stateful|1|artifact.sign;artifact.verify;artifact.attest;oci.verify
Security|Grype|https://github.com/anchore/grype|native_cli|environment_sensitive|2|artifact.vulnerability.scan;artifact.advisory.matches;artifact.remediation
Security|Trivy|https://github.com/aquasecurity/trivy|native_cli|environment_sensitive|2|container.vuln.scan;repo.config.scan;artifact.license.scan
Security|OPA|https://github.com/open-policy-agent/opa|native_cli|deterministic_local|2|policy.rego.eval;policy.deny;policy.constraints
Security|Wasmtime|https://github.com/bytecodealliance/wasmtime|wasm_runtime|bounded_sandbox|2|wasm.module.run;wasm.component.validate;wasm.fuel_bound
'''
entries=[];ops=[];seen=set()
for line in raw.strip().splitlines():
 fields=line.split('|')
 assert len(fields)==7,fields
 family,name,url,runtime,mode,priority,oplist=fields
 o=oplist.split(';')
 for op in o:
  assert op not in seen,(name,op)
  seen.add(op)
 obj={'family':family,'project':name,'source_url':url,'runtime':runtime,'execution_mode':mode,'priority':int(priority),'review_status':'candidate_research_not_executed','licensing':'review exact upstream version and bundled dependencies','proposed_operators':o}
 entries.append(obj)
 for op in o:
  ops.append({'id':op,'family':family,'source_project':name,'source_url':url,'execution_mode':mode,'status':'PROPOSAL_ONLY_NOT_EXECUTABLE','candidate_priority':int(priority),'requires_review':['license','security','runtime','parameter_schema','golden_test']})
entries.sort(key=lambda x:(x['priority'],x['family'],x['project']))
ops.sort(key=lambda x:x['id'])
summary={'sources':len(entries),'candidate_operators':len(ops),'by_family':dict(sorted(collections.Counter(x['family'] for x in ops).items())),'by_priority':dict(sorted(collections.Counter(x['candidate_priority'] for x in ops).items()))}
(ROOT/'docs'/'RESEARCH_SOURCE_CATALOG.json').write_text(json.dumps({'schema':'baltor.research_sources/1','generated_from':'manually_curated_inventory','summary':summary,'sources':entries},indent=2,ensure_ascii=False)+'\n')
(ROOT/'docs'/'CANDIDATE_OPERATOR_REGISTRY.json').write_text(json.dumps({'schema':'baltor.candidate_operations/1','summary':summary,'operators':ops},indent=2)+'\n')
lines=['# Baltor — candidate capabilities (NOT BUILT)', '', 'All projects and operator names below are **research/planning candidates**. An official documentation URL indicates a source to evaluate, not that a wrapper exists, its use is licensed, or its results are deterministic.', '',f"**{summary['sources']} sources**, **{summary['candidate_operators']} proposed operators** across **{len(summary['by_family'])} families**.",'', '| Priority | Family | Source | Proposals | Execution profile |', '|---|---|---|---:|---|']
for row in entries:
 lines.append(f"| P{row['priority']} | {row['family']} | [{row['project']}]({row['source_url']}) | {len(row['proposed_operators'])} | {row['execution_mode']} |")
lines+=['','## Proposed operations by source','']
for row in entries:
 lines+=['### '+row['project'],'',', '.join('`'+o+'`' for o in row['proposed_operators']),'']
(ROOT/'docs'/'CANDIDATES.md').write_text('\n'.join(lines)+'\n')
print(summary)
