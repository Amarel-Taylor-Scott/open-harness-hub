# Baltor Capability Distiller v0.4

A **real native Go CLI**, designed to inventory local Agent Skills and generate **non-executable** operator proposals plus deterministic planning files for Baltor's video factory. It does not download, interpret, compile, or execute foreign scripts. No third-party source code is bundled.

## Binaries
- `bin/baltor-distill-linux-amd64` — tested here
- `bin/baltor-distill-linux-arm64` — cross-compiled, untested on target
- `bin/baltor-distill-darwin-arm64` — cross-compiled, untested on target
- `bin/baltor-distill-windows-amd64.exe` — cross-compiled, untested on target

## Commands
```bash
./bin/baltor-distill-linux-amd64 doctor
./bin/baltor-distill-linux-amd64 scan --root ./testdata/skills --out /tmp/skills.json
./bin/baltor-distill-linux-amd64 propose --catalog /tmp/skills.json --out /tmp/proposals.json
./bin/baltor-distill-linux-amd64 layout --input examples/layout_ad_v04.json --out /tmp/layout_report.json
./bin/baltor-distill-linux-amd64 timeline --input examples/flagship_superbowl_style_storyboard.json --out /tmp/timeline
./bin/baltor-distill-linux-amd64 variants --input examples/ad_campaign_variants.json --out /tmp/variants.json
./bin/baltor-distill-linux-amd64 hash --input /tmp/timeline/compiled_storyboard.json
```

Run `go test ./...` to reproduce the static tests. Distinct command behavior is in `docs/IMPLEMENTED_CONTRACTS.json`.

## Real outputs delivered here
- Four platform binaries, Go source and tests.
- Scan of the three distinct Baltor motion-foundry SKILL.md files already present locally.
- Proposed candidate contracts for those locally scanned skills — **not runnable operations**.
- 68 researched tool and skill ecosystems and 294 manually proposed operator names across 8 families.
- 20-shot, 60-second **original** cinematic-ad storyboard compiled into 1,440 video-frame slots at 24 fps, CSV and SRT.
- 32 deterministic style/camera/narrative/aspect-ratio variation configurations.
- Spatial collision/safe-zone audit of one example advertising layout.

## Trust boundaries
- The scanner reads only `SKILL.md` and file metadata from explicitly named local directories. It does not execute found scripts.
- It is not a full YAML parser, SAST scanner, or malware detector. Advanced frontmatter and uncommon layouts require review.
- A `candidate` in the registry is not an implemented tool. Only commands in `docs/IMPLEMENTED_CONTRACTS.json` exist in this binary.
- No OCI/VM isolation was run here; use external sandboxing for hostile content.
- Output paths and scanned root are chosen by caller and should be constrained by the enclosing harness.
- The storyboard is a preproduction spec: rendering, editing, TTS, audio mixing, and publication remain separate steps.

## Research and licensing
All catalog links reference external projects for evaluation. Verify per-version licensing and asset/model rights before redistributing dependencies. Current code in this package is original; library wrappers beyond the above 7 core commands have NOT been built.
