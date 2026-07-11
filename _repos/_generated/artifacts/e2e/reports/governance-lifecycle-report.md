# Governance lifecycle — approve · reject · revoke — 2026-06-10T16:04:50.100Z

Surface: http://127.0.0.1:9210/opencontexthub/OpenContextHub%20Prototype.html · Realm: opencontexthub · Result: **PASS**

| # | stage | ok | detail |
|---|---|---|---|
| 1 | publisher-submits-two | ok | submitted two candidates — both in review, neither in Browse |
| 2 | operator-grants-reviewer | ok | granted reviewer acct_4980bb917b5f0ba931ce on realm 'opencontexthub' (recorded to /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/dist/registry/reviewers.jsonl) |
| 3 | reviewer-approves-A | ok | approved "Approve Me 1781107473833" → now live in Browse |
| 4 | reviewer-rejects-B | ok | rejected "Reject Me 1781107473833" → never public-active, left the queue (candidate preserved) |
| 5 | reviewer-revokes-A | ok | revoked "Approve Me 1781107473833" → rolled back out of Browse (lossless — decision recorded) |

Video: `artifacts/e2e/videos/governance-lifecycle.mp4`