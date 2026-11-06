"""Generic A4 example-style renderer; project adoption required.
Supports centered spherical singlets and cemented doublets only.
Each call returns one DXF document. No API connection or output side effects.
"""
import math
import numpy as np
import ezdxf
from drawing_ops import *
from profile_geometry import profiles,sag

def render_page(snapshot,item,template,layout,title,drawing_prefix,page,page_count,spec,font_name=None):
 if not font_name:raise ValueError('Provide a registered font filename')
 rows=snapshot['surfaces'];surfs=rows[1:]
 m=dict(c=np.array([0 if s['radius'] is None else 1/s['radius'] for s in surfs]),t=np.array([s['thickness'] or 0 for s in surfs]),ca=np.array([s['ca'] for s in surfs]))
 parts=snapshot['mechanical']['parts'];z=np.r_[0,np.cumsum(m['t'][:-1])]
 opt=snapshot['material_optics'];name=item['id'];inds=item['parts'];key=item['efl_key']
 tol=spec['tolerances'];mat=spec['material_requirements'];surf=spec['surface_requirements'];coat=spec['coating'];ink=spec['blackening'];bevel=spec['chamfer']
 coat_text=f'{coat["metric"]}{coat["comparison"]}{coat["reflectance_percent"]:g}%，{coat["band_nm"][0]}–{coat["band_nm"][1]}nm'
 def prepare(page,name,ps,efl,coat_faces):
  d=ezdxf.readfile(template);d.units=4;d.styles.new('CN',dxfattribs={'font':font_name})
  for layer in ['ANNOTATION','POLISHED_MARK','TABLE','GLASS','AXIS','BLACKEN']:d.layers.new(layer,dxfattribs={'color':7})
  ms=d.modelspace()
  for e in list(ms.query('MTEXT')):
   if 80<float(e.dxf.insert.y)<120:ms.delete_entity(e);continue
   e.dxf.style='CN'
   if float(e.dxf.insert.y)<65:e.dxf.char_height=2.;e.dxf.width=9 if e.plain_text().strip() in ['标记','处数'] else e.dxf.width
   if e.plain_text().replace(' ','').startswith('共') and '张' in e.plain_text():e.text=f'共 {page_count} 张'
   if e.plain_text().replace(' ','').startswith('第') and '张' in e.plain_text():e.text=f'第 {page} 张'
  values=[mat['delta_nD'],mat['delta_nF_minus_nC'],mat['homogeneity'],mat['birefringence'],mat['absorption'],mat['striae'],mat['bubbles'],str(surf['N']),str(surf['delta_N']),surf['delta_R'],surf['scratch_dig'],surf['optical_decenter_arcmin']+'′',f'Ø{2*m["ca"][ps[0]["front"]]:.2f}',f'Ø{2*m["ca"][ps[-1]["back"]]:.2f}',f'{efl:.3f}']
  for yy,value in zip([278,272,266,260,254,248,242,230,224,218,212,206,200,194,188],values):text(ms,value,(40,yy),2.,True)
  text(ms,title+' / 名义尺寸；单位mm',(122,280),2.8,True)
  text(ms,name,(110,50),3.2,True);text(ms,f'{drawing_prefix}-{page:02}',(170,51),2.5,True)
  for k,p in enumerate(ps):
   rr=rows[p['front']+1];line=rr['material'];cat=(rr.get('catalog') or '').replace('.AGF','');nd=rr.get('nd');vd=rr.get('vd')
   if spec.get('title_material_details',False):
    if cat:line+=f'/{cat}'
    if nd is not None:line+=f' nd{nd:.4f}'
    if vd is not None:line+=f' Vd{vd:.3f}'
   text(ms,line,(120,26-5*k),1.7,True)
  text(ms,'1件/套',(120,12.5),2.,True);text(ms,'设计图',(155,35),2.,True);text(ms,'—',(177,35),2.,True);text(ms,'2:1',(192,35),2.2,True)
  text(ms,f'焦距波长：{opt.get("wavelength_nm",587.5618):.3f}nm',(170,21),2.,True);text(ms,'签署栏留供人工签署',(170,14),1.8,True)
  text(ms,'外露面AR：'+coat_text+'；'+coat_faces,(114,61.8),1.75,True)
  return d,ms
 ps=[parts[i] for i in inds]
 nominal_ct=sum(p['center_thickness'] for p in ps)
 ct_tol=center_thickness_tolerance(tol,nominal_ct,len(ps)==1)
 explicit=item.get('spec_overrides',{}).get('tolerances',{})
 if 'center_thickness_mm' in explicit:ct_tol=explicit['center_thickness_mm']
 def _air(s):return not (s or '').strip()
 def _before(p):return rows[p['front']]['material']
 def _after(p):return rows[p['back']+1]['material']
 def _contact(p):
  for q in parts:
   if q['name']==p['name']:continue
   if q['front']==p['back'] or q['back']==p['front']:return min(2*p['radius'],2*q['radius'])
  return None
 ar=[];cem=[]
 if len(ps)==1:
  if _air(_before(ps[0])):ar.append(('S1',ps[0]['front']+1))
  else:cem.append(('S1',ps[0]['front']+1))
  if _air(_after(ps[0])):ar.append(('S2',ps[0]['back']+1))
  else:cem.append(('S2',ps[0]['back']+1))
 else:
  if _air(_before(ps[0])):ar.append(('S1',ps[0]['front']+1))
  cem.append(('S2',ps[0]['back']+1))
  if _air(_after(ps[-1])):ar.append(('S3',ps[-1]['back']+1))
 ar_txt='、'.join(f'{l}(ZOS{z})' for l,z in ar) or '无'
 cem_txt='、'.join(f'{l}(ZOS{z}，胶合)' for l,z in cem) or '无'
 coat_faces=f'AR面 {ar_txt}；不镀：{cem_txt}'
 d,ms=prepare(page,name,ps,opt['efl_d_mm'][key],coat_faces);origin=z[ps[0]['front']];scale=2.;x0=float(layout.get('x0',108));y0=float(layout.get('y0',204));rmax=max(p['radius'] for p in ps)
 def point(j,r):return (x0+scale*(z[j]+surface_point(m['c'][j],r)-origin),y0+scale*r)
 for p in ps:
  yy,x1,x2=profiles(m,p);xy=np.c_[x0+scale*(np.r_[x1,x2[::-1]]-origin),y0+scale*np.r_[yy,yy[::-1]]];ms.add_lwpolyline(xy,close=True,dxfattribs={'layer':'GLASS'})
  for rv in np.linspace(-p['radius']+.7,p['radius']-.7,13):
   xa=z[p['front']]+float(sag(m,p['front_face'],rv,p['radius']));xb=z[p['back']]+float(sag(m,p['back_face'],rv,p['radius']));mid=(xa+xb)/2;h=min((xb-xa)*.14,.35)
   line(ms,(x0+scale*(mid-h-origin),y0+scale*(rv-h)),(x0+scale*(mid+h-origin),y0+scale*(rv+h)),'GLASS')
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
  leader(ms,'平面' if rows[j+1]['radius'] is None else f'R{abs(rows[j+1]["radius"]):.3f}',anchor,point(j,rad),2.6,side='left' if front else 'right')
  nm='S1' if front else ('S2' if len(ps)==1 else 'S3')
  if len(ps)==1 and ((front and not _air(_before(ps[0]))) or ((not front) and not _air(_after(ps[0])))):
   gd=_contact(ps[0]);nm+=' 胶合'+(f' Ø{gd:.2f}' if gd else '')
  leader(ms,nm,tuple(layout.get('surface_front_anchor',[76,192])) if front else tuple(layout.get('surface_back_anchor',[154,214])),point(j,-.12*rmax if front else .12*rmax),2.5,side='left' if front else 'right')
  rr=-.72*rmax if front else .72*rmax;contact=point(j,rr);slope=m['c'][j]*rr/math.sqrt(1-(m['c'][j]*rr)**2);polished_mark(ms,contact,(-1,slope) if front else (1,-slope),1.8)
 if len(ps)>1:
  j=ps[0]['back'];gd=min(2*p['radius'] for p in ps);rlabel='平面' if rows[j+1]['radius'] is None else f'R{abs(rows[j+1]["radius"]):.3f}';leader(ms,f'S2 胶合 {rlabel} Ø{gd:.2f}',tuple(layout.get('cement_anchor',[145,223])),point(j,.3*rmax),2.2,side='right')
 # Explicit chamfer leaders, exceptions determined by mechanical recipe.
 for p,side,anchor in [(ps[0],'front_face',tuple(layout.get('chamfer_front_anchor',[55,249]))),(ps[-1],'back_face',tuple(layout.get('chamfer_back_anchor',[145,249])))]:
  f=p[side];rad=p['radius']-f['outer_bevel']/2;j=f['surface'];tip=(x0+scale*(z[j]+float(sag(m,f,rad,p['radius']))-origin),y0+scale*rad)
  if f['outer_bevel']>0:leader(ms,f'{f["outer_bevel"]:.3f}×{f["bevel_angle"]:.0f}°',anchor,tip,2.4,side='left' if side=='front_face' else 'right')
  else:leader(ms,'无倒角（胶合边）',anchor,tip,2.2,side='left' if side=='front_face' else 'right')
 # Bottom outer rim ink arrow distinct from CT dimension line.
 p=ps[-1];rv=-p['radius'];xfront=z[p['front']]+float(sag(m,p['front_face'],rv,p['radius']));xback=z[p['back']]+float(sag(m,p['back_face'],rv,p['radius']));tip=(x0+scale*((xfront+xback)/2-origin),y0+scale*rv)
 if ink['required']:leader(ms,'外圆涂黑',tuple(layout.get('ink_anchor',[146,162])),tip,2.2,side='right')
 for pi,p in enumerate(ps):
  for side in ['front_face','back_face']:
   f=p[side];flat=p['radius']-f['outer_bevel']-f['curve_end']-f['transition']
   if flat>.2 and ink['required']:
    rv=-(f['curve_end']+f['transition']+flat/2);j=f['surface'];tip=(x0+scale*(z[j]+float(sag(m,f,rv,p['radius']))-origin),y0+scale*rv)
    base=layout.get('platform_anchor',[57,173]);anchor=(base[0],base[1]-6*pi-4*(0 if side=='front_face' else 1))
    leader(ms,'前平台涂黑' if side=='front_face' else '后平台涂黑',anchor,tip,2.,side='left')
 face_rows=[['面号/源面','有效通光直径','机械直径']]
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
 table(ms,58,layout.get('aperture_table_y',141),[43,48,43],face_rows,5.5,2.)
 material_rows=[['子片','材料','ΔnD','Δ(nF−nC)']]+[[p['name'].replace('_positive','A').replace('_negative','B'),rows[p['front']+1]['material'],mat['delta_nD'],mat['delta_nF_minus_nC']] for p in ps]
 table(ms,58,layout.get('material_table_y',116),[34,44,25,31],material_rows,5.5,2.)
 notes=[f'1. 除抛光面外细磨；圆十字为本例约定抛光面标记。N={surf["N"]}，ΔN={surf["delta_N"]}，{surf["scratch_dig"]}，偏心{surf["optical_decenter_arcmin"]}′。',
        '2. 外露光学面AR：'+coat_text+'；'+coat_faces+'。',
        (f'3. 箭头所指非通光周边/平台涂黑；胶合后涂，漆厚{ink["thickness_mm"]:.3f}mm，图示成品尺寸。' if ink['required'] else '3. 本项目不要求周边涂黑；光学面与胶合区域保持清洁。'),
        '4. 通光/胶合区遮蔽；墨料及胶料按供方受控光学工艺，禁止污染与侵入有效径。',
        f'5. 未注线性±{tol["unindicated_linear_mm"]:.3f}mm、角度±{tol["angle_deg"]:g}°；CT±{ct_tol:.3f}mm；默认倒角{bevel["radial_mm"]:.3f}×{bevel["angle_deg"]:g}°，标注例外优先。',
        '6. 提供R、CT、焦距、面形检测数据；括号ET为参考；平台由母曲率/截止径控制。镀膜波段为制造要求，光学设计波段见系统附页。']
 for k,n in enumerate(notes):text(ms,n,(15,layout.get('notes_y',95)-4.8*k),layout.get('notes_height',1.75))
 # Fields must never contain placeholders; signed name cells intentionally blank for manual signatures.

 return d,dict(id=name,parts=[p["name"] for p in ps],ct=ct,diameter=2*rmax)
