import json
import unittest
from pathlib import Path
from test_pipeline_gate import gate, fixture
from test_source_quality import sources

HERE=Path(__file__).resolve().parents[1]

class UniversalNicheTests(unittest.TestCase):
    def test_five_distinct_briefs_use_one_gate(self):
        briefs=json.loads((HERE/'fixtures/five_niches.json').read_text('utf8'))
        self.assertEqual(len(briefs),5)
        for brief in briefs:
            with self.subTest(industry=brief['industry']):
                data=fixture(industry=brief['industry'],fact_mode=brief['evidence_mode'])
                data['brief'].update({k:brief[k] for k in ('topic','audience','industry','goal')})
                if brief['evidence_mode']=='SOURCE_CHECK_REQUIRED':
                    data['facts']['claims']=[{'text':'Организатор указал расписание', 'source_urls':['https://example.org/calendar']}]
                self.assertTrue(gate.audit_pipeline(data)['structurally_complete'])
                s=sources.choose_sources(brief['topic'],brief['audience'],brief['industry'])
                self.assertTrue(s['candidates'])
                self.assertEqual(s['status'],'CANDIDATE_SOURCES_NOT_FETCHED')

if __name__=='__main__':unittest.main()
