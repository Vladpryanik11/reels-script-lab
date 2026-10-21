#!/usr/bin/env python3
"""Reels Script Lab v0.4.1 — validate candidate generation and selection workflow.

This code checks contracts and routes selection outcomes, NOT creative merit.
Independent LLM/audience review requires a separate orchestration runtime.
"""
from __future__ import annotations
import re
from typing import Any

BRANCHES = {'A', 'B', 'C'}
TECHNIQUES = {f'TR-{i:02}' for i in range(1, 7)}


def nonblank(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def norm(x: str) -> str:
    return re.sub(r'[^\w]+', ' ', x.casefold()).strip()


def assess_selection(packet: Any) -> dict:
    errors: list[str] = []
    blockers = ['REAL_INDEPENDENT_REVIEW_NOT_VERIFIED', 'UPSTREAM_ATTESTATIONS_NOT_VERIFIED']
    revise = False
    if not isinstance(packet, dict):
        return {'errors': ['ROOT_NOT_OBJECT'], 'blockers': blockers,
                'status': 'FAIL', 'production_status': 'BLOCKED'}
    if packet.get('version') != '0.4.1':
        errors.append('BAD_VERSION')
    generator_run_id = packet.get('generator_run_id')
    if not nonblank(generator_run_id):
        errors.append('RUN_ID_REQUIRED')
    if packet.get('mode') != 'preview' or packet.get('production_status') != 'BLOCKED':
        errors.append('PRODUCTION_FORGED')
    branches = packet.get('branches')
    if not isinstance(branches, dict) or set(branches) != BRANCHES:
        errors.append('BRANCHES_MUST_BE_A_B_C')
        branches = branches if isinstance(branches, dict) else {}
    for b in sorted(BRANCHES):
        v = branches.get(b)
        if not isinstance(v, dict):
            errors.append(f'{b}.BRANCH_MISSING')
            continue
        hook = v.get('hook_snapshot')
        for k in ('hook_snapshot', 'before_rehook', 'next_beat', 'remaining_payoff'):
            if not nonblank(v.get(k)):
                errors.append(f'{b}.{k.upper()}_REQUIRED')
        candidates = v.get('candidates')
        if not isinstance(candidates, list) or len(candidates) < 6:
            errors.append(f'{b}.CANDIDATES_TOO_FEW')
            candidates = candidates if isinstance(candidates, list) else []
        if len(candidates) > 9:
            errors.append(f'{b}.CANDIDATES_TOO_MANY')
        candidate_ids: set[str] = set()
        candidate_texts: set[str] = set()
        techniques: set[str] = set()
        for c in candidates:
            if not isinstance(c, dict):
                errors.append(f'{b}.INVALID_CANDIDATE')
                continue
            cid, txt, technique = c.get('id'), c.get('text'), c.get('technique_id')
            if not nonblank(cid) or cid in candidate_ids:
                errors.append(f'{b}.DUPLICATE_OR_EMPTY_ID')
            else:
                candidate_ids.add(cid)
            if not nonblank(txt):
                errors.append(f'{b}.EMPTY_CANDIDATE')
            else:
                if norm(txt) in candidate_texts:
                    errors.append(f'{b}.DUPLICATE_CANDIDATE')
                candidate_texts.add(norm(txt))
                if nonblank(hook) and norm(txt)==norm(hook):
                    errors.append(f'{b}.HOOK_REPEATED')
            if technique not in TECHNIQUES:
                errors.append(f'{b}.INVALID_TECHNIQUE')
            else:
                techniques.add(technique)
            for field in ('pivot', 'audience_detail', 'expected_next_beat'):
                if not nonblank(c.get(field)):
                    errors.append(f'{b}.CANDIDATE_MISSING_{field.upper()}')
        if len(techniques) < 3:
            errors.append(f'{b}.LOW_MECHANISM_DIVERSITY')
        critic = v.get('critic')
        if not isinstance(critic, dict):
            errors.append(f'{b}.NO_CRITIC')
            critic = {}
        if not nonblank(critic.get('reviewer_run_id')):
            errors.append(f'{b}.REVIEWER_RUN_ID_MISSING')
        if nonblank(generator_run_id) and critic.get('reviewer_run_id')==generator_run_id:
            errors.append(f'{b}.SELF_REVIEW')
        if critic.get('blind_to_author_rationale') is not True:
            errors.append(f'{b}.REVIEW_NOT_BLIND')
        reports = critic.get('reports')
        if not isinstance(reports, list):
            errors.append(f'{b}.CANDIDATES_NOT_BLIND_REVIEWED')
            reports=[]
        reported_ids = [r.get('candidate_id') for r in reports if isinstance(r,dict)]
        if set(reported_ids) != candidate_ids or len(reported_ids) != len(candidate_ids):
            errors.append(f'{b}.CANDIDATES_NOT_BLIND_REVIEWED')
        by_id = {r.get('candidate_id'):r for r in reports if isinstance(r,dict) and nonblank(r.get('candidate_id'))}
        for cid, r in by_id.items():
            if r.get('verdict') not in ('PASS','REJECT'):
                errors.append(f'{b}.INVALID_REVIEW_VERDICT')
            if r.get('verdict')=='PASS':
                if not nonblank(r.get('inferred_viewer_question')):
                    errors.append(f'{b}.EMPTY_INFERRED_QUESTION')
                if not nonblank(r.get('specific_new_information')):
                    errors.append(f'{b}.NO_OBSERVABLE_NEW_INFORMATION')
                if not nonblank(r.get('next_beat_validation')):
                    errors.append(f'{b}.UNSUPPORTED_NEXT_BEAT')
                if r.get('issues') != []:
                    errors.append(f'{b}.PASS_WITH_ISSUES')
            else:
                if not isinstance(r.get('issues'), list) or not r.get('issues'):
                    errors.append(f'{b}.REJECT_WITHOUT_ISSUES')
        selection = v.get('selection')
        if not isinstance(selection, dict):
            errors.append(f'{b}.SELECTION_MISSING')
            continue
        status, selected = selection.get('status'), selection.get('candidate_id')
        if status == 'REVIEWED':
            if selected not in candidate_ids or by_id.get(selected,{}).get('verdict')!='PASS':
                errors.append(f'{b}.SELECTED_NOT_PASSED')
        elif status in ('NEEDS_REGENERATION','NEEDS_STRUCTURE_REVISION'):
            revise=True
            if selected is not None:
                errors.append(f'{b}.REJECTED_BRANCH_MUST_NOT_SELECT_CANDIDATE')
        else:
            errors.append(f'{b}.UNKNOWN_SELECTION_STATUS')
    status = 'FAIL' if errors else ('NEEDS_REVISION' if revise else 'STRUCTURALLY_READY')
    return {'errors': errors, 'blockers': blockers,'status': status,'production_status':'BLOCKED',
            'note':'Field-level validation only. Reviewer run IDs are declarative and do not prove independence; actual quality and approvals remain unverified.'}