#!/usr/bin/env python3
"""Optional YouTube downloader for content user is authorized to download/analyze.
Does not bypass login, paywalls, DRM, or rate limits. Run manually when network is enabled.
Original audio/video is not used in generated outputs by default.
"""
import argparse, importlib.util, json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--id',required=True,help='ID from reference_manifest.json')
p.add_argument('--outdir',default='inputs')
p.add_argument('--authorized',action='store_true',help='Confirm you have permission or other lawful authorization')
a=p.parse_args()
source=next((s for s in json.loads((ROOT/'reference_manifest.json').read_text())['sources'] if s['id']==a.id),None)
if not source:raise SystemExit('Unknown source ID')
if source['platform']!='YouTube':raise SystemExit('Use a downloaded local Facebook MP4; no Facebook login bypass.')
if not a.authorized:raise SystemExit('Pass --authorized after confirming you may download/analyze this source.')
if not importlib.util.find_spec('yt_dlp'):raise SystemExit('yt-dlp not installed. Install on your internet-connected machine: python -m pip install yt-dlp')
q=ROOT/a.outdir;q.mkdir(parents=True,exist_ok=True)
args=['python','-m','yt_dlp','--no-playlist','--restrict-filenames','-f','bv*+ba/best','--merge-output-format','mp4','-o',str(q/(a.id+'.%(ext)s')),source['url']]
subprocess.run(args,check=True)
