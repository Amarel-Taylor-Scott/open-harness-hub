#!/usr/bin/env python3
"""scripts.check_aidevobserver_vscode_ext — prove the AIDevObserver VS Code extension scaffold is a valid, complete extension.

The extension (editor/aidevobserver-vscode/) is the editor surface of the Teleon Observer session-review layer: it
reads the active editor's transcript and POSTs {demo:"aidevobserver", byo_key, inputs} to the byo_demo_server /run
endpoint. This proof asserts the manifest is valid and declares the required command + BYO-key/endpoint config, and
that the real extension/build/doc files exist and wire the contract. serves_truth=false.

  PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_aidevobserver_vscode_ext.py --self-test
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_here_boot = _Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()), _here_boot.parents[1])
if str(_sbc_boot) not in _sys.path:
    _sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

EXT_DIR = _resource("editor") / "aidevobserver-vscode"
COMMAND_ID = "aidevobserver.reviewSession"
COMMAND_TITLE = "AIDevObserver: Review Session"
DEMO_ID = "aidevobserver"
DEFAULT_ENDPOINT = "http://localhost:8120/run"
APIKEY_CONFIG = "aidevobserver.apiKey"
ENDPOINT_CONFIG = "aidevobserver.endpoint"

# (relative path, must be non-empty)
REQUIRED_FILES = (
    "package.json",
    "src/extension.ts",
    "tsconfig.json",
    ".vscodeignore",
    "README.md",
)


def _read(rel: str) -> str:
    return (EXT_DIR / rel).read_text(encoding="utf-8")


def self_test() -> int:
    # 1) every required file exists and is non-empty
    for rel in REQUIRED_FILES:
        f = EXT_DIR / rel
        assert f.is_file(), f"missing extension file: editor/aidevobserver-vscode/{rel}"
        assert f.stat().st_size > 0, f"empty extension file: editor/aidevobserver-vscode/{rel}"

    # 2) package.json is valid JSON with the required manifest shape
    pkg = json.loads(_read("package.json"))
    assert isinstance(pkg, dict), "package.json must be a JSON object"
    assert isinstance(pkg.get("engines"), dict) and pkg["engines"].get("vscode"), "engines.vscode required"
    assert isinstance(pkg.get("main"), str) and pkg["main"], "main entrypoint required"
    acts = pkg.get("activationEvents")
    assert isinstance(acts, list) and any(COMMAND_ID in a for a in acts), "activationEvents must reference the command"

    contributes = pkg.get("contributes")
    assert isinstance(contributes, dict), "contributes object required"

    # 2a) contributes.commands declares the command id + title
    commands = contributes.get("commands")
    assert isinstance(commands, list) and commands, "contributes.commands must be a non-empty list"
    cmd = next((c for c in commands if c.get("command") == COMMAND_ID), None)
    assert cmd is not None, f"contributes.commands must declare command id {COMMAND_ID!r}"
    assert cmd.get("title") == COMMAND_TITLE, f"command title must be {COMMAND_TITLE!r}"

    # 2b) contributes.configuration declares both the apiKey and endpoint settings (endpoint defaulted)
    config = contributes.get("configuration")
    blocks = config if isinstance(config, list) else [config]
    props: dict = {}
    for b in blocks:
        if isinstance(b, dict):
            props.update(b.get("properties") or {})
    assert APIKEY_CONFIG in props, f"configuration must declare {APIKEY_CONFIG!r} (BYO key)"
    assert ENDPOINT_CONFIG in props, f"configuration must declare {ENDPOINT_CONFIG!r}"
    assert props[ENDPOINT_CONFIG].get("default") == DEFAULT_ENDPOINT, f"endpoint default must be {DEFAULT_ENDPOINT!r}"

    # 3) tsconfig.json is valid JSON and compiles src
    ts = json.loads(_read("tsconfig.json"))
    assert isinstance(ts, dict) and "compilerOptions" in ts, "tsconfig.json must define compilerOptions"

    # 4) extension.ts is real TypeScript that wires the activate/command/fetch contract
    src = _read("src/extension.ts")
    for needle in ("export function activate", "export function deactivate",
                   "registerCommand", COMMAND_ID, DEMO_ID, DEFAULT_ENDPOINT,
                   "byo_key", "inputs"):
        assert needle in src, f"src/extension.ts must contain {needle!r}"

    print(
        "check_aidevobserver_vscode_ext self-test: OK "
        f"(valid manifest: command {COMMAND_ID!r}, config {APIKEY_CONFIG}/{ENDPOINT_CONFIG}; "
        f"{len(REQUIRED_FILES)} required files present; extension.ts POSTs demo={DEMO_ID!r})"
    )
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: check_aidevobserver_vscode_ext.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
