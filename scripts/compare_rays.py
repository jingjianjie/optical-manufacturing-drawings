"""Automatic sampled reconstruction equivalence. Summary + failures only by default.
The sample is primary wavelength, all radial-normalized fields and five meridional
pupil points per physical surface. This is not coupling/performance acceptance.
"""
import argparse,hashlib,json,math,time
from pathlib import Path
from zos_read import session,snapshot

def trace(oss,cases,wave,surfaces):
 from zospy import constants as zc
 out=[]
 for i in surfaces:
  tool=oss.Tools.OpenBatchRayTrace()
  try:
   data=tool.CreateNormUnpol(len(cases),zc.Tools.RayTrace.RaysType.Real,i)
   for fi,hx,hy,py in cases:
    if not data.AddRay(wave,hx,hy,0.,py,zc.Tools.RayTrace.OPDMode.None_):raise RuntimeError('AddRay failed')
   tool.RunAndWaitForCompletion()
   if not data.StartReadingResults():raise RuntimeError('StartReadingResults failed')
   for ci,case in enumerate(cases):
    r=data.ReadNextResult()
    out.append({'surface':i,'case':ci,'success':bool(r[0]),'error':int(r[2]),'vignette':int(r[3]),'xyz':list(map(float,r[4:7])),'lmn':list(map(float,r[7:10]))})
  finally:tool.Close()
 return out

def compare(source,rebuilt):
 start=time.perf_counter();source=Path(source).resolve();rebuilt=Path(rebuilt).resolve()
 with session(source) as oss:
  if str(oss.SystemData.Fields.Normalization)!='Radial':raise ValueError('This frozen sampler supports Radial normalization only')
  src=snapshot(oss,source);system=src['system'];n=oss.LDE.NumberOfSurfaces
  f=system['fields'];scale=max([math.hypot(x,y) for x,y,_ in f] or [1]) or 1
  cases=[(i,x/scale,y/scale,py) for i,(x,y,_) in enumerate(f,1) for py in [-1.,-.5,0.,.5,1.]]
  a=trace(oss,cases,system['primary'],range(1,n));oss.load(str(rebuilt));reb=snapshot(oss,rebuilt)
  if oss.LDE.NumberOfSurfaces!=n:raise ValueError('Different surface counts')
  if system!=reb['system']:raise ValueError('Sample-defining system settings differ; check restoration before tracing')
  b=trace(oss,cases,system['primary'],range(1,n))
 failures=[];mx=md=0.;ev=0;success=0;valid=0
 for x,y in zip(a,b):
  status=(x['error'],x['vignette'])==(y['error'],y['vignette']);ok=x['success']==y['success']
  ev+=not status;success+=not ok;dx=dl=0.
  if x['success'] and y['success'] and x['error']==y['error']==0:
   valid+=1
   diffs=[abs(u-v) for key in ['xyz','lmn'] for u,v in zip(x[key],y[key])]
   if not all(map(math.isfinite,diffs)):dx=dl=float('inf')
   else:dx=max(diffs[:3]);dl=max(diffs[3:])
   mx=max(mx,dx);md=max(md,dl)
  if not status or not ok or dx>1e-6 or dl>1e-9:
   failures.append({'surface':x['surface'],'case':x['case'],'xyz':dx if math.isfinite(dx) else None,'lmn':dl if math.isfinite(dl) else None,'source':x,'rebuild':y})
 result={'pairs':len(a),'valid_coordinate_pairs':valid,'max_xyz_mm':mx if math.isfinite(mx) else None,'max_lmn':md if math.isfinite(md) else None,
   'err_vig_mismatches':ev,'success_mismatches':success,'bad_count':len(failures),'failures':failures,'pass':not failures and valid>0,
   'thresholds':{'xyz_mm':1e-6,'lmn':1e-9},'source_sha256':src['sha256'],'rebuild_sha256':reb['sha256'],'seconds':round(time.perf_counter()-start,3),
   'scope':'primary wavelength, all source fields, five meridional pupil points per surface; sampled equivalence only'}
 return result,{'source':a,'rebuild':b}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source');ap.add_argument('rebuild');ap.add_argument('--out',type=Path,required=True);ap.add_argument('--details',type=Path);a=ap.parse_args()
 result,detail=compare(a.source,a.rebuild);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
 if a.details:a.details.write_text(json.dumps(detail,ensure_ascii=False),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='failures'},ensure_ascii=False));raise SystemExit(0 if result['pass'] else 1)
