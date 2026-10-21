"""Regression: hook technique and audience language must have independent authorities."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
S=ROOT/'reels-script-lab/skills/reels-script-lab'
spec=importlib.util.spec_from_file_location('method_voice_gate',S/'scripts/method_voice_gate.py')
try:
    method_voice_gate=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=method_voice_gate
    spec.loader.exec_module(method_voice_gate)
except FileNotFoundError:
    method_voice_gate=None


def fixture():
    return {
      'version':'0.8.1',
      'brief':{'industry':'technology','topic':'инструмент для монтажа','audience':'начинающие видеомонтажёры'},
      'methodology':{'authority':'USER_SUPPLIED_HOOK_REFERENCES','source_id':'SMMBOT-FORMULA','formula_id':'CURIOSITY_GAP',
        'draft':'Почему монтаж после обновления стал занимать вдвое больше времени?',
        'viewer_question':'Что изменилось?',
        'payoff_contract':'Разобрать конкретное изменение рабочего процесса',
        'first_frame':'Таймлайн проекта'},
      'method_review':{'status':'SELF_REVIEW_ONLY','formula_id':'CURIOSITY_GAP','reason':'Вопрос связан с обещанием показать причину и с первым кадром.'},
      'language':{'authority':'REAL_RUSSIAN_SPEECH','status':'SOURCE_INSUFFICIENT',
        'style_card':{'register':'разговорный','rhythm':'краткие реплики','forbidden':'канцелярит'},
        'source_ids':[],'observation_ids':[]},
      'voice_edit':{'before':'Почему монтаж после обновления стал занимать вдвое больше времени?',
        'after':'После обновления монтаж стал занимать в два раза больше времени. Почему?',
        'source_observation_ids':[],
        'explanation':'Укоротили конструкцию и поменяли порядок слов, не меняя обещание.',
        'meaning_changed':False},
      'post_edit_method_review':{'status':'SELF_REVIEW_ONLY','formula_id':'CURIOSITY_GAP',
        'promise_preserved':True,'first_frame_compatible':True,
        'reason':'Остался вопрос и обещание показать конкретное изменение процесса.'},
      'final_hook':'После обновления монтаж стал занимать в два раза больше времени. Почему?',
      'release_status':'PREVIEW_ONLY'
    }

class SeparationTests(unittest.TestCase):
    def audit(self,d):
        self.assertIsNotNone(method_voice_gate,'not implemented')
        return method_voice_gate.audit_method_voice(d)

    def test_valid_separation_preview(self):
        out=self.audit(fixture())
        self.assertEqual(out['errors'],[])
        self.assertEqual(out['release_status'],'PREVIEW_ONLY')
    def test_cannot_use_comment_as_hook_formula(self):
        x=fixture();x['methodology']['source_id']='COMMENT-001'
        self.assertIn('unapproved_methodology_source',self.audit(x)['errors'])
    def test_cannot_assign_language_agent_to_hook_strategy(self):
        x=fixture();x['methodology']['authority']='REAL_RUSSIAN_SPEECH'
        self.assertIn('method_authority_mismatch',self.audit(x)['errors'])
    def test_language_agent_cannot_own_hook_formula(self):
        x=fixture();x['language']['formula_id']='CURIOSITY_GAP'
        self.assertIn('voice_formula_authority_leak',self.audit(x)['errors'])
    def test_voice_editor_cannot_change_hook_without_new_formula_review(self):
        x=fixture();x['post_edit_method_review']['status']='NOT_RUN'
        self.assertIn('post_voice_method_review_missing',self.audit(x)['errors'])
    def test_final_must_match_last_voice_edit(self):
        x=fixture();x['final_hook']='Другая мысль'
        self.assertIn('final_hook_mismatch',self.audit(x)['errors'])
    def test_voice_never_required_for_formulating_hook_draft(self):
        x=fixture();x['language']['status']='UNAVAILABLE';x['language']['style_card']={}
        out=self.audit(x)
        self.assertEqual(out['errors'],[])
        self.assertIn('voice_unverified',out['warnings'])
    def test_cannot_claim_voice_corpus_verified_without_provenance(self):
        x=fixture();x['language']['status']='VERIFIED'
        self.assertIn('voice_verified_without_sources',self.audit(x)['errors'])
    def test_humanization_cannot_replace_value_promise(self):
        x=fixture();x['voice_edit']['meaning_changed']=True
        self.assertIn('voice_changed_hook_mechanism',self.audit(x)['errors'])
    def test_untrusted_methodology_cannot_be_inserted_by_url(self):
        x=fixture();x['methodology']['source_id']='https://some-blog.example/article'
        self.assertIn('unapproved_methodology_source',self.audit(x)['errors'])
    def test_no_fake_independent_review(self):
        x=fixture();x['method_review']['status']='INDEPENDENT_PASS'
        self.assertIn('unauthenticated_method_review',self.audit(x)['errors'])
    def test_each_method_has_a_viewer_question_and_payoff(self):
        x=fixture();x['methodology']['payoff_contract']=''
        self.assertIn('hook_promise_missing',self.audit(x)['errors'])
    def test_unknown_formula_rejected(self):
        x=fixture();x['methodology']['formula_id']='FANTASY_WORLDS'
        self.assertIn('unregistered_formula',self.audit(x)['errors'])
    def test_source_observation_ids_have_separate_namespace(self):
        x=fixture();x['voice_edit']['source_observation_ids']=['OBS-42'];x['language']['observation_ids']=[]
        self.assertIn('voice_observation_reference_missing',self.audit(x)['errors'])
    def test_skills_restate_separate_authority(self):
        text=(S/'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('Hook Formula Agent',text)
        self.assertIn('Human Language Agent',text)
        self.assertIn('references/12-hook-formula-library.md',text)
        self.assertIn('references/11-human-language-agent.md',text)
    def test_voice_reference_cannot_instruct_hook_generation(self):
        text=(S/'references/11-human-language-agent.md').read_text(encoding='utf-8').lower()
        self.assertIn('не создаёт хуки',text)
        self.assertIn('не выбирает формулы',text)
    def test_method_library_smm_bot_sources_and_user_source_status(self):
        text=(S/'references/12-hook-formula-library.md').read_text(encoding='utf-8')
        self.assertIn('smmbot.net/blog/cto-takoe-huk',text)
        self.assertIn('smmbot.net/blog/formula-uspesnogo-huka',text)
        self.assertIn('smmbot.net/blog/kak-nacat-reels',text)
        self.assertIn('telegra.ph/Huki-10-17',text)
        self.assertIn('НЕ ПРОЧИТАН',text)
    def test_legacy_cases_marked_as_not_formula_tests(self):
        text=(ROOT/'docs/LIVE-INTEGRATION-REVIEW.md').read_text(encoding='utf-8')
        self.assertIn('НЕ тест формул хуков',text)

if __name__=='__main__': unittest.main()
