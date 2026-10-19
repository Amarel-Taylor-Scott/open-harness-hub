"""Generate detailed 65s timing/continuity documents as EDITORIAL PLANS, not rendered claims."""
import json,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parent
cfg=json.loads((ROOT/'layouts.json').read_text())
# Canon continuity reused from the original source, with explicit hierarchy.
bible={
 'series':'THE LAST SIGNAL','version':'2026.10.19/v0.2','production_status':'Original visual studies; draft story continuity',
 'canon':{
   'hero':{'id':'beacon-01','visual':'Ivory round-head stick figure, graphite outline, coral diagonal scarf, fixed proportions','motion_rule':'Rigid limbs connected at coherent hip, knee, shoulder and elbow positions; avoid morphing body scale.'},
   'environment':{'world':'Abandoned midnight-blue ridge, tower, pine trees, distant urban ruins, shelter','canonical_orientation':'Tracking shots move consistently left-to-right; camera crop changes do not relocate permanent landmarks.','lighting':'Cool moonlight, cyan radio pulses, coral warnings, restrained warm flares'},
   'day_clock':'Explicit day/level labels are fiction and advance only when editorially specified, not automatically per template.',
   'threat_language':'Knocks and signal anomalies are recurring narrative motifs, not claims about the referenced Facebook series.',
   'audio':'Original synthesized ambient bed. All voice tracks await separately approved high-quality narration.'
 },
 'character_consistency_checks':['ivory head/body','coral scarf on every appearance','no broken knees/elbows','screen-direction continuity','avoid character covered by unimportant text'],
 'style_locks':{'ivory':'#F4F3E6','cyan':'#85F4E8','danger':'#FA7A72','warning':'#F1C878','ink':'#081521','font_families':['Lato','DejaVu Sans','DejaVu Sans Mono','DejaVu Serif']},
 'source_attribution':'Artwork and video are original programmatic interpretations of common film techniques. Third-party reference videos were not examined frame by frame here.'}
(ROOT/'series_bible_v02.json').write_text(json.dumps(bible,indent=2)+'\n')

beats_by_style={
 'cinematic':['Wide night skyline establishes the setting','Title begins a subtle upward entrance','Camera eases toward a lone survivor','Moon and tower remain separated from title','Close with a restrained time stamp and anticipatory pause'],
 'survival_hud':['Introduce a chapter/level counter','Expose a compact inventory card','Read each dwindling resource value','Move visual emphasis from food to battery','Hold on the resource deadline and narrow escape route'],
 'split_decision':['Present the dilemma with a short headline','Reveal both paths simultaneously','Track distinct parallax framing in left and right panes','Hold to let viewers compare danger','Conclude on a choice cue; cut rather than overanimate'],
 'forensic':['Open on a labeled field report','Identify the tower as focal evidence','Punch into a separately cropped detail view','Draw leader line and emphasize a repeating signal','Hold a measured observation before the next cut'],
 'comic':['Hard, asymmetric salmon title slab appears','Three onomatopoeia beats each punctuate a knock','Comic framing isolates the danger','Pause on an off-screen source of tension','Reveal uncertainty rather than a complete answer'],
 'blueprint':['Establish signal telemetry and sensor context','Reveal origin reticle against the environment','Faint tracking rings expand outward','Render two condensed instrument values','Hold on low confidence rather than claiming certainty'],
 'art_deco':['Symmetrical accent bars establish a new chapter','Serif intertitle fades up centered','Camera drifts toward the watchtower','Single controlled decorative sweep','Leave a clean final pause without HUD clutter'],
 'dashboard':['State the operative problem as a large headline','Display the battery percentage at large scale','Show the resource bar and estimated time','Reserve generous negative space around the character','Finish with one concise operational takeaway'],
 'quadrant':['Cut to four simultaneous surveillance crops','Reveal independently labeled camera windows','Change perceived depth with varied crops','Emphasize observation gaps, not omniscient certainty','Transition from monitoring to the final question'],
 'minimal_finale':['Almost all overlays vanish to create negative space','Build the final line by carefully staged text','Draw a synchronized but quiet signal waveform','Hold on the revelation','End on a small serial cliffhanger, without a busy CTA']
}
beats=[]
durations=[1.05,1.20,1.25,1.35,1.65]
assert abs(sum(durations)-6.5)<1e-7
for s in cfg['shots']:
 t=s['start']
 for j,(desc,dur) in enumerate(zip(beats_by_style[s['layout']],durations),1):
  beats.append({'shot_id':s['id'],'layout':s['layout'],'beat_index':j,'start_sec':round(t,3),'end_sec':round(t+dur,3),'duration_sec':dur,
                'visual_action_proposal':desc,'narration_cue':s['narration_cue'] if j==2 else '',
                'audio_cue_proposal':['ambient setup','soft reveal','supporting movement','subtle transition','hold / tease'][j-1],
                'status':'SECOND-PASS EDITORIAL PLAN — not individually implemented in v0.2 video'})
  t+=dur
(ROOT/'microbeat_plan_50_beats.json').write_text(json.dumps({'runtime_sec':cfg['duration_sec'],'beats':beats},indent=2)+'\n')
# 50 additional styles and content treatments, as research/production backlog.
style_families={
 'Comic & illustrated':['manga-panel tracking','newspaper halftone','inked noir vignette','paper-cut stop motion','retro pulp covers'],
 'Film & photography':['documentary lower-thirds','analog film gate','archival dossier','found-footage camcorder','telescope surveillance'],
 'Tech & research':['isometric CAD projection','annotated node DAG','model evaluation charts','shader laboratory','graph-neural network view'],
 'Games & arcade':['pixel HUD platformer','roguelike inventory','survival-map minimap','tactical overwatch','simulation replay'],
 'Dimensional design':['2.5D diorama','layered depth-card wall','stereoscopic split','floating browser windows','3D exploded panel'],
 'Infographics':['animated timeline','unit economics waterfall','ranked skill database','radial category explorer','AI feed alert report'],
 'Type & typography':['karaoke word highlighting','right-edge vertical titles','center stage kinetic type','text-in-world signboards','minimal type-only vignette'],
 'Effects & transitions':['particle field split','mask wipe through trees','whip-zoom insert','match-cut camera anchors','shock-wave text reveal'],
 'Sound & rhythm':['physics musical notes','subtle waveform equalizer','ASMR mechanical loops','beat-synced infographic','footstep-driven cuts'],
 'Community & conversion':['before-after dev demos','five-way tool benchmark','interactive skill request','two-option audience vote','evidence-backed feed alert']
}
rows=[]
for category,ideas in style_families.items():
 for idea in ideas:
  rows.append({'category':category,'idea':idea,'target_purpose':'original reusable composition','status':'backlog / not implemented','adaptable_to':'vertical, square, landscape (requires re-layout validation)'})
(ROOT/'future_style_ideas_50.json').write_text(json.dumps(rows,indent=2)+'\n')
with open(ROOT/'future_style_ideas_50.csv','w',newline='') as f:
 d=csv.DictWriter(f,fieldnames=rows[0].keys());d.writeheader();d.writerows(rows)
print('Created continuity bible +',len(beats),'timed microbeats +',len(rows),'unimplemented design candidates')
