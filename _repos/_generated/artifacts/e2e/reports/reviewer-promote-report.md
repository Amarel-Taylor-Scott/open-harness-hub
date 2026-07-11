# Reviewer promotion gate × real accounts — 2026-06-10T16:05:39.446Z

Surface: http://127.0.0.1:9210/opencontexthub/OpenContextHub%20Prototype.html · Realm: opencontexthub · Candidate: E2E Promote Pack 1781107523412 · Result: **PASS**

| # | stage | ok | detail |
|---|---|---|---|
| 1 | publisher-submits-candidate | ok | submitted "E2E Promote Pack 1781107523412" → in review, and NOT yet in Browse (candidate ≠ active) |
| 2 | publisher-has-no-review-access | ok | a non-reviewer is gated: "You don’t have reviewer access" — promotion controls hidden |
| 3 | register-separate-reviewer | ok | separate reviewer account acct_e5cddd3d6… registered |
| 4 | operator-grants-reviewer | ok | granted reviewer acct_e5cddd3d65e3e624a0bd on realm 'opencontexthub' (recorded to /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/dist/registry/reviewers.jsonl) |
| 5 | reviewer-approves-and-promotes | ok | reviewer approved "E2E Promote Pack 1781107523412" → server confirms "promoted to the catalog" |
| 6 | promoted-entry-now-in-browse | ok | the promoted "E2E Promote Pack 1781107523412" is now public-active in Browse (with submitter+reviewer lineage) |

Video: `artifacts/e2e/videos/reviewer-promote.mp4`