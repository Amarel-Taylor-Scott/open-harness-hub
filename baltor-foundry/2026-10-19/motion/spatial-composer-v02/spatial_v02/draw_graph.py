import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
nodes=json.loads((ROOT/'spatial_graph.json').read_text())['nodes']
color={'implemented':'#8BE0D1','prototype':'#FFD88C','planned':'#ADB4C4','human_required':'#F4A9AA'}
lines=['digraph BaltorSpatial {','  graph [bgcolor="#0B1420",rankdir=LR,splines=ortho,pad=0.2,ranksep=.57,nodesep=.20];','  node [shape=box,style="rounded,filled",fillcolor="#172638",color="#4C6776",fontcolor="#EDF3F5",fontname="DejaVu Sans",fontsize=10,margin=".10,.07"];','  edge [color="#647785",penwidth=1.0,arrowsize=.5];']
for node in nodes:
 c=color[node['status']]
 lines.append(f'  "{node["id"]}" [label="{node["op"]}\\n{node["id"]}",color="{c}"];')
for node in nodes:
 for dep in node['deps']:
  lines.append(f'  "{dep}" -> "{node["id"]}";')
lines.append('}')
dot=ROOT/'spatial_dag.dot';dot.write_text('\n'.join(lines)+'\n')
for ext in ['png','svg']:
 dest=ROOT/'outputs'/('baltor_spatial_dag.'+ext)
 cmd=['dot',f'-T{ext}','-Gdpi=130',str(dot),'-o',str(dest)]
 subprocess.run(cmd,check=True)
 print('Graph',dest,'bytes',dest.stat().st_size)
