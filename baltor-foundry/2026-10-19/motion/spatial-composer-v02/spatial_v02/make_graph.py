#!/usr/bin/env python3
"""Document and validate per-frame DAG: status indicates what actually runs in v0.2."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parent
nodes=[]
def add(id,op,deps=(),status='implemented',implementation='',output=''):
 nodes.append({'id':id,'op':op,'deps':list(deps),'status':status,'implementation':implementation,'output':output})
add('timeline','timeline.resolve',(),'implemented','composer_v02.shot_at','shot, local t, layout preset')
add('source_rights','rights.check',(),'implemented','layouts.json + provenance manifest','original-asset declaration')
add('canvas','spatial.canvas',('timeline',),'implemented','layout_engine.Engine','working dimensions, aspect, scale')
add('safe_zone','spatial.safe',('canvas',),'implemented','layout_engine._screen_safe','safe inset geometry')
add('scene_assets','scene.plates',('source_rights','timeline'),'implemented','original.composer.ASSETS','parallax plate stack')
add('camera','camera.solve',('timeline','canvas'),'implemented','original.camera','pan, zoom, shake')
add('background','scene.parallax',('scene_assets','camera'),'implemented','original.paste_parallax','sky/mountains/city/trees')
add('props','scene.landmarks',('background','camera'),'implemented','original.paste_parallax','environment props')
add('character','rig.pose',('props','timeline'),'implemented','original.draw_hero','animated stick-figure')
add('foreground','scene.occlude',('character',),'implemented','original foreground plate','foreground cutout and masks')
add('atmosphere','fx.weather',('foreground','timeline'),'implemented','original.draw_extras','rain, mist, signal pulses')
add('color_grade','fx.grade',('atmosphere',),'implemented','original vignette','palette consistency')
add('frame_crop','camera.final_crop',('color_grade','camera'),'implemented','original.zoom_and_shake','clean shot image without v0.1 captions')
add('shot_style','layout.preset',('timeline',),'implemented','layouts.json','element lists')
add('safe_candidate','layout.activity_advisor',('frame_crop','safe_zone'),'prototype','analyze_spatial_video.py','heuristic suggested text regions (offline analysis only)')
add('anchor_solver','layout.anchors',('shot_style','safe_zone'),'implemented','layout_engine.resolve_box','normalized anchored rectangles')
add('padding','layout.padding',('anchor_solver',),'implemented','layout_engine.resolve_padding + inset','top/right/bottom/left inset')
add('text_fit','text.wrap_fit',('padding','shot_style'),'implemented','layout_engine._textfit','wrapped/shrunk font and multiline positions')
add('timing','element.visibility',('timeline','shot_style'),'implemented','layout_engine._active_alpha','entry/exit opacity')
add('shape_layers','shape.raster',('anchor_solver','timing'),'implemented','layout_engine._draw_node','panels, reticles, waveforms')
add('text_layers','text.raster',('text_fit','timing'),'implemented','layout_engine._draw_node','typography and captions')
add('image_layers','image.crop_fit',('frame_crop','anchor_solver'),'implemented','layout_engine._draw_node','picture-in-picture and grid panel crops')
add('layer_sort','layers.z_sort',('shape_layers','text_layers','image_layers'),'implemented','layout_engine.Engine.render','visual stacking order')
add('layer_blend','layers.alpha_blend',('layer_sort','timing'),'implemented','Pillow alpha_composite/ImageChops','alpha, screen, multiply, add')
add('layout_qa','qa.spatial',('layer_blend','safe_zone'),'implemented','layout_engine.inspect_layout','offscreen and text-collision diagnostics')
add('video_pipe','video.render_pipe',('layer_blend','camera'),'implemented','composer_v02.run_render','frame-byte RGB pipe')
add('audio_bed','audio.synthesize',('timeline',),'implemented','make_spatial_audio.py','original ambient score and timed cues')
add('encode','video.encode',('video_pipe',),'implemented','ffmpeg / libx264','H264 video')
add('mux','media.mux',('encode','audio_bed'),'implemented','ffmpeg / AAC','finished MP4')
add('reference_measure','reference.spatial_extract',('mux',),'implemented','analyze_spatial_video.py','frame-by-frame feature CSV and heatmap')
add('qa_full_video','qa.av_probe',('mux','layout_qa'),'implemented','ffprobe + tests/test_spatial.py','duration, tracks, dimensions, continuity')
add('package','asset.package',('qa_full_video','reference_measure','source_rights'),'implemented','make_package.py','sources, presets, release manifests')
add('motion_inference','motion.ai_articulation',('scene_assets',),'planned','Particulate/Articraft integration not performed','inferred or authored motion graph')
add('subject_tracking','layout.subject_tracking',('frame_crop',),'planned','detect/track subject and avoid face/limb captions','semantic no-go zones')
add('beat_automation','beat.story_and_motion',('timeline','reference_measure'),'planned','expand 6.5s shots to microbeats','narration-aligned secondary cues')
add('human_review','qa.editorial',('package',),'human_required','human asset and copy approval','publication decision')

graph={'schema':'baltor.composer_dag/0.2','engine':'Baltor Spatial Motion DAG v0.2','status_rule':'Prototype/planned nodes are documented but NOT executed in the current renderer unless specified by explicit adapter.','nodes':nodes}
(ROOT/'spatial_graph.json').write_text(json.dumps(graph,indent=2)+'\n')
sys.path.insert(0,str(ROOT.parent));from composer import topological_order
order=topological_order(nodes)
(ROOT/'spatial_graph_topological_order.txt').write_text('\n'.join(f'{i:02d}. {id}' for i,id in enumerate(order,1))+'\n')
print('DAG nodes',len(nodes),'validated. Implemented',sum(x['status']=='implemented' for x in nodes),'planned',sum(x['status']=='planned' for x in nodes))
