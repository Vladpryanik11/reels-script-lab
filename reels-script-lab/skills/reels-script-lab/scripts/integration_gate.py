#!/usr/bin/env python3
"""Validate source-to-hook trace of a real-web pilot without granting authority to authored JSON.

Does not fetch URLs. Text from outside is untrusted. Even a passing structural
trace MUST remain preview-only: the local file cannot attest external web access
or an independent human/model reviewer.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta, timezone
import argparse
import json
import re
from urllib.parse import urlsplit

VALID_DOMAINS={
 'habr':('habr.com','habr.ru'),
 'reddit':('reddit.com','redd.it'),
 'pikabu':('pikabu.ru',),
 'woman':('woman.ru',),
 'vc':('vc.ru',),
 'otvet_mail':('otvet.mail.ru',),
 'threads':('threads.net','threads.com'),
 'vk':('vk.com','vk.ru'),
 'telegram':('t.me',)
}
CAPTURE_REF=re.compile(r'^turn\d+(?:view|fetch)\d+$')


def _valid_url(url, platform):
    try:
        p=urlsplit(url)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443):return False
        host=p.hostname.casefold().rstrip('.')
        return any(host==d or host.endswith('.'+d) for d in VALID_DOMAINS.get(platform,()))
    except (TypeError, ValueError):
        return False


def _date_ok(value):
    try:
        dt=datetime.fromisoformat(value)
        return (dt.tzinfo is not None and dt.utcoffset() is not None and
                dt<=datetime.now(timezone.utc)+timedelta(days=1))
    except (ValueError, TypeError):return False


def _russian(s):
    # Shallow script guard; not semantic language or audience verification.
    letters=[c for c in s if c.isalpha()]
    return len(letters)>=20 and sum('а'<=c.casefold()<='я' or c.casefold()=='ё' for c in letters)/len(letters)>=.68


def audit_integration_case(case):
    errors=[];warnings=[]
    if not isinstance(case,dict):
        return dict(release_status='BLOCKED_STRUCTURE',errors=['invalid_case'],warnings=[],
                    usable_observations=0,distinct_discussions=0,voice_confidence='NONE',provenance_independently_attested=False)
    if case.get('contract_version')!='0.8.0':errors.append('invalid_contract_version')
    brief=case.get('brief') or {}
    for key in ('topic','audience','industry','goal'):
        if not isinstance(brief.get(key),str) or not brief[key].strip():errors.append('brief_missing_'+key)
    known_sources={};distinct_discussions=set()
    for source in case.get('sources') or []:
        sid=source.get('id')
        if not isinstance(sid,str) or not sid.strip() or sid in known_sources:
            errors.append('invalid_source_id');continue
        known_sources[sid]=source
        if not _valid_url(source.get('url'),source.get('platform')):errors.append('invalid_source_url')
        if not _date_ok(source.get('captured_at')):errors.append('invalid_capture_time')
        if not CAPTURE_REF.fullmatch(str(source.get('capture_ref',''))):errors.append('invalid_capture_ref')
        if source.get('access') not in ('FULL_PAGE_OPENED','SEARCH_EXCERPT_ONLY','UNAVAILABLE'):
            errors.append('invalid_source_access')
        if source.get('source_kind') not in ('discussion','article','comment_thread','post'):
            errors.append('invalid_source_kind')
    seen_ids=set();usable_ids=set();seen_records=set();usable=0;unique_authors=set()
    for ob in case.get('observations') or []:
        if not isinstance(ob,dict):errors.append('invalid_observation');continue
        oid=ob.get('id');sid=ob.get('source_id')
        if not isinstance(oid,str) or not oid or oid in seen_ids:errors.append('duplicate_observation');continue
        seen_ids.add(oid)
        source=known_sources.get(sid)
        if source is None:errors.append('observation_unknown_source');continue
        if source.get('access')!='FULL_PAGE_OPENED':errors.append('observation_source_not_full_page');continue
        if not _valid_url(source.get('url'),source.get('platform')):continue
        if not _russian(str(ob.get('situation',''))):errors.append('observation_not_target_language');continue
        if ob.get('kind') not in ('user_comment','user_post','firsthand_review','first_person_article'):
            errors.append('invalid_observation_kind');continue
        author=str(ob.get('speaker_id','')).strip()
        if not author:errors.append('observation_missing_author');continue
        if not str(ob.get('voice_signal','')).strip() or not str(ob.get('audience_fit','')).strip():
            errors.append('observation_context_missing');continue
        identity=(sid,author,re.sub(r'\W','',str(ob['situation'])).casefold())
        if identity in seen_records:errors.append('duplicate_observation');continue
        seen_records.add(identity);usable_ids.add(oid);usable+=1;distinct_discussions.add(sid);unique_authors.add((sid,author))
    candidates=case.get('candidates') or []
    if not candidates:errors.append('missing_candidates')
    for c in candidates:
        if not isinstance(c,dict):errors.append('invalid_candidate');continue
        anchors=c.get('anchor_ids') or []
        if not isinstance(anchors,list) or not anchors or any(a not in usable_ids for a in anchors):
            errors.append('candidate_unanchored')
        edits=c.get('edits') or []
        writers=[e for e in edits if isinstance(e,dict) and e.get('actor')=='writer' and str(e.get('text','')).strip()]
        editors=[e for e in edits if isinstance(e,dict) and e.get('actor')=='editor' and e.get('decision') in ('REJECT','SELF_REVIEW_ONLY')
                 and len(str(e.get('reason','')).strip())>=25]
        if len(writers)<2 or not editors or not any(e.get('decision')=='REJECT' for e in editors):
            errors.append('missing_natural_speech_editor_loop')
        if not writers or c.get('hook')!=writers[-1]['text']:
            errors.append('hook_not_last_approved_draft')
        if not isinstance(c.get('angle'),str) or not c['angle'].strip():errors.append('missing_angle')
    if case.get('autonomous_agents_verified') or case.get('editorial_review') not in ('NOT_RUN','SELF_REVIEW_ONLY','REJECTED'):
        errors.append('unverified_independence_claim')
    if not known_sources:errors.append('missing_sources')
    n=len(distinct_discussions)
    confidence='LOW_SINGLE_DISCUSSION' if n==1 else 'PRELIMINARY_MULTISOURCE' if n>1 else 'NONE'
    if n<3 or usable<15 or len(unique_authors)<10:
        warnings.append('source_corpus_below_editorial_diversity_threshold')
    return {'release_status':'BLOCKED_STRUCTURE' if errors else 'PREVIEW_ONLY_SOURCE_AND_EDITORIAL_REVIEW_PENDING',
            'errors':sorted(set(errors)),'warnings':warnings,
            'usable_observations':usable,'distinct_discussions':n,'unique_speakers':len(unique_authors),
            'voice_confidence':confidence,'provenance_independently_attested':False,
            'independent_review_verified':False,
            'meaning':'Static trace only; browser/tool results must be verified by the executing host. This is NOT approval for publication.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('case_json');arg=p.parse_args()
    with open(arg.case_json,encoding='utf-8') as f:case=json.load(f)
    print(json.dumps(audit_integration_case(case),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
