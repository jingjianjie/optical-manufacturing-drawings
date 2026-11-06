"""Create a destructive, non-design ZOS parser sample from fictitious surfaces.
Requires Windows, ZOSPy and a licensed OpticStudio. Never loads a private design.
All thicknesses and fields are zero; surfaces shuffled; aperture diameter 0.1 mm.
The one positive wavelength is a software placeholder, not a design condition.
"""
import argparse,hashlib,json,random,math
from pathlib import Path

def generate(out):
 import zospy as zp
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 zos=zp.ZOS();oss=zos.connect('standalone')
 try:
  oss.new(saveifneeded=False)
  # No source prescription or surface-order mapping is carried into this file.
  values=[18.,-25.,42.,-60.,85.,-110.,130.,-150.,175.,-200.]
  random.Random(20261106).shuffle(values)
  while oss.LDE.NumberOfSurfaces<len(values)+3:oss.LDE.InsertNewSurfaceAt(2)
  sd=oss.SystemData
  sd.TitleNotes.Title='SANITIZED SHUFFLED PARSER SAMPLE'
  sd.TitleNotes.Author=''
  sd.TitleNotes.Notes='Fictitious geometry. Zero spacings and fields. Not an optical design. Aperture diameter 0.1 mm; placeholder wavelength 0.55 um.'
  sd.Aperture.ApertureType=zos.ZOSAPI.SystemData.ZemaxApertureType.EntrancePupilDiameter
  sd.Aperture.ApertureValue=.1
  sd.RayAiming.RayAiming=zos.ZOSAPI.SystemData.RayAimingMethod.Off
  fields=sd.Fields;fields.DeleteAllFields();fields.SetFieldType(zos.ZOSAPI.SystemData.FieldType.Angle)
  fields.GetField(1).X=0.;fields.GetField(1).Y=0.;fields.GetField(1).Weight=1.
  waves=sd.Wavelengths
  while waves.NumberOfWavelengths>1:waves.RemoveWavelength(waves.NumberOfWavelengths)
  waves.GetWavelength(1).Wavelength=.55;waves.GetWavelength(1).Weight=1.;waves.GetWavelength(1).MakePrimary()
  for i in range(oss.LDE.NumberOfSurfaces):
   s=oss.LDE.GetSurfaceAt(i)
   s.RadiusCell.MakeSolveFixed();s.ThicknessCell.MakeSolveFixed()
   s.Radius=values[i-2] if 2<=i<2+len(values) else 0.
   s.Thickness=0.;s.Material='';s.Comment='';s.Conic=0.
   s.SemiDiameterCell.MakeSolveFixed();s.MechanicalSemiDiameterCell.MakeSolveFixed()
   s.SemiDiameter=.05;s.MechanicalSemiDiameter=.05;s.ChipZone=0.
  oss.LDE.GetSurfaceAt(1).IsStop=True
  sd.Aperture.GCRS.SetSelectedSurface(1)
  oss.MFE.DeleteAllRows()
  zosfile=out/'sanitized-shuffled.zos';zmxfile=out/'sanitized-shuffled.zmx'
  oss.save_as(str(zosfile));oss.save_as(str(zmxfile));oss.load(str(zosfile))
  sd=oss.SystemData;fields=sd.Fields
  rows=[{'surface':i,'radius':None if i in [0,1,12] else float(oss.LDE.GetSurfaceAt(i).Radius),'thickness':float(oss.LDE.GetSurfaceAt(i).Thickness),'material':oss.LDE.GetSurfaceAt(i).Material,'comment':oss.LDE.GetSurfaceAt(i).Comment} for i in range(oss.LDE.NumberOfSurfaces)]
  assert all(s['thickness']==0 for s in rows[:-1])
  assert all(not s['material'] and not s['comment'] for s in rows)
  # IMAGE has no following physical spacing; OpticStudio normalizes it to infinity.
  assert math.isinf(rows[-1]['thickness']) or rows[-1]['thickness']==0
  assert abs(sd.Aperture.ApertureValue-.1)<1e-12
  report={'synthetic':True,'private_source_loaded':False,'intended_use':'parser/load smoke test only; no usable optical design',
   'surface_count':len(rows),'all_inter_surface_spacings_zero':True,'image_trailing_thickness':'OpticStudio infinity sentinel; no following physical interval','all_materials_removed':True,'all_surface_comments_removed':True,
   'field_xy':[[float(fields.GetField(1).X),float(fields.GetField(1).Y)]],
   'aperture_type':'EntrancePupilDiameter','aperture_diameter_mm':.1,'stop_semi_diameter_mm':.05,
   'placeholder_wavelength_um':.55,'weight':1,'source_optimization_restored':False,
   'fictitious_shuffled_radii_mm':values,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [zosfile,zmxfile]}}
  (out/'sanitization.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps(report,ensure_ascii=False))
 finally:zos.disconnect()

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();generate(a.out)
