#!/usr/bin/env python3
"""Ship original, editable, reproducible source and analyses without redundant video bytes."""
from pathlib import Path
import zipfile,hashlib,json,datetime
ROOT=Path(__file__).resolve().parent;PARENT=ROOT.parent
TARGET=Path('/mnt/data/Baltor_Spatial_Motion_Composer_v02_Source.zip')
include=[
 'composer.py','build_assets.py','storyboard.json','graph.json','sound_design.py','analyze_references.py','quality_audit.py','reference_manifest.json',
 'README.md','AGENTS.md','SKILL.md','FORMAT_BIBLE_V02.md','layouts.json','layout_schema.json','spatial_graph.json','spatial_graph_topological_order.txt','spatial_dag.dot',
 'layout_engine.py','composer_v02.py','make_presets.py','make_spatial_audio.py','make_graph.py','draw_graph.py','build_editor.py','editor_runtime.js','Baltor_Spatial_Studio_Editor.html',
 'build_editorial_specs.py','make_package.py','validate_config.py','qa_release.py','analyze_spatial_video.py','build_feature300.py',
 'series_bible_v02.json','microbeat_plan_50_beats.json','feature_300s_storyboard_DRAFT.json','feature_300s_storyboard_DRAFT.md','future_style_ideas_50.json','future_style_ideas_50.csv',
 'tests/test_spatial.py',
 'outputs/spatial_10_style_contact_sheet.jpg','outputs/baltor_spatial_dag.png','outputs/baltor_spatial_dag.svg',
 'outputs/qa_final_mp4_contact_sheet.jpg','outputs/QA_RELEASE.md','outputs/qa_release.json',
 'outputs/spatial_analysis/frame_spatial_metrics.csv','outputs/spatial_analysis/spatial_summary.json',
 'outputs/spatial_analysis/per_shot_spatial_suggestions.json','outputs/spatial_analysis/spatial_report.md',
 'outputs/spatial_analysis/per_shot_placement_sheet.jpg','outputs/spatial_analysis/placement_candidates.png',
 'outputs/editor_browser_test.png','outputs/editor_dashboard_test.png','outputs/spatial_original_audio_manifest.json',
]
paths=[]
for name in include:
 p=(PARENT/name) if name in ['composer.py','build_assets.py','storyboard.json','graph.json','sound_design.py','analyze_references.py','quality_audit.py','reference_manifest.json'] else (ROOT/name)
 if not p.exists():raise FileNotFoundError(p)
 paths.append((p, ('stick_composer/'+name) if p.parent==PARENT else ('stick_composer/spatial_v02/'+name)))
for img in sorted((PARENT/'assets').glob('*.png')):paths.append((img,'stick_composer/assets/'+img.name))
for test in sorted((PARENT/'tests').glob('test_*.py')):paths.append((test,'stick_composer/tests/'+test.name))
video=ROOT/'outputs/baltor_spatial_layout_study_65s_FINAL.mp4'
video_h=hashlib.sha256(video.read_bytes()).hexdigest() if video.exists() else 'not_rendered'
meta={
 'version':'0.2','generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'package_intent':'Sources and results for original Baltor spatial motion-composer; finished 65s MP4 delivered as separate download.',
 'work_status':{'original_artwork':'implemented','ten_layouts':'rendered','spatial_engine':'implemented','offline_layout_editor':'test_loaded_and_interacted_in_headless_chromium','frame_analysis':'implemented_for_own_render','300s_feature':'storyboard_only_not_rendered','third_party_video_reverse_engineering':'not_performed'},
 'video_sha256':video_h,
 'file_count':len(paths),
 'license_warning':'Original assets in source package; independently confirm rights before adapting/distributing third-party media. Do not redistribute original font binaries.'
}
with zipfile.ZipFile(TARGET,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
 for p,arc in paths:z.write(p,arc)
 z.writestr('RELEASE_MANIFEST.json',json.dumps(meta,indent=2)+'\n')
print('Source package:',TARGET, 'bytes',TARGET.stat().st_size,'files',len(paths))
(ROOT/'release_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
