# Prompt-injection heuristic detectors

*rule-pack* · `rule-pack/grep-prompt-injection-heuristics` · v0.1.0 · beta

Heuristic regex patterns that flag likely prompt-injection attempts
in input, retrieved documents, or tool results. Inspired by garak
probe families (`promptinject`, `latentinjection`, `ansiescape`,
`encoding`, `dan`) and LLM Guard's `PromptInjection` scanner.

These are FAST FIRST-PASS heuristics; pair with a small-model
classifier (`processor/prompt-injection-detector`) for robust
defense. False positives are common; use to TRIGGER a review or
paraphrase, not to block outright.

| axis | value |
|---|---|
| industry | security, ai, cross_industry |
| capability | safety_gating, classification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `ignore_previous_instructions` | high | prompt_injection.override | `(?i)ignore (the (?:previous|prior|above) )?(?:instructions|prompt|message|dir...` |
| `you_are_now_role_override` | medium | prompt_injection.role_play | `(?i)you (?:are|will be|must be) (?:now |henceforth )?(?:a|an|the) [a-z]+ (?:t...` |
| `dan_jailbreak` | high | prompt_injection.jailbreak | `(?i)\b(DAN|do anything now|developer mode|jailbreak|liberate)\b` |
| `system_prompt_leak_request` | high | prompt_injection.leak | `(?i)(repeat|reveal|tell me|show me|print|output) (the |your )?(?:system promp...` |
| `encoding_attack_base64` | high | prompt_injection.encoding | `(?i)decode (the |this )?base64.{0,40}?(then|and) (execute|follow|do|perform)` |
| `ansi_escape_injection` | high | prompt_injection.terminal_escape | `\x1b\[[0-9;]*[A-Za-z]` |
| `invisible_unicode_tag_chars` | critical | prompt_injection.invisible_unicode | `[\u{E0000}-\u{E007F}]` |
| `zero_width_characters` | medium | prompt_injection.steganography | `[\u200b\u200c\u200d\u2060\ufeff]` |
| `indirect_injection_markdown` | medium | prompt_injection.markdown | `(?i)\[.*?\]\(.*?(?:ignore|reveal|system prompt|disregard).*?\)` |
| `tool_invocation_in_doc` | high | prompt_injection.tool_invocation | `(?i)<tool[\s_-]?(?:call|use)>|\{\{\s*tool\s*\(.*\)\s*\}\}` |
| `grandma_attack` | high | prompt_injection.social_engineering | `(?i)(grandma|grandmother) (used to|would) (tell|recite|sing) (me )?(.{0,40}?)...` |
| `instruction_injection_keyword_list` | high | prompt_injection.override | `(?i)(ignore|disregard|forget|override) (above|previous|all) (instructions|rul...` |

