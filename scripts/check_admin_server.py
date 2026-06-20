#!/usr/bin/env python3
"""scripts.check_admin_server — lock in the Python-3.13+ fix for the live API server.

The admin API server (`scripts/baltor_admin_demo_server.py`) used `cgi.FieldStorage`, which was
REMOVED in Python 3.13 (PEP 594) — it crashed on import. It was fixed with a stdlib `email`-based
`parse_multipart_form`. This proof guards that fix forever: it (1) imports the server module cleanly,
(2) asserts no `import cgi`, and (3) parses a SYNTHETIC multipart/form-data body and checks the text
field + uploaded filename + file bytes come through. Fully offline (no network, no Redis).

CLI:
    python3 scripts/check_admin_server.py --self-test
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

_SERVER = Path(__file__).resolve().parents[1] / "scripts" / "baltor_admin_demo_server.py"


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # (1) imports cleanly on this Python (was a hard crash on `import cgi` pre-fix)
    import_ok = True
    try:
        from scripts.baltor_admin_demo_server import parse_multipart_form
    except Exception as e:  # noqa: BLE001
        import_ok = False
        check("admin server imports cleanly", False, f"{type(e).__name__}: {e}")
    check("admin server imports cleanly (no cgi crash)", import_ok)
    if not import_ok:
        print(f"\n{len(failures)} FAILURES: {failures}")
        return 1

    # (2) the removed-stdlib import is gone
    src = _SERVER.read_text(encoding="utf-8")
    check("server has NO `import cgi` (PEP 594 removed it)", "\nimport cgi\n" not in src)

    # (3) the email-based multipart parser extracts text + uploaded file from a synthetic body
    boundary = "----baltore2e9f3"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="text"\r\n\r\n'
        "hello world\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="connector"\r\n\r\n'
        "\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="policy.txt"\r\n'
        "Content-Type: text/plain\r\n\r\n"
        "RETRY POLICY BYTES 12345\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}", "Content-Length": str(len(body))}
    form = parse_multipart_form(headers, io.BytesIO(body))

    check("text field parsed", form.getfirst("text") == "hello world", repr(form.getfirst("text")))
    check("uploaded file present", "file" in form)
    fp = form["file"] if "file" in form else None
    check("uploaded filename preserved", fp is not None and getattr(fp, "filename", "") == "policy.txt",
          getattr(fp, "filename", "<none>"))
    check("uploaded file bytes preserved", fp is not None and fp.file.read() == b"RETRY POLICY BYTES 12345")
    check("missing field returns the default ''", form.getfirst("nope") == "")

    # (4) showcase token-gate rule: open when unset; exact-match required when set (single source)
    from scripts.baltor_admin_demo_server import _token_ok
    check("token gate OPEN when no token configured", _token_ok("", None) and _token_ok("", "anything"))
    check("token gate requires an exact match when configured",
          _token_ok("s3cret", "s3cret") and not _token_ok("s3cret", "wrong") and not _token_ok("s3cret", None))

    print(f"\n{'all check_admin_server self-tests passed (server imports on Python 3.14; cgi gone; email multipart parser extracts text + file).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Guard the admin server's Python-3.13+ multipart fix.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
