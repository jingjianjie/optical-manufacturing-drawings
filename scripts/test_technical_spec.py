"""Regression checks for repeated manufacturing-text changes; no Zemax needed."""
import copy,json,unittest
from pathlib import Path
from technical_spec import effective_spec,coating_text,render_notes,update_spec

class TechnicalSpecTests(unittest.TestCase):
    def setUp(self):
        self.spec=effective_spec(json.loads((Path(__file__).parent.parent/'assets/drawing-defaults.json').read_text(encoding='utf-8')))
        self.faces=[dict(local='S1',role='coated',label='镀膜面'),dict(local='S2',role='cemented',label='胶合面')]
    def test_both_reflectance_metrics_are_independent(self):
        c=self.spec['coating'];c.update(reflectance_percent=.5,max_reflectance_percent=.8,include_max_reflectance=False)
        self.assertNotIn('Rmax',coating_text(c))
        c['include_max_reflectance']=True
        self.assertIn('Rmax<0.8%',coating_text(c));self.assertIn('Ravg<0.5%',coating_text(c))
    def test_no_coating_no_ar_requirement(self):
        faces=[dict(local='S1',role='uncoated',label='不镀膜面'),self.faces[1]]
        lines=render_notes(self.spec,'单片:子片',faces,.1,[.2,.3])
        self.assertNotIn('Ravg',' '.join(lines));self.assertIn('S2 胶合面不镀膜',' '.join(lines))
        self.assertIn('0.200/0.300',' '.join(lines))
    def test_old_project_new_key_and_atomic_invalid_patch(self):
        old=copy.deepcopy(self.spec);del old['technical_text'];del old['coating']['include_max_reflectance']
        cfg=dict(spec=old,pages=[dict(id='L1',spec_overrides={})]);before=copy.deepcopy(cfg)
        changed=update_spec(cfg,{'coating':{'include_max_reflectance':False}})
        self.assertFalse(changed['spec']['coating']['include_max_reflectance']);self.assertEqual(cfg,before)
        with self.assertRaises(ValueError):update_spec(cfg,{'coating':{'reflectance_percent':.8,'typo':False}})
        self.assertEqual(cfg,before)
    def test_template_and_scope_follow_same_inputs(self):
        s=self.spec;s['technical_text']['adhesive']='测试胶';s['technical_text']['extra_templates']=['复验CT {ct_tolerance:.3f}mm']
        lines=render_notes(s,'胶合件',self.faces,.2,[.2])
        self.assertIn('测试胶',lines[0]);self.assertIn('复验CT 0.200mm',lines[-1])
        self.assertIn('S2 胶合面不镀膜',' '.join(lines))
    def test_blackening_disabled(self):
        self.spec['blackening']['required']=False
        lines=render_notes(self.spec,'单片',self.faces,.2,[.2])
        self.assertIn('本件不涂黑',' '.join(lines));self.assertNotIn('墨厚',' '.join(lines))

if __name__=='__main__':unittest.main()
