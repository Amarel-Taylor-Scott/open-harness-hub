# MCP & Skill security — a REQUIRED CI lane (not optional)

MCP servers and agent skills are a supply-chain surface. **Tool poisoning** — malicious
instructions hidden in an MCP tool *description* (invisible to the user, visible to the model) —
is a documented, prevalent threat: Invariant Labs found it on **~5.5% of public MCP servers**, with
working PoCs exfiltrating SSH keys/config from Claude Desktop and Cursor. So Baltor treats MCP/skill
scanning as a **required CI lane**, not a nice-to-have.

## Verified scanners (research-confirmed, 2026)
- **Snyk Agent Scan** — the former **Invariant Labs `mcp-scan`** (Invariant acquired by Snyk, Jun 2025; rebranded ~Apr 2026). Detects tool poisoning, rug pulls (via **hash-based tool pinning**), cross-origin escalation, prompt injection across Claude Desktop/Code, Cursor, Gemini CLI, Windsurf. Pre-deploy static + real-time proxy.
- **Cisco `mcp-scanner`** (cisco-ai-defense) — OSS, pre-deploy static scanning.
- (Reference: the OWASP MCP Top-10 / tool-poisoning writeups.)

## The CI lane (what fails the build)
- MCP tool descriptions contain **no hidden/invisible instructions** (prompt-injection patterns → fail).
- Tool manifests are **content-hashed**; a manifest change requires review (**rug-pull / pinning** defense).
- **Write** tools are classified high-risk; source-system **bulk-export** tools are **blocked by default**.
- Generated OpenAPI→MCP tools are **scanned before exposure** (read tools auto-expose only after a scan; write tools require approval — see addendum D).
- Skills **declare their allowed tools**; a skill cannot silently add shell/network/source-write tools.
- Findings at/above "high" (tool poisoning, hidden injection) **fail CI**.

## Baltor invariants this enforces
ACL-before-model · raw-source-expansion control · prompt-injection handling · audit trails ·
the MCP/tool boundary · agents act only inside a bounded `DecisionContext`. The verification rail
(continuous + adversarial) and the Gold-Pack Contract are the runtime counterparts; this is the
build-time guard.

## Next (implementation)
`scripts/scan_mcp_manifests.py` + `scripts/scan_agent_skills.py` (regex + LLM-as-judge fallback when
a real scanner is absent — real-or-labeled-seam) + `.github/workflows/mcp-security.yml`, each with a
self-test (a poisoned-description fixture must FAIL). Pair with the verified scanners where available.
