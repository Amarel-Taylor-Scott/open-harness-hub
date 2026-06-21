# Use case: Personal LLM companion with preference layer

Encode an individual reviewer's preferences as a first-class layer that loads on top of any pipeline. The companion respects how *you* read code, write prose, and review research. No generic vendor voice. No re-correcting the same style mistake every session.

## What you get out of the box

- `persona/personal-coding-reviewer`: reviews diffs through your preferences. Default discipline: prefer editing existing files, no speculative abstractions, no impossible-case error handling, no narrative commentary, test UI changes before claiming done, confirm destructive actions.
- `persona/personal-writing-companion`: drafts and edits prose against your style. Default discipline: no em dashes, no marketing-speak (delve, leverage, robust, seamless, cutting-edge), no trailing summaries, cite or decline, minimize the diff when editing your draft.
- `knowledge-pack/personal-preferences-template`: 15 example preferences across scopes (writing.style, writing.discipline, coding.discipline, workflow.safety, workflow.communication). Each carries scope, preference text, why, strictness. **Fork and edit.**
- `rule-pack/grep-personal-style-flags`: detects disallowed idioms (em dash, marketing verbs, hedging adjectives, trailing summaries, fabricated-citation shapes).
- `pattern/personal-preference-layer`: the architectural pattern for wiring this in.
- `pipeline/personal-code-review-with-preferences`: a worked example.

## How preferences work

Preferences are records, not paragraphs:

```json
{
  "id": "no-em-dashes",
  "scope": "writing.style",
  "preference": "Do not use em dashes in any output rendered to the user. Use commas, colons, parentheses, or sentence breaks instead.",
  "why": "Personal style. Em dashes look like AI generation and harm the cadence of how I write.",
  "strictness": "hard"
}
```

The pipeline:

1. Loads the preferences pack at run-start.
2. Injects preferences into the persona system prompt as "user-specific overrides take precedence."
3. Runs the underlying pipeline (code review, writing, research).
4. Applies the personal-style rule pack to the generated output before delivery.
5. If any hard-strictness preference fires, regenerates or refuses + surfaces the violation.
6. Logs applied + violated preferences to the audit trace.

## Forking

The template lives at `knowledge-pack/personal-preferences-template` with data at `data/personal-preferences-pack/preferences.jsonl`. Fork the repo, edit the JSONL, and the personas load your version automatically.

For teams: keep a shared base persona + per-member preference packs. Each person's outputs are gated against their own pack. The team gets convergence on substance and divergence on style.

## Pairing patterns

- `pattern/personal-preference-layer`: the architectural pattern.
- `pattern/composable-success-criteria`: lets you add the style rule pack as a hard success criterion.
- `pattern/anti-over-prompting-as-crutch`: do not stuff preferences into the system prompt as prose. Use the typed knowledge pack + rule pack instead.
