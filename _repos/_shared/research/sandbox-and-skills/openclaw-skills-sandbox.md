# OpenClaw — skills/tools/sandbox design reference
- Summary: clean separation of skills (SKILL.md markdown + YAML frontmatter, multi-dir load precedence), tools, plugins, sandboxing, security. **Skill Workshop** = agent drafts skill PROPOSALS into a review queue; humans inspect/apply (exactly our agent-proposes/human-disposes pattern). Trust envelopes via ClawHub; sandbox modes off/non-main/all; backends Docker/SSH/OpenShell; explicit warnings re Docker socket, bind mounts, credential roots, host paths, egress, escape surfaces.
- Capability slot: `skill_source`/`skill_format` (@candidate) + `sandbox_policy`/`tool_policy` (@research reference).
- Useful: skill load precedence, per-agent allowlists, proposal queue, trust envelopes/verification cards, sandbox/tool policy interplay, public-vs-gated skills, secret-injection scope.
- Risks: third-party skills are untrusted by design; do NOT copy its trust model blindly — ours must be stricter (customer context + governed outputs).
- **Adoption: skill_source.openclaw@candidate; sandbox_policy.reference_openclaw@research. Mirror the proposal-queue + allowlist + trust-envelope posture in our SandboxPolicy.**
