# Every-element click coverage — 2026-06-09T23:57:53.206Z

**6 surfaces · 35 interactive elements found · 0 clicked · 0 held · 0 over-cap (untested) · 0 secret leaks · 17 error notes**

> No surface exceeded the per-surface cap; every element was tested.

| surface | found | tested | held | external | navs | errors |
|---|---|---|---|---|---|---|
| harness-hub/signin | 35 | 0 | 0 | 3 | 0 | 12 |
| harness-hub/signup | 0 | 0 | 0 | 0 | 0 | 1 |
| harness-hub/account/keys | 0 | 0 | 0 | 0 | 0 | 1 |
| harness-hub/ops | 0 | 0 | 0 | 0 | 0 | 1 |
| harness-hub/requests | 0 | 0 | 0 | 0 | 0 | 1 |
| harness-hub/deep | 0 | 0 | 0 | 0 | 0 | 1 |

## Error/leak notes
- **harness-hub/signin**: OpenHubForAI: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: Explore: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: Compare: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: SDG solutions: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: Pricing: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: Docs: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: Trust: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: How it works: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: See how it works: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: Sign in: TimeoutError: elementHandle.click: Timeout 2500ms exceeded.
Call log:
[2m  - at
- **harness-hub/signin**: Build ⌘↵: Error: elementHandle.click: Target page, context or browser has been closed
Call
- **harness-hub/signin**: surface failed: Error: page.$$: Target page, context or browser has been closed
- **harness-hub/signup**: surface failed: Error: page.goto: Target page, context or browser has been closed
- **harness-hub/account/keys**: surface failed: Error: page.goto: Target page, context or browser has been closed
- **harness-hub/ops**: surface failed: Error: page.goto: Target page, context or browser has been closed
- **harness-hub/requests**: surface failed: Error: page.goto: Target page, context or browser has been closed
- **harness-hub/deep**: surface failed: Error: page.goto: Target page, context or browser has been closed