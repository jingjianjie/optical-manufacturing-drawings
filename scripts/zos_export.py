"""Explicit native STEP export. Separate from read-only review and offline layout.
All requested changed groups share one API connection; unchanged source/ranges skip it.
"""
import argparse,json,time
from pathlib import Path
from drawctl import sha,digest,read,write,safe_id
from zos_read import session,snapshot

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--range',action='append',required=True,help='name:first_surface:last_surface');a=ap.parse_args();t=time.perf_counter()
 source=a.source.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);state_path=out/'export-state.json';state=read(state_path) if state_path.exists() else {};groups=[]
 for value in a.range:
  name,first,last=value.split(':');safe_id(name);first,last=int(first),int(last)
  if first<0 or last<first:raise ValueError('invalid surface range')
  signature=digest([sha(source),first,last,.001,'STEP',sha(Path(__file__)),sha(Path(__file__).with_name('zos_read.py'))]);path=out/f'{name}.step';old=state.get(name,{})
  if old.get('input')!=signature or not path.exists() or old.get('output')!=sha(path):groups.append((name,first,last,signature,path))
 if groups:
  from zospy import constants as zc
  with session(source) as oss:
   snap=snapshot(oss,source);write(out/'source_api.json',snap)
   for name,first,last,signature,path in groups:
    if last>=oss.LDE.NumberOfSurfaces:raise ValueError('range outside source model')
    tool=oss.Tools.OpenExportCAD()
    try:
     tool.FileType=zc.Tools.General.CADFileType.STEP;tool.OutputFileName=str(path);tool.FirstSurface=first;tool.LastSurface=last;tool.ExportDummySurfaces=True;tool.DummyThickness=.001;tool.SurfacesAsSolids=True;tool.NumberOfRays=0;tool.Field=0;tool.Wavelength=snap['system']['primary'];tool.DeleteVignetted=True
     assert tool.FirstSurface==first and tool.LastSurface==last and abs(tool.DummyThickness-.001)<1e-10
     tool.RunAndWaitForCompletion()
     if not tool.Succeeded or not path.is_file():raise RuntimeError('native STEP export failed')
    finally:tool.Close()
    state[name]={'input':signature,'output':sha(path),'source':sha(source),'range':[first,last]};write(state_path,state)
 print(json.dumps({'exported':[x[0] for x in groups],'api_connected':bool(groups),'seconds':round(time.perf_counter()-t,3)}))
if __name__=='__main__':main()
