# Baltor Capability Foundry — October 19, 2026

**Agent-facing archive:** A handoff of the Baltor capability-foundry, motion-composer and deterministic harness experiments.

## Start here

1. Read [`handoff/BALTOR_MASTER_AGENT_HANDOFF_2026-10-19.md`](handoff/BALTOR_MASTER_AGENT_HANDOFF_2026-10-19.md).
2. Consult [`handoff/HANDOFF_MANIFEST.json`](handoff/HANDOFF_MANIFEST.json) and the operator registries.
3. Use the tool sources under `tools/` and `motion/` only after reviewing `README.md`, `AGENTS.md`, `SKILL.md`, dependencies, and their tests.
4. Locate **complete binaries, bundled assets, MP4s, and deterministic execution archives** in the linked Google Drive archive. They are intentionally excluded from ordinary Git history.
5. Distinguish **implemented/tested** operators from catalogued **ideas/proposals**.

## Source directories

- `handoff/` — agent brief, references, registries, storyboard examples, evidence legend and backlog.
- `tools/capability-distiller-v04/` — Go CLI distiller, skill scanner, layout/timeline tools, creative prototype.
- `tools/harness-tools-v031/` — deterministic Go DAG runner, typed operators, video recipes and tests.
- `motion/spatial-composer-v02/` — parameterized layout renderer, editor, style rules, and storyboard.
- `motion/stick-composer-v01/` — layered 2D animation prototype, analyzer, shot plans.
- `references/` — Particulate-inspired animation technical study and procedural example.

## Drive archive

Google Drive folder: https://drive.google.com/drive/folders/1fnnHkCpluhLHIWVD0xlAu31KRxkruB5K

The Drive folder contains original MP4 demonstrations and the full source/binary packages. Review the included provenance and rights constraints before reuse.

## Important limitations

- Most proposed operator IDs are **not executable implementations**.
- Several target-platform binaries were cross-compiled but not executed there.
- Sandbox configuration exists, but true OCI/VM isolation was not validated.
- No third-party Facebook/YouTube footage was copied.
- Do not publish social posts, run externally sourced code without review, or deploy live websites without the owner's explicit approval.

## Distribution / security

This directory contains original project documentation and source, **not vendor model weights, paid assets, raw third-party media or compiled binaries**. Existing repository licensing and third-party component licenses must be respected.
