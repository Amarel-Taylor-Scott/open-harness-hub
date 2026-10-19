#!/usr/bin/env python3
"""Generates 10 distinct spatial layouts as JSON assets, not simply recolors."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WHITE='#F4F3E6'; CYAN='#85F4E8'; RED='#FA7A72'; GOLD='#F1C878'; DARK='#081521E8'; SLATE='#102439DD'; MUTED='#A3C2C8'

def box(x,y,w,h,space='safe',anchor='top_left'):return dict(space=space,anchor=anchor,dx=x,dy=y,w=w,h=h)
def e(id,kind,x,y,w,h,*,layer='ui',z=10,space='safe',anchor='top_left',**kwargs):return dict(id=id,kind=kind,box=box(x,y,w,h,space,anchor),z=z,layer=layer,**kwargs)
def text(id,s,x,y,w,h,*,font_size=24,color=WHITE,font='bold',layer='typography',z=40,padding=0,**kwargs):
 return e(id,'text',x,y,w,h,layer=layer,z=z,text=s,font_size=font_size,color=color,font=font,padding=padding,**kwargs)
def pill(id,s,x,y,w,h,*,color=CYAN,font_size=12,**kw):
 return e(id,'pill',x,y,w,h,layer='annotations',z=45,text=s,font_size=font_size,font='bold',color=color,background=True,fill=DARK,outline=True,border=color, padding=[2,9,2,9],radius=7,**kw)
def rectangle(id,x,y,w,h,*,fill=SLATE,border=CYAN,stroke=1,z=25,space='safe',**kw):
 return e(id,'box',x,y,w,h,layer='panels',z=z,space=space,background=True,fill=fill,outline=True,border=border,border_width=stroke,**kw)
def line(id,x,y,w,*,color=CYAN,z=46,**kw):
 return e(id,'line',x,y,w,.003,layer='decor',z=z,color=color,must_safe=True,**kw)
def progress(id,x,y,w,*,val='progress',color=CYAN,z=50):
 return e(id,'progress',x,y,w,.013,layer='hud',z=z,value=val,color=color)

layouts={}
# 01 -- classical cinematic negative space / small label and lower third subtitle
layouts['cinematic']={'name':'01 / CINEMATIC TITLE','description':'Large negative-space composition with a restrained headline, no container panels','elements':[
 pill('chapter','STUDY 01  /  CINEMATIC',.01,.02,.52,.048),
 text('headline','THE LAST\nSIGNAL',.01,.12,.90,.195,font_size=58,min_font_size=28,line_spacing=.98,shadow=True,enter='slide_up',in_=0 if False else None) if False else text('headline','THE LAST\nSIGNAL',.01,.115,.92,.20,font_size=56,min_font_size=28,line_spacing=.96,shadow=True,enter='slide_up',**{'in':.8}),
 line('rule',.02,.34,.23,color=RED),
 text('standfirst','ONE VOICE. NO WAY HOME.',.01,.36,.86,.078,font_size=19,font='mono',color=CYAN,**{'start':.7}),
 text('bottom_line','DAY 01     •     23:48',.02,.93,.82,.05,font_size=13,color=MUTED,font='mono'),
 ]}
# 02 survival HUD with counts, a complete padded card and text hierarchy
layouts['survival_hud']={'name':'02 / SURVIVAL INVENTORY','description':'Countdown-led narrative: modular inventory cards with exact resource quantities','elements':[
 pill('level','LEVEL 02  •  SURVIVAL',.02,.015,.61,.05,color=RED),
 rectangle('inventory_card',.02,.088,.94,.325,fill='#0A1B29E9',border=RED,stroke=2,radius=13),
 text('inv_heading','SUPPLIES REMAINING',.05,.105,.77,.06,font_size=19,color=WHITE),
 line('inv_rule',.05,.171,.83,color=RED),
 text('inv_food_label','FOOD',.06,.195,.25,.055,font_size=14,color=MUTED,font='mono'),
 text('inv_food_val','02',.06,.249,.24,.087,font_size=40,color=RED,font='bold'),
 text('inv_water_label','WATER',.37,.195,.28,.055,font_size=14,color=MUTED,font='mono'),
 text('inv_water_val','01',.37,.249,.23,.087,font_size=40,color=GOLD),
 text('inv_batt_label','BATTERY',.68,.195,.29,.055,font_size=14,color=MUTED,font='mono'),
 text('inv_batt_val','18%',.68,.249,.26,.087,font_size=34,color=CYAN),
 text('countdown','NEXT SAFE WINDOW  00:37',.06,.351,.79,.05,font_size=13,font='mono',color=CYAN),
 text('summary','EACH HOUR COSTS MORE.',.04,.475,.91,.08,font_size=21,shadow=True),
 progress('capacity',.04,.966,.91,val='resource_level',color=RED)
 ]}
# 03 1x2 composite as a core node with distinct crops
layouts['split_decision']={'name':'03 / CHOOSE A PATH','description':'Two simultaneous camera crops separated by a visible film-strip gutter','elements':[
 e('stage_dimmer','box',0,0,1,1,z=18,layer='framing',space='canvas',background=True,fill='#091B2BA8',outline=False,must_safe=False),
 pill('choice_label','YOU HAVE FIVE SECONDS',.02,.014,.75,.05,color=GOLD),
 text('choice_headline','WHICH WAY?',.02,.082,.93,.105,font_size=37),
 e('decisions','panel_grid',.02,.205,.96,.615,z=25,layer='panels',rows=1,cols=2,gap=8,labels=['LEFT / COVER','RIGHT / RUN'],crops=[[.05,.38,.75,.93],[.29,.31,.94,.95]],mirror_alternate=True,accent=CYAN,color=WHITE,must_safe=True),
 text('decision_footer','ONE CHOICE CHANGES EVERYTHING.',.02,.85,.94,.08,font_size=16,align='center',color=WHITE)
 ]}
# 04 documentary with focal PiP and labels
layouts['forensic']={'name':'04 / DOCUMENTARY CALLOUTS','description':'Inset detail, evidence tags, source-linked annotations, controlled negative space','elements':[
 pill('case','FIELD REPORT / 04',.02,.012,.53,.055),
 text('documentary','THE RADIO\nIS STILL ON',.02,.085,.91,.18,font_size=32,line_spacing=1.04),
 e('monitor','image',.50,.285,.46,.315,z=23,layer='insets',radius=8,crop=[.31,.31,.78,.82],border=CYAN,border_width=3,outline=True,must_safe=True),
 pill('monitor_label','DETAIL 01 / SIGNAL',.52,.313,.40,.047,color=CYAN,font_size=10),
 e('annotation_pointer','pointer',.38,.435,.15,.04,z=30,color=CYAN,target=[.45,.58],must_safe=True),
 text('observation','OBSERVATION  •  THE SIGNAL REPEATS.',.03,.85,.91,.09,font_size=17,color=CYAN,font='mono',max_lines=2)
 ]}
# 05 brutal comic graphic panel with abrupt motion text
layouts['comic']={'name':'05 / GRAPHIC NOVEL','description':'Contrasting caption slab and asymmetrical dramatic typography','elements':[
 rectangle('hero_block',.02,.02,.68,.16,fill='#E57A68F2',border=RED,stroke=0,radius=3),
 text('onomatopeia','KNOCK!\nKNOCK!\nKNOCK!',.045,.037,.59,.135,font_size=24,min_font_size=19,color='#151520',line_spacing=.94),
 e('comic_border','box',.01,.32,.96,.48,z=24,layer='decor',background=False,outline=True,border=GOLD,border_width=3,space='safe',radius=1),
 e('impact_ring','reticle',.54,.35,.30,.22,z=28,layer='effects',color=RED),
 pill('comic_counter','3  KNOCKS',.02,.335,.43,.055,color=RED),
 text('comic_bottom','BUT NOBODY IS AT THE DOOR.',.02,.223,.94,.09,font_size=17,color=WHITE)
 ]}
# 06 technical blueprint HUD with reticle, bars, instrument readouts
layouts['blueprint']={'name':'06 / SIGNAL BLUEPRINT','description':'A technical explanatory layout combining reticle and right-aligned metadata','elements':[
 pill('telemetry','TELEMETRY  /  LIVE',.02,.014,.59,.048),
 text('tech_head','SIGNAL ORIGIN',.02,.082,.95,.095,font_size=33,color=CYAN),
 e('tech_reticle','reticle',.22,.28,.52,.37,z=28,layer='effects',color=CYAN),
 rectangle('telemetry_plate',.49,.23,.49,.245,fill='#061A28D9',border=CYAN,radius=4),
 text('freq','FREQUENCY 142.900',.52,.25,.42,.065,font_size=15,font='mono',color=WHITE),
 text('strength','CONFIDENCE  /  UNKNOWN',.52,.328,.43,.065,font_size=13,font='mono',color=GOLD),
 progress('strength_bar',.52,.435,.40,val='signal_strength',color=CYAN)
 ]}
# 07 art deco symmetrical geometric, gold and restrained headings
layouts['art_deco']={'name':'07 / ART-DECO INTERTITLE','description':'Symmetrical gold guides and a centered intertitle instead of conventional top-left captions','elements':[
 e('outer_decoration','box',.025,.05,.95,.84,z=15,layer='framing',background=False,outline=True,border='#E9BE76BA',border_width=2,edge_marks=True,must_safe=True,radius=2),
 line('top_deco',.30,.083,.4,color=GOLD),
 text('act','ACT VII',.32,.128,.36,.055,font_size=19,font='serif',color=GOLD,align='center'),
 text('gold_title','THE\nWATCHTOWER',.08,.21,.84,.18,font_size=37,font='serif',color=WHITE,align='center',line_spacing=1.15),
 text('gold_kicker','THE LAST LIGHT ON THE RIDGE',.05,.81,.90,.06,font_size=14,font='serif',align='center',color=GOLD),
 line('bottom_deco',.30,.904,.4,color=GOLD)
 ]}
# 08 utilitarian infographic: card architecture and typographic numbers
layouts['dashboard']={'name':'08 / INFOGRAPHIC DATA','description':'Charts, quantitative hierarchy, tall side annotation, padded cards','elements':[
 pill('summary_header','SITUATION BRIEF  /  DAY 03',.01,.016,.79,.055),
 text('situation','THE CLOCK\nIS RUNNING OUT',.01,.105,.95,.16,font_size=35,color=WHITE),
 rectangle('stat_card',.02,.285,.94,.345,fill='#061B2AEF',border=CYAN,radius=14),
 text('stat_big','18%',.05,.305,.50,.17,font_size=76,color=RED),
 text('stat_label','POWER REMAINING',.53,.337,.40,.105,font_size=18,font='mono',color=MUTED),
 progress('stat_progress',.06,.489,.85,val='resource_level',color=RED),
 text('stat_context','ESTIMATED RUN TIME  /  04:12',.06,.536,.85,.055,font_size=14,font='mono',color=CYAN),
 text('dashboard_footer','PLAN FOR FAILURE. MOVE BEFORE DARK.',.03,.665,.93,.090,font_size=16,color=WHITE)
 ]}
# 09 2x2 visual explainer with four distinct crop windows
layouts['quadrant']={'name':'09 / FOUR CAMERA FEEDS','description':'2x2 four-view montage, localized labels, separation gutters, time-code bar','elements':[
 e('stage_dimmer','box',0,0,1,1,z=18,layer='framing',space='canvas',background=True,fill='#091B2BBF',outline=False,must_safe=False),
 pill('grid_indicator','LIVE  /  QUAD FEED',.02,.012,.60,.052,color=RED),
 text('grid_headline','EVERY DIRECTION IS A RISK',.02,.083,.95,.08,font_size=21),
 e('four_up','panel_grid',.02,.20,.96,.64,z=23,layer='panels',rows=2,cols=2,gap=7,labels=['CAM 01 / WEST','CAM 02 / EAST','CAM 03 / NORTH','CAM 04 / SOUTH'],crops=[[.05,.15,.62,.73],[.32,.31,.95,.83],[.10,.44,.87,.95],[.36,.10,.98,.65]],mirror_alternate=True,accent=RED,color=WHITE,must_safe=True),
 text('grid_bottom','RECORDING  •  04 CAMERAS',.02,.875,.88,.07,font_size=14,font='mono',color=RED),
 ]}
# 10 minimal cinematic closing, no busy borders
layouts['minimal_finale']={'name':'10 / MINIMAL CLIFFHANGER','description':'Just two typographic layers, a signal waveform and cliffhanger rhythm','elements':[
 text('ending_part','DAY 04    /    00:00',.02,.055,.92,.065,font_size=17,font='mono',color=CYAN),
 text('ending_headline','THE VOICE\nKNOWS YOUR\nNAME.',.02,.155,.93,.27,font_size=48,min_font_size=28,line_spacing=1.03,enter='slide_up',shadow=True,**{'in':.9}),
 line('ending_rule',.03,.455,.36,color=RED),
 e('voice_wave','waveform',.04,.515,.91,.11,z=38,layer='audio_visualizer',bars=45,color=CYAN,must_safe=True),
 text('end_lower','TRANSMISSION ENDS  /  TO BE CONTINUED',.04,.873,.88,.073,font_size=13,font='mono',color=MUTED)
 ]}

DUR=6.5
plan=[]
for n,(key,layout) in enumerate(layouts.items()):
 # Reuse compatible original scene/camera/actor beats, but with a completely new spatial overlay.
 samples=[1.0,7.,20.,29.,47.,54.,43.,39.,63.,68.]
 plan.append({'id':f'{n+1:02d}','start':round(n*DUR,3),'end':round((n+1)*DUR,3), 'layout':key, 'source_shot_seconds':samples[n], 'source_sample_span':2.8,
              'narration_cue':[
 'A single signal survives in the dark.','Three supplies. A shrinking deadline.','Every direction carries a different risk.',
 'The evidence points toward the radio tower.','Then the knocking starts.','Somewhere, a transmitter wakes up.',
 'The last light on the ridge.','Battery at eighteen percent.','Every camera sees a different threat.',
 'Then the voice says your name.'
              ][n]})
conf={'schema':'baltor.spatial.composer/0.2','rights':'Original procedural story and artwork. No reference media copied.','duration_sec':DUR*len(plan),'fps':24,'working_canvas':{'w':540,'h':960},'output':{'w':1080,'h':1920},
      'safe_profile':'reels','safe_profile_notice':'These configurable regions are conservative authoring heuristics; platform UI overlays can change.',
      'layout_keys':list(layouts),'layouts':layouts,'shots':plan,
      'layers':{'sky':0,'parallax':5,'landmarks':8,'character':10,'foreground':13,'atmosphere':17,'framing':20,'panels':25,'insets':27,'effects':28,'decor':35,'audio_visualizer':38,'typography':40,'annotations':45,'hud':50},
      'dimension_families':{
       'Canvas':['width','height','aspect_ratio','fps','frame_number','pixel_aspect','render_scale','safe_profile','bleed_area','safe_zone','device_preview','overscan'],
       'Spatial position':['anchor_15','x_relative','y_relative','offset_px','baseline','thirds_guide','rule_of_fifths','subject_anchor','focal_point','parent_anchor','alignment','grid_cell','column_span','row_span','sticky_region'],
       'Sizing':['relative_width','relative_height','max_width','min_width','max_height','min_height','font_scale','fit_contain','fit_cover','crop_region','auto_fit','aspect_lock'],
       'Spacing':['padding_top','padding_right','padding_bottom','padding_left','margin_top','margin_right','margin_bottom','margin_left','gap_x','gap_y','line_spacing','letter_spacing','baseline_gap','panel_gutter'],
       'Typography':['family','weight','size','minimum_size','stroke_width','shadow','text_color','align_left','align_center','align_right','vertical_align','wrap','maximum_lines','ellipsis','tracking','kerning','leading','background_card','text_path','highlight_per_word','highlight_per_char','reveal_delay'],
       'Shapes':['rect','rounded_rect','line','divider','progress','circle','reticle','ribbon','pointer','pill','metric','waveform','label','corner_marks','frame_border','grid_overlay'],
       'Layering':['z_index','depth','alpha','blend_normal','blend_screen','blend_multiply','blend_add','clip_round','foreground_occlusion','mask','group','parent_space','nested_container','independent_timing','visibility','solo','lock'],
       'Motion':['pan_x','pan_y','zoom','tilt','roll','crop_x','crop_y','shake_x','shake_y','ease_in','ease_out','stagger','hold','fade','slide','scale','typewriter','pop','wipe','parallax_depth'],
       'Camera':['framing','subject_tracking','deadzone','lookahead','dolly','push_in','pull_out','whip','crash_zoom','focus_pull','overshoot','viewpoint','picture_in_picture'],
       'Color':['foreground','background','accent','danger','temperature','tint','vignette','contrast','saturation','gamma','opacity','outline','grading','palette_lock'],
       'Audio':['narration_cue','sound_event','music_duck','ambient_bed','beat_sync','stereo_pan','loudness','fade_in','fade_out','captions','subtitle_sync'],
       'QA':['safe_area','font_readability','offscreen','text_collision','subject_collision','black_frame','subtitle_contrast','duration','cut_detect','camera_flow','edit_manifest','provenance','sample_rate','asset_rights']
      }}
(ROOT/'layouts.json').write_text(json.dumps(conf,indent=2)+'\n')
print('Created',len(layouts),'presets,',len(plan),'shots,',sum(map(len,conf['dimension_families'].values())),'dimension controls')
