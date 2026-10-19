#!/usr/bin/env python3
"""Create a proposed 300-second first episode with 40 shots and 400 timed microbeats.
EDITORIAL BLUEPRINT ONLY. Does not claim 300s movie has been rendered.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
# each tuple: act, scene, shot title, action, narration (14-17 words target), visual composition family, camera operation
scenes=[
('I','01','DEAD AIR','The survivor turns the radio dial above a quiet hillside.','At the edge of the city, the last public radio tower is still transmitting.', 'cinematic','slow pan'),
('I','02','A CLOCK WITHOUT POWER','An abandoned station clock stops while the antenna light blinks.','Nobody has electricity, yet every midnight the tower blinks exactly thirteen times.', 'forensic','clock insert'),
('I','03','THE FIRST COUNT','A hand-written supply list is checked against two remaining batteries.','You have enough water for a day, but the radio can only run for an hour.', 'survival_hud','inventory punch'),
('I','04','THE SKY CHANGES','Rain gathers at the far ridge as the moon slips behind cloud.','The forecast should be impossible to receive, but it predicts rain in seven minutes.', 'minimal_finale','sky tilt'),
('I','05','SEVEN MINUTES','A compact weather gauge rises while wind begins to move the pines.','You write down the prediction, wait, and watch the first drops arrive right on schedule.', 'dashboard','instrument insert'),
('I','06','THE SIGNAL MAP','The survivor sketches a receiver-strength map from three hill positions.','Each new measurement points to the same tower, even when the antenna is pointed away.', 'blueprint','map sweep'),
('I','07','TRAVEL LIGHT','A small bag is packed with one battery, rope, and a paper map.','You cannot carry everything, so the next decision becomes a problem of survival arithmetic.', 'survival_hud','low tracking'),
('I','08','TWO ROUTES','The path divides between a flooded road and a steep pine trail.','The road is shorter but flooded; the ridge might keep the radio line of sight.', 'split_decision','split cross-cut'),
('II','09','THE HIGH GROUND','The figure walks under trees as the ridge opens toward the tower.','You choose higher ground and track the tower light through the branches.', 'cinematic','forest parallax'),
('II','10','UNEXPECTED FREQUENCY','A waveform shifts upward with no change in the radio dial.','A second signal appears exactly between stations, too precise to be atmospheric noise.', 'blueprint','wave insert'),
('II','11','A SILENT CROSSING','Footsteps approach a rusting pedestrian bridge.','The bridge is still intact, but the sound of your footsteps takes too long to return.', 'forensic','bridge reveal'),
('II','12','THE SPARE BATTERY','One battery falls into a stream while the survivor reaches for the rail.','The spare battery disappears downstream, turning a scientific mystery into an immediate practical problem.', 'survival_hud','drop close-up'),
('II','13','COUNTDOWN','A battery gauge drops under a warning threshold.','The receiver has thirty-eight minutes left, and every experiment now has a cost.', 'dashboard','countdown macro'),
('II','14','A PATTERN','Three bursts repeat on a frequency chart.','The pulses resemble a time code, not a voice, and the intervals keep shortening.', 'blueprint','graph push'),
('II','15','ABANDONED SHELTER','A disused maintenance hut appears beyond the pines.','A maintenance hut offers cover, but its logbook stops long before the power failure.', 'forensic','door reveal'),
('II','16','ONE LAST CHARGE','A hand-crank generator is pulled from a shelf.','You find a hand crank and decide to spend ten minutes earning ten more minutes of radio time.', 'comic','mechanism close-up'),
('III','17','THE HAND CRANK','The crank oscillates and a gauge rises just above red.','The battery recovers slowly, and the tower light outside begins to pulse in sympathy.', 'dashboard','mechanism orbit'),
('III','18','THE WRONG SHADOW','The receiver shadows the hut wall as the light flashes.','One light casts two shadows, and only one of them follows the object.', 'comic','shadow track'),
('III','19','A SMALL TEST','The survivor swings a lantern in front of a measuring grid.','Instead of guessing, you set up a simple experiment with the lantern and a fixed marker.', 'forensic','test close-up'),
('III','20','REPEATABLE','Four repeated swings leave nearly identical offset traces.','The results repeat four times, making a random reflection seem increasingly unlikely.', 'quadrant','multi-angle lab'),
('III','21','A SECOND RECEIVER','A spare coil and wire become a crude directional sensor.','You build a second receiver from scrap to determine whether the anomaly is in the air or the equipment.', 'blueprint','exploded insert'),
('III','22','SIGNAL FROM BELOW','The directional needle points down rather than toward the tower.','The strongest reading comes from underground, where the old relay cables enter the hillside.', 'blueprint','tilt down'),
('III','23','THE ACCESS PANEL','A rusted service panel reveals cables disappearing under the floor.','The wires are cold, but their insulation vibrates in time with the transmission.', 'forensic','floor insert'),
('III','24','A BAD TRADE','The survivor weighs opening the panel against staying sheltered.','Opening the panel risks losing shelter, but waiting risks losing the final battery.', 'split_decision','choice cut'),
('IV','25','DOWN THE RELAY','A narrow service tunnel slopes toward the tower foundation.','You take the tunnel, following cables marked with dates that should not exist yet.', 'cinematic','tunnel dolly'),
('IV','26','CAUTION LABEL','The camera isolates an impossible future maintenance date.','A stamped maintenance label bears a date seventeen years beyond the last station inspection.', 'forensic','macro label'),
('IV','27','THE DEAD CIRCUIT','A row of relay lights activates in the wrong order.','The equipment has no external power, but its relays still respond to your receiver.', 'dashboard','relay sweep'),
('IV','28','TIMING DISAGREEMENT','Two clocks record the same pulses with different intervals.','Your stopwatch and the transmitter disagree by seconds, and the difference grows with every measurement.', 'quadrant','dual-clock compare'),
('IV','29','KEEP YOUR NOTES','Measurements are organized into a simple timeline chart.','You stop treating the radio as a message and start treating it as a system to test.', 'blueprint','timeline chart'),
('IV','30','THE OPEN LOOP','A cable loop appears to feed its own signal back into the receiver.','The transmitter might be hearing a distorted version of itself through an old return line.', 'forensic','loop trace'),
('IV','31','DISCONNECT OR LISTEN','Two panel choices appear: separate the loop or continue recording.','There is only time for one experiment before the generator and battery are exhausted.', 'split_decision','tension hold'),
('IV','32','CUT THE LINE','The protagonist disconnects the return cable; nearby lights darken.','You disconnect the loop, and for the first time all night the radio falls completely silent.', 'comic','hard snap'),
('V','33','THE SILENCE','For three seconds the camera shows only a still forest and dark tower.','Silence feels like a solution until the emergency clock begins to count backward.', 'minimal_finale','long static hold'),
('V','34','THE CLOCK REVERSES','Clock hands spin backward while dust remains suspended.','The clock reverses, but the world does not; the anomaly is somewhere in the instruments.', 'forensic','dial close-up'),
('V','35','ONE CONTROL','A single signal-strength slider becomes the focus of the frame.','You isolate one control at a time, resisting the urge to change everything at once.', 'dashboard','macro slider'),
('V','36','NEW BASELINE','The survivor records three unchanged baseline tests before changing a wire.','The baseline holds, giving you a starting point for distinguishing cause from coincidence.', 'quadrant','repeat triptych'),
('V','37','THE SHORT BRIDGE','A short wire bridges two relay terminals and the waveform stabilizes.','A temporary bridge restores a steady frequency, just as the emergency battery dips below five percent.', 'blueprint','solder detail'),
('V','38','SEND A WARNING','A short, coded weather alert is transmitted toward the settlement.','You spend the last reserve sending a warning, hoping someone outside the valley still has a receiver.', 'cinematic','radio tilt'),
('V','39','THE RESPONSE','The screen shows a receiver responding several beats before transmission.','The acknowledgement arrives before your final signal leaves, and the timeline no longer makes sense.', 'forensic','wave comparison'),
('V','40','TOMORROW IS YESTERDAY','A future-dated weather alert appears; the beacon turns blue.','Then the tower broadcasts tomorrow’s weather report with yesterday’s timestamp. What would you investigate next?', 'minimal_finale','slow pullback'),
]
assert len(scenes)==40
beats=[];shots=[];sec_per=7.5;beat_dur=.75
micro_ops=[
 'Establish focal orientation and dominant negative space',
 'Move far parallax independently of camera for depth',
 'Advance the character pose without changing canonical proportions',
 'Highlight the specific prop or evidence with local contrast',
 'Cut to or reveal a close-up of one relevant mechanical detail',
 'Show only the essential on-screen text or measured quantity',
 'Introduce one synchronized weather, particle or signal accent',
 'Shift camera from static to meaningful attention framing',
 'Add an understated event-aligned audio accent',
 'Hold an unanswered visual question and prepare the next transition'
]
for i,(act,num,title,action,narr,layout,camera) in enumerate(scenes):
 start=i*sec_per
 shot={'id':num,'act':act,'start_sec':start,'end_sec':start+sec_per,'duration_sec':sec_per,'title':title,'action':action,'narration_text':narr,
       'layout_preset':layout,'camera_proposal':camera,'on_screen_text':title,'original_character':'beacon-01','lighting':'midnight blue / restrained cyan and coral',
       'release_status':'EDITORIAL PROPOSAL — not yet rendered','microbeats':[]}
 for j,op in enumerate(micro_ops):
  st=round(start+j*beat_dur,3)
  beat={'id':f'{num}.{j+1:02d}','shot_id':num,'start_sec':st,'end_sec':round(st+beat_dur,3),'duration_sec':beat_dur,
        'motion_layer':['camera','far_parallax','character','props','inset','typography','effects','camera','audio','transition'][j],
        'operation':op+' — '+action,'timing':'draft per-beat action; shot narration to be aligned to approved voice',
        'status':'planned_not_rendered'}
  shot['microbeats'].append(beat);beats.append(beat)
 shots.append(shot)
feature={'title':'THE LAST SIGNAL — Day One / 300-second storyboard (draft)','duration_sec':300,'fps':24,'shots':shots,'shot_count':40,'microbeat_count':400,
         'visual_identity':'Original ivory stick figure + coral scarf in midnight-blue abandoned-radio setting. General genre techniques only, not cloned plot or third-party footage.',
         'status':'PLANNING DOCUMENT ONLY: the full 300-second movie is not rendered.',
         'narration':'Draft lines for each 7.5-second shot; no synthetic speech created.',
         'constraints':['Keep shots directionally continuous','Do not place text over subject face','Use original legally usable assets','Do not add 400 overlays to a 300s video; beats are timing actions, not 400 titles.']}
(ROOT/'feature_300s_storyboard_DRAFT.json').write_text(json.dumps(feature,indent=2)+'\n')
lines=['# THE LAST SIGNAL — 300-second feature draft','', '**Status: unrendered editorial storyboard.** Forty primary shots of 7.5 seconds each, with 10 secondary time-boxed actions per shot = 400 microbeats. Narration is draft text, not generated speech. The film is original fiction, not an adaptation of any referenced video.','', 'Each shot includes the proposed camera move, visual action, narration, layout treatment, and ten concrete timed support operations.','']
for s in shots:
 lines.extend([f'## {s["id"]}. {s["title"]} — {s["start_sec"]:05.1f}–{s["end_sec"]:05.1f}s', '',f'**Act:** {s["act"]} · **Layout:** `{s["layout_preset"]}` · **Camera:** {s["camera_proposal"]}', '',f'**Visual:** {s["action"]}', '',f'**Narration draft:** {s["narration_text"]}', '', '**Secondary motion beats:**',''])
 lines.extend([f'- {b["start_sec"]:05.2f}–{b["end_sec"]:05.2f}s · **{b["motion_layer"]}** — {b["operation"]}' for b in s['microbeats']]);lines+=['']
(ROOT/'feature_300s_storyboard_DRAFT.md').write_text('\n'.join(lines))
print('Created',len(shots),'proposed shots,',len(beats),'microbeats, total',shots[-1]['end_sec'],'sec')
