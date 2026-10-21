#!/usr/bin/env python3
"""Offline structural validator for Structure Packet v0.3.1.
No scientific review, editorial judgement or independent AI-run attestation.
Usage: python scripts/validate_structure_packet.py schemas/structure-packet.example.json
"""
import hashlib, json, sys
from pathlib import Path

STRUCTURES = {f'SRC-0{i}' for i in range(1, 8)}
KINDS = ('HOOK','DEVELOPMENT','REHOOK_SLOT','EVIDENCE_OR_MECHANISM','PAYOFF','CTA_SLOT')

def valid_text(t):return isinstance(t,str) and bool(t.strip())
def digest(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()

def assess(doc):
 errors, blockers, warnings=[],[],[]
 if not isinstance(doc,dict):
  return {'errors':['packet must be object'],'blockers':['INVALID_PACKET'],'warnings':[],'structure_status':'FAIL','production_status':'BLOCKED'}
 if doc.get('schema_version')!='0.3.1':errors.append('schema_version: expected 0.3.1')
 for field in ('reels_id','topic','profile'):
  if not valid_text(doc.get(field)):errors.append(f'{field}: required')
 if doc.get('mode') not in ('preview','production'):errors.append('mode: invalid')
 max_s=doc.get('duration_target_s')
 if not isinstance(max_s,(int,float)) or not 15<=max_s<=90:errors.append('duration_target_s: invalid')
 research=doc.get('research') or {}
 claims={c.get('id') for c in research.get('claims',[]) if isinstance(c,dict)}
 if research.get('status')!='PASS_ATTESTED':blockers.append('RESEARCH_NOT_ATTESTED')
 if doc.get('hook_status')!='PASS_ATTESTED':blockers.append('HOOK_NOT_ATTESTED')
 # Offline cannot authenticate status fields even if somebody forges them
 blockers.append('INDEPENDENT_RUNTIME_ATTESTATION_REQUIRED')
 variants=doc.get('variants')
 if not isinstance(variants,dict) or set(variants)!={'A','B','C'}:
  errors.append('variants: must be exactly A/B/C')
  variants=variants if isinstance(variants,dict) else {}
 structures=[]; engines=[]
 for letter in 'ABC':
  v=variants.get(letter)
  if not isinstance(v,dict):errors.append(f'{letter}: missing branch');continue
  head=f'{letter}.'
  if v.get('branch_id')!=letter:errors.append(head+'branch_id: inconsistent')
  s=v.get('structure_id')
  if s not in STRUCTURES:errors.append(head+'structure_id: invalid')
  structures.append(s)
  for k in ('fit_reason','viewer_question','payoff_contract','evidence_logic'):
   if not valid_text(v.get(k)):errors.append(head+k+': required')
  snapshot=v.get('hook_snapshot') or {}
  if not valid_text(snapshot.get('text')):errors.append(head+'hook_snapshot.text: required')
  elif snapshot.get('sha256')!=digest(snapshot['text']):errors.append(head+'HOOK_TAMPER: digest mismatch')
  if snapshot.get('approved') is True or snapshot.get('locked') is True:
   blockers.append(head+'HOOK_APPROVAL_NOT_VERIFIABLE_OFFLINE')
  if v.get('review',{}).get('status')=='PASS' and not v.get('review',{}).get('reviewer_run_id'):
   errors.append(head+'review: PASS without reviewer id')
  if v.get('case_kind') not in ('illustrative','documented_real'):
   errors.append(head+'case_kind: missing validity marker')
  if s=='SRC-06' and v.get('comparison_mode') not in ('illustrative_matched_conditions','verified_matched_conditions'):
   errors.append(head+'comparison_mode: fair baseline missing')
  if s=='SRC-03':
   investigation=v.get('investigation_steps')
   if not isinstance(investigation,list) or len(investigation)<2 or any(not isinstance(item,dict) or not valid_text(item.get('observation')) or not valid_text(item.get('check')) or not valid_text(item.get('finding_basis')) for item in investigation):
    errors.append(head+'SRC-03: investigation steps need at least two grounded observation/check/finding_basis records')
  if s=='SRC-04':
   anchor=v.get('object_anchor') or {}
   required=('object_id','object_label','status','story_function','visual_notes')
   if any(not valid_text(anchor.get(field)) for field in required):errors.append(head+'SRC-04: object anchor fields missing')
   recurrence=anchor.get('beat_kinds')
   if not isinstance(recurrence,list) or any(not isinstance(k,str) for k in recurrence) or len(set(recurrence))<3 or not {'HOOK','DEVELOPMENT','PAYOFF'}.issubset(set(recurrence)) or not set(recurrence).issubset(set(KINDS)):
    errors.append(head+'SRC-04: object must recur from hook through development and payoff')
   if v.get('case_kind')=='illustrative' and anchor.get('status')!='illustrative_visual_not_research_evidence':errors.append(head+'SRC-04: illustrative object cannot claim evidentiary status')
  pacing=v.get('pacing') or {}
  if not valid_text(pacing.get('core_takeaway')) or not valid_text(pacing.get('repetition_policy')) or not isinstance(pacing.get('spoken_points'),list) or not 1<=len(pacing.get('spoken_points'))<=3 or any(not valid_text(t) for t in pacing.get('spoken_points',[]) if isinstance(pacing.get('spoken_points'),list)) or not isinstance(pacing.get('visual_only_details'),list) or not pacing.get('visual_only_details'):
   errors.append(head+'pacing: require one takeaway, 1–3 spoken points and visual-only details')
  for f in ('used_claim_ids','used_example_ids','excluded_structures'):
   if not isinstance(v.get(f),list):errors.append(head+f+': list required')
  for cid in v.get('used_claim_ids',[]) if isinstance(v.get('used_claim_ids'),list) else []:
   if cid not in claims:errors.append(head+'unknown claim '+str(cid))
  beats=v.get('beats',[])
  if not isinstance(beats,list) or not len(beats)>=6:
   errors.append(head+'beats: expected at least 6 ordered beats');continue
  kinds=[b.get('kind') if isinstance(b,dict) else None for b in beats]
  if kinds!=list(KINDS):errors.append(head+'beats: must use ordered narrative stages')
  prior=0
  for b in beats:
   if not isinstance(b,dict):errors.append(head+'beats: invalid item');continue
   start,end=b.get('start_s'),b.get('end_s')
   if not isinstance(start,(int,float)) or not isinstance(end,(int,float)) or start!=prior or end<=start:
    errors.append(head+'beats: noncontiguous/invalid timing');break
   prior=end
   if not valid_text(b.get('plan')):errors.append(head+'beats: empty plan')
  if isinstance(max_s,(int,float)) and prior!=max_s:errors.append(head+'beats: duration mismatch')
  if 'rehook_text' in v:errors.append(head+'rehook_text: Structure Agent must not author rehook')
  if 'script_text' in v:errors.append(head+'script_text: Structure Agent must not author full script')
  slot=v.get('rehook_slot') or {}
  for k in ('function','viewer_question_after_rehook','information_to_withhold','new_information'):
   if not valid_text(slot.get(k)):errors.append(head+'rehook_slot.'+k+': required')
  reveal=v.get('reveal_map') or {}
  for k in ('before_rehook','withheld','at_payoff'):
   if not valid_text(reveal.get(k)):errors.append(head+'reveal_map.'+k+': required')
  engines.append((v.get('structure_id'),slot.get('function')))
 if len(structures)==3 and len(set(structures))!=3:errors.append('diversity: three distinct structures required')
 if len(engines)==3 and len(set(engines))!=3:errors.append('diversity: repeated narrative engine')
 if doc.get('production_status')!='BLOCKED':errors.append('production_status: cannot be released by offline packet')
 return {'errors':errors,'blockers':list(dict.fromkeys(blockers)),'warnings':warnings,'structure_status':'PASS' if not errors else 'FAIL','production_status':'BLOCKED','note':'Offline contract only, no autonomous Structure Reviewer performed'}

def main():
 if len(sys.argv)!=2:print(__doc__);return 2
 result=assess(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if not result['errors'] else 1
if __name__=='__main__':sys.exit(main())
