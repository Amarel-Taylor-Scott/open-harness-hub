import json
from pathlib import Path
R=Path(__file__).resolve().parent
implemented={'camera.pan','camera.track','camera.zoom','camera.shake','camera.whip','camera.easing','image.ken_burns','image.parallax','scene.occlusion','scene.landmarks','character.stick_pose','character.walk','character.run','character.hide','character.point','character.throw','character.scarf_continuity','fx.rain','fx.fog','fx.signal_pulse','fx.impact','fx.flare','fx.border','fx.grade','shot.split_panel','shot.pip','transition.hard_cut','transition.flash','text.scene_label','text.progress','audio.soundscape','audio.footstep','audio.ping','audio.door_knock','audio.flare','video.encode','video.mux','qa.timeline','qa.frame_sampling','qa.frame_metrics','qa.metadata','analysis.cut_candidates','analysis.optical_flow','analysis.contact_sheet','provenance.reference_manifest','provenance.sha256','dag.toposort'}
ops={
 'reference':['download_ytdlp','local_media_import','source_permissions_check','hash_and_register','probe_metadata','frame_decode','frame_bgr_normalize','cut_candidates','adaptive_cut','fade_detection','optical_flow','feature_tracking','global_affine_zoom','semantic_masking','scene_segmentation','palette_cluster','subtitle_ocr','audio_onset','beat_tracker','contact_sheet','montage_export','human_review_queue','shot_taxonomy','confidence_score','license_guard','reference_manifest','sha256'],
 'story':['character_bible','location_map','wardrobe_lock','shot_stager','storybeat_graph','script_draft','story_arc_variants','continuity_check','hook_scoring','shot_density_budget','cta_gate','narration_word_timing'],
 'asset':['image_ken_burns','image_parallax','depth_inference','matte_extract','sprite_import','vector_trace','layer_decompose','background_plate','landmarks','occlusion','tile_seam_validation','animated_cutout','compositing_modes'],
 'actor':['stick_pose','walk','run','hide','point','throw','scarf_continuity','face_expression','hand_contact','inverse_kinematics','motion_matching','state_transition','secondary_motion','silhouette_validation'],
 'camera':['pan','track','zoom','shake','whip','easing','deadzone_follow','rack_focus_2_5d','dolly_zoom','overhead_map','punch_in','tilt','roll','field_of_view','motion_curve_editor','safe_zone_crop'],
 'fx':['rain','fog','signal_pulse','impact','flare','border','grade','snow','smoke','fire','embers','parallax_bokeh','lightning','heat_distortion','depth_fog','pixel_sort','film_grain','chromatic_aberration','cartoon_smear','speed_lines','outline_glow','shadow_map'],
 'shot':['split_panel','pip','comic_grid','2x2_grid','picture_window','scrolling_page','long_pan','crosscut','character_pov','over_shoulder','masked_reveal'],
 'transition':['hard_cut','flash','iris','motion_blur','whip_pan','page_turn','ink_wipe','split_reveal','slide','match_cut','focus_pull','speed_ramp','color_wipe'],
 'text':['scene_label','progress','kinetic_caption','highlight_on_word','type_on','speech_bubble','character_tag','callout_pointer','subtitle_srt','brand_footer'],
 'audio':['soundscape','footstep','ping','door_knock','flare','narration_import','voice_timing','ducking','dialogue_scene','ambient_layers','dynamic_sfx','beat_sync','subtitle_align','human_review_tts'],
 'video':['encode','mux','render_cache','proxy_render','batch_variants','shot_cache','format_profiles','cloud_worker','artifact_registry'],
 'qa':['timeline','frame_sampling','frame_metrics','metadata','silent_audio','black_frame','clipping','character_consistency','text_safe_area','frame_ghosting','motion_jitter','audio_sync','scene_geometry','rights_review','duplicate_detection','thumbnail_selector','ab_preference_test','human_release_approval'],
 'provenance':['reference_manifest','sha256','input_license','model_provenance','transform_lineage','asset_source','revision_history','render_manifest']
}
entries=[]
for category,items in ops.items():
 for op in items:
  id=category+'.'+op
  if id=='image.image_ken_burns':id='image.ken_burns'
  if id=='image.image_parallax':id='image.parallax'
  if id=='actor.stick_pose':id='character.stick_pose'
  if category=='asset' and id.startswith('asset.') and op in ('landmarks','occlusion'):id='scene.'+op
  if id=='actor.walk':id='character.walk'
  if id=='actor.run':id='character.run'
  if id=='actor.hide':id='character.hide'
  if id=='actor.point':id='character.point'
  if id=='actor.throw':id='character.throw'
  if id=='actor.scarf_continuity':id='character.scarf_continuity'
  if category=='reference' and op in ('cut_candidates','optical_flow','contact_sheet'):id='analysis.'+op
  if category=='reference' and op in ('reference_manifest','sha256'):id='provenance.'+op
  entries.append({'id':id,'category':category,'status':'implemented_in_original_prototype' if id in implemented else 'candidate_not_implemented','scope':'generalizable motion/video pipeline primitive','note':'Implemented means a basic procedural version or inspection utility exists, not state-of-the-art performance.'})
uniq={e['id']:e for e in entries}
res={'catalog_kind':'candidate plus prototype-supported video DAG operations','verified_reference_video_count':0,'operator_total':len(uniq),'basic_implemented_total':sum(e['status']=='implemented_in_original_prototype' for e in uniq.values()),'operators':list(uniq.values())}
(R/'operator_catalog.json').write_text(json.dumps(res,indent=2)+'\n')
print('catalog',res['operator_total'],res['basic_implemented_total'])
