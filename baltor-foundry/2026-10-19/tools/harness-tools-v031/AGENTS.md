# AGENTS.md — Baltor Harness Worker

Read SKILL.md and README.md before modifying a recipe. The binary is intentionally multi-call: `baltor-run`, `baltor-plan`, `baltor-verify`, `baltor-graph`, etc. can be symlinks to `baltorctl`.

Allowed operations in this build: scene.frames, audio.synth, frames.metrics, frames.contact, frames.transform, frames.overlay, frames.spatial, timeline.compile, video.encode, video.probe, video.sample, layout.lint, artifact.hash.

Recipes are JSON `baltor.harness/1` and must validate. Source inputs belong under the workspace `inputs/` directory. Jobs are content-addressed as `runs/<fingerprint>` and include deterministic file manifests. `run --force` replaces a known run only after all replacement steps complete successfully; don't force unless deliberately recomputing.

Never try to fetch third-party videos unless permitted and supported by access controls. This worker does not include network downloaders. Never incorporate protected reference footage into an output without sufficient rights.

Containerized deployment: see Containerfile + scripts/run_container.sh; runtime Docker/Podman is required. Do not fall back to privileged local execution if the container runtime is unavailable for untrusted inputs.

Tests: `go test ./...` and `scripts/test_release.sh`. Create a new release version on any executable logic change so the run fingerprint changes accordingly. Retain known-good run manifests when assessing regressions.
