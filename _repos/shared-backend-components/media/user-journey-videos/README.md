# media/user-journey-videos — the committed per-website demo videos

The 29 NARRATED journey videos (one per website in the AI Done Right family), committed so the
deliverable itself is durable in git (~87 MB with stills; H.264 mp4 + AAC voice-over, 1600×900).
Each chapter caption is spoken (Edge neural TTS, en-US-AndrewNeural) and tempo-fitted so narration
never overlaps the next chapter. Known gaps: 2 of ~230 chapter clips failed TTS and are silent
(journey-2-baltor c15, site-openreceipthub c2) — on-screen captions still cover them.
`run-report.json` is the recording run's report (chapters, timings, console status — 0 frictions /
0 console errors across the batch). `stills/<journey>/` holds the per-chapter PNG close-ups shot
during recording.

- Chapter index (GENERATED from the report): `docs/status/user-journey-videos.md`
- Recorder (re-generates everything): `node e2e/record_user_journeys.mjs` — fresh output lands in
  `artifacts/e2e/videos/` (gitignored); then `node e2e/narrate_videos.mjs` writes voice-over'd
  copies to `artifacts/e2e/videos-narrated/` (mux capped with `-t` — apad+stream-copy makes
  `-shortest` alone spin forever); copy a new generation here deliberately, don't hand-edit.
- What's real on camera vs captioned-emulated: the manifest header and
  `docs/status/web-full-design-parity-report.md`.

Set: 4 product journeys (OpenHarnessHub + Teleon recorded through their PUBLIC tunnel URLs,
Baltor with a real pipeline run, AI Done Right parent + Demo Control Tower + scorecard) ·
2 family tours · 21 per-hub fully-wired cuts (real sign-up on each hub's own realm → real
install → real shown-once API key; private bench included) · 2 internal-plane tours.
