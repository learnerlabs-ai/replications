#!/usr/bin/env python3
"""Publication check for third-party corpus files. Standard library only.

data/PUBLIC_RELEASE_DISPOSITION.json lists every sample file that holds third-party text. Each entry
has a `public_release` field. While it is `not recorded`, that file must not be in a public export.
Run this on the tree that is about to be published:

    python3 science/plasticity-without-forgetting/tools/check_public_release.py [tree]

It exits 1 and names the files if any listed file is present without a recorded disposition.
Every listed file in this repository has a recorded decision, so it passes."""
import json, os, sys


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(here))
    disp = json.load(open(os.path.join(here, 'data', 'PUBLIC_RELEASE_DISPOSITION.json')))
    bad = [e['path'] for e in disp['files'] if e['public_release'] not in disp['cleared_values'] and os.path.exists(os.path.join(root, e['path']))]
    if bad:
        print('NOT CLEARED FOR PUBLIC RELEASE: these files are present and have no recorded public-release disposition:')
        for b in bad: print('  ' + b)
        return 1
    print('ok: no uncleared third-party corpus file is present'); return 0


if __name__ == '__main__':
    sys.exit(main())
