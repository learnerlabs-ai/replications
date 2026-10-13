"""Numeric checks: recompute the values each figure claims to plot from the source tables, independently of the figure code,
and compare with the `plotted` block of the figure's sidecar. A deterministic rebuild proves the rendering is reproducible;
these checks tie the rendered numbers to the source data."""
import json,os
def run(HERE):
    D=os.path.join(HERE,'data'); O=os.path.join(HERE,'output'); out=[]
    def side(g,n):
        p=os.path.join(O,g,n+'.json'); return json.load(open(p)).get('plotted') if os.path.exists(p) else None
    def add(fig,ok,detail): out.append({'figure':fig,'ok':bool(ok),'detail':detail})
    T=json.load(open(os.path.join(D,'derived','tables.json'))); SK=T['skills']
    p=side('ten_skills','ts_f4_matrix')
    if p: add('ts_f4_matrix',p['matrix']==[[r.get(k) for k in SK] for r in T['matrix']] and sum(r[k] for k in SK for r in [T['matrix'][-1]])==1525,'matrix equals tables.json; final row sums to 1,525')
    p=side('ten_skills','ts_f5_own_vs_final')
    if p: add('ts_f5_own_vs_final',sum(v[0] for v in p.values())==1528 and sum(v[1] for v in p.values())==1525 and min(v[0] for v in p.values())==12,'own-end 1,528, final 1,525, own-end minimum 12')
    p=side('ten_skills','ts_f6_dose')
    if p: add('ts_f6_dose',sum(v[0] for v in p.values())==T['dose_totals']['updates']==63282 and sum(v[1] for v in p.values())==T['dose_totals']['supervised_trained'],'updates sum to 63,282; supervised tokens sum to the table total')
    p=side('ten_skills','ts_f8_sentinel_base')
    if p:
        B=T['base_battery']; ok=len(p['sentinel_raw'])==11 and all(abs(p['battery'][k]['mmlu_macro_57']-sum(B[k]['mmlu_subjects'].values())/57)<1e-12 for k in B) and len(B['step_zero']['mmlu_subjects'])==57
        add('ts_f8_sentinel_base',ok,f"11 sentinel points {min(p['sentinel_raw'])}-{max(p['sentinel_raw'])}; MMLU macro recomputed over 57 subjects")
    sp=os.path.join(D,'series','training_loss.json'); p=side('ten_skills','ts_f1_stream')
    if p and os.path.exists(sp):
        rows=[r['training_loss'] for r in json.load(open(sp))['rows'] if r['training_loss'] is not None]
        add('ts_f1_stream',p['n_raw_points']==len(rows) and abs(p['raw_max']-max(rows))<1e-12,f"{len(rows):,} raw points drawn inside the envelope; maximum preserved")
    p=side('four_domain','fd_f4_validation')
    if p:
        ok=True
        for arm in ['learner_1x','learner_2x','lora_r256']:
            rows=[json.loads(l) for l in open(os.path.join(D,'four_domain',arm,'val_curve.jsonl')) if l.strip()]
            for dm in ['a_book_class','d_yoruba','c_language','d_news']:
                v=sorted({(r['gstep'],r['val_loss']) for r in rows if r['domain']==dm}); q=p[f'{arm}:{dm}']; ok=ok and q['n']==len(v)==12 and abs(q['last'][1]-v[-1][1])<1e-12
        add('fd_f4_validation',ok,'12 points per condition per domain; endpoints equal val_curve.jsonl')
    p=side('four_domain','fd_f1b_stream_raw')
    if p:
        ok=True
        for arm in ['learner_1x','learner_2x','lora_r256']:
            v=[r['loss'] for r in (json.loads(l) for l in open(os.path.join(D,'four_domain',arm,'train_curve.jsonl')) if l.strip()) if r.get('phase') in ('a_book_class','d_yoruba','c_language','d_news')]
            q=p[arm]; ok=ok and q['points']==len(v)==1200 and abs(q['max']-max(v))<1e-12 and abs(q['min']-min(v))<1e-12
        add('fd_f1b_stream_raw',ok,'1,200 raw points per condition drawn; minimum and maximum preserved for all three conditions')
    p=side('four_domain','fd_f2_bwt')
    if p:
        a=json.load(open(os.path.join(D,'four_domain','lora_r256','A_equivalence.json'))); m=a.get('measured',a); add('fd_f2_bwt',p['lora_r256']['bwt']==m['bwt_per_domain'],'LoRA per-domain values equal the receipt')
    p=side('two_languages','tl_f1_curves')
    if p:
        TL=json.load(open(os.path.join(D,'two_languages.json'))); O=TL['learner_onepass']; add('tl_f1_curves',all(p[l]['held_out']==O['held_out'][l] and p[l]['train_loss_points']==O['updates'][l]==len(O['train_loss'][l]) for l in ('velenic','morvath')),"each panel's held-out points and training-loss count equal the one-pass recording")
    return out
