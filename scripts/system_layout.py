"""Self-contained centered sequential layout, from live ZOS or a saved API snapshot.
Mechanical recipe optional; with it, outline uses actual substrate edges. Otherwise
native mechanical radius / clear+chip flange is a simplified optical outline.
No optimization, no viewer export, no other skill or repository dependency.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from profile_geometry import sphere_sag,profiles

def matrix(row):
    values=row.get('frame')
    if not values or len(values)!=13 or not values[0]:raise ValueError('Missing successful GetGlobalMatrix for surface '+str(row['surface']))
    return np.array(values[1:10]).reshape(3,3),np.array(values[10:13])

def live(path):
    from zos_read import session,snapshot
    from zospy import constants as zc
    with session(path) as oss:
        data=snapshot(oss,path)
        for row in data['surfaces']:
            s=oss.LDE.GetSurfaceAt(row['surface'])
            row.update(type=s.TypeName,conic=float(s.Conic))
        selected=physical(data)
        f=data['system']['fields'];mode=str(oss.SystemData.Fields.Normalization)
        radial=max([math.hypot(x,y) for x,y,_ in f] or [1]) or 1
        dx=max([abs(x) for x,_,_ in f] or [1]) or 1;dy=max([abs(y) for _,y,_ in f] or [1]) or 1
        if mode=='Radial':dx=dy=radial
        elif mode!='Rectangular':raise ValueError('Unsupported field normalization '+mode)
        cases=[(i,x/dx,y/dy,p) for i,(x,y,_) in enumerate(f,1) for p in [-1.,-.5,0.,.5,1.]]
        points=[[] for _ in cases];active=[True]*len(cases);summary={}
        for row in selected:
            i=row['surface'];tool=oss.Tools.OpenBatchRayTrace()
            try:
                rays=tool.CreateNormUnpol(len(cases),zc.Tools.RayTrace.RaysType.Real,i)
                for _,hx,hy,py in cases:
                    if not rays.AddRay(data['system']['primary'],hx,hy,0,py,zc.Tools.RayTrace.OPDMode.None_):raise RuntimeError('AddRay failed')
                tool.RunAndWaitForCompletion()
                if not rays.StartReadingResults():raise RuntimeError('No ray results')
                rot,origin=matrix(row);valid=0;heights=[]
                for k in range(len(cases)):
                    r=rays.ReadNextResult();xyz=np.array(list(r[4:7]),float)
                    good=bool(r[0]) and int(r[2])==0 and int(r[3])==0 and np.isfinite(xyz).all()
                    active[k]=active[k] and good
                    if active[k]:
                        points[k].append((rot@xyz+origin).tolist());valid+=1;heights.append(float(np.hypot(*xyz[:2])))
                summary[str(i)]={'surviving_samples':valid,'max_sample_radius':max(heights,default=None),'ca_radius':row['ca']}
            finally:tool.Close()
        data['layout_rays']=[{'field':cases[k][0],'points':p} for k,p in enumerate(points)]
        data['layout_sample_summary']=summary
        data['layout_sampling']='primary wavelength; five meridional pupil points per source field; each ray stops at first failed/clipped surface'
    return data

def physical(data):
    rows=[]
    for row in data['surfaces']:
        if row['surface']==0:continue  # OBJECT may be at infinity.
        if 'type' not in row or 'conic' not in row:
            raise ValueError('Snapshot must include explicit type/conic; use system_layout --save-snapshot')
        if row['type']!='Standard' or row['conic']!=0:
            raise ValueError('This renderer supports centered Standard spherical/plane surfaces only')
        if str(row.get('material','')).upper()=='MIRROR':raise ValueError('Reflective systems need dedicated coordinates')
        if row.get('thickness') is not None and row['thickness']<0:raise ValueError('Negative thickness is outside this centered renderer scope')
        radius=row.get('mechanical')
        if radius is None or not 0<radius<1e5:continue
        rot,pos=matrix(row)
        if not np.allclose(rot,np.eye(3),atol=1e-9) or not np.allclose(pos[:2],0,atol=1e-7):
            raise ValueError('Tilted/decentered surface needs a dedicated renderer')
        if not np.isfinite(pos).all():raise ValueError('Non-finite global position')
        rows.append(row)
    return rows

def draw(data,out,mechanical=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    rows=physical(data);by={r['surface']:r for r in rows}
    if not rows:raise ValueError('No drawable physical surfaces')
    fig,ax=plt.subplots(figsize=(14,6));extent=[]
    def add_part(x1,x2,y,label,k):
        poly=np.column_stack([np.r_[x1,x2[::-1]],np.r_[y,y[::-1]]])
        ax.add_patch(Polygon(poly,closed=True,facecolor=['#badcf4','#d5e7bb'][k%2],edgecolor='#477a9e',alpha=.7))
        extent.extend(poly.tolist());ax.text(float((x1.mean()+x2.mean())/2),float(max(y))+1,label,ha='center',fontsize=9)
    if mechanical:
        source=data['surfaces'][1:];m={'c':np.array([0 if r['radius'] is None else 1/r['radius'] for r in source]),'t':np.array([r['thickness'] or 0 for r in source])}
        base=matrix(data['surfaces'][1])[1][2]
        for k,p in enumerate(mechanical['parts']):
            y,x1,x2=profiles(m,p);add_part(x1+base,x2+base,y,p['name'],k)
    else:
        for k,row in enumerate(rows):
            i=row['surface']
            if not row['material']:continue
            if row['material'].upper()=='MIRROR':raise ValueError('Reflective systems need dedicated coordinates')
            back=by.get(i+1)
            if back is None:raise ValueError('Missing substrate back surface')
            outer=max(row['mechanical'],back['mechanical']);y=np.linspace(-outer,outer,801)
            def curve(s):
                r=s['radius'];c=0 if r is None else 1/r
                cutoff=min(s['mechanical'],(s['ca'] or 0)+max(s['chip'],0))
                return matrix(s)[1][2]+sphere_sag(c,np.minimum(abs(y),cutoff))
            add_part(curve(row),curve(back),y,(row.get('comment') or f'S{i}-{i+1}'),k)
    for row in rows:
        i=row['surface'];r=row['radius'];ca=row['ca'];z=matrix(row)[1][2]
        if ca is not None and ca>0:
            y=np.linspace(-ca,ca,151);x=z+sphere_sag(0 if r is None else 1/r,y)
            ax.plot(x,y,'--',color='#666',lw=.65)
        if row['stop']:ax.axvline(z,color='#888',ls=':',lw=.8);ax.text(z,0,' STOP',fontsize=8)
    for ray in data.get('layout_rays',[]):
        pts=np.array(ray['points'])
        if len(pts)>1:ax.plot(pts[:,2],pts[:,1],lw=.65,color=plt.cm.tab10((ray['field']-1)%10))
    if extent:
        e=np.array(extent);span=max(float(np.ptp(e[:,0])),10);height=max(float(abs(e[:,1]).max()),5)
        allpos=[matrix(r)[1][2] for r in rows];ax.set_xlim(min(allpos)-span*.06,max(allpos)+span*.06);ax.set_ylim(-height*1.25,height*1.35)
    ax.set_aspect('equal');ax.set_xlabel('Global Z [mm]');ax.set_ylabel('Global Y [mm]');ax.grid(alpha=.2)
    title='Solid: substrate mechanical outline; dashed: clear aperture'
    if not mechanical:title+=' | native simplified edges'
    if not data.get('layout_rays'):title+=' | no ray evidence in snapshot'
    ax.set_title(title,fontsize=10);fig.tight_layout();out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=150);plt.close(fig)
    return {'image':str(out),'physical_surfaces':[r['surface'] for r in rows],'recipe_used':bool(mechanical),'ray_paths':len(data.get('layout_rays',[]))}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--zos',type=Path);g.add_argument('--snapshot',type=Path);ap.add_argument('--mechanical',type=Path);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--save-snapshot',type=Path);a=ap.parse_args()
    data=live(a.zos.resolve()) if a.zos else json.loads(a.snapshot.read_text(encoding='utf-8-sig'))
    mech=json.loads(a.mechanical.read_text(encoding='utf-8-sig')) if a.mechanical else None
    if a.save_snapshot:
        a.save_snapshot.parent.mkdir(parents=True,exist_ok=True);a.save_snapshot.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(draw(data,a.out,mech),ensure_ascii=False))
