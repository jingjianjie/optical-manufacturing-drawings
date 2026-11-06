"""DXF to vector A4 PDF using Matplotlib; proof rendered from final PDF by PDFium."""
from pathlib import Path
import ezdxf
from ezdxf.addons.drawing import Frontend,RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration,ColorPolicy,BackgroundPolicy

def export_one(dxf_path,pdf_path,proof_path):
 import matplotlib
 matplotlib.use("Agg")
 import matplotlib.pyplot as plt
 from pypdf import PdfReader
 import pypdfium2 as pdfium
 doc=ezdxf.readfile(dxf_path)
 fig=plt.figure(figsize=(210/25.4,297/25.4));ax=fig.add_axes([0,0,1,1])
 try:
  backend=MatplotlibBackend(ax)
  Frontend(RenderContext(doc),backend,config=Configuration(color_policy=ColorPolicy.BLACK,background_policy=BackgroundPolicy.WHITE)).draw_layout(doc.modelspace(),finalize=True)
  fig.set_size_inches(210/25.4,297/25.4,forward=True);ax.set_position([0,0,1,1])
  ax.set_xlim(0,210);ax.set_ylim(0,297);ax.set_aspect("equal");ax.set_axis_off()
  # Tiny glyph counters must survive vector PDF export (Ø, 0, 8 etc.).
  for patch in ax.patches:
   if patch.get_fill() and patch.get_facecolor()[3]>0:patch.set_linewidth(0)
  fig.savefig(pdf_path,format="pdf",bbox_inches=None,pad_inches=0,facecolor="white",metadata={"Creator":"optical-manufacturing-drawings"})
 finally:plt.close(fig)
 reader=PdfReader(str(pdf_path));page=reader.pages[0];size=[float(page.mediabox.width)*25.4/72,float(page.mediabox.height)*25.4/72]
 if max(abs(size[0]-210),abs(size[1]-297))>.001:raise ValueError("PDF paper size mismatch")
 pdf=pdfium.PdfDocument(str(pdf_path))
 try:
  pg=pdf[0]
  try:
   bitmap=pg.render(scale=1.5)
   try:bitmap.to_pil().save(str(proof_path))
   finally:bitmap.close()
  finally:pg.close()
 finally:pdf.close()
 return {"paper_mm":size,"text":"vector geometry; editable text retained in DXF","backend":"matplotlib+pypdfium2"}
