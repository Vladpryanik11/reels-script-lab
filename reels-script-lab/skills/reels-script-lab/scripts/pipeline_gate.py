#!/usr/bin/env python3
"""Offline structural validator. Never independently certifies voice, research, or model review."""
from __future__ import annotations
import argparse
import hashlib
import json
from urllib.parse import urlsplit

STAGES=('hook','structure','rehook','script','cta','final')
# IDs designate our operational adaptation of original educational material.
STRUCTURE_IDS={f'SRC-{i:02d}' for i in range(1,8)}
REHOOK_IDS={f'TR-{i:02d}' for i in range(1,7)}
SMMPLANNER_ID='SMMPLANNER-7-STRUCTURES'
TATAM_ID='TATAM-HOOK-REHOOK'
# Known exact filler strings are smoke-test guards; other semantic failures need human review.
EMPTY_REHOOKS={'но есть один нюанс!','а самое интересное впереди!','но самое интересное впереди!','смотрите до конца!'}
EMPTY_DEVELOPMENT={'сегодня разберём это.','сегодня поговорим об этом.','давайте разберёмся.','а теперь подробнее.'}

def _normal(v):
    return ' '.join(v.strip().casefold().split()) if isinstance(v,str) else ''

def _filled(v):
    return isinstance(v,str) and bool(v.strip())

FACT_MODES={'FACT_CHECK_REQUIRED','SOURCE_CHECK_REQUIRED','CREATIVE_NO_FACT_CLAIMS','USER_VERIFIED_CLAIMS'}

def _sha256(v): return hashlib.sha256(v.encode('utf-8')).hexdigest()

def audit_pipeline(d: dict) -> dict:
    errors=[];warnings=[]
    if not isinstance(d,dict):return {'structurally_complete':False,'release_status':'BLOCKED_STRUCTURE','errors':['bad_root'],'warnings':[]}
    if d.get('contract_version')!='0.7.0':errors.append('invalid_contract_version')
    b=d.get('brief') or {}
    for key in ('topic','audience','industry','goal','profile'):
        if not str(b.get(key,'')).strip():errors.append('brief_missing_'+key)
    duration=b.get('duration_sec',0)
    if not isinstance(duration,(float,int)) or not 5<=duration<=180:errors.append('bad_duration')
    facts=d.get('facts') or {}; mode=facts.get('mode')
    if mode not in FACT_MODES:errors.append('invalid_fact_mode')
    if mode=='CREATIVE_NO_FACT_CLAIMS' and facts.get('claims'):
        errors.append('creative_mode_contains_factual_claims')
    if mode in ('FACT_CHECK_REQUIRED','SOURCE_CHECK_REQUIRED'):
        if not facts.get('claims'): errors.append('fact_mode_requires_claims')
        for c in facts.get('claims',[]):
            if not c.get('text') or not c.get('source_urls') or not all(
                isinstance(url,str) and urlsplit(url).scheme=='https' and urlsplit(url).hostname
                for url in c['source_urls']):errors.append('fact_claim_missing_valid_source')
    branches=d.get('branches')
    if not isinstance(branches,list) or len(branches)!=3:errors.append('requires_exactly_three_branches');branches=[]
    ids=[];angles=[];narrative_routes=[]
    for branch in branches:
        if not isinstance(branch,dict):errors.append('branch_not_object');continue
        vid=branch.get('id');ids.append(vid);angles.append(str(branch.get('angle','')).casefold().strip())
        if vid not in ('A','B','C'):errors.append('invalid_branch_id')
        if not branch.get('angle'):errors.append('missing_angle')
        hook=branch.get('hook') or {};ht=hook.get('text','')
        if not ht or hook.get('locked_sha256')!=_sha256(ht):errors.append('hook_lock_mismatch')
        structure=branch.get('structure') or {}
        beats=structure.get('beats') or []
        if not structure.get('name') or not isinstance(beats,list) or not all(t in beats for t in ['HOOK','DEVELOPMENT','REHOOK','PAYOFF','CTA']):
            errors.append('missing_structure_beats')
        elif len(set(beats))!=len(beats) or [beats.index(t) for t in ('HOOK','DEVELOPMENT','REHOOK','PAYOFF','CTA')] != sorted(beats.index(t) for t in ('HOOK','DEVELOPMENT','REHOOK','PAYOFF','CTA')):
            errors.append('wrong_beat_order')
        sid=structure.get('structure_id')
        if sid not in STRUCTURE_IDS or structure.get('name') in ('UNKNOWN_STRUCT_XYZ','generic repeat'):
            errors.append('invalid_structure_id')
        if structure.get('methodology_source_id') != SMMPLANNER_ID:
            errors.append('structure_source_missing')
        if not _filled(structure.get('fit_reason')):
            errors.append('missing_structure_fit_reason')
        if not isinstance(structure.get('excluded_structures'),list) or not structure.get('excluded_structures'):
            errors.append('missing_excluded_structures')
        rm=structure.get('reveal_map') or {}
        if not isinstance(rm,dict) or any(not _filled(rm.get(k)) for k in ('before_rehook','withheld','at_payoff')):
            errors.append('missing_reveal_map')
        route=_normal(structure.get('narrative_route'))
        if not route:
            errors.append('missing_narrative_route')
        narrative_routes.append(route)
        if structure.get('case_kind') not in ('illustrative','real','non_case'):
            errors.append('case_kind_missing')
        # Specific *evidence and staging* requirements: these assert fields only,
        # never certify that the scene will really be filmed or that its claims are true.
        if sid=='SRC-01':
            result=structure.get('result_anchor') or {}
            if not (_filled(result.get('visible_result')) and result.get('kind') in ('documented','illustrative')):
                errors.append('result_story_missing_result')
        if sid=='SRC-02':
            ev=structure.get('expectation_reversal') or {}
            if not (_filled(ev.get('expected')) and _filled(ev.get('supported_alternative'))):
                errors.append('reversal_missing_evidence')
        if sid=='SRC-03':
            steps=structure.get('investigation_steps') or []
            if not isinstance(steps,list) or len(steps)<2 or any(not isinstance(st,dict) or
                not all(_filled(st.get(k)) for k in ('observation','check','finding')) for st in steps):
                errors.append('microdetective_missing_investigation')
        if sid=='SRC-04':
            obj=structure.get('object_anchor') or {}
            if not _filled(obj.get('object')) or not isinstance(obj.get('appearances'),list) or not {'HOOK','DEVELOPMENT','PAYOFF'}.issubset(set(obj.get('appearances') or [])):
                errors.append('object_not_repeated')
        if sid=='SRC-05' and not _filled(structure.get('irony_context')):
            errors.append('reverse_instruction_missing_irony_context')
        if sid=='SRC-06':
            tr=structure.get('parallel_tracks') or {}
            if tr.get('same_start_conditions') is not True or len(tr.get('tracks') or [])!=2 or len(set(map(str,tr.get('tracks') or [])))!=2:
                errors.append('parallel_unfair_comparison')
        if sid=='SRC-07':
            ep=structure.get('episode_anchor') or {}
            if not (_filled(ep.get('in_media_res')) and _filled(ep.get('resolution'))):
                errors.append('in_media_res_episode_missing')
        rehook=branch.get('rehook') or {};rh=rehook.get('text','')
        if rehook.get('technique_id') is None:errors.append('missing_rehook_technique')
        elif rehook.get('technique_id') not in REHOOK_IDS:errors.append('invalid_rehook_technique')
        if rehook.get('methodology_source_id')!=TATAM_ID:errors.append('rehook_source_missing')
        if not _filled(rehook.get('next_beat')):errors.append('missing_rehook_next_beat')
        if not _filled(rehook.get('specific_pivot')):errors.append('missing_rehook_specific_pivot')
        if _normal(rh) in EMPTY_REHOOKS:errors.append('generic_rehook_requires_review')
        if not rh or not rehook.get('viewer_question'):errors.append('missing_rehook_curiosity')
        lines=(branch.get('script') or {}).get('lines') or []
        if not isinstance(lines,list) or len(lines)<4 or any(not isinstance(x,str) or not x.strip() for x in lines):
            errors.append('missing_script_lines');lines=[]
        if len(lines)>1 and _normal(lines[1]) in EMPTY_DEVELOPMENT:
            errors.append('placeholder_development_requires_review')
        if not lines or lines[0]!=ht:errors.append('hook_changed_in_script')
        if not lines or rh not in lines[1:-1]:errors.append('rehook_changed_in_script')
        payoff_index=rehook.get('payoff_line_index')
        has_future_payoff=(
            isinstance(payoff_index,int) and bool(lines) and rh in lines
            and 0 <= payoff_index < len(lines) and payoff_index > lines.index(rh)
        )
        if not has_future_payoff:
            errors.append('missing_future_payoff')
        ct=(branch.get('cta') or {}).get('text','')
        if not ct or not lines or lines[-1]!=ct:errors.append('cta_mismatch')
        reviews=branch.get('reviews') or {}
        if any(reviews.get(stage) not in ('NOT_RUN','REJECTED','SELF_REVIEW_ONLY','INDEPENDENT_REVIEW_PENDING') for stage in STAGES):
            errors.append('unattested_review_status')
        if lines and isinstance(duration,(int,float)) and duration>0:
            count=sum(len(line.split()) for line in lines)
            approx=count/2.5
            if approx>duration*1.35 or approx<duration*0.45:
                warnings.append(f'{vid}_spoken_timing_needs_human_check_{approx:.1f}s')
    if len(narrative_routes)==3 and all(narrative_routes) and len(set(narrative_routes))!=3:
        errors.append('duplicate_narrative_route')
    if len(set(ids))!=len(ids) or set(ids)!={'A','B','C'}:errors.append('branch_ids_not_unique')
    if len(set(angles))!=len(angles):errors.append('angles_not_independent')
    review=d.get('review_runtime') or {}
    if review.get('independent_agents_ran') or review.get('external_human_scores'):
        errors.append('unverified_independent_review_claim')
    if d.get('voice',{}).get('status')!='STRUCTURALLY_READY_EDITORIAL_PENDING':warnings.append('audience_voice_unverified_or_insufficient')
    return {'structurally_complete':not errors,
            'release_status':'BLOCKED_EDITORIAL_AND_SOURCE_REVIEW' if not errors else 'BLOCKED_STRUCTURE',
            'errors':sorted(set(errors)), 'warnings':warnings,
            'independent_review_verified':False,
            'meaning':'Methodology field and placeholder checks only. A successful check is NOT proof the drama, live sources or reviewers genuinely ran.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('file');args=p.parse_args()
    with open(args.file,encoding='utf-8') as f:d=json.load(f)
    print(json.dumps(audit_pipeline(d),ensure_ascii=False,indent=2))

if __name__=='__main__': main()