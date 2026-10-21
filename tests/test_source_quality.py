import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'reels-script-lab/skills/reels-script-lab/scripts'
spec = importlib.util.spec_from_file_location('audience_sources', HERE / 'audience_sources.py')
sources = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sources
spec.loader.exec_module(sources)


def record(i=0, **kw):
    d = {'platform':'pikabu', 'url':f'https://pikabu.ru/story/longstory_{i}', 'source_id':str(i),
         'author_id':f'author{i}', 'kind':'user_comment', 'text':f'Каждую пятницу иду на встречу и снова забываю блокнот номер {i}',
         'captured_at':'2026-10-20T13:00:00+03:00', 'capture_mode':'web_open',
         'access_level':'full_text', 'retrieval_ref':f'turn{i}fetch0'}
    d.update(kw)
    return d


class SourceQualityTests(unittest.TestCase):
    def test_sufficiency_is_not_claim_of_authenticity(self):
        d = sources.build_voice_dossier([record(i) for i in range(6)], min_records=5, min_authors=3)
        self.assertEqual(d['status'],'STRUCTURALLY_READY_EDITORIAL_PENDING')
        self.assertEqual(d['independent_review_status'],'NOT_RUN')
        self.assertFalse(d['real_world_provenance_attested'])

    def test_fake_date_fails(self):
        d = sources.build_voice_dossier([record(captured_at='not-a-date')],min_records=1,min_authors=1)
        self.assertEqual(d['usable_count'],0)
        self.assertIn('invalid_date',d['excluded_reasons'])

    def test_repeated_url_with_fake_authors_rejected(self):
        records = [record(i, url='https://pikabu.ru/story/same_1') for i in range(15)]
        d = sources.build_voice_dossier(records, min_records=10,min_authors=10)
        self.assertEqual(d['usable_count'],1)
        self.assertEqual(d['status'],'SOURCE_INSUFFICIENT')

    def test_multiple_comments_under_one_post_can_count_with_comment_id(self):
        records=[record(i,url='https://pikabu.ru/story/same',comment_id=f'c{i}') for i in range(4)]
        d=sources.build_voice_dossier(records,min_records=4,min_authors=4)
        self.assertEqual(d['usable_count'],4)

    def test_snippet_is_not_full_post(self):
        d=sources.build_voice_dossier([record(access_level='snippet')],min_records=1,min_authors=1)
        self.assertEqual(d['usable_count'],0)
        self.assertIn('not_full_text',d['excluded_reasons'])

    def test_short_natural_reply_can_count(self):
        d=sources.build_voice_dossier([record(text='Да, тоже так')],1,1)
        self.assertEqual(d['usable_count'],1)

    def test_one_russian_character_not_enough(self):
        d=sources.build_voice_dossier([record(text='A big long paragraph mostly in English with я')],min_records=1,min_authors=1)
        self.assertEqual(d['usable_count'],0)
        self.assertIn('not_russian_text',d['excluded_reasons'])

    def test_ad_not_counted(self):
        d=sources.build_voice_dossier([record(kind='advertisement')],min_records=1,min_authors=1)
        self.assertEqual(d['usable_count'],0)

    def test_platform_domain_mismatch(self):
        d=sources.build_voice_dossier([record(url='https://example.com/phony')],min_records=1,min_authors=1)
        self.assertEqual(d['usable_count'],0)
        self.assertIn('platform_domain_mismatch',d['excluded_reasons'])

    def test_duplicate_text_removed_across_urls(self):
        a=record(0); b=record(1,text=a['text'])
        d=sources.build_voice_dossier([a,b],min_records=2,min_authors=2)
        self.assertEqual(d['usable_count'],1)

    def test_requires_capture_ref(self):
        d=sources.build_voice_dossier([record(retrieval_ref='')],min_records=1,min_authors=1)
        self.assertEqual(d['usable_count'],0)

    def test_source_routing_uses_audience(self):
        a=sources.choose_sources('Как выбрать CRM','разработчики SaaS','technology')
        b=sources.choose_sources('Как выбрать CRM','владельцы небольших салонов красоты','technology')
        self.assertNotEqual([x['platform'] for x in a['candidates'][:3]], [x['platform'] for x in b['candidates'][:3]])
        self.assertTrue(all(x['rationale'] for x in a['candidates']))

    def test_future_date_not_counted(self):
        d=sources.build_voice_dossier([record(captured_at='2099-01-01T00:00:00+03:00')],min_records=1,min_authors=1)
        self.assertEqual(d['usable_count'],0)
        self.assertIn('future_date',d['excluded_reasons'])

    def test_wrong_language_for_target_cannot_count(self):
        row=record(text='I often visit a community meeting on Fridays and forget my notes every single time')
        self.assertEqual(sources.build_voice_dossier([row],1,1,target_language='ru')['usable_count'],0)
        self.assertEqual(sources.build_voice_dossier([row],1,1,target_language='en')['usable_count'],1)

    def test_untrusted_language_label_not_enough(self):
        d=sources.build_voice_dossier([record(text='с')],min_records=1,min_authors=1)
        self.assertEqual(d['usable_count'],0)

    def test_bad_url_port_returns_exclusion_not_crash(self):
        d=sources.build_voice_dossier([record(url='https://pikabu.ru:broken/story')],1,1)
        self.assertEqual(d['usable_count'],0)
        self.assertIn('invalid_url',d['excluded_reasons'])

    def test_url_with_credentials_rejected(self):
        d=sources.build_voice_dossier([record(url='https://user:pass@pikabu.ru/story/a')],min_records=1,min_authors=1)
        self.assertEqual(d['usable_count'],0)


if __name__ == '__main__': unittest.main()