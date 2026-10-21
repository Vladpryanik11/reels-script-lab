"""Method-level regressions based on October 21 methodology audit.
New tests are added before implementation; structural checks are necessary but not semantic proofs.
"""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
S = ROOT/'reels-script-lab/skills/reels-script-lab'
spec = importlib.util.spec_from_file_location('restored_gate', S/'scripts/pipeline_gate.py')
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)
spec2 = importlib.util.spec_from_file_location('legacy_test', ROOT/'tests/test_pipeline_gate.py')
tests = importlib.util.module_from_spec(spec2)
sys.modules[spec2.name] = tests
spec2.loader.exec_module(tests)

class MethodRestoration(unittest.TestCase):
    def fixture(self):
        return tests.fixture()
    def errors(self, d):
        return gate.audit_pipeline(d)['errors']

    def test_unregistered_structure_is_rejected(self):
        d=self.fixture();d['branches'][0]['structure']['name']='UNKNOWN_STRUCT_XYZ'
        self.assertIn('invalid_structure_id',self.errors(d))

    def test_duplicate_story_route_is_rejected(self):
        d=self.fixture()
        for b in d['branches']:
            b['structure']['structure_id']='SRC-04'
            b['structure']['narrative_route']='same narrative route'
        self.assertIn('duplicate_narrative_route',self.errors(d))

    def test_structure_requires_fit_and_reveal_map(self):
        d=self.fixture();d['branches'][0]['structure'].pop('fit_reason',None)
        d['branches'][0]['structure'].pop('reveal_map',None)
        err=self.errors(d)
        self.assertIn('missing_structure_fit_reason',err)
        self.assertIn('missing_reveal_map',err)

    def test_microdetective_requires_real_investigative_steps(self):
        d=self.fixture(); s=d['branches'][0]['structure'];s['structure_id']='SRC-03';s['investigation_steps']=[]
        self.assertIn('microdetective_missing_investigation',self.errors(d))

    def test_object_story_requires_object_in_three_scenes(self):
        d=self.fixture();s=d['branches'][0]['structure'];s['structure_id']='SRC-04';s['object_anchor']={'object':'коробка','appearances':['HOOK']}
        self.assertIn('object_not_repeated',self.errors(d))

    def test_parallel_stories_require_comparable_starts(self):
        d=self.fixture();s=d['branches'][0]['structure'];s['structure_id']='SRC-06';s['parallel_tracks']={'same_start_conditions':False,'tracks':['x','y']}
        self.assertIn('parallel_unfair_comparison',self.errors(d))

    def test_fake_rehook_generic_must_not_silently_pass(self):
        d=self.fixture();b=d['branches'][0];b['rehook']['text']='Но есть один нюанс!';b['script']['lines'][2]='Но есть один нюанс!'
        self.assertIn('generic_rehook_requires_review',self.errors(d))

    def test_rehook_needs_tatam_technique_and_next_beat(self):
        d=self.fixture();r=d['branches'][0]['rehook'];r.pop('technique_id',None);r.pop('next_beat',None)
        self.assertIn('missing_rehook_technique',self.errors(d))
        self.assertIn('missing_rehook_next_beat',self.errors(d))

    def test_rehook_unsupported_technique(self):
        d=self.fixture();d['branches'][0]['rehook']['technique_id']='TR-FAKE'
        self.assertIn('invalid_rehook_technique',self.errors(d))

    def test_placeholder_development_blocked(self):
        d=self.fixture();d['branches'][0]['script']['lines'][1]='Сегодня разберём это.'
        self.assertIn('placeholder_development_requires_review',self.errors(d))

    def test_locked_methodology_docs_are_present_and_referenced(self):
        sk=(S/'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('references/13-structure-methodology.md',sk)
        self.assertIn('references/15-rehook-methodology.md',sk)
        for p in ('13-structure-methodology.md','14-structure-reviewer.md','15-rehook-methodology.md','16-rehook-reviewer.md','17-script-storytelling.md'):
            self.assertTrue((S/'references'/p).is_file(),p)

    def test_not_generic_only_story_methods(self):
        text=(S/'references/13-structure-methodology.md').read_text('utf8')
        for id in range(1,8):self.assertIn('SRC-%02d'%id,text)
        self.assertIn('excluded_structures',text)
        text2=(S/'references/15-rehook-methodology.md').read_text('utf8')
        for id in range(1,7):self.assertIn('TR-%02d'%id,text2)

if __name__=='__main__':unittest.main()
