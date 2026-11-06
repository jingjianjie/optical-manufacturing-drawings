"""Two-input intake for centered Standard spherical substrates.
Creates an API-derived archive accepted by drawctl init. Does NOT approve drawings,
export native CAD, make restoration appendices or claim full model reconstruction.
"""
import argparse,copy,hashlib,json,math,shutil,time
from pathlib import Path
import numpy as np
from zos_read import session,snapshot
from profile_geometry import profiles

def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def freeze(source,mechanical,out):
 source=Path(source).resolve();mechanical=Path(mechanical).resolve();out=Path(out).resolve()
 if out.exists():raise FileExistsError('Use a new archive directory; existing archive is never overwritten')
 start=time.perf_counter();mech=json.loads(mechanical.read_text(encoding='utf-8-sig'))
 before=h(source)
 with session(source) as oss:
  data=snapshot(oss,source);rows=data['surfaces'];sd=oss.SystemData
  # Capture optical settings before adding diagnostic F/d/C wavelengths in memory.
  data['system'].update(gcrs=int(sd.Aperture.GCRS.GetSelectedSurface()),stop=int(oss.LDE.StopSurface),
    ray_aiming=str(sd.RayAiming.RayAiming),temperature_c=float(sd.Environment.Temperature),pressure_atm=float(sd.Environment.Pressure),
    field_normalization=str(sd.Fields.Normalization))
  data['configuration_count']=int(oss.MCE.NumberOfConfigurations)
  for row in rows:
   su=oss.LDE.GetSurfaceAt(row['surface']);row.update(type=su.TypeName,conic=float(su.Conic),catalog=su.MaterialCatalog)
   ad=su.ApertureData;row['aperture']={'type':str(ad.CurrentType)}
   if str(ad.CurrentType)=='CircularAperture':
    st=ad.CurrentTypeSettings;row['aperture'].update(min=float(st.MinimumRadius),max=float(st.MaximumRadius),x=float(st.ApertureXDecenter),y=float(st.ApertureYDecenter))
  from zospy import constants as zc
  waves=sd.Wavelengths;wn=[]
  for wavelength in [.4861327,.5875618,.6562725]:
   i=next((i for i in range(1,waves.NumberOfWavelengths+1) if abs(waves.GetWavelength(i).Wavelength-wavelength)<1e-9),None)
   if i is None:waves.AddWavelength(wavelength,1);i=waves.NumberOfWavelengths
   wn.append(i)
  for row in rows:
   if not row['material']:continue
   vals=[float(oss.MFE.GetOperandValue(zc.Editors.MFE.MeritOperandType.INDX,row['surface'],i,0,0,0,0,0,0)) for i in wn]
   row.update(nF=vals[0],nd=vals[1],nC=vals[2],vd=(vals[1]-1)/(vals[0]-vals[2]))
 if h(source)!=before:raise ValueError('Source unexpectedly changed')
 m={'c':np.array([0 if r['radius'] is None else 1/r['radius'] for r in rows[1:]]),'t':np.array([r['thickness'] or 0 for r in rows[1:]])}
 for p in mech['parts']:
  a,b=p['front']+1,p['back']+1
  if b!=a+1 or rows[a]['type']!='Standard' or rows[b]['type']!='Standard' or rows[a]['conic'] or rows[b]['conic']:raise ValueError('Intake supports two-face spherical substrates only')
  p['center_thickness']=rows[a]['thickness'];y,left,right=profiles(m,p)
  p['edge_thickness']=float(right[-1]-left[-1]);p['min_thickness']=float(np.min(right-left))
  for side in ['front','back']:
   f=p[side+'_face'];p[side+'_flat_land']=p['radius']-f['curve_end']-f['transition']-f['outer_bevel']
 def efl(parts):
  M=np.eye(2);n_before=1.
  for p in parts:
   row=rows[p['front']+1];n=row['nd'];c=0 if row['radius'] is None else 1/row['radius']
   M=np.array([[1,0],[-(n-n_before)*c,1]])@M
   M=np.array([[1,p['center_thickness']/n],[0,1]])@M;n_before=n
  r=rows[parts[-1]['back']+1]['radius'];c=0 if r is None else 1/r
  M=np.array([[1,0],[-(1-n_before)*c,1]])@M
  return -1/float(M[1,0])
 parts=mech['parts'];manifest=[];focals={}
 for p in parts:
  name=p['name'];pid=name.replace('_positive','A').replace('_negative','B');manifest.append({'id':pid,'parts':[name]});focals[name]=efl([p])
 for p in parts:
  q=next((q for q in parts if q['front']==p['back']),None)
  if q:
   key=p['name'].split('_')[0]
   if key in focals:raise ValueError('Ambiguous group naming; provide project-specific mapping')
   focals[key]=efl([p,q]);manifest.append({'id':key,'parts':[p['name'],q['name']]})
 for sub in ['data','source','review','native','dxf']:(out/sub).mkdir(parents=True,exist_ok=True)
 shutil.copy2(source,out/'source/design_source.zos')
 save(out/'data/api_surfaces.json',rows);save(out/'data/mechanical.json',mech)
 save(out/'data/material_optics.json',{'efl_d_mm':focals,'wavelength_nm':587.5618,'method':'ZOSAPI INDX and paraxial matrix in air'})
 save(out/'data/drawing_manifest.json',manifest);save(out/'review/main_direct_api.json',dict(data,source_sha256=before))
 report={'archive':str(out),'source_sha256':before,'mechanical_sha256':h(mechanical),'parts':len(parts),'pages':len(manifest),'seconds':round(time.perf_counter()-start,3),'status':'intake only; native CAD / restoration appendix / two reviews required before release'}
 save(out/'intake.json',report);return report

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source');ap.add_argument('mechanical');ap.add_argument('--out',required=True);a=ap.parse_args();print(json.dumps(freeze(a.source,a.mechanical,a.out),ensure_ascii=False))
