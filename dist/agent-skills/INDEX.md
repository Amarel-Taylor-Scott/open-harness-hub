# Agent Skills bundle

# Open Harness Hub — Agent Skills bundle

This directory is the **Agent Skills export** of every harness and
pipeline in the hub. Agent Skills is an open standard (agentskills.io)
adopted by 40+ tools including Claude Code, OpenAI Codex, GitHub
Copilot, Gemini CLI, Cursor, VS Code, OpenHands, Roo Code, Goose,
Letta, Amp, Junie, Workshop, Tabnine, OpenCode, Factory, and more.

## Use as Claude Code skills

Copy any `<slug>/` directory under `~/.claude/skills/` or your
project's `.claude/skills/`:

```bash
cp -r dist/agent-skills/text-safety-review ~/.claude/skills/
```

Restart Claude Code; the skill is now available as
`/text-safety-review`.

## Use as a Claude Code plugin marketplace

The `.claude-plugin/marketplace.json` in this directory makes the
whole bundle a Claude Code plugin marketplace. Users can add it
with:

```
/plugin marketplace add <git-url-of-this-repo>
```

## Use in other Agent Skills-compatible tools

Every other tool that implements Agent Skills (Cursor, OpenHands,
Gemini CLI, Roo Code, etc.) accepts the same SKILL.md folder
layout. Check each tool's docs for the exact install path — the
contents are identical.

## Skills in this bundle

- `redact-pii-text/SKILL.md` — harness (`harness/redact-pii-text`)
- `clinical-decision-support/SKILL.md` — harness (`harness/clinical-decision-support`)
- `aml-investigation/SKILL.md` — harness (`harness/aml-investigation`)
- `code-act-jupyter/SKILL.md` — harness (`harness/code-act-jupyter`)
- `text-safety-review/SKILL.md` — harness (`harness/text-safety-review`)
- `plan-execute-critic-loop/SKILL.md` — pipeline (`pipeline/plan-execute-critic-loop`)
- `research-entity/SKILL.md` — pipeline (`pipeline/research-entity`)
- `multi-model-judging-ensemble/SKILL.md` — pipeline (`pipeline/multi-model-judging-ensemble`)
- `contract-clause-review/SKILL.md` — pipeline (`pipeline/contract-clause-review`)
- `chat-with-pdf-citations/SKILL.md` — pipeline (`pipeline/chat-with-pdf-citations`)
- `everything-research-pipeline/SKILL.md` — pipeline (`pipeline/everything-research-pipeline`)
- `code-review-with-risk-score/SKILL.md` — pipeline (`pipeline/code-review-with-risk-score`)
- `two-time-retrieve-rerank/SKILL.md` — pipeline (`pipeline/two-time-retrieve-rerank`)
- `deep-tier-supplier-audit/SKILL.md` — pipeline (`pipeline/deep-tier-supplier-audit`)
- `knowledge-graph-from-corpus/SKILL.md` — pipeline (`pipeline/knowledge-graph-from-corpus`)
- `deepseek-r1-code-interpreter-math/SKILL.md` — pipeline (`pipeline/deepseek-r1-code-interpreter-math`)
- `synthetic-data-gen-with-teacher-llm/SKILL.md` — pipeline (`pipeline/synthetic-data-gen-with-teacher-llm`)
- `supplier-policy-grading/SKILL.md` — pipeline (`pipeline/supplier-policy-grading`)
- `large-model-faiss-rag/SKILL.md` — pipeline (`pipeline/large-model-faiss-rag`)
- `swe-patch-sample-and-review/SKILL.md` — pipeline (`pipeline/swe-patch-sample-and-review`)
- `radiology-report-grading/SKILL.md` — pipeline (`pipeline/radiology-report-grading`)
- `multi-agent-debate-with-judge/SKILL.md` — pipeline (`pipeline/multi-agent-debate-with-judge`)
- `twenty-questions-agent/SKILL.md` — pipeline (`pipeline/twenty-questions-agent`)
- `vllm-batch-llm-inference/SKILL.md` — pipeline (`pipeline/vllm-batch-llm-inference`)
- `email-triage-and-draft/SKILL.md` — pipeline (`pipeline/email-triage-and-draft`)
- `verify-claim-against-corpus/SKILL.md` — pipeline (`pipeline/verify-claim-against-corpus`)
- `multi-doc-qa-subquestion/SKILL.md` — pipeline (`pipeline/multi-doc-qa-subquestion`)
- `deep-research-with-citations/SKILL.md` — pipeline (`pipeline/deep-research-with-citations`)
- `deep-research-supervisor-workers/SKILL.md` — pipeline (`pipeline/deep-research-supervisor-workers`)
- `perplexity-baseline-scoring/SKILL.md` — pipeline (`pipeline/perplexity-baseline-scoring`)
- `awq-quantized-inference/SKILL.md` — pipeline (`pipeline/awq-quantized-inference`)
- `llm-judge-essay-grading/SKILL.md` — pipeline (`pipeline/llm-judge-essay-grading`)
- `quantized-llm-inference/SKILL.md` — pipeline (`pipeline/quantized-llm-inference`)
- `brand-safe-product-photo/SKILL.md` — pipeline (`pipeline/brand-safe-product-photo`)
- `anonymized-illicit-recruitment-pattern-sharing/SKILL.md` — pipeline (`pipeline/anonymized-illicit-recruitment-pattern-sharing`)
- `code-act-jupyter-loop/SKILL.md` — pipeline (`pipeline/code-act-jupyter-loop`)
- `differential-diagnosis/SKILL.md` — pipeline (`pipeline/differential-diagnosis`)
- `suspicious-transaction-review/SKILL.md` — pipeline (`pipeline/suspicious-transaction-review`)
- `storm-persona-curation-article/SKILL.md` — pipeline (`pipeline/storm-persona-curation-article`)
- `self-rag-grade-and-revise/SKILL.md` — pipeline (`pipeline/self-rag-grade-and-revise`)
- `qwen-vllm-rerank-eedi/SKILL.md` — pipeline (`pipeline/qwen-vllm-rerank-eedi`)
