#!/usr/bin/env python3
"""check_yc_demo_recording — validate the YC-demo recording storyboard + report GO/NO-GO for full video+audio.

The narrated YC-demo video has three layers: VIDEO (Playwright native recording via e2e/gate_common.mjs), CAPTIONS /
text overlay (DOM banners injected per scene, like e2e/record_user_journeys.mjs), and AUDIO (narration -> TTS -> ffmpeg
mux). This gate validates the storyboard offline and honestly reports which tools are present so the camera never starts
into a 404 or a missing encoder.

  --self-test   offline: storyboard well-formed, every target page exists, the recorder + Dockerfile are present
  --report      print GO/NO-GO for a real recording (playwright? ffmpeg? a TTS engine? the served surfaces?)
CLI: PYTHONPATH=. python3 scripts/check_yc_demo_recording.py --self-test
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STORYBOARD = REPO / "architecture" / "yc_demo_storyboard.json"
RECORDER = REPO / "e2e" / "record_yc_demo.mjs"
DOCKERFILE = REPO / "deploy" / "demo-web.Dockerfile"
_REQ_SCENE = ("id", "target", "url", "caption", "narration", "seconds")
_MIN_TOTAL, _MAX_TOTAL = 25, 180   # a YC demo clip should land ~30s-3min


def load() -> dict:
    return json.loads(STORYBOARD.read_text(encoding="utf-8"))


def validate(sb: dict) -> list[str]:
    """Offline structural validation. Returns a list of problems (empty = clean)."""
    problems = []
    scenes = sb.get("scenes", [])
    if len(scenes) < 3:
        problems.append(f"only {len(scenes)} scenes (need >=3 for a narrated arc)")
    ids = set()
    total = 0
    for i, s in enumerate(scenes):
        for f in _REQ_SCENE:
            if not s.get(f):
                problems.append(f"scene {i} ({s.get('id','?')}) missing '{f}'")
        if s.get("id") in ids:
            problems.append(f"duplicate scene id '{s.get('id')}'")
        ids.add(s.get("id"))
        if not isinstance(s.get("seconds"), (int, float)) or not (2 <= s.get("seconds", 0) <= 30):
            problems.append(f"scene '{s.get('id')}' seconds out of range (2-30): {s.get('seconds')}")
        total += s.get("seconds", 0) if isinstance(s.get("seconds"), (int, float)) else 0
        tgt = s.get("target")
        if tgt and not (REPO / tgt).exists():
            problems.append(f"scene '{s.get('id')}' target page missing: {tgt} (build it first)")
        narr = s.get("narration", "")
        if narr and len(narr.split()) > (s.get("seconds", 0) * (sb.get("voice", {}).get("wpm", 165) / 60)) + 6:
            problems.append(f"scene '{s.get('id')}' narration too long for {s.get('seconds')}s at the configured wpm")
    if not (_MIN_TOTAL <= total <= _MAX_TOTAL):
        problems.append(f"total duration {total}s outside {_MIN_TOTAL}-{_MAX_TOTAL}s")
    return problems


def _ffmpeg_present() -> bool:
    """ffmpeg on PATH, OR at the gate_common path (~/.local/share/aidr-tools/ffmpeg), OR via pip imageio-ffmpeg."""
    if shutil.which("ffmpeg") or (Path.home() / ".local" / "share" / "aidr-tools" / "ffmpeg").exists():
        return True
    try:
        import imageio_ffmpeg
        return bool(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:  # noqa: BLE001
        return False


def tool_status() -> dict:
    """What's installed for a REAL recording (honest GO/NO-GO inputs)."""
    pw = (REPO / "node_modules" / ".bin" / "playwright").exists() or bool(shutil.which("playwright"))
    ffmpeg = _ffmpeg_present()
    tts = next((t for t in ("piper", "edge-tts", "say", "espeak-ng") if shutil.which(t)), None)
    return {"playwright": pw, "ffmpeg": ffmpeg, "tts": tts,
            "recorder_present": RECORDER.exists(), "dockerfile_present": DOCKERFILE.exists()}


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    sb = load()
    probs = validate(sb)
    ck("storyboard validates clean (scenes well-formed, every target page exists, durations sane)", not probs, "; ".join(probs[:3]))
    ck("storyboard carries caption + narration per scene (video + audio layers)",
       all(s.get("caption") and s.get("narration") for s in sb.get("scenes", [])))
    ck("an audio/voiceover plan is declared (narration -> TTS -> ffmpeg mux)", "voice" in sb and "tts" in json.dumps(sb["voice"]).lower())
    ck("the Playwright recorder exists (e2e/record_yc_demo.mjs)", RECORDER.exists())
    ck("the containerized demo web server exists (deploy/demo-web.Dockerfile)", DOCKERFILE.exists())
    ck("validate() actually catches a bad scene (not a silent pass)",
       bool(validate({"scenes": [{"id": "x"}], "voice": {"wpm": 165}})))
    ts = tool_status()
    print(f"\n  recording toolchain (informational): playwright={ts['playwright']} ffmpeg={ts['ffmpeg']} tts={ts['tts']}")
    print("\n" + ("PASS - check_yc_demo_recording: the YC-demo storyboard is well-formed, every target page exists, and the "
                  "recorder + containerized server are present. Captions + narration per scene (video + audio layers); "
                  "audio = narration->TTS->ffmpeg mux. Run --report for the live GO/NO-GO. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _report() -> int:
    sb = load()
    probs = validate(sb)
    ts = tool_status()
    total = sum(s.get("seconds", 0) for s in sb.get("scenes", []))
    print(f"YC-demo recording — {len(sb.get('scenes', []))} scenes, ~{total}s")
    print(f"  storyboard: {'CLEAN' if not probs else 'PROBLEMS: ' + '; '.join(probs)}")
    print(f"  playwright: {'✓' if ts['playwright'] else '✗  (npm i -D playwright && npx playwright install chromium)'}")
    print(f"  ffmpeg:     {'✓' if ts['ffmpeg'] else '✗  (needed for webm->mp4 + audio mux)'}")
    print(f"  tts (audio):{'✓ ' + ts['tts'] if ts['tts'] else '✗  (install piper / edge-tts / say for the voiceover)'}")
    go = (not probs) and ts["playwright"] and ts["ffmpeg"]
    print(f"\n  VIDEO+CAPTIONS: {'GO' if go else 'NO-GO'} (need a clean storyboard + playwright + ffmpeg)")
    print(f"  +AUDIO voiceover: {'GO' if go and ts['tts'] else 'NO-GO (also needs a TTS engine)'}")
    print("\n  run: (serve) docker build -f deploy/demo-web.Dockerfile -t aidr-demos . && docker run -p 8088:8088 aidr-demos")
    print("       (record) node e2e/record_yc_demo.mjs   ->  artifacts/e2e/videos/")
    return 0


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--report" in argv:
        return _report()
    print("usage: check_yc_demo_recording.py --self-test | --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
