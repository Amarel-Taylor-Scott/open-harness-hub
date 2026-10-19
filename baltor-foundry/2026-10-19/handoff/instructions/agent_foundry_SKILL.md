---
name: baltor-capability-distiller
description: Discover local Agent Skills and conservatively propose parameterized, sandbox-ready operator contracts; compile storyboards, validate spatial layouts, and generate bounded variation grids without executing untrusted scripts.
license: User-owned prototype; choose license before redistribution.
---
# Baltor Capability Distiller v0.4

Use this skill when an agent needs to inventory available local `SKILL.md` files, propose reliable CLI adapters, validate graphics layouts, or compile a deterministic advertising storyboard. This skill is **not an interpreter for arbitrary skills**. It does not download or run external instructions.

## Discover

1. Run `baltor-distill doctor`.
2. Scan an explicitly approved local read-only directory:
   `baltor-distill scan --root /approved/skills --out /work/scan.json`
3. Read `/work/scan.json` and review flagged shell/network/credential indicators.
4. Generate proposed, non-executable contracts:
   `baltor-distill propose --catalog /work/scan.json --out /work/proposals.json`
5. **Do not execute or install a proposal.** Independently implement reviewed behavior in a pinned worker and only mark implemented after tests, a license check, output verification, and approval.

## Video preproduction

- `baltor-distill layout --input examples/layout_ad_v04.json --out /work/layout_report.json`
- `baltor-distill timeline --input examples/flagship_superbowl_style_storyboard.json --out /work/spot`
- `baltor-distill variants --input examples/ad_campaign_variants.json --out /work/variations.json`

The `timeline` command emits `compiled_storyboard.json`, `timeline.csv`, and `captions.srt`. It does **not** render pixels, synthesize voices, or execute FFmpeg.

## Contract and safety expectations

- Explicit, typed parameters. No `eval`, dynamic shell, unreviewed skill code, or automatic imports from the Internet.
- No network, credentials, social publishing, or filesystem mutation outside approved output paths.
- Record exact tool version, input SHA-256, candidate status, source attribution, execution environment, budgets, and test evidence.
- Cap recursion, maximum files, iteration grids, runtime, output size and memory.
- Model-based outputs are not necessarily deterministic from fixed seeds; declare model hash, sampler/hardware/library details and measured variance.
- Use an OS-level container/VM and privilege restrictions for untrusted content; this binary does not implement kernel-level confinement.
- Preserve licensed originals and never reuse third-party assets or scripts without authorization.
- Keep video publication disabled until the exact final assets and marketing copy are approved by the user.
