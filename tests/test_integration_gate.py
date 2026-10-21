"""Behavior tests first: an editorial claim cannot be certified by self-reported source JSON."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'reels-script-lab/skills/reels-script-lab/scripts'
spec=importlib.util.spec_from_file_location('integration_gate', SCRIPTS / 'integration_gate.py')
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)


def sample():
    return {
        'contract_version':'0.8.0',
        'brief':{'topic':'Покупка робота-пылесоса','audience':'люди с домашними животными','industry':'consumer_goods','goal':'полезный обзор'},
        'sources':[{'id':'HABR1','url':'https://habr.com/ru/articles/587580/comments/',
            'platform':'habr','access':'FULL_PAGE_OPENED','capture_ref':'turn647336view0',
            'captured_at':'2026-10-20T18:00:00+00:00','source_kind':'discussion'}],
        'observations':[{'id':'O1','source_id':'HABR1','speaker_id':'svob','kind':'user_comment',
            'situation':'Волосы и шерсть наматываются на щетку робота, которую потом приходится чистить.',
            'voice_signal':'раздражение из-за обслуживания','audience_fit':'владельцы домашних животных'}],
        'candidates':[{'id':'A','anchor_ids':['O1'],'angle':'обслуживание вместо свободы',
            'hook':'Купили робота, а щетку опять чистить руками?',
            'edits':[{'actor':'writer','text':'У роботов-пылесосов есть скрытая проблема'},
                     {'actor':'editor','decision':'REJECT','reason':'Безличная рекламная фраза, не показывает наблюдаемое действие.'},
                     {'actor':'writer','text':'Купили робота, а щетку опять чистить руками?'},
                     {'actor':'editor','decision':'SELF_REVIEW_ONLY','reason':'Ситуация конкретная, но проверить звучание отдельно.'}]}],
        'editorial_review':'SELF_REVIEW_ONLY', 'autonomous_agents_verified':False
    }

class IntegrationGateTests(unittest.TestCase):
    def test_realistic_pilot_remains_editorially_blocked(self):
        r=module.audit_integration_case(sample())
        self.assertEqual(r['release_status'],'PREVIEW_ONLY_SOURCE_AND_EDITORIAL_REVIEW_PENDING')
        self.assertEqual(r['usable_observations'],1)
        self.assertFalse(r['provenance_independently_attested'])
    def test_search_excerpt_never_counts_as_full_page(self):
        p=sample();p['sources'][0]['access']='SEARCH_EXCERPT_ONLY'
        r=module.audit_integration_case(p)
        self.assertEqual(r['usable_observations'],0)
        self.assertIn('observation_source_not_full_page',r['errors'])
    def test_missing_source_rejected(self):
        p=sample();p['observations'][0]['source_id']='imaginary'
        self.assertIn('observation_unknown_source',module.audit_integration_case(p)['errors'])
    def test_same_comment_from_duplicated_records_rejected(self):
        p=sample();p['observations'].append(copy.deepcopy(p['observations'][0]))
        self.assertIn('duplicate_observation',module.audit_integration_case(p)['errors'])
    def test_candidate_cannot_anchor_to_rejected_snippet(self):
        p=sample();p['sources'][0]['access']='SEARCH_EXCERPT_ONLY'
        r=module.audit_integration_case(p)
        self.assertIn('candidate_unanchored',r['errors'])

    def test_candidate_must_cite_voice_observation(self):
        p=sample();p['candidates'][0]['anchor_ids']=['O999']
        self.assertIn('candidate_unanchored',module.audit_integration_case(p)['errors'])
    def test_editor_only_self_scores_are_not_independent(self):
        p=sample();p['autonomous_agents_verified']=True
        self.assertIn('unverified_independence_claim',module.audit_integration_case(p)['errors'])
    def test_invalid_review_trace_is_rejected(self):
        p=sample();p['candidates'][0]['edits']=[{'actor':'writer','text':'Купили робота, а щетку опять чистить руками?'}]
        self.assertIn('missing_natural_speech_editor_loop',module.audit_integration_case(p)['errors'])
    def test_hook_not_equal_last_edited_version_rejected(self):
        p=sample();p['candidates'][0]['hook']='Другая фраза'
        self.assertIn('hook_not_last_approved_draft',module.audit_integration_case(p)['errors'])
    def test_same_source_many_authors_is_one_discussion(self):
        p=sample()
        for i in range(19):
            d=copy.deepcopy(p['observations'][0]);d['id']=f'X{i}';d['speaker_id']=f'user{i}';d['situation']+=str(i);p['observations'].append(d)
        r=module.audit_integration_case(p)
        self.assertEqual(r['distinct_discussions'],1)
        self.assertEqual(r['voice_confidence'],'LOW_SINGLE_DISCUSSION')
    def test_no_non_russian_scope_for_russian_task(self):
        p=sample();p['observations'][0]['situation']='The brush gets full of hair and requires cleaning after each run.'
        self.assertIn('observation_not_target_language',module.audit_integration_case(p)['errors'])
    def test_fake_url_domain_rejected(self):
        p=sample();p['sources'][0]['url']='https://malicious.example/reader'
        self.assertIn('invalid_source_url',module.audit_integration_case(p)['errors'])
    def test_source_access_unattested_even_if_marked_open(self):
        p=sample();p['sources'][0]['access']='FULL_PAGE_OPENED';p['sources'][0]['capture_ref']='turn999view999'
        r=module.audit_integration_case(p)
        self.assertFalse(r['provenance_independently_attested'])

if __name__=='__main__':unittest.main()
