"""Explicit, relocatable font dependencies. No machine-specific fallback paths."""
import os
from pathlib import Path

def resolve_font(value=None):
    candidate=value or os.environ.get('OPTICAL_DRAWING_FONT')
    if candidate:
        p=Path(candidate).expanduser().resolve()
        if not p.is_file():raise FileNotFoundError(p)
        return p
    frozen=Path(__file__).resolve().parents[2]/'local-fonts'
    choices=[p for p in frozen.glob('*') if p.suffix.lower() in ['.ttf','.otf','.ttc']]
    if len(choices)==1:return choices[0].resolve()
    raise ValueError('Supply --font PATH or OPTICAL_DRAWING_FONT; use a font covering Chinese and engineering symbols. No font is bundled.')

def register_font(path):
    from ezdxf.fonts import fonts
    p=Path(path).resolve()
    if not p.is_file():raise FileNotFoundError(p)
    fonts.font_manager.build([str(p.parent)],support_dirs=False)
    if not fonts.font_manager.has_font(p.name):raise RuntimeError('Font not registered: '+p.name)
    return p
