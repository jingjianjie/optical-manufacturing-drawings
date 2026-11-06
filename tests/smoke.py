"""Offline portability/geometry/font/PDF regression using generated synthetic data."""
import argparse,hashlib,json,shutil,sys,time,zipfile,copy
from pathlib import Path
import ezdxf
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import drawctl
from make_example import create
from system_layout import draw,physical

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--font',type=Path,required=True);ap.add_argument('--workdir',type=Path,required=True);a=ap.parse_args()
 w=a.workdir.resolve();w.mkdir(parents=True,exist_ok=False);t=time.perf_counter()
 archive=create(w/'archive');project=w/'first/project.json'
 drawctl.initialize(archive,project.parent,'SYNTHETIC',a.font)
 build=drawctl.build(project);pdf=drawctl.export_pdfs(project,True)
 assert len(build['rebuilt'])==4 and pdf['pages']==4
 cfg=drawctl.read(project);assert not Path(cfg['font_file']).is_absolute()
 docs={p.stem:ezdxf.readfile(p) for p in (project.parent/'dxf').glob('*.dxf')}
 assert '平面' in [e.dxf.text for e in docs['SINGLET'].modelspace().query('TEXT')]
 assert '2.000±0.100' in [e.dxf.text for e in docs['PAIR_B'].modelspace().query('TEXT')]
 assert all(any(e.dxf.name=='OMD_POLISHED_CROSS' for e in d.modelspace().query('INSERT')) for d in docs.values())
 for p in (project.parent/'proof_pdf').glob('*.pdf'):
  for pg in PdfReader(p).pages:
   assert abs(float(pg.mediabox.width)*25.4/72-210)<.001
   assert abs(float(pg.mediabox.height)*25.4/72-297)<.001
 # Measure the actual PDF diameter line: x=181 mm, length=20 mm at 2:1.
 ops=PdfReader(project.parent/'proof_pdf/PAIR.pdf').pages[0].get_contents().operations
 current=None;found=[]
 for args,op in ops:
  if op==b'm':current=tuple(map(float,args))
  elif op==b'l':
   end=tuple(map(float,args))
   if current and abs(current[0]*25.4/72-181)<.001 and abs(end[0]-current[0])<.001:
    length=abs(end[1]-current[1])*25.4/72
    if abs(length-40)<.001:found.append(length)
   current=end
 assert found,'Missing exact 40 mm paper diameter line'
 before={p.name:drawctl.sha(p) for p in (project.parent/'dxf').glob('*.dxf')}
 assert not drawctl.build(project)['rebuilt']
 # A relocated project must keep working without original absolute font/source paths.
 moved=w/'relocated';shutil.move(str(project.parent),moved);project=moved/'project.json'
 assert not drawctl.build(project)['rebuilt']
 cfg=drawctl.read(project);cfg['pages'][0]['layout']['radius_front_anchor']=[57,235];drawctl.write(project,cfg)
 delta=drawctl.build(project);assert [r['id'] for r in delta['rebuilt']]==['SINGLET']
 after={p.name:drawctl.sha(p) for p in (moved/'dxf').glob('*.dxf')};assert all(before[n]==after[n] for n in before if n!='SINGLET.dxf')
 # A configurable blackening flag must alter both ink geometry and text.
 cfg['pages'][0]['spec_overrides']={'blackening':{'required':False}};drawctl.write(project,cfg);drawctl.build(project)
 d=ezdxf.readfile(moved/'dxf/SINGLET.dxf')
 assert not list(d.modelspace().query('*[layer=="BLACKEN"]'))
 assert '外圆涂黑' not in [e.dxf.text for e in d.modelspace().query('TEXT')]
 proof=drawctl.package(project,True)
 try:drawctl.export_pdfs(project,False)
 except ValueError as e:assert 'Synthetic' in str(e)
 else:raise AssertionError('Synthetic example released')
 with zipfile.ZipFile(proof['package']) as z:
  assert z.testzip() is None and not any(n.lower().endswith(('.ttf','.ttc','.otf')) for n in z.namelist())
 data=drawctl.read(archive/'source/synthetic_source.json');mech=drawctl.read(archive/'data/mechanical.json')
 layout=draw(data,w/'synthetic-layout.png',mech)
 for mutation in ['missing_type','asphere','negative_thickness','mirror']:
  invalid=copy.deepcopy(data);row=invalid['surfaces'][2]
  if mutation=='missing_type':row.pop('type')
  if mutation=='asphere':row['conic']=-1.
  if mutation=='negative_thickness':row['thickness']=-1.
  if mutation=='mirror':row['material']='MIRROR'
  try:physical(invalid)
  except ValueError:pass
  else:raise AssertionError('Unsupported layout accepted: '+mutation)
 report={'offline_only':True,'synthetic':True,'initial_pages':4,'paper_diameter_mm':found,'relocation_cache_preserved':True,'incremental_pages':['SINGLET'],'font_not_in_delivery_zip':True,'plane_label':True,'thin_CT_rule':True,'blackening_switch':True,'source_inputs_unchanged':True,'total_seconds':round(time.perf_counter()-t,3),'build_seconds':build['seconds'],'pdf_seconds':pdf['seconds'],'layout':layout}
 drawctl.write(w/'test-result.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
