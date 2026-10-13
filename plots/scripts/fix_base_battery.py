#!/usr/bin/env python3
"""Recompute the MMLU macro average in plots/data/derived/tables.json over the 57 leaf subjects only.
The first derivation averaged 61 entries (57 subjects + the 4 lm-eval group aggregates humanities/social_sciences/stem/other);
the primary receipts give 0.8634 / 0.8631 / 0.8654 over the 57 subjects. Idempotent."""
import json,os
P=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'data','derived','tables.json'); T=json.load(open(P))
GROUPS={'mmlu_humanities','mmlu_social_sciences','mmlu_stem','mmlu_other','mmlu'}
for k,b in T['base_battery'].items():
    leaf={s:v for s,v in b['mmlu_subjects'].items() if s not in GROUPS}; assert len(leaf)==57,(k,len(leaf))
    b['mmlu_macro_57']=sum(leaf.values())/57; b['n_mmlu_subjects']=57; b['mmlu_subjects']=leaf
    print(k,round(b['mmlu_macro_57'],4),round(b['mmlu_micro'],4))
json.dump(T,open(P,'w'),indent=1)
