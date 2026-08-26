#!/usr/bin/env python3
"""Pre-publication gate for this repository. Reads every tracked file, fails on any hit.

NOT FOR PUBLICATION AS-IS. See tools/README.md: this file and `leak_terms.txt` name the exact
vocabulary the published data must never contain, which means publishing them publishes the
vocabulary. The gate belongs in the private mirror or in CI with the list injected as a secret.

Three classes of term, because there are three kinds of risk and they need different matching.

  STEMS       plain substring. Every stem is a root with no innocent English carrier, so a
              substring match cannot fire on ordinary prose.
  WORDS       alphanumeric-boundary match. These are words ordinary English does carry, so a
              substring match would fire constantly and the gate would be switched off within a
              week. The boundary is deliberately not \\b, because `_` and `-` are word characters
              to \\b and are exactly how internal identifiers are joined: \\b would miss the
              joined forms while still catching the innocent ones.
  PATTERNS    regular expressions for operational identifiers, host names and key prefixes.

Term classes and the boundary reasoning are carried over from the gate that builds our published
reports, so the same words fail in the same way in both places.

Usage:
    python3 tools/leak_sweep.py [root]          # default: the repository root
    python3 tools/leak_sweep.py --self-test     # prove the gate can go red

Exit status 0 clean, 1 on any hit, 2 on a failed self-test.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The gate cannot scan the files that spell out what it forbids: a term list always contains its
# own terms, and the scrubber beside it names every identifier shape it strips. `tools/` is the
# pre-publication machinery and is removed from the published copy, so the whole directory is
# excluded. The exclusion is printed on every run, so it is never silent.
SELF_EXCLUDE_DIRS = {"tools"}

SKIP_DIRS = {".git", "__pycache__", ".github"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".woff", ".woff2", ".ico"}

STEMS = [
    "T_plas", "d_plas", "D_plas", "plastic state", "routing", "codebook", "crystalliz",
    "slice", "content key", "content-key", "gate_scale", "wmask",
    "coarse band", "coarse", "modulat", "mask", "kernel synthes", "backbone(",
    "factored", "grad-rout", "disjoint",
]

# Identifier-shaped terms need a boundary rather than a substring. `H_M` as a plain substring
# matches "teacH_Morvath_series", which is an ordinary field name in one of the published
# sessions; the substring form would fail a clean file and get the gate switched off.
IDENTIFIERS = {
    "H_M":    r"(?<![A-Za-z0-9])H_M(?![A-Za-z0-9])",
    "W_eff":  r"(?<![A-Za-z0-9])W_eff(?![A-Za-z0-9])",
    "head_S": r"(?<![A-Za-z0-9])head_S(?![A-Za-z0-9])",
}

# Note on what is deliberately NOT here: bare "gate". `gate_scale` is a stem above, but "gate" on
# its own is ordinary experimental English, and the published demonstrations use it correctly
# ("two gates were set before the run"). Blocking it would fail approved copy on its first run,
# and a gate that fails approved copy is a gate somebody switches off.
WORDS = {
    "overlay":     r"(?<![A-Za-z0-9])overlay",
    "bank":        r"(?<![A-Za-z0-9])banks?(?![A-Za-z0-9])",
    "tier":        r"(?<![A-Za-z0-9])tier(?![A-Za-z0-9])",
    "run_tier":    r"(?<![A-Za-z0-9])run[_ -]?tier",
    "register":    r"(?<![A-Za-z0-9])registers?(?![A-Za-z0-9])",
    "two-tier":    r"two[ -]?tier",
    "witness":     r"(?<![A-Za-z0-9])witness(?:e[sd])?(?![A-Za-z0-9])",
}

NAMES = ["tfgn", "tachymath", "qwen36-tfgn"]

PATTERNS = {
    "learner id":       r"lrn_[0-9a-f]{6,}",
    "job id":           r"(?:pending_|job_)[0-9A-Za-z_-]{6,}",
    "pod id":           r"pod_[0-9A-Za-z]{6,}",
    "api key":          r"sk-[0-9A-Za-z_-]{8,}",
    "railway host":     r"[0-9A-Za-z._-]+\.railway\.app",
    "vercel host":      r"[0-9A-Za-z._-]+\.vercel\.app",
    "modal host":       r"[0-9A-Za-z._-]+\.modal\.run",
    "fal host":         r"fal\.run/[0-9A-Za-z._/-]+",
    "internal path":    r"closeout_wave3|tfgn_program|scripts_wave|_engine/|mdx_|kf1_",
    "wave/board id":    r"(?<![A-Za-z0-9])(?:PU|MD|NL|FL|SN|EBR|FSP)-[0-9]",
    "internal initial": r"(?<![A-Za-z0-9])(?:F5|AG)(?![A-Za-z0-9])",
}

# Exact phrases the sweep skips, each because the words belong to the SUBJECT, not to us. The
# demonstration corpora are fiction we wrote; if an invented handbook says "incident tier",
# failing the build teaches nobody anything. Every entry is narrow, exact and carries its reason.
ALLOW = [
    ("incident tier", "taught-document content: an invented company's support escalation level"),
    ("support tier", "taught-document content: a customer support level, not a method"),
    ("pricing tier", "taught-document content: a commercial plan, not a method"),
    ("sk-your-key", "the documented placeholder in the install command; a real key never has "
                    "this shape and the api-key pattern still catches one"),
]


def visible(text: str) -> str:
    """The part a reader can read: base64 payloads and comments removed, allowances blanked."""
    text = re.sub(r"data:[a-z/+.-]+;base64,[A-Za-z0-9+/=\s]+", " ", text, flags=re.I)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    for phrase, _why in ALLOW:
        text = re.sub(re.escape(phrase), " ", text, flags=re.I)
    return text


def scan(text: str, audience: str = "public"):
    """Every hit, with the match and about 70 characters of context on each side."""
    vis = visible(text)
    low = vis.lower()
    hits = []
    for t in STEMS + (NAMES if audience == "public" else []):
        i = low.find(t.lower())
        if i >= 0:
            hits.append({"term": t, "how": "substring", "n": low.count(t.lower()),
                         "context": " ".join(vis[max(0, i - 70):i + len(t) + 70].split())})
    for label, pat in list(WORDS.items()) + list(IDENTIFIERS.items()) + list(PATTERNS.items()):
        ms = list(re.finditer(pat, vis, re.I))
        if ms:
            m = ms[0]
            hits.append({"term": label, "how": "pattern", "n": len(ms), "matched": m.group(0),
                         "context": " ".join(vis[max(0, m.start() - 70):m.end() + 70].split())})
    return hits


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            top = rel.split(os.sep)[0]
            if top in SELF_EXCLUDE_DIRS or os.path.splitext(name)[1].lower() in SKIP_EXT:
                continue
            yield path, rel


def self_test():
    """A gate that has never gone red is a gate nobody has tested."""
    fixtures = [
        ("mechanism stem", "the codebook holds it"),
        ("boundary word", "written into the overlay"),
        ("operational id", "learner lrn_85585419b20c answered"),
        ("host name", "posted to tfgn-product.up.railway.app"),
        ("old name", "the tfgn program"),
    ]
    bad = [name for name, text in fixtures if not scan(text)]
    if bad:
        print("SELF-TEST FAILED, these fixtures did not go red: %s" % ", ".join(bad))
        return 2
    if scan("Support response time is 4 hours and the office opens at 09:30."):
        print("SELF-TEST FAILED: a clean fixture went red")
        return 2
    print("SELF-TEST PASSED: 5 planted fixtures went red, 1 clean fixture stayed green")
    return 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    root = os.path.abspath(argv[1]) if len(argv) > 1 else ROOT
    n_files = 0
    findings = []
    for path, rel in walk(root):
        try:
            with open(path, "r", encoding="utf-8", errors="strict") as fh:
                text = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        n_files += 1
        for hit in scan(text):
            findings.append(dict(hit, file=rel))

    print("leak sweep over %s" % root)
    print("  files read      %d" % n_files)
    print("  excluded        %s/ (the pre-publication machinery, not published)"
          % ", ".join(sorted(SELF_EXCLUDE_DIRS)))
    print("  allowances      %d" % len(ALLOW))
    if not findings:
        print("  RESULT          CLEAN, 0 hits")
        return 0
    print("  RESULT          %d hits" % len(findings))
    for f in findings:
        print("    %-44s %-16s x%-4d %s"
              % (f["file"], f["term"], f["n"], f.get("matched", "")))
        print("        ...%s..." % f["context"][:150])
    print(json.dumps({"hits": len(findings)}))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
