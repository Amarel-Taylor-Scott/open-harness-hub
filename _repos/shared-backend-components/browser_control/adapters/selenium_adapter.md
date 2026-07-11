# selenium_adapter (DESIGN SEAM)

> Status: **design seam** — not a real class, and **`selenium` is NOT installed** in this environment
> (`selenium`, `bs4`, `lxml`, `scrapy`, `pyppeteer` are all absent). So a `SeleniumAdapter` would `start_session()`
> → structured `{"supported": False, "reason": "selenium not installed"}` here. Documented for teams whose existing
> WebDriver suites must be reused.

## Adapter shape

- **Class:** `SeleniumAdapter(_BackendAdapter)` backed by a `_SeleniumBackend(BackendPort)` wrapping a
  `webdriver.Chrome` (or Remote WebDriver → a Selenium Grid / Selenoid hub).
- **BackendPort mapping:** `open(url)` → `driver.get(url); driver.page_source (+ get_screenshot_as_png)`;
  `list_tabs/new_tab/switch_tab/close_tab` → `driver.window_handles` + `switch_to.window` + `switch_to.new_window`
  + `close`.
- **Backs:** `navigate`, `snapshot`, DOM/text/links/forms/tables, `screenshot`, tab control, `click_ref`/`fill_ref`
  (gated), `wait_for_state` (WebDriverWait), `download_artifacts`, graph/report (`JS_RENDER = True`).
- **Does NOT back well:** rich `capture_network` (Selenium has no first-class network panel without a CDP hop /
  BiDi / a proxy) → return `capture_network` unsupported unless the Chrome DevTools/BiDi bridge is wired.

## Install + test

```bash
pip install selenium                    # NOT installed here by default
# needs a matching chromedriver on PATH (Selenium Manager can fetch it)
# (promoted) python3 -c "from browser_control import get_adapter; print(get_adapter('selenium').start_session())"
```

## When to use

- A large **existing WebDriver regression suite** or a **Selenium Grid** already runs cross-browser matrices.
- Otherwise prefer `playwright` (cleaner auto-waiting, native network capture) or `cdp` (zero-pip) here.

## Risks

- Extra system dependency (`chromedriver`) + version pinning to Chrome.
- Flaky implicit/explicit waits are the classic Selenium failure mode — always drive `wait_for_state` explicitly.
- Live browser = side effects: read-only default, `write`+ confirmation gate, never submit / bypass a login/captcha.
