"""Freeze completed drawings and create an image-first, model-neutral review request."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

SKILL = Path(__file__).resolve().parents[1]
KINDS = {'singlet', 'cemented-element', 'cemented-assembly'}
BASE_PAGES = {4, 6, 7, 8, 10, 12, 13, 14, 15, 16, 28, 29}
SPHERICAL_PAGES = {6, 10, 13, 28, 29}
EXAMPLE = {'singlet': 20, 'cemented-element': 21, 'cemented-assembly': 19}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(args):
    if not args.completed:
        raise ValueError('Worker has not declared this drawing batch complete; do not start verifier.')
    scope=getattr(args,'scope','spherical')
    extra_pages=set(getattr(args,'reference_page',None) or [])
    if not extra_pages.issubset(set(range(1,31))):raise ValueError('Reference page must be 1..30')
    items = []
    for kind, filename in args.item:
        source = Path(filename).resolve(strict=True)
        if kind not in KINDS:
            raise ValueError(f'Unsupported workpiece type: {kind}')
        if source.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp'}:
            raise ValueError(f'Provide completed drawing images, not CAD/PDF paths: {source}')
        items.append((kind, source))
    selected = (SPHERICAL_PAGES if scope=='spherical' else BASE_PAGES) | {EXAMPLE[k] for k, _ in items} | extra_pages
    if args.standards_root:
        standards = Path(args.standards_root).resolve(strict=True)
        book = standards / '光学制图国标调查'
        full = book / 'mineru/GBT13323-2009_public-reader/extracted/full.md'
        pages = book / 'sources/baidu-reader-pages'
        numbers=list(range(1,31))
    else:
        if scope=='full':raise ValueError('Full scope requires --standards-root with complete OCR and original pages')
        standards=SKILL/'references/gb-reference-pages';pages=standards;full=None
        numbers=sorted(selected)
    required = ([full] if full else []) + [pages / f'page-{i:02}.png' for i in numbers]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    requirements = Path(args.requirements).resolve(strict=True) if args.requirements else None
    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError(f'Use a fresh review directory: {out}')
    out.mkdir(parents=True)
    (out / 'drawings').mkdir()
    (out / 'standard-pages').mkdir()
    drawings = []
    attachments = []
    for index, (kind, source) in enumerate(items, 1):
        dest = out / 'drawings' / f'{index:02}-{source.name}'
        shutil.copy2(source, dest)
        record = {'file': dest.relative_to(out).as_posix(), 'type': kind, 'source': str(source), 'sha256': digest(dest)}
        drawings.append(record)
        attachments.append({'role': 'drawing', 'file': record['file'], 'type': kind})
    page_records = []
    for number in numbers:
        source = pages / f'page-{number:02}.png'
        dest = out / 'standard-pages' / source.name
        shutil.copy2(source, dest)
        page_records.append({'page': number, 'file': dest.relative_to(out).as_posix(), 'sha256': digest(dest)})
        if number in selected:
            attachments.append({'role': 'standard-reference', 'file': dest.relative_to(out).as_posix(), 'pdf_page': number})
    if full:shutil.copy2(full, out / 'standard-ocr.md')
    if (SKILL/'references/gb-reference-pages/README.md').exists():
        shutil.copy2(SKILL/'references/gb-reference-pages/README.md',out/'REFERENCE-NOTICE.md')
    reference_names=['SKILL.md','GLOSSARY.md','references/language-map.md','references/page-heuristics.md']
    reference_names += ['references/spherical-practice.md','references/spherical-standards.md','references/shop-drawing-patterns.md'] if scope=='spherical' else ['references/standard-summary.md','references/necessary-checks.md']
    prompt = [
        '# 完成图独立端到端国标审查',
        'worker 已宣告本轮全部出图完成。以下是冻结送审包。请一次性独立审查并返回完整结果；不要联络或修改 worker。',
        '先看待检图像，再按工件类型判断必要项；不提供预期答案。只执行图面审查，不跑ZOS或另行设计。',
        '## 本轮待检图像与工件类型',
        json.dumps(drawings, ensure_ascii=False, indent=2),
        '## 图像附件顺序（前面为待检图，后面为国标原页）',
        json.dumps(attachments, ensure_ascii=False, indent=2),
        '原页均为标准参考，不能误当待检工件。附录A是示例，示例尺寸不作项目要求。',
        '## 标准资料位置',
        f'来源目录：{standards}\n本次冻结目录：{out}\n原页清单：'+','.join(str(n) for n in numbers)+('；OCR：standard-ocr.md。' if full else '；仅本范围参考原页，无全文OCR。'),
        '## Verifier skill（已直接注入）',
        *[(SKILL / name).read_text(encoding='utf-8') for name in reference_names],
        '## 审查范围',
        ('仅球面/平面玻璃透镜、胶合子片与双胶合总图，先按工作卡筛查，再对疑点查详细指引和已附原页。需清单之外的原页时列最小补证页号，不凭空称已看过。' if scope=='spherical' else '完整通用范围，按工件类型判定适用性。'),
        '## 已提供项目要求',
        requirements.read_text(encoding='utf-8') if requirements else '未附额外项目要求。仍执行本skill内置用户工艺启发式；不另套未提供的厂商默认或设计意图。',
    ]
    if scope=='full':
        prompt += ['## 标准OCR全文（辅助检索；图形与可疑字符以原页为准）', '内嵌图片链接来自原解析包；使用已附原页图，不依赖这些图片链接。', full.read_text(encoding='utf-8')]
    (out / 'initial-prompt.md').write_text('\n\n'.join(prompt), encoding='utf-8')
    (out / 'attachments.json').write_text(json.dumps(attachments, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest = {'worker_completed': True, 'scope':scope, 'reference_pages_attached':sorted(selected), 'ocr_injected':scope=='full', 'drawings': drawings, 'standard': {'name': 'GB/T 13323-2009', 'source_root': str(standards), 'ocr_sha256': digest(full) if full else None, 'pages': page_records}, 'skill_files': {str(p.relative_to(SKILL)): digest(p) for p in [*[SKILL/name for name in reference_names], Path(__file__)]}, 'requirements_sha256': digest(requirements) if requirements else None, 'prompt_sha256': digest(out/'initial-prompt.md')}
    if requirements:
        shutil.copy2(requirements, out / 'project-requirements.md')
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'review_dir': str(out), 'drawings': len(drawings), 'reference_images_attached': len(attachments)-len(drawings), 'prompt': str(out/'initial-prompt.md')},ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--completed', action='store_true')
    parser.add_argument('--standards-root', help='Optional for spherical scope; otherwise use bundled reference pages')
    parser.add_argument('--out', required=True)
    parser.add_argument('--item', action='append', nargs=2, required=True, metavar=('TYPE', 'IMAGE'))
    parser.add_argument('--requirements')
    parser.add_argument('--scope',choices=['spherical','full'],default='spherical')
    parser.add_argument('--reference-page',action='append',type=int,help='Add an original PDF page for a specific disputed item; repeatable')
    prepare(parser.parse_args())
