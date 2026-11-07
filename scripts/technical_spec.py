"""Project-owned manufacturing text, shared by drawing and review export.

Never applies coating to a face: scope comes exclusively from face_types.
"""
import copy
import json
from pathlib import Path

TEXT_ASSET = Path(__file__).resolve().parent.parent / 'assets/technical-text.json'

def merge(base, patch):
    result = copy.deepcopy(base)
    for key, value in patch.items():
        result[key] = merge(result.get(key, {}), value) if isinstance(value, dict) else copy.deepcopy(value)
    return result

def effective_spec(spec):
    defaults = json.loads(TEXT_ASSET.read_text(encoding='utf-8'))
    result = copy.deepcopy(spec)
    result['technical_text'] = merge(defaults, spec.get('technical_text', {}))
    # Preserve historic projects that rendered Rmax even with no switch stored.
    coat = result['coating']
    coat.setdefault('include_max_reflectance', True)
    coat.setdefault('max_reflectance_percent', coat['reflectance_percent'])
    coat.setdefault('max_comparison', coat.get('comparison', '<'))
    result['tolerances'].setdefault('cemented_child_center_thickness_mm', None)
    result['tolerances'].setdefault('cemented_assembly_center_thickness_mm', None)
    result['assembly_tables'] = merge({'material_values': False, 'part_values': False}, spec.get('assembly_tables', {}))
    return result

def coating_text(coat):
    text = f'{coat["metric"]}{coat["comparison"]}{coat["reflectance_percent"]:g}%'
    if coat['include_max_reflectance']:
        text += f'，Rmax{coat["max_comparison"]}{coat["max_reflectance_percent"]:g}%'
    text += f'，{coat["band_nm"][0]:g}–{coat["band_nm"][1]:g}nm'
    if coat.get('incidence_deg') is not None:text += f'，入射角{coat["incidence_deg"]:g}°'
    if coat.get('polarization'):text += f'，{coat["polarization"]}'
    return text

def render_notes(spec, kind, faces, ct_tol, bevels):
    cfg = spec['technical_text'];tol = spec['tolerances'];ink = spec['blackening']
    coated = [f for f in faces if f['role'] == 'coated']
    scope = '；'.join(f'{f["local"]} {f["label"]}' for f in coated)
    excluded = '；'.join(f'{f["local"]} {f["label"]}' + ('不镀膜' if f['role']=='cemented' else '') for f in faces if f['role']!='coated')
    statement = (coating_text(spec['coating'])+'；'+scope if coated else '本件不镀膜')+'。'
    if excluded:statement += excluded+'。'
    context = dict(adhesive=cfg['adhesive'], surface_quality=spec['surface_requirements']['scratch_dig'],
                   ct_tolerance=ct_tol, linear_tolerance=tol['unindicated_linear_mm'], angle_tolerance=tol['angle_deg'],
                   ink_thickness=ink['thickness_mm'], chamfer_radial='/'.join(f'{x:.3f}' for x in sorted(set(bevels))),
                   coating_statement=statement)
    context['adhesion_statement'] = cfg['adhesion_coated' if coated else 'adhesion_uncoated']
    context['quality_statement'] = cfg['quality_coated' if coated else 'quality_uncoated'].format_map(context)
    context['masking_statement'] = cfg['masking_child' if kind=='单片:子片' else 'masking_single'] if ink['required'] else cfg['blackening_disabled']
    context['blackening_statement'] = cfg['blackening_enabled' if ink['required'] else 'blackening_disabled'].format_map(context)
    templates = cfg['cemented_templates' if kind=='胶合件' else 'single_templates'] + cfg['common_templates'] + cfg['extra_templates']
    lines = [t.format_map(context) for t in templates]
    return [f'{i}. {line}' for i,line in enumerate(lines,1)]

def update_spec(cfg, patch, page='ALL'):
    """Known fields only; validate all edits before the caller writes once."""
    base = effective_spec(cfg['spec'])
    def check(known, change, prefix=''):
        for key,value in change.items():
            if key not in known:raise ValueError('unknown spec key: '+prefix+key)
            old=known[key]
            if isinstance(old,dict):
                if not isinstance(value,dict):raise ValueError('expected object: '+prefix+key)
                check(old,value,prefix+key+'.')
            elif old is not None and not (type(value) is type(old) or type(value) in (int,float) and type(old) in (int,float)):
                raise ValueError('spec type mismatch: '+prefix+key)
    check(base,patch)
    out=copy.deepcopy(cfg);out['spec']=base
    if page=='ALL':out['spec']=merge(base,patch)
    else:
        item=next(p for p in out['pages'] if p['id']==page)
        item['spec_overrides']=merge(item.get('spec_overrides',{}),patch)
    return out
