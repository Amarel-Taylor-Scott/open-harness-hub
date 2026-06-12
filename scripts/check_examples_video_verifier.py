#!/usr/bin/env python3
"""scripts.check_examples_video_verifier — gate the ADVERSARIAL gallery-video verifier.

A recorder that asserts "the DOM had the verdict" does NOT prove the produced VIDEO FILE shows
anything. `e2e/verify_examples_gallery_videos.mjs` independently inspects the video bytes (size,
duration, 1600x900, not-blank via luma range, not-black, not-frozen via start/end PSNR) and its
`--self-test` SYNTHESISES deliberately-broken videos (blank-white, all-black, frozen, too-short,
wrong-size) and proves the verifier REJECTS each on the right check — a verifier that always passes
is worthless. This proof keeps that adversarial discrimination wired into the gate.

Environment-tolerant: the verifier needs `node` + `ffmpeg`. Where either is absent (a minimal CI
box), this SKIPS honestly (the discrimination self-test runs in the recording environment, which has
both); where both are present (a dev/recording box) it actually runs the self-test and fails on any
regression. The file-existence + node-syntax checks run wherever `node` is present.

CLI: python3 scripts/check_examples_video_verifier.py [--self-test]
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERIFIER = REPO / "e2e" / "verify_examples_gallery_videos.mjs"
RECORDER = REPO / "e2e" / "record_examples_gallery.mjs"
#: the verifier looks for ffmpeg here first (johnvansickle static) then the playwright-bundled one.
_FFMPEG_CANDIDATES = (Path.home() / ".local" / "share" / "aidr-tools" / "ffmpeg",
                      Path.home() / ".cache" / "ms-playwright" / "ffmpeg-1011" / "ffmpeg-linux")


def _ffmpeg() -> str | None:
    for p in _FFMPEG_CANDIDATES:
        if p.exists():
            return str(p)
    return shutil.which("ffmpeg")


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def ck(name: str, ok: bool) -> None:
        checks.append((name, ok))

    # Always: the verifier + recorder exist and the verifier wires the file-integrity checks.
    ck("adversarial verifier file exists", VERIFIER.exists())
    ck("recorder file exists", RECORDER.exists())
    if VERIFIER.exists():
        src = VERIFIER.read_text(encoding="utf-8")
        for token in ("not_blank", "not_black", "not_frozen", "resolution", "duration"):
            ck(f"verifier asserts '{token}'", token in src)
        ck("verifier self-test synthesises broken videos", "selfTest" in src and "blank_white" in src)

    node = shutil.which("node")
    ffmpeg = _ffmpeg()
    if not node:
        ck("node present (else skip the live self-test, honestly)", True)
        _report(checks, skipped="node not available — the verifier self-test runs in the recording environment")
        return 1 if any(not ok for _, ok in checks) else 0

    # node present → syntax-check both files (cheap, environment-light).
    for f in (VERIFIER, RECORDER):
        r = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)  # noqa: S603
        ck(f"node --check {f.name}", r.returncode == 0)

    if not ffmpeg:
        _report(checks, skipped="ffmpeg not available — the discrimination self-test runs where ffmpeg exists")
        return 1 if any(not ok for _, ok in checks) else 0

    # Both present → RUN the adversarial discrimination self-test for real.
    r = subprocess.run([node, str(VERIFIER), "--self-test"],  # noqa: S603
                       cwd=str(REPO), capture_output=True, text=True, timeout=180)
    ck("verifier --self-test rejects broken videos + accepts a good one (exit 0)", r.returncode == 0)
    if r.returncode != 0:
        sys.stdout.write(r.stdout[-1500:] + r.stderr[-500:])

    _report(checks)
    return 1 if any(not ok for _, ok in checks) else 0


def _report(checks: list[tuple[str, bool]], *, skipped: str | None = None) -> None:
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if skipped:
        print(f"  [skip] {skipped}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"check_examples_video_verifier: {len(checks) - len(failed)}/{len(checks)} — the adversarial "
            "video-file verifier is present and (where node+ffmpeg exist) provably rejects "
            "blank/black/frozen/short/wrong-size videos.")


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--self-test" in argv:
        return _self_test()
    return _self_test()


if __name__ == "__main__":
    sys.exit(main())
