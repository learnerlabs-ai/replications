"""Typed JSON task success plus diagnostics; no repairs affect primary accuracy."""
import json

def pairs(items):
 out={}
 for k,v in items:
  if k in out:raise ValueError('Duplicate JSON key')
  out[k]=v
 return out
def reject_constant(x):raise ValueError('Non-finite JSON')
DECODER=json.JSONDecoder(object_pairs_hook=pairs,parse_constant=reject_constant)
def equal(a,b):
 if type(a)is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return a==b
def leaf_counts(gold,pred):
 if isinstance(gold,dict):
  values=[leaf_counts(v,pred.get(k) if isinstance(pred,dict) else None) for k,v in gold.items()]
 elif isinstance(gold,list) and gold:
  values=[leaf_counts(v,pred[i] if isinstance(pred,list) and i<len(pred) else None) for i,v in enumerate(gold)]
 else:return int(equal(gold,pred)),1
 return sum(v[0] for v in values),sum(v[1] for v in values)
def score_procedure(row,output):
 gold=DECODER.decode(row['target']);valid=True;pred=None
 try:pred=DECODER.decode(output)
 except (ValueError,TypeError):valid=False
 c,n=leaf_counts(gold,pred)
 result={'correct':valid and equal(gold,pred),'empty':not output.strip(),'valid_json':valid,'correct_gold_leaves':c,'gold_leaves':n,'leaf_accuracy':c/n,'diagnostic_note':'Leaf metrics do not penalize every extra field; strict task success does.'}
 try:lead,_=DECODER.raw_decode(output.lstrip());result['leading_json_correct']=equal(gold,lead)
 except (ValueError,TypeError):result['leading_json_correct']=False
 result.update(semantic_diagnostics(row,pred,gold))
 if isinstance(gold,dict):result['field_correct']={k:valid and isinstance(pred,dict) and k in pred and equal(v,pred[k]) for k,v in gold.items()}
 return result

def semantic_diagnostics(row,pred,gold):
 skill=row.get('skill');x=row.get('input')
 if x is None:return {}
 if skill=='lumen_parity':
  bits=pred.get('bits') if isinstance(pred,dict) else None
  valid=isinstance(bits,list) and len(bits)==x['n'] and all(type(b)is int and b in [0,1] for b in bits)
  feasible=valid and all(sum(bits[i] for i in ps)%2==v for ps,v in x['equations'])
  return {'vector_feasible':bool(feasible),'lexicographic_vector_correct':bool(valid and bits==gold['bits']),
          'solution_count_correct':isinstance(pred,dict) and equal(pred.get('count'),gold['count'])}
 if skill=='morrow_cells':
  valid=isinstance(pred,list) and len(pred)==len(gold) and all(isinstance(r,list) and len(r)==len(g) and all(type(v)is int and v in [0,1] for v in r) for r,g in zip(pred,gold))
  return {'valid_grid':valid,'identity_copy_correct':equal(x['grid'],gold),
          'cell_accuracy':sum(u==v for a,b in zip(pred,gold) for u,v in zip(a,b))/sum(map(len,gold)) if valid else 0.0}
 if skill=='sorrel_polynomial':
  valid=isinstance(pred,list) and bool(pred) and all(type(v)is int and 0<=v<17 for v in pred)
  return {'valid_reduced_coefficients':valid,'degree_correct':bool(valid and len(pred)==len(gold)),
          'canonical_degree':bool(valid and (len(pred)==1 or pred[-1]!=0)),
          'coefficient_accuracy':sum(i<len(pred) and equal(v,pred[i]) for i,v in enumerate(gold))/len(gold) if valid else 0.0}
 if skill=='bracken_intervals':
  valid=isinstance(pred,list) and all(isinstance(p,list) and len(p)==2 and all(type(v)is int for v in p) and p[0]<p[1] for p in pred)
  # Bound ranges before expansion: incorrect unbounded answers are diagnostics
  # failures rather than a memory-allocation request from model output.
  bounded=valid and all(-1000<=p[0]<p[1]<=1000 for p in pred)
  actual={i for a,b in pred for i in range(a,b)} if bounded else set()
  expected={i for a,b in gold for i in range(a,b)}
  return {'valid_intervals':valid,'maximal_sorted_intervals':bool(valid and all(a[1]<b[0] for a,b in zip(pred,pred[1:]))),
          'occupied_unit_set_correct':bool(bounded and actual==expected),
          'unit_jaccard':len(actual&expected)/len(actual|expected) if bounded and actual|expected else float(bounded),
          'gold_empty':not bool(gold)}
 if skill=='quill_alignment':
  return {'optimal_cost_correct':isinstance(pred,dict) and equal(pred.get('cost'),gold['cost']),
          'optimal_path_count_correct':isinstance(pred,dict) and equal(pred.get('ways'),gold['ways'])}
 if skill=='cairn_matching':
  n=len(x['proposers']);valid=isinstance(pred,list) and len(pred)==n and all(type(v)is int for v in pred) and set(pred)==set(range(n))
  blocks=None
  if valid:
   inverse={r:p for p,r in enumerate(pred)}
   blocks=sum(x['proposers'][p].index(r)<x['proposers'][p].index(pred[p]) and x['receivers'][r].index(p)<x['receivers'][r].index(inverse[r]) for p in range(n) for r in range(n))
  return {'valid_bijection':valid,'stable_matching':bool(valid and blocks==0),
          'blocking_pairs':blocks,'proposer_optimal':bool(valid and pred==gold)}
 if skill=='ravel_route':
  path=pred.get('path') if isinstance(pred,dict) else None
  valid=isinstance(path,list) and len(path)>=2 and all(type(n)is str for n in path)
  valid=valid and len(path)==len(set(path)) and path[0]==x['start'] and path[-1]==x['finish']
  edges={(a,b):2*w+{'amber':3,'blue':1,'violet':5}[c]+4*(b in x['checkpoints']) for a,b,w,c in x['edges']}
  cost=None
  if valid:
   valid=all((a,b)in edges for a,b in zip(path,path[1:]))
   if valid:cost=sum(edges[a,b] for a,b in zip(path,path[1:]))
  return {'path_feasible':bool(valid),'path_has_optimal_cost':bool(valid and cost==gold['cost']),
          'declared_cost_matches_path':bool(valid and type(pred.get('cost'))is int and pred['cost']==cost),
          'gold_hops':len(gold['path'])-1,'returned_path_cost':cost}
 if skill=='selka_relational':
  valid=isinstance(pred,list) and all(isinstance(p,list) and len(p)==2 and type(p[0])is str and type(p[1])is int for p in pred)
  if valid:valid=len({p[0] for p in pred})==len(pred)
  expected=dict(gold);actual=dict(pred) if valid else {}
  return {'gold_empty':not bool(gold),'account_selection_correct':bool(valid and set(actual)==set(expected)),
          'correct_account_totals':sum(a in actual and actual[a]==t for a,t in expected.items()),
          'gold_accounts':len(expected),'valid_account_total_pairs':valid}
 if skill=='vesper_dimensions':
  valid=isinstance(pred,list) and len(pred)==3 and all(type(v)is int for v in pred)
  return {'valid_dimension_vector':valid,'dimension_l1_error':sum(abs(a-b) for a,b in zip(pred,gold)) if valid else None,
          'gold_dimensionless':gold==[0,0,0]}
 if skill=='oriel_packet_codec':
  decoded=[];valid=isinstance(pred,list);i=0
  if valid:
   while i<len(pred):
    v=pred[i]
    if type(v)is not int or not 0<=v<16:valid=False;break
    if v==15:
     if i+1>=len(pred) or type(pred[i+1])is not int or pred[i+1]not in [9,13]:valid=False;break
     decoded.append(pred[i+1]^6);i+=2
    else:
     if v==11:valid=False
     decoded.append(v);i+=1
  payload=x['payload'];body=[v for p in payload for v in [(p+5)%16,(3*p+1)%16]]
  return {'escaping_valid':valid,'header_correct':decoded[:2]==[11,len(payload)],'transformed_payload_correct':decoded[2:-1]==body if len(decoded)>=3 else False,'checksum_correct':bool(decoded) and decoded[-1]==sum((i+1)*p for i,p in enumerate(payload))%16,'decoded_length_correct':len(decoded)==3+2*len(payload)}
 if skill=='juniper_dispatch':
  jobs={j['id']:j for j in x['jobs']};valid=isinstance(pred,list) and all(isinstance(t,list) and len(t)==3 and isinstance(t[0],str) and type(t[1])is int and type(t[2])is int for t in pred)
  if not valid:return {'schedule_feasible':False,'job_order_correct':False,'job_times_correct':0,'job_count':len(jobs)}
  ids=[p[0] for p in pred];feasible=len(ids)==len(set(ids)) and set(ids)==set(jobs);previous_end=None
  for jid,start,end in pred:
   if jid not in jobs:feasible=False;continue
   j=jobs[jid];feasible=feasible and start>=j['release'] and end-start==j['duration'] and (previous_end is None or start>=previous_end+2);previous_end=end
  expected={r[0]:r[1:] for r in gold}
  return {'schedule_feasible':feasible,'job_order_correct':ids==[r[0] for r in gold],'job_times_correct':sum(t[0]in expected and t[1:]==expected[t[0]] for t in pred) if len(ids)==len(set(ids)) else 0,'job_count':len(jobs)}
 if skill=='tessel_lot_allocation':
  if not isinstance(pred,dict):return {'allocation_branch_correct':False,'allocations_feasible':False}
  a=pred.get('allocations');valid=isinstance(a,list) and all(isinstance(p,list) and len(p)==2 and isinstance(p[0],str) and type(p[1])is int and p[1]>0 for p in a)
  if valid:
   lots={l['id']:l for l in x['lots']};ids=[p[0] for p in a]
   valid=len(ids)==len(set(ids)) and all(i in lots and n<=lots[i]['units'] and lots[i]['cold'] and lots[i]['expiry']>=x['delivery_day']+3 for i,n in a)
   if a:valid=valid and sum(n for _,n in a)==x['demand']
   else:valid=valid and not gold['allocations']
  return {'allocation_branch_correct':isinstance(a,list) and bool(a)==bool(gold['allocations']),'allocations_feasible':bool(valid)}
 if skill=='cobalt_access':
  correct,total=leaf_counts(gold,pred);return {'per_request_correct':correct,'requests':total,'bundle_is_independent_queries':True}
 return {}
