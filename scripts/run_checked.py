"""Run one command without shell pipelines; log original exit code and elapsed time."""
import argparse,json,subprocess,time,sys
from pathlib import Path

def run(argv,log,timeout=180,cwd=None):
 log=Path(log);log.parent.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
 try:
  with log.open('wb') as f:
   proc=subprocess.Popen(argv,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                         creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
   try:code=proc.wait(timeout=timeout)
   except subprocess.TimeoutExpired:
    # Own command only; no global Zemax/GUI kill.
    proc.kill();proc.wait();code=124
 except OSError as e:log.write_text(str(e),encoding='utf-8');code=127
 report={'argv':argv,'exit_code':code,'seconds':round(time.perf_counter()-start,3),'log':str(log.resolve()),'timed_out':code==124}
 log.with_suffix(log.suffix+'.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
 if code:print(log.read_text(encoding='utf-8',errors='replace')[-2500:])
 return code

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--log',required=True);ap.add_argument('--timeout',type=float,default=180);ap.add_argument('--cwd');ap.add_argument('argv',nargs=argparse.REMAINDER);a=ap.parse_args()
 argv=a.argv[1:] if a.argv and a.argv[0]=='--' else a.argv
 if not argv:ap.error('command required after --')
 sys.exit(run(argv,a.log,a.timeout,a.cwd))
