# Offline queue sync on reconnect (store-and-forward for community health alerts)

*processor* · `processor/offline-queue-sync-on-reconnect` · v0.1.0 · experimental

Store-and-forward processor that buffers alert records locally (SQLite or
flat-file queue) when the device is offline and flushes them to the
upstream endpoint (MoH server, NGO dashboard, or district health API) in
FIFO order as soon as a network connection is detected. Designed for the
AfyaEdge syndromic surveillance pattern: field health workers capture triage
outputs locally; the processor ensures no alert is lost during connectivity
gaps and each record carries a content hash, device ID, capture timestamp,
and sync status.

The processor exposes three operations:
  enqueue(record)  — append a record to the local queue with a hash and
                     pending status; always succeeds offline.
  sync_now()       — probe connectivity, then flush pending records in
                     FIFO order; retries on transient failure; marks each
                     record synced or failed.
  status()         — return queue depth, oldest-pending age, and last-sync
                     timestamp.

CAPABILITY LIFT (structural): cloud endpoints are structurally unavailable
in remote last-mile settings during the window that matters most (active
triage). This processor converts a synchronous cloud dependency into an
async queue, making alert capture a purely local operation. The gap is
structural because no amount of model improvement closes the physical
absence of a network link.
lift_reason: no_addressable_source (network absent at point of care);
mechanism: orchestration_complexity (multi-step enqueue/retry/sync
protocol that a bare model cannot execute reliably).

| axis | value |
|---|---|
| industry | healthcare.public_health, public_safety, cross_industry |
| capability | agent_loop, governance, verification |
| modality | structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | Apache-2.0 |



