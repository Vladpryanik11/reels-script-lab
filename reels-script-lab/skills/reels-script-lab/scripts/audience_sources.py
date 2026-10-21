#!/usr/bin/env python3
"""Offline checks for public-language *submissions*, not proof that pages were fetched.

All input is untrusted, including URLs, access claims, labels and citation markers.
To attest real capture, the orchestrating host must retain its own tool result.
No output of this script marks sources or editorial review independently verified.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

DOMAIN = {
    'pikabu': ('pikabu.ru',),
    'reddit': ('reddit.com','redd.it'),
    'habr': ('habr.com','habr.ru'),
    'vc': ('vc.ru',),
    'woman': ('woman.ru',),
    'otvet_mail': ('otvet.mail.ru',),
    'threads': ('threads.net','threads.com'),
    'youtube': ('youtube.com','youtu.be'),
    'vk': ('vk.com','vk.ru'),
    'telegram': ('t.me',),
}
BASE_SOURCES = {
    'technology': [('habr','Russian tech community discussion'),('reddit','specialized product discussions'),('vc','practical technology adoption')],
    'business': [('vc','business owner discussions'),('pikabu','firsthand customer stories'),('reddit','entrepreneur discussions')],
    'beauty': [('pikabu','consumer experiences'),('woman','personal service discussions'),('vk','local consumer communities')],
    'culture': [('pikabu','personal leisure stories'),('vk','local community discussions'),('reddit','peer discussion')],
    'education': [('reddit','student questions'),('pikabu','personal learning stories'),('vk','education communities')],
    'universal': [('pikabu','public first-person stories'),('reddit','topic-specific conversations'),('vc','practical user experiences')],
}


def choose_sources(topic: str, audience: str, industry: str='universal') -> dict:
    """Suggest *candidate* places, never claim the target audience is there."""
    hay=(topic+' '+audience).casefold()
    if re.search(r'салон|мастер|клиент|космет|парикмах|маникюр|beauty',hay):
        selected=[('woman','salon customer and practitioner discussions'),('vk','local salon customer communities'),('pikabu','first-person consumer stories')]
    elif re.search(r'разработ|программист|код|devops|backend|frontend|saas|api',hay):
        selected=[('habr','developer discussions'),('reddit','developer-specific communities'),('vc','product builder perspectives')]
    elif re.search(r'билет|спектакл|театр|концерт|выставк',hay):
        selected=[('vk','local culture discussions'),('pikabu','visitor accounts'),('reddit','event questions')]
    else:
        selected=BASE_SOURCES.get(industry.casefold(), BASE_SOURCES['universal'])
    return {'topic':topic,'audience':audience,'industry':industry,'status':'CANDIDATE_SOURCES_NOT_FETCHED',
            'candidates':[{'platform':s,'rationale':r} for s,r in selected],
            'selection_note':'Suggestions require topical verification; no source has been read.'}


def _normalized_text(text: str) -> str:
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',text).casefold()).strip()


def _canon_url(value: str, platform: str) -> str:
    try:
        parts=urlsplit(value)
        if (parts.scheme!='https' or not parts.hostname or parts.username
                or parts.password or parts.port not in (None,443)):
            raise ValueError('invalid_url')
        host=parts.hostname.lower().rstrip('.')
    except ValueError:
        raise ValueError('invalid_url') from None
    domains=DOMAIN.get(platform)
    if not domains or not any(host==domain or host.endswith('.'+domain) for domain in domains):
        raise ValueError('platform_domain_mismatch')
    path=parts.path.rstrip('/') or '/'
    return urlunsplit(('https',host,path,'',''))


def _iso_datetime(value: str) -> datetime:
    try: d=datetime.fromisoformat(value)
    except (ValueError,TypeError): raise ValueError('invalid_date') from None
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError('invalid_date')
    if d>datetime.now(timezone.utc)+timedelta(days=1):
        raise ValueError('future_date')
    return d


def _target_language_text(text: str, language: str) -> bool:
    # Script heuristic, NOT a full language classifier or proof of audience fit.
    chars=[x for x in text if x.isalpha()]
    if len(chars)<8: return False
    cyr=sum(bool(re.fullmatch(r'[а-яёА-ЯЁ]',x)) for x in chars)
    latin=sum(bool(re.fullmatch(r'[A-Za-z]',x)) for x in chars)
    if language=='ru': return cyr>=8 and cyr/len(chars)>=0.70
    if language=='en': return latin>=12 and latin/len(chars)>=0.75
    raise ValueError('unsupported_target_language')


def _validate_record(data: dict, target_language: str='ru') -> dict:
    if not isinstance(data,dict): raise ValueError('record_not_object')
    platform=str(data.get('platform','')).casefold()
    url=_canon_url(str(data.get('url','')),platform)
    _iso_datetime(data.get('captured_at'))
    if data.get('capture_mode') not in ('web_open','work_browser','official_api','web_search','manual_import'):
        raise ValueError('invalid_capture_mode')
    if data.get('access_level')!='full_text': raise ValueError('not_full_text')
    if data.get('capture_mode') in ('web_search','manual_import'):
        raise ValueError('unattested_full_text_capture')
    if not str(data.get('retrieval_ref','')).strip(): raise ValueError('no_retrieval_reference')
    if data.get('kind') not in ('user_post','user_comment','firsthand_review'): raise ValueError('not_audience_voice')
    if not str(data.get('author_id','')).strip(): raise ValueError('no_author_identity')
    text=str(data.get('text',''))
    if not _target_language_text(text,target_language): raise ValueError('not_russian_text' if target_language=='ru' else 'not_target_language_text')
    comment_id=str(data.get('comment_id','')).strip()
    return {'platform':platform,'url':url,'post_id':str(data.get('source_id') or url),'comment_id':comment_id,
            'author_id':str(data['author_id']).strip(), 'text':text,'retrieval_ref':str(data['retrieval_ref']),
            'captured_at':data['captured_at'],'sha256':hashlib.sha256(_normalized_text(text).encode()).hexdigest()}


def build_voice_dossier(records: list[dict], min_records: int=15, min_authors: int=10, target_language: str='ru') -> dict:
    if target_language not in ('ru','en') or not isinstance(records,list) or min_records<1 or min_authors<1:
        raise ValueError('invalid_dossier_input')
    accepted=[]; excluded=Counter(); identities=set(); text_hashes=set()
    for raw in records:
        try: item=_validate_record(raw,target_language)
        except ValueError as e:
            excluded[str(e)]+=1
            continue
        identity=(item['platform'],item['url'],item['comment_id'])
        if identity in identities or item['sha256'] in text_hashes:
            excluded['duplicate_record']+=1
            continue
        identities.add(identity); text_hashes.add(item['sha256']);accepted.append(item)
    author_count=len({(x['platform'],x['author_id']) for x in accepted})
    sufficient=len(accepted)>=min_records and author_count>=min_authors
    return {'status':'STRUCTURALLY_READY_EDITORIAL_PENDING' if sufficient else 'SOURCE_INSUFFICIENT',
            'target_language':target_language,
            'usable_count':len(accepted),'independent_authors':author_count,
            'excluded_reasons':dict(excluded),'records':accepted,
            'real_world_provenance_attested':False,'independent_review_status':'NOT_RUN',
            'note':'Metadata and full-text claims remain UNTRUSTED. This offline utility did not fetch source URLs; live host tool results and separate editorial review are required.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['route','audit']);p.add_argument('--topic',default='')
    p.add_argument('--audience',default='');p.add_argument('--industry',default='universal')
    p.add_argument('--json-file');p.add_argument('--min-records',type=int,default=15)
    p.add_argument('--min-authors',type=int,default=10);p.add_argument('--language',default='ru',choices=['ru','en'])
    a=p.parse_args()
    data=choose_sources(a.topic,a.audience,a.industry) if a.action=='route' else build_voice_dossier(
        json.load(open(a.json_file,encoding='utf-8')),a.min_records,a.min_authors,a.language)
    print(json.dumps(data,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
