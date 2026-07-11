#!/usr/bin/env python3
"""Race real read-only acquisition paths and emit candidate-only receipts.

The same public URL is captured twice through each selected backend.  Raw HTML,
cookies, storage, screenshots, and response bodies are never persisted.  The
receipt records only final URL, title, text/body digests, structural counts,
prompt-injection flags, latency, and deterministic-replay equality.

Restricted anti-detection adapters are opt-in and are for operator-authorized
public capture/compatibility testing only.  They never solve CAPTCHAs, bypass
authentication, submit forms, or reuse cookies.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import html.parser
import ipaddress
import json
import os
import re
import socket
import subprocess
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path
from typing import Any, Callable, Optional


HERE = Path(__file__).resolve()
SBC = next((p for p in HERE.parents if (p / "scripts" / "_repo_paths.py").exists()), HERE.parents[1])
if str(SBC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SBC))

from scripts._repo_paths import resource  # noqa: E402
from scripts.check_generated_artifact_security import screen_prompt_injection  # noqa: E402


BOUNDARY = {"candidate": True, "serves_truth": False}
SCHEMA_VERSION = "acquisition-path-replay-ab/v1"
DEFAULT_OUT = resource("data") / "dev-intel" / "acquisition_path_replay_ab"
USER_AGENT = "AIDoneRight-PrimitiveDiscovery/1.0 (+read-only; respects robots.txt)"
MAX_BODY_BYTES = 3_000_000
MAX_URLS = 20
MAX_BACKENDS = 5
TIMEOUT_SECONDS = 40
RESTRICTED = frozenset({"nodriver", "undetected_chromedriver"})
SUPPORTED = frozenset({"static", "playwright", "selenium", "nodriver", "undetected_chromedriver"})


def sha(value: str | bytes) -> str:
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


class StructuralParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.text: list[str] = []
        self.links = 0
        self.forms = 0
        self.inputs = 0
        self.headings = 0
        self.spec_links = 0
        self.download_links = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        if tag == "a":
            self.links += 1
            href = values.get("href", "")
            if re.search(r"(?:openapi|swagger|asyncapi|graphql|\.proto\b|\.avsc\b)", href, re.I):
                self.spec_links += 1
            if re.search(r"\.(?:pdf|csv|json|xml|parquet|zip)(?:[?#]|$)", href, re.I):
                self.download_links += 1
        elif tag == "form":
            self.forms += 1
        elif tag in {"input", "select", "textarea"}:
            self.inputs += 1
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        self.text.append(data)


def is_public_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    addresses = {info[4][0].split("%", 1)[0] for info in infos}
    if not addresses:
        return False
    for value in addresses:
        ip = ipaddress.ip_address(value)
        if not ip.is_global:
            return False
    return True


def validate_url(url: str, *, allow_http: bool = False) -> str:
    parsed = urllib.parse.urlparse(url)
    allowed_schemes = {"https"} | ({"http"} if allow_http else set())
    if parsed.scheme not in allowed_schemes or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("url_policy_rejected")
    if not is_public_host(parsed.hostname):
        raise ValueError("non_public_destination")
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", parsed.query, ""))


def robots_allowed(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    robots = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser(robots)
    try:
        parser.read()
    except Exception:
        return False
    return bool(parser.can_fetch(USER_AGENT, url) and parser.can_fetch("*", url))


def summarize_html(raw: str, final_url: str) -> dict[str, Any]:
    parser = StructuralParser()
    parser.feed(raw)
    text = unicodedata.normalize("NFKC", " ".join(" ".join(parser.text).split()))
    title = " ".join(parser.title.split())[:300]
    injection = screen_prompt_injection(text[:200_000])
    return {
        "final_url": final_url,
        "title": title,
        "html_digest": sha(raw),
        "text_digest": sha(text),
        "html_chars": len(raw),
        "text_chars": len(text),
        "links": parser.links,
        "forms": parser.forms,
        "inputs": parser.inputs,
        "headings": parser.headings,
        "api_spec_links": parser.spec_links,
        "download_links": parser.download_links,
        "prompt_injection_flagged": bool(injection.get("flagged")),
        "raw_body_stored": False,
        "cookies_read": False,
        "storage_read": False,
        "side_effects": False,
    }


def static_capture(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        final_url = validate_url(response.geturl())
        raw = response.read(MAX_BODY_BYTES + 1)
        if len(raw) > MAX_BODY_BYTES:
            raise ValueError("body_too_large")
        charset = response.headers.get_content_charset() or "utf-8"
    return summarize_html(raw.decode(charset, errors="replace"), final_url)


def playwright_capture(url: str) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="chrome", headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_SECONDS * 1000)
            final_url = validate_url(page.url)
            return summarize_html(page.content(), final_url)
        finally:
            browser.close()


def selenium_capture(url: str) -> dict[str, Any]:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    options = Options()
    for value in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"):
        options.add_argument(value)
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.binary_location = "/usr/bin/google-chrome"
    driver = webdriver.Chrome(options=options)
    try:
        driver.set_page_load_timeout(TIMEOUT_SECONDS)
        driver.get(url)
        final_url = validate_url(driver.current_url)
        return summarize_html(driver.page_source, final_url)
    finally:
        driver.quit()


def undetected_capture(url: str) -> dict[str, Any]:
    import undetected_chromedriver as uc
    options = uc.ChromeOptions()
    for value in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"):
        options.add_argument(value)
    options.add_argument(f"--user-agent={USER_AGENT}")
    version_output = subprocess.run(
        ["/usr/bin/google-chrome", "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout
    version_match = re.search(r"(\d+)", version_output)
    version_main = int(version_match.group(1)) if version_match else None
    driver = uc.Chrome(
        options=options, browser_executable_path="/usr/bin/google-chrome",
        version_main=version_main, use_subprocess=True,
    )
    try:
        driver.set_page_load_timeout(TIMEOUT_SECONDS)
        driver.get(url)
        final_url = validate_url(driver.current_url)
        return summarize_html(driver.page_source, final_url)
    finally:
        driver.quit()


async def _nodriver_capture(url: str) -> dict[str, Any]:
    import nodriver
    browser = await nodriver.start(
        headless=True, browser_executable_path="/usr/bin/google-chrome",
        browser_args=["--no-sandbox", "--disable-dev-shm-usage", f"--user-agent={USER_AGENT}"],
    )
    try:
        tab = await browser.get(url)
        await tab.sleep(1)
        final_url = validate_url(str(tab.url))
        return summarize_html(await tab.get_content(), final_url)
    finally:
        browser.stop()
        # nodriver closes Chrome transports asynchronously after stop().  Give
        # the loop one scheduling window so subprocess transports are drained
        # before asyncio.run() closes it.
        await asyncio.sleep(0.25)


def nodriver_capture(url: str) -> dict[str, Any]:
    return asyncio.run(_nodriver_capture(url))


CAPTURE: dict[str, Callable[[str], dict[str, Any]]] = {
    "static": static_capture,
    "playwright": playwright_capture,
    "selenium": selenium_capture,
    "nodriver": nodriver_capture,
    "undetected_chromedriver": undetected_capture,
}


def replay(url: str, backend: str) -> dict[str, Any]:
    started = time.monotonic()
    try:
        capture = CAPTURE[backend](url)
        status = "captured"
        error_class = None
    except Exception as exc:
        capture = {}
        status = "error"
        error_class = type(exc).__name__
    return {
        "status": status,
        "error_class": error_class,
        "latency_ms": round((time.monotonic() - started) * 1000),
        "capture": capture,
    }


def run_live(
    urls: list[str], backends: list[str], out_dir: Path, *, allow_restricted: bool,
) -> dict[str, Any]:
    if not 1 <= len(urls) <= MAX_URLS or not 1 <= len(backends) <= MAX_BACKENDS:
        raise ValueError("live run exceeds URL/backend bounds")
    unknown = set(backends) - SUPPORTED
    if unknown:
        raise ValueError(f"unsupported backends: {sorted(unknown)}")
    if set(backends) & RESTRICTED and not allow_restricted:
        raise ValueError("restricted backends require --allow-restricted")
    receipts: list[dict[str, Any]] = []
    for raw_url in urls:
        url = validate_url(raw_url)
        allowed = robots_allowed(url)
        for backend in backends:
            runs = [replay(url, backend) for _ in range(2)] if allowed else []
            captures = [run["capture"] for run in runs if run["status"] == "captured"]
            deterministic = len(captures) == 2 and captures[0].get("text_digest") == captures[1].get("text_digest")
            receipt = {
                "record_type": "acquisition_path_replay_receipt",
                "schema_version": SCHEMA_VERSION,
                "receipt_id": sha(canonical({"url": url, "backend": backend, "runs": runs})),
                "url": url,
                "backend": backend,
                "restricted_backend": backend in RESTRICTED,
                "robots_allowed": allowed,
                "runs": runs,
                "both_captured": len(captures) == 2,
                "deterministic_text_replay": deterministic,
                "execution_authorized": False,
                "created_at": utc_now(),
                **BOUNDARY,
            }
            receipts.append(receipt)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "replay_receipts.jsonl"
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        for row in receipts:
            handle.write(canonical(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)
    summary = {
        "record_type": "acquisition_path_replay_summary",
        "schema_version": SCHEMA_VERSION,
        "receipts": len(receipts),
        "urls": len(urls),
        "backends": backends,
        "both_captured": sum(row["both_captured"] for row in receipts),
        "deterministic_text_replay": sum(row["deterministic_text_replay"] for row in receipts),
        "errors": sum(run["status"] == "error" for row in receipts for run in row["runs"]),
        "raw_body_rows": 0,
        "module_digest": sha(HERE.read_bytes()),
        "created_at": utc_now(),
        **BOUNDARY,
    }
    (out_dir / "latest_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def self_test() -> int:
    fixture = """<html><head><title>Unit</title></head><body><h1>Docs</h1>
    <a href='/openapi.json'>API</a><a href='/manual.pdf'>PDF</a><form><input name='q'></form></body></html>"""
    row = summarize_html(fixture, "https://example.com/")
    checks = [
        ("structural extraction finds title/spec/download/form", row["title"] == "Unit" and row["api_spec_links"] == 1
         and row["download_links"] == 2 and row["forms"] == 1),
        ("capture projection stores no body", "<html" not in canonical(row) and row["raw_body_stored"] is False),
        ("private destinations fail closed", not is_public_host("127.0.0.1")),
        ("restricted adapters are explicitly classified", RESTRICTED <= SUPPORTED),
    ]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    failures = [name for name, ok in checks if not ok]
    if failures:
        print(f"FAIL: {failures}")
        return 1
    print("PASS - acquisition replay receipts are read-only, body-free, robots/SSRF-gated, and restriction-aware.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--live", action="store_true")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--backends", default="static,playwright,selenium")
    parser.add_argument("--allow-restricted", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    backends = [value.strip() for value in args.backends.split(",") if value.strip()]
    print(json.dumps(run_live(args.urls, backends, args.out_dir, allow_restricted=args.allow_restricted),
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
