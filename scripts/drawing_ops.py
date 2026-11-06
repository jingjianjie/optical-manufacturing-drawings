"""Reusable DXF micro-operations. Coordinates and heights are paper mm.
No model-space scaling is hidden: caller transforms real part points explicitly.
"""
import math
from ezdxf.enums import TextEntityAlignment
from symbol_blocks import arrow_block,polished_block

def dimension_value(value,diameter=False,reference=False):
 s=f'{value:.2f}' if diameter else f'{value:.3f}'
 return '('+s+')' if reference else ('Ø'+s if diameter else s)

def text(ms,value,point,height=2.5,center=False,rotation=0,layer='ANNOTATION'):
 e=ms.add_text(value,dxfattribs={'height':height,'style':'CN','layer':layer,'rotation':rotation})
 if center:e.set_placement(point,align=TextEntityAlignment.MIDDLE_CENTER)
 else:e.dxf.insert=point
 return e

def line(ms,a,b,layer='ANNOTATION'):
 return ms.add_line(a,b,dxfattribs={'layer':layer})

def arrow(ms,tip,tail,size=2.):
 return arrow_block(ms,tip,tail,size)

def leader(ms,label,anchor,tip,height=2.5,side='left'):
 e=text(ms,label,anchor,height)
 from ezdxf import bbox
 bounds=bbox.extents([e])
 # Measured glyph bounds replace len()*0.42; the diagonal begins outside text.
 end=(max(anchor[0],bounds.extmax.x)+1,anchor[1]-1)
 start=(anchor[0],anchor[1]-1);line(ms,start,end)
 joint=end if side=='left' else start
 line(ms,joint,tip);arrow(ms,tip,joint)

def polished_mark(ms,contact,normal,radius=2.):
 """User's historical single circle + orthogonal cross, tangent at supplied point.
 This is a house-style graphic; do not claim an unverified standards meaning.
 """
 n=math.hypot(*normal);cx=contact[0]+radius*normal[0]/n;cy=contact[1]+radius*normal[1]/n
 return polished_block(ms,(cx,cy),radius)

def horizontal_dimension(ms,x1,x2,y,attach_y,label,height=2.5,above=False):
 for x in (x1,x2):line(ms,(x,attach_y),(x,y-1))
 line(ms,(x1,y),(x2,y))
 if abs(x2-x1)<9:
  line(ms,(x1-4,y),(x2+4,y));arrow(ms,(x1,y),(x1-4,y));arrow(ms,(x2,y),(x2+4,y))
 else:arrow(ms,(x1,y),(x2,y));arrow(ms,(x2,y),(x1,y))
 if above:
  # Place above extension-line endpoints; narrow spans cannot fit the text between them.
  text(ms,label,((x1+x2)/2,y+3),height,True)
 else:text(ms,label,((x1+x2)/2,y-3),height,True)

def vertical_diameter(ms,y1,y2,x,attach_x,value,upper=0.,lower=-.02):
 for y in (y1,y2):line(ms,(attach_x,y),(x+1,y))
 line(ms,(x,y1),(x,y2));arrow(ms,(x,y1),(x,y2));arrow(ms,(x,y2),(x,y1))
 # Stacked deviations are separate real TEXT objects with rotation and explicit offsets.
 mid=(y1+y2)/2;text(ms,f'Ø{value:.2f}',(x+3,mid),2.7,True,90)
 def dev(v):return '0.00' if v==0 else f'{v:+.2f}'.replace('-','−')
 text(ms,dev(upper),(x+1.2,mid+11),1.8,True,90);text(ms,dev(lower),(x+3.4,mid+11),1.8,True,90)

def center_thickness_tolerance(tol,ct,single=True):
 """Thin rule is based on substrate CT, never ET or cemented total thickness."""
 if single and ct<=tol.get('thin_center_thickness_max_mm',-1):
  return tol['thin_center_thickness_mm']
 return tol['center_thickness_mm']

def wrapped_text(ms,value,point,width,height=2.,line_spacing=1.5):
 """Font-aware line wrapping in paper mm, with measurable TEXT output."""
 from ezdxf.tools.text_size import text_size
 probe=ms.add_text('',dxfattribs={'height':height,'style':'CN'})
 lines=[];part=''
 try:
  for c in value:
   probe.dxf.text=part+c
   if c=='\n' or (part and text_size(probe).width>width):lines.append(part);part='' if c=='\n' else c
   else:part+=c
  if part:lines.append(part)
 finally:ms.delete_entity(probe)
 return [text(ms,s,(point[0],point[1]-i*height*line_spacing),height) for i,s in enumerate(lines)]

def surface_point(curvature,radius):
 return 0. if curvature==0 else curvature*radius*radius/(1+math.sqrt(1-(curvature*radius)**2))

def table(ms,x,y,widths,rows,row_height=5.5,text_height=2.1):
 xs=[x]
 for w in widths:xs.append(xs[-1]+w)
 for xx in xs:line(ms,(xx,y),(xx,y-len(rows)*row_height),'TABLE')
 for k in range(len(rows)+1):line(ms,(x,y-k*row_height),(xs[-1],y-k*row_height),'TABLE')
 for r,row in enumerate(rows):
  for c,value in enumerate(row):text(ms,str(value),((xs[c]+xs[c+1])/2,y-(r+.5)*row_height),text_height,True,layer='TABLE')
