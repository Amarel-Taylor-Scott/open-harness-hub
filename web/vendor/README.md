# web/vendor — pinned front-end runtime (single copy, served at /vendor/)

The full-design surfaces (ported from `dist/sites/openharness-design/`, see
`scripts/port_full_design_to_web.py`) run exactly like the design prototypes:
React UMD + in-browser Babel, **no build step**. The prototypes load these from
unpkg; the web/ apps load them from `/vendor/` (served by
`scripts/showcase/server.py` for every product) so the apps work offline and
behind tunnels with no CDN dependency.

Pinned files — versions and integrity MUST match the design bundle's `<script>`
tags (`dist/sites/openharness-design/*/​*.html`); verified at download time:

| File | Source | sha384 |
|---|---|---|
| `react.development.js` | `https://unpkg.com/react@18.3.1/umd/react.development.js` | `hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L` |
| `react-dom.development.js` | `https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js` | `u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm` |
| `babel.min.js` | `https://unpkg.com/@babel/standalone@7.29.0/babel.min.js` | `m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y` |

Re-verify: `openssl dgst -sha384 -binary <file> | openssl base64 -A`

Development (not production) React builds are intentional — they are what the
design prototypes pin, and the parity gate compares against prototype behavior.
Precompiled-JSX production tooling is a later, separate step
(`dist/sites/openharness-design/IMPLEMENTATION-GUIDANCE.md` “judgment calls”).
