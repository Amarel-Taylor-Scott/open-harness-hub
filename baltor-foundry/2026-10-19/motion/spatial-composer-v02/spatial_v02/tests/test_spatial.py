import sys,json,unittest,hashlib,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import composer_v02 as v2
from layout_engine import Rect,Engine,resolve_box,resolve_padding,inset,rgba,inspect_layout

class TestGeometry(unittest.TestCase):
 def test_normalized_anchors(self):
  c=Engine(540,960,'full')
  n={'box':{'space':'canvas','anchor':'top_left','w':.5,'h':.2,'dx':.05,'dy':.11}}
  r=resolve_box(n,540,960,c.safe)
  self.assertEqual((r.x,r.y,r.w,r.h),(27,106,270,192))
 def test_center_anchor(self):
  c=Engine(540,960,'full');n={'box':{'space':'canvas','anchor':'center','w':.4,'h':.2}}
  r=resolve_box(n,540,960,c.safe)
  self.assertEqual((r.x,r.y,r.w,r.h),(162,384,216,192))
 def test_bottom_right_anchor(self):
  c=Engine(540,960,'full');n={'box':{'space':'canvas','anchor':'bottom_right','w':.3,'h':.25,'dx':-.04,'dy':-.05}}
  r=resolve_box(n,540,960,c.safe)
  self.assertEqual((r.x,r.y,r.w,r.h),(356,672,162,240))
 def test_parent_coordinate_space(self):
  par={'card':Rect(100,100,200,200)};c=Engine()
  n={'box':{'space':'card','anchor':'top_right','w':.4,'h':.2}}
  self.assertEqual(resolve_box(n,540,960,c.safe,par),Rect(220,100,80,40))
 def test_unknown_anchor_rejected(self):
  with self.assertRaises(ValueError):resolve_box({'box':{'anchor':'the-moon'}},540,960,Rect(0,0,540,960))
 def test_bad_box_rejected(self):
  with self.assertRaises(ValueError):resolve_box({'box':{'w':0,'h':.2}},540,960,Rect(0,0,540,960))
 def test_padding_four_dimensions(self):
  p=resolve_padding({'top':8,'right':3,'bottom':6,'left':13});self.assertEqual(p,(8,3,6,13))
  self.assertEqual(inset(Rect(0,0,100,200),p),Rect(13,8,84,186))
 def test_padding_flex(self):
  self.assertEqual(resolve_padding([5,12]),(5,12,5,12))
  self.assertEqual(resolve_padding(8),(8,8,8,8))
 def test_hex_alpha(self):
  self.assertEqual(rgba('#FFFFFF80'),(255,255,255,128))
 def test_distinct_profiles(self):
  self.assertNotEqual(Engine(540,960,'tiktok').safe,Engine(540,960,'reels').safe)
  self.assertTrue(Engine(540,960,'reels').safe.contains(Rect(100,200,100,200)))
 def test_all_fifteen_anchors(self):
  from layout_engine import ANCHOR_FACTORS
  self.assertEqual(len(ANCHOR_FACTORS),15)
  for an in ANCHOR_FACTORS:
   r=resolve_box({'box':{'anchor':an,'space':'canvas','w':.1,'h':.1}},540,960,Rect(0,0,540,960))
   self.assertGreaterEqual(r.x,0);self.assertGreaterEqual(r.y,0);self.assertLessEqual(r.x1,540);self.assertLessEqual(r.y1,960)

class TestRenderer(unittest.TestCase):
 def setUp(self):self.eng=Engine(540,960,'reels');self.bg=Image.new('RGBA',(540,960),(10,22,34,255))
 def test_all_ten_layouts_render(self):
  self.assertEqual(len(v2.CONF['layouts']),10)
  for i,s in enumerate(v2.CONF['shots']):
   im,trace=v2.compose(s['start']+3)
   self.assertEqual(im.size,(540,960));self.assertGreater(len(trace),2)
 def test_deterministic(self):
  a,_=v2.compose(18.65);b,_=v2.compose(18.65)
  self.assertEqual(hashlib.sha256(a.tobytes()).digest(),hashlib.sha256(b.tobytes()).digest())
 def test_presets_are_visually_distinct(self):
  hashes=[]
  for s in v2.CONF['shots']:
   im,_=v2.compose(s['start']+3)
   hashes.append(hashlib.sha256(im.tobytes()).digest())
  self.assertEqual(len(set(hashes)),10)
 def test_layers_z_order(self):
  base={'elements':[{'id':'first','kind':'box','box':{'space':'canvas','w':.5,'h':.5},'fill':'#FF0000FF','outline':False,'z':8},
                    {'id':'second','kind':'box','box':{'space':'canvas','w':.5,'h':.5},'fill':'#0000FFFF','outline':False,'z':12}]}
  a,_=self.eng.render(self.bg,base,1)
  self.assertEqual(a.getpixel((5,5))[:3],(0,0,255))
  base['elements'][1]['z']=3
  b,_=self.eng.render(self.bg,base,1)
  self.assertEqual(b.getpixel((5,5))[:3],(255,0,0))
 def test_safe_violation_is_an_error(self):
  e={'id':'illegal','kind':'text','box':{'space':'canvas','w':.6,'h':.15},'text':'DANGEROUS OFFSET','font_size':18}
  report=inspect_layout(self.eng,{'elements':[e]},2)
  self.assertTrue(any(x['type']=='safe_zone' for x in report['errors']))
 def test_overlapping_text_reports_warning(self):
  el=[{'id':j,'kind':'text','box':{'space':'safe','w':.4,'h':.1,'dx':.1,'dy':.1},'text':'TEST'} for j in ['a','b']]
  report=inspect_layout(self.eng,{'elements':el},1)
  self.assertTrue(any(x['type']=='text_overlap' for x in report['warnings']))
 def test_text_wrap_and_auto_fit(self):
  a={'elements':[{'id':'fit','kind':'text','box':{'space':'safe','w':.3,'h':.06},'text':'SOME VERY VERY LONG WORDS IN SMALL SPACE', 'font_size':34,'min_font_size':8,'max_lines':2}]}
  _,trace=self.eng.render(self.bg,a,1)
  self.assertLessEqual(trace[0]['font_size'],34)
  self.assertGreater(trace[0]['font_size'],0)
 def test_enter_fades(self):
  n={'id':'slow','kind':'box','box':{'space':'canvas','w':1,'h':1},'background':True,'fill':'#FF0000FF','outline':False,'start':0,'end':4,'in':2}
  a,_=self.eng.render(self.bg,{'elements':[n]},.1);b,_=self.eng.render(self.bg,{'elements':[n]},3)
  self.assertLess(a.getpixel((150,150))[0],b.getpixel((150,150))[0])
 def test_trace_does_not_modify_original(self):
  b=self.bg.tobytes();self.eng.render(self.bg,{'elements':[]},1);self.assertEqual(b,self.bg.tobytes())
 def test_thirty_layout_sampled_times_no_collision(self):
  checks=v2.qa_layouts();self.assertEqual(len(checks),30)
  self.assertEqual(sum(len(x['errors']) for x in checks),0)
  self.assertEqual(sum(len(x['warnings']) for x in checks),0)
 def test_layout_graph_valid(self):
  order=v2.validate_graph();self.assertEqual(len(order),36)
  self.assertLess(order.index('camera'),order.index('frame_crop'))
 def test_all_json_valid(self):
  for filename in ('layouts.json','spatial_graph.json'):
   self.assertTrue(json.loads((ROOT/filename).read_text()))
 def test_dimension_catalog_nontrivial(self):
  num=sum(len(x) for x in v2.CONF['dimension_families'].values())
  self.assertGreaterEqual(num,150)
 def test_ffprobe_video_when_present(self):
  p=ROOT/'outputs/baltor_spatial_layout_study_65s_FINAL.mp4'
  if not p.exists():self.skipTest('Final video not rendered yet')
  o=subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)])
  data=json.loads(o)
  self.assertAlmostEqual(float(data['format']['duration']),65,delta=.08)
  video=[s for s in data['streams'] if s['codec_type']=='video'][0]
  self.assertEqual((video['width'],video['height']),(1080,1920))
  self.assertTrue(any(s['codec_type']=='audio' for s in data['streams']))

if __name__=='__main__':unittest.main()
