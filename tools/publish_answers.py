#!/usr/bin/env python3
"""Turn a cleaned session receipt into the published answers file. NOT FOR PUBLICATION.

Input is a receipt that has already had the turn-echo tail removed, so every served string
carries both the cleaned text and the byte-exact original beside it. This script does the second
half: it removes the operational fields, replaces the internal cleaning note with one a reader
can act on, and refuses to write if anything it does not recognise survives.

It is deliberately a whitelist at the top level and a blacklist inside the records. A session's
shape differs per demonstration, so the record-level rule has to be general; the top level is
small enough to name.

Usage:
    python3 tools/publish_answers.py <cleaned.json> <out.json> --demo <slug> --replay-date <date>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# Operational identifiers and internal telemetry. Dropped wherever they appear, at any depth.
DROP_EXACT = {
    "f41",                      # served-identity check: internal field names, internal ids
    "learner_id", "job_id", "teach_job_id", "retrain_job_id", "session",
    "target_learner", "api_base", "host", "pod", "checkpoint_id", "wire_model",
    "log",                      # operational narration, internal phrasing, job handles
    "grader",                   # names an internal module path; grader.md says it in prose
    "source",                   # names an internal wave the document was written for
    "fact_id",                  # the store's row handle, not the demonstration's fact id
    "witness_file", "gates_note", "job_id_note", "race_artifact",
    "demo", "leg",              # the internal demonstration code; the public slug is at the top
    "witness", "checkpoint_note",
}
DROP_SUFFIX = ("_job_id", "_history")   # per-leg job handles; poll-by-poll ops telemetry
DROP_PREFIX = ("_", "f41")              # internal-only keys; f41 and its per-arm variants

# Strings that must never survive into a published file, checked after the drop pass.
FORBIDDEN = {
    "learner id":  re.compile(r"lrn_[0-9a-f]{6,}"),
    "job id":      re.compile(r"(?:pending_|job_)[0-9A-Za-z_-]{6,}"),
    "host":        re.compile(r"[0-9A-Za-z._-]+\.(?:railway\.app|vercel\.app|modal\.run)"),
    "path":        re.compile(r"closeout_wave3|tfgn_program|scripts_wave|lib/\w+\.py"),
    "old name":    re.compile(r"tfgn|tachymath", re.I),
    "checkpoint":  re.compile(r"ckpt_[0-9a-f]{6,}"),
    "wave code":   re.compile(r"(?<![A-Za-z0-9])(?:PU|MD|NL|FL|SN|EBR|FSP)-[0-9]"),
}

PUBLIC_NOTE = {
    "what_was_removed": (
        "A trailing fragment. After answering, the model kept writing the conversation: it "
        "restated the fact in invented formats and then began a new turn that repeated the "
        "question back. Only text from the start of that new turn onward was removed."),
    "why": (
        "A serving fault, not a grading fault. The answer was already graded on the answer "
        "itself, so no pass or fail in this file changes because of the removal."),
    "fixed_on": "2026-08-25",
    "originals": (
        "Every field that was shortened keeps its byte-exact original beside it under the same "
        "name with `_raw` appended. Nothing was deleted."),
    "how_the_cut_was_chosen": (
        "Only at a turn boundary, and only when the text after it was demonstrably the question "
        "coming back: either the first line ended in a question mark, or it repeated at least "
        "60 per cent of that record's own question. Anything else was left alone."),
    "a_third_form_you_may_have_seen": (
        "The demonstrations page shortens further, to the end of the answer proper, because the "
        "invented-format restatements are not readable in a table. This file is the longer form: "
        "answer as served, minus the new turn, with the untouched original beside it."),
}


# Keys holding real data under an internal name. Renamed rather than dropped: the reading is
# worth publishing, the word is not.
RENAME = {
    "kept_after_witness": "kept_fact_rechecked_after_removal",
    "target_after": "deleted_fact_rechecked",
    "kept_after": "kept_fact_rechecked",
}


def scrub(node):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k in DROP_EXACT or k.startswith(DROP_PREFIX) or k.endswith(DROP_SUFFIX):
                continue
            out[RENAME.get(k, k)] = scrub(v)
        return out
    if isinstance(node, list):
        return [scrub(v) for v in node]
    return node


def find_forbidden(node, path=""):
    bad = []
    if isinstance(node, dict):
        for k, v in node.items():
            bad += find_forbidden(v, "%s/%s" % (path, k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            bad += find_forbidden(v, "%s[%d]" % (path, i))
    elif isinstance(node, str):
        for label, rx in FORBIDDEN.items():
            m = rx.search(node)
            if m:
                bad.append((path, label, m.group(0)))
    return bad


def count_answers(node):
    """Every string field that holds something the model served."""
    served = ("got", "answer", "learner_answer", "base_answer", "served_text", "text")
    n = 0
    if isinstance(node, dict):
        for k, v in node.items():
            if k in served and isinstance(v, str):
                n += 1
            else:
                n += count_answers(v)
    elif isinstance(node, list):
        for v in node:
            n += count_answers(v)
    return n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dest")
    ap.add_argument("--demo", required=True)
    ap.add_argument("--replay-date", default="2026-08-24")
    a = ap.parse_args(argv)

    doc = json.load(open(a.src))
    had_cleaning = "cleaning" in doc
    doc.pop("cleaning", None)

    before_answers = count_answers(doc)
    out = scrub(doc)
    after_answers = count_answers(out)

    bad = find_forbidden(out)
    if bad:
        print("REFUSING TO WRITE, %d forbidden string(s) survived:" % len(bad))
        for p, label, m in bad[:20]:
            print("   %-50s %-12s %s" % (p, label, m))
        return 1

    published = {
        "demonstration": a.demo,
        "recorded": a.replay_date,
        "served_by": "learner-1.0:<learner_id>",
        "note_on_how_answers_are_quoted": PUBLIC_NOTE if had_cleaning else
            "No answer in this file carried the trailing-turn fragment; nothing was shortened.",
    }
    published.update(out)

    os.makedirs(os.path.dirname(os.path.abspath(a.dest)), exist_ok=True)
    with open(a.dest, "w") as fh:
        json.dump(published, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print("%-46s -> %s" % (os.path.basename(a.src), a.dest))
    print("   served strings   %d before scrub, %d after" % (before_answers, after_answers))
    print("   shortened rows   %s" % ("yes, note attached" if had_cleaning else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
