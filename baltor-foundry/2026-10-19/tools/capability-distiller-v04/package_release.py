"""Reproducible ZIP packages with fixed timestamps/order (source and artifact bytes pinned)."""
from pathlib import Path
import zipfile,hashlib,json
R=Path(__file__).parent
O=Path('/mnt/data')
def make_zip(out,paths):
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for f in sorted(paths):
            if not f.is_file() or '__pycache__' in f.parts or f.suffix=='.pyc':continue
            info=zipfile.ZipInfo(str(Path('Baltor_Capability_Distiller_v04') / f.relative_to(R)).replace('\\','/'))
            info.date_time=(1980,1,1,0,0,0)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o644<<16)
            z.writestr(info,f.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=8)
    return {'path':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
allf=[p for p in R.rglob('*') if p.is_file() and not any(x in p.parts for x in ['__pycache__','.git'])]
lib=[f for f in allf if 'commercial' not in f.parts or f.name=='render_last_tab.py']
# Exclude absolute QA artefacts requiring external data? All material is from own project.
media=[f for f in allf if 'commercial' in f.parts and f.suffix in ['.mp4','.wav','.jpg','.json'] or f.name=='render_last_tab.py']
full=make_zip(O/'Baltor_Capability_Foundry_v04_COMPLETE.zip',allf)
code=make_zip(O/'Baltor_Capability_Distiller_v04_Binaries_Source.zip',lib)
ads=make_zip(O/'Baltor_Original_Ad_Prototypes_30s.zip',media)
# Rebuild the same source ZIP to prove archive byte stability.
again=make_zip(O/'_release_repeat_check.zip',lib)
assert again['sha256']==code['sha256'],(again,code)
(O/'_release_repeat_check.zip').unlink()
print(json.dumps({'complete':full,'code':code,'ads':ads,'archive_byte_stable':True},indent=2))
