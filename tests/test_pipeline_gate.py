import copy
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parents[1] / 'reels-script-lab/skills/reels-script-lab/scripts'
spec=importlib.util.spec_from_file_location('pipeline_gate',SCRIPTS / 'pipeline_gate.py')
gate=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=gate
spec.loader.exec_module(gate)


def fixture(industry='retail', fact_mode='CREATIVE_NO_FACT_CLAIMS'):
    names=['A','B','C']; branches=[]
    for i,n in enumerate(names):
        hook=f'Вариант {n}: вы открыли коробку, а внутри лежит совсем не то, что ожидали?'
        rehook=f'А что вы заметите, если посмотреть на упаковку вторым взглядом — версия {n}?'
        cta=f'Расскажите, случалось ли с вами подобное — версия {n}.'
        lines=[hook,'Смотрите на деталь: коробка внушительная, а сам предмет помещается на ладони.',rehook,'На коробке изображён крупный предмет, но масштаб фотографии ничем не обозначен.',cta]
        branches.append({'id':n,'angle':f'{n}: смотрим на упаковку с другой стороны',
                         'hook':{'text':hook,'locked_sha256':hashlib.sha256(hook.encode()).hexdigest()},
                         'structure':{'name':f'object arc {n}', 'structure_id':('SRC-04','SRC-02','SRC-05')[i],
                             'methodology_source_id':'SMMPLANNER-7-STRUCTURES',
                             'fit_reason':'Сцены можно показать как условный пример, не приписывая товарам реальных свойств',
                             'excluded_structures':['SRC-03'], 'case_kind':'illustrative',
                             'narrative_route':('Осмотр вещи через упаковку','Опровергаем ожидание от размера фото','Ироничная неправильная инструкция покупки')[i],
                             'reveal_map':{'before_rehook':'Коробка большая','withheld':'Как оценить масштаб','at_payoff':'Показать масштаб честно'},
                             'beats':['HOOK','DEVELOPMENT','REHOOK','PAYOFF','CTA'],
                             **({'object_anchor':{'object':'коробка','appearances':['HOOK','DEVELOPMENT','PAYOFF']}} if i==0 else {}),
                             **({'expectation_reversal':{'expected':'Большое фото = большой предмет',
                                 'supported_alternative':'Рисунок на упаковке не показывает масштаб'}} if i==1 else {}),
                             **({'irony_context':'Ирония на ошибку оценивать физический размер по рекламному фото'} if i==2 else {})},
                         'rehook':{'text':rehook,'viewer_question':f'Как заметить подвох — вариант {n}?', 'payoff_line_index':3,
                         'technique_id':('TR-05','TR-02','TR-03')[i],
                         'methodology_source_id':'TATAM-HOOK-REHOOK',
                         'specific_pivot':'Размер упаковки и предмета различаются',
                         'next_beat':'Показать предмет рядом с коробкой и уточнить масштаб'},
                         'script':{'lines':lines},'cta':{'text':cta},
                         'reviews':{'hook':'NOT_RUN','structure':'NOT_RUN','rehook':'NOT_RUN','script':'NOT_RUN','cta':'NOT_RUN','final':'NOT_RUN'}})
    return {'contract_version':'0.7.0', 'brief':{'topic':'Непропорциональная упаковка','audience':'покупатели','industry':industry,
            'goal':'discussion','duration_sec':30,'profile':'universal'},
            'voice':{'status':'SOURCE_INSUFFICIENT','real_world_provenance_attested':False},
            'facts':{'mode':fact_mode,'claims':[], 'rationale':'Сюжет — личное впечатление без проверяемых чисел'},
            'branches':branches,'review_runtime':{'independent_agents_ran':False,'external_human_scores':False}}


class PipelineTests(unittest.TestCase):
    def test_complete_fixture_is_structural_only(self):
        d=gate.audit_pipeline(fixture())
        self.assertTrue(d['structurally_complete'],d)
        self.assertEqual(d['release_status'],'BLOCKED_EDITORIAL_AND_SOURCE_REVIEW')

    def test_three_independent_angles_required(self):
        data=fixture(); data['branches'][1]['angle']=data['branches'][0]['angle']
        self.assertFalse(gate.audit_pipeline(data)['structurally_complete'])

    def test_requires_three_branches(self):
        data=fixture(); data['branches'].pop()
        self.assertFalse(gate.audit_pipeline(data)['structurally_complete'])

    def test_hook_changed_after_lock(self):
        data=fixture(); data['branches'][0]['hook']['text']+='новое'
        self.assertFalse(gate.audit_pipeline(data)['structurally_complete'])

    def test_hook_script_text_must_match(self):
        data=fixture(); data['branches'][0]['script']['lines'][0]='изменено'
        self.assertFalse(gate.audit_pipeline(data)['structurally_complete'])

    def test_rehook_script_text_must_match(self):
        data=fixture(); data['branches'][0]['script']['lines'][2]='другой рехук'
        self.assertFalse(gate.audit_pipeline(data)['structurally_complete'])

    def test_cta_matches_last_line(self):
        data=fixture(); data['branches'][0]['script']['lines'][-1]='другое'
        self.assertFalse(gate.audit_pipeline(data)['structurally_complete'])

    def test_no_invented_independent_attestation(self):
        data=fixture(); data['review_runtime']['independent_agents_ran']=True
        d=gate.audit_pipeline(data)
        self.assertNotEqual(d['release_status'],'PRODUCTION_READY')
        self.assertIn('unverified_independent_review_claim',d['errors'])

    def test_factual_claims_require_evidence(self):
        data=fixture(fact_mode='FACT_CHECK_REQUIRED')
        data['facts']['claims']=[{'text':'Товар служит 10 лет','source_urls':[]}]
        self.assertFalse(gate.audit_pipeline(data)['structurally_complete'])

    def test_creative_claims_may_be_empty(self):
        self.assertTrue(gate.audit_pipeline(fixture(fact_mode='CREATIVE_NO_FACT_CLAIMS'))['structurally_complete'])

    def test_claim_source_url_required_and_https(self):
        data=fixture(fact_mode='SOURCE_CHECK_REQUIRED'); data['facts']['claims']=[{'text':'Для просмотра нужен билет','source_urls':['http://example.com']}]
        self.assertFalse(gate.audit_pipeline(data)['structurally_complete'])

    def test_review_statuses_not_self_approve(self):
        data=fixture(); data['branches'][0]['reviews']['hook']='PASS'
        d=gate.audit_pipeline(data)
        self.assertFalse(d['structurally_complete'])

    def test_five_niches_same_contract(self):
        for niche in ('saas','local-service','culture','product','education'):
            with self.subTest(niche=niche):
                self.assertTrue(gate.audit_pipeline(fixture(industry=niche))['structurally_complete'])

    def test_fact_mode_with_zero_claims_needs_explanation(self):
        d=fixture(fact_mode='FACT_CHECK_REQUIRED')
        self.assertFalse(gate.audit_pipeline(d)['structurally_complete'])

    def test_payoff_before_rehook_rejected(self):
        d=fixture(); d['branches'][0]['rehook']['payoff_line_index']=1
        self.assertFalse(gate.audit_pipeline(d)['structurally_complete'])

    def test_invalid_version(self):
        data=fixture(); data['contract_version']='0.5.1'
        self.assertFalse(gate.audit_pipeline(data)['structurally_complete'])


if __name__=='__main__':unittest.main()