"""browser_control.adapters — the concrete driver adapters (real backends + documented design seams).

Real, importable adapters:
    http_scrape_adapter.HttpScrapeAdapter  — wraps the harness StaticBackend (offline/stdlib HTTP GET)
    cdp_adapter.CdpAdapter                 — wraps the harness CdpBackend + TabControlAPI (live, system Chrome)
    playwright_adapter.PlaywrightAdapter   — real if Playwright + a launchable Chrome are present; else degrades

Design seams (markdown, one file each — the adapter SHAPE + install/test commands + when-to-use + risks):
    puppeteer · selenium · mcp · lightpanda · extension · remote_browser · browser_use
"""
