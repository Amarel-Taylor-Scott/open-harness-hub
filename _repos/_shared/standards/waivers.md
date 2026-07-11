# Pattern waivers (the time-boxed exceptions)

## Purpose

The standards linter is strict by design. When a real file legitimately deviates from a pattern —
because it is legacy, mid-migration, or a deliberate exception — the answer is **not** to weaken the
linter. The answer is a **waiver**: an explicit, owned, time-boxed record in
`architecture/pattern_waivers.json` that says "we know this deviates, here is who owns it, here is
why it is safe, here is the plan to fix it, and here is the pass by which it must be gone."

Waivers make debt *visible and expiring* instead of silent and permanent. They are deliberately
scarce: the default is to fix the deviation, not to waive it.

## Schema

Each waiver carries:

| Field | Meaning |
|---|---|
| `waiver_id` | stable id, e.g. `WVR-0001-legacy-vague-filename` |
| `pattern_id` | one of the canonical 25 patterns the file deviates from |
| `file_path` | the real file the waiver covers (must exist) |
| `reason` | why the deviation exists |
| `owner` | the team/role accountable for paying it off |
| `expires_by_pass` | the flywheel pass number after which the waiver is no longer honored (a deterministic counter, **not** a wall-clock date) |
| `replacement_plan` | the concrete plan to remove the deviation (and this waiver) |
| `proof_that_safe` | the evidence the deviation is safe today |
| `status` | `active` \| `expired` \| `closed` |

The doc also carries a top-level `current_pass`. A waiver is honored only while `status=="active"`
**and** `current_pass <= expires_by_pass`.

## Proof

```bash
python3 scripts/check_pattern_waivers.py --self-test
```

The proof enforces:

- every waiver has owner + replacement_plan + proof_that_safe + expires_by_pass;
- every `pattern_id` is one of the canonical 25;
- every `file_path` points at a file that exists (a waiver for a deleted file is stale debt → fail);
- a waiver whose `status=="expired"` **fails** the proof (the forcing function);
- an `active` waiver whose `current_pass` has passed `expires_by_pass` **fails** (a negative fixture
  in a temp dir proves both rejections bite).

The standards linter (`check_new_code_uses_standards`) reads this file: a path with an active,
non-expired waiver is exempt from the matching rule, so a waiver is the single, audited way to make
the linter tolerate a known deviation.

## Limitations

- A waiver exempts a path from a *rule*; it does not make the underlying deviation correct. The
  `replacement_plan` is a promise, and `expires_by_pass` is the deadline on that promise.
- `expires_by_pass` is a pass counter, not a date — it stays deterministic and offline, but it means
  the operator must advance `current_pass` for expiry to take effect.
- The example waiver (`WVR-0001-legacy-vague-filename`) covers `scripts/context_workers/common.py`,
  which is also recorded in `architecture/file_layout_policy.json#banned_filename_allowlist`; the
  replacement plan removes both entries in the same change to avoid orphaned contradictions.
