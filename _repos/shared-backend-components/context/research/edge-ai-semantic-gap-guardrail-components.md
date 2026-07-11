# Edge AI Semantic Gap Guardrail Components

Regex-only guardrails create a semantic gap: they inspect the visible string, while the risky instruction may live inside an encoded, nested, or transformed segment. This is especially important for edge AI because mobile and local runtimes cannot cheaply copy cloud agent patterns that make frequent classifier calls to large hosted models.

## Component Family

This research seed should become a reusable family of components:

- recursive encoding detector and sanitizer;
- depth-limited decoder for Base64, hex, URL encoding, and similar reversible encodings;
- post-decode safety evaluator that checks decoded text before the original prompt reaches the model;
- edge micro-model authorization router for low-latency Stage 1 checks;
- main-model escalation gate for uncertain or high-risk inputs;
- prompt-framing and overload detector that spots academic, hypothetical, or multi-task wrappers used to lower scrutiny;
- edge cost and latency estimator that accounts for RAM, battery, thermal throttling, and model context switching;
- audit trace emitter for every decoded segment, decision, escalation, and final allow/block route.

## Why This Matters

The high-value pattern is not another larger keyword list. It is a pipeline that changes the inspection surface before classification. Every suspicious segment should produce a normalized evidence record:

- original segment hash;
- encoding probability;
- decode path;
- recursion depth;
- decoded text hash;
- safety findings;
- uncertainty score;
- route decision;
- model/runtime cost estimate;
- audit trace reference.

This makes the component searchable, testable, and reusable across platform moderation, enterprise copilots, browser-based local assistants, mobile agents, and offline regulated workflows.

## Edge Deployment Shape

A practical edge deployment should avoid calling the main LLM for every low-risk tool or prompt action. The default route is:

1. cheap syntactic screening for obvious cases;
2. recursive decode of suspicious spans with strict depth and size limits;
3. CPU-bound micro-model safety check for decoded and original text;
4. escalation to the main local model only when uncertainty or severity is high;
5. audit trace and policy decision output.

This gives the registry a clear set of pre-LLM, LLM, and post-LLM components that can be wired into many pipelines.

## Daily Factory Expansion

Turn this family into daily candidate rows by varying:

- encoding type;
- nesting depth;
- modality;
- device class;
- route policy;
- allowed task type;
- risk category;
- latency target;
- review requirement;
- evaluation fixture.

The daily component factory can generate thousands of safe synthetic fixtures without storing real user prompts, secrets, or harmful operational instructions.
