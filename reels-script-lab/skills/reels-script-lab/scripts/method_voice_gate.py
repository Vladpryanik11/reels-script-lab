#!/usr/bin/env python3
"""Check a *handoff* between hook craft and the separate natural-language editor.

Not an LLM, not a formula-quality judge, not a source fetcher, not a human-review
attestation. Sources and formula IDs are versioned editorial references.
"""
from __future__ import annotations
import json
import argparse

APPROVED_SOURCES={
 'SMMBOT-WHAT','SMMBOT-FORMULA','SMMBOT-REELS-17',
 'CONTENTFORMAT-HOOK','POSTIUM-SCRIPT','USER-APPROVED-CATALOG',
}
# IDs are our paraphrased hook *mechanisms*, never copyrighted text templates.
FORMULAS={
 'CURIOSITY_GAP','CONCRETE_QUESTION','CONTRAST','CASE_STORY',
 'REAL_PROOF','SPECIFIC_VALUE','DIRECT_CHALLENGE','MISTAKE',
 'NUMBERED_PROMISE','VISUAL_VERBAL','IDENTITY_ADDRESS','OPEN_LOOP',
}
VALID_REVIEWS={'NOT_RUN','SELF_REVIEW_ONLY','REJECTED','INDEPENDENT_REVIEW_PENDING'}
VALID_VOICE={'SOURCE_INSUFFICIENT','UNAVAILABLE','STRUCTURALLY_READY_EDITORIAL_PENDING','PARTIAL_SNIPPETS_ONLY','VERIFIED'}


def audit_method_voice(packet: dict) -> dict:
    e=[];w=[]
    if not isinstance(packet,dict):return {'errors':['invalid_packet'],'warnings':[],'release_status':'BLOCKED_STRUCTURE'}
    if packet.get('version')!='0.8.1':e.append('invalid_contract_version')
    brief=packet.get('brief') or {}
    if any(not str(brief.get(k,'')).strip() for k in ('topic','audience','industry')):
        e.append('brief_missing')
    m=packet.get('methodology') or {}
    if m.get('authority')!='USER_SUPPLIED_HOOK_REFERENCES':e.append('method_authority_mismatch')
    if m.get('source_id') not in APPROVED_SOURCES:e.append('unapproved_methodology_source')
    if m.get('formula_id') not in FORMULAS:e.append('unregistered_formula')
    if not all(str(m.get(k,'')).strip() for k in ('draft','viewer_question','payoff_contract','first_frame')):
        e.append('hook_promise_missing')
    mr=packet.get('method_review') or {}
    if mr.get('status') not in VALID_REVIEWS:e.append('unauthenticated_method_review')
    if mr.get('status')=='NOT_RUN':w.append('method_review_not_run')
    if mr.get('formula_id')!=m.get('formula_id') or not str(mr.get('reason','')).strip():
        e.append('method_review_incomplete')
    language=packet.get('language') or {}
    if language.get('authority')!='REAL_RUSSIAN_SPEECH':e.append('language_authority_mismatch')
    if 'formula_id' in language or 'hook_strategy' in language or 'hook_candidates' in language:
        e.append('voice_formula_authority_leak')
    if language.get('status') not in VALID_VOICE:e.append('invalid_voice_status')
    # A string in JSON saying VERIFIED is not proof of web access.
    if language.get('status')=='VERIFIED':e.append('voice_verified_without_sources')
    if language.get('status') in ('UNAVAILABLE','SOURCE_INSUFFICIENT','PARTIAL_SNIPPETS_ONLY'):
        w.append('voice_unverified')
    ve=packet.get('voice_edit') or {}
    if ve.get('before')!=m.get('draft'):e.append('voice_received_wrong_hook')
    if not isinstance(ve.get('after'),str) or not ve.get('after','').strip():e.append('voice_edit_missing')
    if ve.get('meaning_changed') is not False:e.append('voice_changed_hook_mechanism')
    ids=language.get('observation_ids') or []
    used=ve.get('source_observation_ids') or []
    if not isinstance(ids,list) or not isinstance(used,list) or any(u not in ids for u in used):
        e.append('voice_observation_reference_missing')
    if packet.get('final_hook')!=ve.get('after'):e.append('final_hook_mismatch')
    r=packet.get('post_edit_method_review') or {}
    if r.get('status') not in ('SELF_REVIEW_ONLY','INDEPENDENT_REVIEW_PENDING') or not r.get('reason') or r.get('formula_id')!=m.get('formula_id'):
        e.append('post_voice_method_review_missing')
    if r.get('promise_preserved') is not True or r.get('first_frame_compatible') is not True:
        e.append('post_voice_promise_not_confirmed')
    if packet.get('release_status')!='PREVIEW_ONLY':e.append('unattested_release_claim')
    return {'errors':sorted(set(e)),'warnings':sorted(set(w)),
            'release_status':'BLOCKED_STRUCTURE' if e else 'PREVIEW_ONLY',
            'independent_review_verified':False,
            'meaning':'Static handoff validation only. No semantic verification, no independent AI review, no live source attestation.'}


def main():
    a=argparse.ArgumentParser();a.add_argument('path');opts=a.parse_args()
    with open(opts.path,encoding='utf8') as f:print(json.dumps(audit_method_voice(json.load(f)),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
