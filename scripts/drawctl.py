"""Incremental drawing CLI. Run --help; all paths are relative to project.json.
No automatic optical optimization, installation, API connection or fabricated reviews.
"""
import argparse,copy,hashlib,json,math,shutil,time,zipfile
from font_support import resolve_font, register_font
from pathlib import Path

HERE=Path(__file__).resolve().parent
SKILL=HERE.parent
LAYOUT_KEYS={'radius_front_anchor','radius_back_anchor','surface_front_anchor','surface_back_anchor','cement_anchor','chamfer_front_anchor','chamfer_back_anchor','ink_anchor','platform_anchor','eta_text','ct_y','et_y','diameter_x','aperture_table_y','material_table_y','notes_y','notes_height','x0','y0'}

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=True).encode()).hexdigest()
def safe_id(value):
 if not value or Path(value).name!=value or any(c in value for c in '/\\:'):raise ValueError('page id must be a plain filename stem')
 return value
def artifact_paths(root,pid):return [root/'dxf'/f'{pid}.dxf',root/'preview'/f'{pid}.png']
def engine_hash(names):return digest({n:sha(HERE/n) for n in sorted(set(names)|{'drawctl.py','symbol_blocks.py','font_support.py'})})

def initialize(source,target,title=None,font_file=None,defaults=None):
 source=source.resolve();target=target.resolve()
 if (target/'project.json').exists():raise FileExistsError('project already exists; do not re-import over current edits')
 data=source/'data';snapshot={'surfaces':read(data/'api_surfaces.json'),'mechanical':read(data/'mechanical.json'),'material_optics':read(data/'material_optics.json')}
 manifests=read(data/'drawing_manifest.json');source_files=list((source/'source').glob('*_source.zos'))
 if (source/'SYNTHETIC_EXAMPLE.json').is_file():source_files=[source/'source/synthetic_source.json']
 if len(source_files)!=1:raise ValueError('archive needs one *_source.zos; specify a clean archive')
 proof=read(source/'review/main_direct_api.json')
 if proof['source_sha256']!=sha(source_files[0]):raise ValueError('source ZOS does not match archived direct API evidence')
 for s in snapshot['surfaces']:
  p=next(x for x in proof['surfaces'] if x['surface']==s['surface'])
  for k in ['radius','thickness','material','ca','mechanical','chip','stop']:
   v=s[k];v=None if isinstance(v,float) and not math.isfinite(v) else v
   if p[k]!=v:raise ValueError(f'API archive mismatch at surface {s["surface"]}, {k}')
 for folder in ['inputs','dxf','preview','proof_pdf','pdf','review','evidence']:(target/folder).mkdir(parents=True,exist_ok=True)
 write(target/'inputs/snapshot.json',snapshot)
 source_name='source.json' if source_files[0].suffix=='.json' else 'source.zos'
 shutil.copy2(source_files[0],target/'inputs'/source_name)
 shutil.copy2(SKILL/'assets/a4-frame/generic-a4.dxf',target/'inputs/template.dxf')
 shutil.copy2(source/'review/main_direct_api.json',target/'evidence/source_api.json')
 # Explicit evidence list; no later directory glob can accidentally include stale pages.
 evidence=[]
 for p in sorted((source/'native').glob('*'))+sorted((source/'source').glob('*layout.png')):
  if p.is_file() and p.suffix.lower() in ['.step','.png']:
   dest=target/'evidence'/p.name;shutil.copy2(p,dest);evidence.append(str(dest.relative_to(target)))
 attachments=[]
 for p in sorted((source/'dxf').glob('90_appendix*.dxf')):
  dest=target/'inputs'/p.name;shutil.copy2(p,dest);attachments.append({'id':p.stem,'path':str(dest.relative_to(target))})
 names=[p['name'] for p in snapshot['mechanical']['parts']];items=[]
 for e in manifests:
  inds=[names.index(n) for n in e['parts']];key=e.get('efl_key') or (e['parts'][0] if len(inds)==1 else e['parts'][0].split('_')[0])
  if key not in snapshot['material_optics']['efl_d_mm']:raise ValueError('missing focal length '+key)
  items.append({'id':safe_id(e['id']),'parts':inds,'efl_key':key,'layout':e.get('layout',{}),'spec_overrides':{}})
 font_source=resolve_font(font_file)
 font=target/'local-fonts'/font_source.name;font.parent.mkdir(exist_ok=True);shutil.copy2(font_source,font)
 cfg={'schema':1,'title':title or source_files[0].stem.removesuffix('_source'),'drawing_prefix':(title or source_files[0].stem.removesuffix('_source'))+'-MFG','font_name':font.name,'font_file':font.relative_to(target).as_posix(),'dpi':180,'source':'inputs/'+source_name,'synthetic_example':source_name=='source.json','snapshot':'inputs/snapshot.json','template':'inputs/template.dxf','source_sha256':sha(target/'inputs'/source_name),'snapshot_sha256':sha(target/'inputs/snapshot.json'),'evidence':[{'path':n,'sha256':sha(target/n)} for n in evidence], 'attachments':[dict(e,sha256=sha(target/e['path'])) for e in attachments], 'spec':read(defaults or SKILL/'assets/drawing-defaults.json'),'pages':items,'session_defaults_question':{'status':'not_recorded','source':'Record actual current-user confirmation or an explicit inherited confirmation; init does not assert approval'}}
 write(target/'project.json',cfg);return {'project':str(target/'project.json'),'pages':len(items),'attachments':len(attachments)}

def merge(a,b):
 result=copy.deepcopy(a)
 for k,v in b.items():result[k]=merge(result.get(k,{}),v) if isinstance(v,dict) else v
 return result

def load_project(path):
 path=Path(path).resolve();root=path.parent;cfg=read(path)
 if cfg['schema']!=1:raise ValueError('unsupported project schema')
 if sha(root/cfg['source'])!=cfg['source_sha256']:raise ValueError('source ZOS changed: refresh direct API/native CAD/optical evidence into a NEW frozen archive first')
 if sha(root/cfg['snapshot'])!=cfg['snapshot_sha256']:raise ValueError('frozen API/mechanical snapshot changed: import a newly verified archive, do not reuse old proof')
 ids=[safe_id(e['id']) for e in cfg['pages']+cfg['attachments']]
 if len(ids)!=len(set(ids)):raise ValueError('duplicate page ids')
 for a in cfg['attachments']+cfg['evidence']:
  if sha(root/a['path'])!=a['sha256']:raise ValueError('frozen evidence/appendix changed: '+a['path'])
 register_font(root/cfg['font_file'])
 for e in cfg['pages']:
  if set(e['layout'])-LAYOUT_KEYS:raise ValueError('unknown layout key')
 return root,cfg,read(root/cfg['snapshot'])

def page_signature(root,cfg,snapshot,item,index):
 parts=[snapshot['mechanical']['parts'][j] for j in item['parts']]
 # R/t/CA subset only. Absolute placement cancels for individual part drawings.
 first=min(p['front'] for p in parts)+1;last=max(p['back'] for p in parts)+1
 surfaces=copy.deepcopy(snapshot['surfaces'][first:last+1]);surfaces[-1]['thickness']=0
 return digest({'surface_subset':surfaces,'parts':parts,'efl':snapshot['material_optics']['efl_d_mm'][item['efl_key']], 'item':item,'spec':merge(cfg['spec'],item['spec_overrides']),'page':index,'count':len(cfg['pages']),'title':cfg['title'],'prefix':cfg['drawing_prefix'],'template':sha(root/cfg['template']),'font':sha(root/cfg['font_file']),'font_name':cfg['font_name'],'dpi':cfg['dpi'],'engine':engine_hash(['page_renderer.py','profile_geometry.py','drawing_ops.py'])})

def plan(path):
 root,cfg,snapshot=load_project(path);state=read(root/'build-state.json') if (root/'build-state.json').exists() else {'pages':{}}
 result=[]
 for i,item in enumerate(cfg['pages'],1):
  sig=page_signature(root,cfg,snapshot,item,i);old=state['pages'].get(item['id'],{});outputs=artifact_paths(root,item['id'])
  reason='unchanged'
  if old.get('input')!=sig:reason='input_or_renderer_changed'
  elif any(not p.exists() or old.get('outputs',{}).get(p.name)!=sha(p) for p in outputs):reason='output_missing_or_edited'
  result.append({'id':item['id'],'input':sig,'dirty':reason!='unchanged','reason':reason})
 return root,cfg,snapshot,state,result

def check_doc(doc,font_file):
 from fontTools.ttLib import TTCollection,TTFont
 content='\n'.join(e.plain_text() for e in doc.modelspace() if e.dxftype() in ['TEXT','MTEXT'])
 if any(t in content for t in ['待定','TBD','见面表']):raise ValueError('unresolved placeholder in output')
 audit=doc.audit()
 if audit.errors:raise ValueError('DXF audit errors')
 font=TTCollection(font_file).fonts[0] if Path(font_file).suffix.lower()=='.ttc' else TTFont(font_file)
 missing=sorted({c for c in content if not c.isspace() and ord(c) not in font.getBestCmap()});font.close()
 if missing:raise ValueError('missing font glyphs: '+repr(missing))

def build(path,pages=None):
 started=time.perf_counter();root,cfg,snapshot,state,planned=plan(path)
 chosen=set(pages or [e['id'] for e in planned]);unknown=chosen-{e['id'] for e in planned}
 if unknown:raise ValueError('unknown pages '+repr(unknown))
 dirty=[e for e in planned if e['dirty'] and e['id'] in chosen];timings=[]
 if dirty:
  import ezdxf
  from ezdxf.addons.drawing import matplotlib as dm
  from page_renderer import render_page
  for entry in dirty:
   t=time.perf_counter();idx=next(i for i,e in enumerate(cfg['pages']) if e['id']==entry['id']);item=cfg['pages'][idx]
   doc,meta=render_page(snapshot,item,root/cfg['template'],item['layout'],cfg['title'],cfg['drawing_prefix'],idx+1,len(cfg['pages']),merge(cfg['spec'],item['spec_overrides']),cfg['font_name'])
   dxf,png=artifact_paths(root,item['id']);doc.saveas(dxf);back=ezdxf.readfile(dxf);check_doc(back,root/cfg['font_file'])
   dm.qsave(back.modelspace(),png,bg='#FFFFFF',dpi=cfg['dpi'])
   state['pages'][item['id']]={'input':entry['input'],'outputs':{p.name:sha(p) for p in [dxf,png]},'metadata':meta}
   write(root/'build-state.json',state);timings.append({'id':item['id'],'seconds':round(time.perf_counter()-t,3)})
 report={'operation':'build','seconds':round(time.perf_counter()-started,3),'rebuilt':timings,'skipped':[e['id'] for e in planned if e['id'] not in {d['id'] for d in dirty}],'still_dirty':[e['id'] for e in plan(path)[-1] if e['dirty']]}
 write(root/'last-build.json',report);return report

def fresh_pages(path):
 root,cfg,snapshot,state,planned=plan(path)
 stale=[e['id'] for e in planned if e['dirty']]
 if stale:raise ValueError('build stale pages first: '+','.join(stale))
 return root,cfg,state

def packet(path,pages=None):
 root,cfg,state=fresh_pages(path);ids=pages or [e['id'] for e in cfg['pages']]
 if set(ids)-set(state['pages']):raise ValueError('unknown page id')
 request={'source_sha256':cfg['source_sha256'],'snapshot_sha256':cfg['snapshot_sha256'],'pages':[{'id':p,'dxf':str((root/'dxf'/f'{p}.dxf').resolve()),'preview':str((root/'preview'/f'{p}.png').resolve()),'sha256':state['pages'][p]['outputs'][f'{p}.dxf']} for p in ids],'evidence':cfg['evidence'],'scope':'Explicit current review scope; source and geometry evidence identified separately','reviewers_required':2}
 request['scope']='layout/spec change on frozen geometry; inherit same-source API/STEP evidence; inspect changed pages independently'
 for p in request['pages']:
  p['preview_sha256']=state['pages'][p['id']]['outputs'][p['id']+'.png'];p['input_signature']=state['pages'][p['id']]['input']
 write(root/'review/request.json',request)
 message='只读独立复核。实际查看以下每张PNG与对应DXF标注，检查引线、文字、公差与遮挡。源模型和机械快照未变；同版API/STEP证据在evidence，不需因布局修改重跑光学。若本次是首次完整图纸验收仍须各自直接API读取，不能把缓存当作独立API。不得读取另一位结论。返回逐页事实、问题与所见文件哈希。只读代理不写报告、不建文件锁，由主线程保存。\n'+json.dumps(request,ensure_ascii=False,indent=2)
 for name in ['A','B']:(root/'review'/f'prompt_{name}.txt').write_text(message,encoding='utf-8')
 return request

def record_review(path,reviewer,report,pages):
 root,cfg,state=fresh_pages(path);report=report.resolve()
 if not report.is_file():raise ValueError('actual agent report file required')
 records=read(root/'review/receipts.json') if (root/'review/receipts.json').exists() else []
 for p in pages:
  if p not in state['pages']:raise ValueError('unknown page '+p)
 report_hash=sha(report);saved=root/'review/reports'/f'{report_hash}.md';saved.parent.mkdir(exist_ok=True)
 if saved.resolve()!=report:shutil.copy2(report,saved)
 records.append({'reviewer':reviewer,'report':str(saved.relative_to(root)),'report_sha256':report_hash,'source_sha256':cfg['source_sha256'],'pages':{p:state['pages'][p] for p in pages}})
 write(root/'review/receipts.json',records);return {'recorded':reviewer,'pages':pages,'note':'records caller-reported review; does not fabricate or independently authenticate review content'}

def require_reviews(root,cfg,state):
 if cfg.get('synthetic_example'):raise ValueError('Synthetic examples cannot be released as manufacturing designs; use --proof')
 records=read(root/'review/receipts.json') if (root/'review/receipts.json').exists() else []
 missing=[]
 for pid in [p['id'] for p in cfg['pages']]:
  e=state['pages'][pid]
  reviewers={r['reviewer'] for r in records if r['source_sha256']==cfg['source_sha256'] and r.get('pages',{}).get(pid)==e and (root/r['report']).is_file() and sha(root/r['report'])==r['report_sha256']}
  if len(reviewers)<int(cfg['spec'].get('mandatory_independent_reviewers',2)):missing.append(pid)
 if missing:raise ValueError('two current review records required for release; use --proof for tool tests: '+','.join(missing))

def export_pdfs(path,proof=False):
 start=time.perf_counter();root,cfg,state=fresh_pages(path)
 if not proof:require_reviews(root,cfg,state)
 outdir=root/('proof_pdf' if proof else 'pdf');outdir.mkdir(exist_ok=True)
 inputs=[(e['id'],root/'dxf'/f'{e["id"]}.dxf') for e in cfg['pages']]+[(e['id'],root/e['path']) for e in cfg['attachments']]
 cache_path=outdir/'state.json';cache=read(cache_path) if cache_path.exists() else {'pages':{}}
 eng=engine_hash(['pdf_export.py']);font=sha(root/cfg['font_file']);changed=[]
 for pid,p in inputs:
  signature=digest([sha(p),eng,font]);out=outdir/f'{pid}.pdf';png=outdir/f'{pid}.png';old=cache['pages'].get(pid,{})
  if old.get('input')==signature and all(q.exists() and old.get(q.suffix)==sha(q) for q in [out,png]):continue
  from pdf_export import export_one
  info=export_one(p,out,png);cache['pages'][pid]={'input':signature,'.pdf':sha(out),'.png':sha(png),'check':info};write(cache_path,cache);changed.append(pid)
 order=[p for p,_ in inputs];merge_key=digest([(p,cache['pages'][p]['.pdf']) for p in order]);bound=outdir/'complete.pdf'
 if cache.get('merge')!=merge_key or not bound.exists() or cache.get('bound_sha256')!=sha(bound):
  from pypdf import PdfWriter
  combined=PdfWriter()
  for pid in order:combined.append(str(outdir/f'{pid}.pdf'))
  with bound.open('wb') as stream:combined.write(stream)
  combined.close();cache['merge']=merge_key;cache['bound_sha256']=sha(bound);write(cache_path,cache)
 result={'operation':'pdf','proof':proof,'seconds':round(time.perf_counter()-start,3),'rebuilt':changed,'pages':len(order),'complete':str(bound)}
 write(root/'last-pdf.json',result);return result

def contact(path,pages=None):
 root,cfg,state=fresh_pages(path)
 from PIL import Image,ImageOps,ImageDraw
 ids=pages or [p['id'] for p in cfg['pages']];w=600;h=860;cols=min(3,len(ids));canvas=Image.new('RGB',(cols*w,math.ceil(len(ids)/cols)*h),'white');pen=ImageDraw.Draw(canvas)
 for i,pid in enumerate(ids):
  with Image.open(root/'preview'/f'{pid}.png') as im:canvas.paste(ImageOps.contain(im,(w-10,h-30)),((i%cols)*w,(i//cols)*h+25))
  pen.text(((i%cols)*w+5,(i//cols)*h+5),str(i+1),fill='black')
 canvas.save(root/'review/contact.png');return {'contact':str(root/'review/contact.png'),'pages':ids}

def package(path,proof=False):
 path=Path(path).resolve()
 root,cfg,state=fresh_pages(path)
 if not proof:require_reviews(root,cfg,state)
 # Call PDF no-op check so a stale proof can never be silently packaged.
 pdfresult=export_pdfs(path,proof);folder=root/('proof_pdf' if proof else 'pdf')
 files=[path,root/'build-state.json',root/'inputs/snapshot.json',root/cfg['source'],root/cfg['template'],root/'evidence/source_api.json',folder/'complete.pdf']
 for e in cfg['pages']:files.extend(artifact_paths(root,e['id']));files.extend([folder/f'{e["id"]}.pdf',folder/f'{e["id"]}.png'])
 for e in cfg['attachments']:files.extend([root/e['path'],folder/f'{e["id"]}.pdf'])
 files.extend(root/e['path'] for e in cfg['evidence'])
 for name in ['request.json','receipts.json']:
  if (root/'review'/name).exists():files.append(root/'review'/name)
 if (root/'review/receipts.json').exists():files.extend(root/r['report'] for r in read(root/'review/receipts.json'))
 files=list(dict.fromkeys(files))
 checks={p.relative_to(root).as_posix():sha(p) for p in files};out=root/('PROOF_NOT_RELEASE.zip' if proof else 'delivery.zip')
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.relative_to(root))
  z.writestr('SHA256.json',json.dumps(checks,ensure_ascii=False,indent=2));z.writestr('STATUS.txt','TOOL TEST / NOT RELEASED\n' if proof else 'Review records attached; scope as recorded.\n')
 with zipfile.ZipFile(out) as z:
  assert z.testzip() is None
  for name,h in checks.items():assert hashlib.sha256(z.read(name)).hexdigest()==h
 return {'package':str(out),'sha256':sha(out),'proof':proof,'files':len(files),'pdf_updated':pdfresult['rebuilt']}

def main():
 ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
 p=sub.add_parser('init');p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--title');p.add_argument('--font',type=Path);p.add_argument('--defaults',type=Path)
 for name in ['plan','build','pdf','review-packet','contact','pack','record-review','set-layout','set-spec']:
  p=sub.add_parser(name);p.add_argument('project',type=Path)
  if name in ['build','review-packet','contact']:p.add_argument('--pages',nargs='+')
  if name in ['pdf','pack']:p.add_argument('--proof',action='store_true')
  if name=='record-review':p.add_argument('--reviewer',required=True);p.add_argument('--report',required=True,type=Path);p.add_argument('--pages',required=True,nargs='+')
  if name=='set-layout':p.add_argument('--page',required=True);p.add_argument('--key',required=True,choices=sorted(LAYOUT_KEYS));p.add_argument('--value',required=True,help='JSON number or [x,y]')
  if name=='set-spec':p.add_argument('--page',default='ALL');p.add_argument('--key',required=True,help='existing dotted spec key');p.add_argument('--value',required=True,help='JSON value; only after user has supplied the new requirement')
 a=ap.parse_args()
 if a.command=='init':result=initialize(a.archive,a.out,a.title,a.font,a.defaults)
 elif a.command=='plan':result={'pages':plan(a.project)[-1],'optics':'frozen; no API/STEP/optimizer invoked'}
 elif a.command=='build':result=build(a.project,a.pages)
 elif a.command=='pdf':result=export_pdfs(a.project,a.proof)
 elif a.command=='review-packet':result=packet(a.project,a.pages)
 elif a.command=='contact':result=contact(a.project,a.pages)
 elif a.command=='record-review':result=record_review(a.project,a.reviewer,a.report,a.pages)
 elif a.command=='pack':result=package(a.project,a.proof)
 elif a.command=='set-spec':
  root,cfg,_=load_project(a.project);keys=a.key.split('.');prior=cfg['spec']
  for k in keys:prior=prior[k]
  value=json.loads(a.value)
  if not isinstance(value,type(prior)) and not (isinstance(value,(float,int)) and isinstance(prior,(float,int))):raise ValueError('spec type mismatch')
  if a.page=='ALL':dest=cfg['spec']
  else:dest=next(p for p in cfg['pages'] if p['id']==a.page)['spec_overrides']
  for k in keys[:-1]:dest=dest.setdefault(k,{})
  dest[keys[-1]]=value;write(a.project,cfg);result={'updated_spec':a.key,'page':a.page,'value':value,'note':'no nominal optical dimensions changed; revised tolerances are not optical tolerance-analysis approval'}
 else:
  root,cfg,_=load_project(a.project);item=next(p for p in cfg['pages'] if p['id']==a.page);v=json.loads(a.value)
  if a.key.endswith('_anchor') or a.key=='eta_text':
   if not isinstance(v,list) or len(v)!=2 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in v):raise ValueError('anchor requires finite [x,y]')
  elif not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('finite scalar required')
  item['layout'][a.key]=v;write(a.project,cfg);result={'updated':a.page,'layout':item['layout'],'next':'build then review affected pages'}
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
