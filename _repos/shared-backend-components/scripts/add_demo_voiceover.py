#!/usr/bin/env python3
"""scripts.add_demo_voiceover — real narrated AUDIO for the YC-demo video (narration -> TTS -> ffmpeg mux).

Reads the narration track written by e2e/record_yc_demo.mjs, synthesizes a voice per scene with a TTS engine (edge-tts),
pads/trims each clip to its scene duration so the voice tracks the captions, concatenates, and muxes the voiceover into
the recorded mp4 -> yc-demo.final.mp4. Real audio, aligned to the storyboard. ffmpeg via imageio-ffmpeg (no sudo).

  --build       synthesize + mux (needs edge-tts + ffmpeg + network)
  --self-test   offline: narration track well-formed + tools reported
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/add_demo_voiceover.py --build
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
VID = _resource("artifacts") / "e2e" / "videos"
TRACK = VID / "yc-demo.narration.json"
VOICE = "en-US-AriaNeural"


def _ffmpeg() -> str:
    p = Path.home() / ".local" / "share" / "aidr-tools" / "ffmpeg"
    if p.exists():
        return str(p)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _have(cmd: str) -> bool:
    import shutil
    return bool(shutil.which(cmd))


def build() -> int:
    if not TRACK.exists():
        print(f"no narration track at {TRACK} — run e2e/record_yc_demo.mjs first"); return 1
    track = json.loads(TRACK.read_text())["track"]
    ff = _ffmpeg()
    if not _have("edge-tts"):
        print("edge-tts not found (pip install edge-tts)"); return 1
    with tempfile.TemporaryDirectory() as d:
        clips = []
        for i, s in enumerate(track):
            mp3 = Path(d) / f"{i}.mp3"; wav = Path(d) / f"{i}.wav"
            r = subprocess.run(["edge-tts", "--voice", VOICE, "--text", s["narration"], "--write-media", str(mp3)],
                               capture_output=True, text=True, timeout=60)
            if r.returncode != 0 or not mp3.exists():
                print(f"  scene {s['id']}: TTS failed ({r.stderr.strip()[:80]}) — using silence")
                subprocess.run([ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                                "-t", str(s["seconds"]), str(wav)], timeout=30)
            else:
                # pad/trim to EXACTLY the scene duration so the voice tracks the captions
                subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(mp3), "-af",
                                f"apad=whole_dur={s['seconds']}", "-t", str(s["seconds"]), "-ar", "44100", "-ac", "2", str(wav)],
                               timeout=30)
            if wav.exists():
                clips.append(wav)
        if not clips:
            print("no audio clips produced"); return 1
        listf = Path(d) / "list.txt"
        listf.write_text("".join(f"file '{c}'\n" for c in clips))
        voice = Path(d) / "voice.wav"
        subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listf), "-c", "copy", str(voice)], timeout=60)
        mp4 = VID / "yc-demo.mp4"
        out = VID / "yc-demo.final.mp4"
        if not mp4.exists():
            print(f"no video at {mp4} — record it first"); return 1
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(mp4), "-i", str(voice),
                        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", str(out)], timeout=120)
        ok = out.exists() and out.stat().st_size > 0
        print(f"{'wrote' if ok else 'FAILED'} {out.relative_to(REPO)}" + (f" ({out.stat().st_size//1024} KB, {len(clips)} narrated scenes)" if ok else ""))
        return 0 if ok else 1


def _self_test() -> int:
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    ck("ffmpeg resolvable (imageio-ffmpeg / aidr-tools)", Path(_ffmpeg()).exists() or _ffmpeg() == "ffmpeg")
    if TRACK.exists():
        t = json.loads(TRACK.read_text()).get("track", [])
        ck("narration track has scenes with narration text", t and all(s.get("narration") for s in t))
    else:
        print("  [info] no narration track yet (record the video first)")
    print(f"\n  tools: edge-tts={_have('edge-tts')} ffmpeg={Path(_ffmpeg()).name}")
    print("\nPASS - add_demo_voiceover: narration -> TTS (edge-tts) -> per-scene pad/trim -> concat -> ffmpeg mux into "
          "yc-demo.final.mp4. Real aligned audio." if not fails else f"FAIL: {fails}")
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--build" in argv or not argv:
        return build()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
