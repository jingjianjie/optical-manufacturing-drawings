"""Run one fresh read-only Pi verifier on a prepared completed-image batch."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import os
import time

def run_bounded(cmd,out,err,timeout):
    """Terminate this invocation's descendants on Windows; pi.cmd spawns node."""
    process=subprocess.Popen(cmd,stdout=out,stderr=err)
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name=='nt':
            subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        if process.poll() is None:process.kill()
        process.wait()
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('review_dir')
    p.add_argument('--provider', default='openai-codex')
    p.add_argument('--model', default='gpt-6.1-terra')
    p.add_argument('--thinking', default='high')
    p.add_argument('--timeout', type=float, default=600)
    a = p.parse_args()
    root = Path(a.review_dir).resolve(strict=True)
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('worker_completed') is not True:
        raise ValueError('No completed-worker signal')
    records = manifest['drawings'] + manifest['standard']['pages']
    records += [{'file':'initial-prompt.md', 'sha256':manifest['prompt_sha256']}]
    for r in records:
        actual = hashlib.sha256((root/r['file']).read_bytes()).hexdigest()
        if actual != r['sha256']:
            raise ValueError(f'Frozen input changed: {r["file"]}')
    output = root/'verifier-result.md'
    if output.exists():
        raise FileExistsError('Keep the existing review; prepare a new batch')
    exe = shutil.which('pi.cmd') or shutil.which('pi')
    if not exe:
        raise RuntimeError('Pi CLI not found')
    attachments = json.loads((root/'attachments.json').read_text(encoding='utf-8'))
    cmd = [exe,'--provider',a.provider,'--model',a.model,'--thinking',a.thinking,
           '--no-extensions','--no-mcp','--no-skills','--no-context-files',
           '--no-prompt-templates','--no-tools','--session-dir',str(root/'pi-session'),
           '--print','@'+str(root/'initial-prompt.md')]
    cmd += ['@'+str(root/r['file']) for r in attachments]
    cmd += ['所有图像按附件清单顺序已直接附入。无需文件工具，依据图像、国标原页及注入skill独立端到端检查。只返回审查结果。']
    started=time.monotonic()
    try:
        with output.open('w',encoding='utf-8') as out, (root/'runner-stderr.txt').open('w',encoding='utf-8') as err:
            code=run_bounded(cmd,out,err,a.timeout)
    except subprocess.TimeoutExpired:
        (root/'runner-status.json').write_text(json.dumps({'status':'TIMEOUT','seconds':round(time.monotonic()-started,3),'review_valid':False}),encoding='utf-8')
        raise RuntimeError('Verifier timed out; process tree stopped, no valid review. Preserve this batch and use a fresh narrower review if needed.') from None
    (root/'runner-status.json').write_text(json.dumps({'status':'RETURNED' if code==0 else 'ERROR','exit_code':code,'seconds':round(time.monotonic()-started,3),'review_valid':False,'note':'Coordinator must inspect the report; exit 0 is not PASS.'}),encoding='utf-8')
    if code:
        raise RuntimeError(f'Pi failed ({code}); see runner-stderr.txt')
    print(f'Review returned: {output}. Inspect content; exit 0 alone is not a verification result.')


if __name__=='__main__':
    main()
