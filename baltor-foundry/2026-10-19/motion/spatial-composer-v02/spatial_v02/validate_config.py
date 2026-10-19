#!/usr/bin/env python3
"""Validate schema, references, time continuity, IDs and layout bounds metadata."""
from pathlib import Path
import sys,json
import jsonschema
ROOT=Path(__file__).resolve().parent

def validate(path=ROOT/'layouts.json'):
 cfg=json.loads(Path(path).read_text())
 sch=json.loads((ROOT/'layout_schema.json').read_text())
 jsonschema.Draft202012Validator(sch).validate(cfg)
 layouts=cfg['layouts'];shots=cfg['shots']
 assert len({str(i['id']) for i in shots})==len(shots),'Duplicate shot IDs'
 assert abs(shots[0]['start'])<1e-6,'Timeline must start at zero'
 assert abs(shots[-1]['end']-cfg['duration_sec'])<1e-6,'Timeline duration mismatch'
 for i,s in enumerate(shots):
  assert s['layout'] in layouts,'Missing layout '+s['layout']
  assert s['end']>s['start'],'Shot end must be after start'
  if i:assert abs(shots[i-1]['end']-s['start'])<1e-6,'Gap or overlap in shot timeline'
 for key,val in layouts.items():
  els=val['elements'];ids=[str(n['id']) for n in els]
  assert len(ids)==len(set(ids)),'Duplicate element ID in '+key
  for n in els:
   b=n['box'];assert float(b['w'])>0 and float(b['h'])>0
   if 'start' in n and 'end' in n:assert n['start']<n['end']
 print('Valid schema,',len(layouts),'layout configurations,',len(shots),'contiguous shots,',sum(len(x['elements']) for x in layouts.values()),'elements')
 return True

if __name__=='__main__':
 validate(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'layouts.json')
