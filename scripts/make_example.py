"""Original synthetic singlet + unequal-diameter doublet for offline pipeline tests.
No actual lens prescription, material catalog, API receipt or production approval.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from profile_geometry import profiles,sphere_sag
from drawctl import write,sha

def create(out):
    out=Path(out).resolve()
    if out.exists():raise FileExistsError('Choose a new example archive')
    for sub in ['data','source','review','native','dxf']:(out/sub).mkdir(parents=True)
    # Demo optical numbers are deliberately synthetic; EFL is for the demo medium only.
    raw=[(None,None,'',None,None),(None,12.,'',3.,3.),(35.,6.,'DEMO_CROWN',8.,9.),(None,18.,'',8.,9.),(40.,5.,'DEMO_CROWN',8.,9.),(-45.,2.,'DEMO_FLINT',8.,10.),(-80.,25.,'',8.5,10.),(None,0.,'',12.,12.)]
    rows=[];z=-12.
    for i,(r,t,g,ca,mech) in enumerate(raw):
        if i==0:gz=-1e10
        else:gz=z
        rows.append(dict(surface=i,radius=r,thickness=t,material=g,catalog='SYNTHETIC' if g else '',nd=1.52 if g=='DEMO_CROWN' else 1.65 if g else 1.,vd=60. if g=='DEMO_CROWN' else 30. if g else 0.,ca=ca,mechanical=mech,chip=0.,stop=i==1,type='Standard',conic=0.,comment={2:'SINGLET',4:'DOUBLET'}.get(i,''),frame=[True,1.,0.,0.,0.,1.,0.,0.,0.,1.,0.,0.,gz]))
        if i>0:z+=t or 0
    def part(name,front,back,radius,front_end=None,back_end=None):
        p={'name':name,'front':front-1,'back':back-1,'radius':radius,'center_thickness':rows[front]['thickness']}
        for side,j,cutoff,sign in [('front',front,front_end,1),('back',back,back_end,-1)]:
            rc=radius-.2 if cutoff is None else cutoff;c=0 if rows[j]['radius'] is None else 1/rows[j]['radius']
            p[side+'_face']={'surface':j-1,'curve_end':rc,'transition':0.,'plateau':float(sphere_sag(c,rc)),'outer_bevel':.2,'bevel_angle':45.,'inward':sign}
            p[side+'_flat_land']=radius-p[side+'_face']['outer_bevel']-rc
        return p
    parts=[part('SINGLET',2,3,9.),part('PAIR_positive',4,5,9.,back_end=8.8),part('PAIR_negative',5,6,10.,front_end=9.)]
    m={'c':np.array([0 if r['radius'] is None else 1/r['radius'] for r in rows[1:]]),'t':np.array([r['thickness'] or 0 for r in rows[1:]])}
    for p in parts:
        y,a,b=profiles(m,p);p.update(edge_thickness=float(b[-1]-a[-1]),min_thickness=float(min(b-a)))
    manifest=[{'id':name,'parts':[p['name']],'efl_key':p['name'],'layout':{'surface_front_anchor':[58,210],'radius_back_anchor':[145,176]}} for name,p in zip(['SINGLET','PAIR_A','PAIR_B'],parts)]+[{'id':'PAIR','parts':['PAIR_positive','PAIR_negative'],'efl_key':'PAIR','layout':{'cement_anchor':[140,236],'radius_back_anchor':[145,176]}}]
    def focal(ps):
        M=np.eye(2);before=1.
        for p in ps:
            r=rows[p['front']+1];n=r['nd'];c=0 if r['radius'] is None else 1/r['radius'];M=np.array([[1,0],[-(n-before)*c,1]])@M;M=np.array([[1,p['center_thickness']/n],[0,1]])@M;before=n
        r=rows[ps[-1]['back']+1]['radius'];c=0 if r is None else 1/r;M=np.array([[1,0],[-(1-before)*c,1]])@M
        return -1/float(M[1,0])
    focals={p['name']:focal([p]) for p in parts};focals['PAIR']=focal(parts[1:])
    data={'surfaces':rows,'system':{'wavelengths':[[.55,1]],'fields':[[0,0,1]],'primary':1},'synthetic_example':True}
    src=out/'source/synthetic_source.json';write(src,data)
    write(out/'data/api_surfaces.json',rows);write(out/'data/mechanical.json',{'parts':parts,'source':'synthetic educational geometry'})
    write(out/'data/material_optics.json',{'efl_d_mm':focals,'wavelength_nm':550.,'method':'synthetic constant indices; not a material catalog'})
    write(out/'data/drawing_manifest.json',manifest)
    write(out/'review/main_direct_api.json',{'source_sha256':sha(src),'surfaces':rows,'synthetic_example':True,'note':'Schema fixture, NOT a ZOSAPI measurement'})
    write(out/'SYNTHETIC_EXAMPLE.json',{'synthetic':True,'release_allowed':False,'description':'Original educational fixture; no approved glass or optical performance'})
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();print(create(a.out))
