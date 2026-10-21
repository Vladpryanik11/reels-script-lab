import json
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'reels-script-lab/skills/reels-script-lab/scripts'
spec=importlib.util.spec_from_file_location('integration_gate', SCRIPTS/'integration_gate.py')
gate=importlib.util.module_from_spec(spec);sys.modules[spec.name]=gate;spec.loader.exec_module(gate)

class LivePilotFixtureTests(unittest.TestCase):
    def test_three_independent_industries_with_three_angles_each(self):
        files=list(sorted((ROOT/'fixtures/live-pilots').glob('*.json')))
        self.assertEqual(len(files),3)
        industries=set();angles=set();hooks=set()
        for file in files:
            case=json.loads(file.read_text(encoding='utf-8'))
            result=gate.audit_integration_case(case)
            self.assertEqual(result['errors'],[],(file.name,result))
            self.assertEqual(result['release_status'],'PREVIEW_ONLY_SOURCE_AND_EDITORIAL_REVIEW_PENDING')
            self.assertLess(result['distinct_discussions'],3)
            self.assertFalse(result['provenance_independently_attested'])
            self.assertEqual(case['editorial_review'],'SELF_REVIEW_ONLY')
            self.assertEqual(len(case['candidates']),3)
            industries.add(case['brief']['industry'])
            for c in case['candidates']:
                angles.add((case['brief']['industry'],c['angle']))
                hooks.add(c['hook'])
        self.assertEqual(len(industries),3)
        self.assertEqual(len(angles),9)
        self.assertEqual(len(hooks),9)
    def test_real_source_urls_not_trusted_as_authoritative_claims(self):
        for file in (ROOT/'fixtures/live-pilots').glob('*.json'):
            case=json.loads(file.read_text(encoding='utf-8'))
            self.assertNotIn('INDEPENDENT_PASS',file.read_text())
            self.assertFalse(case['autonomous_agents_verified'])
            self.assertTrue(all(a['source_id'] in {s['id'] for s in case['sources']} for a in case['observations']))

if __name__=='__main__':unittest.main()
