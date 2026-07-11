# Use case 2 - Code review with security

> Review a diff. Get file:line comments, OWASP/CWE/MITRE citations, and a numeric risk score.

## When to use

- PR review automation
- Pre-commit security gate
- Audit / red-team prep
- Onboarding review checklist enforcement

## Primary pipeline

[`pipeline/code-review-with-risk-score`](../catalog/pipeline_code-review-with-risk-score.md)

## Primitives used

| Layer | Component | What it does |
|---|---|---|
| GREP - cloud | `rule-pack/grep-cloud-secrets` | AWS/GCP/Azure/DO/OCI/Cloudflare keys in the diff |
| GREP - AI vendor | `rule-pack/grep-ai-vendor-keys` | Anthropic/OpenAI/HF/Cohere/Replicate/Groq/Together/etc. |
| GREP - VCS | `rule-pack/grep-vcs-platform-pats` | GitHub/GitLab/Atlassian/Bitbucket PATs |
| GREP - keys | `rule-pack/grep-private-key-blocks` | RSA/EC/OpenSSH/PGP/Age private-key blocks |
| GREP - prompt injection | `rule-pack/grep-prompt-injection-heuristics` | If the diff contains LLM-prompt strings |
| RAG | `knowledge-pack/owasp-top-10-llm` | OWASP Top 10 for LLM Apps citations |
| RAG | `knowledge-pack/mitre-attack-sample` | MITRE ATT&CK technique references |
| Persona | `persona/code-consultant` | Senior-engineer voice; specific fixes |
| Harness | `harness/text-safety-review` | Compose persona + RAG + citations |
| Verify | `processor/citation-coverage` | Every finding has a CWE/OWASP cite |

## Composition

```
diff_text
  → grep-cloud-secrets / ai-vendor-keys / vcs-pats / private-keys
  → owasp-top-10-llm retrieval
  → mitre-attack-sample retrieval
  → text-safety-review (persona/code-consultant)
  → citation-coverage
  → findings[], overall_verdict, overall_risk_score
```

## Sample inputs / outputs

```python
inputs = {
    "diff_text":     open(".git/diff_HEAD.txt").read(),
    "language_hint": "python"
}
# → findings: [
#     { file: "src/api.py:42", severity: "critical",
#       cwe: "CWE-798", owasp: "LLM06",
#       issue: "Hardcoded OpenAI API key (sk-...).",
#       fix:   "Move to env var; rotate the leaked key." },
#     ...
#   ]
# → overall_verdict: "block"
# → overall_risk_score: 9.5
```

## Install path

### Claude Code

```
/plugin marketplace add Amarel-Taylor-Scott/openhubforai@dist-published
/code-review-with-risk-score
```

Then pipe a diff:

```bash
git diff HEAD | claude /code-review-with-risk-score
```

### GitHub Actions (CI gate)

```yaml
# .github/workflows/security-review.yml
- uses: actions/checkout@v4
- run: pip install kaggle pyyaml jsonschema  # plus your local LLM client
- run: |
    git diff HEAD~1 > /tmp/diff.txt
    python scripts/run_pipeline.py pipeline/code-review-with-risk-score \
      --inputs /tmp/inputs.json | tee review.json
    # fail the build if overall_risk_score >= 7
    test "$(jq .overall_risk_score review.json)" -lt 7
```

## Customization knobs

- **Add language-specific lints**: bundle a new `rule-pack/grep-<lang>-anti-patterns`.
- **Stricter on AI keys**: change `rule-pack/grep-ai-vendor-keys` severity to `critical`+`halt`.
- **Different rubric**: write your own `rubric/code-review-v2` and set as the pipeline's `success_criteria`.
- **Faster on large diffs**: enable `processor/llmlingua-context-compressor` between RAG and the harness.
