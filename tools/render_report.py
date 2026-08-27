#!/usr/bin/env python3
"""Render a replay session (the JSON `replay_status` returns) as a readable Markdown report.

    python3 tools/render_report.py session.json            # writes session.md beside it
    python3 tools/render_report.py session.json -o out.md
    python3 tools/render_report.py session.json --stdout

Accepts either the whole session object (with `result` inside) or a bare result. Nothing here
talks to the network; it only reads the file you give it. Answers are quoted to the end of the
answer itself (the served text can carry a trailing fragment in which the model starts a new
turn); the JSON keeps every byte, this render does not.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def _trim(answer: str, limit: int = 160) -> str:
    """Quote to the end of the answer itself: cut at the first new-turn marker, then cap."""
    a = (answer or "").strip()
    m = re.search(r"(?:^|[\s.!?])(?:user|assistant)\n", a)
    if m and m.start() > 0:
        a = a[: m.start() + (1 if a[m.start()] in ".!?" else 0)]
    for marker in ("\nQ:", "\nUser:", "\n\n"):
        i = a.find(marker)
        if i > 0:
            a = a[:i]
    a = a.replace("\n", " ").strip()
    return a if len(a) <= limit else a[: limit - 1] + "…"


def _cell(s: Any) -> str:
    return str(s if s is not None else "").replace("|", "\\|")


def _rows_table(rows: List[Dict[str, Any]]) -> List[str]:
    out = ["| label | wording | expected | served answer (trimmed) | strict | lenient |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        strict = "pass" if r.get("passed") else "miss"
        if r.get("served_identity_violation"):
            strict = "excluded (served by the wrong identity)"
        lenient = "pass" if r.get("passed_lenient") else "miss"
        out.append("| %s | %s | %s | %s | %s | %s |" % (
            _cell(r.get("label_id")), _cell(r.get("wording")), _cell(r.get("expected")),
            _cell(_trim(r.get("got") or r.get("answer") or "")), strict, lenient))
    return out


def _count(rows: List[Dict[str, Any]], key: str = "passed") -> str:
    if not rows:
        return "none"
    return "%d/%d" % (sum(1 for r in rows if r.get(key)), len(rows))


def render(session: Dict[str, Any], keep_ids: bool = False) -> str:
    res = session.get("result") if isinstance(session.get("result"), dict) else session
    if not isinstance(res, dict):
        raise SystemExit("no result in this file (the session has not finished, or it failed: %r)"
                         % session.get("error"))
    doc = res.get("document") or {}
    lid = res.get("learner_id") if keep_ids else ("<learner_id>" if res.get("learner_id") else None)
    jid = res.get("job_id") if keep_ids else ("<job_id>" if res.get("job_id") else None)
    lines: List[str] = []
    lines.append("# Replay report — %s" % (session.get("kind") or "session"))
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append("| learner | `%s` |" % _cell(lid))
    lines.append("| teach job | `%s` |" % _cell(jid))
    lines.append("| document | %s (%s words, %s bytes) |" % (
        _cell(doc.get("name")), _cell(doc.get("words")), _cell(doc.get("bytes"))))
    if doc.get("sha256"):
        lines.append("| document sha256 | `%s` |" % _cell(doc.get("sha256")))
    lines.append("| started / ended (UTC) | %s / %s |" % (
        _cell(session.get("started_utc")), _cell(session.get("ended_utc"))))
    lines.append("| question frame | `%s` |" % _cell(res.get("frame")))
    lines.append("| grader | %s |" % _cell(res.get("grader")))
    lines.append("")

    funnel = res.get("funnel") or []
    if funnel:
        lines.append("## Funnel")
        lines.append("")
        lines.append("| stage | count | of | share | note |")
        lines.append("|---|---|---|---|---|")
        for f in funnel:
            share = f.get("share")
            lines.append("| %s | %s | %s | %s | %s |" % (
                _cell(f.get("stage")), _cell(f.get("n")), _cell(f.get("of")),
                ("%.2f" % share) if isinstance(share, (int, float)) else _cell(share),
                _cell(f.get("note"))))
        lines.append("")

    tr = res.get("training") or {}
    if tr:
        lines.append("## Training")
        lines.append("")
        acq = tr.get("acquisition_nats")
        lines.append("- acquisition on the taught material: %s" % (
            ("%.4f nats" % acq) if isinstance(acq, (int, float)) else "not reported"))
        lines.append("- job status: %s" % _cell(tr.get("status")))
        series = [s for s in (tr.get("loss_series") or []) if s.get("loss") is not None]
        if series:
            first, last = series[0], series[-1]
            lines.append("- training loss: %.4f at step %s → %.4f at step %s (%d points polled)" % (
                first["loss"], first.get("step"), last["loss"], last.get("step"), len(series)))
            lines.append("")
            lines.append("| step | loss | phase | pass |")
            lines.append("|---|---|---|---|")
            for s in series:
                lines.append("| %s | %.4f | %s | %s |" % (
                    _cell(s.get("step")), s["loss"], _cell(s.get("phase")), _cell(s.get("passes"))))
        else:
            lines.append("- training loss series: not available for this job")
        lines.append("")

    for key, title in (("verify", "Verify (asked the way the document says it)"),
                       ("ask", "Ask (re-asked, other wordings)")):
        rows = res.get(key) or []
        if not rows:
            continue
        lines.append("## %s — %s strict, %s lenient" % (title, _count(rows), _count(rows, "passed_lenient")))
        lines.append("")
        lines.extend(_rows_table(rows))
        lines.append("")

    f41 = res.get("f41") or {}
    if f41:
        lines.append("## Served identity")
        lines.append("")
        n = f41.get("n_asks")
        verdict = f41.get("all_served_by_learner")
        if verdict is None:
            verdict = f41.get("served_by_learner")
        ck = f41.get("checkpoint_ids") or f41.get("checkpoints") or []
        lines.append("- asks recorded: %s" % _cell(n))
        lines.append("- every answer served by this learner: %s" % (
            "yes" if verdict is True else ("NO — see the excluded rows above" if verdict is False
                                           else "not observable from the client side on this build")))
        if isinstance(ck, list) and ck:
            lines.append("- distinct checkpoints seen serving: %d" % len(ck))
        lines.append("")

    lines.append("_Answers above are quoted to the end of the answer itself; the JSON file holds every "
                 "served byte untrimmed._")
    return "\n".join(lines) + "\n"


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("session", help="replay_status JSON (session or bare result)")
    ap.add_argument("-o", "--out", help="output .md path (default: beside the input)")
    ap.add_argument("--stdout", action="store_true", help="print instead of writing a file")
    ap.add_argument("--keep-ids", action="store_true",
                    help="print the learner and job ids (default redacts them, so the report can be "
                         "posted as-is; ids are yours, but a posted report should not carry them)")
    a = ap.parse_args(argv)
    src = Path(a.session)
    md = render(json.loads(src.read_text(encoding="utf-8")), keep_ids=a.keep_ids)
    if a.stdout:
        sys.stdout.write(md)
        return 0
    out = Path(a.out) if a.out else src.with_suffix(".md")
    out.write_text(md, encoding="utf-8")
    print("wrote %s (%d lines)" % (out, md.count("\n")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
