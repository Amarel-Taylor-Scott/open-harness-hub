> **EDITOR'S NOTE (captured 2026-06-06 from the owner).** Canonical spec for the Shared Sandbox + Skill
> Digestion Lab. Executed INCREMENTALLY. **DONE + proven (flywheel 343):** the Shared Sandbox Gateway core —
> SandboxProviderPort + LocalTempdirProvider (deny-by-default: no network/secrets, scoped tempdir, timeout,
> no-host-escape; external providers candidate-only, never run on host) in src/teleon/sandbox/; contracts
> schemas/sandbox/{SandboxRunRequest,SandboxRunResult,SandboxPolicy}.v1 (registered); provider catalog
> architecture/sandbox_provider_catalog.json (local golden + CubeSandbox/E2B/Daytona/Docker/OpenShell/K8s
> candidates, each w/ local_equivalent + proof_to_promote); proof scripts/check_sandbox_gateway.py; research
> records research/sandbox-and-skills/{cubesandbox,hermes-skills,openclaw-skills-sandbox,skill-tool-hubs}.md.
> Sandbox output is NEVER truth — evidence for the promotion gate only. **QUEUED — the Skill/Tool DIGESTION
> LAB** (the money loop: skill → cheaper deterministic runtime): skill-format adapters (OpenClaw/Hermes/Codex/
> agentskills SKILL.md → SkillArtifact.v1); skill_digester + contract_inferencer + model_compatibility (via the
> Inference Gateway) + determinism_extractor (extract deterministic substeps → cheap runtime path, keep original
> as fallback) + runtime_candidate_builder → Teleon PurposeTask candidate; digestion contracts
> (SkillDigestRun/ToolDigestRun/CapabilityInferenceReport/ModelCompatibilityReport/DeterminismExtractionReport);
> open-hub candidate outputs; /api/sandbox + /api/digestion + UI; the full redteam.

# /workflows /shared-sandbox-and-skill-digestion-lab
A shared SandboxProviderPort (used by Teleon/Baltor/all hubs) + a skill/tool digestion lab that turns expensive
skills/tools into cheaper, more deterministic runtimes. Discovery≠trust · sandbox-run≠trust · eval-pass≠truth ·
skill/tool/LLM output≠truth · candidate≠active · promotion needs contract+sandbox+eval+redteam+receipts+policy.

## SHARED SANDBOX + SKILL DIGESTION CLAUSE (carry forward)
All external skills/tools/generated implementations/repo-derived candidates/self-evolved paths run through the
shared SandboxProviderPort BEFORE promotion. Local sandbox = golden path; CubeSandbox/E2B/Daytona/Docker/
OpenShell/SSH/K8s = candidates until proven. Skill digestion parses skill formats, infers capability/input/
output contracts, tests model compatibility, detects deterministic substeps, converts repeated skill behavior
into cheaper deterministic runtimes when proven, and PRESERVES the original skill/tool as fallback.

## Candidates recorded (see research/sandbox-and-skills/)
sandbox.cubesandbox@candidate (E2B-compatible micro-VM; needs kernel/root/XFS/KVM — not golden path) ·
skill_source.hermes@candidate · skill_source.openclaw@candidate (proposal-queue + trust-envelope = our model) ·
skill_source.codex/agentskills_io/voltagent@candidate · tool_source.mcp_registry/modelcontextprotocol_servers@candidate.
*(Full PART 1–17 detail in the owner's message + the proven core above; build the QUEUED digestion lab next.)*
