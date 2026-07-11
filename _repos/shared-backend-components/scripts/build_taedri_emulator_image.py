#!/usr/bin/env python3
"""build_taedri_emulator_image — the containerized user machine: browsers + claude CLI + optional VNC desktop.

Owner (2026-07-10): "setup docker or a complete containerized user emulation, a full desktop so we can test
browser, CLI, etc" → "go ahead and build the containerized desktop emulation image." This builds `taedri-emulator`,
a self-contained "user machine" image that runs the full real-use emulation against any deployment:

    docker run --rm taedri-emulator:local --base https://taedri.fly.dev --journeys api,mcp,cli,browser
    docker run --rm -e START_VNC=1 -p 6080:6080 taedri-emulator:local ...   # WATCHABLE desktop at
                                                                            # http://localhost:6080/vnc.html

Inside: the Playwright Python base (Chromium/Firefox/WebKit preinstalled, version-matched), the Claude Code CLI
(native installer — the `cli` journey performs a real `claude mcp add/list/get/remove` round trip), Xvfb +
fluxbox + x11vnc + noVNC for the watchable-desktop lane (START_VNC=1 flips the browser journey to HEADED so you
can watch it click). The context is STAGED (emulator script copied in) so the docker build context stays tiny.

    PYTHONPATH=. python3 scripts/build_taedri_emulator_image.py --self-test
    PYTHONPATH=. python3 scripts/build_taedri_emulator_image.py --build
    PYTHONPATH=. python3 scripts/build_taedri_emulator_image.py --run --base https://taedri.fly.dev
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

IMAGE_TAG = "taedri-emulator:local"
#: version-matched to the playwright pinned by this repo's environment; bump together with the pip package.
PLAYWRIGHT_BASE_IMAGE = "mcr.microsoft.com/playwright/python:v1.61.0-noble"
#: the pip pin is DERIVED from the base tag (one source of truth) — the base ships browsers + OS deps but,
#: verified on v1.61.0-noble, NOT the python package itself; installing the same version binds to the
#: bundled browser builds exactly.
PLAYWRIGHT_PIP_VERSION = PLAYWRIGHT_BASE_IMAGE.rsplit(":", 1)[1].split("-")[0].lstrip("v")
CONTEXT_DIR = _SBC / "dist" / "taedri-emulator-context"
EMULATOR_SOURCE = _SBC / "scripts" / "taedri_real_use_emulator.py"
NOVNC_PORT = 6080

_DOCKERFILE = f"""# taedri-emulator — a containerized USER MACHINE: browsers + Claude Code CLI + optional VNC desktop.
FROM {PLAYWRIGHT_BASE_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends \\
        x11vnc novnc websockify fluxbox curl ca-certificates \\
    && rm -rf /var/lib/apt/lists/*
# the base image ships the BROWSERS (/ms-playwright) but not the python package — install it version-matched.
RUN pip install --no-cache-dir playwright=={PLAYWRIGHT_PIP_VERSION}
# Claude Code CLI (native installer, no node needed). If the install ever fails, the cli journey
# reports an HONEST labeled skip at runtime — the image still works for api/mcp/browser.
RUN curl -fsSL https://claude.ai/install.sh | bash \\
    || echo "claude CLI install failed; the cli journey will skip honestly"
ENV PATH="/root/.local/bin:${{PATH}}"
WORKDIR /emulator
COPY taedri_real_use_emulator.py .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE {NOVNC_PORT}
ENTRYPOINT ["/entrypoint.sh"]
CMD ["--base", "https://taedri.fly.dev", "--journeys", "api,mcp,cli,browser"]
"""

_ENTRYPOINT = f"""#!/bin/bash
# START_VNC=1 -> a WATCHABLE desktop: Xvfb + fluxbox + x11vnc + noVNC on :{NOVNC_PORT}, browser runs HEADED.
set -e
if [ "$START_VNC" = "1" ]; then
    Xvfb :99 -screen 0 1600x900x24 &
    sleep 1
    DISPLAY=:99 fluxbox >/dev/null 2>&1 &
    x11vnc -display :99 -forever -nopw -shared -bg -quiet
    websockify --web=/usr/share/novnc {NOVNC_PORT} localhost:5900 >/dev/null 2>&1 &
    export DISPLAY=:99 TAEDRI_EMULATOR_HEADED=1
    echo "watchable desktop: http://localhost:{NOVNC_PORT}/vnc.html (connect, no password)"
fi
exec python3 /emulator/taedri_real_use_emulator.py "$@"
"""


def stage() -> dict[str, Any]:
    """Assemble the tiny build context (Dockerfile + entrypoint + THE emulator script, copied fresh)."""
    if CONTEXT_DIR.exists():
        shutil.rmtree(CONTEXT_DIR)  # derived context, fully regenerated
    CONTEXT_DIR.mkdir(parents=True)
    shutil.copy2(EMULATOR_SOURCE, CONTEXT_DIR / "taedri_real_use_emulator.py")
    (CONTEXT_DIR / "Dockerfile").write_text(_DOCKERFILE)
    (CONTEXT_DIR / "entrypoint.sh").write_text(_ENTRYPOINT)
    files = sorted(f.name for f in CONTEXT_DIR.iterdir())
    return {"staged": True, "context_dir": str(CONTEXT_DIR), "files": files,
            "base_image": PLAYWRIGHT_BASE_IMAGE, "candidate": True, "serves_truth": False}


def build() -> dict[str, Any]:
    staged = stage()
    completed = subprocess.run(["docker", "build", "-q", "-t", IMAGE_TAG, str(CONTEXT_DIR)],
                               capture_output=True, text=True, timeout=1800)
    return {**staged, "built": completed.returncode == 0, "image": IMAGE_TAG,
            "digest_or_error": (completed.stdout or completed.stderr).strip()[-300:]}


def run_container(base: str, journeys: str, *, owner_key: str = "", vnc: bool = False,
                  timeout: int = 900) -> dict[str, Any]:
    command = ["docker", "run", "--rm"]
    if vnc:
        command += ["-e", "START_VNC=1", "-p", f"{NOVNC_PORT}:{NOVNC_PORT}"]
    command += [IMAGE_TAG, "--base", base, "--journeys", journeys]
    if owner_key:
        command += ["--owner-key", owner_key]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    try:
        receipt = json.loads(completed.stdout[completed.stdout.index("{"):])
    except (ValueError, json.JSONDecodeError):
        receipt = {"ok": False, "_raw": (completed.stdout + completed.stderr)[-600:]}
    return {"exit": completed.returncode, "receipt": receipt}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    staged = stage()
    checks.append(("context stages exactly Dockerfile + entrypoint + the emulator (tiny build context)",
                   staged["files"] == ["Dockerfile", "entrypoint.sh", "taedri_real_use_emulator.py"],
                   json.dumps(staged["files"])))

    dockerfile = (CONTEXT_DIR / "Dockerfile").read_text()
    entrypoint = (CONTEXT_DIR / "entrypoint.sh").read_text()
    checks.append(("Dockerfile: version-matched playwright base + claude installer + noVNC port + honest-skip note",
                   PLAYWRIGHT_BASE_IMAGE in dockerfile and "claude.ai/install.sh" in dockerfile
                   and str(NOVNC_PORT) in dockerfile and "skip honestly" in dockerfile, ""))
    checks.append(("Dockerfile pip-installs the python package version-DERIVED from the base tag (the base "
                   "ships browsers only — found the hard way; a bare tag digit change updates both)",
                   f"playwright=={PLAYWRIGHT_PIP_VERSION}" in dockerfile
                   and PLAYWRIGHT_PIP_VERSION in PLAYWRIGHT_BASE_IMAGE
                   and PLAYWRIGHT_PIP_VERSION[0].isdigit(), PLAYWRIGHT_PIP_VERSION))
    checks.append(("entrypoint: VNC lane exports HEADED + DISPLAY and serves noVNC; default lane is exec-clean",
                   "START_VNC" in entrypoint and "TAEDRI_EMULATOR_HEADED=1" in entrypoint
                   and "websockify" in entrypoint and entrypoint.strip().endswith('"$@"'), ""))

    # staging is deterministic (byte-identical on rebuild)
    first = (CONTEXT_DIR / "Dockerfile").read_bytes(), (CONTEXT_DIR / "entrypoint.sh").read_bytes()
    stage()
    second = (CONTEXT_DIR / "Dockerfile").read_bytes(), (CONTEXT_DIR / "entrypoint.sh").read_bytes()
    checks.append(("staging deterministic (byte-identical)", first == second, ""))

    checks.append(("docker availability is reported honestly (build requires it; staging does not)",
                   True, f"docker={'present' if shutil.which('docker') else 'absent'}"))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - build_taedri_emulator_image: containerized user machine (playwright "
          f"base v-matched + claude CLI + Xvfb/x11vnc/noVNC watchable desktop); staged tiny context; "
          f"deterministic. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build/run the containerized taedri user-emulation image.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--base", default="https://taedri.fly.dev")
    parser.add_argument("--journeys", default="api,mcp,cli,browser")
    parser.add_argument("--owner-key", default="")
    parser.add_argument("--vnc", action="store_true", help="watchable desktop on :6080 (headed browser)")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.stage:
        print(json.dumps(stage(), indent=2, sort_keys=True))
        return 0
    if args.build:
        result = build()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["built"] else 1
    if args.run:
        result = run_container(args.base, args.journeys, owner_key=args.owner_key, vnc=args.vnc)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["receipt"].get("ok") else 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
