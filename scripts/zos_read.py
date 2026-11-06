"""One standardized read-only ZOS connection. stdout JSON, no save or report writes.
Use only when source geometry changed or independent source verification is required.
"""
import argparse,ctypes,hashlib,json,math,time,os,sys
from contextlib import contextmanager
from pathlib import Path

def finite(v):
 v=float(v);return v if math.isfinite(v) else None

@contextmanager
def session(path,timeout=60):
 if sys.platform!='win32':raise RuntimeError('Live ZOSAPI requires Windows and a licensed OpticStudio installation; offline drawing does not.')
 import zospy as zp
 k=ctypes.WinDLL('kernel32',use_last_error=True)
 k.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p];k.CreateMutexW.restype=ctypes.c_void_p
 k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong];k.ReleaseMutex.argtypes=[ctypes.c_void_p];k.CloseHandle.argtypes=[ctypes.c_void_p]
 mutex=k.CreateMutexW(None,False,'Local\\OpticalManufacturingZOS');acquired=False;zos=None
 try:
  if not mutex:raise ctypes.WinError(ctypes.get_last_error())
  status=k.WaitForSingleObject(mutex,int(timeout*1000))
  if status not in [0,128]:raise TimeoutError('ZOS access busy; no unrelated process was stopped')
  acquired=True;zos=zp.ZOS(**({'opticstudio_directory':os.environ['OPTICSTUDIO_DIRECTORY']} if os.environ.get('OPTICSTUDIO_DIRECTORY') else {}));oss=zos.connect('standalone');oss.load(str(path));yield oss
 finally:
  try:
   if zos is not None:zos.disconnect()
  finally:
   if acquired:k.ReleaseMutex(mutex)
   if mutex:k.CloseHandle(mutex)

def snapshot(oss,path):
 rows=[]
 for i in range(oss.LDE.NumberOfSurfaces):
  s=oss.LDE.GetSurfaceAt(i);rows.append(dict(surface=i,comment=s.Comment,type=s.TypeName,conic=float(s.Conic),radius=finite(s.Radius),thickness=finite(s.Thickness),material=s.Material,ca=finite(s.SemiDiameter),mechanical=finite(s.MechanicalSemiDiameter),chip=finite(s.ChipZone),stop=bool(s.IsStop),frame=list(oss.LDE.GetGlobalMatrix(i))))
 system=oss.SystemData;w=system.Wavelengths;f=system.Fields;a=system.Aperture
 settings=dict(aperture_type=str(a.ApertureType),aperture_value=float(a.ApertureValue),field_type=str(f.GetFieldType()),fields=[[float(f.GetField(i).X),float(f.GetField(i).Y),float(f.GetField(i).Weight)] for i in range(1,f.NumberOfFields+1)],wavelengths=[[float(w.GetWavelength(i).Wavelength),float(w.GetWavelength(i).Weight)] for i in range(1,w.NumberOfWavelengths+1)],primary=next(i for i in range(1,w.NumberOfWavelengths+1) if w.GetWavelength(i).IsPrimary))
 return dict(source=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),surfaces=rows,system=settings)

def read_source(path,timeout=60):
 with session(path,timeout) as oss:return snapshot(oss,path)

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source',type=Path);ap.add_argument('--timeout',type=float,default=60);args=ap.parse_args()
 t=time.perf_counter();result=read_source(args.source.resolve(),args.timeout);result['seconds']=round(time.perf_counter()-t,3);print('ZOS_JSON_BEGIN');print(json.dumps(result,ensure_ascii=False,allow_nan=False));print('ZOS_JSON_END')
