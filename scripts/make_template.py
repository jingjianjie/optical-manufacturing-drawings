"""Generate the package's original generic A4 frame. No historical CAD is read."""
import argparse
from pathlib import Path
import ezdxf

def create(path):
    d=ezdxf.new('R2010');d.units=4;m=d.modelspace()
    # Labels and grid positions are the renderer's public paper-mm interface.
    d.styles.new('TemplateChinese',dxfattribs={'font':''})
    def line(a,b):m.add_line(a,b)
    def label(s,x,y,h=2.2):
        m.add_mtext(s,dxfattribs={'insert':(x,y),'char_height':h,'attachment_point':5,'style':'TemplateChinese','width':38})
    m.add_lwpolyline([(0,0),(210,0),(210,297),(0,297)],close=True)
    m.add_lwpolyline([(10,10),(200,10),(200,287),(10,287)],close=True)
    # Specification table; values placed separately by renderer.
    for x in [10,30,50]:line((x,185),(x,287))
    for y in range(185,288,6):line((10,y),(50,y))
    labels=['材料要求','ΔnD','Δ(nF−nC)','光学均匀性','应力双折射','光吸收系数','条纹度','气泡度','表面要求','N','ΔN','ΔR','B','C','D01','D02','f']
    for s,y in zip(labels,range(284,187,-6)):label(s,20,y,1.8 if len(s)>4 else 2.2)
    # A deliberately simple original title block, compatible with documented fill areas.
    for y in [10,15.5,21,26.5,32,37.5,43,59,65]:line((10,y),(200 if y in [10,32,37.5,59,65] else 80,y))
    for x in [30,48,64,80,100,140,170,185]:
        line((x,10),(x,59 if x in [30,48,64,80,140] else 32 if x==100 else 37.5))
    line((80,43),(200,43));line((140,37.5),(200,37.5));line((140,26.5),(200,26.5))
    for s,x,y in [('镀膜',20,62),('名称',90,55),('图号',150,55),('材料',90,24),('数量',90,13),('比例',192,40),('阶段',155,40),('重量',177,40),('共 张',154,29.5),('第 张',184,29.5),('设计',20,29),('制图',20,24),('审核',20,18.5),('工艺',20,13),('标准化',56,29),('批准',56,18.5),('日期',56,13),('更改记录',43,40)]:label(s,x,y)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);d.saveas(path)
    return path

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out',type=Path);a=ap.parse_args();print(create(a.out))
