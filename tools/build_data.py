#!/usr/bin/env python3
"""Build the taught material and the question sets from the runners. NOT FOR PUBLICATION.

The runners are not published: they encode the protocol and internal decisions. The DATA inside
them is the whole point of the repository, so it is lifted out here without importing anything
(the modules pull in the product client on import). Facts are declared as `dict(...)` calls, which
`ast.literal_eval` will not touch, so the assignment nodes are compiled and evaluated in a
namespace holding nothing but `dict` and the typing names.
"""
from __future__ import annotations

import ast
import json
import os
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.abspath(os.path.join(ROOT, "..", "..", "..", "tfgn_demo", "mcp"))
DEMOS = os.path.join(ROOT, "demos")


def grab(path: str, names: set) -> Dict[str, Any]:
    tree = ast.parse(open(path).read())
    ns = {"dict": dict, "List": List, "Dict": Dict, "Any": Any}
    out = {}
    for node in tree.body:
        tgt = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            tgt = node.targets[0].id
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            tgt = node.target.id
        if tgt in names and getattr(node, "value", None) is not None:
            out[tgt] = eval(compile(ast.Expression(node.value), "<data>", "eval"), ns)
    missing = names - set(out)
    if missing:
        raise SystemExit("could not read %s from %s" % (sorted(missing), path))
    return out


def write(path: str, obj, raw=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        if raw:
            fh.write(obj)
        else:
            json.dump(obj, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
    print("  %-58s %6d B" % (os.path.relpath(path, ROOT), os.path.getsize(path)))


def facts_block(facts, extra=()):
    rows = []
    for f in facts:
        row = {"id": f["rid"], "taught": f["fact"], "question": f["q"],
               "accepted_answers": f["keys"]}
        for k in extra:
            if k in f:
                row[k] = f[k]
        rows.append(row)
    return rows


def main():
    bake = grab(os.path.join(SRC, "demo_bake.py"),
                {"MD2_FACTS", "MD3_LESSON_A", "MD3_LESSON_B", "MD3_LESSON_C", "PREAMBLES"})
    md4 = grab(os.path.join(SRC, "demo_md4.py"),
               {"MD4_FACTS", "EARTH_CONTROLS", "VEYRA_PREAMBLE", "DELETE_RID", "KEEP_RID"})

    # ---- delete-a-fact -----------------------------------------------------------------
    d = os.path.join(DEMOS, "delete-a-fact")
    print("delete-a-fact")
    write(os.path.join(d, "data", "preamble.md"), bake["PREAMBLES"]["md2"], raw=True)
    write(os.path.join(d, "data", "facts.json"), {
        "world": "Meridian, a fictional engineering organisation",
        "preamble": "data/preamble.md",
        "note": ("The preamble is taught first as a document. The twelve facts are taught as "
                 "facts. Both are needed to reproduce the setup."),
        "facts": facts_block(bake["MD2_FACTS"], extra=("topic", "del_target")),
    })
    write(os.path.join(d, "questions.json"), {
        "frame": "Q: {question}",
        "wordings_per_fact": 1,
        "asked": "all twelve, before the deletion and again after it",
        "deleted_fact": next(f["rid"] for f in bake["MD2_FACTS"] if f.get("del_target")),
        "questions": [{"id": f["rid"], "topic": f["topic"], "question": f["q"],
                       "accepted_answers": f["keys"]} for f in bake["MD2_FACTS"]],
    })

    # ---- teach-in-sequence -------------------------------------------------------------
    d = os.path.join(DEMOS, "teach-in-sequence")
    print("teach-in-sequence")
    write(os.path.join(d, "data", "preamble.md"), bake["PREAMBLES"]["md3"], raw=True)
    lessons = [("A", "Kestrel, a fictional hardware board", bake["MD3_LESSON_A"], False),
               ("B", "Ondine, a fictional protocol", bake["MD3_LESSON_B"], False),
               ("C", "Tallow, a fictional billing system", bake["MD3_LESSON_C"], True)]
    write(os.path.join(d, "data", "lessons.json"), {
        "preamble": "data/preamble.md",
        "order": "A, then B, then C, all into the same learner",
        "lessons": [{"lesson": n, "subject": s, "trained_live_in_this_demonstration": live,
                     "facts": facts_block(f)} for n, s, f, live in lessons],
    })
    write(os.path.join(d, "questions.json"), {
        "frame": "Q: {question}",
        "wordings_per_fact": 1,
        "asked": ("lessons A and B before C was taught and again after; lesson C once, "
                  "after it was taught"),
        "questions": [{"id": f["rid"], "lesson": n, "question": f["q"],
                       "accepted_answers": f["keys"]}
                      for n, _s, fs, _l in lessons for f in fs],
    })

    # ---- override-a-belief -------------------------------------------------------------
    d = os.path.join(DEMOS, "override-a-belief")
    print("override-a-belief")
    write(os.path.join(d, "data", "preamble.md"), md4["VEYRA_PREAMBLE"], raw=True)
    write(os.path.join(d, "data", "facts.json"), {
        "world": "Veyra, an invented planet whose physics deliberately differ from Earth's",
        "preamble": "data/preamble.md",
        "deleted_fact": md4["DELETE_RID"],
        "kept_fact_checked_after_deletion": md4["KEEP_RID"],
        "facts": facts_block(md4["MD4_FACTS"]),
    })
    write(os.path.join(d, "data", "earth_controls.json"), {
        "purpose": ("Asked of the frozen base model and of the learner alike. If Earth physics "
                    "moved, something general was traded away to make room for Veyra."),
        "note": "These are never taught. They are only ever asked.",
        "controls": [{"id": f["rid"], "question": f["q"], "accepted_answers": f["keys"]}
                     for f in md4["EARTH_CONTROLS"]],
    })
    write(os.path.join(d, "questions.json"), {
        "frame": "Q: {question}",
        "wordings_per_fact": 1,
        "asked": ("every question of the frozen base first, then of the learner after teaching, "
                  "then once more after one fact was deleted"),
        "questions": [{"id": f["rid"], "question": f["q"], "accepted_answers": f["keys"]}
                      for f in md4["MD4_FACTS"]],
        "earth_controls": [{"id": f["rid"], "question": f["q"], "accepted_answers": f["keys"]}
                           for f in md4["EARTH_CONTROLS"]],
    })
    print("done")


if __name__ == "__main__":
    main()
