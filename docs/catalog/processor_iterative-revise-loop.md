# Iterative revise loop

*processor* · `processor/iterative-revise-loop` · v0.1.0 · experimental

The "send the response back to the LLM with accumulating context" primitive.
Loops:
  1. Run an inner harness call.
  2. Run one or more verification processors on the response.
  3. If any verifier fails (citation coverage, schema, factuality,
     safety), append the failure as additional context and call the
     inner harness again.
  4. Stop when (a) all verifiers pass, (b) max_iterations hit, or
     (c) cost ceiling breached.

This is the key primitive for self-correction loops: Self-Refine,
Constitutional-AI critique-revise, Self-RAG retrieve-then-judge,
Corrective-RAG with knowledge refinement, Reflexion. Distinct from
`processor/self-refine-critique` (which is a single critique-revise
pair); this primitive is the GENERIC LOOP that any verifier list can
drive.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | reasoning, verification, agent_loop |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



