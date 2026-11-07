"""Configurable generic A4 renderer; project requirements govern notation.
Supports centered spherical singlets and cemented doublets only.
Each call returns one DXF document. No API connection or output side effects.
"""
import math
import numpy as np
import ezdxf
from drawing_ops import *
from profile_geometry import profiles,sag
from page_policy import classify
from technical_spec import effective_spec,coating_text,render_notes

def paraxial_focals(rows,ps):
 """Paraxial matrix in air, state [y,n*u], signed radii and real nd/CT.
 M maps the front vertex to the back vertex. EFL=-1/C, front focal point
 position from the front vertex FFL=D/C, back focal point from the back
 vertex along +z BFL=-A/C. Positive FFL is therefore to the right of the
 front vertex; a positive lens normally has negative FFL and positive BFL.
 """
 M=np.eye(2);n_before=1.
 for p in ps:
  j=p['front'];n=rows[j+1]['nd'];c=0. if rows[j+1]['radius'] is None else 1./rows[j+1]['radius']
  M=np.array([[1,0],[-(n-n_before)*c,1]])@M
  M=np.array([[1,(rows[j+1]['thickness'] or 0.)/n],[0,1]])@M;n_before=n
 j=ps[-1]['back'];r=rows[j+1]['radius'];c=0. if r is None else 1./r
 M=np.array([[1,0],[-(1.-n_before)*c,1]])@M
 A,B,C,D=(float(M[0,0]),float(M[0,1]),float(M[1,0]),float(M[1,1]))
 return -1./C,D/C,-A/C

def render_page(snapshot,item,template,layout,title,drawing_prefix,page,page_count,spec,font_name=None):
 if not font_name:raise ValueError('Provide a registered font filename')
 spec=effective_spec(spec)
 rows=snapshot['surfaces'];surfs=rows[1:]
 m=dict(c=np.array([0 if s['radius'] is None else 1/s['radius'] for s in surfs]),t=np.array([s['thickness'] or 0 for s in surfs]),ca=np.array([s['ca'] for s in surfs]))
 parts=snapshot['mechanical']['parts'];z=np.r_[0,np.cumsum(m['t'][:-1])]
 opt=snapshot['material_optics'];name=item['id'];inds=item['parts'];key=item['efl_key']
 tol=spec['tolerances'];mat=spec['material_requirements'];surf=spec['surface_requirements'];coat=spec['coating'];ink=spec['blackening'];bevel=spec['chamfer']
 coat_text=coating_text(coat)
 def prepare(page,name,ps,efl,coat_faces):
  d=ezdxf.readfile(template);d.units=4;d.styles.new('CN',dxfattribs={'font':font_name})
  for layer in ['ANNOTATION','POLISHED_MARK','TABLE','GLASS','AXIS','BLACKEN']:d.layers.new(layer,dxfattribs={'color':7})
  d.linetypes.new('OPTICAL_AXIS',dxfattribs={'description':'thin double dash dot','pattern':[6.,3.,-.6,0.,-.6,0.,-1.2]})
  d.linetypes.new('INK_CHAIN',dxfattribs={'description':'blackening chain','pattern':[4.,2.5,-.5,0.,-1.]})
  d.layers.get('AXIS').dxf.linetype='OPTICAL_AXIS'
  d.layers.get('BLACKEN').dxf.linetype='INK_CHAIN'
  d.layers.get('BLACKEN').dxf.lineweight=50
  ms=d.modelspace()
  for e in list(ms.query('MTEXT')):
   if 80<float(e.dxf.insert.y)<120:ms.delete_entity(e);continue
   e.dxf.style='CN'
   if float(e.dxf.insert.y)<65:e.dxf.char_height=2.;e.dxf.width=9 if e.plain_text().strip() in ['标记','处数'] else e.dxf.width
   if e.plain_text().replace(' ','').startswith('共') and '张' in e.plain_text():e.text=f'共 {page_count} 张'
   if e.plain_text().replace(' ','').startswith('第') and '张' in e.plain_text():e.text=f'第 {page} 张'
  values=[mat['delta_nD'],mat['delta_nF_minus_nC'],mat['homogeneity'],mat['birefringence'],mat['absorption'],mat['striae'],mat['bubbles'],str(surf['N']),str(surf['delta_N']),surf['delta_R'],surf['scratch_dig'],surf['optical_decenter_arcmin']+'′',f'Ø{2*m["ca"][ps[0]["front"]]:.2f}',f'Ø{2*m["ca"][ps[-1]["back"]]:.2f}',f'{efl:.3f}']
  if kind=='胶合件':
   if not spec['assembly_tables']['material_values']:values[:7]=['-']*7
   if not spec['assembly_tables']['part_values']:values[7:]=['-']*8
  for yy,value in zip([278,272,266,260,254,248,242,230,224,218,212,206,200,194,188],values):text(ms,value,(40,yy),2.,True)
  text(ms,title+' / '+kind+' / 名义尺寸；单位mm',(122,280),2.8,True)
  text(ms,name,(110,50),3.2,True);text(ms,f'{drawing_prefix}-{page:02}',(170,51),2.5,True)
  for k,p in enumerate(ps):
   rr=rows[p['front']+1];line=rr['material'];cat=(rr.get('catalog') or '').replace('.AGF','');nd=rr.get('nd');vd=rr.get('vd')
   if spec.get('title_material_details',False):
    if cat:line+=f'/{cat}'
    if nd is not None:line+=f' nd{nd:.4f}'
    if vd is not None:line+=f' Vd{vd:.3f}'
   text(ms,line,(120,26-5*k),1.7,True)
  text(ms,'1件/套',(120,12.5),2.,True);text(ms,'设计图',(155,35),2.,True);text(ms,'—',(177,35),2.,True);text(ms,'2:1',(192,35),2.2,True)
  text(ms,f'焦距波长：{opt.get("wavelength_nm",587.562):.3f}nm',(170,21),2.,True);text(ms,'签署栏留供人工签署',(170,14),1.8,True)
  text(ms,(coat_text+'；'+coat_faces) if coat_faces else '本件不镀膜',(114,61.8),1.6,True)
  return d,ms
 ps=[parts[i] for i in inds]
 kind,faces=classify(parts,ps,spec.get('face_types',{}))
 nominal_ct=sum(p['center_thickness'] for p in ps)
 ct_tol=center_thickness_tolerance(tol,nominal_ct,len(ps)==1)
 role_tol=tol.get('cemented_child_center_thickness_mm' if kind=='单片:子片' else 'cemented_assembly_center_thickness_mm') if kind!='单片' else None
 if role_tol is not None:ct_tol=role_tol
 explicit=item.get('spec_overrides',{}).get('tolerances',{})
 if 'center_thickness_mm' in explicit:ct_tol=explicit['center_thickness_mm']
 def _air(s):return not (s or '').strip()
 def _before(p):return rows[p['front']]['material']
 def _after(p):return rows[p['back']+1]['material']
 def _contact(p):
  for q in parts:
   if q['name']==p['name']:continue
   if q['front']==p['back'] or q['back']==p['front']:return 2*min(p['radius']-p['front_face' if q['back']==p['front'] else 'back_face']['outer_bevel'],q['radius']-q['back_face' if q['back']==p['front'] else 'front_face']['outer_bevel'])
  return None
 ar=[(f['local'],f['zos']) for f in faces if f['role']=='coated']
 cem=[(f['local'],f['zos']) for f in faces if f['role']=='cemented']
 coat_faces='；'.join(f"{f['local']} {f['label']}" for f in faces if f['role']=='coated')
 excl_faces='；'.join(f"{f['local']} {f['label']}不镀膜" for f in faces if f['role']=='cemented')
 d,ms=prepare(page,name,ps,opt['efl_d_mm'][key],coat_faces);origin=z[ps[0]['front']];scale=2.;x0=float(layout.get('x0',108));y0=float(layout.get('y0',204));rmax=max(p['radius'] for p in ps)
 def point(j,r):return (x0+scale*(z[j]+surface_point(m['c'][j],r)-origin),y0+scale*r)
 for part_index,p in enumerate(ps):
  yy,x1,x2=profiles(m,p);xy=np.c_[x0+scale*(np.r_[x1,x2[::-1]]-origin),y0+scale*np.r_[yy,yy[::-1]]];ms.add_lwpolyline(xy,close=True,dxfattribs={'layer':'GLASS'})
  for rv in np.linspace(-p['radius']+.7,p['radius']-.7,13):
   xa=z[p['front']]+float(sag(m,p['front_face'],rv,p['radius']));xb=z[p['back']]+float(sag(m,p['back_face'],rv,p['radius']));mid=(xa+xb)/2;h=min((xb-xa)*.14,.35)
   direction=1 if part_index%2==0 else -1
   line(ms,(x0+scale*(mid-h-origin),y0+scale*(rv-direction*h)),(x0+scale*(mid+h-origin),y0+scale*(rv+direction*h)),'GLASS')
  # cylindrical rim is the explicit ink region; optical/adhesive areas excluded.
  for sign in ([1,-1] if ink['required'] else []):
   rv=sign*p['radius'];a=x0+scale*(z[p['front']]+float(sag(m,p['front_face'],rv,p['radius']))-origin);b=x0+scale*(z[p['back']]+float(sag(m,p['back_face'],rv,p['radius']))-origin)
   line(ms,(a,y0+scale*rv),(b,y0+scale*rv),'BLACKEN')
 a=ps[0]['front'];b=ps[-1]['back'];ct=sum(p['center_thickness'] for p in ps)
 line(ms,(75,y0),(160,y0),'AXIS')
 horizontal_dimension(ms,x0,x0+scale*ct,layout.get('ct_y',153),y0,f'{ct:.3f}±{ct_tol:.3f}')
 vertical_diameter(ms,y0-scale*rmax,y0+scale*rmax,layout.get('diameter_x',181),x0+scale*ct,2*rmax,tol['diameter_upper_mm'],tol['diameter_lower_mm'])
 # Edge thickness referenced at the actual rim, with dimension extension endpoints.
 for k,p in enumerate(ps):
  rv=p['radius'];xf=z[p['front']]+float(sag(m,p['front_face'],rv,rv));xb=z[p['back']]+float(sag(m,p['back_face'],rv,rv))
  horizontal_dimension(ms,x0+scale*(xf-origin),x0+scale*(xb-origin),layout.get('et_y',258)+9*k,y0+scale*rv,f'ET{chr(65+k) if len(ps)>1 else ""} ({xb-xf:.3f})',2.,above=True)
  if len(ps)>1 and k==0:
   label=f'ETA ({xb-xf:.3f})'
   for e in ms.query('TEXT'):
    if e.dxf.text==label:e.set_placement(tuple(layout.get('eta_text',[76,261])),align=TextEntityAlignment.MIDDLE_CENTER)
   line(ms,(layout.get('eta_text',[76,261])[0],layout.get('et_y',258)),(x0+scale*(xf-origin),layout.get('et_y',258)))
 for j,front,anchor,rad in [(a,True,tuple(layout.get('radius_front_anchor',[57,232])),.45*rmax),(b,False,tuple(layout.get('radius_back_anchor',[145,183])),-.4*rmax)]:
  leader(ms,('平面' if rows[j+1]['radius'] is None else f'R{abs(rows[j+1]["radius"]):.3f}'),anchor,point(j,rad),2.6,side='left' if front else 'right')
  nm='S1' if front else ('S2' if len(ps)==1 else 'S3')
  if len(ps)==1 and ((front and not _air(_before(ps[0]))) or ((not front) and not _air(_after(ps[0])))):
   gd=_contact(ps[0]);nm+=' 胶合面不镀膜'
  leader(ms,nm,tuple(layout.get('surface_front_anchor',[76,192])) if front else tuple(layout.get('surface_back_anchor',[150,214])),point(j,-.12*rmax if front else .12*rmax),2.5,side='left' if front else 'right')
  if any(zos_surface==j+1 for _,zos_surface in ar):
   rr=(-1 if front else 1)*min(.72*rmax,.85*ps[0 if front else -1]['front_face' if front else 'back_face']['curve_end']);contact=point(j,rr);slope=m['c'][j]*rr/math.sqrt(1-(m['c'][j]*rr)**2);polished_mark(ms,contact,(-1,slope) if front else (1,-slope),1.8)
 if len(ps)>1:
  j=ps[0]['back'];gd=2*min(ps[0]['radius']-ps[0]['back_face']['outer_bevel'],ps[1]['radius']-ps[1]['front_face']['outer_bevel'])
  leader(ms,('平面' if rows[j+1]['radius'] is None else f'R{abs(rows[j+1]["radius"]):.3f}')+f' 胶合Ø{gd:.2f}',tuple(layout.get('cement_anchor',[142,222.2])),point(j,.3*rmax),2.2,side='right')
  text(ms,'S2 胶合面不镀膜',(142,226.6),2.2)
 # Explicit chamfer leaders, exceptions determined by mechanical recipe.
 for p,side,anchor in [(ps[0],'front_face',tuple(layout.get('chamfer_front_anchor',[55,249]))),(ps[-1],'back_face',tuple(layout.get('chamfer_back_anchor',[145,249])))]:
  f=p[side];rad=p['radius']-f['outer_bevel']/2;j=f['surface'];tip=(x0+scale*(z[j]+float(sag(m,f,rad,p['radius']))-origin),y0+scale*rad)
  if f['outer_bevel']>0:leader(ms,f'{f["outer_bevel"]:.3f}×{f["bevel_angle"]:.0f}°',anchor,tip,2.4,side='left' if side=='front_face' else 'right')
  else:leader(ms,'胶合边不镀膜、无倒角',anchor,tip,2.2,side='left' if side=='front_face' else 'right')
 # Bottom outer rim ink arrow distinct from CT dimension line.
 p=ps[-1];rv=-p['radius'];xfront=z[p['front']]+float(sag(m,p['front_face'],rv,p['radius']));xback=z[p['back']]+float(sag(m,p['back_face'],rv,p['radius']));tip=(x0+scale*((xfront+xback)/2-origin),y0+scale*rv)
 if ink['required']:leader(ms,'外圆涂黑',tuple(layout.get('ink_anchor',[146,164.5])),tip,2.2,side='right')
 for pi,p in enumerate(ps):
  for side in ['front_face','back_face']:
   f=p[side];flat=p['radius']-f['outer_bevel']-f['curve_end']-f['transition']
   if flat>.2:
    rv=-(f['curve_end']+f['transition']+flat/2);j=f['surface'];tip=(x0+scale*(z[j]+float(sag(m,f,rv,p['radius']))-origin),y0+scale*rv)
    base=layout.get('platform_anchor',[57,173]);anchor=(base[0],base[1]-6*pi-4*(0 if side=='front_face' else 1))
    leader(ms,('前平台' if side=='front_face' else '后平台')+('涂黑' if ink['required'] else '')+f' 曲面截止Ø{2*f["curve_end"]:.2f}',anchor,tip,2.,side='left')
 face_rows=[['面号/源面/类型','有效通光直径','机械直径']]
 def _mech(p,which):
  s=f'Ø{2*p["radius"]:.2f}'
  if len(ps)==1 and ((which=='front' and not _air(_before(p))) or (which=='back' and not _air(_after(p)))):
   d=_contact(p)
   if d:s+=f' 胶合Ø{d:.2f}'
  return s
 if len(ps)==1:
  for local,j,which in [(1,a,'front'),(2,b,'back')]:face_rows.append([f'S{local} / ZOS{j+1}',f'D0{local}=Ø{2*m["ca"][j]:.2f}',_mech(ps[0],which)])
 else:
  face_rows += [[f'S1 / ZOS{a+1}',f'D01=Ø{2*m["ca"][a]:.2f}',f'Ø{2*ps[0]["radius"]:.2f}'],[f'S2 / ZOS{ps[0]["back"]+1}',f'Ø{2*m["ca"][ps[0]["back"]]:.2f}',f'Ø{2*ps[0]["radius"]:.2f}/Ø{2*ps[1]["radius"]:.2f}'],[f'S3 / ZOS{b+1}',f'D02=Ø{2*m["ca"][b]:.2f}',f'Ø{2*ps[1]["radius"]:.2f}']]
 for i,f in enumerate(faces,1):face_rows[i][0]+=' '+f['label']
 table(ms,58,layout.get('aperture_table_y',141),[48,43,43],face_rows,5.5,1.75)
 material_rows=[['子片','材料','ΔnD','Δ(nF−nC)']]+[[p['name'].replace('_positive','A').replace('_negative','B'),rows[p['front']+1]['material'],mat['delta_nD'],mat['delta_nF_minus_nC']] for p in ps]
 table(ms,58,layout.get('material_table_y',116),[34,44,25,31],material_rows,5.5,2.)
 text(ms,spec['technical_text']['title'],(15,100),2.5)
 notes=render_notes(spec,kind,faces,ct_tol,[p[side]['outer_bevel'] for p in ps for side in ('front_face','back_face')])
 for k,n in enumerate(notes):text(ms,n,(15,layout.get('notes_y',95)-4.8*k),layout.get('notes_height',1.7))
 if kind=='胶合件':
  efl_p,ffl,bfl=paraxial_focals(rows,ps)
  if abs(efl_p-opt['efl_d_mm'][key])>1e-6:raise ValueError(f'paraxial EFL mismatch {name}: {efl_p} vs {opt["efl_d_mm"][key]}')
  text(ms,f'胶合组 f={efl_p:.3f}mm；前顶点焦距={ffl:+.3f}mm；后顶点焦距={bfl:+.3f}mm；{opt.get("wavelength_nm",587.562):.3f}nm（参考傍轴）',(15,67.2),1.7)
 # Add part identities and overall thickness references for concave substrates.
 if len(ps)>1:
  for k,p in enumerate(ps):
   rv=(.55 if k==0 else -.55)*p['radius']; xx=(z[p['front']]+float(sag(m,p['front_face'],rv,p['radius']))+z[p['back']]+float(sag(m,p['back_face'],rv,p['radius'])))/2
   leader(ms,'件'+str(k+1)+' '+p['name'].replace('_positive','A').replace('_negative','B'),(63,240-60*k),(x0+scale*(xx-origin),y0+scale*rv),2.,side='left')
 else:
  p=ps[0]
  if m['c'][p['front']]<0 or m['c'][p['back']]>0:
   yy,lf,rt=profiles(m,p); span=float(rt.max()-lf.min())
   text(ms,f'总厚参考 ({span:.3f})',(155,146),2.,True)
 if len(ps)>1:
  for k,(p,side) in enumerate([(ps[0],'back_face'),(ps[1],'front_face')]):
   f=p[side];rr=p['radius']-f['outer_bevel']/2;yy=rr if k==0 else -rr
   xx=z[f['surface']]+float(sag(m,f,yy,p['radius']))
   leader(ms,f'胶合边{f["outer_bevel"]:.3f}×{f["bevel_angle"]:.0f}°',(145,266 if k==0 else 157),(x0+scale*(xx-origin),y0+scale*yy),2.,side='right')
  # Adhesive requirement is defined once in the technical requirements block.
 # Fields must never contain placeholders; signed name cells intentionally blank for manual signatures.

 return d,dict(id=name,parts=[p["name"] for p in ps],ct=ct,diameter=2*rmax)
