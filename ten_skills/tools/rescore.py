#!/usr/bin/env python3
"""Re-score every released answer of the ten-skill study with the frozen scorers and check the panels.

Runs on a CPU in under a minute, standard library only:

    python3 ten_skills/tools/rescore.py

Checks, all of which must pass (exit code 0):
  1. each skill's panel has 225 rows with unique ids;
  2. answers/final.jsonl and answers/own_end.jsonl each hold exactly one answer per panel row (2,250 each);
  3. every answer's stored grade equals the grade the frozen scorer gives its stored output;
  4. the totals are 1,525 correct at the final checkpoint and 1,528 at each skill's own-end checkpoint;
  5. every by_teach file has unique (skill, id) pairs, ids that exist in the panel, and grades that re-score identically;
  6. no panel prompt and no panel id appears in that skill's training file.
"""
import json, os, sys, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(T, 'scorers'))
import candidate_scoring

def rows(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]

fails = []
def check(name, ok, detail=''):
    print(('PASS ' if ok else 'FAIL ') + name + ((' : ' + detail) if detail else ''))
    if not ok: fails.append(name)

panel = {}
for d in sorted(glob.glob(os.path.join(T, 'data', 'evals', '*'))):
    s = os.path.basename(d); r = rows(os.path.join(d, 'panel.jsonl')); panel[s] = {x['id']: x for x in r}
    check(f'panel {s}: 225 rows, unique ids', len(r) == 225 and len(panel[s]) == 225)
check('ten panels', len(panel) == 10)

def rescore(path, expect_total=None, expect_rows=None):
    A = rows(path); seen = collections.Counter((a['skill'], a['id']) for a in A); bad = 0; unknown = 0; correct = 0
    for a in A:
        row = panel.get(a['skill'], {}).get(a['id'])
        if row is None: unknown += 1; continue
        try: g = bool(candidate_scoring.score(row, a['output'])['correct'])
        except Exception: g = False
        bad += (g != bool(a['correct'])); correct += g
    name = os.path.relpath(path, T)
    check(f'{name}: no duplicate (skill, id)', max(seen.values()) == 1)
    check(f'{name}: every id is a panel row', unknown == 0)
    check(f'{name}: stored grades equal re-scored grades', bad == 0, f'{bad} differ' if bad else f'{len(A)} answers')
    if expect_rows is not None: check(f'{name}: {expect_rows} answers', len(A) == expect_rows, str(len(A)))
    if expect_total is not None: check(f'{name}: {expect_total} correct', correct == expect_total, str(correct))

rescore(os.path.join(T, 'answers', 'final.jsonl'), 1525, 2250)
rescore(os.path.join(T, 'answers', 'own_end.jsonl'), 1528, 2250)
for p in sorted(glob.glob(os.path.join(T, 'answers', 'by_teach', '*.jsonl'))): rescore(p)

for tr in sorted(glob.glob(os.path.join(T, 'data', 'train', '*.jsonl'))):
    s = os.path.basename(tr)[3:-6]; R = rows(tr)
    prompts = {x['prompt'] for x in R}; ids = {x['id'] for x in R}
    clash = sum(1 for x in panel[s].values() if x['prompt'] in prompts or x['id'] in ids)
    check(f'train/eval disjoint {s}', clash == 0, f'{len(R)} training rows against 225 panel rows' if not clash else f'{clash} overlap')

print('\n' + ('ALL CHECKS PASS' if not fails else f'{len(fails)} CHECK(S) FAILED'))
sys.exit(1 if fails else 0)
