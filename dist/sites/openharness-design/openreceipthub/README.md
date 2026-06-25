# OpenReceiptHub.io — portable receipts

**PRIVATE-FIRST candidate hub** — built on the shared kit, kept private until a competitor
enters the lane. Portable, signed receipts — model invocation, served pack, run, review, approval — that travel with the artifact and verify anywhere, by hash. The attestation face of the family.

## Status & release policy
- **status:** `private` (in `shared/products.js` → `PORTFOLIO.ENTITIES`). Muted accent +
  "Private preview" banner now; adopts its saturated `futureAccent` when opened — a one-line
  `status: 'private' → 'live'` flip (accent resolves automatically, banner disappears).
- **open trigger:** a portable AI-receipt / attestation standard gains traction.
- **drawn from:** receipt + AI-BOM / provenance spine (Sigstore · in-toto · CycloneDX · C2PA).
- **distinct from:** OpenReviewHub (a review is a VERDICT) — a receipt is a portable ATTESTATION of what happened.
- discovery ≠ trust; never public without owner clearance.

## Open it
`OpenReceiptHub Prototype.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `openreceipthub-main.jsx` + one accent + the `PORTFOLIO` entity. Inherits the
entire registry site from the shared kit: landing, browse graph, entry detail with
provenance/trust, the open-standards section, the full account layer, ⌘K, A/B and tracking.
`access` is derived from `status`, so the pre-launch banner is automatic.

Kind: **Receipt state**.
