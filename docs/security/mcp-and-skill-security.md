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

## The adopted deep scanner: NVIDIA **SkillSpector** (the "real scanner" SEAM)

`scan_mcp_manifests.py` / `scan_agent_skills.py` were always the deterministic *floor* with a
declared SEAM for "a real scanner ... when present." **SkillSpector** (github.com/nvidia/skillspector,
**Apache-2.0**) is adopted as that scanner — it is the most complete for *skills + MCP* specifically:

- **68 vulnerability patterns / 17 categories**: prompt injection + jailbreak, data exfiltration
  (API keys, env vars, file enumeration), privilege escalation / credential theft, **supply chain**
  (unpinned deps, live **OSV.dev** CVE lookup, obfuscation), **excessive agency** (unrestricted tool
  access), dangerous code (**AST** detection of `exec`/`eval`/`subprocess`), **taint tracking**
  (credential/input → sink), **MCP-specific** (tool poisoning, least-privilege), **YARA** malware /
  webshell signatures.
- **Static-first, local-first**: stage 1 is regex + Python AST + OSV.dev (no model); stage 2 LLM is
  *optional* and supports **local Ollama** + `--no-llm` — so it satisfies the local-first / keyless law.
- **Outputs SARIF + exit codes** (0 safe / 1 unsafe / 2 error); runs as CLI, Docker, Python API, **or
  an MCP server for runtime install gating**. It fits behind a port exactly like every other adapter.

It composes with — does not replace — the already-named scanners (Snyk Agent Scan / ex-Invariant
`mcp-scan` with hash-pinning rug-pull defense; Cisco `mcp-scanner`). One `SkillScannerPort`, several
backends, deterministic floor always on.

## The descent ladder (deterministic-first, cost-ordered, honest-unavailable)

The cost-ordered ladder, same shape as every capability in this repo (cheap/deterministic/local first;
climb only when the cheaper rung can't resolve):

0. **Regex floor** — `scan_mcp_manifests.find_poison` + `scan_agent_skills` (shared `POISON_PATTERNS`).
   Always on, free, local, deterministic. Never skipped.
1. **SkillSpector static (`--no-llm`)** — AST, the 68 patterns, OSV.dev CVE lookup, YARA. Local, no model.
2. **SkillSpector + local Ollama** — context-aware semantic pass (~87% precision) to cut false positives.
   Local-first: no cloud key.
3. **SkillSpector + hosted LLM** (NVIDIA Build / Anthropic) — only for high-stakes artifacts the local
   rungs can't resolve, and only with the honest note that file contents leave the machine.

If SkillSpector is not installed, rung 0 still runs and the verdict is **labeled** "floor only, deep
scanner absent" (real-or-labeled-seam; escalate-before-concluding-unavailable) — never silently "clean."

## Two gates: what we INGEST and what we MAKE

Scanning is wired as two gates, the security counterpart of the promotion boundary:

- **Ingest gate (what we INGEST).** The discovery pipeline (`scripts/discovery_pipeline.py`: scrape
  GitHub / governed sources → classify → govern) scans every harvested **skill / MCP manifest / repo**
  *before* it becomes a candidate. A finding at/above **high** → the row is **quarantined**
  (`status=quarantined`, candidate-only, **never promoted**) with the SARIF attached to its
  `source_record`. Lossless: quarantined ≠ deleted — it stays with its finding for lineage + appeal.
- **Output gate (what we MAKE).** The promotion boundary
  (`scripts.db.daily_promotion_readiness_plan`) gains a security-scan gate alongside the existing
  review-ticket gate: a component / pipeline / skill **we generate** cannot become tenant-visible with
  an **open ≥high** security finding. The scan receipt joins the evidence ledger / audit log.

Both emit SARIF receipts into the audit log — *governance is the product*: provenance + a signed
"scanned, clean (or quarantined), here is the evidence" is the external moat, not a nice-to-have. The
AIDevObserver **footgun** detector is the *runtime* counterpart (catching the risky command in a live
session); these two gates are the *ingest-time* and *build-time* counterparts.

## Next (implementation)

1. `scripts/security/skill_scanner.py` — the **`SkillScannerPort`**: runs the descent ladder (regex
   floor → SkillSpector `--no-llm` → +local Ollama → +hosted), merges + normalizes findings to one
   schema, returns `{verdict, severity, findings[], scanner, sarif}`, honest-labels when SkillSpector
   is absent. `--self-test` with a poisoned fixture that MUST fail. Register in `run_proofs.py`.
2. Wire the **ingest gate** into `discovery_pipeline.py` (quarantine ≥high) and the **output gate** into
   `daily_promotion_readiness_plan` (block tenant-visibility on open ≥high).
3. `.github/workflows/mcp-security.yml` — the CI lane (SARIF upload; ≥high fails the build).
4. Pair with Snyk/Cisco where their licenses/keys are present (additional backends behind the port).
