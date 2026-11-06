"""Reusable house-style vectors, not claims of standards compliance.
Insertion units are paper mm. Arrow points at local origin toward local -X.
"""
import math

def ensure(doc):
    if 'OMD_ARROW' not in doc.blocks:
        b=doc.blocks.new('OMD_ARROW')
        b.add_solid([(0,0),(1,.25),(1,-.25)],dxfattribs={'layer':'0'})
    if 'OMD_POLISHED_CROSS' not in doc.blocks:
        b=doc.blocks.new('OMD_POLISHED_CROSS')
        b.add_circle((0,0),1,dxfattribs={'layer':'0'})
        b.add_line((-1,0),(1,0),dxfattribs={'layer':'0'})
        b.add_line((0,-1),(0,1),dxfattribs={'layer':'0'})

def arrow_block(ms,tip,tail,size=2):
    ensure(ms.doc)
    angle=math.degrees(math.atan2(tail[1]-tip[1],tail[0]-tip[0]))
    return ms.add_blockref('OMD_ARROW',tip,dxfattribs={'xscale':size,'yscale':size,'rotation':angle,'layer':'ANNOTATION'})

def polished_block(ms,center,radius):
    ensure(ms.doc)
    return ms.add_blockref('OMD_POLISHED_CROSS',center,dxfattribs={'xscale':radius,'yscale':radius,'layer':'POLISHED_MARK'})

if __name__=='__main__':
    import argparse,ezdxf
    from pathlib import Path
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args()
    d=ezdxf.new('R2010');d.units=4;ensure(d)
    for layer in ['ANNOTATION','POLISHED_MARK']:d.layers.new(layer)
    arrow_block(d.modelspace(),(5,5),(8,5));polished_block(d.modelspace(),(15,5),2)
    a.out.parent.mkdir(parents=True,exist_ok=True);d.saveas(a.out)
