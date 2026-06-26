"""OpenHubForAI — deliver / emit (outbound) processors.

This package holds the implementations behind the `catalog/processors/deliver/`
manifests — the outbound bucket: hand the validated result back, post it,
mail it, page a human, or package/serve a governed corpus.

Shared rules:
  * the RENDER half of every processor is deterministic and testable offline;
  * the OUTBOUND half goes through an INJECTED transport (model-route idiom);
    pure-outbound processors REFUSE to run without one (a delivery receipt is
    never faked), renderable ones return an honest ``delivered: False`` preview;
  * receipts/ids are content-addressed; on_error=raise.
"""
