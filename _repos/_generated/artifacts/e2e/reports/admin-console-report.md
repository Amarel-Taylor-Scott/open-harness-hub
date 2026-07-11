# Admin console × real accounts — 2026-06-10T16:05:54.050Z

Surface: http://127.0.0.1:9210/opencontexthub/OpenContextHub%20Prototype.html · Realm: opencontexthub · Result: **PASS**

| # | stage | ok | detail |
|---|---|---|---|
| 1 | contributor-submits | ok | contributor acct_1075761ed… submitted a candidate |
| 2 | contributor-has-no-admin-access | ok | a non-admin is gated: "You don’t have admin access" — the controls are hidden |
| 3 | register-separate-admin | ok | separate admin account acct_4d7e8a88c… registered |
| 4 | operator-bootstraps-admin | ok | granted admin acct_4d7e8a88c47f28063f71 on realm 'opencontexthub' (recorded to /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/dist/registry/admins.jsonl) |
| 5 | admin-grants-reviewer | ok | admin granted reviewer → acct_1075761ed… is now in the reviewer roster |

Video: `artifacts/e2e/videos/admin-console.mp4`