"""Start each drawing batch in WORKDIR/.pdfout with copied inputs/dependencies.
Fresh input: --source design.zos --mechanical mechanical.json.
Incremental: --project previous/project.json (copies evidence, settings and caches).
Neither mode runs Zemax, renders drawings, nor certifies inherited reviews.
"""
import argparse,datetime,hashlib,json,platform,shutil,sys,uuid
from font_support import resolve_font
from pathlib import Path

SKILL=Path(__file__).resolve().parents[1]
IGNORE=shutil.ignore_patterns('__pycache__','*.pyc','.pdfout')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def freeze(workdir,source=None,mechanical=None,project=None,dependencies=(),label='drawing',font_file=None):
 workdir=Path(workdir).resolve()
 if not workdir.is_dir():raise NotADirectoryError(workdir)
 if not label or any(c in label for c in '<>:"/\\|?*') or label in ['.','..']:raise ValueError('label should be a plain directory name')
 if bool(project)==bool(source):raise ValueError('Choose --project OR --source with --mechanical')
 if source and not mechanical:raise ValueError('--mechanical required with --source')
 stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
 dest=workdir/'.pdfout'/f'{stamp}_{label}_{uuid.uuid4().hex[:6]}'
 dest.mkdir(parents=True,exist_ok=False);source_records=[]
 def copy_file(src,target):
  src=Path(src).resolve()
  if not src.is_file():raise FileNotFoundError(src)
  before=sha(src);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
  if sha(src)!=before or sha(target)!=before:raise RuntimeError('Input changed during snapshot: '+str(src))
  source_records.append({'source':str(src),'copy':str(target.relative_to(dest)),'sha256':before})
 if project:
  project=Path(project).resolve();old=project.parent
  if dest.is_relative_to(old):raise ValueError('Choose a working directory outside the previous project to avoid recursive copying')
  cfg=json.loads(project.read_text(encoding='utf-8-sig'))
  for name in ['source','snapshot','template']:
   if not (old/cfg[name]).is_file():raise FileNotFoundError(old/cfg[name])
  # Copy actual project files, including useful caches; exclude old archives and nested batches.
  shutil.copytree(old,dest/'project',ignore=shutil.ignore_patterns('__pycache__','*.pyc','.pdfout','*.zip'))
  # Raw inputs/references belong to the batch, not necessarily project.json's directory.
  # Carry them forward so every increment remains self-contained.
  prior_batch=next((p for p in [old,old.parent] if (p/'frozen-manifest.json').is_file()),None)
  if prior_batch:
   for folder in ['inputs','dependencies','added_dependencies']:
    if (prior_batch/folder).is_dir():shutil.copytree(prior_batch/folder,dest/folder,ignore=IGNORE)
   copy_file(prior_batch/'frozen-manifest.json',dest/'previous-frozen-manifest.json')
  def localize(ref):
   p=(old/ref).resolve()
   if p.is_relative_to(old):return p.relative_to(old).as_posix()
   new=dest/'project/dependencies'/(sha(p)[:12]+'_'+p.name);copy_file(p,new)
   return new.relative_to(dest/'project').as_posix()
  for name in ['source','snapshot','template']:cfg[name]=localize(cfg[name])
  for entry in cfg.get('attachments',[])+cfg.get('evidence',[]):entry['path']=localize(entry['path'])
  font=(old/cfg['font_file']).resolve()
  copy_file(font,dest/'local-fonts'/font.name)
  cfg['font_file']='local-fonts/'+font.name
  copy_file(font,dest/'project/local-fonts'/font.name)
  save(dest/'project/project.json',cfg)
  source_records.append({'source':str(project),'copy':'project/project.json','source_sha256':sha(project),'note':'paths rebased; prior configuration retained as frozen_original_project.json'})
  copy_file(project,dest/'frozen_original_project.json')
 else:
  copy_file(source,dest/'inputs/design.zos');copy_file(mechanical,dest/'inputs/mechanical.json')
  font=resolve_font(font_file)
  copy_file(font,dest/'local-fonts'/font.name)
 # The invoked skill is a frozen dependency. Use its CLI within the new batch.
 shutil.copytree(SKILL,dest/'skill',ignore=IGNORE)
 for i,dependency in enumerate(dependencies,1):
  src=Path(dependency).resolve();bucket='added_dependencies' if project else 'dependencies'
  target=dest/bucket/f'{stamp}_{i:02}_{src.name}'
  if src.is_file():copy_file(src,target)
  elif src.is_dir():
   if dest.is_relative_to(src):raise ValueError('Dependency contains destination: '+str(src))
   shutil.copytree(src,target,ignore=IGNORE)
  else:raise FileNotFoundError(src)
 manifest={'created_at':datetime.datetime.now().astimezone().isoformat(),'mode':'incremental' if project else 'fresh',
   'workdir':str(workdir),'previous_project':str(project) if project else None,'skill_origin':str(SKILL),
   'runtime':{'python':sys.version,'executable':sys.executable,'platform':platform.platform()},'sources':source_records,
   'files':{p.relative_to(dest).as_posix():sha(p) for p in sorted(dest.rglob('*')) if p.is_file()},
   'semantics':'Initial copy manifest; original source/previous project unchanged. Edit this batch configuration and derived outputs only; a subsequent batch starts a new copy. Runtime software remains installed externally; local fonts are not redistributable package assets.'}
 save(dest/'frozen-manifest.json',manifest)
 return {'batch':str(dest),'project':str(dest/'project/project.json') if project else None,'skill':str(dest/'skill'),
   'manifest':str(dest/'frozen-manifest.json'),'files':len(manifest['files']),'next':'Use copied skill/scripts CLI in this batch; fresh intake still needs API/CAD/appendix/reviews.'}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--workdir',type=Path,default=Path.cwd());ap.add_argument('--source',type=Path);ap.add_argument('--mechanical',type=Path);ap.add_argument('--project',type=Path);ap.add_argument('--dependency',type=Path,action='append',default=[]);ap.add_argument('--label',default='drawing');ap.add_argument('--font',type=Path);a=ap.parse_args()
 print(json.dumps(freeze(a.workdir,a.source,a.mechanical,a.project,a.dependency,a.label,a.font),ensure_ascii=False,indent=2))
