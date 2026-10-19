import subprocess,json,pathlib,hashlib,os,cv2, numpy as np,shutil,tempfile
R=pathlib.Path(__file__).parent
BIN=R/'bin/baltor-distill-linux-amd64'
def H(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def exe(args):return subprocess.run(args,check=True,capture_output=True,text=True)
checks={}
checks['go_tests_pass']=exe(['go','test','./...']).returncode==0
with tempfile.TemporaryDirectory() as td:
 t=pathlib.Path(td)
 exe([str(BIN),'timeline','--input',str(R/'examples/flagship_superbowl_style_storyboard.json'),'--out',str(t/'story')])
 checks['storyboard_byte_stable']=all(H(t/'story'/name)==H(R/'outputs/flagship_storyboard'/name) for name in ['compiled_storyboard.json','timeline.csv','captions.srt'])
 exe([str(BIN),'variants','--input',str(R/'examples/ad_campaign_variants.json'),'--out',str(t/'v.json')])
 checks['variation_byte_stable']=H(t/'v.json')==H(R/'outputs/variation_grid.json')
 build=t/'fresh-binary'
 subprocess.run(['go','build','-trimpath','-ldflags=-s -w','-o',str(build),'./cmd/baltor-distill'],check=True,capture_output=True,text=True,env={**os.environ,'CGO_ENABLED':'0','GOOS':'linux','GOARCH':'amd64'})
 checks['native_binary_rebuild_byte_stable']=H(BIN)==H(build)
 exe([str(BIN),'scan','--root',str(R/'testdata/skills'),'--out',str(t/'skill_scan.json')])
 report=json.loads((t/'skill_scan.json').read_text())
 checks['fixture_scan_detects_scripts']=len(report['skills'])==2 and sum(len(s['scripts']) for s in report['skills'])==1
 exe([str(BIN),'propose','--catalog',str(t/'skill_scan.json'),'--out',str(t/'proposals.json')])
 q=json.loads((t/'proposals.json').read_text())
 checks['proposals_never_executable']=all(not x['execution_allowed'] for x in q['proposals'])
 checks['cross_platform_binary_sizes']=all((R/'bin'/b).stat().st_size>1000000 for b in ['baltor-distill-linux-amd64','baltor-distill-linux-arm64','baltor-distill-darwin-arm64','baltor-distill-windows-amd64.exe'])
vids={}
for style in ['kinetic','paper']:
 path=R/f'outputs/commercial/last_tab_{style}_30s.mp4'
 info=json.loads(exe(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames','-of','json',str(path)]).stdout)
 streams=info['streams'];vs=next(s for s in streams if s['codec_type']=='video'); audio=next(s for s in streams if s['codec_type']=='audio')
 cap=cv2.VideoCapture(str(path));total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); samples=[]
 for idx in [0,10,100,200,300,400,500,600,719]:
  cap.set(cv2.CAP_PROP_POS_FRAMES,idx);ret,frame=cap.read();
  if ret:
   gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY);samples.append({'frame':idx,'mean_luma':round(float(gray.mean()),3),'percent_black':round(float(np.mean(gray<6)),4)})
 cap.release()
 good=abs(float(info['format']['duration'])-30)<0.1 and total==720 and len(samples)==9 and vs['width']==720 and vs['height']==1280 and vs['codec_name']=='h264' and audio['codec_name']=='aac' and samples[0]['percent_black']<.8 and samples[-1]['percent_black']<.8
 checks[f'{style}_video_tech_qa']=good
 vids[style]={'path':str(path.relative_to(R)),'bytes':path.stat().st_size,'sha256':H(path),'duration_seconds':float(info['format']['duration']),'frames':total,'resolution':[vs['width'],vs['height']],'samples':samples,'status':'tech_qa_pass' if good else 'tech_qa_fail','creative_review':'not_human_reviewed','audio':'original procedural score, no narration'}
catalog=json.loads((R/'docs/RESEARCH_SOURCE_CATALOG.json').read_text())
checks['catalog_scope_and_status']=catalog['summary']['sources']==68 and catalog['summary']['candidate_operators']==294 and all(x['review_status']=='candidate_research_not_executed' for x in catalog['sources'])
result={'release':'0.4.0','all_checks_pass':all(checks.values()),'checks':checks,'videos':vids,'candidate_summary':catalog['summary'],'test_scope':'Local Linux x86-64; cross-built binaries not executed on other OSs; no kernel sandbox; no third-party skill execution; video checks technical, not creative QA.'}
(R/'outputs/RELEASE_QA.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'pass':all(checks.values()),'checks':checks},indent=2))
