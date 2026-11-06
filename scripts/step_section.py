"""Render a real native STEP section, never construct replacement 3D geometry.
OCP is an optional environment dependency; --ocp-path replaces the old Temp hardcode.
"""
import argparse,sys,json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--ocp-path',type=Path);ap.add_argument('--deflection',type=float,default=.002);a=ap.parse_args()
 import numpy as np
 if a.ocp_path:sys.path.append(str(a.ocp_path))
 from OCP.STEPControl import STEPControl_Reader
 from OCP.TopExp import TopExp_Explorer
 from OCP.TopAbs import TopAbs_EDGE
 from OCP.TopoDS import TopoDS
 from OCP.BRepAdaptor import BRepAdaptor_Curve
 from OCP.GCPnts import GCPnts_QuasiUniformDeflection
 from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
 from OCP.gp import gp_Pln,gp_Pnt,gp_Dir
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 reader=STEPControl_Reader()
 if int(reader.ReadFile(str(a.input.resolve())))!=1:raise ValueError('STEP read failed')
 reader.TransferRoots();cut=BRepAlgoAPI_Section(reader.OneShape(),gp_Pln(gp_Pnt(0,0,0),gp_Dir(1,0,0)),False);cut.Build()
 if not cut.IsDone():raise ValueError('STEP section failed')
 ex=TopExp_Explorer(cut.Shape(),TopAbs_EDGE);curves=[];cast=getattr(TopoDS,'Edge_s',None) or TopoDS.Edge
 while ex.More():
  sample=GCPnts_QuasiUniformDeflection(BRepAdaptor_Curve(cast(ex.Current())),a.deflection)
  if not sample.IsDone():raise ValueError('STEP edge discretization failed')
  curves.append(np.array([[sample.Value(i).X(),sample.Value(i).Y(),sample.Value(i).Z()] for i in range(1,sample.NbPoints()+1)]));ex.Next()
 if not curves:raise ValueError('empty STEP section')
 fig,ax=plt.subplots(figsize=(11,5),constrained_layout=True)
 for c in curves:ax.plot(c[:,2],c[:,1],color='#17466e',lw=.65)
 ax.set_aspect('equal');ax.grid(alpha=.2);ax.set(title=a.input.stem+' | native STEP section x=0',xlabel='Native global z / mm',ylabel='Native global y / mm')
 a.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.output,dpi=150);plt.close(fig)
 pts=np.concatenate(curves);print(json.dumps({'edges':len(curves),'bbox_min':pts.min(0).tolist(),'bbox_max':pts.max(0).tolist(),'output':str(a.output)}))
if __name__=='__main__':main()
