"""Local DXF inventory, candidate-font coverage, preview and scoped comparison."""
import argparse
from collections import Counter
import json
import io
from pathlib import Path
import re
import sys

import ezdxf
from ezdxf.lldxf.encoding import decode_dxf_unicode


def emit(value, output):
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if output:
        path = Path(output)
        if path.exists():
            raise FileExistsError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        print(path)
    else:
        print(text)


def spaces(doc):
    for layout in doc.layouts:
        yield 'layout:' + layout.name, layout
    for block in doc.blocks:
        if not block.block_record.is_any_layout:
            yield 'block:' + block.name, block


def entities(doc):
    for scope, space in spaces(doc):
        for entity in space:
            yield scope, entity
            if entity.dxftype() == 'INSERT':
                for attr in entity.attribs:
                    yield scope, attr


def text_value(entity):
    if entity.dxftype() == 'MTEXT':
        return entity.text, decode_dxf_unicode(entity.plain_text())
    if entity.dxftype() in ('TEXT', 'ATTRIB', 'ATTDEF'):
        return entity.dxf.text, decode_dxf_unicode(entity.plain_text())
    if entity.dxftype() == 'DIMENSION':
        raw = entity.dxf.get('text', '')
        return raw, decode_dxf_unicode(raw)
    return None


def inventory(doc):
    texts = []
    for scope, entity in entities(doc):
        value = text_value(entity)
        if value is not None:
            raw, plain = value
            texts.append(dict(scope=scope, handle=entity.dxf.handle,
                              type=entity.dxftype(), style=entity.dxf.get('style'),
                              raw=raw, plain=plain,
                              inline_fonts=re.findall(r'\\[fF]([^;]+);', raw)))
    audit = doc.audit()
    return dict(version=doc.dxfversion, units=doc.header.get('$INSUNITS', 0),
                codepage=doc.header.get('$DWGCODEPAGE'),
                spaces={s: dict(Counter(e.dxftype() for e in es)) for s, es in spaces(doc)},
                layers=[l.dxf.name for l in doc.layers],
                styles=[dict(name=s.dxf.name, font=s.dxf.font,
                             bigfont=s.dxf.get('bigfont', '')) for s in doc.styles],
                texts=texts,
                audit_errors=[str(e) for e in audit.errors],
                audit_fixes=[str(e) for e in audit.fixes],
                text_scope='TEXT/MTEXT/ATTRIB/ATTDEF and DIMENSION override; complex objects require separate inspection')


def font_check(doc, filename):
    from fontTools.ttLib import TTCollection, TTFont
    chars = set(''.join(v[1] for _, e in entities(doc) if (v := text_value(e))))
    chars = {c for c in chars if not c.isspace()}
    path = Path(filename)
    if path.suffix.lower() in ('.ttc', '.otc'):
        collection = TTCollection(path)
        fonts = collection.fonts
    else:
        fonts = [TTFont(path)]
    results = []
    try:
        for index, font in enumerate(fonts):
            cmap = font.getBestCmap() or {}
            missing = sorted(chars - {chr(code) for code in cmap})
            results.append(dict(face=index, family=font['name'].getDebugName(1),
                                missing=[dict(char=c, codepoint=f'U+{ord(c):04X}') for c in missing]))
    finally:
        for font in fonts:
            font.close()
    return dict(font=str(path.resolve()), unique_characters=len(chars), faces=results,
                scope='Candidate font coverage only; does not resolve actual entity/inline font or SHX rendering')


SKIP = {'handle', 'owner', 'material_handle', 'plotstyle_handle', 'visualstyle_handle'}
SUPPORTED = {'LINE', 'POINT', 'CIRCLE', 'ARC', 'ELLIPSE', 'LWPOLYLINE',
             'TEXT', 'MTEXT', 'ATTRIB', 'ATTDEF', 'INSERT', 'SOLID', 'TRACE', '3DFACE'}


def normalized(value, decimals):
    if isinstance(value, float):
        return round(value, decimals)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        return {k: normalized(v, decimals) for k, v in sorted(value.items()) if k not in SKIP}
    try:
        return [normalized(v, decimals) for v in value]
    except TypeError:
        return str(value)


def snapshot(doc, decimals):
    records, unsupported = Counter(), Counter()
    for scope, entity in entities(doc):
        kind = entity.dxftype()
        if kind not in SUPPORTED:
            unsupported[kind] += 1
        data = dict(scope=scope, type=kind, attrs=entity.dxf.all_existing_dxf_attribs())
        if kind == 'MTEXT':
            data['content'] = entity.text
        if kind == 'LWPOLYLINE':
            data['points_xyseb'] = list(entity.get_points())
        records[json.dumps(normalized(data, decimals), ensure_ascii=False, sort_keys=True)] += 1
    tables = dict(styles=[normalized(s.dxf.all_existing_dxf_attribs(), decimals) for s in doc.styles],
                  layers=[normalized(s.dxf.all_existing_dxf_attribs(), decimals) for s in doc.layers])
    for key in tables:
        tables[key] = sorted(tables[key], key=lambda item: item['name'])
    return records, unsupported, tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('inspect', 'font-check', 'render', 'compare', 'unicode-copy'):
        cmd = sub.add_parser(name)
        cmd.add_argument('input')
        if name == 'font-check':
            cmd.add_argument('font')
        if name in ('render', 'compare', 'unicode-copy'):
            cmd.add_argument('target')
        if name not in ('render', 'unicode-copy'):
            cmd.add_argument('--out')
        if name == 'render':
            cmd.add_argument('--layout', default='Model')
            cmd.add_argument('--dpi', type=int, default=180)
        if name == 'compare':
            cmd.add_argument('--decimals', type=int, default=7)
    args = parser.parse_args()
    if Path(args.input).suffix.lower() != '.dxf':
        parser.error('Convert DWG to a working DXF first.')
    doc = ezdxf.readfile(args.input)
    if args.command == 'unicode-copy':
        path = Path(args.target)
        if path.exists():
            raise FileExistsError(path)
        if path.suffix.lower() != '.dxf':
            parser.error('unicode-copy output must be DXF.')
        source = Path(args.input).read_bytes()
        if source.startswith(b'AutoCAD Binary DXF'):
            parser.error('unicode-copy requires ASCII/text DXF, not binary DXF.')
        encoding = 'utf-8' if doc.dxfversion >= 'AC1021' else doc.encoding
        decoded = decode_dxf_unicode(source.decode(encoding))
        upgraded = ezdxf.read(io.StringIO(decoded, newline=None))
        # Never downgrade a modern source.
        if upgraded.dxfversion < 'AC1024':
            upgraded.dxfversion = 'AC1024'
        path.parent.mkdir(parents=True, exist_ok=True)
        upgraded.saveas(path)
        print('Decoded standard DXF Unicode escapes into a modern UTF-8 DXF copy:', path)
    elif args.command == 'inspect':
        emit(inventory(doc), args.out)
    elif args.command == 'font-check':
        result = font_check(doc, args.font)
        emit(result, args.out)
        return 0 if any(not face['missing'] for face in result['faces']) else 2
    elif args.command == 'render':
        from ezdxf.addons.drawing import matplotlib
        path = Path(args.target)
        if path.exists():
            raise FileExistsError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        matplotlib.qsave(doc.layouts.get(args.layout), path, bg='#FFFFFF', dpi=args.dpi)
        print('Review preview AND renderer output for missing/skipped text:', path)
    else:
        other = ezdxf.readfile(args.target)
        a, ua, ta = snapshot(doc, args.decimals)
        b, ub, tb = snapshot(other, args.decimals)
        headers = ('$INSUNITS', '$MEASUREMENT', '$INSBASE')
        hd = {k: [normalized(doc.header.get(k), args.decimals),
                  normalized(other.header.get(k), args.decimals)] for k in headers
              if normalized(doc.header.get(k), args.decimals) != normalized(other.header.get(k), args.decimals)}
        equal = a == b and ta == tb and not hd
        emit(dict(equal_in_checked_scope=equal, unsupported_before=dict(ua), unsupported_after=dict(ub),
                  missing=[dict(count=n, entity=json.loads(s)) for s, n in (a-b).items()],
                  added=[dict(count=n, entity=json.loads(s)) for s, n in (b-a).items()],
                  style_layer_tables_equal=ta == tb, header_differences=hd,
                  limits='Excludes handles, xdata, reactors, dictionaries, linetype definitions, plot settings and extension objects. Unsupported types need independent validation. Explicit/default attribute differences may require review.'), args.out)
        return 0 if equal and not ua and not ub else 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
