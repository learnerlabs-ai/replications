"""Strict primary scores and explicitly separate diagnostics. No answer repair."""
import math,unicodedata

def normalized(s):return unicodedata.normalize('NFC',s)
def edit_distance(a,b):
 previous=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  current=[i]
  for j,y in enumerate(b,1):current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
  previous=current
 return previous[-1]
def score(row,output):
 if row['scorer']=='scan_actions':
  if not isinstance(output,str):raise TypeError('Output must be text')
  gold=row['target'].split();pred=output.split()
  allowed={'I_WALK','I_RUN','I_JUMP','I_LOOK','I_TURN_LEFT','I_TURN_RIGHT'}
  return {'correct':pred==gold,'valid_actions':bool(pred) and all(x in allowed for x in pred),
          'token_edits':edit_distance(gold,pred),'gold_tokens':len(gold),'predicted_tokens':len(pred)}
 if row['scorer']=='json_value':
  import json
  def invalid_constant(s):raise ValueError('Nonfinite JSON')
  def unique(pairs):
   out={}
   for k,v in pairs:
    if k in out:raise ValueError('Duplicate JSON key')
    out[k]=v
   return out
  def typed(v):
   if isinstance(v,list):return ('list',tuple(typed(x) for x in v))
   if isinstance(v,dict):return ('dict',tuple(sorted((k,typed(x)) for k,x in v.items())))
   return (type(v).__name__,v)
  gold=json.loads(row['target'],parse_constant=invalid_constant,object_pairs_hook=unique)
  try:pred=json.loads(output,parse_constant=invalid_constant,object_pairs_hook=unique)
  except (ValueError,TypeError):return {'correct':False,'valid_json':False}
  return {'correct':typed(gold)==typed(pred),'valid_json':True}
 if row['scorer']=='cogs_sequence':
  if not isinstance(output,str):raise TypeError('Output must be text')
  gold=row['target'].split();pred=output.split()
  return {'correct':pred==gold,'empty':not pred,'token_edits':edit_distance(gold,pred),
          'gold_tokens':len(gold),'predicted_tokens':len(pred)}
 if row['scorer']=='inflected_word':
  if not isinstance(output,str):raise TypeError('Output must be text')
  gold=row['target'];pred=output.strip()
  return {'correct':pred==gold,'raw_exact':output==gold,'empty':not pred,
          'character_edits':edit_distance(gold,pred),
          'nfc_correct':normalized(pred)==normalized(gold),
          'copy_lemma_correct':gold==row['input']['lemma'],
          'copied_lemma':pred==row['input']['lemma']}
 if row['scorer']=='typed_json_procedure':
  from procedure_scoring import score_procedure
  return score_procedure(row,output)
 if row['scorer']=='calflow_canonical':
  from calflow_scoring import score_calflow
  return score_calflow(row,output)
 if not isinstance(output,str):raise TypeError('Output must be text')
 gold=normalized(row['target']).split();pred=normalized(output).split()
 result={'correct':pred==gold,'empty':not pred,'token_edits':edit_distance(gold,pred),'gold_tokens':len(gold),'predicted_tokens':len(pred)}
 if row['scorer']=='phoneme_sequence':
  # Equal unsegmented IPA does not prove phoneme segmentation, but excludes a spacing-only gain.
  result['ipa_without_spaces_correct']=''.join(gold)==''.join(pred)
  result['ipa_character_edits']=edit_distance(''.join(gold),''.join(pred))
 elif row['scorer']=='symbol_sequence':
  import re
  result['valid_symbol_sequence']=bool(pred) and all(re.fullmatch('[A-Z][0-9]+',v) for v in pred)
 else:raise ValueError('Unregistered scorer')
 return result
def wilson(k,n,z=1.959963984540054):
 if not n:return [None,None]
 p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return [max(0,c-h),min(1,c+h)]
