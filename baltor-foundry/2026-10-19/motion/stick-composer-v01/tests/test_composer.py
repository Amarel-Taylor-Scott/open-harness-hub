import unittest,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import composer
class TestComposer(unittest.TestCase):
 def test_storyboard_covers_timeline_without_gaps(self):
  shots=composer.SHOTS
  self.assertEqual(shots[0]['start'],0)
  self.assertEqual(shots[-1]['end'],70)
  for a,b in zip(shots,shots[1:]):self.assertEqual(a['end'],b['start'])
 def test_dag_valid(self):
  order=composer.topological_order(composer.GRAPH['nodes'])
  self.assertEqual(len(order),len(set(order)))
  self.assertTrue(order.index('camera')<order.index('parallax'))
  self.assertTrue(order.index('picture_in_picture')<order.index('transition'))
 def test_cycle_rejected(self):
  with self.assertRaises(ValueError):
   composer.topological_order([{'id':'a','deps':['b']},{'id':'b','deps':['a']}])
 def test_frames_change_with_time(self):
  a=composer.compose(0).tobytes();b=composer.compose(3).tobytes()
  self.assertNotEqual(hashlib.sha256(a).hexdigest(),hashlib.sha256(b).hexdigest())
 def test_frame_determinism(self):
  a=composer.compose(8.125).tobytes();b=composer.compose(8.125).tobytes()
  self.assertEqual(a,b)
 def test_dimensions(self):
  self.assertEqual(composer.compose(52).size,(540,960))
 def test_asset_layers_exist(self):
  self.assertEqual(set(['sky','mountains','city','pines_far','ground','props','foreground'])-set(composer.ASSETS),set())
 def test_midshot_selection(self):
  self.assertEqual(composer.find_shot(20.5)['id'],'05')
  self.assertEqual(composer.find_shot(68.1)['id'],'15')
 def test_visual_treatments(self):
  a=composer.compose(20.7);b=composer.compose(11.8)
  self.assertNotEqual(a.getpixel((31,319)),b.getpixel((31,319)))
if __name__=='__main__':unittest.main()
