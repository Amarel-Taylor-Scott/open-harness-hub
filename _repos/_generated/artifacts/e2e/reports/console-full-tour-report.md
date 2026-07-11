# Full console tour × real backends — 2026-06-10T16:03:24.379Z

Surface: http://127.0.0.1:9210/opencontexthub/OpenContextHub%20Prototype.html · Realm: opencontexthub · Result: **PASS**

| # | stage | ok | detail |
|---|---|---|---|
| 1 | register | ok | signed in — dashboard shows REAL Installed 0 |
| 2 | browse-real-catalog | ok | Browse renders 12 entries straight from the registry |
| 3 | create-real-api-key | ok | real API key minted (shown once) — 1 active key, hash-only at rest |
| 4 | revoke-api-key | ok | key revoked — 0 active (revoked keys stop working immediately) |
| 5 | install-entry | ok | installed ILO Forced Labour Standards (real) |
| 6 | publish-candidate | ok | published "Tour Pack 1781107384076" → in review (candidate ≠ active) |
| 7 | audit-real-activity | ok | audit shows the account's REAL actions (2 rows: install + submit recorded) |
| 8 | usage-billing-team-settings-real | ok | usage = real metrics · billing = real Free plan (no fake invoices) · settings = real email + account id |

Video: `artifacts/e2e/videos/console-full-tour.mp4`