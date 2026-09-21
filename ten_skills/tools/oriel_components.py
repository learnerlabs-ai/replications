#!/usr/bin/env python3
"""Oriel packet codec: component-level comparison of the 225 panel rows at two checkpoints.

Reads only released files: the panel, the stored answers after teach 9 and teach 10, and the frozen scorers.
Regenerates results/oriel_components.json and results/oriel_flipped_rows.json (written to --out, default a temp dir,
and compared with the released copies).

    python3 ten_skills/tools/oriel_components.py
"""
import argparse, glob, json, os, sys, collections, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(T, 'scorers'))
import candidate_scoring, procedure_scoring
SKILL = 'oriel_packet_codec'
COMP = ['escaping_valid', 'header_correct', 'transformed_payload_correct', 'checksum_correct', 'decoded_length_correct']

def answers(teach):
    (p,) = glob.glob(os.path.join(T, 'answers', 'by_teach', f'teach_{teach:02d}_*.jsonl'))
    out = {}
    for l in open(p, encoding='utf-8'):
        r = json.loads(l)
        if r['skill'] == SKILL: out[r['id']] = r
    return out, os.path.basename(p)[9:17]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=None); a = ap.parse_args()
    out = a.out or tempfile.mkdtemp()
    panel = {}
    for l in open(os.path.join(T, 'data', 'evals', SKILL, 'panel.jsonl'), encoding='utf-8'):
        r = json.loads(l); panel[r['id']] = r
    B, shab = answers(9); A, shaa = answers(10)
    agg = collections.Counter(); flips = []; tot = {9: collections.Counter(), 10: collections.Counter()}
    lost = {9: collections.Counter(), 10: collections.Counter()}; gained = {9: collections.Counter(), 10: collections.Counter()}
    lost_ids = []; gained_ids = []
    for i in sorted(panel):
        row = panel[i]; pb = B[i]['output']; pa = A[i]['output']
        cb = bool(candidate_scoring.score(row, pb)['correct']); ca = bool(candidate_scoring.score(row, pa)['correct'])
        db = procedure_scoring.score_procedure(row, pb); da = procedure_scoring.score_procedure(row, pa)
        tr = ('correct' if cb else 'wrong') + '->' + ('correct' if ca else 'wrong'); agg[tr] += 1
        if pb != pa: agg['prediction_changed:' + tr] += 1
        for k in COMP: tot[9][k] += bool(db.get(k)); tot[10][k] += bool(da.get(k))
        if cb != ca:
            (lost_ids if cb else gained_ids).append(i)
            tgt = lost if cb else gained
            for k in COMP: tgt[9][k] += bool(db.get(k)); tgt[10][k] += bool(da.get(k))
            flips.append({'id': i, 'input': row['input'], 'target': row['target'], 'prediction_teach9': pb, 'prediction_teach10': pa,
                          'correct_teach9': cb, 'correct_teach10': ca,
                          'components_teach9': {k: bool(db.get(k)) for k in COMP}, 'components_teach10': {k: bool(da.get(k)) for k in COMP}})
    summary = {'panel_rows': len(panel), 'before_correct': sum(v for k, v in agg.items() if k.startswith('correct->')),
               'after_correct': sum(v for k, v in agg.items() if k.endswith('->correct') and not k.startswith('prediction')),
               'before_checkpoint_sha8': shab, 'after_checkpoint_sha8': shaa, 'transitions': dict(agg),
               'lost_ids': lost_ids, 'gained_ids': gained_ids,
               'lost_components_teach9': dict(lost[9]), 'lost_components_teach10': dict(lost[10]),
               'gained_components_teach9': dict(gained[9]), 'gained_components_teach10': dict(gained[10]),
               'all_rows_component_totals_teach9': dict(tot[9]), 'all_rows_component_totals_teach10': dict(tot[10])}
    os.makedirs(out, exist_ok=True)
    json.dump(summary, open(os.path.join(out, 'oriel_components.json'), 'w'), indent=1)
    json.dump(flips, open(os.path.join(out, 'oriel_flipped_rows.json'), 'w'), indent=1, ensure_ascii=False)
    rel = json.load(open(os.path.join(T, 'results', 'oriel_components.json')))
    keys = ['before_correct', 'after_correct', 'lost_ids', 'gained_ids', 'all_rows_component_totals_teach9', 'all_rows_component_totals_teach10']
    same = all(rel.get(k) == summary[k] for k in keys)
    print(f"teach 9: {summary['before_correct']} correct; teach 10: {summary['after_correct']} correct; lost {len(lost_ids)}, gained {len(gained_ids)}")
    print('written to', out); print('matches the released results/oriel_components.json:', same)
    sys.exit(0 if same else 1)

if __name__ == '__main__': main()
