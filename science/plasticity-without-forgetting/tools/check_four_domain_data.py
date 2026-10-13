#!/usr/bin/env python3
"""Check the four-domain sample files against windows_index.json. Standard library only.
Recomputes every window checksum, checks counts, splits, token lengths and ids, and that no exact
window appears in more than one set. Run from the repository root."""
import hashlib, json, os, sys

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
EXPECT = {'train': 1200, 'heldout': 32, 'control': 64}


def main():
    idx = json.load(open(os.path.join(D, 'windows_index.json')))
    seen, n = {}, {'train': 0, 'heldout': 0, 'control': 0}
    absent = []
    for key, rec in idx['domains'].items():
        # `files` names what is published; `files_not_redistributed`, when present, names what the
        # index still accounts for but the repository does not carry. Walking both keeps the counts
        # honest while letting a naive reader of `files` fetch only paths that exist.
        for fn in list(rec['files']) + list(rec.get('files_not_redistributed', [])):
            split = fn.split('.')[1]
            path = os.path.join(D, fn)
            # [2026-09-19] Some domains are recorded in the index but are third-party text that is
            # not redistributed, so their files are absent here by design. This used to crash on the
            # first one, which meant the documented command failed on the published tree. An absent
            # file is reported, not an error; a file that IS here is checked exactly as before.
            if not os.path.exists(path):
                absent.append(fn)
                continue
            rows = [json.loads(l) for l in open(path, encoding='utf-8')]
            got = [hashlib.sha256(json.dumps(r['token_ids'], separators=(',', ':')).encode()).hexdigest() for r in rows]
            assert got == rec[split + '_sha256'], ('checksums', fn)
            for i, r in enumerate(rows):
                assert r['index'] == i and r['split'] == split and r['domain'] == key and len(r['token_ids']) == 256 == r['n_tokens'] and r['sha256'] == got[i], (fn, i)
                assert got[i] not in seen, ('window in two places', fn, i, seen[got[i]])
                seen[got[i]] = (fn, i)
            n[split] += len(rows)
    tr = n['train']
    checked = sum(n.values())
    print(f"{checked} windows match: {n['train']} training, {n['heldout']} held-out, {n['control']} control; "
          f"{tr * 256:,} training input tokens, {tr * 255:,} next-token targets; no exact window in more than one set")
    if absent:
        recorded = sum(EXPECT.values())
        print(f"{recorded - checked} further windows are recorded in windows_index.json and are not "
              f"redistributed here ({len(absent)} files): {', '.join(sorted(absent))}")
    else:
        assert n == EXPECT, n
        assert (tr * 256, tr * 255) == (307200, 306000)


if __name__ == '__main__':
    sys.exit(main())
