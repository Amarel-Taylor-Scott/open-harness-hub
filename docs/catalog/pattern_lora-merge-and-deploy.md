# LoRA merge + deploy (or hot-swap)

*pattern* · `pattern/lora-merge-and-deploy` · v0.1.0 · stable

Two production deployment shapes for LoRA-trained models: (a) merge the LoRA delta into base weights once + serve as a single monolithic model — zero adapter overhead per request, no multi-tenant routing; or (b) keep the adapter separate + hot-swap per request — single base instance serves N task-specific tenants with cheap adapter switching. Pick by latency target + tenancy model.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | serving, generation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



