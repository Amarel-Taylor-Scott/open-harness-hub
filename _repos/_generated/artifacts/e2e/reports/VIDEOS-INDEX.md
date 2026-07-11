# Registry & console — end-to-end proof videos

Every video is a real browser (Chrome) driving the full-design UI against the live local backends
(identity :9410 · events :9420 · registry :9423 · bundle :9210). Real accounts, real sessions, real
data — no mocks, no fabricated numbers. Each has a matching `*-report.md` with per-stage results.

| Video | What it proves | Stages |
|---|---|---|
| `videos/console-full-tour.mp4` | The **whole signed-in console is real**: register → dashboard (Installed 0) → mint a real API key (shown once) → revoke it → install an entry (Installed 1) → publish a candidate → audit shows the real recorded actions → usage/billing/team/settings all show real account data (Free plan, **no fake invoices**, real email + account id). | 8/8 |
| `videos/governance-lifecycle.mp4` | The **full reviewer lifecycle** in one run: approve → entry goes live in Browse; reject → never goes live; revoke → rolled back out of Browse (lossless, decision recorded). | 5/5 |
| `videos/registry-dashboard.mp4` | The dashboard shows **real per-account data**: a fresh account is Installed 0; a real UI install moves it to 1 with a real activity row; Browse renders from the registry catalog. | 8/8 |
| `videos/reviewer-promote.mp4` | The **promotion gate**: publisher submits (not in Browse) → publisher gated out of /review → operator grants a separate reviewer → reviewer approves → it becomes public-active with lineage. | 6/6 |
| `videos/admin-console.mp4` | The **admin console**: a contributor is gated out of /admin → an operator bootstraps an admin → that admin grants the contributor reviewer access in-app → the roster updates live. | 5/5 |

## Governance guarantees demonstrated
- **candidate ≠ active** — a submission is never in Browse until a reviewer approves it.
- **separation of duties** — a reviewer can't decide on their own submission.
- **operator-rooted trust** — reviewer access is granted by admins; admin status is operator-only (no in-app escalation); every grant is audited with the acting account.
- **lossless** — reject/revoke preserve the candidate and record the decision; promotions carry submitter + reviewer lineage; revoke is a real rollback.

Regenerate any video: `node e2e/<name>.mjs` (requires the four local services running).
