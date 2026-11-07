"""Public-source allowlist archive. Never packages .pdfout, design deliveries or fonts."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOP={'SKILL.md','GLOSSARY.md','README.md','LICENSE','THIRD_PARTY.md','requirements.txt','requirements-zos.txt','requirements-step.txt','.gitignore','.gitattributes'}

def selected(root=ROOT):
    files=[]
    for p in root.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(root);parts=rel.parts
        if any(x in ['__pycache__','.pdfout','bin','obj','.venv'] for x in parts):continue
        good=(rel.as_posix() in TOP or (parts[0] in ['references','scripts','tests','prompts'] and p.suffix in ['.md','.py'])
              or (parts[0]=='verifier' and p.suffix in ['.md','.py'])
              or (parts[0] in ['references','verifier'] and 'gb-reference-pages' in parts and p.suffix in ['.png','.json'])
              or rel.as_posix()=='assets/technical-text.json'
              or (parts[0]=='cad' and p.suffix in ['.md','.py','.cs','.csproj'])
              or rel.as_posix() in ['assets/drawing-defaults.json','assets/a4-frame/generic-a4.dxf','assets/symbols/optical-house-symbols.dxf','samples/README.md','samples/sanitized-shuffled.zos','samples/sanitized-shuffled.zmx','samples/sanitization.json','docs/previews/SINGLET.png','docs/previews/PAIR_A.png','docs/previews/PAIR_B.png','docs/previews/PAIR.png','docs/previews/complete.pdf'])
        if good:files.append(p)
    return sorted(files)

def audit(files,root=ROOT):
    errors=[]
    for p in files:
        rel=p.relative_to(root).as_posix()
        if p.suffix in ['.zos','.png','.pdf']:continue  # Explicit allowlist includes attributed standard reference pages.
        raw=p.read_bytes();s=raw.decode('utf-16') if raw[:2] in [b'\xff\xfe',b'\xfe\xff'] else raw.decode('utf-8-sig')
        if re.search(r'(?i)(?<![a-z])[a-z]:[\\/](?!/)',s):errors.append(rel+': absolute drive path')
        if rel!='scripts/release.py' and re.search(r'(?i)(/Users/|/home/|Users[\\/]+win|\.agents[\\/]+skills|replay_tests|R13_|VR66_|orca-paste)',s):errors.append(rel+': private workspace reference')
        if p.suffix=='.md':
            for link in re.findall(r'\]\(([^)]+)\)',s):
                link=link.split('#')[0].strip('<>')
                if not link or '://' in link or link.startswith('mailto:'):continue
                if not (p.parent/link).is_file():errors.append(rel+': missing local link '+link)
        if p.suffix=='.py':compile(s,str(p),'exec')
    if errors:raise ValueError('\n'.join(errors))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    files=selected();audit(files);a.out.parent.mkdir(parents=True,exist_ok=True)
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with zipfile.ZipFile(a.out,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
        z.writestr(ROOT.name+'/RELEASE-MANIFEST.json',json.dumps({'license':'MIT; standard reference pages retain third-party rights, see THIRD_PARTY.md','files':hashes,'policy':'allowlisted public source, synthetic assets and attributed standard reference pages'},indent=2))
    with zipfile.ZipFile(a.out) as z:
        assert z.testzip() is None
        for name,h in hashes.items():assert hashlib.sha256(z.read(ROOT.name+'/'+name)).hexdigest()==h
    print(json.dumps({'archive':str(a.out),'files':len(files),'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'bytes':a.out.stat().st_size}))
if __name__=='__main__':main()
