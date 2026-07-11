# Moat-cluster deep dives — verification-adjacent repos (2026-06-12)

Five web-grounded strategic deep dives (live-fetched from the repos, not training knowledge)
on the cluster that most directly touches the verification + portable-receipts + governed-
truth-promotion moat: **Langfuse** (observability), **Ragas + DeepEval** (eval),
**Guardrails-AI + NeMo** (guardrails), **vLLM + SGLang + LMCache** (self-hosted serving),
**DSPy** (prompt compilation). Each follows the repo's deep-dive idiom: what it is →
seam mapping → threat/validation → wrap shape → what-to-borrow → watch triggers. Companion
shallow intake: `github-repo-intel-2026-06-12.md`.

**The one-line thesis check across all five:** none of them does verification + portable
receipts + governed truth promotion. The eval/guardrails repos VALIDATE the gate pattern,
observability is COMPLEMENT (assurance-vs-logging), serving is an INTEGRATION decision, and
prompt-compilation is admissible only under the lossless law. The white space holds.

---

## 1. Langfuse — the closest competitive pressure (COMPLEMENT, not foil)

**What it is** (MIT except `/ee`; ClickHouse+Postgres+Redis+S3; OpenTelemetry-based):
"open-source LLM engineering platform." Data model is observability-native — Trace →
Observations (span/event/generation) → Sessions/Users/Scores; prompt management with version
**labels** (deploy via label, no code change); Datasets/Experiments/LLM-as-judge/Annotation-
Queues evals; 50+ integrations.

**Maps to our receipts plane — and the difference IS the thesis.** Their Trace = "what
HAPPENED" (after-the-fact log); our receipt = "what may be SERVED as truth" (forward verdict
+ source precedence + revocation/CDC). A Langfuse Score ANNOTATES a trace; it does not GATE
publication. **Assurance vs logging** — they record an outcome, we authorize one.

**Threat:** closest pressure because eval+prompt-mgmt+scores already touch quality. But
convergence needs a promotion boundary (candidate≠tenant-visible), source-precedence, and
revocation/CDC — none expressible in a trace-shaped append-only model. **Structurally cannot
do:** provider-neutral PORTABLE receipts a customer carries to another runtime (their value
is centralizing telemetry INTO Langfuse — the opposite); governed truth promotion. Their OTel
base CEMENTS them as a logging sink, not a verdict authority.

**Wrap:** swappable telemetry backend behind a `TelemetrySinkPort`; map execution→traces, our
verdict→a categorical Score (served/held/rejected), receipt id→trace attribute. FleetLedger
stays truth; Langfuse is a VIEW. Near-free given we already emit OTel/OpenInference.

**Borrow:** the span/event/generation data model (for the internal execution view, not the
receipt); prompt-versioning via labels; self-host-in-minutes (Compose/Helm/TF); the crisp
"MIT except /ee" open-core boundary as the OpenHarnessHub-open vs Teleon-commercial model.

**Watch triggers:** adds source-precedence / revocation / CDC to any object; ships a promotion
gate (candidate→published with a verdict); exports a portable provider-neutral receipt usable
by a NON-Langfuse runtime; turns Scores into publication-GATING verdicts; markets "governed
truth". Memory: `langfuse-observability-competitor`.

---

## 2. Guardrails-AI + NeMo-Guardrails — VALIDATE our gate pattern (wrap as candidate If-Statements)

**What they are** (both Apache-2.0): **Guardrails-AI** centers on the `Guard` abstraction —
compose **validators** (70 on the Hub, installed individually `guardrails hub install
hub://...`) each with an `on_fail` policy (`exception`/`fix`/`reask`/`filter`); plus
structured-output enforcement (`Guard.for_pydantic`) with a **reask** loop. **NeMo-Guardrails**
models conversations in **Colang** (a dialogue-flow DSL); rails run at five stages
(input/dialog/retrieval/execution/output) with jailbreak/injection detection + LLM self-checks.

**Maps to our deterministic gates:** RegexMatch/ValidJSON → structured-json-fence-guard;
PII/Secrets → PII gates; Prompt Injection Detector / NeMo input rails → prompt-injection-screen;
factuality/grounding checks → the abstain shape of clinical-abstention-gate. **Each Hub
validator is a candidate If-Statement.**

**The key line (our law cuts exactly here):** their Hub splits into (a) **genuinely
deterministic** validators — Valid JSON/SQL/Python, Regex, Detect PII, Secrets Present, Web
Sanitization, Exclude SQL Predicates (ADMIT as real gates after lift confirmation) — and (b)
**LLM-self-checks** — Llama Guard, Detect Jailbreak, Provenance LLM, LLM Critic, Hallucination,
Toxic Language LLM (the model judging the model). By our law an LLM-self-check is a **candidate
signal, never the final word**: it feeds a deterministic gate or opens a review ticket; the
deterministic gate disposes. NeMo's entire `self_check_*` family is signal-only.

**Borrow:** one-installable-validator = one If-Statement (their Hub granularity = our registry
granularity); the `on_fail` enum → our gate disposition vocabulary; the bounded reask loop for
structured-json-fence-guard; schema-driven structured output for any typed-JSON Action.

**Wrap:** individual validators behind a port; on hit → receipt + review ticket, never a silent
edit. Deterministic ones promote to active gates after lift; LLM-based stay signal-only. NeMo
sandboxed (Colang interpreter = bounded-agent, never truth).

**Watch/risk:** both Apache-2.0 (clean). Risks: Colang lock-in (extract the CHECK, not the
DSL); the LLM-self-check-undermines-determinism trap (never let model-judges-model graduate to
dispositive). Watch the Hub for new DETERMINISTIC validators worth importing.

---

## 3. vLLM + SGLang + LMCache — the self-hosted serving plane (INTEGRATION decision)

**What they are** (all Apache-2.0): **vLLM** — the de-facto OSS serving engine (PagedAttention;
automatic prefix caching; **OpenAI-compatible API server + native Anthropic Messages API**;
NVIDIA/AMD/TPU/Gaudi/CPU). **SGLang** — **RadixAttention** (a radix tree reusing shared prefixes
*across* requests, claimed up to 5x) + a structured-output frontend (compressed-FSM JSON, ~3x).
**LMCache** — a KV-cache layer offloading KV into a tiered hierarchy (CPU RAM / SSD / Redis / S3);
via **CacheBlend** reuses cached blocks at ANY position, not only the prefix.

**The integration decision:** **vLLM as the Teleon self-hosted serving engine, LMCache as the
KV layer beneath it, SGLang reserved for prefix-cache-heavy workloads.** vLLM wins on the seam —
its OpenAI-compatible server drops straight into our existing `OPENAI_BASE_URL` gateway path with
**zero adapter code** (and the native Anthropic Messages API covers the other provider shape).

**Ties to OUR components (the clean split):** `cache-kv-reuse` and `cache-prompt-prefix` are both
`deterministic: true` **planners** — they decide *what* to reuse; these engines *do* it.
`cache-kv-reuse.yaml` already names the backend in prose ("LMCache-style … ~7x TTFT") — LMCache/
CacheBlend IS that backend. `cache-prompt-prefix` marks the stable prefix: on hosted lanes that's
the ~90% Anthropic read discount; on the self-hosted lane the SAME mark is what SGLang's
RadixAttention / vLLM's APC key on. The **prefill re-read cost** (the context-efficiency thread)
is the precise tax these attack — our planner estimates the reusable span, their engine skips
recomputing it.

**What it unblocks:** a self-hosted lane = provider neutrality (the structural edge over OpenAI/
Ona), real cost control, and a genuinely cheap lane for cheapest-capable routing — the execution
surface under the owner's Ollama/Mistral/OpenRouter direction.

**Cost/ops reality (honest):** all three want **GPUs**. The Fly plane is CPU-batch today and Fly
GPUs were flagged dying **2026-08-01**, so this lane is **NOT viable on current infra** — it's a
deliberate-GPU decision (rented A100/H100 or a separable GPU host), not a flip of the existing
deploy. Until then hosted-API lanes carry production, and `cache-prompt-prefix` delivers value NOW
via provider prompt caching — free, no GPU.

**Watch:** all Apache-2.0 (clean). Pin versions, keep behind the gateway as swappable backends,
treat the 5x/7x figures as claims to re-verify.

---

## 4. DSPy — prompt compilation, admissible ONLY under the lossless law

**What it is** (MIT): "Program, don't prompt." A **Signature** is a typed input/output contract;
**Modules** (`Predict`/`ChainOfThought`/`ReAct`) are interchangeable execution strategies over a
signature; the load-bearing piece is the **compiler/optimizer** — give it examples + a scoring
function and it tunes prompts until quality converges. Optimizers: BootstrapFewShot (keep demos
that pass the metric), MIPROv2 (joint instruction+demo search), COPRO (coordinate-ascent
instructions), GEPA (reflective prompt evolution), BootstrapFinetune (distill into weights).
`compile()` returns an optimized program you `.save()`.

**Maps to two seams:** a compiled prompt is an OPTIMIZATION ARTIFACT, not truth. The compiled
instruction+demos block is what **system-prompt-builder** assembles by hand — DSPy is a
metric-driven generator of it. And the optimizer loop is a precise instance of the
**determinism-factory thesis**: compile a process (search→score→keep-what-passes) into a fixed
replayable target. DSPy distills "what to say to the model" from outcomes; our factory distills
"what rule to fire" from VERIFIED outcomes — same shape, different medium.

**The lossless-distillation tension (the core analysis):** DSPy's `.save()` keeps only the
WINNER — the search trace, rejected candidates, and per-candidate scores are discarded. Our top
law forbids exactly this (a winner without lineage to the losers is prohibited). To admit DSPy we
wrap `compile()` to emit a VERSIONED derived layer capturing: (a) the full optimization trace;
(b) the rejected instructions/demos (held-out ≠ deleted); (c) the metric, trainset hash, model/
version; (d) a rollback target = the un-compiled signature + baseline prompt. Promotable only with
that lineage + a side-by-side run vs baseline.

**Borrow:** metric-driven compilation for the determinism factory (but distill from VERIFIED
outcomes only — DSPy's scoring fn becomes our verification rail); the Signature abstraction as a
typed prompt contract for system-prompt-builder; the optimizer as a candidate behind an
`OptimizerPort`; demo-bootstrapping as a governed few-shot candidate feeding the review queue.

**The risk:** a compiled prompt is overfit to the optimizer's metric AND the specific model — our
provider-neutrality demands prompts survive model swaps. DSPy's portability covers the SIGNATURE,
not the compiled weights/demos (brittle across swaps). So DSPy belongs strictly on the OFFLINE
distillation path (compile per model, version per model, re-verify on swap), NEVER spliced into
the live provider-neutral routing plane.

**Watch:** MIT (clean). Track per-model metric drift; re-trigger compilation (or fail the gate) on
any provider/model change.

---

## 5. Ragas + DeepEval — candidate SCORERS for the gate (the actionable one)

**What they are** (both Apache-2.0): **Ragas** — RAG-eval metrics, mostly LLM-as-judge and
reference-FREE: **Faithfulness** (decompose response into claims, verify each vs context, score
`supported/total`; a deterministic `FaithfulnesswithHHEM` variant swaps the LLM for Vectara's
small open HHEM NLI classifier), **Response Relevancy**, **Context Precision** (`Σ Precision@k·v_k`,
in WithReference / WithoutReference forms) — plus genuinely deterministic metrics (Non-LLM String
Similarity, BLEU/ROUGE/CHRF, Exact Match, embedding Semantic Similarity). **DeepEval** — a
pytest-shaped harness (`assert_test`, `deepeval test run`); every metric is self-explaining
(score + reason); **G-Eval** (custom-criteria LLM judge, explicitly NOT deterministic); **DeepTeam**
(red-team: 40+ vulnerabilities × 10+ attacks).

**Maps to our seam — and the seam ALREADY EXISTS.** `scripts/foundry/measure.py` is offline-capped:
it scores recorded answers with a `DeterministicChecker` (token_f1) and honestly returns
`lift = None` when no live scorer is wired. It exposes exactly three Protocols —
`BareModel.answer()`, `PipelineRunner.run()`, `Judge.score()`. Ragas/DeepEval metrics are the
**candidate scorers** that fill that gap: not our gate, our gate's INPUTS.

**What to borrow (the concrete wiring):**
- **Faithfulness (reference-free)** → the **lift signal**: run on bare vs pipeline answer; `Δfaithfulness
  > 0` is structural evidence the corpus closed a hallucination gap.
- **Context Precision WithoutReference** → proves the retrieval earned its place, no ground truth needed.
- **FaithfulnesswithHHEM + Ragas Non-LLM String Similarity / Exact Match** → DETERMINISTIC `Judge`
  implementations, preferred whenever the task admits them.
- **Factual Correctness / Semantic Similarity (reference-based)** → the `Judge` when an eval task
  carries a gold answer.
- **DeepEval `assert_test` ergonomics** → the threshold→pass/fail shape for our deterministic gates;
  **DeepTeam** → a safety scorer feeding `review_ticket` on the promotion boundary.

**The critical caveat:** their judges are LLM-as-judge — non-deterministic and gameable. They may be
the `BareModel`/`PipelineRunner`/`Judge` scorer, **never the gate**. The two-axis gate stays
deterministic Python. Wrap any LLM judge as **N-judge majority/median with a variance floor**: judges
disagree past tolerance → emit `unmeasured` (the existing honest `None`), not a fabricated lift. Pin
model+prompt and hash them into the measurement receipt.

**Wrap shape:** a `ragas_scorer.py` / `deepeval_scorer.py` adapter implements the three Protocols,
calling Ragas/DeepEval behind the `src/teleon/inference` model-route seam (governed judge-model
selection, cost caps, receipts). `measure.py` consumes them unchanged; `offline()` flips false only
when a scorer is injected — preserving the honest offline cap. **This is the shippable next step that
closes the 5W1H backlog item "wire live model scorers into foundry measure" — now unblocked by the
owner's Mistral/Ollama keys.**

**Watch:** both Apache-2.0 (clean). Both are pure eval drifting toward governance via the Confident AI
/ commercial platforms (datasets, tracing, production monitoring — NOT promotion/receipts/CDC).
Trigger: if either ships truth-promotion, audit receipts, or a verification ledger → re-assess from
"wrapped scorer" to "thesis-overlap competitor."

---

## Synthesis — what the five say together

| Repo(s) | Relation to the moat | Shape | License | Actionability |
|---|---|---|---|---|
| Langfuse | COMPLEMENT (closest pressure) | telemetry backend behind a port | MIT/`ee` | wrap; adopt OTel emission |
| Ragas + DeepEval | VALIDATE (gate inputs) | candidate scorers behind measure.py Protocols | Apache-2.0 | **ship: the measure-stage scorer adapter** |
| Guardrails + NeMo | VALIDATE (gate pattern) | candidate If-Statement validators | Apache-2.0 | import deterministic validators |
| vLLM + SGLang + LMCache | INTEGRATION (serving) | swappable engine behind the gateway | Apache-2.0 | GPU-gated; cache-prefix value now |
| DSPy | ADMISSIBLE under lossless law | optimizer behind a port (offline only) | MIT | determinism-factory borrow |

**The thesis holds at depth:** every one of these either validates the verification-gate pattern,
complements it as logging/serving, or is admissible only behind our governance laws. None does
verification + portable receipts + governed truth promotion. The single highest-leverage move
the cluster surfaces is the **Ragas/DeepEval scorer adapter into `foundry/measure.py`** — the seam
already exists, the keys now exist, and it turns the offline-capped two-axis gate into one fed by
real measured lift.
